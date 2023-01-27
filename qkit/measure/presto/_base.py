# -*- coding: utf-8 -*-
import os
import time
import ast
from typing import Optional
import logging
import json
import qkit
#from qkit.measure.measurement_class.Measurement import _JSON_instruments_dict
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
import os
import h5py
import numpy as np

from presto.utils import get_sourcecode
from presto.hardware import AdcFSample, AdcMode, DacFSample, DacMode

class Base:
    """
    Base class for measurements
    """
    
    def save(self, script_path: str, save_filename: Optional[str] = None,print_save:bool = True) -> str:
        script_path = os.path.realpath(script_path)  # full path of current script

        if ( 'qkit' in globals()):
            if ('cfg' in qkit.__dict__):
                datafolder = qkit.cfg['datadir']+'\\'+qkit.cfg['run_id']+'\\'+qkit.cfg['user']+'\\'
                
                if os.path.isdir(datafolder):
                    pass
                elif os.path.isdir(qkit.cfg['datadir']+'\\'+qkit.cfg['run_id']):
                    os.mkdir(datafolder)
                elif os.path.isdir(qkit.cfg['datadir']):
                    os.mkdir(qkit.cfg['datadir']+'\\'+qkit.cfg['run_id'])
                    os.mkdir(datafolder)
               
            filename_split = os.path.normpath(save_filename).split(os.path.sep)
            if   len(filename_split) == 1 :
                save_path = datafolder+save_filename+'.h5'
            else:
                current_folder = datafolder
                for folder in filename_split[:-1]:
                    current_folder += folder+ '\\'
                    if np.logical_not( os.path.isdir(current_folder)):
                        os.mkdir(current_folder)
                
                save_path = os.path.realpath(datafolder+save_filename+'.h5')
        else:
            save_path = os.path.realpath(save_filename+'.h5')
        source_code = get_sourcecode(
            script_path
        )  # save also the sourcecode of the script for future reference
        with h5py.File(save_path, "w") as h5f:
            dt = h5py.string_dtype(encoding="utf-8")
            ds = h5f.create_dataset("source_code", (len(source_code),), dt)
            for ii, line in enumerate(source_code):
                ds[ii] = line

            for attribute in self.__dict__:
                if attribute.startswith("_"):
                    # don't save private attributes
                    continue
                elif attribute in ["jpa_params", "clear"]:
                    h5f.attrs[attribute] = str(self.__dict__[attribute])
                # elif "converter_config":
                    # if self.__dict__["converter_config"] == None:
                        # pass
                    # else:
                        # converter_settings = self.__dict__["converter_config"]
                        # grp_settings = h5f.create_group("converter_config")
                        # for key in dict_settings:
                            # dset = grp_settings.create_dataset(key,0)
                elif attribute in ["settings"]:
                    if self.__dict__["settings"] == None:
                        pass
                    else:
                        dict_settings = self.__dict__["settings"]
                    
                        grp_settings = h5f.create_group("settings")
                        for key in dict_settings:
                            dset = grp_settings.create_dataset(key,0)
                            for key_,value_ in dict_settings[key].items():
                                if type(value_) in [bool,float,int,str]:
                                    dset.attrs[key_] = value_
                                    
                                elif (value_)==None:
                                    dset.attrs[key_] = 'none'
                elif np.isscalar(self.__dict__[attribute]):
                    h5f.attrs[attribute] = self.__dict__[attribute]
                else:
                    h5f.create_dataset(attribute, data=self.__dict__[attribute])
        print_path  = os.path.splitext(save_path.replace('\\', '/'))[0]
        if print_save:
            print(f'Data saved to: {print_path}')
        return save_path



    @classmethod
    def load(cls, load_filename: str) -> "Sweep":
        load_filename_ = os.path.realpath(load_filename)
        with h5py.File(load_filename_+'.h5', "r") as h5f:
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
            if "settings" in dict(h5f.items()):
                if h5f["settings"] == None:
                        pass
                else:
                    dict_settings = {}
                    for key in list(h5f["settings"].keys()):
                        dict_instr = {}
                        for key_,val_ in (h5f["settings"][key].attrs.items()):
                            if val_ == 'none':
                                dict_instr[key_] = None
                            else:
                                dict_instr[key_] = val_
                        dict_settings[key] = dict_instr
                    setattr(self, "settings",dict_settings)
        return self

    def get_instr_dict(self):
        if ( 'qkit' in globals()):
            if ('instruments' in qkit.__dict__):
                instr_dict = {}
                for ins_name in qkit.instruments.get_instruments():
                    ins = qkit.instruments.get(ins_name)
                    param_dict = {}
                    for (param, popts) in _dict_to_ordered_tuples(ins.get_parameters()):
                        param_dict.update({param:ins.get(param, query=False, channels=popts)})
                        if popts.get('offset',False):
                            param_dict.update({param+"_offset": ins._offsets[param]})
                    instr_dict.update({ins_name:param_dict})
                return instr_dict
            else:
                return None
        else:
            return None
            
            
            
    # def converter_config(self,n):
        # [DacFSample.G8, DacFSample.G6, DacFSample.G8, DacFSample.G6]
        # CONVERTER_CONFIGURATION = {
            # "adc_mode": AdcMode.Mixed,
            # "adc_fsample": [AdcFSample.G4,]
            #"dac_mode": [DacMode.Mixed04, DacMode.Mixed02, DacMode.Mixed02, DacMode.Mixed02],
            #"dac_fsample": [DacFSample.G8, DacFSample.G6, DacFSample.G6, DacFSample.G6],
            # "dac_mode": [DacMode.Mixed04, DacMode.Mixed02, DacMode.Mixed42, DacMode.Mixed02],
            # "dac_fsample": [DacFSample.G8, DacFSample.G6, DacFSample.G8, DacFSample.G6],}
        
        
        #return CONVERTER_CONFIGURATION
        
        
        
def project(resp_arr, reference_templates):
    ref_g, ref_e = reference_templates
    conj_g = ref_g.conj()
    conj_e = ref_e.conj()
    norm_g = np.sum(ref_g * conj_g).real
    norm_e = np.sum(ref_e * conj_e).real
    overlap = np.sum(ref_g * conj_e).real
    proj_g = np.zeros(resp_arr.shape[0])
    proj_e = np.zeros(resp_arr.shape[0])
    for i in range(resp_arr.shape[0]):
        proj_g[i] = np.sum(conj_g * resp_arr[i, :]).real
        proj_e[i] = np.sum(conj_e * resp_arr[i, :]).real
    res = proj_e - proj_g
    res_g = overlap - norm_g
    res_e = norm_e - overlap
    res_min = res_g
    res_rng = res_e - res_g
    data = (res - res_min) / res_rng
    return data



def _dict_to_ordered_tuples(dic):
    '''Convert a dictionary to a list of tuples, sorted by key.'''
    if dic is None:
        return []
    keys = sorted(dic.keys())
    ret = [(key, dic[key]) for key in keys]
    return ret
    