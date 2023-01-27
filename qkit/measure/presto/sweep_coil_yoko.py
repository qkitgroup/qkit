# -*- coding: utf-8 -*-
"""
Simple frequency sweep using the Lockin mode.
"""
import h5py
import numpy as np

from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode
from presto import lockin
from presto.utils import ProgressBar
import time
from qkit.measure.presto._base import Base

DAC_CURRENT = 32_000  # uA
config_0 = {
    "adc_mode": [1,1,1,1],
    "adc_fsample": [2,2,2,2],
    "dac_mode": [2,2,2,2],
    "dac_fsample": [2,2,2,2]}



class SweepCoil(Base):
    '''
    ###### Define the experiment as such :
    experiment = presto_sweep_coil.SweepCoil({  'input_port' : 1,
                            'output_port' : 1,
                            'df' : 0.5e6,
                            'freq_center' : 7.32e9,
                            'freq_span' : 0.04e9,
                            'amp' : 0.03,
                            'dither' : True,
                            'num_skip' : 0 ,
                            'num_averages' : 400,
                            'bias_port' : 1,
                            'bias_arr': linspace(5,9,200)}
                            )
    #####  Define the data folder and launch it using : 
    experiment.experiment_name = './data_09_01_2023/D7Qubit_sweep_coil2.h5'
    save_filename = experiment.run(presto_address)
    '''
    def __init__(
        self,dict_param = {},
        qubit_bias_function: int = 0
     ) -> None:
    
        self._default_vals = {
            'freq_center' : 6e9,
            'freq_span' : 100e6,
            'df' : 1e6,
            'num_averages' : 10,
            'amp' : 0.1,
            'bias_arr':[0],
            'output_port' : 1,
            'input_port': 1,
            'dither': True,
            'num_skip': 0,
            'experiment_name': "0.h5",
            'freq_arr': [None],
            'resp_arr':[None],
            '_qubit_bias_function': 0}
            
            
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
        with lockin.Lockin(
            address=presto_address,
            port=presto_port,
            ext_ref_clk=ext_ref_clk,
            force_config =True,
            **CONVERTER_CONFIGURATION,
        ) as lck:
            assert lck.hardware is not None
            

            self._qubit_bias_function(self.bias_arr[0])
            lck.hardware.sleep(1.0, False)


                    
            lck.hardware.set_adc_attenuation(self.input_port, 20.0)
            lck.hardware.set_dac_current(self.output_port, DAC_CURRENT)
            lck.hardware.set_inv_sinc(self.output_port, 0)

            # tune frequencies
            _, self.df = lck.tune(0.0, self.df)
            f_start = self.freq_center - self.freq_span / 2
            f_stop = self.freq_center + self.freq_span / 2
            n_start = int(round(f_start / self.df))
            n_stop = int(round(f_stop / self.df))
            n_arr = np.arange(n_start, n_stop + 1)
            nr_freq = len(n_arr)
            n_coil = len(self.bias_arr)
            self.freq_arr = self.df * n_arr
            self.resp_arr = np.zeros((n_coil,nr_freq), np.complex128)

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

            
            #pb = ProgressBar(nr_freq)
            #pb.start()
            t0 = time.time()
            for jj in range(n_coil):
                if jj>0:
                    self._qubit_bias_function(self.bias_arr[jj])
                
                lck.hardware.sleep(0.2, False)
                dt = time.time() - t0
                print(f"\r dc bias {round(self.bias_arr[jj],3)} V, iteration {jj+1} over {n_coil} / should end in {round((dt*(n_coil-jj)/(jj+1))/60,3)} min ", end="")
                
                for ii in range(len(n_arr)):
                    f = self.freq_arr[ii]

                    lck.hardware.configure_mixer(
                        freq=f,
                        in_ports=self.input_port,
                        out_ports=self.output_port,
                    )
                    lck.hardware.sleep(1e-3, False)

                    _d = lck.get_pixels(self.num_skip + self.num_averages, quiet=True)
                    data_i = _d[self.input_port][1][:, 0]
                    data_q = _d[self.input_port][2][:, 0]
                    data = data_i.real + 1j * data_q.real  # using zero IF

                    self.resp_arr[jj,ii] = np.mean(data[-self.num_averages :])

                    #pb.increment()

                #pb.done()

            # Mute outputs at the end of the sweep
            og.set_amplitudes(0.0)
            lck.apply_settings()

        return self.save(self.experiment_name)

    def save(self, save_filename: str = None) -> str:
        return super().save(__file__, save_filename=save_filename)
