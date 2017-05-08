# Load matplotlib and select the GTK Agg back-end
import matplotlib as mpl
mpl.use('gtkagg')

# Load pyplot wrappers and set interactive mode on
import matplotlib.pyplot as plt
plt.ion()

# Create a plot
import numpy as np
xs = np.arange(0, 10, 0.1)
ys = xs**2
plt.plot(xs, ys)

