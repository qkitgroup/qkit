from subprocess import Popen, PIPE
from qkit.storage import hdf_lib
import os
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)
from qkit.config.environment import cfg
from qkit.storage.hdf_constants import ds_types

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

# this is for live-plots
def plot(h5_filepath, datasets=[], refresh = 2, live = True, echo = False):
    """
    opens a .h5-file with qviewkit in a python subprocess to be independent from other processes i.e. measurement.

    input:
    h5_filepath (string)
    datasets (array, optional): dataset urls to be opened at start of qviewkit, default: []
    refresh (int, optional): refreshing time in seconds for live view, default: 2
    live (bool, optional): checks constantly the file for changes, default: True
    echo (bool, optional): echo settings for debugging, default: False
    """
    # the plot engine for live plots is set in the environement
    plot_viewer = cfg['plot_engine']
    ds = ""
    for s in datasets: ds+=s+","
    ds = ds.strip(",")

    cmd = "python"
    cmd += " -m "+ plot_viewer #load qviewkit/main.py as module, so we do not need to know its folder
    options =  " -f " + h5_filepath.encode("string-escape") #raw string encoding
    if ds:
        options += " -ds "+ str(ds)
    options += " -rt "+ str(refresh)
    if live:
        options += " -live "

    if echo:
        print "Qviewkit open cmd: "+ cmd + options
        P = Popen(cmd+options, shell=False, stdout=PIPE)
        print P.stdout.read()
        return P
    else:
        return Popen(cmd+options, shell=False)


# this is for saving plots
def save_plots(h5_filepath, comment='', save_pdf=False):
    """
    Save plots is a helper function to extract and save image plots from hdf-files

    """
    h5plot(h5_filepath, comment=comment, save_pdf=save_pdf)


