# data.py, class for handling measurement data
# Reinier Heeres <reinier@heeres.eu>
# Pieter de Groot <pieterdegroot@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gobject
import os
import os.path
import time
import numpy
import types
import re
import logging
import copy
import shutil

from gettext import gettext as _L

from lib import namedlist, temp
from lib.misc import dict_to_ordered_tuples, get_arg_type
from lib.config import get_config
config = get_config()
in_qtlab = config.get('qtlab', False)
from lib.network.object_sharer import SharedGObject, cache_result

if in_qtlab:
    import qt

# Filename generator classes

class DateTimeGenerator:
    '''
    Class to generate filenames / directories based on the date and time.
    '''

    def __init__(self):
        pass

    def create_data_dir(self, datadir, name=None, ts=None, datesubdir=True, timesubdir=True):
        '''
        Create and return a new data directory.

        Input:
            datadir (string): base directory
            name (string): optional name of measurement
            ts (time.localtime()): timestamp which will be used if timesubdir=True
            datesubdir (bool): whether to create a subdirectory for the date
            timesubdir (bool): whether to create a subdirectory for the time

        Output:
            The directory to place the new file in
        '''

        path = datadir
        if ts is None:
            ts = time.localtime()
        if datesubdir:
            path = os.path.join(path, time.strftime('%Y%m%d', ts))
        if timesubdir:
            tsd = time.strftime('%H%M%S', ts)
            if name is not None:
                tsd += '_' + name
            path = os.path.join(path, tsd)

        return path

    def new_filename(self, data_obj):
        '''Return a new filename, based on name and timestamp.'''

        dir = self.create_data_dir(config['datadir'], name=data_obj._name,
                ts=data_obj._localtime)
        tstr = time.strftime('%H%M%S', data_obj._localtime)
        filename = '%s_%s.dat' % (tstr, data_obj._name)

        return os.path.join(dir, filename)


class IncrementalGenerator:
    '''
    Class to generate filenames that are incrementally numbered.
    '''

    def __init__(self, basename, start=1):
        self._basename = basename
        self._counter = start
        self._counter = self._check_last_number(self._counter)
        logging.info('IncrementalGenerator: starting counter at %d',
                self._counter)

    def _fn(self, n):
        return self._basename + ('_%d.dat' % n)

    def _check_last_number(self, start=1):
        if not os.path.exists(self._fn(1)):
            return 1

        curn = start
        stepsize = 1
        while os.path.exists(self._fn(curn)):
            curn += stepsize
            stepsize *= 2

        dir = -1
        stepsize /= 2
        while stepsize != 0:
            if os.path.exists(self._fn(curn)):
                stepsize /= 2
                curn += stepsize
            else:
                curn -= stepsize

        return curn + 1

    def new_filename(self, data_obj):
        fn = self._fn(self._counter)
        while os.path.exists(fn):
            logging.warning('File "%s" exists, incrementing counter', fn)
            self._counter += 1
            fn = self._fn(self._counter)
        self._counter += 1
        return fn

class _DataList(namedlist.NamedList):
    def __init__(self, time_name=False):
        namedlist.NamedList.__init__(self, base_name='data')

        self._time_name = time_name

    def new_item_name(self, item, name):
        '''Function to generate a new item name.'''

        if name == '':
            self._auto_counter += 1
            name = self._base_name + str(self._auto_counter)

        if self._time_name:
            return item.get_time_name()
        else:
            return name

