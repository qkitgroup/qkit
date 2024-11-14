#-*- coding: utf-8 -*-
from subprocess import Popen, PIPE
import os
import numpy as np
import logging
import json

from numpy.core.multiarray import ndarray

logging.basicConfig(level=logging.INFO)

import qkit
from qkit.storage import store
from qkit.storage.hdf_constants import ds_types
from qkit.core.lib.misc import str3,concat
import sys

try:
    if qkit.module_available("matplotlib"):
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        plot_enable = True
except AttributeError:
    try:
        import matplotlib.pyplot as plt
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
        plot_enable = True
    except ImportError:
        plot_enable = False

# this is for live-plots
def plot(h5_filepath, datasets=[], refresh = 2, live = True, echo = False):
    """
    Opens a .h5-file with qviewkit in a python subprocess.
    
    This is the outermost function to open a h5 file with qviewkit.
    To be independent from other processes i.e. running measurement the viewer
    is opend in a python subprocess. The function opens a shell and executes
    the qviewkit main routine with the given arguments.

    Args:
        h5_filepath: String, absolute filepath.
        datasets: Optional arrays of dataset urls to be opened at start of 
            qviewkit, default: []
        refresh: Optional integer refreshing time in seconds for live view, 
            default: 2
        live: Boolean, optional for constant checks for updates. 
            default: True
        echo: Boolean, optional. Echo settings for debugging, default: False
    Return:
        Popen call with the correct commend that opens a shell and executes
        the main qviewkit routine with a given filename. If given, some
        datasets open automaticall.
    """
    # the plot engine for live plots is set in the environement
    plot_viewer = qkit.cfg.get('plot_engine', None)
    
    # the final return call should look sth. like this:
    # python -m qkit.gui.qviewkit.main -f [h5_filepath] -ds amplitude,phase -rt 2 -live
    
    cmd = [sys.executable]
    cmd.append('-m')
    cmd.append(plot_viewer)
    
    cmd.append('-f')
    cmd.append(h5_filepath)
    
    if datasets:
        cmd.append('-ds')
        ds = ""
        for s in datasets:
            ds += s+','
        cmd.append(ds[:-1])
    cmd.append('-rt')
    cmd.append(str(refresh))
    if live:
        cmd.append('-live')
    
    if echo:
        print("Qviewkit open cmd: "+ str(cmd))
        os.putenv("HDF5_USE_FILE_LOCKING",'FALSE')
        P = Popen(cmd, shell=False, stdout=PIPE)
        print(P.stdout.read())
        return P
    else:
        os.putenv("HDF5_USE_FILE_LOCKING", 'FALSE')
        return Popen(cmd, shell=False, stdout=PIPE, text=True)


# this is for saving plots
def save_plots(h5_filepath, comment='', save_pdf=False):
    """
    Saves plots of all datasets with default settings.
    
    Args:
        h5_filepath: String, absolute filepath.
        comment: Optional comment for the plots to be added to the filenames.
            default : ''
        save_pdf: Optional boolean setting for the output file type.
            default: False
    """
    h5plot(h5_filepath, comment=comment, save_pdf=save_pdf)


