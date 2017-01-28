#!/usr/bin/env python
# DATA class v1.0 written by HR,JB@KIT 2011, 2016

# DATA exchange class, also holds global variables for thread management
# data class generalized based on the TIP data class


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

from qkit.storage import hdf_lib
from qkit.gui.plot import plot as qviewkit


# DATA class, to be instanced with 'config' argument
class DATA(object):

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
            #print p_attr
            self.p_index = p_index
            #self.attribute_name = str(p_attr)
            self.name = config.get(str(p_attr),'name')
            self.interval = config.getfloat(str(p_attr),'interval')
            self.data_request_object = lambda: 0
            self.value = 0
            self.timestamp = 0
            self.next_schedule = time.time() + self.interval
            self.logging = bool(int(config.get(str(p_attr),'logging')))
            self.log_path = config.get(str(p_attr),'log_path')
            self.log_lock = Lock()
            self.url_timestamps = None
            print "Parameter %s loaded."%str(self.name)
            
        def get_all(self):
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
        
        def get_history(self,range):
            #read out h5 file
            if self.url_timestamps != None:
                try:
                    with self.log_lock:
                        timestamps = np.array(self.hf[self.url_timestamps])
                        values = np.array(self.hf[self.url_values])
                    data_points_requested = np.where(time.time()-timestamps < range*3600)
                    return [timestamps[data_points_requested],values[data_points_requested]]
                except KeyError:   #AttributeError, NameError:
                    print 'Error opening h5 log file.'
                    return [0]
            else:
                return [0]
        
        def store_value(self,value):
            with Lock():
                try:
                    self.value = float(value)
                except ValueError:
                    print 'type cast error, ignoring'
                self.timestamp = time.time()
            if self.logging:
                self.append_to_log()
                
        def create_logfile(self):
            print 'Create new log file for parameter %s.'%self.name
            self.fname = os.path.join(self.log_path,time.strftime('%m%Y')+'/',self.name.replace(' ','_')+time.strftime('%d%m%Y%M%S')+'.h5')
            print self.fname
            #if os.path.isfile(self.fname):   #h5 already exists
            #    self.hf = hdf_lib.Data(path=self.fname)
            #    self.hdf_t = self.hf.get_dataset(self.url_timestamps)   #has a bug in hdf_lib.py JB 12/2016
            #    self.hdf_v = self.hf.get_dataset(self.url_values)
            #else:
            self.hf = hdf_lib.Data(path=self.fname)
            self.hdf_t = self.hf.add_coordinate('timestamps')
            self.hdf_v = self.hf.add_value_vector('values', x = self.hdf_t)
            self.url_timestamps = '/entry/data0/timestamps'
            self.url_values = '/entry/data0/values'
            #qviewkit.plot(self.hf.get_filepath(), datasets=['value'])
        
        def append_to_log(self):
            with self.log_lock:
                self.hdf_t.append(float(self.get_timestamp()))
                self.hdf_v.append(float(self.get_last_value()))
            
        def close_logfile(self):
            self.hf.close_file()
        
        def schedule(self):
            '''
            specifiy whether the parameter is to be updated,
            typicalled called in each worker iteration
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
        
        self.wants_abort = False
        self.debug = True
        self.cycle_time = config.getfloat('worker','cycle_time')
        
        p_instances = config.get('parameters','p').split(",")   #parameter instance names
        #print p_instances
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
