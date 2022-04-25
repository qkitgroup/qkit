import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import gc


class SemiFigure(Figure):
    """Standard class for plots.
    """
    def __init__(self, *args, jumbo_data = False, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fig = plt.figure()
        self.ax = self.fig.subplots()
        self.set_dpi = 400
        self.set_bbox_inches = "tight"
        self.save_as = ".png"

        self.ax.title.set_size(fontsize=14)
        self.ax.xaxis.label.set_size(fontsize=12)
        self.ax.yaxis.label.set_size(fontsize=12)
        
        if jumbo_data:
            plt.rcParams['agg.path.chunksize'] = 10000 # makes saving too big data sets possible.
            
    def close_delete(self):
        """Closes fig and deletes instance to free RAM.
        """
        self.fig.clear()
        plt.close(self.fig)
        del self
        gc.collect()
        
