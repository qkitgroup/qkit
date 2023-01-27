# -*- coding: utf-8 -*-
"""Measure a Ramsey chevron pattern by changing the delay between two π/2 pulses and their frequency."""
import ast
from typing import List

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


class RamseyChevron(Base):
    def __init__(
        self,dict_param = {}
     ) -> None:
    
    
        self._default_vals = {
            'readout_freq' : 6e9,
            'control_freq_center' : 2.5e9,
            'control_freq_span': 2e6,
            'control_freq_nr' : 101,
            'readout_amp' : 0.06,
            'control_amp' : 0.81,
            'readout_duration' : 1000e-9,
            'control_duration' : 500e-9,
            'match_duration' : 200e-9,
            'delay_arr' : [1e-9],
            'control_port':3,
            'readout_port': 1,
            'sample_port' : 1,
            'wait_delay' : 50e-6,
            'readout_match_delay' :200e-6,
            'num_averages' : 10,
            'jpa_params' : None,
            'experiment_name': "0.h5",
            'drag' : 0.0,
            'control_freq_arr' : [None ], 
            'match_arr' : [None] }
        
        for key,value in dict_param.items():
            if key  not in self._default_vals :
                print(key ,'is unnecessary')
                
            
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))

    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
        print_time: bool = True
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

            # figure out frequencies
            assert self.control_freq_center > (self.control_freq_span / 2)
            assert self.control_freq_span < pls.get_fs("dac") / 2  # fits in HSB
            control_if_center = pls.get_fs("dac") / 4  # middle of HSB
            control_if_start = control_if_center - self.control_freq_span / 2
            control_if_stop = control_if_center + self.control_freq_span / 2
            control_if_arr = np.linspace(control_if_start, control_if_stop, self.control_freq_nr)
            control_nco = self.control_freq_center - control_if_center
            self.control_freq_arr = control_nco + control_if_arr

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
                freq=control_nco,
                out_ports=self.control_port,
                sync=True,  # sync here
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
            # we only need to use carrier 1
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
                frequencies=control_if_arr,
                phases=np.full_like(control_if_arr, 0.0),
                phases_q=np.full_like(control_if_arr, -np.pi / 2),  # HSB
            )

            # Setup lookup tables for amplitudes
            pls.setup_scale_lut(
                output_ports=self.readout_port,
                group=0,
                scales=self.readout_amp,
            )
            pls.setup_scale_lut(
                output_ports=self.control_port,
                group=0,
                scales=1.0,  # set amplitude in template
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
            # number of samples in the control template
            control_ns = int(round(self.control_duration * pls.get_fs("dac")))
            control_envelope = self.control_amp * sin2(control_ns, drag=self.drag)

            # we loose 3 dB by using a nonzero IF
            # so multiply the envelope by sqrt(2)
            if self.drag == 0.0:
                control_envelope *= np.sqrt(2)
            else:
                # for DRAG we also rotate by 45 deg
                # so that we don't saturate the output
                control_envelope *= np.sqrt(2) * np.exp(1j * np.pi / 4)

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
            T = 0.0  # s, start at time zero ...
            for delay in self.delay_arr:
                # first pi/2 pulse
                pls.reset_phase(T, self.control_port)
                pls.output_pulse(T, control_pulse)
                T += self.control_duration
                # Ramsey delay
                T += delay
                # second pi/2 pulse
                pls.output_pulse(T, control_pulse)
                T += self.control_duration
                # Readout
                pls.reset_phase(T, self.readout_port)
                pls.output_pulse(T, readout_pulse)
                pls.match(T + self.readout_match_delay, [match_i, match_q])
                #pls.store(T + self.readout_sample_delay)
                T += self.readout_duration
                # Move to next iteration
                T += self.wait_delay
            pls.next_frequency(T, self.control_port)
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
            pls.run(
                period=T,
                repeat_count=self.control_freq_nr,
                num_averages=self.num_averages,
                print_time=print_time,
            )
            match_arr = np.array(pls.get_template_matching_data([match_i, match_q]))
            self.match_arr = match_arr
            if self.jpa_params is not None:
                pls.hardware.set_lmx(0.0, 0.0, self.jpa_params["pump_port"])
                pls.hardware.set_dc_bias(0.0, self.jpa_params["bias_port"])

        return self.save(self.experiment_name)

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)
