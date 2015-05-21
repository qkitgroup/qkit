#!/usr/bin/env python 
# -*- coding: utf-8 -*-



import h5py
import re
import types
import os, sys
import numpy

import argparse

class H5_file(object):
    def __init__(self,output_file):
        self.hf = h5py.File(output_file,'w')
        # make the structure compatible with the nexus format
        # first the entry group
        self.hf.attrs.create("NeXus_version","4.3.0")
        self.entry = self.hf.create_group("entry")
        self.entry.attrs.create("NX_class","NXentry")
        # create a nexus data group        
        self.grp = self.entry.create_group("data")
        self.grp.attrs.create("NX_class","NXdata")
        
    def h5_create_dataset(self,name,tracelength):
        
        # handle one and two dimensional data
        if tracelength:
            shape    = (100,tracelength)
            maxshape = (None,tracelength)
        else:
            shape     = (100,)
            maxshape  = (None,)
            
        #create the dataset            
        ds = self.grp.create_dataset(name, shape, maxshape=maxshape)
        
        # keep track of the actual fill of an array.
        ds.attrs.create("fill",0)
        ds.attrs.create("name",name)
        ds.attrs.create("units","#")
        return ds
        
    def h5_append(self,ds,data):
        """ Append method for hdf5 data. """
        fill = ds.attrs.get("fill")
        try:
            ds[fill] = data
            ds.attrs.modify("fill",fill+1)
            
        except ValueError:
            # array full...
            new_size = (ds.shape[0])+100
            ds.resize(new_size, axis=0)
            print "resized at fill:", fill
            
            ds[fill] = data
            ds.attrs.modify("fill",fill+1)
            
            
    def h5_close_file(self):
        for ds in self.grp.itervalues():
                fill  = ds.attrs.get("fill")
                if fill > 0:
                    ds.resize(fill,axis=0)
              
        self.hf.close()
        
                


