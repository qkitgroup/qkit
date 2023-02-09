import matplotlib.pyplot as plt
import gc


class SemiFigure():
    """Standard class for plots of semiconducting people.
    """
    def __init__(self, jumbo_data = False): 
        self.fig = plt.figure()
        self.ax = self.fig.subplots()
        self.set_dpi = 400
        self.set_bbox_inches = "tight"
        self.save_as = ".png"
        self.ax.set_axisbelow(True) # pushes grid to background
        self.fig.set_facecolor("White")
        self.ax.title.set_size(fontsize=14)
        self.ax.xaxis.label.set_size(fontsize=12)
        self.ax.yaxis.label.set_size(fontsize=12)
        self.jumbo_data = jumbo_data
        
        
    @property
    def jumbo_data(self):
        return self._jumbo_data
    
    @jumbo_data.setter
    def jumbo_data(self, yesno:bool):
        if yesno:
            plt.rcParams['agg.path.chunksize'] = 10000 # makes saving too big data sets possible.
        else:
            plt.rcParams['agg.path.chunksize'] = 0
        self._jumbo_data = yesno
    

    def close_delete(self):
        """Closes fig and deletes instance to free RAM.
        """
        self.fig.clear()
        plt.close(self.fig)
        del self
        gc.collect()
        

        
if __name__ == "__main__":
    print(plt.rcParams['agg.path.chunksize'])
    sf = SemiFigure(True)
    print(plt.rcParams['agg.path.chunksize'])
    sf.jumbo_data = False
    print(sf.jumbo_data)
    print(plt.rcParams['agg.path.chunksize'])
    sf.jumbo_data = True
    print(plt.rcParams['agg.path.chunksize'])
    print(sf.jumbo_data)