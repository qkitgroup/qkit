import numpy as np
import qt

d = qt.Data()
d.add_coordinate('X')
d.add_value('Y')
d.create_file()
p = plot(d)

# Inform wrapper that a measurement has started
qt.mstart()

for x in arange(0, 40, 0.1):
    y = np.sin(x) + np.random.rand()/10
    d.add_data_point(x, y)

    # Sleep for 100msec and allow UI interaction
    qt.msleep(0.1)

# Inform wrapper that the measurement has ended
qt.mend()

d.close_file()
