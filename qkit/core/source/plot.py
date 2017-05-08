# plot.py, abstract plotting classes
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
import logging
import os
import time
import types
import numpy

from lib.config import get_config
config = get_config()

from data import Data
from lib import namedlist
from lib.misc import get_dict_keys
from lib.network.object_sharer import SharedGObject, cache_result

def _convert_arrays(args):
    args = list(args)
    for i in range(len(args)):
        if type(args[i]) in (types.ListType, types.TupleType):
            args[i] = numpy.array(args[i])
    return args

class _PlotList(namedlist.NamedList):
    def __init__(self):
        namedlist.NamedList.__init__(self, base_name='plot')

    def add(self, name, item):
        '''Add an item to the list.'''
        if name in self._list:
            self.remove(name, send_quit=False)
        self._list[name] = item
        self._last_item = item
        self.emit('item-added', name)

    def remove(self, name, send_quit=True):
        '''Remove a plot (should be cleared and closed).'''
        if name in self:
            self[name].clear()
            if send_quit:
                self[name].quit()
        namedlist.NamedList.remove(self, name)

class Plot(SharedGObject):
    '''
    Base class / interface for plot implementations.

    Implementing _do_update will make sure the plot is updated when new data
    is available (only when the global qt auto_update flag is set and the
    plot was last updated longer than mintime (sec) ago.
    '''

    _plot_list = _PlotList()

    def __init__(self, *args, **kwargs):
        '''
        Create a plot object.

        args input:
            data objects (Data)
            filenames (string)

        kwargs input:
            name (string), default will be 'plot<n>'
            maxpoints (int), maximum number of points to show, default 10000
            maxtraces (int), maximum number of traces to show, default 5
            mintime (int, seconds), default 1
            autoupdate (bool), default None, which means listen to global
            needtempfile (bool), default False. Whether the plot needs data
            in a temporary file.
            supportbin (bool), default False. Whether the temporary file can
            be in binary format.
        '''

        maxpoints = kwargs.get('maxpoints', 10000)
        maxtraces = kwargs.get('maxtraces', 5)
        mintime = kwargs.get('mintime', 1)
        autoupdate = kwargs.get('autoupdate', None)
        needtempfile = kwargs.get('needtempfile', False)
        supportbin = kwargs.get('supportbin', False)
        name = kwargs.get('name', '')
        self._name = Plot._plot_list.new_item_name(self, name)
        SharedGObject.__init__(self, 'plot_%s' % self._name, replace=True)

        self._data = []

        # Plot properties, things such as maxpoints might be migrated here.
        self._properties = {}

        self._maxpoints = maxpoints
        self._maxtraces = maxtraces
        self._mintime = mintime
        self._autoupdate = autoupdate
        self._needtempfile = needtempfile
        self._supportbin = supportbin

        self._last_update = 0
        self._update_hid = None

        data_args = get_dict_keys(kwargs, ('coorddim', 'coorddims', 'valdim',
            'title', 'offset', 'ofs', 'traceofs', 'surfofs'))
        data_args['update'] = False
        data_args['setlabels'] = False
        self.add(*args, **data_args)

        Plot._plot_list.add(self._name, self)

    def get_name(self):
        '''Get plot name.'''
        return self._name

    _ADD_DATA_PLOT_OPTS = set((
        'xrange', 'yrange', 'zrange',
    ))

    def add_data(self, data, **kwargs):
        '''Add a Data class with options to the plot list.'''

        # Extract options that apply to the global plot
        plot_opts = self._ADD_DATA_PLOT_OPTS & set(kwargs.keys())
        for key in plot_opts:
            val = kwargs.pop(key)
            self.set_property(key, val)

        kwargs['data'] = data
        kwargs['new-data-point-hid'] = \
                data.connect('new-data-point', self._new_data_point_cb)
        kwargs['new-data-block-hid'] = \
                data.connect('new-data-block', self._new_data_block_cb)

        if 'title' not in kwargs:
            coorddims = kwargs['coorddims']
            valdim = kwargs['valdim']
            kwargs['title'] = data.get_title(coorddims, valdim)

        # Enable y2tics if plotting or right axis and not explicitly disabled
        if kwargs.get('right', False):
            if self.get_property('y2tics', None) is None:
                self.set_property('y2tics', True)

        self._data.append(kwargs)

    def add_file(self, filename, **kwargs):
        kwargs['file'] = filename
        self._data.append(kwargs)

    def set_mintime(self, t):
        self._mintime = t

    def get_mintime(self):
        return self._mintime

    def set_maxtraces(self, n):
        self._maxtraces = n

    def get_maxtraces(self):
        return self._maxtraces

    def set_maxpoints(self, n):
        self._maxpoints = n

    def get_maxpoints(self):
        return self._maxpoints

    def set_property(self, prop, val, update=False):
        self._properties[prop] = val
        if update:
            self.update()

    def get_property(self, prop, default=None):
        return self._properties.get(prop, default)

    def get_properties(self):
        return self._properties

    def set_properties(self, props, update=True):
        for key, val in props.iteritems():
            self.set_property(key, val, update=False)
        if update:
            self.update()

    # Predefined properties, actual handling needs to be implemented in
    # the set_property() function of the implementation class.

    def set_xlabel(self, val, update=True):
        '''Set label for left x axis.'''
        self.set_property('xlabel', val, update=update)

    def set_x2label(self, val, update=True):
        '''Set label for right x axis.'''
        self.set_property('x2label', val, update=update)

    def set_ylabel(self, val, update=True):
        '''Set label for bottom y axis.'''
        self.set_property('ylabel', val, update=update)

    def set_y2label(self, val, update=True):
        '''Set label for top y axis.'''
        self.set_property('y2label', val, update=update)

    def set_zlabel(self, val, update=True):
        '''Set label for z/color axis.'''
        self.set_property('zlabel', val, update=update)

    def set_cblabel(self, val, update=True):
        '''Set label for z/color axis.'''
        self.set_property('cblabel', val, update=update)

    def set_xlog(self, val, update=True):
        '''Set log scale on left x axis.'''
        self.set_property('xlog', val, update=update)

    def set_x2log(self, val, update=True):
        '''Set log scale on right x axis.'''
        self.set_property('x2log', val, update=update)

    def set_ylog(self, val, update=True):
        '''Set log scale on bottom y axis.'''
        self.set_property('ylog', val, update=update)

    def set_y2log(self, val, update=True):
        '''Set log scale on top y axis.'''
        self.set_property('y2log', val, update=update)

    def set_xtics(self, val, update=True):
        '''Enable/disable tics on left x axis.'''
        self.set_property('xtics', val, update=update)

    def set_x2tics(self, val, update=True):
        '''Enable/disable tics on right x axis.'''
        self.set_property('x2tics', val, update=update)

    def set_ytics(self, val, update=True):
        '''Enable/disable tics on bottom y axis.'''
        self.set_property('ytics', val, update=update)

    def set_y2tics(self, val, update=True):
        '''Enable/disable tics on top y axis.'''
        self.set_property('y2tics', val, update=update)

    def set_ztics(self, val, update=True):
        '''Enable/disable tics on z axis.'''
        self.set_property('ztics', val, update=update)

    # Implementation classes need to implement set_range()

    def set_xrange(self, minval=None, maxval=None, update=True):
        '''Set left x axis range, None means auto.'''
        self.set_range('x', minval, maxval, update=update)

    def set_x2range(self, minval=None, maxval=None, update=True):
        '''Set right x axis range, None means auto.'''
        self.set_range('x2', minval, maxval, update=update)

    def set_yrange(self, minval=None, maxval=None, update=True):
        '''Set bottom y axis range, None means auto.'''
        self.set_range('y', minval, maxval, update=update)

    def set_y2range(self, minval=None, maxval=None, update=True):
        '''Set top y axis range, None means auto.'''
        self.set_range('y2', minval, maxval, update=update)

    def set_zrange(self, minval=None, maxval=None, update=True):
        '''Set z axis range, None means auto.'''
        self.set_range('z', minval, maxval, update=update)

    def clear(self):
        '''Clear the plot and remove all data items.'''

        logging.info('Clearing plot %s...', self._name)
        while len(self._data) > 0:
            info = self._data[0]
            if 'new-data-point-hid' in info:
                info['data'].disconnect(info['new-data-point-hid'])
            if 'new-data-block-hid' in info:
                info['data'].disconnect(info['new-data-block-hid'])
            del self._data[0]

    def quit(self):
        '''Close back-end, override in implementation'''
        pass

    def set_title(self, val):
        '''Set the title of the plot window. Override in implementation.'''
        pass

    def add_legend(self, val):
        '''Add a legend to the plot window. Override in implementation.'''
        pass

    def update(self, force=True, **kwargs):
        '''
        Update the plot.

        Input:
            force (bool): if True force an update, else check whether we
                would like to autoupdate and whether the last update is longer
                than 'mintime' ago.
        '''

        dt = time.time() - self._last_update

        if not force and self._autoupdate is not None and not self._autoupdate:
            return

        if self._update_hid is not None:
            if force:
                gobject.source_remove(self._update_hid)
                self._update_hid = None
            else:
                return

        cfgau = config.get('live-plot', True)
        if force or (cfgau and dt > self._mintime):
            if self.is_busy():
                self._queue_update(force=force, **kwargs)
                return

            self._last_update = time.time()
            self._do_update(**kwargs)

        # Auto-update later
        elif cfgau:
            self._queue_update(force=force, **kwargs)

    def _queue_update(self, force=False, **kwargs):
        if self._update_hid is not None:
            return
        self._update_hid = gobject.timeout_add(int(self._mintime * 1000),
                self._delayed_update, force, **kwargs)

    def _delayed_update(self, force=True, **kwargs):
        self._update_hid = None
        self.update(force=force, **kwargs)
        return False

    def _new_data_point_cb(self, sender):
        try:
            self.update(force=False)
        except Exception, e:
            logging.warning('Failed to update plot %s: %s', self._name, str(e))

    def _new_data_block_cb(self, sender):
        self.update(force=False)

    def set_maxpoints(self, val):
        self._maxpoints = val

    @staticmethod
    def get_named_list():
        return Plot._plot_list

    @staticmethod
    def get(name):
        return Plot._plot_list[name]

    def get_needtempfile(self):
        '''Return whether this plot type needs temporary files.'''
        return self._needtempfile

    def get_support_binary(self):
        '''Return whether this plot supports binary files.'''
        return self._supportbin

    def is_busy(self):
        '''Return whether the graph is being updated.'''
        return False

    def _process_plot_options(self, kwargs):
        clear = kwargs.pop('clear', False)
        if clear:
            self.clear()

        opts = ('xlabel', 'x2label', 'ylabel', 'y2label', 'zlabel', \
                'xtics', 'x2tics', 'ytics', 'y2tics', 'ztics', \
                'cblabel', 'legend', 'plottitle', 'grid')

        for key in opts:
            if key in kwargs:
                self.set_property(key, kwargs.pop(key), update=False)

        if 'style' in kwargs:
            self.set_style(kwargs.pop('style'), update=False)

