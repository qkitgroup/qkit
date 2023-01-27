# -*- coding: utf-8 -*-
"""
Two-tone spectroscopy with Pulsed mode: sweep of pump frequency, with fixed pump power and fixed probe.
"""
import ast

import h5py
import numpy as np

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import pulsed
from presto.utils import rotate_opt, sin2

from qkit.measure.presto._base import Base

DAC_CURRENT = 32_000  # uA

config_0 = {
    "adc_mode": [1,1,1,1],
    "adc_fsample": [2,2,2,2],
    "dac_mode": [2,2,2,2],
    "dac_fsample": [2,2,2,2]}


IDX_LOW = 1_500
IDX_HIGH = 2_000


class TwoTonePulsed(Base):
    def __init__(
        self,dict_param = {}
     ) -> None:
    
        
        self._default_vals = {
            'readout_freq' : 6e9,
            'control_freq_center' : 2.5e9,
            'control_freq_span' : 0.5e9,
            'control_freq_nr' : 10,
            'num_averages' : 10,
            'readout_amp':0.1,
            'control_amp':0.1,
            'readout_duration':200e-9,
            'control_duration' : 300e-9,
            'sample_duration' : 200e-9,
            'sample_port' : 1,
            'control_port':3,
            'readout_port': 1,
            'readout_sample_delay':200e-6,
            'wait_delay' : 50e-6,
            'drag': 0,
            'experiment_name': "0.h5",
            'control_freq_arr': [None],
            'store_arr':[None],
            't_arr' : [None],
            'jpa_params' : None}
            
        for key,value in dict_param.items():
            if key  not in self._default_vals :
                print(key ,'is unnecessary')
        
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))
        
        self.converter_config = config_0
        
        
    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
        print_time:bool = True,
        print_save:bool = True,
    ) -> str:
        self.settings  = self.get_instr_dict()
        CONVERTER_CONFIGURATION = self.create_converter_config(self.converter_config)
        with pulsed.Pulsed(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **CONVERTER_CONFIGURATION,
        ) as pls:
            assert pls.hardware is not None
            pls.hardware.set_dc_bias(-3.6091, 1)
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
                scales=self.control_amp,
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
            # For the control pulse we create a sine-squared envelope,
            # and use setup_template to use the user-defined envelope
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

            # Setup sampling window
            pls.set_store_ports(self.sample_port)
            pls.set_store_duration(self.sample_duration)

            # ******************************
            # *** Program pulse sequence ***
            # ******************************
            T = 0.0  # s, start at time zero ...
            # Control pulse
            pls.reset_phase(T, self.control_port)
            pls.output_pulse(T, control_pulse)
            # Readout pulse starts right after control pulse
            T += self.control_duration
            pls.reset_phase(T, self.readout_port)
            pls.output_pulse(T, readout_pulse)
            # Sampling window
            pls.store(T + self.readout_sample_delay)
            # Move to next Rabi amplitude
            T += self.readout_duration
            pls.next_frequency(
                T, self.control_port
            )  # every iteration will have a different frequency
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
            # repeat the whole sequence `rabi_n` times
            # then average `num_averages` times
            pls.run(
                period=T,
                repeat_count=self.control_freq_nr,
                num_averages=self.num_averages,
                print_time=print_time,
            )
            self.t_arr, self.store_arr = pls.get_store_data()

            if self.jpa_params is not None:
                pls.hardware.set_lmx(0.0, 0.0, self.jpa_params["pump_port"])
                #pls.hardware.set_dc_bias(0.0, self.jpa_params["bias_port"])

        return self.save(self.experiment_name,print_save=print_save)

    def save(self, save_filename: str = None,print_save:bool = True) -> str:
        return super().save(__file__, save_filename=save_filename,print_save = print_save)
