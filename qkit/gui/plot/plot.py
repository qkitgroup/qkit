from subprocess import Popen, PIPE
from qkit.storage import hdf_lib
import os
import matplotlib.pyplot as plt
plt.ioff()
import numpy as np
import logging
logging.basicConfig(level=logging.INFO)

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

    ds = ""
    for s in datasets: ds+=s+","
    ds = ds.strip(",")

    cmd = "python"
    cmd += " -m qkit.gui.qviewkit.main" #load qviewkit/main.py as module, so we do not need to know it's folder
    options =  " -f " + h5_filepath.encode("string-escape") #raw string encoding
    if ds:
        options += " -ds "+ str(ds)
    options += " -rt "+ str(refresh)
    if live:
        options += " -live "

    if echo:
        print "Qviewkit open cmd: "+ cmd + options
        print Popen(cmd+options, shell=True, stdout=PIPE).stdout.read()
    else:
        Popen(cmd+options, shell=True)


# this is for saving plots
def save_plots(h5_filepath, datasets=[], comment='', save_pdf=False):
    """
    Save plots is a helper function to extract and save image plots from hdf-files

    """
    h5p = h5plot(h5_filepath, datasets=[], comment=comment,  save_pdf=False)


class h5plot(object):

    def __init__(self,h5_filepath, datasets=[], comment='', save_pdf=False):

        self.comment = comment
        self.save_pdf = save_pdf

        filepath = os.path.abspath(h5_filepath)   #put filepath to platform standards
        self.filedir  = os.path.dirname(filepath)   #return directory component of the given pathname, here filepath

        self.image_dir = os.path.join(self.filedir,'images')
        try:
            os.mkdir(self.image_dir)
        except OSError:
            logging.warning('Error creating image directory.')
            pass

        # open the h5 file and get the hdf_lib object
        self.hf = hdf_lib.Data(path=h5_filepath)

        # check for datasets
        if datasets:
            logging.info(" -> plotting given datasets:" +str(datasets))
            for i,key in enumerate(datasets):

                split_key=key.split('/')
                if len(split_key) == 1:
                    key = "/entry/data0/"+split_key[0]
                    self.plt_ds(key)
                if len(split_key) == 2:
                    key = "/entry/"+split_key[0]+"/"+split_key[1]
                    if split_key[0] == 'views':
                        self.plt_views(key)
                    else:
                        self.plt_ds(key)
        else:
            for i, pentry in enumerate(self.hf['/entry'].keys()):
                key='/entry/'+pentry
                for j, centry in enumerate(self.hf[key].keys()):
                    key='/entry/'+pentry+"/"+centry
                    if pentry == 'views':
                        self.plt_views(key)
                    else:
                        self.plt_ds(key)

        #close hf file
        self.hf.close()
        print 'Plots saved in', self.image_dir

    def plt_ds(self,dataset):
            logging.info(" -> plotting dataset: "+str(dataset))

            ds=self.hf[dataset]
            x_ds_url = ds.attrs.get('x_ds_url','')
            y_ds_url = ds.attrs.get('y_ds_url','')

            ds_label = ds.attrs.get('name','_name_')+' / '+ds.attrs.get('unit','_unit_')

            if x_ds_url:
                logging.info("x_ds_url exists.")
                x_ds = self.hf[x_ds_url]
                x_label = x_ds.attrs.get('name','_xname_')+' / '+x_ds.attrs.get('unit','_xunit_')

            else:
                #x_ds = self.hf[x_ds_url]
                #data_x = np.array(x_ds)

                x_label = ds.attrs.get('name','_xname_')+' / ' + ds.attrs.get('unit','_xunit_')
                x_ds = self.hf['/entry/data0/'+ds.attrs.get('x_name')]
            
            # Hack to detect (and not plot) coordinate-datasets
            if x_ds == ds:
                return
            
            fig, ax = plt.subplots(figsize=(20,10))

            if len(ds.shape)==1:
            #checking the shape is a little hack to save plots from earlier .h5 files without proper metadata settings
                """
                dataset is only one-dimensional
                print data vs. x-coordinate
                """
                logging.info("ds is one dimensional.")

                data_y = ds

                y_label = ds_label
                ax.plot(x_ds,data_y[0:len(x_ds)], '-')   #JB: avoid crash after pressing the stop button when arrays are of different lengths

            elif len(ds.shape)>=2:
                """
                dataset is two-dimensional
                print data color-coded y-coordinate vs. x-coordinate
                """
                logging.info("ds is two dimensional.")
                if not y_ds_url:
                    y_ds = self.hf['/entry/data0/'+ds.attrs.get('y_name')] #hack for 'older' datasets that do not yet have y_ds_url entries
                else:
                    y_ds = self.hf[y_ds_url]
                data_y = np.array(y_ds)
                if len(ds.shape)==3:
                    data_y = data_y[:,:,data_y.shape[2]/2]
                y_label = y_ds.attrs.get('name','_yname_')+' / '+y_ds.attrs.get('unit','_yunit_')

                data_z = np.array(ds)

                xmin = x_ds.attrs.get('x0',0)
                xmax = xmin+x_ds.attrs.get('dx',1)*x_ds.shape[0]
                ymin = y_ds.attrs.get('x0',0)
                ymax = ymin+y_ds.attrs.get('dx',1)*y_ds.shape[0]

                cax = ax.imshow(data_z.T, aspect='auto', extent=[xmin,xmax,ymin,ymax], origin = 'lower')
                cbar = fig.colorbar(cax)
                cbar.ax.set_ylabel(ds_label)
                cbar.ax.yaxis.label.set_fontsize(20)
                for i in cbar.ax.get_yticklabels():
                    i.set_fontsize(16)
            else:
                pass
            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.xaxis.label.set_fontsize(20)
            ax.yaxis.label.set_fontsize(20)
            ax.ticklabel_format(useOffset=False)
            for i in ax.get_xticklabels():
                i.set_fontsize(16)
            for i in ax.get_yticklabels():
                i.set_fontsize(16)
            fig.tight_layout()

            save_name = str(os.path.basename(self.filedir))[0:6] + '_' + dataset.replace('/entry/','').replace('/','_')
            if self.comment:
                save_name = save_name+'_'+self.comment
            image_path = str(os.path.join(self.image_dir,save_name))
            #print 'image path', image_path
            #
            if self.save_pdf:
                fig.savefig(image_path+'.pdf')
            fig.savefig(image_path+'.png')

            plt.close()

    def plt_views(self,key):
            # not (yet?) implemented. we'll see ...
            pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
    description="plot.py hdf and matplotlib-based plotting of datasets / KIT 2015")

    parser.add_argument('-f','--file',required=True,type=str, help='hdf/h5 filename to open')
    parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    parser.add_argument('-c', '--comment', type=str, help='(optional) comment to append at filenames')
    parser.add_argument('-pdf','--save-pdf', default=False,action='store_true', help='(optional) save default plots')

    args=parser.parse_args()
    # split the dataset string into a list
    datasets=[]
    if args.datasets:
        dss=args.datasets.split(',')
        for ds in dss: datasets.append(ds)
    # get the full path
    filepath= os.path.abspath(args.file)
    save_plots(filepath, datasets=datasets,comment=args.comment,save_pdf=args.save_pdf)