class Plot2DBase(Plot):
    '''
    Abstract base class for a 2D plot.
    Real implementations should at least implement:
        - set_xlabel(self, label)
        - set_ylabel(self, label)
    '''

    def __init__(self, *args, **kwargs):
        Plot.__init__(self, *args, **kwargs)

    @cache_result
    def get_ndimensions(self):
        return 2

    def add_data(self, data, coorddim=None, valdim=None, **kwargs):
        '''
        Add Data object to 2D plot.

        Input:
            data (Data):
                Data object
            coorddim (int):
                Which coordinate column to use (0 by default)
            valdim (int):
                Which value column to use for plotting (0 by default)
        '''

        if coorddim is None:
            ncoord = data.get_ncoordinates()
            #FIXME: labels
            if ncoord == 0:
                coorddims = ()
            else:
                coorddims = (0,)
                if ncoord > 1:
                    logging.info('Data object has multiple coordinates, using the first one')
        else:
            coorddims = (coorddim,)

        if valdim is None:
            if data.get_nvalues() > 1:
                logging.info('Data object has multiple values, using the first one')
            valdim = data.get_ncoordinates()

        kwargs['coorddims'] = coorddims
        kwargs['valdim'] = valdim
        Plot.add_data(self, data, **kwargs)

    def add(self, *args, **kwargs):
        '''
        Add data object or list / numpy.array to the current plot.
        '''

        args = _convert_arrays(args)
        coorddim = kwargs.pop('coorddim', None)
        globalx = kwargs.pop('x', None)
        valdim = kwargs.pop('valdim', None)
        update = kwargs.pop('update', True)
        self._process_plot_options(kwargs)

        i = 0
        while i < len(args):

            # This is easy
            if isinstance(args[i], Data):
                data = args[i]
                i += 1

            elif isinstance(args[i], numpy.ndarray):
                if len(args[i].shape) == 1:
                    if globalx is not None:
                        y = args[i]
                        data = numpy.column_stack((globalx, y))
                        i += 1
                    elif i + 1 < len(args) and type(args[i+1]) is numpy.ndarray:
                        x = args[i]
                        y = args[i + 1]
                        if 'yerr' in kwargs:
                            data = numpy.column_stack((x, y, kwargs['yerr']))
                            if valdim is None:
                                valdim = 1
                        else:
                            data = numpy.column_stack((x, y))
                        i += 2
                    else:
                        data = args[i]
                        i += 1

                elif len(args[i].shape) == 2 and args[i].shape[1] == 2:
                    data = args[i]
                    i += 1

                else:
                    logging.warning('Unable to plot array of shape %r',
                            (args[i].shape))
                    i += 1
                    continue

                tmp = self.get_needtempfile()
                if not self.get_support_binary():
                    kwargs['binary'] = False
                elif 'binary' not in kwargs:
                    kwargs['binary'] = True
                if 'yerr' in kwargs:
                    kwargs['yerrdim'] = 2
                data = Data(data=data, tempfile=tmp, binary=kwargs['binary'])

            else:
                logging.warning('Unhandled argument: %r', args[i])
                i += 1
                continue

            # data contains a valid data object, add some options and plot it
            opts = _get_plot_options(i, *args)
            for key, val in opts.iteritems():
                kwargs[key] = val
            i += len(opts)

            self.add_data(data, coorddim=coorddim, valdim=valdim, **kwargs)

        if update:
            self.update()

    def set_labels(self, left='', bottom='', right='', top='', update=True):
        for datadict in self._data:
            data = datadict['data']
            if len(datadict['coorddims']) > 0:
                if 'top' in datadict and top == '':
                    top = data.format_label(datadict['coorddims'][0])
                elif bottom == '':
                    bottom = data.format_label(datadict['coorddims'][0])

            if 'right' in datadict and right == '':
                right = data.format_label(datadict['valdim'])
            elif left == '':
                 left = data.format_label(datadict['valdim'])

        if left == '':
            left = 'Y'
        self.set_ylabel(left, update=False)
        self.set_y2label(right, update=False)
        if bottom == '':
            bottom = 'X'
        self.set_xlabel(bottom, update=False)
        self.set_x2label(top, update=False)

        if update:
            self.update()

