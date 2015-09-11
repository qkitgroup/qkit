from subprocess import Popen, PIPE
from qkit.storage import hdf_lib
import os
from pylab import *
import numpy as np

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

def save_plots(h5_filepath, datasets=[], save_pdf=False):
    def plt_ds(key):
        ds=hf[key]
        x_ds_url = ds.attrs.get('x_ds_url','')
        y_ds_url = ds.attrs.get('y_ds_url','')

        if not x_ds_url:
            #attempt to not print out coordinates. we have to chage the _setup_metadata() anyway. maybe it works
            return

        x_ds = hf[x_ds_url]
        data_x = np.array(x_ds)

        ds_label = ds.attrs.get('name','_name_')+' / '+ds.attrs.get('unit','_unit_')
        x_label = x_ds.attrs.get('name','_xname_')+' / '+x_ds.attrs.get('unit','_xunit_')

        fig, ax = subplots()

        if not y_ds_url and len(np.array(ds).shape)==1: #checking the shape is a little hack to save plots from earlier .h5 files without propper metadata settings
            """
            dataset is only one-dimensional
            print data vs. x-coordinate
            """
            y_ds = ds
            data_y = np.array(y_ds)
            y_label = ds_label

            ax.plot(data_x,data_y, '-')
        else:
            """
            dataset is two-dimensional
            print data color-coded y-coordinate vs. x-coordinate
            """
            if not y_ds_url:
                y_ds = hf['/entry/data0/'+ds.attrs.get('y_name')] #hack for 'older' datasets that do not yet have y_ds_url entries

            else:
                y_ds = hf[y_ds_url]
            data_y = np.array(y_ds)
            y_label = y_ds.attrs.get('name','_yname_')+' / '+y_ds.attrs.get('unit','_yunit_')

            data_z = np.array(ds)

            xmin = x_ds.attrs.get('x0',0)
            xmax = xmin+x_ds.attrs.get('dx',1)*data_x.shape[0]
            ymin = y_ds.attrs.get('x0',0)
            ymax = ymin+y_ds.attrs.get('dx',1)*data_y.shape[0]

            cax = ax.imshow(data_z.T, aspect='auto', extent=[xmin,xmax,ymin,ymax])
            cbar = fig.colorbar(cax)
            cbar.ax.set_ylabel(ds_label)
            cbar.ax.yaxis.label.set_fontsize(20)
            for i in cbar.ax.get_yticklabels():
                i.set_fontsize(16)

        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.xaxis.label.set_fontsize(20)
        ax.yaxis.label.set_fontsize(20)
        ax.ticklabel_format(useOffset=False)
        for i in ax.get_xticklabels():
            i.set_fontsize(16)
        for i in ax.get_yticklabels():
            i.set_fontsize(16)
        tight_layout()

        save_name=(key.replace('/entry/','')).replace('/','_')
        if save_pdf:
            savefig(save_name+'.pdf')
        else:
            savefig(save_name+'.png')

    def plt_views(key):
        # not (yet?) implemented. we'll see ...
        pass

    cwd=os.getcwd()

    hf = hdf_lib.Data(path=h5_filepath)

    save_dir = hf.get_folder()+r'\images'
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    os.chdir(save_dir)
    if datasets:
        for i,key in enumerate(datasets):
            split_key=key.split('/')
            if len(split_key) == 1:
                key = "/entry/data0/"+split_key[0]
                plt_ds(key)
            if len(split_key) == 2:
                key = "/entry/"+split_key[0]+"/"+split_key[1]
                if pentry == 'views':
                    plt_views(key)
                else:
                    plt_ds(key)

    else:
        for i, pentry in enumerate(hf['/entry'].keys()):
            key='/entry/'+pentry
            for j, centry in enumerate(hf[key].keys()):
                key='/entry/'+pentry+"/"+centry
                if pentry == 'views':
                    plt_views(key)
                else:
                    plt_ds(key)
    hf.close()
    os.chdir(cwd)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
    description="plot.py hdf and matplotlib-based plotting frontend / KIT 2015")

    parser.add_argument('-f','--file',     type=str, help='hdf filename to open')
    parser.add_argument('-ds','--datasets', type=str, help='(optional) datasets opened by default')
    parser.add_argument('-pdf','--save-pdf', default=False,action='store_true', help='(optional) save default plots')

    args=parser.parse_args()
    filepath= os.path.abspath(args.file)
    ds=args.datasets.split(',')
    datasets=[]
    for i,entry in enumerate(ds):
        datasets.append(entry)
    save_plots(filepath, datasets=datasets,save_pdf=args.save_pdf)