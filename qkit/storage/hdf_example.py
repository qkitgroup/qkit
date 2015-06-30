# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 00:16:06 2015

@author: hrotzing
"""
#import sys
#sys.path.append("/Users/hrotzing/pik/devel/python/qkit")
try:
    from qkit.storage import hdf_lib as hl
except ImportError:
    import hdf_lib as hl
## for random data
from numpy.random import rand
from numpy import linspace,arange
nop = 100
##


# first create a data object , if path is set to None or is omitted, a new path will be created
h5d = hl.Data(name='VNA_tracedata', path = None)

# measurement setup:
# add_coordinate()    <- for measurement boundaries/steps
# options: name (mandatory)
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")
f_co = h5d.add_coordinate('frequency', unit = "Hz", comment = "VNA frequency scan")
I_co = h5d.add_coordinate('current',   unit = "A",  comment = "magnetic field current")

# add_value_vector()    <- for measurement data
# options: name (mandatory)
#        : x = X  (optional) coordinate vector in x direction, default: None
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")

T_vec = h5d.add_value_vector('temperature', x = None, unit = "K", comment = "save temperature values")

# add_value_matrix()    <- for measurement data
# options: name (mandatory)
#        : x = X  (optional) coordinate vector in x direction, default: None
#        : y = Y  (mandatory) coordinate vector in y direction
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")


amp_mx = h5d.add_value_matrix('amplitude', x = I_co , y = f_co, unit = "V", comment = "magic data")
pha_mx = h5d.add_value_matrix('phase',     x = I_co , y = f_co, unit = "rad", comment = "more magic data!")



# now we add data to the file
fs = linspace(1e9,5e9,nop)
Is = linspace(1e-3,10e-3,nop)
f_co.add(fs)
I_co.add(Is)

for i in arange(1000):
    amp = rand(nop)
    pha = rand(nop)
    amp_mx.append(amp)
    pha_mx.append(pha)
    T_vec.append(float(rand(1)))
    
print h5d.get_filepath()
h5d.close()
