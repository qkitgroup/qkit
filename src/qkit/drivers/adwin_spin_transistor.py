''' ADwin driver for the Spin-Transistor measurement. The idea is to
    view the Adwin as a highly configurable measurement device (since it
    is a programmable fpga with different hardware configurations it
    will always be specially programmed to do certain tasks efficiently)
    Here we view the Adwin as a unit together with its peripherals, like
    current sources, voltage dividers, iv_converters, filters, coils, ..
    We just want to tell it what physical quantities we want to measure 
    or apply at the sample (B-Fields, voltages, currents ...)
    Therefore the driver includes two parts:
        * AdwinIO which handles the translation between physical
          quantities and BITS.
        * The insturment driver (adwin_spin_transistor) itself only
          containes the measurement functions using bit values for the 
          DAC/ADC.
    
    So far, all measurements consist of a sweep process and a lockin
    process:
        * The lockin process can apply a sine wave at a hard coded adwin
          output and performs the measurement of the input with 500kHz
          sample_rate. It contains the lockin demodulation with low pass
          filter and can send subsampled data to the PC (depending on 
          the filter constant of the filters it does not make sense to
          use a to high data rate). The same process can also be used to
          measure the raw input of the ADC with full 500kHz or
          subsampled to a smaller sample_rate.
        * The sweep process can perform a linear sweep of the adwin
          outputs in a certain time. As soon as the sweep starts, it
          triggers the lockin process.
    
    Modes:
        * LOCKIN: After initiliazing the ADwin the lockin process has to
          be started setting the desired lockin-parameters. Then the
          lockin will continously just without sending data to the PC.
          Therfore the filter parameters are always initialized.
          As soon as the "measurment_active" flag is set to "1", the
          lockin will write the values to the FIFO. Since communication
          between PC and Adwin does affect the measurement by
          introducing jitter and maybe more, it makes sense to fetch the
          data after the measurement is done, limiting  (sample_rate *
          measurement time) by the length of the FIFOs.
        * DC: Here we just want to use the lockin prcoess for data
          aquisition, therefore just set the amplitude of the lockin to
          zero to not apply a lockin signal.

    
    ToDO:   * Sanity checky for sweep parameters e.g.
            * Maybe programm the LP filter for dc measurements as well
    '''

__all__ = ['adwin_spin_transistor', 'AdwinIO']
__version__ = '0.1_20240514'
__author__ = 'Luca Kosche'

import logging as log
from pathlib import Path
from time import sleep
import numpy as np
import ADwin as adw
from qkit.core.instrument_base import Instrument
from qkit.drivers.adwinlib.io_handler import AdwinIO, AdwinModeError
from qkit.drivers.adwinlib.io_handler import AdwinLimitError
from qkit.drivers.adwinlib.io_handler import AdwinArgumentError
from qkit.drivers.adwinlib.io_handler import AdwinNotImplementedError

# These constants have to be synchronised with the definitions of Par_no
# FPar_no and Data_no and constants in the ADbasic files.

# BOTH PROCESSES
LOCKIN_ACTIVE_PAR = 21      # Reports "1" if lockin process is active
# LOCKIN PROCESS
LOCKIN_BIAS_PAR = 8         # Lockin bias voltage (bits)
MEASURE_ACTIVE_PAR = 22     # activate data aquisition with "1"
LOCKIN_OR_DC_PAR = 23   	# Measure lockin or raw dc input
AMPLITUDE_PAR = 24          # Lockin amplitude (bits)
TAO_FPAR = 23               # Time constant of lockin filter
FREQUENCY_FPAR = 22         # Target lockin frequency
REPORT_FREQUENCY_FPAR = 24  # Real lockin frequency due to lockin_array
SAMPLERATE_FPAR = 25        # Target sample rate
REPORT_SAMPLERATE_FPAR = 26 # Real samplerate due to 2us time resolution
FIFO_LEN = 1000003          # Length of Fifo for data transmittion
INS = {'inph': 1, 'quad': 2, 'raw': 3} #fifo numbers
LOCKIN_CARD = 3             # Hard coded DAC card for lockin output
LOCKIN_CHANNEL = 8          # Hard coded DAC channel for lockin output
LOCKIN_LEN = 8003           # Length of lockin output/reference arrays
# SWEEP PROCESS
SWEEP_ACTIVE_PAR = 20       # Active sweep by setting to "2" and check
                            # rate by looking for "1".
