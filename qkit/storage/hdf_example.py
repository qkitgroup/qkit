# -*- coding: utf-8 -*-
"""
Created on Sun Jun 21 00:16:06 2015

@author: hrotzing
"""
#import sys
#sys.path.append("/Users/hrotzing/pik/devel/python/qkit")
import time
try:
    from qkit.storage import hdf_lib as hl
except ImportError:
    import hdf_lib as hl
## for random data
from numpy.random import rand
from numpy import linspace,arange
nop = 101
##


# first create a data object , if path is set to None or is omitted, a new path will be created
h5d = hl.Data(name='VNA_tracedata', path = "./test2.h5")

# comment added to the hdf (internal) folder
# options : comment (mandatory)
#        : folder='data' | 'analysis' (optional, default is "data") 
h5d.add_comment("New data has been created ....") 

# measurement setup:
# add_coordinate()    <- for measurement boundaries/steps
# options: name (mandatory)
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")
#        : folder='data' | 'analysis' (optional, default is "data") 
f_co = h5d.add_coordinate('frequency', unit = "Hz", comment = "VNA frequency scan")
I_co = h5d.add_coordinate('current',   unit = "A",  comment = "magnetic field current")
P_co = h5d.add_coordinate('power',   unit = "dBm",  comment = "microwave power")
# add_value_vector()    <- for measurement data
# options: name (mandatory)
#        : x = X  (optional) coordinate vector in x direction, default: None
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")
#        : folder='data' | 'analysis' (optional, default is "data") 

T_vec = h5d.add_value_vector('temperature', x = None, unit = "K", comment = "save temperature values") 
Tc_vec = h5d.add_value_vector('critical_temperature', x = I_co, unit = "K", folder='analysis' ,comment = "save temperature values")

TvsTc_view = h5d.add_view("f_vs_I", x= f_co, y = I_co)
TvsTc_view.add("TvsTc",x=T_vec,y=Tc_vec)
# add_value_matrix()    <- for measurement data
# convention: the last coordiante should be the one with the fastest changes:
#             e.g.  for a VNA scan x= magnetic field y= transmission frequency
# 
# options: name (mandatory)
#        : x = X  (optional) coordinate vector in x direction, default: None
#        : y = Y  (mandatory) coordinate vector in y direction / fastest changes
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")
#        : folder='data' | 'analysis' (optional, default is "data") 


amp_mx = h5d.add_value_matrix('amplitude', x = I_co , y = f_co, unit = "V", comment = "magic data")
pha_mx = h5d.add_value_matrix('phase',     x = I_co , y = f_co, unit = "rad", comment = "more magic data!")



# add_value_box()    <- for measurement data
# options: name (mandatory)
#        : x = X  (optional) coordinate vector in x direction, default: None
#        : y = Y  (optional) coordinate vector in y direction
#        : z = Z  (mandatory) coordinate vector in y direction /  fastest changes
#        : unit = "" (optional, default is "a.u.")
#        : comment = "" (optional, default is "")
#        : folder='data' | 'analysis' (optional, default is "data") 


amp_bx = h5d.add_value_box('amplitude', x = I_co , y = f_co, z= P_co, unit = "V", comment = "magic data")
pha_bx = h5d.add_value_box('phase',     x = I_co , y = f_co, z= P_co, unit = "rad", comment = "more magic data!")





# now we add the coordinate data to the file
fs = linspace(1e9,5e9,nop)
Is = linspace(0e-3,10e-3,nop)
#print Is
f_co.add(fs)
I_co.add(Is)

for i in arange(nop):
    #time.sleep(10)
    amp = rand(nop)
    pha = rand(nop)
    amp_mx.append(amp)
    pha_mx.append(pha)
    T_vec.append(float(rand(1)))
    Tc_vec.append(float(rand(1)))


print h5d.get_filepath()
h5d.close_file()
