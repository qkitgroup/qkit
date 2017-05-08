import os
import logging

class SpyView():

    def __init__(self, dataobject):
        self._data = dataobject
        self._meta_info = {}

    def get_meta_info(self):
        '''
        This retreives the necessary information from a data object
        for writing a '.meta.txt' file as used by spyview.
        '''

        ncoords = self._data.get_ncoordinates()
        if ncoords not in (2,3):
            loggin.error('this function currently only supports data files \
                    with 2 or 3 coordinate dimensions. The data provided has \
                    %d coordinate dimensions', ncoords)

        self._meta_info['ncoords'] = ncoords

        info = self._data.get_dimensions()[0]
        self._meta_info['xlabel'] = info.get('name', None)
        self._meta_info['xstart'] = info.get('start', None)
        self._meta_info['xend'] = info.get('end', None)
        self._meta_info['xsize'] = info.get('size', None)

        info = self._data.get_dimensions()[1]
        self._meta_info['ylabel'] = info.get('name', None)
        self._meta_info['ystart'] = info.get('start', None)
        self._meta_info['yend'] = info.get('end', None)
        self._meta_info['ysize'] = info.get('size', None)

        if ncoords == 3:
            info = self._data.get_dimensions()[2]
            self._meta_info['zlabel'] = info.get('name', None)
            self._meta_info['zstart'] = info.get('start', None)
            self._meta_info['zend'] = info.get('end', None)
            self._meta_info['zsize'] = info.get('size', None)
        else:
            self._meta_info['zlabel'] = 'none'
            self._meta_info['zstart'] = 0
            self._meta_info['zend'] = 0
            self._meta_info['zsize'] = 1

        nvals = self._data.get_nvalues()
        self._meta_info['nvals'] = nvals

        for i in range(nvals):
            self._meta_info['val%d_label' % i] = self._data.get_dimension_name(ncoords + i)
            self._meta_info['val%d_colnr' % i] = ncoords + i

        return self._meta_info

    def write_meta_file(self):
        '''
        Writes meta-data file for spyview. The name will be
        automatically generated from the name of the data file:
        <data-file>.meta.txt
        '''
        if len(self._meta_info) == 0:
            self.get_meta_info()

        if None in self._meta_info.values():
            logging.warning('spyview: not enough info for making meta.txt file')
            return

        datafilename = self._data.get_filepath()
        name, ext = os.path.splitext(datafilename)
        metafilename = name + '.meta.txt'
        f = file(metafilename, 'w')

        KEYLIST = [ ('xsize',   '%d'),
                    ('xstart',  '%e'),
                    ('xend',    '%e'),
                    ('xlabel',  '%s'),
                    ('ysize',   '%d'),
                    ('ystart',  '%e'),
                    ('yend',    '%e'),
                    ('ylabel',  '%s'),
                    ('zsize',   '%d'),
                    ('zstart',  '%e'),
                    ('zend',    '%e'),
                    ('zlabel',  '%s') ]

        for key, fmt in KEYLIST:
            f.write( (fmt + '\n') % self._meta_info[key])

        for i in range(self._meta_info['nvals']):
            f.write('%d\n' % self._meta_info['val%d_colnr' % i])
            f.write('%s\n' % self._meta_info['val%d_label' % i])

        f.close()