class Data(SharedGObject):
    '''
    Data class
    '''

    _data_list = _DataList()
    _filename_generator = DateTimeGenerator()

    __gsignals__ = {
        'new-data-point': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ()),
        'new-data-block': (gobject.SIGNAL_RUN_FIRST,
                            gobject.TYPE_NONE,
                            ())
    }

    _METADATA_INFO = {
        'instrument': {
            're': re.compile('^#[ \t]*Ins?trument: ?(.*)$', re.I),
            'type': types.StringType
        },
        'parameter': {
            're': re.compile('^#[ \t]*Parameter: ?(.*)$', re.I),
            'type': types.StringType
        },
        'units': {
            're': re.compile('^#[ \t]*Units?: ?(.*)$', re.I),
            'type': types.StringType
        },
        'steps': {
            're': re.compile('^#[ \t]*Steps?: ?(.*)$', re.I),
            'type': types.IntType
        },
        'stepsize': {
            're': re.compile('^#[ \t]*Stepsizes?: ?(.*)$', re.I),
            'type': types.FloatType
        },
        'name': {
            're': re.compile('^#[ \t]*Name: ?(.*)$', re.I),
            'type': types.StringType
        },
        'type': {
            're': re.compile('^#[ \t]*Type?: ?(.*)$', re.I),
            'type': types.StringType,
            'function': lambda self, type: self._type_added(type)
        },
    }

    _META_STEPRE = re.compile('^#.*[ \t](\d+) steps', re.I)
    _META_COLRE = re.compile('^#.*Column ?(\d+)', re.I)
    _META_COMMENTRE = re.compile('^#(.*)', re.I)

    _INT_TYPES = (
            types.IntType, types.LongType,
            numpy.int, numpy.int0, numpy.int8,
            numpy.int16, numpy.int32, numpy.int64,
    )

    def __init__(self, *args, **kwargs):
        '''
        Create data object. There are three different uses:
        1) create an empty data object for use in a measurement
        2) create a data object and fill immediately with a numpy array
        3) create a data object from an existing data file

        All inputs are optional.
        The 'name' input is used in an internal list (accessable through
        qt.data). If omitted, a name will be auto generated.
        This 'name' will also be used later to auto generate a filename
        when calling 'create_file()' (if that is called without options).
        The input 'filename' here is only used for loading an existing file.

        args input:
            filename (string), set the filename to load.
            data (numpy.array), array to construct data object for

        kwargs input:
            name (string), default will be 'data<n>'
            infile (bool), default True
            inmem (bool), default False if no file specified, True otherwise
            tempfile (bool), default False. If True create a temporary file
                for the data.
            binary (bool), default True. Whether tempfile should be binary.
        '''

        # Init SharedGObject a bit lower

        name = kwargs.get('name', '')
        infile = kwargs.get('infile', True)
        inmem = kwargs.get('inmem', False)

        self._inmem = inmem
        self._tempfile = kwargs.get('tempfile', False)
        self._temp_binary = kwargs.get('binary', True)
        self._options = kwargs
        self._file = None
        self._stop_req_hid = None

        # Dimension info
        self._dimensions = []
        self._block_sizes = []
        self._loopdims = None
        self._loopshape = None
        self._complete = False
        self._reshaped_data = None

        # Number of coordinate dimensions
        self._ncoordinates = 0

        # Number of value dimensions
        self._nvalues = 0

        # Number of data points
        self._npoints = 0
        self._npoints_last_block = 0
        self._npoints_max_block = 0

        self._comment = []
        self._localtime = time.localtime()
        self._timestamp = time.asctime(self._localtime)
        self._timemark = time.strftime('%H%M%S', self._localtime)
        self._datemark = time.strftime('%Y%m%d', self._localtime)

        # FIXME: the name generation here is a bit nasty
        name = Data._data_list.new_item_name(self, name)
        self._name = name

        SharedGObject.__init__(self, 'data_%s' % name,
            replace=True, idle_emit=True)

        data = get_arg_type(args, kwargs,
                (numpy.ndarray, list, tuple),
                'data')
        if data is not None:
            self.set_data(data)
        else:
            self._data = numpy.array([])
            self._infile = infile

        filepath = get_arg_type(args, kwargs, types.StringType, 'filepath')
        if self._tempfile:
            self.create_tempfile(filepath)
        elif filepath is not None and filepath != '':
            if 'inmem' not in kwargs:
                inmem = True
            self.set_filepath(filepath, inmem)
            self._infile = True
        else:
            self._dir = ''
            self._filename = ''
            self._infile = infile

        # Don't hold references to temporary data files
        if not self._tempfile:
            Data._data_list.add(name, self)

    def __repr__(self):
        ret = "Data '%s', filename '%s'" % (self._name, self._filename)
        return ret

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, val):
        self._data[index] = val

