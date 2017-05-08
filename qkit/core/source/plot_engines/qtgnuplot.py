# qtgnuplot.py, classes for plotting with gnuplot
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

import os
import time
import random
import types
import logging
import numpy as np

from lib.config import get_config
config = get_config()
from lib.namedlist import NamedList
from lib.network.object_sharer import cache_result
import plot

import gnuplotpipe


class _GnuPlotList(NamedList):

    def __init__(self):
        NamedList.__init__(self, 'plot', type=NamedList.TYPE_ACTIVE,
                shared_name='namedlist_gnuplot')

    def create(self, name):
        term = config.get('gnuplot_terminal', None)
        return gnuplotpipe.GnuplotPipe(termtitle=name,
            default_terminal=term)

    def get(self, name=''):
        '''Get Gnuplot instance from list and verify whether it's alive.'''

        item = NamedList.get(self, name)
        if item is None:
            return None

        if not item.is_alive():
            logging.warning('Gnuplot not alive, creating new instance')
            del self[name]
            item = NamedList.get(self, name)

        return item

class _QTGnuPlot():
    """
    Base class for 2D/3D QT gnuplot classes.
    """

    _SAVE_AS_TYPES = [
        'ps',
        'png',
        'jpeg',
        'svg',
    ]

    _LEGEND_POSITIONS = [
        'bottom left',
        'bottom right',
        'top left',
        'top right',
    ]

    _DATA_TYPES = {
        np.dtype('int8'): 'int8',
        np.dtype('int16'): 'int16',
        np.dtype('int32'): 'int32',
        np.dtype('int64'): 'int64',
        np.dtype('uint8'): 'uint8',
        np.dtype('uint16'): 'uint16',
        np.dtype('uint32'): 'uint32',
        np.dtype('uint64'): 'uint64',
        np.dtype('float32'): 'float32',
        np.dtype('float64'): 'float64',
    }

    _gnuplot_list = _GnuPlotList()

    _COMMAND_MAP = {
        'xlabel': 'set xlabel "%s"\n',
        'x2label': 'set x2label "%s"\n',
        'ylabel': 'set ylabel "%s"\n',
        'y2label': 'set y2label "%s"\n',
        'zlabel': 'set zlabel "%s"\n',
        'cblabel': 'set cblabel "%s"\n',

        'xlog': 'set logscale x %s\n',
        'x2log': 'set logscale x2 %s\n',
        'ylog': 'set logscale y %s\n',
        'y2log': 'set logscale y2 %s\n',
        'zlog': 'set logscale z %s\n',
        'cblog': 'set logscale cb %s\n',

        'xrange': 'set xrange [%s:%s]\n',
        'x2range': 'set x2range [%s:%s]\n',
        'yrange': 'set yrange [%s:%s]\n',
        'y2range': 'set y2range [%s:%s]\n',
        'zrange': 'set zrange [%s:%s]\n',
        'cbrange': 'set cbrange [%s:%s]\n',

        'xtics': 'set xtics\n',
        'x2tics': 'set x2tics\n',
        'ytics': 'set ytics\n',
        'y2tics': 'set y2tics\n',
        'ztics': 'set ztics\n',

        'xdata': 'set xdata %s\n',
        'x2data': 'set x2data %s\n',
        'ydata': 'set ydata %s\n',
        'y2data': 'set y2data %s\n',
        'zdata': 'set zdata %s\n',
        'cbdata': 'set cbdata %s\n',

        'timefmt': 'set timefmt %s\n',

        'grid': 'set grid\n',
        'datastyle': 'set style data %s\n',
        'legend': 'set key\n',
        'legendpos': 'set key %s\n',

        'plottitle': 'set title "%s"\n',
    }

    def __init__(self):
        name = self.get_name()
        self._gnuplot = self._gnuplot_list[name]
        self._gnuplot.set_reopen_cb(lambda x: self.reset())
        self.cmd('reset')
        self.cmd('clear')

        self._auto_suffix_counters = {}

    def create_command(self, name, val):
        '''Create command for a plot property.'''

        if name not in self._COMMAND_MAP:
            return None

        if type(val) is types.BooleanType:
            if val:
                cmd = self._COMMAND_MAP[name]
            else:
                cmd = 'un' + self._COMMAND_MAP[name]
            cmd = cmd.replace('%s', '')
        else:
            cmd = self._COMMAND_MAP[name] % val

        return cmd

    def set_property(self, name, val, update=False, **kwargs):
        '''Set a plot property value.'''

        cmd = self.create_command(name, val, **kwargs)
        if cmd is not None and cmd != '':
            self.cmd(cmd)
        return plot.Plot.set_property(self, name, val, update=update)

    def get_commands(self):
        '''Get commands for the current plot properties.'''
        cmd = ''
        for key, val in self.get_properties().iteritems():
            line = self.create_command(key, val)
            if line is not None and line != '':
                cmd += line
        return cmd

    def reset(self):
        self.cmd('reset')
        self.cmd('clear')
        self.cmd(self.get_commands())
        self.update()

    def clear(self):
        '''Clear the plot.'''
        self.cmd('clear')
        plot.Plot.clear(self)

    def quit(self):
        self.cmd('quit')

    def get_first_filepath(self):
        '''Return filepath of first data item.'''
        if len(self._data) > 0:
            return self._data[0]['data'].get_filepath()
        else:
            return ''

    def _generate_suffix(self, append_graphname=True, add_suffix=None, autosuffix=True, ext='None'):

        suffix = ''
        if append_graphname:
            suffix = '_' + self.get_name()
        if add_suffix is not None:
            suffix += '_' + str(add_suffix)
        if autosuffix:
            if not self._auto_suffix_counters.has_key(ext):
                self._auto_suffix_counters[ext] = 0
            if self._auto_suffix_counters[ext] > 0:
                suffix += '_%d' % self._auto_suffix_counters[ext]
            self._auto_suffix_counters[ext] += 1

        return suffix

    def _process_filepath(self, filepath, extension, **kwargs):

        if filepath is None:
            filepath = self.get_first_filepath()
            if filepath.startswith(config['tempdir']):
                filepath = os.getcwd()

        if os.path.isdir(filepath):
            fn = os.path.join(filepath, self.get_name())
            kwargs['append_graphname'] = False
        else:
            fn, ext = os.path.splitext(filepath)

        suffix = self._generate_suffix(ext=extension, **kwargs)
        filepath = '%s%s.%s' % (fn, suffix, extension)
        filepath = os.path.abspath(filepath)

        return filepath

    def save_as_type(self, terminal, extension, filepath=None, **kwargs):
        '''
        Save a different version of the plot.

        kwargs:
            filepath (path)     :       filepath to save to
            add_suffix (string) :       filename suffix
            autosuffix (bool)   :       auto increment suffix
            append_graphname    :       add graphname to filename
        '''

        filepath = self._process_filepath(filepath, extension, **kwargs)
        # Fix GnuPlot on windows issue
        filepath = filepath.replace('\\', '/')

        self.update()
        self._gnuplot.set_terminal(terminal)
        self._gnuplot.cmd('set output "%s"' % filepath)
        self._gnuplot.cmd('replot')
        self._gnuplot.reset_default_terminal()
        self._gnuplot.cmd('set output')
        self._gnuplot.cmd('replot')

    @cache_result
    def get_save_as_types(self):
        return _QTGnuPlot._SAVE_AS_TYPES

    def save_ps(self, filepath=None, font='Helvetica', fontsize=14, **kwargs):
        '''
        Save postscript version of the plot.

        Arguments:
            - filepath: file path + name
            - font: font name
            - fontsize: font size
        '''

        fontstring = '"%s, %s"' % (font, fontsize)
        term = 'postscript color enhanced %s' % (fontstring)
        self.save_as_type(term, 'ps', filepath=filepath, **kwargs)

    def save_eps(self, filepath=None, font='Helvetica', fontsize=14, **kwargs):
        '''
        Save encapsulated-postscript version of the plot.

        Arguments:
            - filepath: file path + name
            - font: font name
            - fontsize: font size
        '''

        fontstring = '"%s, %s"' % (font, fontsize)
        term = 'postscript eps color enhanced %s' % (fontstring)
        self.save_as_type(term, 'eps', filepath=filepath, **kwargs)

    def save_png(self, filepath=None, font='', transparent=False, **kwargs):
        '''
        Save png version of the plot.

        Arguments:
            - filepath: file path + name
            - font: font spec (either 'tiny', 'small', 'medium', 'large' or
            'giant', or font <face> <pointsize>)
            - transparent:
                - False: no transparency
                - True: white will be transparent
                - Color spec (e.g. '#808080'): the transparent color
        '''

        if transparent is False:
            transparent = ''
        else:
            if transparent is True:
                transparent = '#ffffff'
            transparent = 'transparent %s' % transparent

        self.save_as_type('png %s %s size 1024,768' % (font, transparent),
                'png', filepath=filepath, **kwargs)

    def save_jpeg(self, filepath=None, **kwargs):
        '''Save jpeg version of the plot'''
        self.save_as_type('jpeg', 'jpg', filepath=filepath, **kwargs)

    def save_svg(self, filepath=None, **kwargs):
        '''Save svg version of the plot'''
        self.save_as_type('svg', 'svg', filepath=filepath, **kwargs)

    def _write_gp(self, s, filepath=None, **kwargs):

        filepath = self._process_filepath(filepath, 'gp', **kwargs)

        f = open(filepath, 'w')
        f.write(s)
        f.close()

    def set_range(self, axis, minval, maxval, update=True):
        if minval is None or minval == '':
            minval = '*'
        if maxval is None or maxval == '':
            maxval = '*'
        cmd = '%srange' % axis
        self.set_property(cmd, (minval, maxval), update=update)

    @staticmethod
    def get_named_list():
        return _QTGnuPlot._gnuplot_list

    @staticmethod
    def get(name):
        return _QTGnuPlot._gnuplot_list.get(name)

    def _do_update(self):
        '''
        Perform an update of the plot.
        '''
        cmd = self.create_plot_command()
        self.cmd(cmd)
        return True

    def cmd(self, cmdstr):
        '''Send command to gnuplot instance directly.'''
        if self._gnuplot is not None:
            self._gnuplot.cmd(cmdstr)

    def live(self):
        self._gnuplot.live()

    def is_busy(self):
        return not self._gnuplot.is_responding()

    def set_grid(self, on=True, update=True):
        self.set_property('grid', on, update=update)

    def set_legend(self, on=True, update=True):
        self.set_property('legend', on, update=update)

    @cache_result
    def get_legend_positions(self):
        pos = self._LEGEND_POSITIONS
        pos.sort()
        return pos

    def set_legend_position(self, pos='top left', update=True):
        self.set_property('legendpos', pos, update=update)

    def set_plottitle(self, text, update=True):
        self.set_property('plottitle', text)

    def set_datastyle(self, style):
        self.set_property('datastyle', style)

    @cache_result
    def get_styles(self):
        styles = self._STYLES.keys()
        styles.sort()
        return styles

    def _check_style_options(self, datadict):
        if 'style' not in datadict:
            return
        datadict = _parse_style_string(datadict['style'], datadict)
        del datadict['style']

    def _get_trace_options(self, datadict, defaults={}):
        datadict = datadict.copy()
        for key, val in defaults.iteritems():
            if key not in datadict:
                datadict[key] = val

        s = ''
        if 'binary' in datadict and datadict['binary'] == True:
            data = datadict['data']
            dimsizes = [data.get_dimension_size(i) \
                    for i in datadict['coorddims']]
            dt = data.get_data().dtype
            fmt = (r'%' + self._DATA_TYPES[dt]) * data.get_ndimensions()
            s += " binary format='%s'" % fmt
            if len(dimsizes) == 1:
                s += " record=%d" % dimsizes[0]
            elif len(dimsizes) != 0:
                s += " record=%dx%d" % (dimsizes[0], dimsizes[1])

        if 'with' in datadict and datadict['with'] != '':
            s += ' with %s' % datadict['with']
        if 'pointtype' in datadict:
            s += ' pt %d' % datadict['pointtype']
        if 'pointsize' in datadict:
            s += ' ps %d' % datadict['pointsize']
        if 'linetype' in datadict:
            s += ' lt %d' % datadict['linetype']
        if 'linewidth' in datadict:
            s += ' lw %d' % datadict['linewidth']
        if 'color' in datadict:
            s += ' lc rgb "%s"' % datadict['color']
        if 'title' in datadict:
            s += ' title "%s"' % datadict['title']

        return s

