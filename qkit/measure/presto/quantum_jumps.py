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


class QuantumJumps(Base):
    def __init__(
        self,dict_param = {}
     ) -> None:
        self._default_vals = {
            'readout_freq' : 7e9,
            'control_freq' : 4e9,
            'readout_amp' : 0.1,     
            'readout_phase':0,
            'control_amp' : 0.1,
            'control_duration' : 200e-9,
            'match_duration' : 300e-9,
            'readout_port' : 1,           
            'control_port' : 3,
            'sample_port' : 1,
            'readout_match_delay' :  100e-9,
            'n_repeat':500,          
            'total_repeat':1,
            'experiment_name': '0.h5',
            'drag' : 0,
            'match_arr' : [None],
            'jpa_params' : None}
            
        for key,value in dict_param.items():
            if key  not in self._default_vals :
                print(key ,'is unnecessary')
                 
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))
            
        if self.n_repeat >3000:
            self.total_repeat = self.n_repeat//4500 +1
            self.n_repeat= 3000*self.total_repeat
            self._n_sub_repeat = 3000
            print(f'total_number of points set to 4500*{self.total_repeat}')
        else:
            self._n_sub_repeat = self.n_repeat

    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
        print_time: bool = True,
        print_save = True,
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
            pls.hardware.set_dac_current(self.control_port, DAC_CURRENT)
            pls.hardware.set_inv_sinc(self.readout_port, 0)
            pls.hardware.set_inv_sinc(self.control_port, 0)
            
            pls.hardware.configure_mixer(
                freq=self.readout_freq,
                in_ports=self.sample_port,
                out_ports=self.readout_port,
                sync=False,  # sync in next call
            )
            
            pls.hardware.configure_mixer(
                freq=self.control_freq,
                out_ports=self.control_port,
                sync=True,
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
            pls.setup_freq_lut(
                output_ports=self.control_port,
                group=0,
                frequencies=0.0,
                phases=0.0,
                phases_q=0.0,
            )
            # Setup lookup tables for amplitudes
            pls.setup_scale_lut(
                output_ports=self.readout_port,
                group=0,
                scales =self.readout_amp,
            )
            pls.setup_scale_lut(
                output_ports=self.control_port,
                group=0,
                scales=self.control_amp,
            )

            # Setup readout and control pulses
            # use setup_long_drive to create a pulse with square envelope
            # setup_long_drive supports smooth rise and fall transitions for the pulse,
            # but we keep it simple here
            readout_pulse = pls.setup_long_drive(
                output_port=self.readout_port,
                group=0,
                duration=self._n_sub_repeat*(self.match_duration+40e-9),
                amplitude=1.0 ,
                amplitude_q = np.imag( np.exp(1j*self.readout_phase)),
                rise_time=0e-9,
                fall_time=0e-9,
            )
            control_ns = int(
                round(self.control_duration * pls.get_fs("dac"))
            )  # number of samples in the control template
            control_envelope = sin2(control_ns, drag=self.drag)
            control_pulse = pls.setup_template(
                output_port=self.control_port,
                group=0,
                template=control_envelope,
                template_q=control_envelope if self.drag == 0.0 else None,
                envelope=True,
            )
          
            # Setup template matching
            ns_match = int(round(self.match_duration * pls.get_fs("adc")))
            templ_i = np.full(ns_match, 1+0j)
            templ_q = np.full(ns_match, 0+1j)
            match_i, match_q = pls.setup_template_matching_pair(
                input_port=self.sample_port,
                template1=templ_i,
                template2=templ_q,
                )
            

            # ******************************
            # *** Program pulse sequence ***
            # ******************************
            T = 0.0  

            pls.reset_phase(T, self.readout_port)
            pls.output_pulse(T, readout_pulse)
            T += self.readout_match_delay
            for _ in range(self._n_sub_repeat):
                pls.match(T, [match_i, match_q])
                T +=  self.match_duration+40e-9
            T+= 50*self.match_duration

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
                num_averages=self.total_repeat,
                print_time=print_time,
            )
#             self.t_arr, self.store_arr = pls.get_store_data()
            self.match_arr = pls.get_template_matching_data([match_i, match_q])
            
            

            if self.jpa_params is not None:
                pls.hardware.set_lmx(0.0, 0.0, self.jpa_params["pump_port"])
                pls.hardware.set_dc_bias(0.0, self.jpa_params["bias_port"])

        return self.save(self.experiment_name,print_save=print_save)

    def save(self, save_filename: str = None,print_save:bool = True) -> str:
        return super().save(__file__, save_filename=save_filename,print_save = print_save)
