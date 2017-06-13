# qtrun.py, scripts for measurements including script copying
# Reinier Heeres <reinier@heeres.eu>, 2008-2009
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
import shutil
import copy
from lib import calltimer

def qtrun(filepath, name=''):
    if not os.path.isfile(filepath):
        raise ValueError("file '%s' does not exist" % filepath)

    dir, filename = os.path.split(filepath)
    name, ext = os.path.splitext(filename)

    if ext != '.py':
        raise ValueError("file '%s' is not of type .py" % filepath)

    data = qt.data[name]
    data.create_datafile(name)
    tstr_filename = data.get_filename() + '.py'
    fulldir = data.get_fulldir()

    if os.path.isfile(tstr_filename):
        raise ValueError("file '%s' already exists, could not copy" % tstr_filename)
    shutil.copy(filepath, fulldir + '/' + tstr_filename)

    try:
        fn = fulldir + '/' + tstr_filename

        # Make sure we don't mess up our globals
        gvars = copy.copy(globals())
        execfile(fn, gvars)
    except Exception, e:
        data.close_datafile()
        print '\n    => Measurement Aborted: %s <=' % e
    finally:
        data.close_datafile()

def qtrun_thread(filepath, name=''):
    '''
    Run a script using qtrun() in a separate thread.
    '''

    if config.get('threading_warning', True):
        logging.warning('Using threading functions could result in QTLab becoming unstable!')

    calltimer.ThreadCall(qtrun, filepath, name)
