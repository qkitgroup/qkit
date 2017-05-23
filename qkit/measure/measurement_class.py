# MP, AS @ KIT 05/2017
# Class to collect all information about a single measurement

import json
import os, copy
import qt
from qkit.measure.json_handler import QkitJSONEncoder, QkitJSONDecoder
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

    def get_JSON(self):
        """
        Returns JSON string of all attributes. The function is mostly used for saving in .h5.
        """
        copydict = copy.copy(self.__dict__)
        if copydict['sample']:
            copydict['sample'] = copydict['sample'].__dict__ # change entry to dict to make it readable for JSONEncoder
        return json.dumps(obj=copydict, cls=QkitJSONEncoder, indent = 4, sort_keys=True)

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
            self.__dict__ = json.load(filehandle, cls = QkitJSONDecoder)

        s = Sample()
        s.__dict__ = self.__dict__['sample']
        self.__dict__['sample'] = s