# -*- coding: utf-8 -*-
"""
2D sweep of DC bias and frequency of probe to find the modulation curve of the JPA.
"""
from typing import List

import h5py
import numpy as np

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import lockin
from presto.utils import ProgressBar
import time


from qkit.measure.presto._base import Base

DAC_CURRENT = 32_000  # uA
CONVERTER_CONFIGURATION = {
    "adc_mode": AdcMode.Mixed,
    "adc_fsample": AdcFSample.G4,
    "dac_mode": DacMode.Mixed04,
    "dac_fsample": DacFSample.G8,
}


class JpaSweepBias(Base):
    def __init__(
        self,dict_param = {}
     ) -> None:
        self._default_vals = {
                'freq_center' : 6e9,
                'freq_span' : 1e9,
                'df' : 1e6,
                'num_averages' : 10,
                'amp' : 0.1,
                'bias_arr' : [0],
                'output_port' : 1,
                'input_port' : 1,
                'bias_port':2,
                'experiment_name': "0.h5",
                'dither' : True,
                'freq_arr' : [None], 
                'resp_arr' : [None]
        }
        
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))


    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
    ) -> str:
        with lockin.Lockin(
            force_config = True,
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **CONVERTER_CONFIGURATION,
        ) as lck:
            assert lck.hardware is not None

            lck.hardware.set_adc_attenuation(self.input_port, 20.0)
            lck.hardware.set_dac_current(self.output_port, DAC_CURRENT)
            lck.hardware.set_inv_sinc(self.output_port, 0)
            
            nr_bias = len(self.bias_arr)
            _, self.df = lck.tune(0.0, self.df)

            f_start = self.freq_center - self.freq_span / 2
            f_stop = self.freq_center + self.freq_span / 2
            n_start = int(round(f_start / self.df))
            n_stop = int(round(f_stop / self.df))
            n_arr = np.arange(n_start, n_stop + 1)
            nr_freq = len(n_arr)
            self.freq_arr = self.df * n_arr
            self.resp_arr = np.zeros((nr_bias, nr_freq), np.complex128)
            def ramp_bias(biasstart,biasend,t):
                for v in np.linspace(biasstart,biasend,200):
                    lck.hardware.set_dc_bias(v, self.bias_port)
                    time.sleep(t/200)
                    
            ramp_bias(-0.2,self.bias_arr[0],2)    
            lck.hardware.sleep(1.0, False)

            lck.hardware.configure_mixer(
                freq=self.freq_arr[0],
                in_ports=self.input_port,
                out_ports=self.output_port,
            )

            lck.set_df(self.df)
            og = lck.add_output_group(self.output_port, 1)
            og.set_frequencies(0.0)
            og.set_amplitudes(self.amp)
            og.set_phases(0.0, 0.0)

            lck.set_dither(self.dither, self.output_port)
            ig = lck.add_input_group(self.input_port, 1)
            ig.set_frequencies(0.0)

            lck.apply_settings()


            t0 = time.time()
            for jj in range(nr_bias):
                if jj>0:
                    ramp_bias(self.bias_arr[jj-1],self.bias_arr[jj],2)   
                
                
                lck.hardware.sleep(1.0, False)

                for ii, freq in enumerate(self.freq_arr):
                    lck.hardware.configure_mixer(
                        freq=freq,
                        in_ports=self.input_port,
                        out_ports=self.output_port,
                    )
                    lck.hardware.sleep(1e-3, False)

                    _d = lck.get_pixels( self.num_averages, quiet=True)
                    data_i = _d[self.input_port][1][:, 0]
                    data_q = _d[self.input_port][2][:, 0]
                    data = data_i.real + 1j * data_q.real  # using zero IF

                    self.resp_arr[jj, ii] = np.mean(data[-self.num_averages :])
                dt = time.time() - t0
                print(f"\r dc bias {round(self.bias_arr[jj],3)} V, iteration {jj+1} over {nr_bias} / should end in {round((dt*(nr_bias-jj)/(jj+1))//60,3)} min and {round((dt*(nr_bias-jj)/(jj+1))%60)} seconds", end="")
                
            print('\n')
            # Mute outputs at the end of the sweep
            og.set_amplitudes(0.0)
            lck.apply_settings()
            lck.hardware.set_dc_bias(0.0, self.bias_port)

        return self.save(self.experiment_name)

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)

    @classmethod
    def load(cls, load_filename: str) -> "basic_pulse_check":
        with h5py.File(load_filename, "r") as h5f:
            dict_h5_attrs = dict(h5f.attrs.items())
            dict_h5 = dict(h5f.items())
            self = cls()
            for key,val in self._default_vals.items():
                if isinstance(val,( np.ndarray,list)):
                    setattr(self, key, dict_h5[key][()])
                elif key == "jpa_params":
                    setattr(self, key, ast.literal_eval(dict_h5_attrs.get(key, self._default_vals[key])))
                else:
                    setattr(self, key, dict_h5_attrs.get(key, self._default_vals[key]))
        return self