class Plot3DBase(Plot):
    '''
    Abstract base class for a 3D plot.
    Real implementations should at least implement:
        - set_xlabel(self, label)
        - set_ylabel(self, label)
        - set_zlabel(self, label)
    '''

    def __init__(self, *args, **kwargs):
        if 'mintime' not in kwargs:
            kwargs['mintime'] = 2
        Plot.__init__(self, *args, **kwargs)

    @cache_result
    def get_ndimensions(self):
        return 3

    def add_data(self, data, coorddims=None, valdim=None, **kwargs):
        '''
        Add data to 3D plot.

        Input:
            data (Data):
                Data object
            coorddim (tuple(int)):
                Which coordinate columns to use ((0, 1) by default)
            valdim (int):
                Which value column to use for plotting (0 by default)
        '''

        if coorddims is None:
            if data.get_ncoordinates() > 2:
                logging.info('Data object has multiple coordinates, using the first two')
            coorddims = (0, 1)

        if valdim is None:
            if data.get_nvalues() > 1:
                logging.info('Data object has multiple values, using the first one')
            valdim = data.get_ncoordinates()
            if valdim < 2:
                valdim = 2

        Plot.add_data(self, data, coorddims=coorddims, valdim=valdim, **kwargs)

    def add(self, *args, **kwargs):
        '''
        Add data object or list / numpy.array to the current plot.
        '''

        args = _convert_arrays(args)
        coorddims = kwargs.pop('coorddims', None)
        valdim = kwargs.pop('valdim', None)
        globalxy = kwargs.pop('xy', None)
        globalx = kwargs.pop('x', None)
        globaly = kwargs.pop('y', None)
        update = kwargs.pop('update', True)
        self._process_plot_options(kwargs)

        i = 0
        while i < len(args):

            # This is easy
            if isinstance(args[i], Data):
                data = args[i]
                i += 1

            elif isinstance(args[i], numpy.ndarray):
                if len(args[i].shape) == 1:
                    if globalx is not None and globaly is not None:
                        z = args[i]
                        data = numpy.column_stack((globalx, globaly, z))
                        i += 1
                    elif globalxy is not None:
                        z = args[i]
                        data = numpy.column_stack((globalxy, z))
                        i += 1
                    elif i + 2 < len(args) and \
                            type(args[i+1]) is numpy.ndarray and \
                            type(args[i+2]) is numpy.ndarray:
                        x = args[i]
                        y = args[i + 1]
                        z = args[i + 2]
                        data = numpy.column_stack((x, y, z))
                        i += 3
                    else:
                        data = args[i]
                        i += 1

                elif len(args[i].shape) == 2 and args[i].shape[1] >= 3:
                    data = args[i]
                    i += 1

                else:
                    logging.warning('Unable to plot array of shape %r', \
                            (args[i].shape))
                    i += 1
                    continue

                tmp = self.get_needtempfile()
                if not self.get_support_binary():
                    kwargs['binary'] = False
                elif 'binary' not in kwargs:
                    kwargs['binary'] = True
                data = Data(data=data, tempfile=tmp, binary=kwargs['binary'])

            else:
                logging.warning('Unhandled argument: %r', args[i])
                i += 1
                continue

            # data contains a valid data object, add some options and plot it
            opts = _get_plot_options(i, *args)
            for key, val in opts.iteritems():
                kwargs[key] = val
            i += len(opts)

            self.add_data(data, coorddims=coorddims, valdim=valdim, **kwargs)

        if update:
            self.update()

    def set_labels(self, x='', y='', z='', update=True):
        '''
        Set labels in the plot. Use x, y and z if specified, else let the data
        object create the proper format for each dimensions
        '''

        for datadict in self._data:
            data = datadict['data']
            if x == '' and len(datadict['coorddims']) > 0:
                x = data.format_label(datadict['coorddims'][0])
            if y == '' and len(datadict['coorddims']) > 1:
                y = data.format_label(datadict['coorddims'][1])
            if z == '':
                z = data.format_label(datadict['valdim'])

        if x == '':
            x = 'X'
        self.set_xlabel(x, update=False)
        if y == '':
            y = 'Y'
        self.set_ylabel(y, update=False)
        if z == '':
            z = 'Z'
        self.set_zlabel(z, update=False)
        self.set_cblabel(z, update=False)

        if update:
            self.update()

