# -*- coding: utf-8 -*-
"""
Two-tone spectroscopy in Lockin mode: 2D sweep of pump power and frequency, with fixed probe.
"""
from typing import List

import h5py
import numpy as np
import time

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import lockin
from presto.utils import ProgressBar, rotate_opt

from qkit.measure.presto._base import Base

DAC_CURRENT = 32_000  # uA

config_0 = {
    "adc_mode": [1,1,1,1],
    "adc_fsample": [2,2,2,2],
    "dac_mode": [2,2,2,2],
    "dac_fsample": [2,2,2,2]}


class TwoToneBiasSweep(Base):
    '''
    ###### Define the experiment as such :
    experiment_two_tone = presto_two_tone_bias_sweep.TwoToneBiasSweep({
            'readout_freq' : 7.3255e9,
            'control_freq_center' : 4.13e9,
            'control_freq_span' : 0.05e9,
            'df' : 0.5e6,
            'num_averages' : 500,
            'readout_amp':0.005,
            'control_amp':0.05,
            'bias_arr': [-3.6] ,
            'bias_port':1,
            'input_port' : 1,
            'control_port':3,
            'readout_port': 1})
    #####  Define the data folder and launch it using : 
    experiment_two_tone.experiment_name = 'filename'
    save_filename = experiment_two_tone.run(presto_address)
    '''
    def __init__(
        self,dict_param = {}
     ) -> None:
    
        self._default_vals = {
            'readout_freq' : 6e9,
            'control_freq_center' : 2.5e9,
            'control_freq_span' : 0.5e9,
            'df' : 1e6,
            'num_averages' : 10,
            'amp' : 0.1,
            'readout_amp':0.1,
            'control_amp':0.1,
            'bias_arr':[0],
            'bias_port':1,
            'input_port' : 1,
            'control_port' :3,
            'readout_port': 1,
            'dither': True,
            'num_skip': 0,
            'previous_val':0,
            'experiment_name': "0.h5",
            'control_freq_arr': [None],
            'resp_arr':[None]}
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
    ) -> str:
        self.settings  = self.get_instr_dict()
        CONVERTER_CONFIGURATION = self.create_converter_config(self.converter_config)
        #print(CONVERTER_CONFIGURATION['dac_fsample'])
        with lockin.Lockin(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **CONVERTER_CONFIGURATION,
        ) as lck:
            assert lck.hardware is not None
            
            
            #def ramp_bias(cur):
            def ramp_bias(biasstart,biasend,t):
                for v in np.linspace(biasstart,biasend,200):
                    lck.hardware.set_dc_bias(v, self.bias_port)
                    time.sleep(t/200)
                    
            ramp_bias(self.previous_val,self.bias_arr[0],3)
            lck.hardware.set_adc_attenuation(self.input_port, 20.0)
            lck.hardware.set_dac_current(self.readout_port, DAC_CURRENT)
            lck.hardware.set_dac_current(self.control_port, DAC_CURRENT)
            lck.hardware.set_inv_sinc(self.readout_port, 0)
            lck.hardware.set_inv_sinc(self.control_port, 0)
            # if USE_JPA:
            #     lck.hardware.set_lmx(jpa_pump_freq, jpa_pump_pwr)

            n_coil = len(self.bias_arr)

            # tune frequencies
            _, self.df = lck.tune(0.0, self.df)
            f_start = self.control_freq_center - self.control_freq_span / 2
            f_stop = self.control_freq_center + self.control_freq_span / 2
            n_start = int(round(f_start / self.df))
            n_stop = int(round(f_stop / self.df))
            n_arr = np.arange(n_start, n_stop + 1)
            nr_freq = len(n_arr)
            self.control_freq_arr = self.df * n_arr
            self.resp_arr = np.zeros((n_coil, nr_freq), np.complex128)
            
            lck.hardware.configure_mixer(
                freq=self.readout_freq,
                in_ports=self.input_port,
                out_ports=self.readout_port,
            )
            lck.hardware.configure_mixer(
                freq=self.control_freq_arr[0],
                out_ports=self.control_port,
            )
            lck.set_df(self.df)
            ogr = lck.add_output_group(self.readout_port, 1)
            ogr.set_frequencies(0.0)
            ogr.set_amplitudes(self.readout_amp)
            ogr.set_phases(0.0, 0.0)
            ogc = lck.add_output_group(self.control_port, 1)
            ogc.set_frequencies(0.0)
            ogc.set_amplitudes(self.control_amp)
            ogc.set_phases(0.0, 0.0)

            lck.set_dither(self.dither, [self.readout_port, self.control_port])
            ig = lck.add_input_group(self.input_port, 1)
            ig.set_frequencies(0.0)
            
            lck.apply_settings()


            t0 = time.time()
            for jj in range(n_coil):
                if jj>0:
                    ramp_bias(self.bias_arr[jj-1],self.bias_arr[jj],0.00)
                lck.hardware.sleep(0.0, False)
                for ii in range(len(self.control_freq_arr)):

                    lck.hardware.configure_mixer(
                        freq=self.control_freq_arr[ii],
                        out_ports=self.control_port,
                    )
                    lck.hardware.sleep(1e-3, False)

                    _d = lck.get_pixels(self.num_skip + self.num_averages, quiet=True)
                    data_i = _d[self.input_port][1][:, 0]
                    data_q = _d[self.input_port][2][:, 0]
                    data = data_i.real + 1j * data_q.real  # using zero IF

                    self.resp_arr[jj, ii] = np.mean(data[-self.num_averages :])

                
                dt = time.time() - t0
                print(f"\r dc bias {round(self.bias_arr[jj],3)} V, iteration {jj+1} over {n_coil} / should end in {round((dt*(n_coil-jj)/(jj+1))//60,3)} min and {round((dt*(n_coil-jj)/(jj+1))%60)} seconds", end="")
                
            # Mute outputs at the end of the sweep
            ogr.set_amplitudes(0.0)
            ogc.set_amplitudes(0.0)
            lck.apply_settings()
            # if USE_JPA:
            #     lck.hardware.set_lmx(0.0, 0)
        # if USE_JPA:
        #     mla.lockin.set_dc_offset(jpa_bias_port, 0.0)
        #     mla.disconnect()

        return self.save(self.experiment_name)

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)
