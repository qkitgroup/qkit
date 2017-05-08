import numpy as np

x = np.arange(-10, 10, 0.2)
y = np.sinc(x)
p = plot(x, y, 'ks',                    # x vs y with black squares
        title='sinc(x)',                # Trace title (in legend)
        legend=True,                    # Show legend
        plottitle='Plotting example',   # Plot title
        name='Functions',               # Plot window name
        clear=True,                     # Clear plot before adding trace
        grid=True,                      # Show grid (enabled by default)
        xlabel='X value [radians]',     # X label
        ylabel='f(x) [AU]'              # Y label
)

# Add another curve to the plot, on the right axis
y2 = np.cos(x) *10
p.add(x, y2, 'r-', title='cos(x)', right=True)
p.set_y2range(-25, 15)

# Adjust x and y range
p.set_xrange(-11, 11)
p.set_yrange(-0.3, 1.1)

# Save figure to a file
p.save_png(filepath='functions.png')

