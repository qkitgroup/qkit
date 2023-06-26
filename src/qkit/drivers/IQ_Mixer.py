# Toolset for calibrating and using IQ-Mixers as Single-Sideband-Mixers (SSB)
# Started by Andre Schneider 01/2015 <andre.schneider@student.kit.edu>

import qkit
from qkit.core.instrument_base import Instrument
import time
import types
import logging
import os
import numpy as np
if qkit.module_available("matplotlib"):
    import matplotlib.pyplot as plt
import sys, gc
from copy import copy


class IQ_Mixer(Instrument):

    def __init__(self, name, sample, mixer_name):
        Instrument.__init__(self, name, tags=['virtual'])
        self._sample = sample
        self._FSUP_connected = False
        self._fsup = None
        self._swb = None
        # self._iq_frequency = None
        self._output_power = None
        self._sideband_frequency = None
        self._mw_power = None
        self.maxage = 100 * 24 * 3600  # Age of calibration data in seconds
        self.interpol_freqspan = 1e9  # Frequency span where interpolated data is used and recalibrated
        self.trust_region = 500e6  # Frequency span where interpolated data is used without recalibration. Do not set this to zero, because calibration will round frequency
        self._iq_frequency = self._sample.iq_frequency
        self.do_set_mixer_name(mixer_name)

        self.cache_valid = False
        self.cache_frequency = self._sample.f01
        self.cache_power = self._sample.mw_power
        self.cache_iq = self._sample.iq_frequency

        # Parameters
        self.add_parameter('sideband_frequency', type=float,
                           flags=Instrument.FLAG_GET, units='Hz',
                           minval=1, maxval=20e9)

        self.add_parameter('output_power', type=float,
                           flags=Instrument.FLAG_GET, units='dBm')

        self.add_parameter('iq_frequency', type=float,
                           flags=Instrument.FLAG_GET, units='Hz',
                           minval=0,
                           maxval=1e9)  # This is only a get variable, because changing requires an update of all sequences in AWG

        self.add_parameter('FSUP_connected', type=bool,
                           flags=Instrument.FLAG_GET)

        self.add_parameter('mixer_name', type=str,
                           flags=Instrument.FLAG_GETSET)

        self.add_function('connect_FSUP')
        self.add_function('disconnect_FSUP')
        self.add_function('get_all')
        self.add_function('set_sample')

    IQ0307 = 'IQ0307'  # simply define the currently known mixers so you can see them when pressing tab
    IQ0318 = 'IQ0318'
    IQ4509 = 'IQ4509'

    _ch1_filename = 'ch1_opt'
    _ch2_filename = 'ch2_opt'
    _awg_filepath = 'C:\\waveforms\\'
    (x, y) = (0, 0)  # initial values for DC offset in Volts

    def get_all(self):
        self.get_FSUP_connected()
        self.get_iq_frequency()
        self.get_output_power()
        self.get_sideband_frequency()

    def ch1(self, t):
        return np.cos(t)

    def ch2(self, t):
        return np.sin(t)

    def set_sample(self, sample):
        self._sample = sample
        self.cache_valid = False

    def do_set_mixer_name(self, mixer_name):
        self.mixer_name = mixer_name
        self.cache_valid = False

    def do_get_mixer_name(self):
        return self.mixer_name

    def do_get_FSUP_connected(self):
        return self._FSUP_connected

    def do_set_sideband_frequency(self, frequency):
        self._sideband_frequency = frequency

    def do_get_sideband_frequency(self):
        return self._sideband_frequency

    def do_set_mw_power(self, mw_power):
        self._mw_power = mw_power

    def do_get_output_power(self):
        return self._output_power

    def do_get_iq_frequency(self):
        '''This returns the iq_frequency which was used for the last call of convert()'''
        return self._iq_frequency

    def do_set_iq_frequency(self, iq_frequency):
        self._iq_frequency = iq_frequency

    def connect_FSUP(self, fsup):
        self._fsup = fsup
        self._FSUP_connected = True

    def disconnect_FSUP(self):
        self._FSUP_connected = False

    def connect_switchbox(self, swb):
        '''
        as a default, Ch1 is cryo, Ch2 is fsup.
        '''
        self._swb = swb

    def disconnect_switchbox(self):
        self._swb = None

    def dcoptimize(self, DC):
        # you need to have a zero-waveform loaded in the awg and turn outputs on!
        if (np.abs(DC[0]) > .5 or np.abs(DC[1]) > .5):
            qkit.flow.sleep()
            return 50
        self._sample.awg.set({'ch1_offset': DC[0], 'ch2_offset': DC[1]})
        # qkit.flow.sleep(.05)
        self._fsup.sweep()
        return np.around(self._fsup.get_marker_level(1), 2)  # assuming that marker1 is at leakage frequency

    def xoptimize(self, x):
        # you need to have a zero-waveform loaded in the awg and turn outputs on!
        if (np.abs(x) > .5):
            qkit.flow.sleep()
            return 50
        self._sample.awg.set_ch1_offset(x)
        self._fsup.sweep()
        return np.around(self._fsup.get_marker_level(1), 2)  # assuming that marker1 is at leakage frequency

    def yoptimize(self, y):
        # you need to have a zero-waveform loaded in the awg and turn outputs on!
        if (np.abs(y) > .5):
            qkit.flow.sleep()
            return 50
        self._sample.awg.set_ch2_offset(y)
        self._fsup.sweep()
        return np.around(self._fsup.get_marker_level(1), 2)  # assuming that marker1 is at leakage frequency

    def relampoptimize(self, amp):
        self._sample.awg.set_ch1_amplitude(amp)
        self._fsup.sweep()
        return np.around(self._fsup.get_marker_level(4), 2)  # assuming that marker4 is at unwanted sideband

    def relampoptimize2(self, amp):
        self._sample.awg.set_ch2_amplitude(amp)
        self._fsup.sweep()
        return np.around(self._fsup.get_marker_level(4), 2)  # assuming that marker4 is at unwanted sideband

    def focus(self, frequency, marker):
        self._fsup.enable_marker(1, 'OFF')
        self._fsup.enable_marker(2, 'OFF')
        self._fsup.enable_marker(3, 'OFF')
        self._fsup.enable_marker(4, 'OFF')
        self._fsup.set_continuous_sweep_mode('OFF')
        self._fsup.set({'centerfreq': frequency,
                        'freqspan': 2e2,
                        'resolutionBW': 200,
                        'videoBW': 200})
        self._fsup.set_marker(marker, frequency)
        sweeptime = self._fsup.get_sweeptime()
        self._fsup.sweep()
        return sweeptime

    def load_zeros(self):
        ch1wfm = np.zeros(10)
        ch2wfm = np.zeros(10)
        marker = np.zeros_like(ch1wfm)
        self._sample.awg.wfm_send(ch1wfm, marker, marker, self._awg_filepath + self._ch1_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch1_filename, self._awg_filepath + self._ch1_filename, 'WFM')
        self._sample.awg.wfm_send(ch2wfm, marker, marker, self._awg_filepath + self._ch2_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch2_filename, self._awg_filepath + self._ch2_filename, 'WFM')
        self._sample.awg.set({'ch1_waveform': self._ch1_filename,
                              'ch1_offset': 0,
                              'ch1_amplitude': 1,
                              'ch1_waveform': self._ch2_filename,
                              'ch1_offset': 0,
                              'ch1_amplitude': 1})
        self._sample.awg.run()
        self._sample.awg.set({'ch1_output': 1, 'ch2_output': 1})

    def load_wfm_init(self):
        t = np.linspace(0, 2 * np.pi, self._sample.clock / self._iq_frequency, endpoint=False)
        ch1wfm = self.ch1(t)
        ch2wfm = self.ch2(t)
        marker = np.zeros_like(ch1wfm)
        self._sample.awg.wfm_send(ch2wfm, marker, marker, self._awg_filepath + self._ch2_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch2_filename, self._awg_filepath + self._ch2_filename, 'WFM')
        self._sample.awg.set_ch2_waveform(self._ch2_filename)
        self._sample.awg.wfm_send(ch1wfm, marker, marker, self._awg_filepath + self._ch1_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch1_filename, self._awg_filepath + self._ch1_filename, 'WFM')
        self._sample.awg.set_ch1_waveform(self._ch1_filename)
        self._sample.awg.run()
        self._sample.awg.set({'ch1_output': 1, 'ch2_output': 1})

    def optimize_dc(self, frequency, x, y, maxiter=10, verbose=False):
        self.focus(frequency, 1)
        for i in range(0, maxiter):
            xold = x
            yold = y
            x = opt.minimize_scalar(lambda x: self.dcoptimize([x, y]), method='golden', tol=0.1).x
            if (verbose): print(" %.3f  (%.3f) %.2fdBm" % (x, y, self.dcoptimize([x, y])))
            sys.stdout.flush()
            y = opt.minimize_scalar(lambda y: self.dcoptimize([x, y]), method='golden', tol=0.1).x
            if (verbose): print("(%.3f)  %.3f  %.2fdBm" % (x, y, self.dcoptimize([x, y])))
            sys.stdout.flush()
            if (np.around(xold - x, 3) == 0 and np.around(yold - y, 3) == 0):
                if (verbose): print("Finished after %i iterations with delta x: %.5f delta y: %.5f" % (
                    i + 1, xold - x, yold - y))
                break
        return [x, y]

    def optimize_phase(self):
        self.focus(self._f_rounded - 2 * self._iq_frequency, 4)
        return opt.minimize_scalar(self.phaseoptimize, method="bounded", bounds=(0, 2 * np.pi),
                                   options={"xatol": .01}).x

    def optimize_relamp(self):
        self.focus(self._f_rounded - 2 * self._iq_frequency, 4)
        return opt.minimize_scalar(self.relampoptimize, method="bounded", bounds=(0, 2), options={"xatol": .001}).x

    def findmin(self, function, start, stop, stepsize, plot=False, averages=1):
        a = np.arange(start, stop + stepsize / 2, stepsize)
        if (len(a) < 2):
            # print "*************TRYING TO MINIMIZE %s BETWEEN %f and %f => NOT POSSIBLE!*********"%(function,start,stop)
            return start
        b = np.zeros(len(a))
        for u, v in enumerate(a):
            for i in range(averages):
                b[u] += function(v)
        b = b / averages
        if plot and qkit.module_available("matplotlib"):
            plt.plot(a, b, "k*-")
            plt.show()
        return a[b.argmin()]

    def minimize(self, function, start, stop, init_stepsize, min_stepsize, initial_averages=1, final_averages=5,
                 verbose=False, hardbounds=False, confirmonly=False, bounds=(-np.inf, np.inf)):
        '''
            returns (value,function value) where function is minimal
            The bounds are not really hard: if this function leaves your bounds, you should increase initial stepsize and initial averages
        '''
        if hardbounds:
            print("HARDBOUNDS is no longer supported, use bounds=(lowe,upper) instead!")
        if confirmonly:
            stepsize = min_stepsize
            x = (start + stop) / 2
            initial_averages = final_averages
        else:
            stepsize = init_stepsize
            x = self.findmin(function, start, stop, stepsize, verbose, initial_averages)
            if (verbose): print("stepsize was %f, minimum detected at %f" % (init_stepsize, x))
            if (x == start):
                x = start - 3 * stepsize
            elif (x == stop):
                x = stop + 3 * stepsize
            else:
                stepsize = max(stepsize / 10, min_stepsize)
        while True:
            xold = x
            x = self.findmin(function, max(bounds[0], x - 3 * stepsize), min(bounds[1], x + 3 * stepsize), stepsize,
                             verbose, initial_averages)
            if (verbose): print("stepsize was %f, minimum detected at %f" % (stepsize, x))
            if (x == xold - 3 * stepsize):
                x -= 2 * stepsize
            elif (x == xold + 3 * stepsize):
                x += 2 * stepsize
            else:
                if confirmonly:
                    return (x, function(x))
                if (stepsize == min_stepsize):
                    break
                stepsize = max(stepsize / 5, min_stepsize)
        if (verbose): print("Finishing with stepsize %f" % (stepsize))
        x = self.findmin(function, max(bounds[0], x - 2 * stepsize), min(bounds[1], x + 2 * stepsize), stepsize,
                         verbose, final_averages)
        return (x, function(x))

    def load_zeros(self):
        ch1wfm = np.zeros(10)
        ch2wfm = np.zeros(10)
        marker = np.zeros_like(ch1wfm)
        self._sample.awg.wfm_send(ch1wfm, marker, marker, self._awg_filepath + self._ch1_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch1_filename, self._awg_filepath + self._ch1_filename, 'WFM')
        self._sample.awg.wfm_send(ch2wfm, marker, marker, self._awg_filepath + self._ch2_filename, self._sample.clock)
        self._sample.awg.wfm_import(self._ch2_filename, self._awg_filepath + self._ch2_filename, 'WFM')
        self._sample.awg.set({'ch1_waveform': self._ch1_filename,
                              'ch1_offset': 0,
                              'ch1_amplitude': 2,
                              'ch2_waveform': self._ch2_filename,
                              'ch1_offset': 0,
                              'ch1_amplitude': 2})
        self._sample.awg.run()
        self._sample.awg.set({'ch1_output': 1, 'ch2_output': 1})

    def load_wfm(self, sin_phase=0, update_channels=(True, True), init=False, relamp=1.5, relamp2=1.5):
        if (update_channels[0]):
            t1 = np.linspace(sin_phase, sin_phase + 2 * np.pi, self._sample.clock / self._iq_frequency, endpoint=False)
            ch1wfm = self.ch1(t1)
            marker = np.zeros_like(ch1wfm)
            self._sample.awg.wfm_send(ch1wfm, marker, marker, self._awg_filepath + self._ch1_filename,
                                      self._sample.clock)
            self._sample.awg.wfm_import(self._ch1_filename, self._awg_filepath + self._ch1_filename, 'WFM')
            self._sample.awg.set_ch1_waveform(self._ch1_filename)
        if (update_channels[1]):
            t2 = np.linspace(0, 2 * np.pi, self._sample.clock / self._iq_frequency, endpoint=False)
            ch2wfm = self.ch2(t2)
            marker = np.zeros_like(ch2wfm)
            self._sample.awg.wfm_send(ch2wfm, marker, marker, self._awg_filepath + self._ch2_filename,
                                      self._sample.clock)
            self._sample.awg.wfm_import(self._ch2_filename, self._awg_filepath + self._ch2_filename, 'WFM')
            self._sample.awg.set_ch2_waveform(self._ch2_filename)
        if (init):
            self._sample.awg.set({'ch1_amplitude': relamp, 'ch2_amplitude': relamp2})
            self._sample.awg.run()
            self._sample.awg.set({'ch1_output': 1, 'ch2_output': 1})

    def phaseoptimize(self, offset):
        '''
        phase offset in radians
        '''
        self.load_wfm(sin_phase=offset, update_channels=(True, False))
        self._fsup.sweep()
        return self._fsup.get_marker_level(4)  # assuming that marker4 is at unwanted sideband

    def recalibrate(self, dcx, dcy, x, y, phaseoffset, relamp, relamp2):
        self.cache_valid = False
        if self._swb is not None:  # switching to fsup
            self._swb.set_position('2')
        else:
            logging.warning(
                __name__ + ' : Switch was not switched. Define switchbox instrument via iq.connect_switchbox(swb). If you do not have a switchbox, make sure your cables are connected and go on.')
        self._sample.awg.set_clock(self._sample.clock)
        if not self._FSUP_connected:
            raise ValueError((
                                 'FSUP is possibly not connected. \nIncrease trust_region and maxage to interpolate values or connect FSUP and execute connect_FSUP(fsup)'))
        qkit.flow.start()
        (hx_amp, hx_phase, hy_amp, hy_phase) = (0, 0, 0, 0)
        if self._iq_frequency == 0: logging.warning(
            __name__ + ': Your IQ Frequency is 0. It is better to calibrate with a finite IQ frequency because you will get inconsistent data in the calibration file otherwise. If you calibrate with iq!=0, the right values for iq=0 are extracted.')
        mw_freq = self._f_rounded - self._iq_frequency
        # self._sample.awg.stop()
        self._sample.awg.set({'ch1_output': 0, 'ch2_output': 0, 'runmode': 'CONT'})
        self._sample.qubit_mw_src.set({'frequency': mw_freq, 'power': self._mw_power, 'status': 1})

        print("Recalibrating %s for Frequency: %.2fGHz (MW-Freq: %.2fGHz), MW Power: %.2fdBm" % (
            self.mixer_name, self._sideband_frequency / 1e9, mw_freq / 1e9, self._mw_power))
        sys.stdout.flush()
        frequencies = [mw_freq - 3 * self._iq_frequency, mw_freq - 2 * self._iq_frequency, mw_freq - self._iq_frequency,
                       mw_freq, mw_freq + self._iq_frequency, mw_freq + 2 * self._iq_frequency,
                       mw_freq + 3 * self._iq_frequency]
        self.focus(mw_freq, 1)
        self.load_zeros()
        print("Optimizing DC offsets to reduce leakage when there is no pulse")
        (xold, yold) = (np.inf, np.inf)
        while (np.all(np.around((dcx, dcy), 3) != np.around((xold, yold), 3))):
            (xold, yold) = (dcx, dcy)
            dcx = self.minimize(self.xoptimize, dcx - .002, dcx + .002, .002, 1e-3, final_averages=3, confirmonly=True)[
                0]
            dcy = self.minimize(self.yoptimize, dcy - .002, dcy + .002, .002, 1e-3, final_averages=3, confirmonly=True)[
                0]
        if not self._iq_frequency == 0:
            self.load_wfm(sin_phase=phaseoffset, update_channels=(True, True), relamp=relamp, relamp2=relamp2,
                          init=True)
            optimized = [(self.focus(frequencies[i], 1), self._fsup.get_marker_level(1))[1] for i in
                         range(len(frequencies))]
            optimized_old = [np.inf, np.inf, np.inf, np.inf]
            print("iterating")
            while (optimized_old[2] - optimized[2] > 1 or optimized_old[3] - optimized[3] > 1):
                print ".",
                sys.stdout.flush()
                optimized_old = copy(optimized)
                self.focus(mw_freq, 1)
                (xold, yold) = (np.inf, np.inf)
                while (np.all(np.around((x, y), 3) != np.around((xold, yold), 3))):
                    (xold, yold) = (x, y)
                    x = \
                    self.minimize(self.xoptimize, x - .002, x + .002, .001, 1e-3, final_averages=1, confirmonly=True)[0]
                    y = \
                    self.minimize(self.yoptimize, y - .002, y + .002, .001, 1e-3, final_averages=1, confirmonly=True)[0]
                self.focus(mw_freq - self._iq_frequency, 4)
                phaseoffset = \
                self.minimize(self.phaseoptimize, phaseoffset - .15, phaseoffset + .15, 5e-3, 5e-3, final_averages=1,
                              confirmonly=True)[0]
                relamp = self.minimize(self.relampoptimize, relamp - .01, relamp + .01, .05, 1e-3, final_averages=2,
                                       bounds=(.5, 2), confirmonly=True)[0]
                relamp2 = self.minimize(self.relampoptimize2, relamp2 - .01, relamp2 + .01, .05, 1e-3, final_averages=2,
                                        bounds=(.5, 2), confirmonly=True)[0]
                optimized = [(self.focus(frequencies[i], 1),
                              np.mean([(self._fsup.sweep(), self._fsup.get_marker_level(1))[1] for j in range(5)]))[1]
                             for i in range(len(frequencies))]
        else:
            x, y, phaseoffset, relamp, relamp2 = 0, 0, 0, 1, 1
            optimized = [(self.focus(frequencies[i], 1),
                          np.mean([(self._fsup.sweep(), self._fsup.get_marker_level(1))[1] for j in range(5)]))[1] for i
                         in range(len(frequencies))]
        print("Parameters: DC x: %.1fmV, DC y: %.1fmV AC x: %.1fmV, AC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp" % (
            dcx * 1e3, dcy * 1e3, x * 1e3, y * 1e3, phaseoffset * 180 / np.pi, relamp, relamp2))
        print(
                "Your Sideband has a power of %.3fdBm, Leakage is %.2fdB lower, other sideband is %.2fdB lower.\nThe largest of the higher harmonics is %.2fdB lower." % (
                    optimized[4], optimized[4] - optimized[3], optimized[4] - optimized[2], np.max((optimized[4] - optimized[0],
                                                                                                    optimized[4] - optimized[1],
                                                                                                    optimized[4] - optimized[4],
                                                                                                    optimized[5] - optimized[6]))))
        data = np.array([np.append(
            (self._f_rounded, mw_freq, self._mw_power, time.time(), dcx, dcy, x, y, phaseoffset, relamp, relamp2),
            optimized)])
        currentdata = copy(data)

        # Make a nice image on the FSUP so that you can see the results of calibration there.
        self._fsup.set({'freqspan': self._iq_frequency * 10,
                        'centerfreq': self._sideband_frequency - self._iq_frequency,
                        'resolutionBW': 5e5,
                        'videoBW': 5e2})
        self._fsup.set_marker(1, self._sideband_frequency - self._iq_frequency)
        self._fsup.set_marker(2, self._sideband_frequency)
        self._fsup.set_marker(3, self._sideband_frequency + self._iq_frequency)
        self._fsup.set_marker(4, self._sideband_frequency + 2 * self._iq_frequency)
        sweeptime = self._fsup.get_sweeptime()
        self._fsup.sweep()
        qkit.flow.sleep(sweeptime)
        if qkit.module_available("matplotlib"):
            plt.plot(self._fsup.get_frequencies() / 1e9, self._fsup.get_trace())
            plt.xlabel('Frequency (GHz)')
            plt.ylabel('Power (dBm)')
            plt.grid()

        if self._swb is not None:  # switching back
            self._swb.set_position('1')
        # reset awg
        [self._sample.awg.set({'ch%i_amplitude' % i: 2, 'ch%i_offset' % i: 0}) for i in (1, 2)]

        try:
            storedvalues = np.loadtxt(os.path.join(qkit.cfg.getget('datadir'), "IQMixer\\%s.cal" % self.mixer_name))
            if np.size(storedvalues) < 30:  # Only one dataset
                storedvalues = [storedvalues]
            # If there was a calibration with the same parameters, remove it
            todelete = []
            for index, t in enumerate(storedvalues):
                if t[0] == self._f_rounded and t[1] == mw_freq and t[2] == self._mw_power:
                    todelete = np.append(todelete, index)
                    print("\nLast time (%s), there have been the following values:" % (time.ctime(t[3])))
                    print("Parameters: DC x: %.1fmV, DC y: %.1fmV phase: %.1fdegree Amplitude: %.3fVpp/%.3fVpp" % (
                        t[6] * 1e3, t[7] * 1e3, t[8] * 180 / np.pi, t[9], t[10]))
                    print(
                            "Your Sideband had a power of %.3fdBm, Leakage was %.2fdB lower, other sideband was %.2fdB lower.\nThe largest of the higher harmonics was %.2fdB lower." % (
                                t[15], t[15] - t[14], t[15] - t[13],
                                np.max((t[15] - t[11], t[15] - t[12], t[15] - t[16], t[15] - t[17]))))

            storedvalues = np.delete(storedvalues, todelete, axis=0)

            data = np.append(storedvalues, data)

        except IOError:
            pass
        data = data.reshape((data.size / 18, 18))
        np.savetxt(os.path.join(qkit.cfg.getget('datadir'), "IQMixer\\%s.cal" % self.mixer_name), data, (
        "%.2f", "%.2f", "%.2f", "%i", "%.3f", "%.3f", "%.3f", "%.3f", "%.6f", "%.3f", "%.3f", "%.4f", "%.4f", "%.4f",
        "%.4f", "%.4f", "%.4f", "%.4f"))
        return currentdata[0]

    def initial_calibrate(self):
        if not self._FSUP_connected:
            raise ValueError((
                                 'FSUP is possibly not connected. \nIncrease trust_region and maxage to interpolate values or connect FSUP and execute connect_FSUP(fsup)'))

        if self._swb is not None:  # switching to fsup
            self._swb.set_position('2')
        else:
            logging.warning(
                __name__ + ' : Switch was not switched. Define switchbox instrument via iq.connect_switchbox(swb). If you do not have a switchbox, make sure your cables are connected and go on.')
        qkit.flow.start()
        (hx_amp, hx_phase, hy_amp, hy_phase, phaseoffset) = (0, 0, 0, 0, 0)
        self._f_rounded = np.round(self._sideband_frequency, -3)
        mw_freq = self._f_rounded - self._iq_frequency
        if self._iq_frequency == 0: logging.warning(
            __name__ + ': Your IQ Frequency is 0. It is better to calibrate with a finite IQ frequency because you will get inconsistent data in the calibration file otherwise. If you calibrate with iq!=0, the right values for iq=0 are extracted.')

        # self._sample.awg.stop()
        self._sample.awg.set({'ch1_output': 0, 'ch2_output': 0, 'runmode': 'CONT'})
        self._sample.qubit_mw_src.set({'frequency': mw_freq, 'power': self._mw_power, 'status': 1})

        print("Starting an initial calibration of %s for Frequency: %.2fGHz (MW-Freq: %.2fGHz), MW Power: %.2fdBm" % (
            self.mixer_name, self._sideband_frequency / 1e9, mw_freq / 1e9, self._mw_power))
        sys.stdout.flush()
        frequencies = [mw_freq - 3 * self._iq_frequency, mw_freq - 2 * self._iq_frequency, mw_freq - self._iq_frequency,
                       mw_freq, mw_freq + self._iq_frequency, mw_freq + 2 * self._iq_frequency,
                       mw_freq + 3 * self._iq_frequency]
        self.focus(mw_freq, 1)
        self.load_zeros()
        (xold, yold) = (np.inf, np.inf)
        print("Finding initial values for DC offsets to reduce leakage when there is no pulse")
        dcx = self.minimize(self.xoptimize, -.02, .02, .01, 5e-3, final_averages=1)[0]
        dcy = self.minimize(self.yoptimize, -.02, .02, .01, 5e-3, final_averages=1)[0]
        while (np.all(np.around((dcx, dcy), 3) != np.around((xold, yold), 3))):
            (xold, yold) = (dcx, dcy)
            dcx = self.minimize(self.xoptimize, dcx - .002, dcx + .002, .002, 1e-3, final_averages=3, confirmonly=True)[
                0]
            dcy = self.minimize(self.yoptimize, dcy - .002, dcy + .002, .002, 1e-3, final_averages=3, confirmonly=True)[
                0]
        if not self._iq_frequency == 0:
            print("Finding initial values for Sine and Cosine waveform parameters")
            self.load_wfm(sin_phase=phaseoffset, update_channels=(True, True), relamp=2, relamp2=2, init=True)
            self.focus(mw_freq, 1)
            (xold, yold) = (0, 0)
            x = self.minimize(self.xoptimize, -.02, .02, .01, 5e-3, final_averages=1)[0]
            y = self.minimize(self.yoptimize, -.02, .02, .01, 5e-3, final_averages=1)[0]
            while (np.all(np.around((x, y), 3) != np.around((xold, yold), 3))):
                (xold, yold) = (x, y)
                x = self.minimize(self.xoptimize, x - .002, x + .002, .002, 2e-3, final_averages=1, verbose=False,
                                  confirmonly=True)[0]
                y = self.minimize(self.yoptimize, y - .002, y + .002, .002, 2e-3, final_averages=1, verbose=False,
                                  confirmonly=True)[0]
            self.focus(mw_freq - self._iq_frequency, 4)
            relamp = self.minimize(self.relampoptimize, 0.2, 2, .3, 10e-3, final_averages=1, bounds=(.5, 2))[0]
            relamp2 = self.minimize(self.relampoptimize2, 0.2, 2, .3, 10e-3, final_averages=1, bounds=(.5, 2))[0]
            phaseoffset = self.minimize(self.phaseoptimize, 0, 1, .2, 5e-3, final_averages=1)[0]
        else:
            x, y, phaseoffset, relamp, relamp2 = 0, 0, 0, 1, 1
        print("Initial parameterset found, starting optimization...")
        return self.recalibrate(dcx, dcy, x, y, phaseoffset, relamp, relamp2)

    def _validate_iq_setting(self):
        '''
        validates iq setting:
        the rounded Tektronix AWG clock devided by the iq frequency needs to be an integer number
        '''

        samples_per_1_iqfreq = float(self._sample.clock) / self._sample.iq_frequency
        if samples_per_1_iqfreq % 2 != 0:  # if number not integer and even
            self._sample.iq_frequency = self._sample.clock / (2 * np.floor(samples_per_1_iqfreq / 2))
            if np.abs(samples_per_1_iqfreq) < 4:
                raise ValueError('samples per iq frequency too small')
            while round(self._sample.iq_frequency, -4) != self._sample.iq_frequency:
                print(self._sample.iq_frequency)
                samples_per_1_iqfreq = float(self._sample.clock) / self._sample.iq_frequency - 1
                if samples_per_1_iqfreq < 4:
                    raise ValueError('samples per iq frequency too small')
                self._sample.iq_frequency = self._sample.clock / (2 * np.floor(samples_per_1_iqfreq / 2))
            logging.warning('Invalid iq frequency for AWG clock setting. Setting iq frequency to ' + str(
                self._sample.iq_frequency * 1e-6) + ' MHz')
        return self._sample.iq_frequency

    def calibrate(self, recalibrate=True, frequency=None, power=None, iq_frequency=None):
        '''
            This function automatically looks up, if this mixer has already been calibrated before:
            - If this frequency was calibrated less than maxage secs ago, it will just load this settings
            - If this frequency was calibrated more than maxage secs ago (or if you set recalibration=True), it will recalibrate, starting at the old parameters
            - If two adjacent frequencies, not further away than interpol_freqspan have been calibrated, interpolate starting values and recalibrate 
            - You can have the same behaviour as above without recalibrating, if you use trust_region instead of interpol_freqspan
            
        '''

        interpol_freqspan = np.max(
            (self.interpol_freqspan, self.trust_region)) / 2  # Half of the span in each direction

        if frequency is None:
            frequency = self._sample.f01
        if power is None:
            power = self._sample.mw_power
        if iq_frequency is None:
            iq_frequency = self._sample.iq_frequency
        self.do_set_sideband_frequency(frequency)
        self.do_set_mw_power(power)
        self.do_set_iq_frequency(iq_frequency)

        self._sample.iq_frequency = self._validate_iq_setting()

        self._f_rounded = np.round(self._sideband_frequency,
                                   -3)  # The FSUP can only resolve 7 digits in frequency, so for Frequencies <10GHz, you can not set frequencies finer than kHz. But as the MW source can, there will be a missmatch if we do not round here.

        try:
            storedvalues = np.loadtxt(os.path.join(qkit.cfg.get('datadir'), "IQMixer\\%s.cal" % self.mixer_name))
            NeedForInterpolation = False
            left_border = -np.inf
            right_border = np.inf
            if len(
                    storedvalues.shape) == 1:  # check dimensionality -> otherwise you will have problems if there is only one line in calibration file.
                storedvalues = [storedvalues]
            for index, t in enumerate(storedvalues):
                if t[0] == self._sideband_frequency and t[1] == self._sideband_frequency - self._iq_frequency and t[
                    2] == self._mw_power:
                    if time.time() - t[3] > self.maxage or recalibrate:  # Calibration is too old
                        print("recalibrating because calibration is too old (%.2f days ago)" % (
                            (time.time() - t[3]) / 24 / 3600))
                        return self.recalibrate(t[4], t[5], t[6], t[7], t[8], t[9], t[10])
                    else:
                        # print "returning known values"
                        return t
                    break
                if np.abs(t[0] - self._sideband_frequency) <= self.interpol_freqspan and t[
                    0] - self._sideband_frequency <= 0:
                    if left_border == -np.inf:
                        left_border = index
                        NeedForInterpolation = True
                    elif storedvalues[left_border][0] < t[0]:
                        left_border = index
                    elif np.abs(storedvalues[left_border][2] - self._mw_power) > np.abs(self._mw_power - t[2]):
                        left_border = index
                if np.abs(t[0] - self._sideband_frequency) <= self.interpol_freqspan and t[
                    0] - self._sideband_frequency >= 0:
                    if right_border == np.inf:
                        right_border = index
                        NeedForInterpolation = True
                    elif storedvalues[right_border][0] > t[0]:
                        right_border = index
                    elif np.abs(storedvalues[right_border][2] - self._mw_power) > np.abs(self._mw_power - t[2]):
                        right_border = index
            if NeedForInterpolation:
                if left_border == -np.inf:  # Within interpol_freqspan, only higher calibrated frequencies could be found
                    print("initial calibration for this frequency required, because only higher frequencies are calibrated yet.")
                    self._f_rounded = np.floor(self._sideband_frequency / 1e4) * 1e4 - 100e6
                    return self.initial_calibrate
                if right_border == +np.inf:  # same for lower frequencies
                    print("initial calibration for this frequency required, because only lower frequencies are calibrated yet.")
                    self._f_rounded = np.ceil(self._sideband_frequency / 1e4) * 1e4 + 100e6
                    return self.initial_calibrate
                if (left_border == right_border):
                    print("Same frequency for different powers found")
                    return self.recalibrate(storedvalues[left_border][4], storedvalues[left_border][5],
                                            storedvalues[left_border][6], storedvalues[left_border][7],
                                            storedvalues[left_border][8], storedvalues[left_border][9],
                                            storedvalues[left_border][10])
                interpolated = storedvalues[left_border] + (storedvalues[right_border] - storedvalues[left_border]) * (
                            self._sideband_frequency - storedvalues[left_border][0]) / (
                                           storedvalues[right_border][0] - storedvalues[left_border][0])
                if (storedvalues[right_border][0] - storedvalues[left_border][
                    0]) <= self.trust_region:  # No need for recalibration
                    if recalibrate:  # Except if we enforce a recalibration
                        return self.recalibrate(interpolated[4], interpolated[5], interpolated[6], interpolated[7],
                                                interpolated[8], interpolated[9], interpolated[10])
                    # print "using interpolated values"
                    return interpolated
                else:
                    print("recalibrate interpolated values")
                    if storedvalues[right_border][0] - self._sideband_frequency > self._sideband_frequency - \
                            storedvalues[left_border][0]:  # sideband_frequency is closer to left border
                        self._f_rounded = np.ceil(self._sideband_frequency / 1e3) * 1e3
                    else:
                        self._f_rounded = np.floor(self._sideband_frequency / 1e3) * 1e3
                    return self.recalibrate(interpolated[4], interpolated[5], interpolated[6], interpolated[7],
                                            interpolated[8], interpolated[9], interpolated[10])
            else:
                print("initial calibration for this frequency required. Think about using the interpol_freqspan option!")
                return self.initial_calibrate()

        except IOError:
            # Mixer has not at all been calibrated before
            # print "initial calibration required"
            # (sideband_frequency,mw_freq,mw_power,time.time(),dcx,dcy,x,y,phaseoffset,relamp,relamp2)
            return (
            self._sample.f01, self._sample.f01 - self._sample.iq_frequency, self._sample.mw_power, 0, 0, 0, 0, 0, np.pi,
            1., 1., -99, -99, -99, -99, -99)
            if self._sideband_frequency != np.round(self._sideband_frequency,
                                                    -3):  # If we only calibrate the rounded frequency, we will get problems later, because there is nothing to interpolate against
                self._f_rounded = np.floor(self._sideband_frequency / 1e3) * 1e3
                dcx, dcy, x, y, phaseoffset, relamp, relamp2 = self.initial_calibrate[4:11]
                self._f_rounded = np.ceil(self._sideband_frequency / 1e3) * 1e3
            return self.recalibrate(dcx, dcy, x, y, phaseoffset, relamp, relamp2)

    def get_calibration(self):
        if self.cache_valid and self.cache_frequency == self._sample.f01 and self.cache_power == self._sample.mw_power and self.cache_iq == self._sample.iq_frequency:
            return self.cache
        else:
            self.cache_frequency = self._sample.f01
            self.cache_power = self._sample.mw_power
            self.cache_iq = self._sample.iq_frequency
            self.cache = self.calibrate(recalibrate=False)
            self.cache_valid = True
            return self.cache

    def convert(self, wfm):
        '''
           wfm is an 1D array of complex values with absolute values <=1,
           where complex phase represents the phase of the later microwave
           Example: With an iq frequency of 100MHz and a samplerate of 6GS/s you have 
           60 Samples per wave, corresponding to 6degree phase resolution
           
        '''
        params = self.get_calibration()

        # content of params:(sideband_frequency,mw_freq,mw_power,time.time(),dcx,dcy,x,y,phaseoffset,relamp,relamp2),optimized
        # self.do_set_sideband_frequency(params[0])
        # self._output_power = params[15]
        # self.do_set_iq_frequency(self._sample.iq_frequency) #This is unnecessary, because it's done in calibrate()
        # self.get_all()
        dcx, dcy, x, y, phaseoffset, relamp, relamp2 = params[4:11]
        if self._iq_frequency == 0: x, y, phaseoffset, relamp, relamp2 = 0., 0., 0., 1., 1.  # homodyne
        t = np.arange(len(wfm)) / self._sample.clock
        # Relamp is Peak-to-Peak
        relamp, relamp2 = relamp / 2, relamp2 / 2
        angle = np.angle(wfm)
        wfm1 = dcx + np.abs(wfm) * (
                    relamp * self.ch1(2 * np.pi * self._iq_frequency * t + angle + phaseoffset) - dcx + x)
        wfm2 = dcy + np.abs(wfm) * (relamp2 * self.ch2(2 * np.pi * self._iq_frequency * t + angle) - dcy + y)
        del dcx, dcy, x, y, phaseoffset, relamp, relamp2, t, angle
        gc.collect()
        return (wfm1, wfm2)
