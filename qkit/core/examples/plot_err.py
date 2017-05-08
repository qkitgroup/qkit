import numpy as np
import qt

x = np.arange(-10, 10, 0.2)
y = np.sinc(x)
yerr = 0.1*np.random.rand(len(x))

d = qt.Data()
d.add_coordinate('x')
d.add_coordinate('y')
d.add_coordinate('yerr')
d.create_file()
d.add_data_point(x,y,yerr)

p = qt.Plot2D()
p.add_data(d, coorddim=0, valdim=1, yerrdim=2)

# or: ('ok' is style for black circles)
qt.plot(x, y, 'ok', yerr=yerr, name='test2')