### Data info

    def get_dimensions(self):
        '''Return info for all dimensions.'''
        return self._dimensions

    def get_dimension_size(self, dim):
        '''Return size of dimensions dim'''

        if dim >= len(self._dimensions):
            return 0

        if 'size' in self._dimensions[dim]:
            return self._dimensions[dim]['size']
        else:
            return 0

    def get_dimension_name(self, dim):
        '''Return the name of dimension dim'''

        if dim >= len(self._dimensions):
            return 'col%d' % dim
        else:
            return self._dimensions[dim].get('name', 'col%d' % dim)

    def get_ndimensions(self):
        '''Return number of dimensions.'''
        return len(self._dimensions)

    def get_coordinates(self):
        '''Return info for all coordinate dimensions.'''
        return self._dimensions[:self._ncoordinates]

    def get_ncoordinates(self):
        '''Return number of coordinate dimensions.'''
        return self._ncoordinates

    def get_values(self):
        '''Return info for all value dimensions.'''
        return self._dimensions[self._ncoordinates:]

    def get_nvalues(self):
        '''Return number of value dimensions.'''
        return self._nvalues

    def get_npoints(self):
        '''Return number of data points'''
        return self._npoints

    def get_npoints_max_block(self):
        '''Return the maximum number of data points in a block.'''
        return self._npoints_max_block

    def get_npoints_last_block(self):
        '''Return number of data points in most recent block'''
        return self.get_block_size(self.get_nblocks() - 1)

    def get_nblocks(self):
        '''Return number of blocks.'''
        nblocks = len(self._block_sizes)
        if self._npoints_last_block > 0:
            return nblocks + 1
        else:
            return nblocks

    def get_nblocks_complete(self):
        '''Return number of completed blocks.'''
        return len(self._block_sizes)

    def get_block_size(self, blockid):
        if blockid == len(self._block_sizes):
            return self._npoints_last_block
        elif blockid < 0 or blockid > len(self._block_sizes):
            return 0
        else:
            return self._block_sizes[blockid]

    def format_label(self, dim):
        '''Return a formatted label for dimensions dim'''

        if dim >= len(self._dimensions):
            return ''

        info = self._dimensions[dim]

        label = ''
        if 'name' in info:
            label += info['name']

        if 'instrument' in info and 'parameter' in info:
            insname = info['instrument']
            if type(insname) not in (types.StringType, types.UnicodeType):
                insname = insname.get_name()

            label += ' (%s.%s' % (insname, info['parameter'])
            if 'units' in info:
                label += ' [%s]' % info['units']
            label += ')'

        elif 'name' not in info:
            label = 'dim%d' % dim

        return label

    def get_data(self, reshape=False):
        '''
        Return data as a numpy.array.

        Normally the data is just a 2D array, with a set of values on each
        'line'. However, if reshape is True, the data will be reshaped into
        the detected dimension sizes.
        '''

        if not self._inmem and self._infile:
            self._load_file()

        if self._inmem:
            if reshape:
                return self._reshape_data()
            else:
                return self._data
        else:
            return None

    def get_reshaped_data(self):
        ''''Return data reshaped with the proper dimensions.'''
        return self.get_data(reshape=True)

    def get_title(self, coorddims, valdim):
        '''
        Return a title that can be used in a plot, containing the filename
        and the name of the coordinate and value dimensions.
        '''

        dir = self.get_dir().rstrip('/\\')
        lastdir = os.path.split(dir)[-1]
        dirfn = '%s/%s' % (lastdir, self.get_filename())

        title = '%s, %s vs ' % (dirfn, self.get_dimension_name(valdim))

        first = True
        for coord in coorddims:
            if not first:
                title += ', '
            first = False
            title += '%s' % self.get_dimension_name(coord)

        return title