class gp_data(object):

    _METADATA_INFO = {
        'instrument': {
            're': re.compile('^#[ \t]*Ins?trument: ?(.*)$', re.I),
            'type': types.StringType
        },
        'parameter': {
            're': re.compile('^#[ \t]*Parameter: ?(.*)$', re.I),
            'type': types.StringType
        },
        'units': {
            're': re.compile('^#[ \t]*Units?: ?(.*)$', re.I),
            'type': types.StringType
        },
        'steps': {
            're': re.compile('^#[ \t]*Steps?: ?(.*)$', re.I),
            'type': types.IntType
        },
        'stepsize': {
            're': re.compile('^#[ \t]*Stepsizes?: ?(.*)$', re.I),
            'type': types.FloatType
        },
        'name': {
            're': re.compile('^#[ \t]*Name: ?(.*)$', re.I),
            'type': types.StringType
        },
        'type': {
            're': re.compile('^#[ \t]*Type?: ?(.*)$', re.I),
            'type': types.StringType,
            'function': lambda self, type: self._type_added(type)
        },
    }

    _META_STEPRE = re.compile('^#.*[ \t](\d+) steps', re.I)
    _META_COLRE = re.compile('^#.*Column ?(\d+)', re.I)
    _META_COMMENTRE = re.compile('^#(.*)', re.I)

    _INT_TYPES = (
            types.IntType, types.LongType,
            numpy.int, numpy.int0, numpy.int8,
            numpy.int16, numpy.int32, numpy.int64,
    )

    def __init__(self,filename, outfile):
        print "oj load"
        #self._dir = filedir
        self._filename = filename
        self._ncoordinates = 0
        self._of = outfile
        
    def get_filename(self):
        return self._filename
    def get_filepath(self):
        return self._filename
        #return os.path.join(self._dir, self._filename)
    
    def set_col_types(self,col_types):
        def sv_sw(x):
            if x.lower() =='s': return False
            if x.lower() =='v': return True
            else: 
                print "Type either V or S!"
                raise TypeError
        
        self.col_types =  map(sv_sw,col_types)
    
    def set_col_names(self,col_names):
        self.col_names =  col_names
        
    def _load_file(self):
        
        """
        Load data from file and store in the hdf file.
        """
        print "creating hdf_file"
        # create an empty hdf file
        self.h5f = H5_file(self._of)
        
        
        
        try:
            f = file(self.get_filepath(), 'r')
        except:
            print('Unable to open file %s' % self.get_filepath())
            return False

        self._dimensions = []
        self._values = []
        self._comment = []
        
        # data colums 
        # create empty datasets
        dc= []
        for i,v in enumerate(self.col_names):
            dc.append([])
        
        
        ds = []        
        
        nfields = 0

        self._block_sizes = []
        self._npoints = 0
        self._npoints_last_block = 0
        self._npoints_max_block = 0

        blocksize = 0
        first_block = True
        for line in f:
            line = line.rstrip(' \n\t\r')

            # Count blocks
            if len(line) == 0 and len(dc[0]) > 0:
                self._block_sizes.append(blocksize)
                
                if blocksize > self._npoints_max_block:
                    self._npoints_max_block = blocksize
                blocksize = 0
                # here we save the data to the hdf file                    
                # we have now enough information to guess the trace length
                if first_block:
                    first_block = False
                    tracelength = len(dc[0])
                    if len(dc[0]) != len(dc[-1]):
                        print('Error while detecting dimension size')
                    print "tracelength detected  = ", tracelength
                    for i, col_name in enumerate(self.col_names):
                        if self.col_types[i]:
                            # is a list of vectors of length tracelength
                            ds.append(self.h5f.h5_create_dataset(col_name,tracelength))
                        else:
                            # is a list of scalars of length 1, well 0
                            ds.append(self.h5f.h5_create_dataset(col_name,0))
                    #dS_It  = self.h5f.h5_create_dataset("It",tracelength)
                    #dS_time = self.h5f.h5_create_dataset("time",tracelength)
                    #dS_A = self.h5f.h5_create_dataset("Amp",tracelength)
                    #dS_P  = self.h5f.h5_create_dataset("Phase",tracelength)
                #print len(dc0)
                for i, data_set in enumerate(ds):
                   
                    if self.col_types[i]:
                        
                        self.h5f.h5_append(data_set ,numpy.array(dc[i]))
                    else:
                        self.h5f.h5_append(data_set ,dc[i][0])
                
                #self.h5f.h5_append(dS_It,numpy.array(dc0))
                #self.h5f.h5_append(dS_time,numpy.array(dc1))
                #self.h5f.h5_append(dS_A,numpy.array(dc2))
                #self.h5f.h5_append(dS_P,numpy.array(dc3))
                
                for i in range(len(dc)):
                    dc[i] = []
                
                
                                                                
            # Strip comment
            commentpos = line.find('#')
            if commentpos != -1:
                self._parse_meta_data(line)
                line = line[:commentpos]

            fields = line.split()
            if len(fields) > nfields:
                nfields = len(fields)

            fields = [float(fi) for fi in fields]
            
             # for now we simply hardcode the four columns
            if len(fields) > 0:
                for i, field in enumerate(fields):
                    dc[i].append(field)
                
                #dc0.append(fields[0])
                #dc1.append(fields[1])
                #dc2.append(fields[2])
                #dc3.append(fields[3])
                #dc3.append(fields[2])
                blocksize += 1
        
            
        #self._add_missing_dimensions(nfields)
        #self._count_coord_val_dims()

        #self._data = numpy.array(data)
        #self._npoints = len(self._data)
        #self._inmem = True

        self._npoints_last_block = blocksize

        self.h5f.h5_close_file()
        return True
        
    def _type_added(self, name):
        if name == 'coordinate':
            self._ncoordinates += 1
        elif name == 'values':
            self._nvalues += 1

    def _parse_meta_data(self, line):
        m = self._META_STEPRE.match(line)
        if m is not None:
            self._dimensions.append({'size': int(m.group(1))})
            return True

        m = self._META_COLRE.match(line)
        if m is not None:
            index = int(m.group(1))
            if index > len(self._dimensions):
                self._dimensions.append({})
            return True

        colnum = len(self._dimensions) - 1

        for tagname, metainfo in self._METADATA_INFO.iteritems():
            m = metainfo['re'].match(line)
            if m is not None:
                if metainfo['type'] == types.FloatType:
                    self._dimensions[colnum][tagname] = float(m.group(1))
                elif metainfo['type'] == types.IntType:
                    self._dimensions[colnum][tagname] = int(m.group(1))
                else:
                    try:
                        self._dimensions[colnum][tagname] = eval(m.group(1))
                    except:
                        self._dimensions[colnum][tagname] = m.group(1)

                if 'function' in metainfo:
                    metainfo['function'](self, m.group(1))
                
                print metainfo
                return True

        m = self._META_COMMENTRE.match(line)
        if m is not None:
            self._comment.append(m.group(1))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Qkit qtlab .dat to hdf file converter')
    parser.add_argument('infile',type=str,
                        help='Input .dat file')
    parser.add_argument('--outfile', type=str,
                        help='Output .h5 file')
    parser.add_argument('--cols', type=str, required=True,
                        help='Column names: comma separated list of Column names example: --columns Ampl,Phase,Bias,Current')
    parser.add_argument('--col_types',type=str, required=True,
                        help="Column types: [S]calar or [V]ector type  example: --column_type V,V,S,S")
                        
    args = parser.parse_args()
    
    col_names = []
    col_types = [] 
    col_names = args.cols.split(',')
    col_types = args.col_types.split(',')    
    if len(col_names) != len(col_types):
        print "ERROR: column names and column types do not match!" 
        print col_names
        print col_types
        sys.exit(1)
    print col_names
    print col_types
    #if True: sys.exit()
        
    outfile = args.infile.replace(".dat",".h5")
    if args.outfile: outfile = args.outfile
    df = gp_data (args.infile,outfile)
    df.set_col_names(col_names)
    df.set_col_types(col_types)
    df._load_file()