_COLOR_MAP = {
    'b': 'blue',
    'g': 'green',
    'k': 'black',
    'm': 'magenta',
    'r': 'red',
    'y': 'yellow',
    'w': 'white',
}

_MARKER_MAP = {
    '+': 1,
    'x': 2,
    '*': 3,
    'S': 4,     # Open squares
    's': 5,     # Closed squares
    'O': 6,     # Open circles
    'o': 7,     # Closed circles
#    '': 8,     # Open triangle up
    '^': 9,     # Closed triangle up
#    '': 10,    # Open triangle down
    'v': 11,    # Closed triangle down
    'D': 12,    # Open diamond
    'd': 13,    # Closed diamond
}

def _parse_style_string(spec, opts):
    if spec == '':
        return opts

    for ch in spec:
        if ch in _COLOR_MAP:
            opts['color'] = _COLOR_MAP[ch]
        if ch in _MARKER_MAP:
            opts['pointtype'] = _MARKER_MAP[ch]
            if opts.get('with', '') not in ['yerrorbars']:
                opts['with'] = 'points'

    if '-' in spec:
        if 'with' in opts:
            opts['with'] = 'linespoints'
        else:
            opts['with'] = 'lines'

    return opts

class Plot2D(plot.Plot2DBase, _QTGnuPlot):
    '''
    Class to create line plots.
    '''

    _STYLES = {
        'lines': {'datastyle': 'lines'},
        'points': {'datastyle': 'points'},
        'linespoints': {'datastyle': 'linespoints'},
        'steps': {'datastyle': 'steps'},
        'histeps': {'datastyle': 'histeps'},
        'boxes': {'datastyle': 'boxes'},
    }

    def __init__(self, *args, **kwargs):
        kwargs['needtempfile'] = True
        kwargs['supportbin'] = config.get('gnuplot_binary', True)
        plot.Plot2DBase.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        self.set_grid(update=False)
        self.set_style('lines', update=False)

        top = kwargs.get('x2label', '')
        bottom = kwargs.get('xlabel', '')
        right = kwargs.get('y2label', '')
        left = kwargs.get('ylabel', '')
        self.set_labels(
                left=left, right=right,
                bottom=bottom, top=top,
                update=False)

        if kwargs.get('update', True):
            self.update()

    def set_property(self, *args, **kwargs):
        return _QTGnuPlot.set_property(self, *args, **kwargs)

    def add_data(self, data, *args, **kwargs):
        if 'yerrdim' in kwargs:
            kwargs['with'] = 'yerrorbars'
        plot.Plot2DBase.add_data(self, data, *args, **kwargs)

    def create_command(self, name, val):
        if name == "style":
            return ''
        else:
            return _QTGnuPlot.create_command(self, name, val)

    def set_style(self, style, update=True):
        '''Set plotting style.'''

        if style is None or style == '':
            style = config.get('gnuplot2d_style', 'lines')

        if style not in self._STYLES:
            logging.warning('Unknown style: %s', style)
            return None

        for k, v in self._STYLES[style].iteritems():
            self.set_property(k, v, update=False)
        self.set_property('style', style, update=update)

    def create_plot_command(self, fullpath=True, data_entry=None):
        '''
        Create a gnuplot plot command.
        If data_entry is given only that item will be used, otherwise
        all items are included.
        '''

        s = 'plot '
        first = True

        if data_entry is not None:
            items = [data_entry]
        else:
            items = self._data

        for datadict in items:
            if 'file' in datadict:
                if not first:
                    s += ', '
                else:
                    first = False
                s += '"%s"' % datadict['file']
                coorddim = datadict.get('coorddim', 0)
                valdim = datadict.get('valdim', 1)
                s += ' using %d:%d' % (coorddim + 1, valdim + 1)
                continue

            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']
            yerrdim = datadict.get('yerrdim', None)
            ofs = datadict.get('ofs', datadict.get('offset', 0))
            traceofs = datadict.get('traceofs', 0)
            self._check_style_options(datadict)

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            if len(coorddims) == 0:
                using = '($%d+%f+%f*column(-1))' % (valdim + 1, ofs, traceofs)
            elif len(coorddims) == 1:
                using = '%d:($%d+%f+%f*column(-1))' % (coorddims[0] + 1, valdim + 1, ofs, traceofs)
            else:
                logging.error('Need 0 or 1 coordinate dimensions!')
                continue
            if yerrdim is not None:
                using += ':%d' % (yerrdim+1)

            npoints = data.get_npoints()
            if datadict.get('with', None) in ['lines']:
                min_npoints = 2
            else:
                min_npoints = 1
            if npoints < min_npoints:
                continue

            nblocks = data.get_nblocks()
            npoints_last_block = data.get_block_size(nblocks - 1)
            if npoints_last_block < 2:
                nblocks -= 1
                npoints_last_block = data.get_block_size(nblocks - 1)

            startpoint = max(0, npoints_last_block - self._maxpoints)
            startblock = max(0, nblocks - self._maxtraces)
            if len(coorddims) == 0:
                every = "::%d" % (startpoint)
            else:
                every = '::%d:%d' % (startpoint, startblock)

            if 'top' in datadict:
                axes = 'x2'
            else:
                axes = 'x1'
            if 'right' in datadict:
                axes += 'y2'
            else:
                axes += 'y1'

            if not first:
                s += ', '
            else:
                first = False

            s += '"%s" using %s every %s' % \
                (str(filepath), using, every)
            s += self._get_trace_options(datadict)
            s += ' axes %s' % axes

        if first:
            return ''
        else:
            return s

    def save_gp(self, filepath=None, **kwargs):
        '''Save file that can be opened with gnuplot.'''
        s = self.get_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s, filepath=filepath, **kwargs)

    def is_busy(self):
        return _QTGnuPlot.is_busy(self)

    def clear(self):
        return _QTGnuPlot.clear(self)

    def quit(self):
        return _QTGnuPlot.quit(self)

