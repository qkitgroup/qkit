"""
wafeform plotter JB@KIT 02/2016 jochen.braumueller@kit.edu

The waveform plotter wf_plot.py visualizes the waveform generated and employed for a measurement.
Prospectively, the plotter may be called by default to save a picture of the pulse sequence.

input:		analog_wfm: single (homodyne) or tuple of matrices carrying analog entries for traces and points in AWG window
            seq: sequence to be plotted, default 1
            complete_marker: single marker matrice or set of up to for marker lists (possibly arranged as [[...],[...]])
            xrange: xrange to be plotted
            sample
output: -
"""

import numpy as np
import matplotlib.pyplot as plt
# import os, glob
import time
import logging

no_qkit = False
try:
    import qkit
    data_dir_config = qkit.cfg.get('datadir')
except ImportError:
    logging.warning('no qkit environment')
    no_qkit = True


def wfplot(analog_wfm, seq=1, complete_marker=None, x_range=None, sample=None):
    font = {'weight': 'normal', 'size': 16}
    plt.rc('font', **font)
    labelsize = 16
    fig, axis = plt.subplots(figsize=(15, 5))

    # extract x axis information
    if sample != None:
        xval = np.linspace(0, sample.exc_T * 1e6, int(np.round(sample.exc_T * sample.clock) / 4) * 4)  # in us
        axis.set_xlabel(r'$time\,(\mathrm{\mu s})$', fontsize=labelsize)

        try:
            t = np.arange(0, sample.readout_tone_length, 1 / sample.readout_clock)
            r1 = np.sin(2 * np.pi * t * sample.readout_iq_frequency)
            r2 = np.cos(2 * np.pi * t * sample.readout_iq_frequency)
            axis.plot((sample.exc_T - sample.overlap * 1e-9) * 1e6 + range(len(r1)), r1, 'black')
            axis.plot((sample.exc_T - sample.overlap * 1e-9) * 1e6 + range(len(r1)), r2, 'black')
        except:
            logging.warning('readout pulse not plotted: sample parameters not found')
    else:
        axis.set_xlabel('# samples', fontsize=labelsize)
        if isinstance(analog_wfm[seq][0], (list, tuple, np.ndarray)):  # heterodyne mode
            xval = np.arange(0, len(analog_wfm[seq][0]))
        else:
            xval = np.arange(0, len(analog_wfm[seq]))

    if isinstance(analog_wfm[seq][0], (list, tuple, np.ndarray)):  # heterodyne mode
        axis.plot(xval, analog_wfm[seq][0], 'red', alpha=0.7, label='I')
        axis.plot(xval, analog_wfm[seq][1], 'blue', alpha=0.7, label='Q')
    else:
        axis.fill_between(xval, 0, analog_wfm[seq], color='red', alpha=0.7)
        axis.plot(xval, analog_wfm[seq], 'r-', alpha=0.7, label='homodyne')

    if complete_marker != None:
        clr_dict = {0: 'grey', 1: 'magneta', 2: 'green', 3: 'tan'}
        if len(np.array(complete_marker).shape) > 2:  # more than one single marker
            markers = np.array(complete_marker).reshape(4, np.array(complete_marker).shape[2],
                                                        np.array(complete_marker).shape[3])
        else:
            markers = [np.array(complete_marker)]

        maxis = axis.twinx()
        xlm = len(xval)
        xrm = 0
        for mi, m in enumerate(markers):
            if (m != np.zeros_like(m)).any() and m != None:
                maxis.fill_between(xval, 0, float(4 - mi) / 2 * m[seq], color=clr_dict[mi], alpha=0.7)
                maxis.plot(xval, float(4 - mi) / 2 * m[seq], color=clr_dict[mi], alpha=0.7, label='m%d' % mi)
                ''' find appropriate boundaries for the plot window '''
                xl = np.min(xlm, np.where(np.array(m[seq]) > 0)[0][0])
                xr = np.max(xrm, np.where(np.array(m[seq]) > 0)[0][-1])
        maxis.legend(loc=1)

    axis.legend(loc=2)
    if xrange != None:
        plt.xlim(x_range)
    else:
        ''' find appropriate window by cutting off edge regions filled with zeros '''
        if isinstance(analog_wfm[seq][0], (list, tuple, np.ndarray)):  # heterodyne mode
            xl = np.min(xl, np.where(np.gradient(analog_wfm[seq][0]) > 0)[0][0])
            xr = np.max(xr, np.where(np.gradient(analog_wfm[seq][0]) > 0)[0][-1])
        else:
            xl = np.min(xl, np.where(np.gradient(analog_wfm[seq]) > 0)[0][0])
            xr = np.max(xr, np.where(np.gradient(analog_wfm[seq]) > 0)[0][-1])

        # put some space left and right and check whether this is still a valid window
        xl -= 100
        if xl < 0:
            xl = 0
        xr += 100
        if xr > len(xval):
            xr = len(xval)

        plt.xlim([xl, xr])

    fig.tight_layout()
