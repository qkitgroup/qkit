import json
from dataclasses import dataclass, field
from enum import Enum
from os import PathLike
from typing import Optional, Literal, Any

import h5py
import numpy as np

from qkit._version import __version__ as qkit_version

class HDF5:
    """
    A thin wrapper around h5py to support qviewkit meta-data.

    The base structure consists out of a root node 'entry' with subnodes 'data0', 'view0', 'analysis0'.
    Data is stored in 'data0', views in 'view0', and analysis in 'analysis0'.
    """

    hdf: h5py.File
    can_write: bool
    data_group: h5py.Group
    view_group: h5py.Group
    analysis_group: h5py.Group

    def __init__(self, filename: str | PathLike, mode: Literal['r', 'w', 'a'], locking: bool=False):
        """
        Open a hdf5 file. If writing, create a base structure (/entry/data0, /entry/view0, /entry/analysis0).

        Also enables simultaneous reading by qviewkit using the SWMR feature of HDF5. Prevents crashes due to locking.
        """
        self.can_write = not 'r' in mode
        if self.can_write:
            self.hdf = h5py.File(filename, mode, libver='latest', locking=locking)
            self.hdf.swmr_mode = True  # Enable simultaneous reading by qviewkit
            self.hdf.attrs['qkit_version'] = qkit_version.encode('utf-8')
            self.hdf.attrs['NeXus_version'] = "4.3.0".encode('utf-8')
        else: # Read-only
            self.hdf = h5py.File(filename, mode, libver='latest', locking=locking, swmr=True)

        entry = self.hdf.require_group('entry')
        if self.can_write:
            entry.attrs.update(
                {
                    'NX_class': 'NXentry'.encode('utf-8'),
                    'data_latest': 0,
                    'analysis_latest': 0,
                    'updating': True
                }
            )

        self.data_group = entry.require_group('data0')
        if self.can_write:
            self.data_group.attrs['NX_class'] = "NXdata".encode('utf-8')

        self.view_group = entry.require_group('view0')
        self.analysis_group = entry.require_group('analysis0')

    def create_dataset(self, name: str, shape: tuple[int,...], unit: str = 'a.u.', dtype: str = 'f',
                       axes: Optional[list[h5py.Dataset]] = None, comment: Optional[str] = None, category: Literal['data', 'analysis'] = 'data', **kwargs):
        """
        Create a dataset of fixed size. Initialized empty, but compressed, no scale offset.

        Let's hdf5 do automatic chunking, also uses lzf compression to minimize empty file size.
        Derives type of data from dimensionality (i.e. 1D=vector, 2D=matrix, 3D=box).

        Use the axis argument to define x, y, z axis. The category manages placement into either the data or analysis
        group.
        """
        if category == 'data':
            group = self.data_group
        elif category == 'analysis':
            group = self.analysis_group
        else:
            raise ValueError(f"Category {category} not supported.")
        ds = group.create_dataset(
            name,
            shape, maxshape=shape, # Shape
            dtype=dtype, fillvalue = np.nan, # Empty initialization
            chunks=True, compression='lzf' # Storage options
        )
        # Set Metadata: ds_type from dimension
        match len(shape):
            case 1:
                ds_type = HDF5.DataSetType.VECTOR
            case 2:
                ds_type = HDF5.DataSetType.MATRIX
            case 3:
                ds_type = HDF5.DataSetType.BOX
            case _:
                raise NotImplementedError(f"Dimensionality {len(shape)} not supported.")
        ds.attrs['ds_type'] = ds_type.value
        ds.attrs['name'] = name.encode('utf-8')
        if comment is not None:
            ds.attrs['comment'] = comment.encode('utf-8')
        ds.attrs['ds_url'] = ds.name.encode('utf-8')
        ds.attrs['unit'] = unit.encode('utf-8')
        if axes is not None:
            for i, axis in enumerate(axes):
                label = chr(ord('x') + i) #x, y, z.
                ds.attrs[f"{label}_ds_url"] = axis.name.encode('utf-8')
        return ds

    def get_dataset(self, ds_url: str, category: Literal['data', 'analysis'] = 'data') -> h5py.Dataset | None:
        """
        Get a dataset by its name, either from the data or analysis group.
        """
        if category == 'data':
            group = self.data_group
        elif category == 'analysis':
            group = self.analysis_group
        else:
            raise ValueError(f"Category {category} not supported.")
        return group.get(ds_url, default=None)

    def write_text_record(self, name: str, content: str, comment: Optional[str] = None):
        """
        Writes a text record to the dataset name in the 'data' group.
        """
        dtype = h5py.string_dtype(encoding='utf-8')
        ds = self.data_group.create_dataset(name, shape=(1,), dtype=dtype)
        ds[0] = str(content)
        ds.attrs['ds_type'] = HDF5.DataSetType.TXT.value
        ds.attrs['ds_url'] = ds.name.encode('utf-8')
        if comment is not None:
            ds.attrs['comment'] = comment.encode('utf-8')

    def insert_view(self, name: str, view: 'HDF5.DataView'):
        """
        Adapts QViewKits proprietary view format. Overall config in settings, and a list of views.

        Settings set the view type, dataset type, and view parameters. For example, this defines if we
        have a line or color plot.

        The views are a list of view objects, which define the x, y, filter, and error datasets. They are displayed
        in the same plot.
        """
        ds = self.view_group.require_dataset(name, shape=(0,), dtype='f')
        ds.attrs['name'] = name
        view.write(self, ds)

    def close(self):
        """
        Close the backing file.
        """
        self.hdf.attrs['updating'] = False
        self.hdf.close()

    def flush(self):
        """
        Flush the backing file.
        """
        self.hdf.flush()

    @dataclass(frozen=True)
    class DataView:
        """
        Describes the data required for a view, and allows for writing this in the format required by QViewKit.

        The view type defines the type of plot, e.g. line, color, etc. The view parameters allow for default plotting
        options, such as marker size.

        The view sets contain references to data in the hdf5 file to be plotted.
        """
        view_type: 'HDF5.DataViewType'
        view_params: dict[str, Any] = field(default_factory=dict)
        view_sets: list['HDF5.DataViewSet'] = field(default_factory=list)

        def write(self, file: 'HDF5', dataset: h5py.Dataset):
            """
            Write the view metadata to the dataset, followed by the view sets.
            """
            dataset.attrs['ds_type'] = HDF5.DataSetType.VIEW.value
            dataset.attrs['view_type'] = self.view_type.value
            dataset.attrs['view_params'] = json.dumps(self.view_params).encode('utf-8')
            dataset.attrs['overlays'] = len(self.view_sets)
            for i, view in enumerate(self.view_sets):
                view.write_to_dataset(file, dataset, i)

    @dataclass(frozen=True)
    class DataReference:
        """
        A reference to a dataset in the hdf5 file. Consists out of its name and the category it belongs to.
        """
        name: str
        category: Literal['data', 'analysis'] = 'data'

        def get_dataset(self, hdf: 'HDF5') -> h5py.Dataset:
            """
            Get a handle to the dataset.
            """
            return hdf.get_dataset(self.name, self.category)

        def to_path(self, hdf: 'HDF5') -> str:
            """
            Get the path of the dataset in the hdf5 file, if it exists.
            """
            ds = self.get_dataset(hdf)
            if ds is None:
                raise ValueError(f"Dataset '{self.name}' not found.")
            return ds.name


    @dataclass(frozen=True)
    class DataViewSet:
        """
        A view set for a view, consisting of the x and y datasets, and optional error dataset and filter methods.
        """
        x_path: 'HDF5.DataReference'
        y_path: 'HDF5.DataReference'
        filter: Optional[str] = None
        error: Optional[str] = None

        def write_to_dataset(self, file: 'HDF5', dataset: h5py.Dataset, index):
            """
            Writes the view set to the dataset belonging to the view.
            """
            dataset.attrs[f'xy_{index}'] = f"{self.x_path.to_path(file)}:{self.y_path.to_path(file)}".encode('utf-8')
            dataset.attrs[f'xy_{index}_filter'] = str(self.filter).encode('utf-8')
            if self.error:
                dataset.attrs[f'xy_{index}_error'] = self.error.encode('utf-8')


    class DataSetType(Enum):
        """
        The QViewKit proprietary data set types constants.
        """
        COORDINATE = 0
        VECTOR = 1
        MATRIX = 2
        BOX = 3
        TXT = 10
        VIEW = 20

    class DataViewType(Enum):
        """
        The QViewKit proprietary view types constants. The view type defines the type of plot, e.g. line, color, etc.
        """
        ONE_D = 0
        ONE_D_V = 1
        TWO_D = 2
        THREE_D = 3
        TABLE = 4
        TXT = 5