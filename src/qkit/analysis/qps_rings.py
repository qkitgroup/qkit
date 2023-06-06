# -*- coding: utf-8 -*-
"""

@author: h.rotzinger
"""
from qkit.storage import hdf_lib
import numpy as np
from scipy.ndimage.filters import sobel
from scipy.ndimage import gaussian_filter1d
from scipy.ndimage import median_filter


class qps_ring(object):
    def __init__(self, file_path):
        self._hf = hdf_lib.Data(path=file_path)
        self._prepare_datasets()
        
    def _prepare_datasets(self):
        '''
        reads out the file
        '''    
        # these ds_url should always be present in a resonator measurement
        ds_url_amp = "/entry/data0/amplitude"
        ds_url_pha = "/entry/data0/phase"
        ds_url_freq = "/entry/data0/frequency"
    
    
        self._ds_amp = self._hf.get_dataset(ds_url_amp)
        self._ds_pha = self._hf.get_dataset(ds_url_pha)
    
        self._amplitude = np.array(self._hf[ds_url_amp],dtype=np.float64)
        self._phase = np.array(self._hf[ds_url_pha],dtype=np.float64)
        self._frequency = np.array(self._hf[ds_url_freq],dtype=np.float64)
    

        self._x_co = self._hf.get_dataset(self._ds_amp.x_ds_url)
 
        self._prepared_datasets = True

    def _prepare_find_jumps(self):
        self.qps_jpn_nr    = self._hf.add_value_vector('qps_jpn_nr', folder = 'analysis', 
                                                    x = self._x_co, unit = 'Num')
        self.qps_jpn_hight = self._hf.add_value_vector('qps_jpn_hight', folder = 'analysis', 
                                                    x = self._x_co, unit = 'Hz')
        self.qps_jpn_spec  = self._hf.add_value_vector('qps_jpn_spec', folder = 'analysis', 
                                                    x = self._x_co, unit = 'Hz')

    def find_jumps(self,ds, threshold = 40000):
        self._prepare_find_jumps()
        ds = self._hf[ds]
        ds = gaussian_filter1d(ds,2)
        offset=ds[0]
        jpnh = 0
        for i in xrange(ds.shape[0]-3):
            #i +=3
            #df=(((ds[i+1]+ds[i+2]+ds[i+3])/3.)-ds[i])
            #df=(ds[i] - ((ds[i-1]+ds[i-2]+ds[i-3])/3.))
            df=((ds[i+1])-ds[i])
            if (abs(df)>threshold):
                self.qps_jpn_nr.append(1.)
                offset = offset-df
                jpnh = df
                #print df, offset
                self.qps_jpn_hight.append(abs(float(jpnh)))
                
                self.qps_jpn_spec.append(float(ds[i]+offset))
                jpnh = df
            
            else:
                self.qps_jpn_nr.append(0.)
                #self.qps_jpn_hight.append(float(jpnh))
                self.qps_jpn_spec.append(float(ds[i]+offset))
    def find_jumps2(self,ds,threshold=30000):
        self._prepare_find_jumps()
        ds = self._hf[ds]
        offset=ds[0]
        # first we remove a bit of noise
        #flt = gaussian_filter1d(ds,10)
        flt = median_filter(ds,size=10)
        #flt = ds
        # the sobel filter finds the "jumps" 
        sb=sobel(flt)
        for i in sb:
            self.qps_jpn_hight.append(float(i))
            
        for i in flt: self.qps_jpn_spec.append(float(i))
        """    
        for i in xrange(flt.shape[0]-1):
            if(abs(sb[i])>threshold):
                offset -= sb[i]
                
                self.qps_jpn_spec.append(float(flt[i]-offset))
            else:
                self.qps_jpn_spec.append(float(flt[i]-offset))
        """       

        #for i in sb
        
    def split_traces(self,ds,threshold=30000):
        self._prepare_find_jumps()
        ds = self._hf[ds]
        # first we remove a bit of noise, size is the number of averages
        #flt = gaussian_filter1d(ds,10)
        flt = median_filter(ds,size=3)
        #flt = ds
        # the sobel filter finds the "jumps" 
        sb=sobel(flt)
        for i in sb:
            self.qps_jpn_hight.append(float(i))
            
        #for i in flt: self.qps_jpn_spec.append(float(i))
        offset=ds[0]
        tr_num = 0
        tr_name = "qps_tr_"+str(tr_num)
        tr_obj =  self._hf.add_value_vector(tr_name, 
                                            folder = 'analysis', 
                                            x = self._x_co, 
                                            unit = 'Hz')
        keepout = 4
        for i,tr in enumerate(flt):
            keepout += 1
            if abs(sb[i])>threshold and keepout>3:
                keepout = 0
                # new trace
                tr_num +=1
                tr_name = "qps_tr_"+str(tr_num)
                tr_obj =  self._hf.add_value_vector(tr_name, 
                                                    folder = 'analysis', 
                                                    x =  self._x_co, 
                                                    unit = 'Hz')
                print tr , i
                #tr_obj.append(float(tr))
            else:
                if keepout>2:
                    tr_obj.append(float(tr-offset))
        
                
            
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="qps_rings: simple ring trace split/analysis/ KIT 2016 \n The traces have to be fitted first. Assumed is a skewed lorenzian fit.")

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    parser.add_argument('-tr','--threshold', type=float, help='(optional) treshold frequency for splitting the traces')
    #parser.add_argument('-fit','--fit-dataset',     type=str, help='dataset to split')

    args=parser.parse_args()
    if not args.file:
        print "please provide a hdf filename!"
        exit(1)
    qr = qps_ring(args.file)
    if args.threshold:
        qr.split_traces('/entry/analysis0/sklr_f0', threshold = args.threshold)
    else:
        qr.split_traces('/entry/analysis0/sklr_f0')