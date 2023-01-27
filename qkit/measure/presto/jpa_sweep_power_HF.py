# -*- coding: utf-8 -*-
"""
3D sweep of pump power, DC bias and frequency of probe, to see where we get gain.
"""
from typing import List

import h5py
import numpy as np

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import lockin
from presto.utils import ProgressBar

from _base import Base

DAC_CURRENT = 32_000  # uA
CONVERTER_CONFIGURATION = {
    "adc_mode": AdcMode.Mixed,
    "adc_fsample": AdcFSample.G4,
    "dac_mode": DacMode.Mixed04,
    "dac_fsample": DacFSample.G8
}


class JpaSweepPowerBiasHF(Base):
    def __init__(
        self,dict_param = {}
     ) -> None:
    
    
    
    
        self._default_vals = {
            'freq_center': 6e9,
            'freq_span': 0.1e9,
            'df' : 1e6,
            'num_averages':10,
            'amp' : 0.05,
            'freq_pump_arr' : [None],
            'pump_pwr_arr' : [None],
            'output_port' : 1,
            'input_port':  1,
            'bias_port': 4,
            'pump_port': 1,
            'bias' : 0,
            'dither' : True,
            'freq_arr' : [None],
            'ref_resp_arr' : [None],
            'ref_pwr_arr' : [None]}
    
     
     
        for key, value in self._default_vals.items():
            setattr(self, key, dict_param.get(key, value))


    def run(
        self,
        presto_address: str,
        presto_port: int = None,
        ext_ref_clk: bool = False,
    ) -> str:
        with lockin.Lockin(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            **CONVERTER_CONFIGURATION,
        ) as lck:
            assert lck.hardware is not None

            lck.hardware.set_adc_attenuation(self.input_port, 25.0)
            lck.hardware.set_dac_current(self.output_port, DAC_CURRENT)
            lck.hardware.set_inv_sinc(self.output_port, 0)

            nr_freq_arr = len(self.freq_pump_arr)
            nr_pump_pwr = len(self.pump_pwr_arr)
            _, self.df = lck.tune(0.0, self.df)

            f_start = self.freq_center - self.freq_span / 2
            f_stop = self.freq_center + self.freq_span / 2
            n_start = int(round(f_start / self.df))
            n_stop = int(round(f_stop / self.df))
            n_arr = np.arange(n_start, n_stop + 1)
            nr_freq = len(n_arr)
            self.freq_arr = self.df * n_arr

            self.ref_resp_arr = np.zeros((nr_freq_arr, nr_freq), np.complex128)
            self.ref_pwr_arr = np.zeros((nr_freq_arr, nr_freq), np.float64)
            self.resp_arr = np.zeros((nr_pump_pwr, nr_freq_arr, nr_freq), np.complex128)
            self.pwr_arr = np.zeros((nr_pump_pwr, nr_freq_arr, nr_freq), np.float64)

            lck.hardware.set_lmx(0.0, 0, self.pump_port)  # start with pump off for reference
            lck.hardware.set_dc_bias(self.bias, self.bias_port)
            lck.hardware.sleep(0.1, False)

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

            #pb = ProgressBar((nr_pump_pwr + 1) * nr_freq_arr * nr_freq)
            #pb.start()
            Nit = 0
            for kk, pump_pwr in enumerate(np.r_[-1, self.pump_pwr_arr]):
                if kk == 0:
                    lck.hardware.set_lmx(0.0, 0, self.pump_port)
                else:
                    lck.hardware.set_lmx(self.freq_pump_arr[0], pump_pwr, self.pump_port)
                lck.hardware.sleep(0.1, False)
                for jj in range(len(self.freq_pump_arr)):
                    print(f"\r power {pump_pwr} unit lmx !!!!, freq {self.freq_pump_arr[jj]/1e9} GHz !!!!, iteration {Nit} over {(nr_pump_pwr + 1) * nr_freq_arr } ", end="")
                    Nit+=1
                    if kk == 0:
                        lck.hardware.set_lmx(0, 0, self.pump_port)
                    else:
                        lck.hardware.set_lmx(self.freq_pump_arr[jj], pump_pwr, self.pump_port)
                        
                    lck.hardware.sleep(0.1, False)

                    for ii, freq in enumerate(self.freq_arr):
                        
                        lck.hardware.configure_mixer(
                            freq=freq,
                            in_ports=self.input_port,
                            out_ports=self.output_port,
                        )
                        lck.hardware.sleep(2e-3, False)

                        _d = lck.get_pixels( self.num_averages, quiet=True)
                        data_i = _d[self.input_port][1][:, 0]
                        data_q = _d[self.input_port][2][:, 0]
                        data = data_i.real + 1j * data_q.real  # using zero IF

                        if kk == 0:
                            self.ref_resp_arr[jj, ii] = np.mean(data[-self.num_averages :])
                            self.ref_pwr_arr[jj, ii] = np.mean(
                                np.abs(data[-self.num_averages :]) ** 2
                            )
                        else:
                            self.resp_arr[kk - 1, jj, ii] = np.mean(data[-self.num_averages :])
                            self.pwr_arr[kk - 1, jj, ii] = np.mean(
                                np.abs(data[-self.num_averages :]) ** 2
                            )

                        #pb.increment()

            #pb.done()

            # Mute outputs at the end of the sweep
            og.set_amplitudes(0.0)
            lck.apply_settings()
            lck.hardware.set_dc_bias(0.0, self.bias_port)
            lck.hardware.set_lmx(0.0, 0, self.pump_port)

        return self.save()

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)

    @classmethod
    def load(cls, load_filename: str) -> "Sweep":
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

