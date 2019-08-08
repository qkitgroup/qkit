# -*- coding: utf-8 -*-
"""
@author: andre.schneider@kit.edu / 2019
@license: GPL

This file provides some methods to quickly plot different datasets in a
matplotlib (QT) window. The data file to show can be easily selected in
the database view of qkit.fid

make sure to have qkit.fid enabled and %matplotlib qt executed beforehand
"""
import h5py
import matplotlib.pyplot as plt
import numpy as np
from IPython.core.display import display, HTML

import qkit


class QuickPlot(object):
    def __init__(self, maximize=True):
        """
        Quickplot routine to scan through your measurement data.
        The maximize switch can be used to increase the width of
        the notebook view, giving you more space for the database table.
        """
        self.fig, [self.ax1, self.ax2] = plt.subplots(2, num="Quickplot", clear=True)
        self.remove_offset_x_avg = False
        self.remove_offset_y_avg = False
        self.unwrap_phase = False
        if maximize:
            display(HTML("<style>.container { width:100% !important; }</style>"))
    
    def plot_selected_df(self, change):
        uuid = qkit.fid._selected_df.index[0]
        d = h5py.File(qkit.fid.h5_db[uuid], 'r')
        try:
            self.ax1.cla()
            self.ax2.cla()
            self.ax2.set_title("WORKING")
            self.fig.canvas.draw()
            self.ax1.set_title(uuid + " | " + qkit.fid.h5_info_db[uuid]['name'])
            if "amplitude_midpoint" in d["entry/data0"].keys():
                self.plot_2D("amplitude_midpoint", "phase_midpoint", d)
            elif "amplitude" in d["entry/data0"].keys():
                if len(d["entry/data0/amplitude"].shape) == 3:
                    self.plot_4D("amplitude", "phase", d)
                if len(d["entry/data0/amplitude"].shape) == 2:
                    self.plot_3D("amplitude", "phase", d)
                elif len(d["entry/data0/amplitude"].shape) == 1:
                    self.plot_2D("amplitude", "phase", d)
            else:
                print("No matching entries found for file %s" % uuid)
            self.fig.tight_layout()
        except Exception as e:
            print(e)
        finally:
            d.close()
            self.ax2.set_title("")
            self.ax1.autoscale_view()
            self.fig.canvas.draw()
    
    @staticmethod
    def si_prefix(data):
        switch = int(np.floor(np.log10(np.max(np.abs(np.array(data)))) / 3)) * 3
        try:
            return {
                -9: [1e-9, "nano", "n"],
                -6: [1e-6, "micro", "u"],
                -3: [1e-3, "mili", "m"],
                0 : [1, "", ""],
                3 : [1e3, "kilo", "k"],
                6 : [1e6, "Mega", "M"],
                9 : [1e9, "Giga", "G"]
            }[switch]
        except KeyError:
            return [1, "", ""]
    
    def plot_4D(self, key1, key2, d):
        if type(key1) is not list:
            key1 = [key1]
        if type(key2) is not list:
            key2 = [key2]
        
        def _plot(axis, k, d):
            if "/" not in k:
                k = "entry/data0/" + k
            si_x = self.si_prefix(d[d[k].attrs['x_ds_url']])
            si_y = self.si_prefix(d[d[k].attrs['y_ds_url']])
            z_index = int(d[k].shape[2] / 2)
            data = d[k][:, :, z_index].T
            if self.unwrap_phase and k.split("/")[-1] == "phase":
                data.T[~np.isnan(data.T)] = np.unwrap(data.T[~np.isnan(data.T)])
            if self.remove_offset_x_avg:
                data -= np.nanmean(data, axis=1, keepdims=True)
            if self.remove_offset_y_avg:
                data -= np.nanmean(data, axis=0, keepdims=True)
            axis.pcolorfast(d[d[k].attrs['x_ds_url']][:d[k].shape[0]] / si_x[0], d[d[k].attrs['y_ds_url']][:d[k].shape[1]] / si_y[0], data)
            axis.set_xlabel("%s (%s%s)" % (d[d[k].attrs['x_ds_url']].attrs['name'], si_x[2], d[d[k].attrs['x_ds_url']].attrs['unit']))
            axis.set_ylabel("%s (%s%s)" % (d[d[k].attrs['y_ds_url']].attrs['name'], si_y[2], d[d[k].attrs['y_ds_url']].attrs['unit']))
        
        for k in key1:
            _plot(self.ax1, k, d)
        for k in key2:
            _plot(self.ax2, k, d)
    
    def plot_3D(self, key1, key2, d):
        if type(key1) is not list:
            key1 = [key1]
        if type(key2) is not list:
            key2 = [key2]
        
        def _plot(axis, k, d):
            if "/" not in k:
                k = "entry/data0/" + k
            si_x = self.si_prefix(d[d[k].attrs['x_ds_url']])
            si_y = self.si_prefix(d[d[k].attrs['y_ds_url']])
            data = d[k][:].T
            if self.unwrap_phase and k.split("/")[-1] == "phase":
                data[~np.isnan(data)] = np.unwrap(data[~np.isnan(data)], axis=0)
            if self.remove_offset_x_avg:
                data -= np.nanmean(data, axis=1, keepdims=True)
            if self.remove_offset_y_avg:
                data -= np.nanmean(data, axis=0, keepdims=True)
            axis.pcolorfast(d[d[k].attrs['x_ds_url']][:d[k].shape[0]] / si_x[0], d[d[k].attrs['y_ds_url']][:d[k].shape[1]] / si_y[0], data)
            axis.set_xlabel("%s (%s%s)" % (d[d[k].attrs['x_ds_url']].attrs['name'], si_x[2], d[d[k].attrs['x_ds_url']].attrs['unit']))
            axis.set_ylabel("%s (%s%s)" % (d[d[k].attrs['y_ds_url']].attrs['name'], si_y[2], d[d[k].attrs['y_ds_url']].attrs['unit']))
        
        for k in key1:
            _plot(self.ax1, k, d)
        for k in key2:
            _plot(self.ax2, k, d)
    
    def plot_2D(self, key1, key2, d):
        if type(key1) is not list:
            key1 = [key1]
        if type(key2) is not list:
            key2 = [key2]
        
        def _plot(axis, k, d):
            if "/" not in k:
                k = "entry/data0/" + k
            si_x = self.si_prefix(d[d[k].attrs['x_ds_url']])
            si_d = self.si_prefix(d[k])
            axis.plot(d[d[k].attrs['x_ds_url']][:d[k].shape[0]] / si_x[0], d[k][:] / si_d[0])
            axis.set_ylabel("%s (%s%s)" % (d[k].attrs['name'], si_d[2], d[k].attrs['unit']))
            axis.set_xlabel("%s (%s%s)" % (d[d[k].attrs['x_ds_url']].attrs['name'], si_x[2], d[d[k].attrs['x_ds_url']].attrs['unit']))
        
        for k in key1:
            _plot(self.ax1, k, d)
        for k in key2:
            _plot(self.ax2, k, d)
    
    def show(self):
        qkit.fid.show()
        qkit.fid.grid.observe(self.plot_selected_df, names=['_selected_rows'])
        return qkit.fid.grid
