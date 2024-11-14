# AS @ KIT 04/2015
# modified JB 04/2016
# modified MP 05/2017 switch from pickle to JSON
# Sample Class to define all values necessary to measure a sample

import json, pickle
import logging
import os, copy

from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator as dtg

import qkit

class Sample(object):
    '''
    Sample Class to define all values necessary to measure a sample
    '''
    def __init__(self, path=None):
        self.name = 'Arbitrary Sample'
        self.comment = ''
        if path:
            self.load(path)
            
    def get(self,argname,default=None):
        '''
        Gets an argument of the sample and returns default, if it does not exist.
        '''
        return self.__dict__.get(argname,default)
        

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

        if not os.path.splitext(path)[-1] == '.sample':
            path = path + '.sample'

        copydict = copy.copy(self.__dict__)
        with open(path,'w+') as filehandler:
            json.dump(obj=copydict, fp=filehandler, cls=QkitJSONEncoder, indent = 4, sort_keys=True)
        return path

    def load(self, filename):
        '''
        load sample keys and entries to current sample instance
        '''

        if not os.path.isabs(filename):
            filename = os.path.join(qkit.cfg.get('datadir'),filename)

        try:
            with open(filename) as filehandle:
                self._load_legacy_pickle(filehandle)
            return
        except: pass

        with open(filename) as filehandle:
            self.__dict__ = json.load(filehandle, cls = QkitJSONDecoder)

    def _load_legacy_pickle(self, filehandle):
        self.__dict__ = pickle.loads(filehandle.read().split('<PICKLE PACKET BEGINS HERE>')[1].strip().replace('\r\n', '\n'))

        copydict = copy.copy(self.__dict__)
        for key in sorted(copydict):
            if ('xxxx'+str(copydict[key]))[-4:] == ' ins':   #instrument
                self.__dict__[key] = qkit.instruments.get(copydict[key][:-4])