NB_OUTS = 8                 # number of Adwin outputs
DURATION_FPAR = 20          # Target duration of sweep
REPORT_DURATION_FPAR = 21   # Duration of sweep due to 50kHz resolution
TARGET_DATA = 20            # Target values of the next sweep.

# RESULTING FROM ADBASIC FILES
MIN_FREQUENCY = 62.48
MAX_FREQUENCY = 40E3 # too high frequency might suffer from jitter


class adwin_spin_transistor(Instrument):
    ''' ADwin driver to handle kHz lockin + readout while performing
        sweeps on the output. So far the T11 processor, 16-bit output
        card and 18-bit input card are supported. '''
    _instance = None  # class variable

    def __new__(cls, *args, **kwargs):
        # proves there will only be one instance of this class
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__initialized = False
        else:
            log.warning("Parameters of existing instance may be replaced!")
        return cls._instance

    def __del__(self):
        # Resetting the class variable when the instance is deleted
        type(self)._instance = None
        print("Instance deleted and _instance reseted")

    def __init__(self,
        name='my_instrument',
        processor='T11',
        mode='lockin', #lockin or dc
        devicenumber=1,
        bootload=True,
        hard_config=None,
        soft_config=None):

        log.info('Initializing instrument in "%s" mode.', mode)
        Instrument.__init__(self, name, tags=['physical','ADwin_ProII'])

        self._state = 'init'
        self._params = {'sample_rate': None,
                        'inputs': []}
        module_dir = Path(__file__).parent
        adbasic_dir = module_dir / 'adwinlib' / 'spin-transistor'
        self._lockin_process = adbasic_dir / 'Pro2_T11_lockin.TB1'
        self._lockin_process_no = 1
        self._sweep_process = adbasic_dir / 'Pro2_T11_sweep.TB2'
        self._sweep_process_no = 2

        # create AdwinIO Instance
        self.aio = AdwinIO(hard_config, soft_config)

        # create ADwin instance
        self.adw = adw.ADwin(DeviceNo=devicenumber,
                                raiseExceptions=1,
                                useNumpyArrays=True)

        # Set 'bootload' to 'False' to not reboot the Adwin.
        if bootload:
            # before boot try to read the current outputs, which can
            # fail if the adwin was power cycled and never booted since
            try:
                output_buffer = self.read_outputs(out_format='bit')
                self._state = 'output_buffer_loaded'
            except adw.ADwinError:
                self._state = 'output_buffer_unknown'
                log.critical('ADwin: outputs unknown! Booting.')
            #boot adwin
            btl_name = f"ADwin{processor.replace('T', '')}.btl"
            btl_path = Path(self.adw.ADwindir) / btl_name
            self.adw.Boot(str(btl_path))
            # set output buffer if possible, otherwise set all outputs
            # to zero volts
            if self._state == 'output_buffer_loaded':
                self.set_output_buffer(output_buffer, val_format='bit')
            else:
                outs_zero = [2**15] * NB_OUTS
                self.set_output_buffer(outs_zero, val_format='bit')
                msg = ('Adwin: setting output buffer to zero! Recover '
                        + 'the current working Point by manually setting'
                        + ' the output buffer using set_output_buffer() '
                        + 'BEFORE THE FIRST SWEEP')
                log.critical(msg)

            self._state = 'booted'

            # load processes
            log.info('Adwin loading: %s', self._lockin_process.name)
            self.adw.Load_Process(str(self._lockin_process))
            log.info('Adwin loading: %s', self._sweep_process.name)
            self.adw.Load_Process(str(self._sweep_process))

            self._state = 'processes_loaded'

        # implement general functions
        self.add_function("sweep")
        self.add_function("sweep_measure")
        self.add_function("measure")
        self.add_function("init_measurement")
        self.add_function("stop_measurement")
        self.add_function("read_outputs")
        self.add_function("stop_sweep")
        self.add_function("set_output_buffer")

