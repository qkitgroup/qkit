# File name: read_qtlab_settingsfile.py
#
# This example should be run with "execfile('read_qtlab_settingsfile.py')"
#
# it shows how to read back the information from an instrument settingsfile

from numpy import pi, linspace, sinc
from lib.file_support.settingsfile import SettingsFile
from pprint import pprint

x_vec = linspace(-2 * pi, 2 * pi, 200)

qt.mstart()

data = qt.Data(name='testmeasurement')
data.add_coordinate('X')
data.add_value('Y')
data.create_file()

plot3d = qt.Plot2D(data, name='measure2D', coorddims=0, valdim=1)

for x in x_vec:

    result = sinc(x)
    data.add_data_point(x, result)
    qt.msleep(0.02)

data.close_file()
qt.mend()

st = SettingsFile(data.get_filepath())
print '\n Get the list of instruments with "get_instruments()": \n'
pprint( st.get_instruments() )
print '\n Get the full dictionary of settings with "get_settings()": \n'
pprint( st.get_settings() )
print '\n Get a single instrument setting with "get(ins, param)": \n'
print st.get('example1', 'gain')
