import numpy as np
import sys
import h5py
import logging as log
import copy
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from scipy.signal import find_peaks
from qkit.analysis.magnetoconductance.data_extraction import HDFData

class JumpDetective:
    ''' The module takes an object of the HDFData class to extract measurement data
    from a .h/hdf5 file and detect jumps in the sweeps. The HDFData object
    can also be used to save the detected jumps in the .h/hdf5 file analysis0 group.'''
    def __init__(self, hf:HDFData, mvars, dirns, mfunc, **kwargs):
        self._hf = hf
        self._mvars = mvars
        self._dirns = dirns
        self._data_prefix = mfunc+'.'
        self._names = {}
        self._jump_prefix = 'jumpdetect.'
        self._jump_suffix = {'pos':'.pos','amp':'.amp'}
        self._pos = None
        self._amp = None
        self._data = {}
        self._analysis = {}
        self._save = {}
        self._multiple_jumps = False
        self._params = {'filter': ('gauss', 7),     # (gauss or uni, sigma or number of datapnts)
                        'sel_peak': 'highest' }      # 'highest', 'first', or 'last'
        self.update_params(**kwargs)
        self.generate_names()
        self.dataload = False


    def save_jumps(self, ds_pos=None, ds_amp=None):
        ''' save jumps '''
        if ds_pos and ds_amp:
            pass
        elif ds_amp:
            ds_pos = ds_amp[:-4]+self._jump_suffix['pos']
        elif ds_pos:
            ds_amp = ds_pos[:-4]+self._jump_suffix['amp']
        else:
            print("No jump analysis chosen for saving jumps\nChoose jump analysis from following list:")
            for key,val in self._save.items():
                for val2 in val:
                    print(f"- {val2}: params: {self._analysis[val2][2]}")
            return
        try:
            if isinstance(self._analysis[ds_pos],h5py.Dataset):
                print("Dataset already exists!")
                return
            elif isinstance(self._analysis[ds_amp],h5py.Dataset):
                print("Dataset already exists!")
                return
            print(f'Saving datasets: {ds_pos}, {ds_amp}')
            for key, val in self._save.items():
                if ds_amp in val[1:]:
                    self._analysis[ds_amp], self._analysis[val[0]] = self._analysis[val[0]], self._analysis[ds_amp]
                    ds_amp = val[0]
                if ds_pos in val[1:]:
                    self._analysis[ds_pos], self._analysis[val[0]] = self._analysis[val[0]], self._analysis[ds_pos]
                    ds_pos = val[0]
                if ds_amp == val[0] or ds_pos == val[0]:
                    del val[0]
            print(f'Names changed: {ds_pos}, {ds_amp}')
            pos_meta = {'unit':self._analysis[ds_pos][1], 'ds_url':f'/entry/analysis0/{ds_pos}', 'params':self._analysis[ds_pos][2]}
            amp_meta = {'unit':self._analysis[ds_amp][1], 'ds_url':f'/entry/analysis0/{ds_amp}', 'params':self._analysis[ds_pos][2], 'x_ds_url':f"/entry/analysis0/{ds_pos}"}
            print(f'Saving datasets: {ds_pos}, {ds_amp}')
            self._hf.create_analysis_ds(data=self._analysis[ds_pos][0],ds_name=ds_pos,**pos_meta)
            self._hf.create_analysis_ds(data=self._analysis[ds_amp][0],ds_name=ds_amp,**amp_meta)
            print("Datasets saved!")
        except KeyError:
            print("Analysis chosen for saving jumps does not exist\nChoose jump analysis from following list:")
            for key,val in self._analysis.items():
                if (self._jump_suffix['amp'] in key or self._jump_suffix['pos'] in key) and not 'unit' in key:
                    if not isinstance(val,h5py.Dataset):
                        print(f"- {key}")


    def generate_names(self):
        ''' generate names for data extraction and saving analysis'''
        for val in self._mvars:
            for val2 in self._dirns:
                self._names[f"{val}_{val2}"] = None


    def search_jump_dss(self):
        ''' function to search for already existing analysis datasets'''
        pre = self._jump_prefix
        suf = self._jump_suffix
        for key in self._names.keys():
            dss = self._hf.get_analysis_data(prefix=pre,ds_name=[key],suffix=suf['amp'])
            if dss:
                for name, ds in dss.items():
                    if isinstance(ds, h5py.Dataset):
                        params = ds.attrs.get('params')
                        if params == str(self._params):
                            self._analysis[name] = ds
                if self._names.get(key,None) is None:
                    iname = f"{pre}{key}{suf['amp']}__imax"
                    imax = dss.get(iname,None)
                    self._names[key] = imax


    def load_analysis(self):
        ''' function to load analysis datasets from .h/hdf5 file'''
        pre = self._jump_prefix
        suf = self._jump_suffix
        for key, val in self._hf.get_analysis_data(prefix=pre,ds_name=list(self._names.keys()),suffix=suf['amp']).items():
            if isinstance(val, h5py.Dataset):
                self._analysis[key] = val


    def load_data(self):
        ''' function to load all needed datasets from .h/hdf5 file'''
        self.search_jump_dss()
        for key, val in self._hf.get_measure_data(prefix=self._data_prefix,ds_name=list(self._names.keys())).items():
            self._data[key] = val
        self.dataload = True
        self.sweep = np.array(self._data['y_data'])


    def update_params(self, **kwargs):
        ''' update filter and peak select param'''
        for key, value in kwargs.items():
            self._params[key] = value
        self.search_jump_dss()


    def multidetect(self, ds_names:list=[]):
        ''' Detect all jumps positions and ampltiudes for multiple chosen datasets '''
        if not self.dataload:
            self.load_data()
        if ds_names:
            for name in ds_names:
                self.detect_all_jumps(ds_name=name)
        else:
            for name in self._names.keys():
                self.detect_all_jumps(ds_name=name)


    def detect_all_jumps(self, ds_name):
        ''' Detect all jumps positions and ampltiudes in one dataset '''
        for key, val in self._analysis.items():
            if ds_name in key:
                if isinstance(val, h5py.Dataset):
                    params = val.attrs.get('params')
                    if params == str(self._params):
                        return
                elif isinstance(val,list):
                    if len(val) == 3:
                        if val[2] == self._params:
                            return
        analysis_name = ds_name
        index = self._names.get(ds_name)
        if isinstance(index,int):
            analysis_name = f"{ds_name}_{index}"
        if self._data_prefix + ds_name in self._data.keys():
            if 'retrace' in ds_name:
                self.sign = -1
            else:
                self.sign = 1
            self.ds = np.array(self._data[self._data_prefix+ds_name],np.float32)
            self.ds_unit = self._data[self._data_prefix+ds_name].attrs.get('unit','')
            self.sweep_unit = self._data['y_data'].attrs.get('unit','')
            self.sweep_count, self.sweep_length = self.ds.shape
            self.pos = np.empty(self.sweep_count)
            self.amp = np.empty(self.sweep_count)
            for i in range(self.sweep_count):
                self.pos[i], self.amp[i], *_ = self.detect_jump(i)
            # define key for analysis data dict
            pre = self._jump_prefix
            pos_name=f"{pre}{analysis_name}{self._jump_suffix['pos']}"
            amp_name=f"{pre}{analysis_name}{self._jump_suffix['amp']}"
            # save data, unit, params in val of analysis dict
            self._analysis[pos_name] = [self.pos, self.sweep_unit, copy.deepcopy(self._params)]
            self._analysis[amp_name] = [self.amp, self.ds_unit, copy.deepcopy(self._params)]
            # add new analysis data to savable data
            if isinstance(self._save.get(f"{ds_name}{self._jump_suffix['pos']}"),list):
                self._save[f"{ds_name}{self._jump_suffix['pos']}"].append(pos_name)
            else:
                self._save[f"{ds_name}{self._jump_suffix['pos']}"] = [pos_name]
            if isinstance(self._save.get(f"{ds_name}{self._jump_suffix['amp']}"),list):
                self._save[f"{ds_name}{self._jump_suffix['amp']}"].append(amp_name)
            else:
                self._save[f"{ds_name}{self._jump_suffix['amp']}"] = [amp_name]
            # adjust indices for the next analysis
            if isinstance(index,int):
                self._names[ds_name] = index + 1
            elif index == None:
                self._names[ds_name] = 0
            else:
                assert IndexError
        elif self._jump_prefix+ds_name in self._analysis.keys():
            print(f"Dataset for jump analysis of {self._data_prefix}{ds_name} does already exist for given parameter!")
        else:
            assert KeyError(f"No dataset called {self._data_prefix}{ds_name} loaded!")

    def show_analysis_keys(self):
        ''' getter function for keys of all loaded and created analysis data'''
        for key, val in self._analysis.items():
            if isinstance(val,h5py.Dataset):
                print(f"- {key} --- ({val.attrs.get('params',None)})")
            elif isinstance(val,list):
                print(f"- {key} --- ({val[2]})")


    def filter_and_derive_sweep(self, i):
        # get x and y data
        x = self.sweep
        y = self.ds[i,:]
        # FILTER + DERIVATION
        if self._params['filter'][0] == 'uni':
            yf = uniform_filter1d(y, self._params['filter'][1])
            d = np.diff(yf, n=1, append=2*yf[-1]-yf[-2])
        elif self._params['filter'][0] == 'gauss':
            d = gaussian_filter1d(y, order=1, sigma=self._params['filter'][1])
            yf = gaussian_filter1d(y, order=0, sigma=self._params['filter'][1])
        else:
            assert NotImplementedError(f"Filter {self._params['filter'][0]} is not defined!")
        return x, y, yf, d


    def detect_jump(self,i):
        ''' extract the jump and height (amplitude of derivative) for sweep i.
            Return jpos, jamp and a list containing the filtered derivative,
            where all values out of athres have been put to zero. This could be
            changed, if needed. '''
        # get sweepvar, filtered measvar and the derivative for sweep i 
        x, _ , yf, d = self.filter_and_derive_sweep(i)
        # CHANGE SIGN OF D; SUCH THAT DESIRED PEAKS ARE ALWAYS POSITIVE
        # d *= self.sign

        peak_indices, jproperties = find_peaks(d)
        if len(peak_indices) > 0: # if peaks have been detected
            if self._params['sel_peak'] == 'highest':
                peak_idx = peak_indices[np.argmax(d[peak_indices])]
            elif self._params['sel_peak'] == 'first':
                peak_idx = peak_indices[0] ####################### NOT INCLUDING RETRACE!
            elif self._params['sel_peak'] == 'last':
                peak_idx = peak_indices[-1]#######################
            elif self._params['sel_peak'] == 'second_highest':
                if len(peak_indices) > 1:
                    peak_heights = d[peak_indices]
                    peak_heights[np.argmax(peak_heights)] = 0
                    peak_idx = peak_indices[np.argmax(peak_heights)]
                else:
                    return np.nan, np.nan
            else:
                print('sel_peak setting is not supported!')
                sys.exit()
            jpos = x[peak_idx]
            jamp = d[peak_idx]
        else: # no jumps -> np.nan
            jpos = np.nan
            jamp = np.nan
        return jpos, jamp


    def get_sliced_jumps(self, pos_name=None, amp_name=None, bthres:tuple=(None,None), athres:tuple=(None,None), nans=False):
        ''' getter func for jumps, sliced with input params'''
        pos_data, pos_unit, amp_data, amp_unit = self.get_full_jumps(pos_name,amp_name)
        if pos_data is None or amp_data is None:
            return None, None, None, None
        for i, val in enumerate(pos_data):
            if bthres[0]:
                if val < bthres[0]:
                    pos_data[i]=np.nan
                    amp_data[i]=np.nan
            if bthres[1]:
                if val > bthres[1]:
                    pos_data[i]=np.nan
                    amp_data[i]=np.nan
        for i, val in enumerate(amp_data):
            if athres[0]:
                if val < athres[0]:
                    pos_data[i]=np.nan
                    amp_data[i]=np.nan
            if athres[1]:
                if val > athres[1]:
                    pos_data[i]=np.nan
                    amp_data[i]=np.nan
        if not nans:
            # delete nan values
            pos_data = pos_data[~np.isnan(pos_data)]
            amp_data = amp_data[~np.isnan(amp_data)]
        return pos_data, pos_unit, amp_data, amp_unit

    def get_sweep_data(self):
        ''' getter func for sweep data'''
        if not self.dataload:
            self.load_data()
        return self.sweep


    def get_full_jumps(self, pos_name=None, amp_name=None):
        ''' getter func for full jump data'''
        if pos_name and amp_name:
            pass
        elif amp_name:
            pos_name = amp_name[:-4]+self._jump_suffix['pos']
        elif pos_name:
            amp_name = pos_name[:-4]+self._jump_suffix['amp']
        else:
            print("No jump analysis chosen for saving jumps\nChoose jump analysis from following list:")
            self.show_analysis_keys()
            return None, None, None, None
        pos_data = self._analysis[pos_name]
        amp_data = self._analysis[amp_name]
        if isinstance(pos_data,h5py.Dataset):
            pos_unit = pos_data.attrs.get('unit','')
            pos_data = np.array(pos_data)
        else:
            pos_data = pos_data[0]
            pos_unit = pos_data[1]
        if isinstance(amp_data,h5py.Dataset):
            amp_unit = amp_data.attrs.get('unit','')
            amp_data = np.array(amp_data)
        else:
            amp_data = amp_data[0]
            amp_unit = amp_data[1]
        return pos_data, pos_unit, amp_data, amp_unit