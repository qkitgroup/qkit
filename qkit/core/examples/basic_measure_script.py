# File name: basic_measure_script.py
#
# This example should be run with "execfile('basic_measure_script.py')"

from numpy import pi, random, arange, size
from time import time,sleep

#####################################################
# this part is to simulate some data, you can skip it
#####################################################

# fake data
def lorentzian(x, center, width):
    return 1/pi*(0.5*width)/((x-center)**2+(0.5*width)**2)

def addnoise(x, variance):
    return x+variance*random.randn(size(x))

def fake_data(x,y):
    return addnoise(lorentzian(x,y*y/5+1,0.1),0.1)[0]

# fake instruments
def fake_ivvi_set_dac_3(val):
    global fake_dac_3
    fake_dac_3 = val

def fake_mw_src_set_freq(val):
    global fake_freq
    fake_freq = val

def fake_readout_psw():
    global fake_dac_3, fake_freq
    return fake_data(fake_freq, fake_dac_3)


#####################################################
# here is where the actual measurement program starts
#####################################################

# you define two vectors of what you want to sweep. In this case
# a magnetic field (b_vec) and a frequency (f_vec)
f_vec = arange(0,10,0.01)
b_vec = arange(-5,5,0.1)

# you indicate that a measurement is about to start and other
# processes should stop (like batterycheckers, or temperature
# monitors)
qt.mstart()

# Next a new data object is made.
# The file will be placed in the folder:
# <datadir>/<datestamp>/<timestamp>_testmeasurement/
# and will be called:
# <timestamp>_testmeasurement.dat
# to find out what 'datadir' is set to, type: qt.config.get('datadir')
data = qt.Data(name='testmeasurement')

# Now you provide the information of what data will be saved in the
# datafile. A distinction is made between 'coordinates', and 'values'.
# Coordinates are the parameters that you sweep, values are the
# parameters that you readout (the result of an experiment). This
# information is used later for plotting purposes.
# Adding coordinate and value info is optional, but recommended.
# If you don't supply it, the data class will guess your data format.
data.add_coordinate('frequency, mw src 1 [Hz]')
data.add_coordinate('Bfield, ivvi dac 3 [mV]')
data.add_value('Psw SQUID')

# The next command will actually create the dirs and files, based
# on the information provided above. Additionally a settingsfile
# is created containing the current settings of all the instruments.
data.create_file()

# Next two plot-objects are created. First argument is the data object
# that needs to be plotted. To prevent new windows from popping up each
# measurement a 'name' can be provided so that window can be reused.
# If the 'name' doesn't already exists, a new window with that name
# will be created. For 3d plots, a plotting style is set.
plot2d = qt.Plot2D(data, name='measure2D', coorddim=0, valdim=2, traceofs=10)
plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

# preparation is done, now start the measurement.
# It is actually a simple loop.
for b in b_vec:
    # set the magnetic field
    fake_ivvi_set_dac_3(b)
    for f in f_vec:
        # set the frequency
        fake_mw_src_set_freq(f)

        # readout
        result = fake_readout_psw()

        # save the data point to the file, this will automatically trigger
        # the plot windows to update
        data.add_data_point(f, b, result)

        # the next function is necessary to keep the gui responsive. It
        # checks for instance if the 'stop' button is pushed. It also checks
        # if the plots need updating.
        qt.msleep(0.001)

    # the next line defines the end of a single 'block', which is when sweeping
    # the most inner loop finishes. An empty line is put in the datafile, and
    # the 3d plot is updated.
    data.new_block()

# after the measurement ends, you need to close the data file.
data.close_file()
# lastly tell the secondary processes (if any) that they are allowed to start again.
qt.mend()