### File info

    @staticmethod
    def set_filename_generator(generator):
        Data._filename_generator = generator

    def get_filename(self):
        return self._filename

    def get_dir(self):
        return self._dir

    def get_filepath(self):
        return os.path.join(self._dir, self._filename)

    def get_name(self):
        return self._name

    def set_name(self, name):
        self._name = name

    def get_time_name(self):
        return '%s_%s' % (self._timemark, self._name)

    def get_settings_filepath(self):
        fn, ext = os.path.splitext(self.get_filepath())
        return fn + '.set'

    def is_file_open(self):
        '''Return whether a file is open or not.'''

        if self._file is not None:
            return True
        else:
            return False

### Measurement info

    def add_coordinate(self, name, **kwargs):
        '''
        Add a coordinate dimension. Use add_value() to add a value dimension.

        Input:
            name (string): the name for this coordinate
            kwargs: you can add any info here, but predefined are:
                size (int): the size of this dimension
                instrument (Instrument): instrument this coordinate belongs to
                parameter (string): parameter of the instrument
                units (string): units of this coordinate
                precision (int): precision of stored data, default is
                    'default_precision' from config, or 12 if not defined.
                format (string): format of stored data, not used by default
        '''

        kwargs['name'] = name
        kwargs['type'] = 'coordinate'
        if 'size' not in kwargs:
            kwargs['size'] = 0
        self._ncoordinates += 1
        self._dimensions.append(kwargs)

    def add_value(self, name, **kwargs):
        '''
        Add a value dimension. Use add_dimension() to add a coordinate
        dimension.

        Input:
            name (string): the name for this coordinate
            kwargs: you can add any info here, but predefined are:
                instrument (Instrument): instrument this coordinate belongs to
                parameter (string): parameter of the instrument
                units (string): units of this coordinate
                precision (int): precision of stored data, default is
                    'default_precision' from config, or 12 if not defined.
                format (string): format of stored data, not used by default
        '''
        kwargs['name'] = name
        kwargs['type'] = 'value'
        self._nvalues += 1
        self._dimensions.append(kwargs)

    def add_comment(self, comment):
        '''Add comment to the Data object.'''
        self._comment.append(comment)
        if self._file is not None:
            self._file.write('# %s\n' % comment)

    def get_comment(self):
        '''Return the comment for the Data object.'''
        return self._comment