class h5plot(object):

    def __init__(self,h5_filepath, comment='', save_pdf=False):

        self.comment = comment
        self.save_pdf = save_pdf
        self.path = h5_filepath

        filepath = os.path.abspath(self.path)   #put filepath to platform standards
        self.filedir  = os.path.dirname(filepath)   #return directory component of the given pathname, here filepath

        self.image_dir = os.path.join(self.filedir,'images')
        print self.image_dir
        try:
            os.mkdir(self.image_dir)
        except OSError:
            logging.warning('Error creating image directory.')
            pass

        # open the h5 file and get the hdf_lib object
        self.hf = hdf_lib.Data(path=self.path)

        # check for datasets
        for i, pentry in enumerate(self.hf['/entry'].keys()):
            key='/entry/'+pentry
            for j, centry in enumerate(self.hf[key].keys()):
                self.key='/entry/'+pentry+"/"+centry
                self.ds = self.hf[self.key]
                if self.ds.attrs.get('save_plot', True):
                    self.plt()

        #close hf file
        self.hf.close()
        print 'Plots saved in', self.image_dir

    def plt(self):
        logging.info(" -> plotting dataset: "+str(self.ds.attrs.get('name')))

        self.ds_type = self.ds.attrs.get('ds_type', '')
        self.x_ds_url = self.ds.attrs.get('x_ds_url','')
        self.y_ds_url = self.ds.attrs.get('y_ds_url','')
        self.z_ds_url = self.ds.attrs.get('z_ds_url','')

        self.fig = Figure(figsize=(20,10),tight_layout=True)
        self.ax = self.fig.gca()
        self.canvas = FigureCanvas(self.fig)

        if self.ds_type == ds_types['coordinate']:
            #self.plt_coord()
            return
        elif self.ds_type == ds_types['vector']:
            self.plt_vector()
        elif self.ds_type == ds_types['matrix']:
            self.plt_matrix()
        elif self.ds_type == ds_types['box']:
            self.plt_box()
        elif self.ds_type == ds_types['txt']:
            #self.plt_txt()
            return
        elif self.ds_type == ds_types['view']:
            #self.plt_view()
            return
        else:
            return

        self.ax.set_xlabel(self.x_label)
        self.ax.set_ylabel(self.y_label)
        self.ax.xaxis.label.set_fontsize(20)
        self.ax.yaxis.label.set_fontsize(20)
        self.ax.ticklabel_format(useOffset=False)
        for i in self.ax.get_xticklabels():
            i.set_fontsize(16)
        for i in self.ax.get_yticklabels():
            i.set_fontsize(16)

        save_name = str(os.path.basename(self.filedir))[0:6] + '_' + self.key.replace('/entry/','').replace('/','_')
        if self.comment:
            save_name = save_name+'_'+self.comment
        image_path = str(os.path.join(self.image_dir,save_name))

        if self.save_pdf:
            self.canvas.print_figure(image_path+'.pdf')
        self.canvas.print_figure(image_path+'.png')

        """
        except Exception as e:
            print "Exception in qkit/gui/plot/plot.py"
            print e
        """

    def plt_vector(self):
        """
        dataset is only one-dimensional
        print data vs. x-coordinate
        """
        self.x_ds = self.hf[self.x_ds_url]

        self.x_label = self.x_ds.attrs.get('name','_xname_')+' / '+self.x_ds.attrs.get('unit','_xunit_')
        self.ds_label = self.ds.attrs.get('name','_name_')+' / '+self.ds.attrs.get('unit','_unit_')
        self.data_y = np.array(self.ds)
        self.y_label = self.ds_label
        if len(self.data_y) == 1: #only one entry, print as cross
            plt_style = 'x'
        else:
            plt_style = '-'
        self.ax.plot(self.x_ds,self.data_y[0:len(self.x_ds)], plt_style)   #JB: avoid crash after pressing the stop button when arrays are of different lengths

    def plt_matrix(self):
        """
        dataset is two-dimensional
        print data color-coded y-coordinate vs. x-coordinate
        """

        self.x_ds = self.hf[self.x_ds_url]
        self.y_ds = self.hf[self.y_ds_url]

        self.x_label = self.x_ds.attrs.get('name','_xname_')+' / '+self.x_ds.attrs.get('unit','_xunit_')
        self.y_label = self.y_ds.attrs.get('name','_yname_')+' / '+self.y_ds.attrs.get('unit','_yunit_')
        self.ds_label = self.ds.attrs.get('name','_name_')+' / '+self.ds.attrs.get('unit','_unit_')

        self.data = np.array(self.ds).T #transpose matrix to get x/y axis correct

        self.xmin = self.x_ds.attrs.get('x0',0)
        self.dx = self.x_ds.attrs.get('dx',1)
        self.xmax = self.xmin+self.dx*self.x_ds.shape[0]
        self.ymin = self.y_ds.attrs.get('x0',0)
        self.dy = self.y_ds.attrs.get('dx',1)
        self.ymax = self.ymin+self.dy*self.y_ds.shape[0]

        # downsweeps in any direction have to be corrected
        # this is triggered by dx/dy values < 0
        # data-matrix and min/max-values have to be swapped
        if self.dx < 0:
            self.data = np.fliplr(self.data)
            self.xmin, self.xmax = self.xmax, self.xmin
        if self.dy < 0:
            self.data = np.flipud(self.data)
            self.ymin, self.ymax = self.ymax, self.ymin

        self.cax = self.ax.imshow(self.data, aspect='auto', extent=[self.xmin,self.xmax,self.ymin,self.ymax], origin = 'lower', vmin = self._get_vrange(self.data,2)[0], vmax = self._get_vrange(self.data,2)[1], interpolation='none', cmap=plt.get_cmap('Greys_r'))
        self.cbar = self.fig.colorbar(self.cax)
        self.cbar.ax.set_ylabel(self.ds_label)
        self.cbar.ax.yaxis.label.set_fontsize(20)
        for i in self.cbar.ax.get_yticklabels():
            i.set_fontsize(16)

    def plt_box(self):
        """
        dataset is two-dimensional
        print data color-coded y-coordinate vs. x-coordinate
        """

        self.x_ds = self.hf[self.x_ds_url]
        self.y_ds = self.hf[self.y_ds_url]
        self.z_ds = self.hf[self.z_ds_url]

        self.x_label = self.x_ds.attrs.get('name','_xname_')+' / '+self.x_ds.attrs.get('unit','_xunit_')
        self.y_label = self.y_ds.attrs.get('name','_yname_')+' / '+self.y_ds.attrs.get('unit','_yunit_')
        self.ds_label = self.ds.attrs.get('name','_name_')+' / '+self.ds.attrs.get('unit','_unit_')

        self.nop = self.ds.shape[2] #S1 this was ->self.z_ds.shape[0]<- before, but causes problems for some data
        self.data = np.array(self.ds)[:,:,self.nop/2].T #transpose matrix to get x/y axis correct

        self.xmin = self.x_ds.attrs.get('x0',0)
        self.dx = self.x_ds.attrs.get('dx',1)
        self.xmax = self.xmin+self.dx*self.x_ds.shape[0]
        self.ymin = self.y_ds.attrs.get('x0',0)
        self.dy = self.y_ds.attrs.get('dx',1)
        self.ymax = self.ymin+self.dy*self.y_ds.shape[0]

        # downsweeps in any direction have to be corrected
        # this is triggered by dx/dy values < 0
        # data-matrix and min/max-values have to be swapped
        if self.dx < 0:
            self.data = np.fliplr(self.data)
            self.xmin, self.xmax = self.xmax, self.xmin
        if self.dy < 0:
            self.data = np.flipud(self.data)
            self.ymin, self.ymax = self.ymax, self.ymin

        self.cax = self.ax.imshow(self.data, aspect='auto', extent=[self.xmin,self.xmax,self.ymin,self.ymax], origin = 'lower', vmin = self._get_vrange(self.data,2)[0], vmax = self._get_vrange(self.data,2)[1], interpolation='none', cmap=plt.get_cmap('Greys_r'))
        self.cbar = self.fig.colorbar(self.cax)
        self.cbar.ax.set_ylabel(self.ds_label)
        self.cbar.ax.yaxis.label.set_fontsize(20)
        for i in self.cbar.ax.get_yticklabels():
            i.set_fontsize(16)

    def plt_coord(self):
        # not (yet?) implemented. we'll see ...
        pass
    def plt_txt(self):
        # not (yet?) implemented. we'll see ...
        pass
    def plt_view(self):
        # not (yet?) implemented. we'll see ...
        pass

    def _get_vrange(self,data,percent):
        '''
        This function calculates ranges for the colorbar to get rid of spikes in the data.
        If the data is evenly distributed, this should not change anything in your colorbar.
        '''
        _min = np.percentile(data,percent)
        _max = np.percentile(data,100-percent)
        _min -= (_max-_min)*percent/(100.-2*percent)
        _max += (_max-_min)*percent/(100.-2*percent)
        return [_min,_max]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
    description="plot.py hdf and matplotlib-based plotting of datasets / KIT 2015")

    parser.add_argument('-f','--file',required=True,type=str, help='hdf/h5 filename to open')
    parser.add_argument('-c', '--comment', type=str, help='(optional) comment to append at filenames')
    parser.add_argument('-pdf','--save-pdf', default=False,action='store_true', help='(optional) save default plots')

    args=parser.parse_args()

    # get the full path
    filepath= os.path.abspath(args.file)
    save_plots(filepath,comment=args.comment,save_pdf=args.save_pdf)
