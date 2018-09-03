# DATA class v1.0 written by HR,JB@KIT 2011, 2016

'''
DATA exchange class, also holds global variables for thread management. 
Generalized version based on TIP.
'''


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import time
import os
from threading import Lock
import numpy as np

from qkit.storage import store as hdf_lib
from qkit.gui.plot import plot as qviewkit

class DATA(object):
    '''
    DATA class. Controls all access to parameter values and stored data.
    '''
    class LOCALHOST(object):
        def __init__(self,config):
            self.name = config.get('LOCALHOST','name')
            self.ip   = config.get('LOCALHOST','ip')
            self.port = config.getint('LOCALHOST','port')
    class REMOTEHOST(object):
        def __init__(self,config):
            self.name = config.get('REMOTEHOST','name')
            self.ip   = config.get('REMOTEHOST','ip')
            self.port = config.getint('REMOTEHOST','port')
            
    class PARAMETER(object):
        def __init__(self,config,p_index,p_attr):
            '''
            Initialize parameter attributes, mostly taken from the config file.
            '''
            self.p_index = p_index
            self.name = config.get(str(p_attr),'name')
            self.interval = config.getfloat(str(p_attr),'interval')
            self.data_request_object = lambda: 0   #this is written by server_main.py
            self.value = 0
            self.timestamp = 0
            self.next_schedule = time.time() + self.interval
            self.logging = bool(int(config.get(str(p_attr),'logging')))
            self.log_path = config.get(str(p_attr),'log_path')
            self.log_lock = Lock()
            self.url_timestamps = None
            print("Parameter %s loaded."%str(self.name))
            
        def get_all(self):
            '''
            Get all parameter attributes.
            '''
            with Lock():
                return {
                    "parameter": self.p_index,
                    "name":self.name,
                    "interval":self.interval,
                    "value":self.value,
                    "timestamp":self.timestamp,
                    "next_schedule":self.next_schedule,
                    }

        def set_interval(self,interval):
            '''
            Setup the scheduling, which corresponds to the value request interval.
            '''
            interval = float(interval)
            if interval == 0:
                interval = 120*365*24*3600 #120 years
            self.next_schedule += -self.interval+interval #update next schedule
            self.interval = interval   
        
        def get_last_value(self):
            with Lock():
                return self.value
        def get_timestamp(self):
            with Lock():
                return self.timestamp
        
        def get_history(self,range,nchunks=100):
            '''
            Read out the h5 file.
            - range: history data range
            - nchunks: number of data points to be returned
            '''
            
            if self.url_timestamps != None:
                try:
                    with self.log_lock:
                        timestamps = np.array(self.hf[self.url_timestamps])
                        values = np.array(self.hf[self.url_values])
                    data_points_requested_mask = np.where(time.time()-timestamps < range*3600)
                    timestamps_requested = timestamps[data_points_requested_mask]
                    data_points_requested = values[data_points_requested_mask]
                    #return only nchunks data points
                    if len(data_points_requested) > nchunks:
                        timestamp_chunks = np.array(np.split(timestamps_requested[:(len(timestamps_requested)-len(timestamps_requested)%nchunks)],nchunks))
                        timestamps = timestamp_chunks[:,int(0.5*len(timestamps_requested)/nchunks)]
                        data_chunks = np.array(np.split(data_points_requested[:(len(data_points_requested)-len(data_points_requested)%nchunks)],nchunks))
                        #calculate medians and return them instead of the mean (due to runaways in the log file)
                        medians = np.sort(data_chunks,axis=-1)[:,int(0.5*len(data_points_requested)/nchunks)]
                        return [timestamps,medians]
                    else:
                        return [timestamps_requested,data_points_requested]
                    
                except KeyError:   #AttributeError, NameError:
                    print('Error opening h5 log file.')
                    return [0]
            else:
                return [0]
        
        def store_value(self,value):
            '''
            Store method, used by the worker.
            '''
            with Lock():
                try:
                    self.value = float(value)
                except ValueError:
                    print('type cast error, ignoring')
                self.timestamp = time.time()
            if self.logging:
                self.append_to_log()
                
        def create_logfile(self):
            print('Create new log file for parameter %s.'%self.name)
            self.fname = os.path.join(self.log_path,self.name.replace(' ','_')+time.strftime('%d%m%Y%H%M%S')+'.h5')
            #print self.fname
            self.hf = hdf_lib.Data(self.fname, mode='a')
            self.hdf_t = self.hf.add_coordinate('timestamps')
            self.hdf_v = self.hf.add_value_vector('values', x = self.hdf_t)
            self.url_timestamps = '/entry/data0/timestamps'
            self.url_values = '/entry/data0/values'
            view = self.hf.add_view('data_vs_time', x = self.hdf_t, y = self.hdf_v)   #fit
        
        def append_to_log(self):
            with self.log_lock:
                self.hdf_t.append(float(self.get_timestamp()))
                self.hdf_v.append(float(self.get_last_value()))
            
        def close_logfile(self):
            self.hf.close_file()
        
        def schedule(self):
            '''
            Specifiy whether the parameter is to be updated, 
            typicalled called in each worker iteration. 
            Returns True if new parameter value needs to be read.
            '''
            if time.time() > self.next_schedule:
                while time.time() > self.next_schedule:
                    self.next_schedule += self.interval
                return True
            else:
                return False

        def set_schedule(self):
            self.next_schedule = time.time()
            return True
    
    def __init__(self,config):
        '''
        Reads the cfg file and instanciates all parameters accordingly.
        '''
        self.wants_abort = False
        self.debug = True
        self.cycle_time = config.getfloat('worker','cycle_time')
        
        p_instances = config.get('parameters','p').split(",")   #parameter instance names
        #print(p_instances)
        self.parameters = [self.PARAMETER(config,i,p) for i,p in enumerate(p_instances)]   #instanciate parameter array
        for i,p_i in enumerate(p_instances):   #create human readable aliases, such that objects are accessible from clients according to the seetings.cfg entry in []
            setattr(self,str(p_i),self.parameters[i])
        
        self.localhost = self.LOCALHOST(config)
        #self.remotehost = self.REMOTEHOST(config)
        self.ctrl_lock = Lock()

    def atexit(self):
        self.set_wants_abort()

    def get_wants_abort(self):
        with self.ctrl_lock:
            return self.wants_abort
    def set_wants_abort(self):
        with self.ctrl_lock:
            self.wants_abort = True
        

if __name__ == "__main__":
    DATA = DATA()