### File writing

    def create_file(self, name=None, filepath=None, settings_file=True):
        '''
        Create a new data file and leave it open. In addition a
        settings file is generated, unless settings_file=False is
        specified.

        This function should be called after adding the comment and the
        coordinate and value metadata, because it writes the file header.
        '''

        if name is None and filepath is None:
            name = self._name

        if filepath is None:
            filepath = self._filename_generator.new_filename(self)

        self._dir, self._filename = os.path.split(filepath)
        if not os.path.isdir(self._dir):
            os.makedirs(self._dir)

        try:
            self._file = open(self.get_filepath(), 'w+')
        except:
            logging.error('Unable to open file')
            return False

        self._write_header()

        if settings_file and in_qtlab:
            self._write_settings_file()

        try:
            if in_qtlab:
                self._stop_req_hid = \
                    qt.flow.connect('stop-request', self._stop_request_cb)
        except:
            pass

        return True

    def close_file(self):
        '''
        Close open data file.
        '''

        if self._file is not None:
            self._file.close()
            self._file = None

        if self._stop_req_hid is not None and in_qtlab:
            qt.flow.disconnect(self._stop_req_hid)
            self._stop_req_hid = None

    def _write_settings_file(self):
        fn = self.get_settings_filepath()
        f = open(fn, 'w+')
        f.write('Filename: %s\n' % self._filename)
        f.write('Timestamp: %s\n\n' % self._timestamp)

        inslist = dict_to_ordered_tuples(qt.instruments.get_instruments())
        for (iname, ins) in inslist:
            f.write('Instrument: %s\n' % iname)
            parlist = dict_to_ordered_tuples(ins.get_parameters())
            for (param, popts) in parlist:
                f.write('\t%s: %s\n' % (param, ins.get(param, query=False)))

        f.close()

    def _write_header(self):
        self._file.write('# Filename: %s\n' % self._filename)
        self._file.write('# Timestamp: %s\n\n' % self._timestamp)
        for line in self._comment:
            self._file.write('# %s\n' % line)

        i = 1
        for dim in self._dimensions:
            self._file.write('# Column %d:\n' % i)
            for key, val in dict_to_ordered_tuples(dim):
                self._file.write('#\t%s: %s\n' % (key, val))
            i += 1

        self._file.write('\n')

    def _format_data_value(self, val, colnum):
        if type(val) in self._INT_TYPES:
            return '%d' % val

        if colnum < len(self._dimensions):
            opts = self._dimensions[colnum]
            if 'format' in opts:
                return opts['format'] % val
            elif 'precision' in opts:
                format = '%%.%de' % opts['precision']
                return format % val

        precision = config.get('default_precision', 12)
        format = '%%.%de' % precision
        return format % val

    def _write_data_line(self, args):
        '''
        Write a line of data.
        Args can be a single value or a 1d numpy.array / list / tuple.
        '''

        if hasattr(args, '__len__'):
            if len(args) > 0:
                line = self._format_data_value(args[0], 0)
                for colnum in range(1, len(args)):
                    line += '\t%s' % \
                            self._format_data_value(args[colnum], colnum)
            else:
                line = ''
        else:
            line = self._format_data_value(args, 0)

        line += '\n'
        self._file.write(line)
        self._file.flush()

    def _get_block_columns(self):
        blockcols = []
        for i in range(self.get_ncoordinates()):
            if len(self._data) > 1 and self._data[0][i] == self._data[1][i]:
                blockcols.append(True)
            else:
                blockcols.append(False)
        for i in range(self.get_nvalues()):
            blockcols.append(False)

        return blockcols

    def _write_data(self):
        if not self._inmem:
            logging.warning('Unable to _write_data() without having it memory')
            return False

        blockcols = self._get_block_columns()

        lastvals = None
        for vals in self._data:
            if type(vals) is numpy.ndarray and lastvals is not None:
                for i in range(len(vals)):
                    if blockcols[i] and vals[i] != lastvals[i]:
                        self._file.write('\n')

            self._write_data_line(vals)
            lastvals = vals

    def _write_binary(self):
        if not self._inmem:
            logging.warning('Unable to _write_binary() without having it memory')
            return False

        self._data.tofile(self._file.get_file())
        return True

### High-level file writing

    def write_file(self, name=None, filepath=None):
        '''
        Create and write a new data file.
        '''

        if not self.create_file(name=name, filepath=filepath):
            return

        self._write_data()
        self.close_file()

    def create_tempfile(self, path=None):
        '''
        Create a temporary file, optionally called <path>.
        '''

        if self._temp_binary:
            mode = 'wb'
        else:
            mode = 'w'
        self._file = temp.File(path, mode=mode, binary=self._temp_binary)
        try:
            if self._temp_binary:
                ret = self._write_binary()
            else:
                self._write_data()

            self._dir, self._filename = os.path.split(self._file.name)
            self._file.close()
            self._tempfile = True
        except Exception, e:
            logging.warning('Error creating temporary file: %s', e)
            self._dir = ''
            self._filename = ''
            self._tempfile = False

    def rewrite_tempfile(self):
        '''
        Rewrite the temporary file with the current data.
        '''

        if not self._tempfile:
            logging.warning('Data object has no temporary file to rewrite')
            return

        self._file.reopen()
        if self._temp_binary:
            self._write_binary()
        else:
            self._write_data()
        self._file.close()

    def copy_file(self, fn):
        '''
        Copy a relevant file to the directory where the main data file is
        located.
        '''
        p, n = os.path.split(fn)
        newfn = os.path.join(self.get_dir(), n)
        shutil.copyfile(fn, newfn)