class Plot3D(plot.Plot3DBase, _QTGnuPlot):
    '''
    Class to create surface plots using gnuplot.
    '''

    # For backwards compatibility
    STYLE_IMAGE = 'image'
    STYLE_3D = '3d'

    _STYLES = {
        'image': {
            'style': [
                'unset pm3d',
                'set view map',
                'set style data image',
            ],
            'splotopt': '',
        },
        'image3d': {
            'style': [
                'set pm3d map corners2color c1',
            ],
            'splotopt': 'with pm3d',
        },
        'points': {
            'style': [
                'unset pm3d',
                'set view 60,15'
            ],
            'splotopt': 'with points',
        },
        'lines': {
            'style': [
                'unset pm3d',
                'set view 60,16'
            ],
            'splotopt': 'with lines',
        },
        '3d': {
            'style': [
                'set pm3d',
                'set view 60,15',
            ],
            'splotopt': 'with pm3d',
        },
        '3dpoints' : {
            'style': [
                'set pm3d',
                'set view 60,15',
            ],
            'splotopt': 'with points',
        },
        '3dlines': {
            'style': [
                'set pm3d',
                'set view 60,15',
            ],
            'splotopt': 'with lines',
        },
    }

    _PALETTE_MAP = {
        'default': (7, 5, 15),
        'hot': (21, 22, 23),
        'ocean': (23, 28, 3),
        'rainbow': (33, 13, 10),
        'afmhot': (34, 35, 36),
        'bw': (7, 7, 7),
        'redwhiteblue': (-34, 13, 34),
        'bluewhitered': (34, 13, -34),
        'jet': (30, -13, -23),
        'hsv': 'set palette model HSV functions (gray**gamma),1,1',
        'byr': 'set palette model RGB defined ( 0 "blue", 0.5 "yellow", 1 "red")',
    }

    # Palette functions in gnuplot, so we can use them with custom gamma
    _PALETTE_FUNCTIONS = {
        0: '0',
        1: '0.5',
        2: '1',
        3: '%(x)s',
        4: '%(x)s**2',
        5: '%(x)s**3',
        6: '%(x)s**4',
        7: 'sqrt(%(x)s)',
        8: 'sqrt(sqrt(%(x)s))',
        9: 'sin(90*%(x)s*0.0174532925)',
        10: 'cos(90*%(x)s*0.0174532925)',
        11: 'abs(%(x)s-0.5)',
        12: '(2.0*%(x)s-1)*(2.0*%(x)s-1)',
        13: 'sin(180*%(x)s*0.0174532925)',
        14: 'abs(cos(180*%(x)s*0.0174532925))',
        15: 'sin(360*%(x)s*0.0174532925)',
        16: 'cos(360*%(x)s*0.0174532925)',
        17: 'abs(sin(360*%(x)s*0.0174532925))',
        18: 'abs(cos(360*%(x)s*0.0174532925))',
        19: 'abs(sin(720*%(x)s*0.0174532925))',
        20: 'abs(cos(720*%(x)s*0.0174532925))',
        21: '3*%(x)s',
        22: '3*%(x)s-1',
        23: '3*%(x)s-2',
        24: 'abs(3*%(x)s-1)',
        25: 'abs(3*%(x)s-2)',
        26: '1.5*%(x)s-0.5',
        27: '1.5*%(x)s-1',
        28: 'abs(1.5*%(x)s-0.5)',
        29: 'abs(1.5*%(x)s-1)',
        30: '%(x)s/0.32-0.78125',
        31: '2*%(x)s-0.84',
        32: '0',
        33: 'abs(2*%(x)s-0.5)',
        34: '2*%(x)s',
        35: '2*%(x)s-0.5',
        36: '2*%(x)s-1',
    }

    def __init__(self, *args, **kwargs):
        kwargs['needtempfile'] = True
        kwargs['supportbin'] = config.get('gnuplot_binary', True)
        plot.Plot3DBase.__init__(self, *args, **kwargs)
        _QTGnuPlot.__init__(self)

        style = kwargs.get('style', None)

        self.set_style(style, update=False)
        _QTGnuPlot.cmd(self, 'unset key')
        self.set_labels(update=False)
        self.set_palette('default', gamma=1.0, update=False)

        self.update()

    def set_property(self, prop, val, **kwargs):
        if prop == 'style':
            try:
                self._default_with = self._STYLES[val]['splotopt'].split(' ')[1]
            except:
                self._default_with = ''

        return _QTGnuPlot.set_property(self, prop, val, **kwargs)

    def add_data(self, data, *args, **kwargs):
        if 'palette' in kwargs:
            gamma = kwargs.pop('gamma', 1.0)
            self.set_palette(kwargs.pop('palette'), gamma, update=False)
        plot.Plot3DBase.add_data(self, data, *args, **kwargs)

    def create_command(self, name, val):
        if name == 'style':
            ret = '\n'.join(self._STYLES[val]['style']) + '\n'
            return ret

        elif name == 'palette':
            if type(val) is not types.DictType:
                logging.warning('Invalid palette properties: %s', val)
                return None

            return self._create_palette_commands(**val)

        else:
            return _QTGnuPlot.create_command(self, name, val)

    def set_style(self, style, update=True):
        '''Set plotting style.'''

        if style is None or style == '':
            style = config.get('gnuplot_style', 'image3d')

        if style not in self._STYLES:
            logging.warning('Unknown style: %s', style)
            return None

        self.set_property('style', style, update=update)

    @cache_result
    def get_palettes(self):
        '''Return available palettes.'''
        pals = Plot3D._PALETTE_MAP.keys()
        pals.sort()
        return pals

    def set_palette(self, pal, gamma=1.0, update=True):
        '''
        Set a color palette.

        Input:
            pal (string): palette name, get available ones with get_palettes()
            gamma (float): gamma correction, if gamma=1 a 'simple' gnuplot
                palette function will be used.
            update (bool): whether to update the current plot.
        '''

        if pal not in self._PALETTE_MAP:
            logging.warning('Unknown palette: %s', pal)
            return False

        self.set_property('palette', dict(name=pal, gamma=gamma), \
                update=update)

    def create_plot_command(self, fullpath=True, data_entry=None):
        '''
        Create a gnuplot splot command.
        If data_entry is given only that item will be used, otherwise
        all items are included.
        '''

        s = 'splot '
        first = True

        if data_entry is not None:
            items = [data_entry]
        else:
            items = self._data

        for datadict in items:
            if 'file' in datadict:
                s += '"%s"' % datadict['file']
                if not first:
                    s += ', '
                else:
                    first = False
                    continue

            data = datadict['data']
            coorddims = datadict['coorddims']
            valdim = datadict['valdim']
            ofs = datadict.get('ofs', datadict.get('offset', 0))
            traceofs = datadict.get('traceofs', 0)
            surfofs = datadict.get('surfofs', 0)
            self._check_style_options(datadict)

            if len(coorddims) != 2:
                logging.error('Unable to plot without two coordinate columns')
                continue

            if fullpath:
                filepath = data.get_filepath()
            else:
                filepath = data.get_filename()
            filepath = filepath.replace('\\','/')

            using = '%d:%d:($%d+%f+%f*column(-1)+%f*column(-2))' % (coorddims[0] + 1, coorddims[1] + 1, valdim + 1, ofs, traceofs, surfofs)

            style = self.get_property('style')
            if style == self.STYLE_IMAGE:
                stopblock = data.get_nblocks_complete() - 1
                if stopblock < 1:
                    #logging.warning('Unable to plot in style "image" with <=1 block')
                    continue
                everystr = 'every :::0::%s' % (stopblock)
            else:
                everystr = ''


            if not first:
                s += ', '
            else:
                first = False
            s += '"%s" using %s %s' % (str(filepath), using, everystr)

            defaults = {
                'with': self._default_with
            }
            s += self._get_trace_options(datadict, defaults)

        # gnuplot (version 4.3 november) has bug for placing keys (legends)
        # here we put ugly hack as a temporary fix
        # also remove 'unset key' in __init__ when reverting this hack
            s  = ('set label 1 "%s" at screen 0.1,0.9' % \
                    datadict.get('title', filepath)) + '\n' + s

        if first:
            return ''
        else:
            return s

    def save_gp(self, filepath=None, **kwargs):
        '''Save file that can be opened with gnuplot.'''
        s = self.get_commands()
        s += self.create_plot_command(fullpath=False)
        self._write_gp(s, filepath=filepath, **kwargs)

    def _new_data_point_cb(self, sender):
        if self.get_property('style') != self.STYLE_IMAGE:
            self.update(force=False)

    def _palette_func(self, func_id):
        if func_id >= 0:
            return self._PALETTE_FUNCTIONS[abs(func_id)] % \
                    dict(x='(gray**gamma)')
        else:
            return self._PALETTE_FUNCTIONS[abs(func_id)] % \
                    dict(x='(1-gray**gamma)')

    def _create_palette_commands(self, **kwargs):
        name = kwargs.get('name', 'default')
        gamma = kwargs.get('gamma', 1.0)

        data = self._PALETTE_MAP[name]
        cmd = ''
        if type(data) is types.TupleType and gamma == 1.0:
            cmd += 'set palette model RGB rgbformulae %d,%d,%d\n' % \
                (data[0], data[1], data[2])
        else:
            cmd += 'gamma = %f\n' % float(1/gamma)
            if type(data) is types.TupleType:
                cmd += 'rcol(gray) = %s\n' % (self._palette_func(data[0]))
                cmd += 'gcol(gray) = %s\n' % (self._palette_func(data[1]))
                cmd += 'bcol(gray) = %s\n' % (self._palette_func(data[2]))
                cmd += 'set palette model RGB functions rcol(gray), gcol(gray), bcol(gray)\n'
            else:
                cmd += data

        return cmd

    def is_busy(self):
        return _QTGnuPlot.is_busy(self)

    def clear(self):
        return _QTGnuPlot.clear(self)

    def quit(self):
        return _QTGnuPlot.quit(self)

def get_gnuplot(name=None):
    return _QTGnuPlot.get(name=name)

def get_gnuplot_list():
    return _QTGnuPlot.get_named_list()

def plot_file(filename, name='plot', update=True, clear=False, **kwargs):
    p = plot.Plot.get(name)
    if p is None:
        p = Plot2D(name=name)
    elif clear:
        p.clear()
    p.add_file(filename, **kwargs)
    if update:
        p.update()

