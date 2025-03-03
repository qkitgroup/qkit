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
import ADwin

class ADwinProII_SMU(Instrument):
    """
    The ADwin Pro II by Jäger Computergesteuerte Messtechnik GmbH provides slots for various 
    ADC/DAC or data in/out cards as well as an accessable FPGA-like processor for control. Our
    group's device currently has a 4-channel 16-bit ADC, a 50kHz filtered 8-channel 16-bit ADC 
    and an 8-channel 16-bit DAC card. Getting the device running requires some steps outlined
    below:

    - Selecting drivers from https://www.adwin.de/de/download/download.html. Installing the 
      full software package is recommended for potential debugging, analyzing timings, etc.
    - 'pip install ADwin' to the qkit virtual environment. (Note: despite being present, the 
      driver could not correctly read out the ADwin install directory from the windows registry
      on my machine. To fix this, I commented out the entire try/except block around line ~100 
      in *venv*/site-packages/ADwin.py and hardcoded 'self.ADwindir = *adwin_install_path*')
    - The tool *adwin_install_path*/Tools/ADconfig/ADconfig.exe finds ADwin devices in the 
      network and allows e.g. assigning their MAC-addresses to a fixed IP-address. This should
      already be done for this device. In either case one still needs to register it as an 
      adwin-device on the measurement pc and assign it an adwin-device-number (default: 1)
    - With *adwin_install_path*/Tools/Test/ADpro/ADpro.exe one can check if communication with
      device is now possible & what the id-numbers of the used cards are (should be 1, 2, 3)
    - For usage one needs to provide a bootloader and to be run processes. The bootloader can 
      be found under *adwin_install_path*/ADwin12.btl for the T12 processor type. This driver 
      is in particular designed around 2 processes which configure the FPGA as a default SMU.
      If you're still reading this your problem can't be solved any other way but with this 
      box, so at this point I wish you good luck with whatever is troubling you. The already 
      compiled processes can be found as .TCx-files alongside the other files on the exchange 
      under exchange/Devices/ADwinProII/ and should be provided somewhere on the measurement pc. 

    SMU_SingleSetGet.TC1 enables ADC/DAC access by checking in regular intervals if a  
    respective action is requested. SMU_SweepLoop.TC2 is a high-priority process for sweeping 
    over a given array and reading back a given signal. The speed of one step is mostly limited 
    by the ADC/DAC access commands taking up to ~1600 CPU cycles = ~1.6e-6 s. The source code 
    for these processes is provided in the .bas-files. Alternatively one can program the FPGA 
    to do whatever one wants but then this driver obviously will no longer work with it. 
    """
    # static stuff
    ADC_CARD_OFFSET = 10
    ADC_FILTER_CARD_OFFSET = 20
    DAC_CARD_OFFSET = 30
    @staticmethod
    def _to_volt(x: np.ndarray) -> np.ndarray:
        return (x.astype(np.float64) - 0x8000) * 20.0 / 0x10000
    @staticmethod
    def _to_reg(x: np.ndarray) -> np.ndarray:
        x_reg = np.round((x + 10.0)/20.0*0x10000)
        x_reg = np.where(x_reg == -1, 0, x_reg)
        return np.where(x_reg == 0x10000, 0xFFFF, x_reg)
    
    def __init__(self, name: str, btl_path: str = "C:\\ADwin\\ADwin12.btl", proc1_path: str = "C:\\ADwin\\SMU_SingleSetGet.TC1", proc2_path: str = "C:\\ADwin\\SMU_SweepLoop.TC2", device_num: int = 1):
        """
        This is a driver for using the ADwinProII as an SMU by using the provided processes.

        Usage:
        Initialize with
        <name> = qkit.instruments.create('<name>', 'ADwinProII_SMU', **kwargs)

        Keyword arguments:
            btl_path:   path to bootloader file (default: "C:\\ADwin\\ADwin12.btl")
            proc1_path: path to process file containing low-priority ADC/DAC access
                        (default: "C:\\ADwin\\SMU_SingleSetGet.TC1")
            proc2_path: path to process file containing high-priority array sweep
                        (default: "C:\\ADwin\\SMU_SweepLoop.TC1")
            device_num: number assigned to device on your pc by ADconfig (default: 1)
        """
        # qkit stuff
        Instrument.__init__(self, name, tags=['physical'])
        self.add_parameter("adc", type = float, flags = Instrument.FLAG_GET, channels = (1, 4), minval = -10.0, maxval=10.0, units = "V")
        self.add_parameter("adc_filtered", type = float, flags = Instrument.FLAG_GET, channels = (1, 8), minval = -10.0, maxval=10.0, units = "V")
        self.add_parameter("dac", type = float, flags = Instrument.FLAG_SET, channels = (1, 8), minval = -10.0, maxval = 10.0, units = "V")
        # Boot & Load processes
        self.adw = ADwin.ADwin(device_num)
        self.adw.Boot(btl_path)
        logging.info("Booted ADwinProII with processor {}".format(self.adw.Processor_Type()))
        self.adw.Load_Process(proc1_path)
        self.adw.Start_Process(1)
        logging.info("Loaded SMU process 1 for ADwinProII's FPGA")
        self.adw.Load_Process(proc2_path)
        logging.info("Loaded SMU process 2 for ADwinProII's FPGA")
        # Sweep parameters
        self.dac_channel = 1 # 1...8
        self.adc_channel = 1 # 1...4 or 1...8 depending on card
        self.adc_card = 1 # 1 (normal), 2 (filtered)
        self._sweep_channels = (self.dac_channel, self.adc_channel) # for qkit compability
        self.delay = 2000 # NOTE: int describing to be slept time inbetween dac set and adc get. 
        # slept time <=> self.delay * 1e-8 s, set/get commands take ~2e-6 s per point on their own always

    # functionality
    def do_get_adc(self, channel: int) -> float:
        """
        This is a very nice docstring
        """
        if channel in range(1, 5):
            self.adw.Set_Par(channel + self.ADC_CARD_OFFSET, 1)
            for i in range(5000):
                if self.adw.Get_Par(channel + self.ADC_CARD_OFFSET) == 0:
                    return self.adw.Get_FPar(channel + self.ADC_CARD_OFFSET)
                time.sleep(0.001)
            raise TimeoutError("ADwin Pro II did not confirm ADC read within 5s")
        else:
            raise ValueError("Channel must be 1...4")
        
    def do_get_adc_filtered(self, channel: int) -> float:
        """
        This is a very nice docstring
        """
        if channel in range(1, 9):
            self.adw.Set_Par(channel + self.ADC_FILTER_CARD_OFFSET, 1)
            for i in range(5000):
                if self.adw.Get_Par(channel + self.ADC_FILTER_CARD_OFFSET) == 0:
                    return self.adw.Get_FPar(channel + self.ADC_FILTER_CARD_OFFSET)
                time.sleep(0.001)
            raise TimeoutError("ADwin Pro II did not confirm ADC read within 5s")
        else:
            raise ValueError("Channel must be 1...8")
        
    def do_set_dac(self, volt: float, channel: int) -> None:
        """
        This is a very nice docstring
        """
        if channel in range(1, 9):
            self.adw.Set_FPar(channel + self.DAC_CARD_OFFSET, volt)
            self.adw.Set_Par(channel + self.DAC_CARD_OFFSET, 1)
        else:
            raise ValueError("Channel must be 1...8")

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
        self.adw.SetData_Long(self._to_reg(set_array), 1, 1, len(set_array))

    def get_tracedata(self) -> tuple[np.ndarray]:
        """
        Starts a sweep with parameters currently set on device and returns
        set_values_array, measured_values_array. Sorting by what is I and V
        is being handled by overlaying virtual_tunnel_electronic
        """
        # Sweep
        self.adw.Start_Process(2)
        while self.adw.Process_Status(2):
            time.sleep(0.1)
        # Read result
        return self._to_volt(self.adw.GetData_Long(1, 1, self.adw.Get_Par(1))), self._to_volt(self.adw.GetData_Long(2, 1, self.adw.Get_Par(1)))
    
    # qkit SMU compability
    def set_sweep_mode(self, mode: int = 0):
        if mode != 0:
            print("ADwinProII only has voltage ADC/DACs, only VV-mode 0 supported")
    def get_sweep_mode(self) -> int:
        return 0
    def get_sweep_channels(self) -> tuple[int]:
        return (self.dac_channel, self.adc_channel)
    def set_status(self, *args, **kwargs) -> None:
        pass # ADC/DACs are always responsive
    def reset(self):
        for i in range(1, 9):
            self.do_set_dac(0.0, i)
