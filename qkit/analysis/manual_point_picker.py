# Manual point picker
# by M. Spiecker

import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap


class ManualPointPicker:

    def __init__(self, cmap_data=None, cmap_points=None):

        self.fig = None
        self.ax = None
        self.selection_artist = None

        if cmap_data is None:
            self.cmap_data = mpl.cm.bwr
        else:
            self.cmap_data = cmap_data

        if cmap_points is None:
            # point colors should be distinguishable from data colormap
            self.colors = 10
            self.cmap_points = np.ones((self.colors, 4))

            # fill colors
            self.cmap_points[0, :] = (0.0, 0.0, 0.0, 0.0)  # transparent

            # create a colors that are well visible with bwr
            colors = [(0.0, 0.9, 0.0), # green
                      (0.9, 0.9, 0.0), # yello
                      (0.3, 0.2, 0.1),  # dark brown
                      (0.0, 0.3, 0.2),  # dark green blue
                      (0.0, 0.5, 0.0),  # dark green
                      (0.5, 0.4, 0.2), # brown
                      (0.6, 0.6, 0.6),  # light gray
                      (0.3, 0.3, 0.3),  # gray
                      (0.0, 0.0, 0.0), # black
                      ]

            for i in range(self.colors - 1):
                self.cmap_points[1 + i, :3] = colors[i]

        else:
            self.colors = cmap_points.shape[0]
            self.cmap_points = cmap_points

        self.cmap_points = ListedColormap(self.cmap_points)

        # Data
        self.x_vec = None
        self.y_vec = None
        self.data = None
        self.data_selected = None

    def set_figure(self, fig, ax):

        self.fig = fig
        self.ax = ax

        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

    def start_point_picker(self, x_vec, y_vec, data):

        self.x_vec = x_vec
        self.y_vec = y_vec
        self.data = data
        self.data_selected = np.zeros_like(self.data)

        self.plot()

    def on_key(self, event):
        """
            point with mouse on a data point and press one of the numbers 1-9
            press "0" or "r" to remove data point from the list
        """

        try:
            i = int(np.round(event.ydata))
            j = int(np.round(event.xdata))
        except:
            pass

        if event.key == "r":
            self.data_selected[i, j] = 0.0
        else:
            try:
                self.data_selected[i, j] = int(event.key)
            except:
                pass

        self.refresh_artist()

    def get_data_list(self):

        n, m = self.data_selected.shape

        data = []

        for i in range(n):
            for j in range(m):
                if self.data_selected[i, j] != 0.0:
                    data.append(np.array([self.x_vec[j], self.y_vec[i], self.data_selected[i, j]]))

        return np.asarray(data)

    def refresh_artist(self):

        self.selection_artist.set_data(self.data_selected)
        self.fig.canvas.draw()

    def plot(self):

        self.ax.imshow(self.data, cmap=self.cmap_data, origin='lower', aspect='auto')
        self.selection_artist = self.ax.imshow(self.data_selected, cmap=self.cmap_points, vmin=0.0, vmax=self.colors - 1,
                                               origin='lower', aspect='auto')
        plt.show(block=True)