### Adding data

    def add_data_point(self, *args, **kwargs):
        '''

        Add new data point(s) to the data set (in memory and/or on disk).
        Note that one data point can consist of multiple coordinates and values.

        provide 1 data point
            - N numbers: d.add_data_points(1, 2, 3)

        OR

        provide >1 data points.
            - a single MxN 2d array: d.add_data_point(arraydata)
            - N 1d arrays of length M: d.add_data_points(a1, a2, a3)

        Notes:
        If providing >1 argument, all vectors should have same shape.
        String data is not compatible with 'inmem'.

        Input:
            *args:
                n column values or a 2d array
            **kwargs:
                newblock (boolean): marks a new 'block' starts after this point

        Output:
            None
        '''

        # Check what type of data is being added
        shapes = [numpy.shape(i) for i in args]
        dims = numpy.array([len(i) for i in shapes])

        if len(args) == 0:
            logging.warning('add_data_point(): no data specified')
            return
        elif len(args) == 1:
            if dims[0] == 2:
                ncols = shapes[0][1]
                npoints = shapes[0][0]
                args = args[0]
            elif dims[0] == 1:
                ncols = 1
                npoints = shapes[0][0]
                args = args[0]
            elif dims[0] == 0:
                ncols = 1
                npoints = 1
            else:
                loggin.warning('add_data_point(): adding >2d data not supported')
                return
        else:
            # Check if all arguments have same shape
            for i in range(1, len(args)):
                if shapes[i] != shapes[i-1]:
                    logging.warning('add_data_point(): not all provided data arguments have same shape')
                    return

            if sum(dims!=1) == 0:
                ncols = len(args)
                npoints = shapes[0][0]
                # Transpose args to a single 2-d list
                args = zip(*args)
            elif sum(dims!=0) == 0:
                ncols = len(args)
                npoints = 1
            else:
                logging.warning('add_data_point(): addint >2d data not supported')
                return

        # Check if the number of columns is correct.
        # If the number of columns is not yet specified, then it will be done
        # (only the first time) according to the data

        if len(self._dimensions) == 0:
            logging.warning('add_data_point(): no dimensions specified, adding according to data')
            self._add_missing_dimensions(ncols)

        if ncols < len(self._dimensions):
            logging.warning('add_data_point(): missing columns (%d < %d)' % \
                (ncols, len(self._dimensions)))
            return
        elif ncols > len(self._dimensions):
            logging.warning('add_data_point(): too many columns (%d > %d)' % \
                (ncols, len(self._dimensions)))
            return

        # At this point 'args' is either:
        #   - a 1d tuple of numbers, for adding a single data point
        #   - a 2d tuple/list/array, for adding >1 data points
        if self._inmem:
            if len(self._data) == 0:
                self._data = numpy.atleast_2d(args)
            else:
                self._data = numpy.append(self._data, [args], axis=0)

        if self._infile:
            if npoints == 1:
                self._write_data_line(args)
            elif npoints > 1:
                for i in range(npoints):
                    self._write_data_line(args[i])

        self._npoints += npoints
        self._npoints_last_block += npoints
        if self._npoints_last_block > self._npoints_max_block:
            self._npoints_max_block = self._npoints_last_block

        if 'newblock' in kwargs and kwargs['newblock']:
            self.new_block()
        else:
            self.emit('new-data-point')

    def new_block(self):
        '''Start a new data block.'''

        if self._infile:
            self._file.write('\n')

        self._block_sizes.append(self._npoints_last_block)
        self._npoints_last_block = 0

        self.emit('new-data-block')

    def _add_missing_dimensions(self, nfields):
        '''
        Add extra dimensions so that the total equals nfields.
        Only the last field will be tagged as a value, the rest will be
        coordinates.
        '''

        # Add info for (assumed coordinate) columns that had no metadata
        while self.get_ndimensions() < nfields - 1:
            self.add_coordinate('col%d' % (self.get_ndimensions() + 1))

        # Add info for (assumed value) column that had no metadata
        if self.get_ndimensions() < nfields:
            self.add_value('col%d' % (self.get_ndimensions() + 1))

        # If types are not specified assume all except one are coordinates
        if self.get_ncoordinates() == 0 and nfields > 1:
            self._ncoordinates = nfields - 1
            self._nvalues = 1