def _get_plot_options(i, *args):
    if len(args) > i:
        if type(args[i]) is types.StringType:
            return {'style': args[i]}
    return {}

def set_global_plot_options(graph, kwargs):
    if 'maxtraces' in kwargs:
        graph.set_maxtraces(kwargs.pop('maxtraces'))
    if 'maxpoints' in kwargs:
        graph.set_maxpoints(kwargs.pop('maxpoints'))

def plot(*args, **kwargs):
    '''
    Plot items.

    Variable argument input:
        Data object(s)
        numpy array(s), size n x 1 (two n x 1 arrays to represent x and y),
            or n x 2
        color string(s), such as 'r', 'g', 'b'

    Keyword argument input:
        name (string): the plot name to use, defaults to 'plot'
        coorddim, valdim: specify coordinate and value dimension for Data
            object.
        ret (bool): whether to return plot object (default: True).
    '''

    plotname = kwargs.pop('name', 'plot')
    ret = kwargs.pop('ret', True)
    graph = Plot._plot_list[plotname]
    if graph is None:
        graph = Plot2D(name=plotname)

    set_global_plot_options(graph, kwargs)

    graph.add(*args, **kwargs)

    if ret:
        return graph

def waterfall(*args, **kwargs):
    '''
    Create a waterfall plot, e.g. 3D data as offseted 2D lines.
    '''
    traceofs = kwargs.get('traceofs', 10)
    kwargs['traceofs'] = traceofs
    return plot(*args, **kwargs)

def plot3(*args, **kwargs):
    '''
    Plot items.

    Variable argument input:
        Data object(s)
        numpy array(s), size n x 1 (three n x 1 arrays to represent x, y and
            z), or n x 3
        color string(s), such as 'r', 'g', 'b'

    Keyword argument input:
        name (string): the plot name to use, defaults to 'plot'
        coorddims, valdim: specify coordinate and value dimensions for Data
            object.
        ret (bool): whether to return plot object (default: True).
    '''

    plotname = kwargs.pop('name', 'plot3d')
    ret = kwargs.pop('ret', True)
    graph = Plot._plot_list[plotname]
    if graph is None:
        graph = Plot3D(name=plotname)

    set_global_plot_options(graph, kwargs)

    graph.add(*args, **kwargs)

    if ret:
        return graph

def replot_all():
    '''
    replot all plots in the plot-list
    '''
    plots = Plot.get_named_list()
    for p in plots:
        plots[p].update()

if config.get('plot_type', 'gnuplot') == 'matplotlib':
    from plot_engines.qtmatplotlib import Plot2D, Plot3D
else:
    from plot_engines.qtgnuplot import Plot2D, Plot3D, plot_file
