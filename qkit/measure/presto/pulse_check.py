# -*- coding: utf-8 -*-
"""
Measure Rabi oscillation by changing the amplitude of the control pulse.

The control pulse has a sin^2 envelope, while the readout pulse is square.
"""
import ast
import math
from typing import List, Tuple

import h5py
import numpy as np

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import pulsed
from presto.utils import rotate_opt, sin2

from qkit.measure.presto._base import Base

DAC_CURRENT = 32_000  # uA
CONVERTER_CONFIGURATION = {
    "adc_mode": AdcMode.Mixed,
    "adc_fsample": AdcFSample.G4,
    #"dac_mode": [DacMode.Mixed04, DacMode.Mixed02, DacMode.Mixed02, DacMode.Mixed02],
    #"dac_fsample": [DacFSample.G8, DacFSample.G6, DacFSample.G6, DacFSample.G6],
    "dac_mode": [DacMode.Mixed04, DacMode.Mixed02, DacMode.Mixed42, DacMode.Mixed02],
   "dac_fsample": [DacFSample.G8, DacFSample.G6, DacFSample.G8, DacFSample.G6],
}

IDX_LOW = 1_500
IDX_HIGH = 2_000


class SimplePulse(Base):
    '''
    experiment_simple_pulse = presto_basic_pulse_check.SimplePulse({ 'readout_freq' : 7.325e9,
                                        'num_averages' : 500000,
                                        'readout_amp' : 0.02,
                                        'readout_duration' : 500e-9,
                                        'sample_duration' : 900e-9,
                                        'sample_port' : 1,
                                        'readout_port': 1,
                                        'readout_sample_delay' : 200e-9,
                                        'wait_delay' : 50e-6})
    experiment_simple_pulse.experiment_name = 'filename'
    save_filename = experiment_simple_pulse.run(presto_address)
    '''
    def __init__(
        self,dict_param = {}
     ) -> None:
        
        self._default_vals = {
            'readout_freq' : 6e9,
            'num_averages' : 10,
            'readout_amp':0.1,
            'readout_duration':200e-9,
            'sample_duration' : 200e-9,
            'sample_port' : 1,
            'readout_port': 1,
            'readout_sample_delay':200e-6,
            'wait_delay' : 50e-6,
            'drag': 0,
            'experiment_name': "0.h5",
            'store_arr':[None],
            't_arr' : [None],
            'jpa_params' : None}
        
        
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))

    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
    ) -> str:
        self.settings  = self.get_instr_dict()
        # Instantiate interface class
        with pulsed.Pulsed(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **CONVERTER_CONFIGURATION,
        ) as pls:
            assert pls.hardware is not None

            pls.hardware.set_adc_attenuation(self.sample_port, 20.0)
            pls.hardware.set_dac_current(self.readout_port, DAC_CURRENT)
            pls.hardware.set_inv_sinc(self.readout_port, 0)
            pls.hardware.configure_mixer(
                freq=self.readout_freq,
                in_ports=self.sample_port,
                out_ports=self.readout_port,
                #sync=False,  # sync in next call
            )
            if self.jpa_params is not None:
                pls.hardware.set_lmx(
                    self.jpa_params["pump_freq"],
                    self.jpa_params["pump_pwr"],
                    self.jpa_params["pump_port"],
                )
                pls.hardware.set_dc_bias(self.jpa_params["bias"], self.jpa_params["bias_port"])
                pls.hardware.sleep(1.0, False)

            # ************************************
            # *** Setup measurement parameters ***
            # ************************************

            # Setup lookup tables for frequencies
            pls.setup_freq_lut(
                output_ports=self.readout_port,
                group=0,
                frequencies=0.0,
                phases=0.0,
                phases_q=0.0,
            )

            # Setup lookup tables for amplitudes
            pls.setup_scale_lut(
                output_ports=self.readout_port,
                group=0,
                scales=self.readout_amp,
            )
            

            # Setup readout and control pulses
            # use setup_long_drive to create a pulse with square envelope
            # setup_long_drive supports smooth rise and fall transitions for the pulse,
            # but we keep it simple here
            readout_pulse = pls.setup_long_drive(
                output_port=self.readout_port,
                group=0,
                duration=self.readout_duration,
                amplitude=1.0,
                amplitude_q=1.0,
                rise_time=0e-9,
                fall_time=0e-9,
            )


            # Setup sampling window
            pls.set_store_ports(self.sample_port)
            pls.set_store_duration(self.sample_duration)

            # ******************************
            # *** Program pulse sequence ***
            # ******************************
            T = 0.0  # s, start at time zero ...
            # Readout
            pls.reset_phase(T, self.readout_port)
            pls.output_pulse(T, readout_pulse)
            pls.store(T + self.readout_sample_delay)
            T += self.readout_duration
            # Wait for decay
            T += self.wait_delay

            if self.jpa_params is not None:
                # adjust period to minimize effect of JPA idler
                idler_freq = self.jpa_params["pump_freq"] - self.readout_freq
                idler_if = abs(idler_freq - self.readout_freq)  # NCO at readout_freq
                idler_period = 1 / idler_if
                T_clk = int(round(T * pls.get_clk_f()))
                idler_period_clk = int(round(idler_period * pls.get_clk_f()))
                # first make T a multiple of idler period
                if T_clk % idler_period_clk > 0:
                    T_clk += idler_period_clk - (T_clk % idler_period_clk)
                # then make it off by one clock cycle
                T_clk += 1
                T = T_clk * pls.get_clk_T()

            # **************************
            # *** Run the experiment ***
            # **************************
            # repeat the whole sequence `nr_amps` times
            # then average `num_averages` times

            pls.run(
                period=T,
                repeat_count=1,
                num_averages=self.num_averages,
                print_time=True,
            )
            self.t_arr, self.store_arr = pls.get_store_data()

            if self.jpa_params is not None:
                pls.hardware.set_lmx(0.0, 0.0, self.jpa_params["pump_port"])
                pls.hardware.set_dc_bias(0.0, self.jpa_params["bias_port"])

        return self.save(self.experiment_name)

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)
