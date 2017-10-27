# AS @ KIT 04/2015
# modified JB 04/2016
# modified MP 05/2017 switch from pickle to JSON
# Sample Class to define all values necessary to measure a sample

import time
import json, pickle
import logging
import os, copy
import numpy as np

from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator as dtg

import qkit.core.qt as qt

class Sample(object):
    '''
    Sample Class to define all values necessary to measure a sample
    '''
    def __init__(self):
        self.name = 'Arbitrary Sample'
        self.comment = ''

    def update_instruments(self):
        '''
        Updates the following values:
        - awg clock
        - qubit_mw_src power
        - qubit_mw_src f01-iq_frequency
        '''
        try:
            self.awg
            self.clock
            self.qubit_mw_src
            self.f01
            self.iq_frequency
            self.mw_power
        except AttributeError or NameError:
            logging.error('Relevant instruments and attributes not properly specified.')
        else:
            if self.awg == None:
                logging.error(__name__ + ' : awg not defined')
            else:
                self.awg.set_clock(self.clock)

            if self.qubit_mw_src == None:
                logging.error(__name__ + ' : qubit_mw_src not defined')
            else:
                self.qubit_mw_src.set_frequency(self.f01-self.iq_frequency)
                self.qubit_mw_src.set_power(self.mw_power)

    def set_times(self,tpi):
        '''
        pass tpi to this function and it will update tpi as well as tpi2 = tpi/2
        '''
        self.tpi  = tpi
        self.tpi2 = tpi/2.


    def get_all(self):
        '''
        return all keys and entries of sample instance
        '''
        msg = ""
        copydict = copy.copy(self.__dict__)
        for key in sorted(copydict):
            msg+= str(key) + ":   " + str(copydict[key])+"\n"
        return msg

    def save(self,filename=None):
        '''
        save sample object.
        Filename can either be:
            - a full (absolute) path to the sample file or
            - any other string that is added to the filename in the data dir
            - None (default), the the sample object is stored in the data dir.
            
        returns the location of the sample file
        '''
        if filename is None or not(os.path.isabs(filename)):
            d = dtg()
            path = d.new_filename(filename)['_folder']
        else:
            path = filename

        if not os.path.exists(os.path.split(path)[0]):
            os.makedirs(os.path.split(path)[0])

        copydict = copy.copy(self.__dict__)
        with open(path+'.sample','w+') as filehandler:
            json.dump(obj=copydict, fp=filehandler, cls=QkitJSONEncoder, indent = 4, sort_keys=True)
        return str(path+'.sample')

    def load(self, filename):
        '''
        load sample keys and entries to current sample instance
        '''

        if not os.path.isabs(filename):
            filename = os.path.join(qt.config.get('datadir'),filename)

        try:
            with open(filename) as filehandle:
                self._load_legacy_pickle(filehandle)
            return
        except: pass

        with open(filename) as filehandle:
            self.__dict__ = json.load(filehandle, cls = QkitJSONDecoder)

    def _load_legacy_pickle(self, filehandle):
        self.__dict__ = pickle.loads(filehandle.read().split("<PICKLE PACKET BEGINS HERE>\n")[1])

        copydict = copy.copy(self.__dict__)
        for key in sorted(copydict):
            if ('xxxx'+str(copydict[key]))[-4:] == ' ins':   #instrument
                self.__dict__[key] = qt.instruments.get(copydict[key][:-4])
