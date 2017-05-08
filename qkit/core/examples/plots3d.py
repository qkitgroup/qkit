import numpy as np

x = np.linspace(-2 * np.pi, 2 * np.pi, 200)
y = np.linspace(-2 * np.pi, 2 * np.pi, 200)
X, Y = meshgrid(x, y)
Z = np.sinc(np.sqrt(X**2 + Y**2))

# Plot in 3D
plot3(ravel(X), ravel(Y), ravel(Z),
        style='3d',
        palette='jet',
        gamma=1.25,
        title='Example 3D plot',
        name='example_3d',
        xrange=(-2 * np.pi, 2 * np.pi),
        yrange=(-2 * np.pi, 2 * np.pi),
        clear=True)

# Plot as image (only for complete NxM data sets!)
p = plot3(ravel(X), ravel(Y), ravel(Z),
        style='image',
        palette='hot',
        title='Example image',
        name='example_img',
        xrange=(-2 * np.pi, 2 * np.pi),
        yrange=(-2 * np.pi, 2 * np.pi),
        clear=True)

x = np.linspace(-np.pi, np.pi, 75)
y = np.linspace(1, 3, 10)
X, Y = meshgrid(x, y)
Z = np.cos(X * Y)

# Plot as points
p = plot3(ravel(X), ravel(Y), ravel(Z), 'rv',
        style='points',
        name='example_points',
        clear=True)

# Plot as lines
p = plot3(ravel(X), ravel(Y), ravel(Z), 'b',
        style='lines',
        name='example_lines',
        clear=True)

