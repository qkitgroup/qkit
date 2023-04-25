# NI_DAQ.py, National Instruments Data Acquisition instrument driver
# Reinier Heeres <reinier@heeres.eu>, 2009
# Hannes Rotzinger, hannes.rotzinger@kit.edu 2010
# Micha Wildermuth, micha.wildermuth@kit.edu 2019
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# DAQ=qt.instruments.create('DAQ', 'NI_DAQ_IV',id='Dev1')
import qkit
from qkit.core.instrument_base import Instrument
import logging
import nidaq_syncIV as nidaq  # documentation see http://zone.ni.com/reference/en-XX/help/370471AM-01/
import numpy as np
import time


class NI_DAQ_IV(Instrument):
    """
    This is the driver for the National Instruments DAQs such as NI USB-6259 BNC.
    """

    def __init__(self, name, dev, reset=False):
        """
        Initializes VISA communication with the instrument Keithley 2636A.

        Parameters
        ----------
        name: string
            Name of the instrument (driver).
        dev: str
            Device identifier such as 'Dev1'
        reset: bool, optional
            Resets the instrument to default conditions. Default is False.

        Returns
        -------
        None

        Examples
        --------
        >>> import qkit
        QKIT configuration initialized -> available as qkit.cfg[...]

        >>> qkit.start()
        Starting QKIT framework ... -> qkit.core.startup
        Loading module ... S10_logging.py
        Loading module ... S12_lockfile.py
        Loading module ... S14_setup_directories.py
        Loading module ... S20_check_for_updates.py
        Loading module ... S25_info_service.py
        Loading module ... S30_qkit_start.py
        Loading module ... S65_load_RI_service.py
        Loading module ... S70_load_visa.py
        Loading module ... S80_load_file_service.py
        Loading module ... S85_init_measurement.py
        Loading module ... S98_started.py
        Loading module ... S99_init_user.py

        >>> DAQ = qkit.instruments.create('DAQ', 'NI_DAQ_IV', dev='Dev1', reset=True)
        Initialized the file info database (qkit.fid) in 0.000 seconds.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/mxcprop/func193b/
        self.__name__ = __name__
        # setup
        logging.info(__name__ + ': Initializing instrument NI DAQ')
        Instrument.__init__(self, name, tags=['physical'])
        if dev in nidaq.get_device_names():
            self._dev = dev
        else:
            raise ValueError('{:s}: Cannot find device {!s}'.format(self.__name__, id))
        self._plc = 50.
        self._input_channels = self._get_input_channels()
        self._output_channels = self._get_output_channels()
        self._chan_config = dict(zip(self._input_channels, ['DEFAULT']*len(self._input_channels)))
        self._bias_delay = dict(zip(self._output_channels, np.zeros_like(self._output_channels, dtype=float)))
        self._sense_delay = dict(zip(self._input_channels, np.zeros_like(self._input_channels, dtype=float)))
        self._sample_freq = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)*1e4))
        self._sense_average = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)))
        self._sense_nplc = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)*1e-2))
        self._bias_values = dict(zip(self._output_channels, np.zeros_like(self._output_channels, dtype=float)))
        self._sweep_channels = (0, 0)
        self.bias_data = None
        self.rate = None
        # reset
        if reset:
            self.reset()
        else:
            self.get_all()

    def write(self, data, channel, freq=1e4, minv=-10.0, maxv=10.0, timeout=10.0):
        """
        Writes analog output values <data> to output channel <channel> with sample frequency <freq>.

        Parameters
        ----------
        data: int/float/numpy.array
            Voltage data to write in Volts.
        channel: int
            Number of output channel of interest.
        freq: float
            Sample frequency in Hertz.
        minv: float
            Minimum voltage in Volts.
        maxv: float
            Maximum voltage in Volts.
        timeout: float
            Time to wait for completion in seconds.

        Returns
        -------
        written: int
            Number of values written
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcreatetask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxwriteanalogscalarf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcfgsampclktiming/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxwriteanalogf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstarttask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstoptask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcleartask/
        return nidaq.write(devchan='{:s}/ao{:d}'.format(self._dev, channel),
                           data=data,
                           freq=freq,
                           minv=minv,
                           maxv=maxv,
                           timeout=timeout)

    def read(self, channel, samples=1, freq=1e4, minv=-10.0, maxv=10.0, timeout=10.0):
        """
        Reads analog input values <data> of input channel <channel> with sample frequency <freq>.

        Parameters
        ----------
        channel: int
            Number of input channel of interest.
        samples: int
            Number of samples to read up to max_samples.
        freq: float
            Sample frequency in Hertz.
        minv: float
            Minimum voltage in Volts.
        maxv: float
            Maximum voltage in Volts.
        timeout: float
            Time to wait for completion in seconds.

        Returns
        -------
        data: float/numpy.array/None
            Read voltage data in Volts on success or None on error.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcreatetask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471W-01/daqmxcfunc/daqmxcreateaivoltagechan/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcfgsampclktiming/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstarttask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxreadanalogf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxreadanalogscalarf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstoptask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcleartask/
        return nidaq.read(devchan='{:s}/ai{:d}'.format(self._dev, channel),
                          samples=samples,
                          freq=freq,
                          minv=minv,
                          maxv=maxv,
                          timeout=timeout,
                          config=self._chan_config[channel])

    def _get_input_channels(self):
        """
        Gets all physical input channels of the device.

        Parameters
        ----------
        None

        Returns
        -------
        channels: list(str)
            Physical input channels.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/mxcprop/func231e/
        return np.array(list(map(lambda x: x.split('ai')[-1], nidaq.get_physical_input_channels(self._dev))), dtype=int)

    def _get_output_channels(self):
        """
        Gets all physical output channels of the device.

        Parameters
        ----------
        None

        Returns
        -------
        channels: list(str)
            Physical output channels.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/mxcprop/func231f/
        return np.array(list(map(lambda x: x.split('ao')[-1], nidaq.get_physical_output_channels(self._dev))), dtype=int)

    def _get_counter_channels(self):
        """
        Gets all physical counter channels of the device.

        Parameters
        ----------
        None

        Returns
        -------
        channels: list(str)
            Physical counter channels.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/mxcprop/func2324/
        return np.array(list(map(lambda x: x.split('ctr')[-1], nidaq.get_physical_counter_channels(self._dev))), dtype=int)

    def set_channel_config(self, val, channel):
        """
        Sets the channel configuration of channel <channel> to the mode <val>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).
        val: str
            Analog input channel configuration. Possible values are
              * 'DEFAULT',
              * 'RSE' (Referenced single-ended mode),
              * 'NRSE' (Non-referenced single-ended mode),
              * 'Diff' (Differential mode),
              * 'PseudoDiff' (Pseudodifferential mode)

        Returns
        -------
        None
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471W-01/daqmxcfunc/daqmxcreateaivoltagechan/
        self._chan_config[channel] = val.upper()

    def get_channel_config(self, channel):
        """
        Gets the channel configuration of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).

        Returns
        -------
        val: str
            Analog input channel configuration. Possible values are
              * 'DEFAULT',
              * 'RSE' (Referenced single-ended mode),
              * 'NRSE' (Non-referenced single-ended mode),
              * 'Diff' (Differential mode),
              * 'PseudoDiff' (Pseudodifferential mode)
        """
        return self._chan_config[channel]

    ####################################################################################################################
    ### functions needed for transport.py and virtual_tunnel_electronics.py                                          ###
    ####################################################################################################################

    def get_measurement_mode(self, channel=0):
        """
        This is a dummy function and is always 1 (4-wire). This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        return 1  # 4-wire

    def get_bias_mode(self, channel=0):
        """
        This is a dummy function and is always 1 (voltage). This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        return 1  # voltage bias

    def get_sense_mode(self, channel=0):
        """
        This is a dummy function and is always 1 (voltage). This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        return 1  # voltage bias

    def get_bias_range(self, channel=0):
        """
        This is a dummy function and is always -1 ('auto'). This DAQ provides only the range -10V .. +10V.
        """
        return -1  # 10V

    def get_sense_range(self, channel=0):
        """
        This is a dummy function and is always -1 ('auto'). This DAQ provides only the range -10V .. +10V.
        """
        return -1  # 10V

    def get_bias_delay(self, channel=0):
        """
        This is a dummy function and is always 0. This DAQ samples continuously and provides no delay.
        """
        return 0

    def get_sense_delay(self, channel=0):
        """
        This is a dummy function and is always 0. This DAQ samples continuously and provides no delay.
        """
        return 0

    def set_sense_average(self, val, channel=0):
        """
        Sets sense average of channel <channel> to <val>.

        Parameters
        ----------
        val: int
            Number of measured readings that are required to yield one filtered measurement.
        channel: int
            Number of channel of interest. Default is 0 (ai0).

        Returns
        -------
        None
        """
        self._sense_average[channel] = int(val)

    def get_sense_average(self, channel=0):
        """
        Gets sense average status <status>, value <val> and mode <mode> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).

        Returns
        -------
        val: int
            Number of measured readings that are required to yield one filtered measurement.
        """
        return self._sense_average[channel]

    def set_plc(self, val):
        """
        Sets power line cycle (PLC) to <val>.

        Parameters
        ----------
        val: int
            Power line frequency setting used for NPLC calculations. 50 | 60.

        Returns
        -------
        None
        """
        self._plc = val

    def get_plc(self):
        """
        Gets power line cycle (PLC) <plc>.

        Parameters
        ----------
        None

        Returns
        -------
        plc: int
            Power line frequency setting used for NPLC calculations.
        """
        return self._plc

    def set_sense_nplc(self, val, sample_freq=None, channel=0):
        """
        Sets sense nplc (number of power line cycle) of channel <channel> with the <val>-fold of one power line cycle. Note that the sample frequency needs to be >= plc/nplc.
        The integral of sampled data is calculated by menas of numpy.trapz, which approximates the integral by trapezoidal rule (https://en.wikipedia.org/wiki/Trapezoidal_rule)

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).
        val: float
            Integration aperture for measurements.
        sample_freq: float
            Sample frequency. Default is None (previous settings).

        Returns
        -------
        None
        """
        if sample_freq:
            self._sample_freq[channel] = sample_freq
        self._sense_nplc[channel] = val
        if not int(self._sample_freq[channel] / self._plc * self._sense_nplc[channel]):
            logging.warning('Measurement time will increase, since samples will be set to 1. Samples ( = sample_freq / plc * nplc) must be >= 1. Check the sampling frequency and nplc settings.')

    def get_sense_nplc(self, channel=0):
        """
        Gets sense nplc (number of power line cycle) <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).

        Returns
        -------
        val: float
            Integration aperture for measurements.
        """
        return self._sense_nplc[channel]

    def set_sample_freq(self, val, channel=0):
        """
        Sets sample frequency of input channel <channel> to <val>.

        Parameters
        ----------
        channel: int
            Number of input channel of interest. Default is 0 (ai0).
        val: float
            Sample frequency. Default is None (previous settings).

        Returns
        -------
        None
        """
        self._sample_freq[channel] = val

    def get_sample_freq(self, channel=0):
        """
        Gets sample frequency of input channel <channel>.

        Parameters
        ----------
        channel: int
            Number of input channel of interest. Default is 0 (ai0).

        Returns
        -------
        val: float
            Sample frequency. Default is None (previous settings).
        """
        return self._sample_freq[channel]

    def set_bias_value(self, val, channel=0):
        """
        Sets bias value of channel <channel> to value <val>.

        Parameters
        ----------
        val: float
            Bias value.
        channel: int
            Number of channel of interest. Default is 0 (ao0).

        Returns
        -------
        None
        """
        self._bias_values[channel] = val
        nidaq.write(devchan='{:s}/ao{:d}'.format(self._dev, channel), data=val)

    def get_bias_value(self, channel=0):
        """
        Gets bias value <val> of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ao0).

        Returns
        -------
        val: float
            Bias value.
        """
        # TODO: read back bias value (https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000kGDISA2&l=de-DE)
        # TODO: than use bias_delay
        return self._bias_values[channel]

    def get_sense_value(self, sample_freq=None, channel=0):
        """
        Gets sense value of channel <channel>.
        
        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0 (ai0).
        
        Returns
        -------
        val: float
            Sense value.
        """
        if sample_freq:
            self._sample_freq[channel] = sample_freq
        samples = int(self._sample_freq[channel] / self._plc * self._sense_nplc[channel])
        if not samples:
            samples = 1
        data = list(map(lambda i: nidaq.read(devchan='{:s}/ai{:d}'.format(self._dev, channel),
                                             samples=samples,
                                             freq=self._sample_freq[channel],
                                             config=self._chan_config[channel]),
                        range(int(self._sense_average[channel]))))
        return np.mean(np.trapz(data, dx=1./(samples-1)))

    def set_status(self, status, channel=0):
        """
        Sets output status of channel <channel> to <status>.
        This is a dummy function. The output cannot be turned off, so that False equals 0V.

        Parameters
        ----------
        status: int
            Output status.
        channel: int
            Number of channel of interest. Default is 0 (ao0).

        Returns
        -------
        None
        """
        if not status:
            self.set_bias_value(val=0, channel=channel)

    def set_sweep_channels(self, *channels):
        """
        Sets channels <channels> that are used during sweeps.

        Parameters
        ----------
        channels: int or tuple(int)
            Number of channel of usage. The 1st argument is the bias channel and the 2nd argument the sense channel.

        Returns
        -------
        None
        """
        self._sweep_channels = channels

    def get_sweep_channels(self):
        """
        Gets channels <channels> that are used during sweeps.

        Parameters
        ----------
        None

        Returns
        -------
        channels: int or tuple(int)
            Number of channel of usage. The 1st argument is the bias channel and the 2nd argument the sense channel.
        """
        return self._sweep_channels

    def get_sweep_bias(self):
        """
        This is a dummy function and is always 1 (voltage). This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        return 1  # voltage

    def set_sweep_mode(self, *args, **kwargs):
        """
        This is a dummy function and just passes. This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        pass

    def get_sweep_mode(self):
        """
        This is a dummy function and is always 0 (VV-mode). This DAQ can only source and measure voltages and currents by means of tunnel electronics.
        """
        return 0  # (VV-mode)

    def set_sweep_parameters(self, sweep):
        """
        Sets sweep parameters <sweep>.

        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using qkit.measure.transport.transport.sweep class)

        Returns
        -------
        None
        """
        start = float(sweep[0])
        stop = float(sweep[1])
        step = float(sweep[2])
        self.nop = int(round(abs((stop-start)/step)+1))
        self.bias_data = np.linspace(start, np.sign(stop-start)*(np.floor(np.abs(np.round(float(stop-start)/step)))*step)+start, self.nop)  # stop is rounded down to multiples of step
        self.rate = self._plc/self._sense_nplc[self.get_sweep_channels()[1]]
        self.set_bias_value(start)
        time.sleep(1./self.rate)

    def get_tracedata(self):
        """
        Starts bias sweep with already set parameters and gets trace data of bias <bias_values> and sense <sense_values> in the set sweep mode.
        Note that this function sweeps the bias permanently, reads synchronized with a 10fold sampling rate and averages this 10 samples
        The sweep rate is calculated from plc and nplc, while averages are ignored.

        Parameters
        ----------
        None

        Returns
        -------
        bias_values: numpy.array(float)
            Measured bias values.
        sense_values: numpy.array(float)
            Measured sense values.
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/mxcprop/func2986/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcreatetask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471W-01/daqmxcfunc/daqmxcreateaivoltagechan/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcfgsampclktiming/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcreateaovoltagechan/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcfgdigedgestarttrig/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxwriteanalogf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstarttask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxwaituntiltaskdone/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxreadanalogf64/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxstoptask/
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxcleartask/
        output_channel, input_channel = [''.join(i).strip() for i in zip(*np.array([[self._dev] * 2,
                                                                                    ['/ao', '/ai'],
                                                                                    self.get_sweep_channels()]))]
        sense_data = nidaq.sync_write_read(O_devchan=output_channel,  # device / bias channel
                                           I_devchan=input_channel,  # device / sense channel
                                           waveform=self.bias_data,  # bias data
                                           rate=self.rate,  # sweep rate
                                           timeout=self.nop/self.rate*1.1,  # 1.1 fold of the calculated measurement time, just to be on the safe side
                                           config=self._chan_config[self.get_sweep_channels()[1]])  # sense channel configuration
        return self.bias_data, sense_data

    def take_IV(self, sweep):
        """
        Takes IV curve with sweep parameters <sweep>.

        Parameters
        ----------
        sweep: array_likes of floats
            Sweep range containing start, stop and step size (e.g. sweep object using qkit.measure.transport.transport.sweep class)

        Returns
        -------
        bias_values: numpy.array(float)
            Bias values.
        sense_values: numpy.array(float)
            Measured sense values.
        """
        self.set_sweep_parameters(sweep=sweep)
        return self.get_tracedata()

    def reset(self):
        """
        Resets the instrument to default conditions.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # Corresponding command: http://zone.ni.com/reference/en-XX/help/370471AM-01/daqmxcfunc/daqmxresetdevice/
        nidaq.reset_device(self._dev)

    def set_defaults(self):
        """
        Sets default settings.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.reset()
        self._plc = 50.
        self._chan_config = dict(zip(self._input_channels, ['DEFAULT']*len(self._input_channels)))
        self._bias_delay = dict(zip(self._output_channels, np.zeros_like(self._output_channels, dtype=float)))
        self._sense_delay = dict(zip(self._input_channels, np.zeros_like(self._input_channels, dtype=float)))
        self._sample_freq = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)*1e4))
        self._sense_average = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)))
        self._sense_nplc = dict(zip(self._input_channels, np.ones_like(self._input_channels, dtype=float)*1e-2))
        self._bias_values = dict(zip(self._output_channels, np.zeros_like(self._output_channels, dtype=float)))
        self._bias_values = None
        self.rate = None
        self._sweep_channels = (0, 0)

    def get_all(self, channel=0):
        """
        Prints all settings of channel <channel>.

        Parameters
        ----------
        channel: int
            Number of channel of interest. Default is 0.

        Returns
        -------
        None
        """
        logging.debug('{:s}: Get all'.format(__name__))
        print('output channels  = {!s}'.format(self._output_channels))
        print('input channels   = {!s}'.format(self._input_channels))
        print('channel config   = {!s}'.format(self._chan_config[channel]))
        print('sample frequency = {:g}'.format(self._sample_freq[channel]))
        print('sense average      = {:f}'.format(self.get_sense_average(channel=channel)))
        print('plc                = {:g}Hz'.format(self.get_plc()))
        print('sense nplc         = {:g}'.format(self.get_sense_nplc(channel=channel)))
        print('bias value         = {:g}V'.format(self.get_bias_value(channel=channel)))
        print('sense value        = {:g}V'.format(self.get_sense_value(channel=channel)))
        return

    def get_parameters(self):
        """
        Gets a parameter list <parlist> of measurement specific setting parameters.
        Needed for .set-file in 'write_additional_files', if qt parameters are not used.

        Parameters
        ----------
        None

        Returns
        -------
        parlist: dict
            Parameter names as keys, corresponding channels of interest as values.
        """
        parlist = {'channel_config': self._input_channels,
                   #'bias_delay': self._output_channels,
                   #'sense_delay': self._input_channels,
                   'sample_freq': self._input_channels,
                   'sense_average': self._input_channels,
                   'sense_nplc': self._input_channels,
                   'bias_value': self._output_channels,
                  }
        return parlist

    def get(self, param, **kwargs):
        """
        Gets the current parameter <param> by evaluation 'get_'+<param> and corresponding channel if needed
        In combination with <self.get_parameters> above.

        Parameters
        ----------
        param: str
            Parameter of interest.
        channels: array_likes
            Number of channels of interest. Can be a list for channel specific parameters or None for channel independent (global) parameters.

        Returns
        -------
        parlist: dict
            Parameter names as keys, values of corresponding channels as values.
        """
        channels = kwargs.get('channels')
        if channels is [None]:
            return tuple(eval('map(lambda channel, self=self: self.get_{:s}(), [None])'.format(param)))
            #return eval('self.get_{:s}()'.format(param))
        else:
            return tuple(eval('map(lambda channel, self=self: self.get_{:s}(channel=channel), [{:s}])'.format(param, ', '.join(map(str, channels)))))
            #return tuple([eval('self.get_{:s}(channel={!s})'.format(param, channel)) for channel in channels])
