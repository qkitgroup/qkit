# ADwinProII_SMU.py driver for using ADwin Pro II as an SMU
# Author: Marius Frohn (uzrfo@student.kit.edu)
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

import logging, time
from qkit.core.instrument_base import Instrument
import numpy as np
from typing import Callable
from  qkit.drivers.ADwinProII_Base import ADwinProII_Base

class ADwinProII_DoubleSweep(Instrument):
    def __init__(self, name: str, adw_base: ADwinProII_Base, proc_path="C:\\ADwin\\SMU_DoubleSweep.TC3"):
        Instrument.__init__(self, name, tags=["virtual"])
        self.proc_num = int(proc_path[-1])
        self.adw = adw_base.adw
        self.dac1_channel = 2
        self.dac2_channel = 3
        self.adc1_channel = 2
        self.adc2_channel = 3
        self.adc1_card = 1 # 1 (normal), 2 (filtered)
        self.adc2_card = 1 # 1 (normal), 2 (filtered)
        self.delay = 2000 # NOTE: int describing to be slept time inbetween dac set and adc get. 
        # slept time <=> self.delay * 1e-8 s, set/get commands take ~2e-6 s per point on their own always
        self.adw.Load_Process(proc_path)
        logging.info("Loaded process '{}' for ADwinProII's FPGA".format(proc_path))

    def double_sweep(self, v1: np.ndarray, v2: np.ndarray, update_sweep_device: Callable[[], bool] = lambda: True):
        if update_sweep_device():
            self.set_sweep_parameters(v1, v2)
        self.adw.Start_Process(self.proc_num)
        while self.adw.Process_Status(self.proc_num):
            time.sleep(0.1)
        nops = self.adw.Get_Par(41)
        return ADwinProII_Base._to_volt(self.adw.GetData_Long(3, 1, nops)), ADwinProII_Base._to_volt(self.adw.GetData_Long(4, 1, nops)), ADwinProII_Base._to_volt(self.adw.GetData_Long(5, 1, nops)), ADwinProII_Base._to_volt(self.adw.GetData_Long(6, 1, nops))

    def set_sweep_parameters(self, v1: np.ndarray, v2: np.ndarray):
        # Skip checks here; if you use this, you'll know what you're doing because you're me
        self.adw.Set_Par(41, len(v1))
        self.adw.Set_Par(42, self.dac1_channel)
        self.adw.Set_Par(43, self.dac2_channel)
        self.adw.Set_Par(44, self.adc1_channel)
        self.adw.Set_Par(45, self.adc1_card)
        self.adw.Set_Par(46, self.adc2_channel)
        self.adw.Set_Par(47, self.adc2_card)
        self.adw.Set_Par(48, int(self.delay))
        self.adw.SetData_Long(ADwinProII_Base._to_reg(v1), 3, 1, len(v1))
        self.adw.SetData_Long(ADwinProII_Base._to_reg(v2), 4, 1, len(v1))

class InitHandler(object):
    def __init__(self):
        self.not_called_yet = True
    def __call__(self):
        if self.not_called_yet:
            self.not_called_yet = False
            return True
        return False