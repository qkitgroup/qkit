# MP, AS @ KIT 05/2017
# Class to collect all information about a single measurement

import json
import os, copy, types
import numpy as np
import qt
from qkit.measure.samples_class import QkitJSONEncoder
from qkit.measure.samples_class import Sample

class Measurement(object):
    '''
    Measurement class to define general information about the specific measurement.
    '''
    def __init__(self):
        self.uuid = None
        self.hdf_relpath = ''
        self.sample = None
        self.web_visible = True
        self.rating = 3
        self.analyzed = False
        self.measurement_type = ''
        self.measurement_func = ''
        self.x_axis = ''
        self.y_axis = ''
        self.z_axis = ''

    def get_all(self):
        """
        Returns printable, organized string of all attributes. The 'real' "Measurement" attributes are in front, followed by the inherited sample attributes.
        The function is mostly used for saving in .h5.
        """
        copydict = copy.copy(self.__dict__)
        sample = copydict.pop('sample', None)

        ret = ''
        for key, value in sorted(copydict.items()):
            ret += str(key)+': '+str(value)+'\n'

        if sample:
            ret += 'sample:\n'
            sample_dict = sample.__dict__
            for key, value in sorted(sample_dict.items()):
                ret += '\t'+str(key)+': '+str(value)+'\n'
        return ret.rstrip()

    def save(self,filepath=None):
        '''
        Save sample object in the same directory as the measurement .h5 file or in the given filepath.
        '''
        
        if filepath:
            filepath=filepath
        else:
            filepath = os.path.join(qt.config.get('datadir'),self.hdf_relpath.replace('.h5', '.measurement'))

        copydict = copy.copy(self.__dict__)

        """
        Sample entry has to be converted to JSON first, to save information about datatype.
        """
        if copydict['sample']:
            copydict['sample'] = copydict['sample'].__dict__ # change entry to dict to make it readable for JSONEncoder
        with open(filepath,'w+') as filehandler:
            json.dump(obj=copydict, fp=filehandler, cls=QkitJSONEncoder, indent = 4, sort_keys=True)

    def load(self, filename):
        '''
        Load sample keys and entries to current sample instance.
        '''

        if not os.path.isabs(filename):
            filename = os.path.join(qt.config.get('datadir'),filename)

        with open(filename) as filehandle:
            self.__dict__ = json.load(filehandle)

        copydict = copy.copy(self.__dict__)
        for entry in sorted(copydict):
            if type(copydict[entry]) == types.DictType:
                if copydict[entry].has_key('dtype') and copydict[entry].has_key('content'): # non JSON standard, special handling
                    if copydict[entry]['dtype'] == 'ndarray': self.__dict__[entry] = np.array(copydict[entry]['content'])
                    if copydict[entry]['dtype'] == 'instance':  self.__dict__[entry] = qt.instruments.get(copydict[entry]['content'])
            """
            A "Sample" entry itself is a JSON encoded string of all attributes of the "Sample"-class.
            Such a decoded "Sample"-object is created here.
            """
            if entry == 'sample':
                s = Sample()
                s.__dict__ = copydict[entry]

                sample_dict = copy.copy(s.__dict__)
                for entry_s in sorted(sample_dict):
                    if type(sample_dict[entry_s]) == types.DictType:
                        if sample_dict[entry_s].has_key('dtype') and sample_dict[entry_s].has_key('content'): # non JSON standard, special handling
                            if sample_dict[entry_s]['dtype'] == 'ndarray': s.__dict__[entry_s] = np.array(sample_dict[entry_s]['content'])
                            if copydict[entry][entry_s]['dtype'] == 'instance':  s.__dict__[entry_s] = qt.instruments.get(sample_dict[entry_s]['content'])
                """
                The created "Sample"-object is an attribute of the measurement object.
                """
                self.__dict__[entry] = s