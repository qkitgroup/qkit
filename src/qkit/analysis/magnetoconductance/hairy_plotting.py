import matplotlib.pyplot as plt
import numpy as np
import sys

# plt.style.use('./plt_styles/default.mplstyle')


class HarryPlotter:
    ''' Plot the results from JumpDetective. Don't think about sweeps anymore,
        but the extracted data after jump detection '''
    def __init__(self, **kwargs):
        # Check here for all keywords which are not supposed to be given to the
        # plot function!
        if 'style' in kwargs.keys():
            self.load_stylesheet(kwargs['style'])
            kwargs.pop('style')
        # All other keywords will be saved and used by the plot fun
        self.settings = kwargs
    def add_plot(self, **kwargs):
        ''' overwrite by children '''
        pass

    def load_stylesheet(self, path):
        plt.style.use(path)

    def save(self, path, dpi=100):
        plt.savefig(path, dpi=dpi)

    def show(self):
        plt.show()
    
    def add_legend(self):
        self.ax.legend()


class ScatterPlotter(HarryPlotter):
    ''' Scatterplots '''
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fig, self.ax = plt.subplots()

    def add_plot(self, x, y, **kwargs):
        settings = self.settings.copy()
        settings.update(kwargs)
        print(settings)
        self.ax.scatter(x, y, **settings)


class HistogramPlotter(HarryPlotter):
    ''' Plot Histrograms '''
    def __init__(self, sweep_values, resolution=None, bins=None,  **kwargs):
        super().__init__(**kwargs)
        self.resolution = resolution
        self.bins = bins
        self.fig, self.ax = plt.subplots()
        self.sweep_values = sweep_values
        self.x = None

    def _get_bin_edges(self):
        ''' Return number of bins. If resoltion is specified, calculate bins from
            limits and resolution. Otherwise, use the bins. '''
            # I DONT KNOW EXACTLY WHY; BUT I HAD TO REMOVE THE FIRST AND THE LAST
            # BAR TO NOT HAVE ARTIFACTS AT THE ENDPOINTS. IT SEEMS THAT OTHERWISE I
            # COUNT VALUES DOUBLE FOR THESE BARS.
        # Find the range of the data
        min = np.nanmin(self.x)
        max = np.nanmax(self.x)
        if self.resolution:
            if self.resolution == 'max':
                # If resolution = 'max' create one bin for each sweep value
                # which is between min and max
                bins = [val for val in self.sweep_values if min <= val <=max]
            elif isinstance(self.resolution, (int, float)):
                return int((max - min) / self.resolution)
        elif self.bins:
            if isinstance(self.bins, int):
                return np.linspace(min, max, num=self.bins)
            elif isinstance(self.bins, list):
                return self.bins
        else:
            print('Need either resolution or bins keyword')
            sys.exit()
        # To get the bin_edges we need add a bin and shift everything
        # by half a bin to the side (otherwise, there will be double
        # counting at the edges
        diff = np.mean(np.diff(bins))
        edges = np.append(bins, bins[-1] + diff) - diff / 2
        return edges


    def add_plot(self, x, **kwargs):
        settings = self.settings.copy()
        settings.update(kwargs)
        # save 1D data to plot as histogram, but remove NaN values
        self.x = x
        # get the bin edges for resolution=max and number of bins otherwise
        edges = self._get_bin_edges()
        # create histogram data: counts for all values betw. edges 
        counts, edges = np.histogram(x, bins=edges)
        # find bins (middle of the range over which histogram counted)
        bins = edges[:-1] + np.mean(np.diff(edges)) / 2
        self.ax.bar(bins, counts, width=np.diff(edges), **settings)