class h5plot(object):
    """
    h5plot class plots and saves all dataset in the h5 file.

    We recursively walk through the entry tree of datasets, check for their
    ds_type and plot the data in a default setting with matplotlib. The plots 
    are then saved in an 'image' folder beside the h5 file. 
    """
    y_data = None  # type: ndarray

    def __init__(self,h5_filepath, comment='', save_pdf=False):
        """Inits h5plot with a h5_filepath (string, absolute path), optional 
        comment string, and optional save_pdf boolean.
        """
        if not plot_enable or not qkit.module_available("matplotlib"):
            logging.warning("matplotlib not installed. I can not save your measurement files as png. I will disable this function.")
            qkit.cfg['save_png'] = False
        if not qkit.cfg.get('save_png',True):
            return
        self.comment = comment
        self.save_pdf = save_pdf
        self.path = h5_filepath

        filepath = os.path.abspath(self.path)   #put filepath to platform standards
        self.filedir  = os.path.dirname(filepath)   #return directory component of the given pathname, here filepath

        self.image_dir = os.path.join(self.filedir,'images')
        try:
            os.mkdir(self.image_dir)
        except OSError:
            logging.warning('Error creating image directory.')
            pass

        # open the h5 file and get the hdf_lib object
        self.hf = store.Data(self.path)

        # check for datasets
        for i, pentry in enumerate(self.hf['/entry'].keys()):
            key='/entry/'+pentry
            for j, centry in enumerate(self.hf[key].keys()):
                try:
                    self.key='/entry/'+pentry+"/"+centry
                    self.ds = self.hf[self.key]
                    if self.ds.attrs.get('save_plot', True):
                        self.plt() # this is the plot function
                except Exception as e:
                    print("Exception in qkit/gui/plot/plot.py while plotting")
                    print(self.key)
                    print(e)
        #close hf file
        self.hf.close()
        print('Plots saved in ' + self.image_dir)

    def plt(self):
        """
        Creates the matplotlib figure, checks for some metadata and calls
        the plotting with respect to the ds_type of the dataset.
        
        Args:
            self: Object of the h5plot class.
        Returns:
            No return variable. The function operates on the given object.
        """
        logging.info(" -> plotting dataset: "+str(self.ds.attrs.get('name')))

        self.ds_type = self.ds.attrs.get('ds_type', '')
        self.x_ds_url = self.ds.attrs.get('x_ds_url','')
        self.y_ds_url = self.ds.attrs.get('y_ds_url','')
        self.z_ds_url = self.ds.attrs.get('z_ds_url','')

        self.fig = Figure(figsize=(20,10),tight_layout=True)
        self.ax = self.fig.gca()
        self.canvas = FigureCanvas(self.fig)

        self._unit_prefixes = {24: 'Y', 21: 'Z', 18: 'E', 15: 'P', 12: 'T', 9: 'G', 6: 'M', 3: 'k', 0: '', -3: 'm', -6: u'µ', -9: 'n', -12: 'p', -15: 'f', -18: 'a', -21: 'z', -24: 'y'}
        self.plot_styles = {0:'-', 1:'.-', 2:'.'}

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
            self.plt_view()
        else:
            return

        ## Some labeling depending on the ds_type. The label variables are set
        ## in the respective plt_xxx() fcts.
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
        Plot one-dimensional dataset. Print data vs. x-coordinate.
        
        Args:
            self: Object of the h5plot class.
        Returns:
            No return variable. The function operates on the self- matplotlib 
            objects.
        """
        self.ax.set_title(self.hf._filename[:-3]+" "+str3(self.ds.attrs.get('name','_name_')))
        self.y_data = np.array(self.ds)
        self.y_exp = self._get_exp(self.y_data)
        self.y_label = concat(self.ds.attrs.get('name','_name_'),' (',self._unit_prefixes[self.y_exp],self.ds.attrs.get('unit','_unit_'),')')
        try:
            self.x_data = self.hf[self.x_ds_url]
            self.x_exp = self._get_exp(np.array(self.x_data))
            self.x_label = concat(self.x_data.attrs.get('name','_xname_'),' (', self._unit_prefixes[self.x_exp],self.x_data.attrs.get('unit','_xunit_'),')')
        except Exception:
            self.x_data = np.arange(len(self.y_data))
            self.x_label = '_none_ / _none_'
        plot_style = self.plot_styles[int(not (len(self.y_data) - 1)) * 2] # default is 'x' for one point and '-' for lines
        #if len(self.y_data) == 1: #only one entry, print as cross
        #    plot_style = 'x'
        #else:
        #    plot_style = '-'
        try:
            self.ax.plot(np.array(self.x_data)*10**int(-self.x_exp), self.y_data[0:len(self.x_data)]*10**int(-self.y_exp), plot_style)   #JB: avoid crash after pressing the stop button when arrays are of different lengths
        except TypeError:
            self.ax.plot(0,self.y_data, plot_style)

    def plt_matrix(self):
        """
        Plot two-dimensional dataset. print data color-coded y-coordinate
        vs. x-coordinate.
        
        Args:
            self: Object of the h5plot class.
        Returns:
            No return variable. The function operates on the self- matplotlib 
            objects.
        """
        self.x_ds = self.hf[self.x_ds_url]
        self.x_exp = self._get_exp(np.array(self.x_ds))
        self.x_label = concat(self.x_ds.attrs.get('name', '_xname_'),' (',self._unit_prefixes[self.x_exp],self.x_ds.attrs.get('unit','_xunit_'),')')
        self.y_ds = self.hf[self.y_ds_url]
        self.y_exp = self._get_exp(np.array(self.y_ds))
        self.y_label = concat(self.y_ds.attrs.get('name', '_yname_'),' (', self._unit_prefixes[self.y_exp] ,self.y_ds.attrs.get('unit','_yunit_'),')')
        self.ds_data = np.array(self.ds).T #transpose matrix to get x/y axis correct
        self.ds_exp = self._get_exp(self.ds_data)
        self.ds_data *= 10.**-self.ds_exp
        self.ds_label = concat(self.ds.attrs.get('name', '_name_'),' (',self._unit_prefixes[self.ds_exp],self.ds.attrs.get('unit', '_unit_'),')')

        x_data = np.array(self.x_ds)*10.**-self.x_exp
        x_min, x_max = np.amin(x_data), np.amax(x_data)
        dx = self.x_ds.attrs.get('dx', (x_data[-1]-x_data[0])/(len(x_data)-1))
        y_data = np.array(self.y_ds)*10.**-self.y_exp
        y_min, y_max = np.amin(y_data), np.amax(y_data)
        dy = self.y_ds.attrs.get('dy', (y_data[-1]-y_data[0])/(len(y_data)-1))

        # downsweeps in any direction have to be corrected
        # this is triggered by dx/dy values < 0
        # data-matrix and min/max-values have to be swapped
        if dx < 0:
            self.ds_data = np.fliplr(self.ds_data)
        if dy < 0:
            self.ds_data = np.flipud(self.ds_data)

        # plot
        self.ax.set_title(self.hf._filename[:-3]+" "+str3(self.ds.attrs.get('name','_name_')))
        self.cax = self.ax.imshow(self.ds_data,
                                  extent=(x_min, x_max, y_min, y_max),
                                  aspect='auto',
                                  origin='lower',
                                  vmin=self._get_vrange(self.ds_data, 2)[0], vmax=self._get_vrange(self.ds_data, 2)[1],
                                  interpolation='none')
        #self.cax = self.ax.pcolormesh(x_data, y_data, self.ds_data)
        self.cax.set_rasterized(True)
        self.cbar = self.fig.colorbar(self.cax)
        self.cbar.ax.set_ylabel(self.ds_label)
        self.cbar.ax.yaxis.label.set_fontsize(20)
        for i in self.cbar.ax.get_yticklabels():
            i.set_fontsize(16)

    def plt_box(self):
        """
        Plot two-dimensional dataset. Print data color-coded y-coordinate
        vs. x-coordinate.

        Args:
            self: Object of the h5plot class.
        Returns:
            No return variable. The function operates on the self- matplotlib
            objects.
        """
        self.x_ds = self.hf[self.x_ds_url]
        self.x_exp = self._get_exp(np.array(self.x_ds))
        self.x_label = concat(self.x_ds.attrs.get('name', '_xname_'),' (',self._unit_prefixes[self.x_exp],self.x_ds.attrs.get('unit','_xunit_'),')')
        self.y_ds = self.hf[self.y_ds_url]
        self.y_exp = self._get_exp(np.array(self.y_ds))
        self.y_label = concat(self.y_ds.attrs.get('name', '_yname_'),' (',self._unit_prefixes[self.y_exp],self.y_ds.attrs.get('unit', '_yunit_'),')')
        self.z_ds = self.hf[self.z_ds_url]
        self.z_exp = self._get_exp(np.array(self.z_ds))
        self.z_label = concat(self.z_ds.attrs.get('name', '_zname_'),' (',self._unit_prefixes[self.z_exp],self.z_ds.attrs.get('unit','_zunit_'), ')')
        self.ds_data = np.array(self.ds)[:, :, self.ds.shape[2] // 2].T  # transpose matrix to get x/y axis correct
        self.ds_exp = self._get_exp(self.ds_data)
        self.ds_data *= 10.**-self.ds_exp
        self.ds_label = concat(self.ds.attrs.get('name', '_name_'),' (',self._unit_prefixes[self.ds_exp],self.ds.attrs.get('unit','_unit_'),')')

        x_data = np.array(self.x_ds)*10.**-self.x_exp
        x_min, x_max = np.amin(x_data), np.amax(x_data)
        dx = self.x_ds.attrs.get('dx', (x_data[-1]-x_data[0])/(len(x_data)-1))
        y_data = np.array(self.y_ds)*10.**-self.y_exp
        y_min, y_max = np.amin(y_data), np.amax(y_data)
        dy = self.y_ds.attrs.get('dy', (y_data[-1]-y_data[0])/(len(y_data)-1))

        # downsweeps in any direction have to be corrected
        # this is triggered by dx/dy values < 0
        # data-matrix and min/max-values have to be swapped
        if dx < 0:
            self.ds_data = np.fliplr(self.ds_data)
        if dy < 0:
            self.ds_data = np.flipud(self.ds_data)

        # plot
        self.ax.set_title(concat(self.hf._filename[:-3]," ",self.ds.attrs.get('name','_name_')))
        self.cax = self.ax.imshow(self.ds_data,
                                  extent=(x_min, x_max, y_min, y_max),
                                  aspect='auto',
                                  origin='lower',
                                  vmin=self._get_vrange(self.ds_data, 2)[0], vmax=self._get_vrange(self.ds_data, 2)[1],
                                  interpolation='none')
        #self.cax = self.ax.pcolormesh(x_data, y_data, self.ds_data)
        self.cax.set_rasterized(True)
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
        """
        Plot views with possible multi-level overlays.
        
        First shot at (automatically) plotting views.
        Since this structure is rather flexible, there is no universal approach
        for meaningful plots. First demand was IV curves from the transport 
        measurements.
        The code is a recycled version of the _display_1D_view() fct of 
        qkit.gui.qviewkit.PlotWindow_lib
        
        Args:
            self: Object of the h5plot class.
        Returns:
            No return variable. The function operates on the self- matplotlib 
            objects.
        """
        # views are organized in overlays, the number of x vs y plot in one figure (i.e. data and fit)
        overlay_num = self.ds.attrs.get("overlays",0)
        overlay_urls = []
        err_urls = []
        self.ax.set_title(self.hf._filename[:-3]+" "+str3(self.ds.attrs.get('name','_name_')))
        
        # the overlay_urls (urls of the x and y datasets that ar plotted) are extracted from the metadata
        for i in range(overlay_num+1):
            ov = str3(self.ds.attrs.get("xy_"+str(i),""))
            if ov:
                overlay_urls.append(ov.split(":"))
            err_urls.append(self.ds.attrs.get("xy_"+str(i)+"_error",""))
                
        self.ds_xs = []
        self.ds_ys = []
        self.ds_errs = []
        for xy in overlay_urls:
            self.ds_xs.append(self.hf[xy[0]])
            self.ds_ys.append(self.hf[xy[1]])
            
        for err_url in err_urls:
            try:
                self.ds_errs.append(self.hf[err_url])
            except:
                self.ds_errs.append(0)
        
        """
        the ds_type are detected. this determines which dataset is displayed as a 1D plot.
        since the initial demand for the plotting comes from IV measurements and for easy handling,
        the default display in qviewkit is saved.
        """
        self.ds_label = str3(self.ds.attrs.get('name','_name_'))
        view_params = json.loads(str3(self.ds.attrs.get("view_params", {})))
        #if 'aspect' in view_params:
        #    self.ax.set_aspect = view_params.get('aspect', 'auto')
        markersize = view_params.get('markersize', 5)
        # iteratring over all x- (and y-)datasets and checking for dimensions gives the data to be plotted
        for i, x_ds in enumerate(self.ds_xs):
            y_ds = self.ds_ys[i]
            err_ds = self.ds_errs[i]
            
            #1D data is easy, for matrix and box the very last recorded 1D data is plotted
            if x_ds.attrs.get('ds_type',0) == ds_types['coordinate'] or x_ds.attrs.get('ds_type',0) == ds_types['vector']:
                if y_ds.attrs.get('ds_type',0) == ds_types['vector'] or y_ds.attrs.get('ds_type',0) == ds_types['coordinate']:
                    x_data = np.array(x_ds)
                    y_data = np.array(y_ds)
                    if err_ds:
                        err_data = np.array(err_ds)
    
                elif y_ds.attrs.get('ds_type',0) == ds_types['matrix']:
                    x_data = np.array(x_ds)
                    if "default_trace" in  view_params:
                        y_data = np.array(y_ds[:,view_params.get("default_trace",-1)])
                    else:
                        y_data = np.array(y_ds[-1]) # The code was like this, but I believe the axis is wrong
                    if err_ds:
                        err_data = np.array(err_ds[-1])
    
                elif y_ds.attrs.get('ds_type',0) == ds_types['box']:
                    x_data = np.array(x_ds)
                    y_data = np.array(y_ds[-1,-1,:])
                    if err_ds:
                        err_data = np.array(err_ds[-1,-1,:])
    
            ## This is in our case used so far only for IQ plots. The functionality derives from this application.
            elif x_ds.attrs.get('ds_type',0) == ds_types['matrix']:
                x_data = np.array(x_ds[-1])
                y_data = np.array(y_ds[-1])
            
            elif x_ds.attrs.get('ds_type',0) == ds_types['box']:
                x_data = np.array(x_ds[-1,-1,:])
                y_data = np.array(y_ds[-1,-1,:])

            plot_style = self.plot_styles[view_params.get('plot_style', int(not (len(y_data) - 1)) * 2)] # default is 'x' for one point and '-' for lines
            if err_ds:
                self.ax.errorbar(x_data, y_data[0:len(x_data)], yerr=err_data[0:len(x_data)], label=y_ds.name.split('/')[-1])
            else:
                try:
                    x_exp = self._get_exp(x_data) # caculate order of magnitude for unit-prefix
                    y_exp = self._get_exp(y_data[0:len(x_data)])
                    self.ax.plot(x_data*10**-x_exp, y_data[0:len(x_data)]*10**-y_exp, plot_style, label=y_ds.name.split('/')[-1])
                except TypeError:
                    self.ax.plot(0,y_data, plot_style)

            # x- and y-labels come from view_params['labels'] or if not provided from the last added entry in the overlay
            if view_params.get("labels", False):
                self.x_label = view_params['labels'][0]
                self.y_label = view_params['labels'][1]
            else:
                self.x_label = str3(x_ds.attrs.get("name", "_none_"))
                self.y_label = str3(y_ds.attrs.get("name", "_none_"))
            self.x_unit = str3(x_ds.attrs.get("unit","_none_"))
            self.y_unit = str3(y_ds.attrs.get("unit","_none_"))
            self.x_label += ' (' + self._unit_prefixes[x_exp] + self.x_unit + ')'
            self.y_label += ' (' + self._unit_prefixes[y_exp] + self.y_unit + ')'
        self.ax.legend()

    def _get_exp(self, data):
        """
        This function calculates the order of magnitude (exponent in steps of 3) to use for unit-prefix.
        """
        try:
            return np.nanmax(np.log10(np.abs(data[data != 0]))) // 3 * 3
        except:
            return 0

    def _get_vrange(self, data, percent):
        '''
        This function calculates ranges for the colorbar to get rid of spikes in the data.
        If the data is evenly distributed, this should not change anything in your colorbar.
        '''
        _min = np.nanpercentile(data,percent)
        _max = np.nanpercentile(data,100-percent)
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