### Set array data

    def set_data(self, data):
        '''
        Set data, can be a numpy.array or a list / tuple. The latter will be
        converted to a numpy.array.
        '''

        if not isinstance(data, numpy.ndarray):
            data = numpy.array(data)
        self._data = data
        self._inmem = True
        self._infile = False
        self._npoints = len(self._data)
        self._block_sizes = []

        # Add dimension information
        if len(data.shape) == 1:
            self.add_value('Y')
        elif len(data.shape) == 2:
            if data.shape[1] == 2:
                self.add_coordinate('X')
                self.add_value('Y')
            elif data.shape[1] == 3:
                self.add_coordinate('X')
                self.add_coordinate('Y')
                self.add_value('Z')
            else:
                for i in range(data.shape[1] - 1):
                    self.add_coordinate('col%d' % (i + 1))
                self.add_value('col%d' % data.shape[1])

            try:
                self._detect_dimensions_size()
            except Exception, e:
                logging.warning('Error while detecting dimension size')

            # For more than 2 dimensions also look at detected size
            if self.get_ndimensions() > 2:
                for info in reversed(self._dimensions[2:]):
                    # More likely to be a value than a coordinate
                    if 'size' in info:
                        if info['size'] == 0:
                            self._ncoordinates -= 1
                            self._nvalues += 1
                            info['type'] = 'value'
                            del info['size']
                        else:
                            break

    def update_data(self, data):
        '''
        Update this Data object with a new data set.
        No checks are performed on dimensions etc.
        If the data is associated with a temporary file, it will be updated.
        '''
        self._data = data
        if self._tempfile:
            self.rewrite_tempfile()