########################################################################
####################### MEASUREMENT ROUTINES ###########################
########################################################################

    def sweep(self, target, duration, wait=True):
        """ Ramp the outputs of the ADwin wihtout measurement.
            If wait==True it waits for the sweep to be finished. """
        self._start_sweep(target, duration)
        while wait is True and self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        for i in INS.values():
            self.adw.Fifo_Clear(i)
        if wait is True:
            log.info('Adwin finished sweep.')
        else:
            log.info('Adwin sweeping with no idea, when it ends.')

    def sweep_measure(self, target, duration):
        ''' Start a sweep while measuring with lockin with minimal 
            communication between adwin-PC (buffering the measurement
            in fifo). The sample rate is determined by the lockin
            process which needs to be already running. '''
        # sanity checks
        self._check_measurement_active()
        self._warn_if_fifo_to_small(duration)
        # start sweep
        self._start_sweep(target, duration)
        # wait for sweep to be finished (this might not be the best
        # timing, but limits communication during measurement)
        sleep(duration)
        # check if sweep has ended
        while self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        # fetch measurement data from adwin and return
        return self._fetch_data_from_fifos()

    def measure(self, duration):
        ''' Measure DC input for duration with full 500kHz sample rate
            for duration seconds. If no lockin should be applied, start
            lockin process with amplitude zero. Amount of collectable
            data is limited by fifo buffer length. '''
        # sanity checks
        self._check_measurement_active()
        self._warn_if_fifo_to_small(duration)
        # enable data aquisition
        self.adw.Set_Par(MEASURE_ACTIVE_PAR, 1)
        sleep(duration)
        # disable data aquisition
        self.adw.Set_Par(MEASURE_ACTIVE_PAR, 0)
        # fetch measurement data from adwin and return
        return self._fetch_data_from_fifos()

    def _fetch_data_from_fifos(self):
        ''' Fetch all data from the fifos which has been set as inputs
            during init_measurement() and clear all other fifos '''
        res = {'inph': None, 'quad': None, 'raw': None}
        samples = self.adw.Fifo_Full(INS['inph'])
        for key in res:
            if key in self._params['inputs']:
                tmp = self.adw.GetFifo_Float(INS[key], samples)
                res[key] = self.aio.bit2qty(tmp, 'readout', False)
            else:
                self.adw.Fifo_Clear(INS[key])
        return res

########################################################################
########################## PREPARE MEASUREMENT #########################
########################################################################

    def init_measurement(self, mode, sample_rate, bias, inputs,
                         **kwargs):
        ''' Initialize a lockin or dc measurement (mode). This start 
            the process needed for data aquisition. In lockin mode it
            also applies the continous lockin signal. '''
        # stop old measurement process if still running
        if self._state == 'measurement_ready':
            self.adw.Stop_Process(self._lockin_process_no)
        # set sample rate
        self.adw.Set_FPar(SAMPLERATE_FPAR, sample_rate)
        # set bias voltage
        bias_bits = self.aio.qty2bit(bias, LOCKIN_CHANNEL)
        self.adw.Set_Par(LOCKIN_BIAS_PAR, bias_bits)
        # set inputs
        for inp in inputs:
            if inp not in INS:
                raise AdwinArgumentError
        self._params['inputs'] = inputs
        # handle measurement modes
        match mode:
            case 'lockin':
                try:
                    # get lockin frequency
                    freq = kwargs['frequency']
                    # check if frequency is supported
                    if not MIN_FREQUENCY <= freq <= MAX_FREQUENCY:
                        raise AdwinLimitError
                    self.adw.Set_FPar(FREQUENCY_FPAR, freq)
                    # get lockin amplitude
                    amp = kwargs['amplitude']
                    # translate to bit value
                    amp_bits = self.aio.qty2bit(amp, LOCKIN_CHANNEL,
                                                absolute=False)
                    self.adw.Set_Par(AMPLITUDE_PAR, amp_bits)
                    # get filter constant tao
                    tao = kwargs['tao']
                    self.adw.Set_FPar(TAO_FPAR, tao)
                except KeyError as exc:
                    raise AdwinArgumentError from exc
            case 'dc':
                # set 'fake' frequency (no effect with amplitude zero)
                self.adw.Set_FPar(FREQUENCY_FPAR, 62.5)
                # set zero amplitude
                self.adw.Set_Par(AMPLITUDE_PAR, 0)
                # set 'fake' tao
                self.adw.Set_FPar(TAO_FPAR, 1)
            case _:
                raise AdwinArgumentError

        # start lockin process
        log.info('Adwin starting: %s', self._lockin_process.name)
        self.adw.Start_Process(self._lockin_process_no)

        # get actual parameters
        sample_rate = self.adw.Get_FPar(REPORT_SAMPLERATE_FPAR)
        self._params['sample_rate'] = sample_rate
        # set measurement ready state
        self._state = 'measurement_ready'
        # handle logging for each mode
        match mode:
            case 'lockin':
                freq = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)
                log.warning('ADwin: lock-in: frequency = %s Hz. '
                            + 'amplitdue = %s V, tao = %s s, '
                            + 'sample_rate = %s', freq, amp, tao,
                            sample_rate)
            case 'dc':
                log.warning('ADwin dc measurement initialized with '
                            + 'sample_rate = %s', sample_rate)

    def stop_measurement(self):
        """ Stops the lockin process. No lockin signal is applied and no
            readout is triggered by a sweep anymore. """
        self._check_measurement_active()
        log.info('Adwin stopping: %s', self._lockin_process.name)
        self.adw.Stop_Process(self._lockin_process_no)
        self._state = 'processes_loaded'

