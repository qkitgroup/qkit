from dataclasses import dataclass
from enum import Enum
from typing import Optional, Literal

import h5py
import numpy as np

from qkit._version import __version__ as qkit_version

class HDF5:
    """
    A thin wrapper around h5py to support qviewkit meta-data.
    """

    hdf: h5py.File
    can_write: bool
    data_group: h5py.Group
    view_group: h5py.Group
    analysis_group: h5py.Group

    def __init__(self, filename: str, mode: Literal['r', 'w', 'a'], locking: bool=False):
        """
        Open a hdf5 file. If writing, create base structure.

        The base structure consists out of a root node 'entry' with subnodes 'data0', 'view0', 'analysis0'.
        Data is stored in 'data0', views in 'view0', and analysis in 'analysis0'.
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
                       axes: Optional[list[h5py.Dataset]] = None, comment: Optional[str] = None, **kwargs):
        """
        Create a dataset of fixed size. No compression, no scale offset.

        Let's hdf5 do automatic chunking, also uses lzf compression to minimize empty file size.
        Derives type of data from dimensionality (i.e. 1D=vector, 2D=matrix, 3D=box).

        Use the axis argument to define x, y, z axis.
        """
        # We assume, that at most full vectors will be written. We can thus start growing our array from the last dimension.
        ds = self.data_group.create_dataset(name,
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
        if comment is not None:
            ds.attrs['comment'] = comment.encode('utf-8')
        ds.attrs['ds_url'] = ds.name.encode('utf-8')
        ds.attrs['unit'] = unit.encode('utf-8')
        if axes is not None:
            for i, axis in enumerate(axes):
                label = chr(ord('x') + i) #x, y, z.
                ds.attrs[f"{label}_ds_url"] = axis.name.encode('utf-8')
        return ds

    def get_dataset(self, ds_url: str):
        return self.data_group[ds_url]

    def write_text_record(self, name: str, content: str, comment: Optional[str] = None):
        """
        Writes a text record to the dataset 'name'.
        """
        dtype = h5py.string_dtype(encoding='utf-8')
        ds = self.data_group.create_dataset(name, shape=(1,), dtype=dtype)
        ds[0] = content
        ds.attrs['ds_type'] = HDF5.DataSetType.TXT.value
        ds.attrs['ds_url'] = ds.name.encode('utf-8')
        if comment is not None:
            ds.attrs['comment'] = comment.encode('utf-8')

    def insert_view(self, name: str, settings: 'HDF5.DataViewSettings', views: list['HDF5.DataView']):
        """
        Adapts QViewKits proprietary view format. Overall config in settings, and a list of views.

        Settings set the view type, dataset type, and view parameters. For example, this defines if we
        have a line or color plot.

        The views are a list of view objects, which define the x, y, filter, and error datasets. They are displayed
        in the same plot.
        """
        ds = self.view_group.require_dataset(name, shape=(), maxshape=(), dtype='f')
        ds.attrs['overlays'] = len(views)
        settings.write(ds)
        for i, view in enumerate(views):
            view.write_to_dataset(ds, i)

    def close(self):
        self.hdf.close()

    @dataclass
    class DataViewSettings:
        dataset_type: 'HDF5.DataSetType'
        view_type: 'HDF5.DataViewType'
        view_params: str

        def write(self, dataset: h5py.Dataset):
            dataset.attrs['ds_type'] = self.dataset_type.value
            dataset.attrs['view_type'] = self.view_type.value
            dataset.attrs['view_params'] = self.view_params.encode('utf-8')

    @dataclass
    class DataView:
        x_path: [str] = None
        y_path: [str] = None
        filter: Optional[str] = None
        error: Optional[str] = None

        def write_to_dataset(self, dataset: h5py.Dataset, index):
            dataset.attrs[f'xy_{index}'] = f"{self.x_path}:{self.y_path}".encode('utf-8')
            dataset.attrs[f'xy_{index}_filter'] = self.filter.encode('utf-8') if self.filter else None
            if self.error:
                dataset.attrs[f'xy_{index}_error'] = self.error.encode('utf-8')

    class DataSetType(Enum):
        COORDINATE = 0
        VECTOR = 1
        MATRIX = 2
        BOX = 3
        TXT = 10
        VIEW = 20

    class DataViewType(Enum):
        ONE_D = 0
        ONE_D_V = 1
        TWO_D = 2
        THREE_D = 3
        TABLE = 4
        TXT = 5