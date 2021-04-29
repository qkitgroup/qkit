# spin_tune.py intented for use with a voltage source and an arbitrary I-V-device or lockin
# JF@KIT 04/2021

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
################################################################## Julian Added
import qkit
import qkit.measure.measurement_base as mb
from qkit.gui.notebook.Progress_Bar import Progress_Bar
################################################################## Old

import numpy as np


##################################################################
class IV_meas(mb.MeasureBase):
    def __init__(self, exp_name = "", sample = None):
        mb.MeasureBase.__init__(self, sample)
        
        self._get_value_func = None
        self._get_tracedata_func = None
        self.qviewkit_singleInstance = False
        #self._qvk_process = Which datatype you get?
        
    def set_get_value_func(self, get_func, *args, **kwargs):
        if not callable(get_func):
            raise TypeError("%s: Cannot set %s as get_value_func. Callable object needed." % (__name__, get_func))
        self._get_value_func = lambda: get_func(*args, **kwargs)
        self._get_tracedata_func = None
        
    def set_get_tracedata_func(self, get_func, *args, **kwargs):
        if not callable(get_func):
            raise TypeError("%s: Cannot set %s as get_tracedata_func. Callable object needed." % (__name__, get_func))
        self._get_tracedata_func = lambda: get_func(*args, **kwargs)
        self._get_value_func = None
        
    def measure1D(self):
        #add useful information about the measurement
        self._measurement_object_measurement_func = "measure1D_spin_tune"
        
        pb = Progress_Bar(len(self._x_parameter.values))
        
        def create_file():
            self._prepare_measurement_file(
                    [self.Data("I", [self._x_parameter], "A")])
            self._open_qviewkit()
        
        #implement creation of save file right here?
        qkit.flow.start()
        create_file()
        try:
            for index, x_val in enumerate(self._x_parameter.values):
                self._x_parameter.set_function(x_val)
                qkit.flow.sleep(self._x_parameter.wait_time)                
                i = self._get_value_func()
                self._datasets["I"].append(i)
                pb.iterate()
        finally:
            qkit.flow.end()
            self._end_measurement()