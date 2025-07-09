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
from  qkit.drivers.ADwinProII_Base import ADwinProII_Base

class ADwinProII_SweepLoop(Instrument):
    """
    To be used with the FPGA process 'SMU_SweepLoop.TC2', enabling SMU functionality for 
    making qkit transport script DC sweeps.
    """
    def __init__(self, name: str, adw_base: ADwinProII_Base, proc_path="C:\\ADwin\\SMU_SweepLoop.TC2"):
        Instrument.__init__(self, name, tags=["virtual"])
        self.proc_num = int(proc_path[-1])
        self.adw = adw_base.adw
        self.adw.Load_Process(proc_path)
        logging.info("Loaded process '{}' for ADwinProII's FPGA".format(proc_path))
        self.dac_channel = 1 # 1...8
        self.adc_channel = 1 # 1...4 or 1...8 depending on card
        self.adc_card = 1 # 1 (normal), 2 (filtered)
        self._sweep_channels = (self.dac_channel, self.adc_channel) # for qkit compability
        self.delay = 2000 # NOTE: int describing to be slept time inbetween dac set and adc get. 
        # slept time <=> self.delay * 1e-8 s, set/get commands take ~2e-6 s per point on their own always
    def set_sweep_parameters(self, sweep: np.ndarray) -> None:
        """
        Check to be swept parameter settings and write them to the device.
        Sweep: array describing sweep values by [start, stop, step]

        Max 2^16 points due to (arbitary) memory limitation on device (More 
        values would not make sense anyways though since the ADC/DACs have 
        only 16-bit resolution)
        Voltage range is limited to +-10V for both ADC/DACs
        Look at device for channel number limitations
        """
        # self.dac_channel, self.adc_channel = self._sweep_channels # NOTE: keep this line? potentially causes more problems with qkit defaults not fitting for this device than the feature is worth 
        set_array = np.arange(sweep[0], sweep[1] + sweep[2]/2, sweep[2])
        # Check values
        if len(set_array) > 0x1000:
            raise ValueError("Sweep size of 16 bit ADC/DACs limited to 2^16 values")
        if np.any(np.abs(set_array) > 10.0):
            raise ValueError("Sweep array contains values outside +-10V range")
        if not self.dac_channel in range(1, 9):
            raise ValueError("DAC channel must be 1...8")
        if not self.adc_card in [1, 2]:
            raise ValueError("ADC card must be 1 (normal), 2 (50kHz filtered)")
        if self.adc_card == 1 and not self.adc_channel in range(1, 5):
            raise ValueError("ADC channel must be 1...4")
        if self.adc_card == 2 and not self.adc_channel in range(1, 9):
            raise ValueError("Filtered ADC channel must be 1...8")
        # Set values
        self.adw.Set_Par(1, len(set_array))
        self.adw.Set_Par(2, self.dac_channel)
        self.adw.Set_Par(3, self.adc_channel)
        self.adw.Set_Par(4, self.adc_card)
        self.adw.Set_Par(5, int(self.delay))
        self.adw.SetData_Long(ADwinProII_Base._to_reg(set_array), 1, 1, len(set_array))
    def get_tracedata(self) -> tuple[np.ndarray]:
        """
        Starts a sweep with parameters currently set on device and returns
        set_values_array, measured_values_array. Sorting by what is I and V
        is being handled by overlaying virtual_tunnel_electronic
        """
        # Sweep
        self.adw.Start_Process(self.proc_num)
        while self.adw.Process_Status(self.proc_num):
            time.sleep(0.1)
        # Read result
        return ADwinProII_Base._to_volt(self.adw.GetData_Long(1, 1, self.adw.Get_Par(1))), ADwinProII_Base._to_volt(self.adw.GetData_Long(2, 1, self.adw.Get_Par(1)))
    # qkit SMU compability
    def set_sweep_mode(self, mode: int = 0):
        if mode != 0:
            logging.error("ADwinProII only has voltage ADC/DACs, only VV-mode 0 supported")
    def get_sweep_mode(self) -> int:
        return 0
    def get_sweep_channels(self) -> tuple[int]:
        return (self.dac_channel, self.adc_channel)
    def set_status(self, *args, **kwargs) -> None:
        pass # ADC/DACs are always responsive