### File reading

    def _count_coord_val_dims(self):
        self._ncoordinates = 0
        self._nvalues = 0
        for info in self._dimensions:
            if info.get('type', 'coordinate') == 'coordinate':
                self._ncoordinates += 1
            else:
                self._nvalues += 1
        if self._nvalues == 0 and self._ncoordinates > 0:
            self._nvalues = 1
            self._ncoordinates -= 1

    def _load_file(self):
        """
        Load data from file and store internally.
        """

        try:
            f = file(self.get_filepath(), 'r')
        except:
            logging.warning('Unable to open file %s' % self.get_filepath())
            return False

        self._dimensions = []
        self._values = []
        self._comment = []
        data = []
        nfields = 0

        self._block_sizes = []
        self._npoints = 0
        self._npoints_last_block = 0
        self._npoints_max_block = 0

        blocksize = 0

        for line in f:
            line = line.rstrip(' \n\t\r')

            # Count blocks
            if len(line) == 0 and len(data) > 0:
                self._block_sizes.append(blocksize)
                if blocksize > self._npoints_max_block:
                    self._npoints_max_block = blocksize
                blocksize = 0

            # Strip comment
            commentpos = line.find('#')
            if commentpos != -1:
                self._parse_meta_data(line)
                line = line[:commentpos]

            fields = line.split()
            if len(fields) > nfields:
                nfields = len(fields)

            fields = [float(f) for f in fields]
            if len(fields) > 0:
                data.append(fields)
                blocksize += 1

        self._add_missing_dimensions(nfields)
        self._count_coord_val_dims()

        self._data = numpy.array(data)
        self._npoints = len(self._data)
        self._inmem = True

        self._npoints_last_block = blocksize

        try:
            self._detect_dimensions_size()
        except Exception, e:
            logging.warning('Error while detecting dimension size')

        return True

    def _type_added(self, name):
        if name == 'coordinate':
            self._ncoordinates += 1
        elif name == 'values':
            self._nvalues += 1

    def _parse_meta_data(self, line):
        m = self._META_STEPRE.match(line)
        if m is not None:
            self._dimensions.append({'size': int(m.group(1))})
            return True

        m = self._META_COLRE.match(line)
        if m is not None:
            index = int(m.group(1))
            if index > len(self._dimensions):
                self._dimensions.append({})
            return True

        colnum = len(self._dimensions) - 1

        for tagname, metainfo in self._METADATA_INFO.iteritems():
            m = metainfo['re'].match(line)
            if m is not None:
                if metainfo['type'] == types.FloatType:
                    self._dimensions[colnum][tagname] = float(m.group(1))
                elif metainfo['type'] == types.IntType:
                    self._dimensions[colnum][tagname] = int(m.group(1))
                else:
                    try:
                        self._dimensions[colnum][tagname] = eval(m.group(1))
                    except:
                        self._dimensions[colnum][tagname] = m.group(1)

                if 'function' in metainfo:
                    metainfo['function'](self, m.group(1))

                return True

        m = self._META_COMMENTRE.match(line)
        if m is not None:
            self._comment.append(m.group(1))

    def _reshape_data(self):
        '''
        Return a reshaped version of the data. This is not guaranteed to be
        a view to the same data object.
        '''

        if self._reshaped_data is not None:
            return self._reshaped_data

        loopdims = copy.copy(self._loopdims)
        newshape = copy.copy(self._loopshape)
        if not self._complete or None in (loopdims, newshape):
            return None

        data = self._data

        cshape_ok, fshape_ok = True, True
        for i in range(len(loopdims)):
            if loopdims[i] != i:
                fshape_ok = False
            if loopdims[i] != len(loopdims) - i -1:
                cshape_ok = False

        if not cshape_ok and not fshape_ok:
            logging.warning('Unable to do simple data reshape')
        else:
            newshape.reverse()
            newshape.append(-1)
            data = data.reshape(newshape)

            # Swap axes if necessary
            if fshape_ok:
                for i in range(self.get_ncoordinates() - 1):
                    data = data.swapaxes(i, i + 1)

        self._reshaped_data = data
        return self._reshaped_data

    def _detect_dimensions_size(self):
        data = self._data
        ncoords = self.get_ncoordinates()
        if len(data) < 2:
            for colnum in range(ncoords):
                self._dimensions[colnum]['size'] = len(data)
            return

        loopdims = []
        newshape = []
        mulsize = 1
        firstloopdim = None
        for iter in range(ncoords):
            loopdim = None
            for colnum in range(ncoords):
                if mulsize >= len(data):
                    continue

                if data[0, colnum] != data[mulsize, colnum]:
                    loopdim = colnum
                    loopdims.append(loopdim)
                    loopstart = data[0, loopdim]
                    break

            if loopdim is None:
                break

            if firstloopdim is None:
                firstloopdim = loopdim

            i = 1
            while i * mulsize < len(data):
                if data[i * mulsize, loopdim] == loopstart:
                    break
                i += 1

            opt = self._dimensions[loopdim]
            opt['start'] = loopstart
            opt['size'] = i
            opt['end'] = data[mulsize * (i - 1), loopdim]
            newshape.append(i)

            mulsize *= i

        complete = len(self._data) == mulsize
        self._loopdims = loopdims
        self._loopshape = newshape
        self._complete = complete

        # Determine number of blocks
        bs = self._dimensions[firstloopdim]['size']
        if bs > 0:
            if len(data) % bs == 0:
                self._block_sizes = [bs] * (len(data) / bs)
            else:
                self._block_sizes = [bs] * (int(len(data) / bs) + 1)

        return complete

    def set_filepath(self, fp, inmem=True):
        '''
        Set the filepath associated with the data.
        If inmem is True it will be loaded directly.
        If fp is a directory, a file with extension .dat will be searched for.
        '''

        if os.path.isdir(fp):
            files = os.listdir(fp)
            foundfile = None
            for fn in files:
                if os.path.splitext(fn)[1] == '.dat':
                    if foundfile is not None:
                        raise ValueError('Multiple .dat files in directory, Unable to decide which one to load')
                    foundfile = fn
            if foundfile is None:
                raise ValueError('No .dat file found in directory')

            self._dir, self._filename = fp, foundfile

        else:
            self._dir, self._filename = os.path.split(fp)

        if inmem:
            if self._load_file():
                self._inmem = True
            else:
                self._inmem = False

### Misc

    def _stop_request_cb(self, sender):
        '''Called when qtflow emits a stop-request.'''
        self.close_file()

    @staticmethod
    def get_named_list():
        return Data._data_list

    @staticmethod
    def get(name):
        return Data._data_list.get(name)

def slice(data, coords, vals):
    """
    Return new data object with a slice of the given data set
    """
