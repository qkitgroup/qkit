# -*- coding: utf-8 -*-
"""
@author: andre.schneider@kit.edu / 2019
@author: micha.wildermuth@kit.edu / 2019
@license: GPL

This file provides some methods to quickly plot different datasets in a
matplotlib (QT) window. The data file to show can be easily selected in
the database view of qkit.fid

make sure to have qkit.fid enabled and %matplotlib qt executed beforehand
"""
import h5py
import json
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
        self.fig, self.ax = plt.subplots(2, num="Quickplot", clear=True)
        self.args, self.kwargs = (), {}
        self.m_type, self.ds_type, self.num_plots = None, None, None
        self.remove_offset_x_avg = False
        self.remove_offset_y_avg = False
        self.unwrap_phase = False
        if maximize:
            display(HTML("<style>.container { width:100% !important; }</style>"))
    
    def plot_selected_df(self, change):
        uuid = qkit.fid._selected_df.index[0]
        self.d = h5py.File(qkit.fid.h5_db[uuid], "r")
        try:
            self.m_type = json.loads(self.d["entry/data0/measurement"][0])["measurement_type"]
        except:
            self.m_type = None
        if self.m_type == "transport":
            self.overlays = self.d["entry/views/IV"].attrs[u"overlays"]+1
        else:
            self.overlays = None
        try:
            self.ds_type = self.d["entry/data0/"+{"spectroscopy": "amplitude", "transport": "v_0"}[self.m_type]].attrs["ds_type"]
        except:
            self.ds_type = None
        if self.args is () and self.kwargs == {}:
            self.num_plots = {"spectroscopy": 2,
                              "transport": (1, self.overlays, self.overlays)[self.ds_type-1]}[self.m_type]
        else:
            self.num_plots = len(self.args)+sum([1 if type(val) is str else len(val) for val in self.kwargs.values()])
        try:
            plt.clf()
            self.fig, self.ax = plt.subplots(self.num_plots, num="Quickplot", clear=True)
            if not np.iterable(self.ax):
                self.ax = [self.ax]
            self.fig.canvas.draw()
            self.ax[0].set_title(uuid + " | " + qkit.fid.h5_info_db[uuid]["name"])
            args = {}
            if self.m_type == "spectroscopy":
                if "amplitude_midpoint" in self.d["entry/data0"].keys():
                    self.plot_2D("amplitude_midpoint", "phase_midpoint")
                else:
                    if self.args == ():
                        args["ds"] = ["amplitude", "phase"]
                    else:
                        args["ds"] = list(self.args)
                    [self.plot_1D, self.plot_2D, self.plot_3D][self.ds_type - 1](args)
            elif self.m_type == "transport":
                if self.args == () and self.kwargs == {}:
                    if self.ds_type == 1:
                        args["view"] = ["IV"]
                    else:
                        args["ds"] = ["v_" + str(i) for i in range(self.overlays)]
                else:
                    if len(self.args) != 0:
                        args["ds"] = list(self.args)
                    if "ds" in self.kwargs.keys():
                        if len(argss["ds"]) != 0:
                            args["ds"] = list(self.kwargs["ds"])
                        else:
                            args["ds"].append(self.kwargs["ds"])
                    if "view" in self.kwargs.keys():
                        args["view"] = self.kwargs["view"] if type(self.kwargs["view"])==list else [self.kwargs["view"]]
                [self.plot_1D, self.plot_2D, self.plot_3D][self.ds_type - 1](args)
            else:
                print("No matching entries found for file %s" % uuid)
            self.fig.tight_layout()
        except Exception as e:
            print(e)
        finally:
            self.d.close()
            [ax.set_title("") for ax in self.ax[1:]]
            self.ax[0].autoscale_view()
            self.fig.canvas.draw()
    
    @staticmethod
    def si_prefix(data):
        switch = int(np.floor(np.log10(np.max(np.abs(np.array(data)))) / 3)) * 3
        try:
            return {
                -9: [1e-9, "nano", "n"],
                -6: [1e-6, "micro", "u"],
                -3: [1e-3, "milli", "m"],
                0 : [1, "", ""],
                3 : [1e3, "kilo", "k"],
                6 : [1e6, "Mega", "M"],
                9 : [1e9, "Giga", "G"]
            }[switch]
        except KeyError:
            return [1, "", ""]
    
    def plot_3D(self, args):
        def _plot(ax, key, val):
            if key == "view":
                for i in range(self.overlays):
                    x_url, d_url = self.d["entry/views/" + val].attrs[u"xy_" + str(i)].split(":")
                    si_x = self.si_prefix(self.d[x_url])
                    si_d = self.si_prefix(self.d[d_url])
                    x_index = int(self.d[x_url].shape[0] / 2)
                    y_index = int(self.d[x_url].shape[1] / 2)
                    ax.plot(self.d[x_url][x_index,y_index,:] / si_x[0], self.d[d_url][x_index,y_index,:] / si_d[0])
                    ax.set_xlabel("%s (%s%s)" % (self.d[x_url].attrs["name"], si_x[2], self.d[x_url].attrs["unit"]))
                    ax.set_ylabel("%s (%s%s)" % (self.d[d_url].attrs["name"], si_d[2], self.d[d_url].attrs["unit"]))
            elif key == "ds":
                if "/" not in val:
                    val = "entry/data0/" + val
                si_x = self.si_prefix(self.d[self.d[val].attrs["x_ds_url"]])
                si_y = self.si_prefix(self.d[self.d[val].attrs["y_ds_url"]])
                z_index = int(self.d[val].shape[2] / 2)
                data = self.d[val][:, :, z_index].T
                if self.unwrap_phase and val.split("/")[-1] == "phase":
                    data.T[~np.isnan(data.T)] = np.unwrap(data.T[~np.isnan(data.T)])
                if self.remove_offset_x_avg:
                    data -= np.nanmean(data, axis=1, keepdims=True)
                if self.remove_offset_y_avg:
                    data -= np.nanmean(data, axis=0, keepdims=True)
                ax.pcolormesh(self.d[self.d[val].attrs["x_ds_url"]][:self.d[val].shape[0]] / si_x[0], self.d[self.d[val].attrs["y_ds_url"]][:self.d[val].shape[1]] / si_y[0], data)
                ax.set_xlabel("%s (%s%s)" % (self.d[self.d[val].attrs["x_ds_url"]].attrs["name"], si_x[2], self.d[self.d[val].attrs["x_ds_url"]].attrs["unit"]))
                ax.set_ylabel("%s (%s%s)" % (self.d[self.d[val].attrs["y_ds_url"]].attrs["name"], si_y[2], self.d[self.d[val].attrs["y_ds_url"]].attrs["unit"]))
        ax_iter = iter(self.ax)
        for key, vals in args.items():
            for val in vals:
                _plot(next(ax_iter), key, val)

    def plot_2D(self, args):
        def _plot(ax, key, val):
            if key == "view":
                for i in range(self.overlays):
                    x_url, d_url = self.d["entry/views/" + val].attrs[u"xy_" + str(i)].split(":")
                    si_x = self.si_prefix(self.d[x_url])
                    si_d = self.si_prefix(self.d[d_url])
                    y_index = int(self.d[x_url].shape[0] / 2)
                    ax.plot(self.d[x_url][y_index,:] / si_x[0], self.d[d_url][y_index,:] / si_d[0])
                    ax.set_xlabel("%s (%s%s)" % (self.d[x_url].attrs["name"], si_x[2], self.d[x_url].attrs["unit"]))
                    ax.set_ylabel("%s (%s%s)" % (self.d[d_url].attrs["name"], si_d[2], self.d[d_url].attrs["unit"]))
            elif key == "ds":
                if "/" not in val:
                    val = "entry/data0/" + val
                si_x = self.si_prefix(self.d[self.d[val].attrs["x_ds_url"]])
                si_y = self.si_prefix(self.d[self.d[val].attrs["y_ds_url"]])
                data = self.d[val][:].T
                if self.unwrap_phase and val.split("/")[-1] == "phase":
                    data[~np.isnan(data)] = np.unwrap(data[~np.isnan(data)], axis=0)
                if self.remove_offset_x_avg:
                    data -= np.nanmean(data, axis=1, keepdims=True)
                if self.remove_offset_y_avg:
                    data -= np.nanmean(data, axis=0, keepdims=True)
                ax.pcolormesh(self.d[self.d[val].attrs["x_ds_url"]][:self.d[val][:].shape[0]] / si_x[0],
                              self.d[self.d[val].attrs["y_ds_url"]][:self.d[val][:].shape[1]] / si_y[0],
                              data)
                ax.set_xlabel("%s (%s%s)" % (self.d[self.d[val].attrs["x_ds_url"]].attrs["name"], si_x[2], self.d[self.d[val].attrs["x_ds_url"]].attrs["unit"]))
                ax.set_ylabel("%s (%s%s)" % (self.d[self.d[val].attrs["y_ds_url"]].attrs["name"], si_y[2], self.d[self.d[val].attrs["y_ds_url"]].attrs["unit"]))
        ax_iter = iter(self.ax)
        for key, vals in args.items():
            for val in vals:
                _plot(next(ax_iter), key, val)
    
    def plot_1D(self, args):
        def _plot(ax, key, val):
            if key == "view":
                for i in range(self.overlays):
                    x_url, d_url = self.d["entry/views/"+val].attrs[u"xy_" + str(i)].split(":")
                    si_x = self.si_prefix(self.d[x_url])
                    si_d = self.si_prefix(self.d[d_url])
                    ax.plot(self.d[x_url][:] / si_x[0], self.d[d_url][:] / si_d[0])
                    ax.set_ylabel("%s (%s%s)" % (self.d[d_url].attrs["name"], si_d[2], self.d[d_url].attrs["unit"]))
                    ax.set_xlabel("%s (%s%s)" % (self.d[x_url].attrs["name"], si_x[2], self.d[x_url].attrs["unit"]))
            elif key == "ds":
                if "/" not in val:
                    val = "entry/data0/" + val
                si_x = self.si_prefix(self.d[self.d[val].attrs["x_ds_url"]])
                si_d = self.si_prefix(self.d[val])
                ax.plot(self.d[self.d[val].attrs["x_ds_url"]][:self.d[val].shape[0]] / si_x[0], self.d[val][:] / si_d[0])
                ax.set_ylabel("%s (%s%s)" % (self.d[val].attrs["name"], si_d[2], self.d[val].attrs["unit"]))
                ax.set_xlabel("%s (%s%s)" % (self.d[self.d[val].attrs["x_ds_url"]].attrs["name"], si_x[2], self.d[self.d[val].attrs["x_ds_url"]].attrs["unit"]))
        self.output = self.ax, args
        ax_iter = iter(self.ax)
        for key, vals in args.items():
            for val in vals:
                _plot(next(ax_iter), key, val)

    def show(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        qkit.fid.show()
        qkit.fid.grid.observe(self.plot_selected_df, names=["_selected_rows"])
        return qkit.fid.grid