########################################################################
########################## OTHER FUNCTIONS #############################
########################################################################

    def read_outputs(self, channel:int|str=None, out_format='qty'):
        """ Read the current saved output values of the ADwin. After a 
            restart this might not be the correct values. """
        # Read all adwin parameters holding the current output values
        match channel:
            case int():
                val = self.adw.Get_Par(channel)
                if out_format == 'qty':
                    return self.aio.bit2qty(val, channel, absolute=True)
                elif out_format == 'bit':
                    return val
                else:
                    raise AdwinArgumentError
            case str():
                raise AdwinNotImplementedError
            case None:
                if out_format == 'qty':
                    outs = np.empty(NB_OUTS)
                    outs.fill(np.NaN)
                    for i, _ in enumerate(outs):
                        val =  self.adw.Get_Par(i+1)
                        outs[i] = self.aio.bit2qty(val, i+1, True)
                elif out_format == 'bit':
                    outs = []
                    for i in range(NB_OUTS):
                        outs.append(self.adw.Get_Par(i+1))
                else:
                    raise AdwinArgumentError
                return outs
            case _:
                raise AdwinArgumentError

    def stop_sweep(self):
        """ Stopping sweep process immediately """
        log.info('Adwin stopping: %s', self._sweep_process.name)
        self.adw.Stop_Process(self._sweep_process_no)

    def set_output_buffer(self, outs, val_format='qty'):
        ''' Set the buffer in which the Adwin saveds the current output
            values of the DAC's (Par_1 - Par_8 so far). This can be 
            useful after a reboot of the adwin in which the adwin can
            loose this information. '''
        if val_format in ['qty', 'wp']:
            outs = self.aio.qty2bit(outs)
        if len(outs) != NB_OUTS:
            raise AdwinArgumentError
        for idx, val in enumerate(outs):
            self.adw.Set_Par(idx+1, int(val))

    def _start_sweep(self, target, duration, delay=0.05):
        # set sweep parameters
        self.adw.Set_FPar(DURATION_FPAR, duration)
        target_bits = self.aio.qty2bit(target)
        self.adw.SetData_Long(target_bits, TARGET_DATA, 1,
                              len(target_bits))
        log.info('Adwin starting %.1f second sweep.', duration)
        # initialize process
        self.adw.Start_Process(self._sweep_process_no)
        # start process after small delay to wait for init to calm down
        sleep(delay)
        self.adw.Set_Par(SWEEP_ACTIVE_PAR, 1)

    def _check_measurement_active(self):
        # just check the state of the adwin driver. It could be done by
        # reading the adwin's lockin_active par, but I want to limit
        # communication
        if self._state != 'measurement_ready':
            log.critical('ADwin: measurement not initialized. Abort! '
                         + 'Run init_measurement() first.')
            raise AdwinModeError

    def _warn_if_fifo_to_small(self, duration):
        if duration * self._params['sample_rate'] > FIFO_LEN:
            log.warning('ADwin: Fifo holds values for max %s seconds.',
            FIFO_LEN / self._params['sample_rate'])

if __name__ == '__main__':
    pass
