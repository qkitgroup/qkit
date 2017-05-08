# File name: spyview.py
#
# This example should be run with "execfile('spyview.py')"

from numpy import pi, linspace, sinc, sqrt
from lib.file_support.spyview import SpyView

x_vec = linspace(-2 * pi, 2 * pi, 100)
y_vec = linspace(-2 * pi, 2 * pi, 100)

qt.mstart()

data = qt.Data(name='testmeasurement')

# to make the spyview meta.txt file dimension info is required:
data.add_coordinate('X',
        size=len(x_vec),
        start=x_vec[0],
        end=x_vec[-1])
data.add_coordinate('Y',
        size=len(y_vec),
        start=y_vec[0],
        end=y_vec[-1])
data.add_value('Z')

data.create_file()

plot3d = qt.Plot3D(data, name='measure3D', coorddims=(0,1), valdim=2, style='image')

for y in y_vec:
    for x in x_vec:

        result = sinc(sqrt(x**2 + y**2))
        data.add_data_point(x, y, result)
        qt.msleep(0.001)

    data.new_block()

data.close_file()
qt.mend()

# create the spyview meta.txt file:
SpyView(data).write_meta_file()
