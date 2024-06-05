''' ADwin driver for the Spin-Transistor measurement. The idea is to
    view the Adwin as a highly configurable measurement device (since it
    is a programmable fpga with different hardware configurations it
    will always be specially programmed to do certain tasks efficiently)
    Here we look at the Adwin in symbiosis with its current sources,
    voltage dividers and iv_converters, so that we just want to tell it 
    what physical quantities we want to measure or apply (B-Fields, 
    voltages, currents ...) Therefore the driver includes two parts:
    AdwinIO which handles the translation between physical quantities
    and BITS. The insturment driver itself only applies and measures bit
    values and gives the ability to perform sweeps and dc/lockin readout
    
    ToDO:   * Explain modes of this driver
            * Sanity checky for sweep parameters e.g.

    * make sure that the lockin fifo is always cleared at the end of a
      sweep, that it doesn't have to be done in the beginnig (noise)
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
from qkit.drivers.adwinlib.io_handler import AdwinLimitError, AdwinArgumentError
from qkit.drivers.adwinlib.io_handler import AdwinNotImplementedError

# These constants have to be synchronised with the definitions of Par_no
# FPar_no and Data_no and constants in the ADbasic files.

# multiple files
DAC_ZERO = 32768    #dac
BIAS_PAR = 8
SWEEP_ACTIVE_PAR = 9
LOCKIN_ACTIVE_PAR = 10
LOCKIN_CHANNEL = 8
NO_OUTPUT_CHANNELS = 8
# only "sweep" file
DURATION_FPAR = 1
START_DATA = 3              # sweep_start data_no
STOP_DATA = 4               # sweep_stop data_no
# only "lockin" file
INPUT_CARD = 2
AMPLITUDE_PAR = 11
FREQUENCY_FPAR = 2
TAO_FPAR = 3
REPORT_FREQUENCY_FPAR = 4
FIFO_INPHASE = 1
FIFO_QUADRATURE = 2
FIFO_LENGTH = 1000003
MIN_FREQUENCY = 20
MAX_FREQUENCY = 40E3
SAMPLERATE_FPAR = 5
# only "sweep_DC_readout" file
LOCKIN_RATE = 500e3
FIFO_DC_READOUT = 1
FIFO_LEN_DC_RO = 1000003
STEPS_PAR = 10


class adwin_spin_transistor(Instrument):
    ''' ADwin driver to handle kHz lockin + readout while performing
        sweeps on the output. So far the T11 processor, 16-bit output
        card and 18-bit input card are supported. '''

    def __init__(self,
        name='my_instrument',
        processor='T11',
        mode='lockin', #lockin or dc
        devicenumber=1,
        bootload=True,
        start_wp=None,
        hard_config=None,
        soft_config=None):

        log.info('Initializing instrument in "%s" mode.', mode)
        Instrument.__init__(self, name, tags=['physical','ADwin_ProII'])

        self._mode = mode
        self._state = 'init'
        self._lockin_freq = None
        module_dir = Path(__file__).parent
        adbasic_dir = module_dir / 'adwinlib' / 'spin-transistor'
        self._lockin_process_no = 1
        self._lockin_process = adbasic_dir / 'Pro2_T11_lockin.TB1'
        self._sweep_process_no = 2
        self._sweep_process = adbasic_dir / 'Pro2_T11_sweep.TB2'
        self._dc_readout_process_no = 1
        self._dc_readout_process = adbasic_dir / 'Pro2_T11_sweep_DC_readout.TB1'

        # create AdwinIO Instance
        self.aio = AdwinIO(hard_config, soft_config)

        # create ADwin instance
        self.adw = adw.ADwin(DeviceNo=devicenumber,
                             raiseExceptions=1,
                             useNumpyArrays=True)

        # Set 'bootload' to 'False' to not reboot the Adwin.
        if bootload:
            # before boot try to read the current outputs, which can
            # fail if the adwin was power cycles and never booted since
            try:
                output_buffer = self.read_outputs(out_format='bit')
                print(output_buffer)
                self._state = 'output_buffer_loaded'
            except:
                self._state = 'output_buffer_unknown'
                log.critical('ADwin: outputs unknown! Booting.')
            # boot adwin
            btl_name = f"ADwin{processor.replace('T', '')}.btl"
            btl_path = Path(self.adw.ADwindir) / btl_name
            self.adw.Boot(str(btl_path))
            # set output buffer if possible, otherwise set all outputs
            # to zero volts
            if self._state == 'output_buffer_loaded':
                self.set_output_buffer(output_buffer, val_format='bit')
            elif self._state == 'output_buffer_unknown':
                outs_zero = [2**15] * NO_OUTPUT_CHANNELS
                self.set_output_buffer(outs_zero, val_format='bit')
                msg = ('Adwin: setting output buffer to zero! Recover '
                       + 'the current working Point by manually setting'
                       + ' the output buffer using set_output_buffer() '
                       + 'BEFORE THE FIRST SWEEP')
                log.critical(msg)
            # change state
            self._state = 'booted'

            # load processes
            if mode == 'lockin':
                log.info('Adwin loading: %s', self._lockin_process.name)
                self.adw.Load_Process(str(self._lockin_process))
                log.info('Adwin loading: %s', self._sweep_process.name)
                self.adw.Load_Process(str(self._sweep_process))
            elif mode == 'dc':
                log.info('Adwin loading: %s', self._dc_readout_process.name)
                self.adw.Load_Process(str(self._dc_readout_process))
            else:
                log.critical('%s: mode not supported.', __name__)

            # setup the start working point for the first sweep
            if isinstance(start_wp, (list, dict, np.ndarray)):
                start = self.aio.qty2bit(start_wp)
                self.adw.SetData_Long(start, START_DATA, 1, len(start))

        # implement general functions
        self.add_function("start_lockin")
        self.add_function("stop_lockin")
        self.add_function("read_outputs")
        self.add_function("start_sweep")
        self.add_function("stop_sweep")
        if mode == 'lockin':
            self.add_function("sweep_lockin_readout")
            self.add_function("lockin_noise_measurement")
        if mode == 'dc':
            ###################################################### DEBUG
            self.add_function("start_sweep_dc_readout")

    def start_lockin(self, amplitude, frequency, tao, sample_rate, bias=0):
        """ Sets the lockin parameters and starts the lockin process.
            From that time on the lockin signal is applied """
        if 'lockin' not in self._mode:
            raise AdwinModeError
        # check if parameters are supported
        if not MIN_FREQUENCY <= frequency <= MAX_FREQUENCY:
            raise AdwinLimitError
        # stop old lockin process (only applied if active)
        if self._state == 'lockin_running':
            self.adw.Stop_Process(self._lockin_process_no)
        # lockin bias to bits
        bias_bits = self.aio.qty2bit(bias, LOCKIN_CHANNEL)
        # lockin amplitude is relative not nezo not absolute DAC output.
        amp_bits = self.aio.qty2bit(amplitude, LOCKIN_CHANNEL, absolute=False)
        self.adw.Set_Par(BIAS_PAR, bias_bits)
        self.adw.Set_Par(AMPLITUDE_PAR, amp_bits)
        self.adw.Set_FPar(FREQUENCY_FPAR, frequency)
        self.adw.Set_FPar(TAO_FPAR, tao)
        self.adw.Set_FPar(SAMPLERATE_FPAR, sample_rate)
        # start lockin process
        log.info('Adwin starting: %s', self._lockin_process.name)
        self.adw.Start_Process(self._lockin_process_no)
        self._state = 'lockin_running'
        # get lockin (sample) frequency    
        self._lockin_freq = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)
        log.warning('Adwin lock-in frequency is %.2f Hz.',
                    self._lockin_freq)

    def sweep_lockin_readout(self, stop, duration):
        ''' Start a sweep while measuring with lockin with minimal 
            communication between adwin-PC (buffering the measurement
            in fifo). The sample rate is determined by the lockin
            process which needs to be already running. '''
        # lockin must already be running
        if self._state != 'lockin_running':
            log.critical('ADwin: Lockin must be running for readout.Abort')
            raise AdwinModeError
        # set sweep parameters
        self.adw.Set_FPar(DURATION_FPAR, duration)
        stop_bits = self.aio.qty2bit(stop)
        self.adw.SetData_Long(stop_bits, STOP_DATA, 1, len(stop_bits))
        log.info('Adwin starting %.1f second sweep with readout.', duration)
        # initialize process
        self.adw.Start_Process(self._sweep_process_no)
        # start process after small delay to wait for init to calm down
        sleep(0.05)
        self.adw.Set_Par(9, 2)
        sleep(duration)
        # check if sweep has ended
        while self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        # fetch all data from fifo (both should have the same samples)
        samples = self.adw.Fifo_Full(FIFO_INPHASE)
        inph = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
        quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
        inph = self.aio.bit2qty(inph, channel='readout', absolute=False)
        quad = self.aio.bit2qty(quad, channel='readout', absolute=False)
        print(type(inph[0]))
        return inph, quad

    def lockin_noise_measurement(self, duration):
        ''' Measure DC input for duration with full 500kHz sample rate
            for duration seconds. If no lockin should be applied, start
            lockin process with amplitude zero. Amount of collectable
            data is limited by fifo buffer length. '''
        # lockin must already be running
        if self._state != 'lockin_running':
            log.critical('ADwin: Lockin must be running for readout.Abort')
            raise AdwinModeError
        if duration > (FIFO_LENGTH / LOCKIN_RATE):
            log.warning('ADwin: Fifo holds values for max %s seconds.',
                        FIFO_LENGTH / LOCKIN_RATE)
        # enable data aquisition of lockin_input at max rate
        self.adw.Set_Par(9, 3)
        sleep(duration)
        # disable data aquisition of lockin_input at max rate
        self.adw.Set_Par(9, 0)
        # fetch all data from fifo (both should have the same samples)
        samples = self.adw.Fifo_Full(FIFO_INPHASE)
        lockin = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
        lockout = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
        lockin = self.aio.bit2qty(lockin, channel='readout', absolute=False)
        lockout = self.aio.bit2qty(lockout, channel='vd', absolute=True)
        return lockin, lockout

    def stop_lockin(self):
        """ Stops the lockin process. No lockin signal is applied and no
            readout is triggered by a sweep anymore. """
        if 'lockin' not in self._mode:
            raise AdwinModeError
        if self._state != 'lockin_running':
            log.warning('ADwin: Lockin not running? Stopping anyway.')
        log.info('Adwin stopping: %s', self._lockin_process.name)
        self.adw.Stop_Process(self._lockin_process_no)

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
                outs = np.empty(NO_OUTPUT_CHANNELS)
                outs.fill(np.NaN)
                for i, _ in enumerate(outs):
                    val =  self.adw.Get_Par(i+1)
                    if out_format == 'qty':
                        outs[i] = self.aio.bit2qty(val, i+1, True)
                    elif out_format == 'bit':
                        outs[i] = val
                    else:
                        raise AdwinArgumentError
                return outs
            case _:
                raise AdwinArgumentError

    def start_sweep(self, stop, duration, wait=False):
        """ Send the target values of the sweep to the PC and start the 
            sweep process. If wait==True it waits for the sweep to be
            finished. """
        # set sweep parameters
        self.adw.Set_FPar(DURATION_FPAR, duration)
        # transform stop array/workin_point to bit list
        stop = self.aio.qty2bit(stop)
        self.adw.SetData_Long(stop, STOP_DATA, 1, len(stop))
        self.adw.Start_Process(self._sweep_process_no)
        log.info('Adwin started %.1f second sweep.', duration)
        while wait is True and self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        if wait is True:
            log.info('Adwin finished sweep.')
        else:
            log.info('Adwin sweeping untracked by "start_sweep".')

    def stop_sweep(self):
        """ Stopping sweep process immediately """
        if self._mode in ['lockin', 'lockin_dc_readout']:
            log.info('Adwin stopping: %s', self._sweep_process.name)
            self.adw.Stop_Process(self._sweep_process_no)
        elif self._mode == 'dc':
            log.info('Adwin stopping: %s', self._dc_readout_process.name)
            self.adw.Stop_Process(self._dc_readout_process_no)

    def set_output_buffer(self, outs, val_format='qty'):
        ''' Set the buffer in which the Adwin saveds the current output
            values of the DAC's (Par_1 - Par_8 so far). This can be 
            useful after a reboot of the adwin in which the adwin can
            loose this information. '''
        match val_format:
            case 'qty', 'wp':
                outs = self.aio.qty2bit(outs)
            case 'bit':
                pass
            case _:
                raise AdwinArgumentError
        if len(outs) != NO_OUTPUT_CHANNELS:
            raise AdwinArgumentError
        for idx, val in outs:
            self.adw.Set_Par(idx+1, val)

    ########################################### DEBUG AND CHECK IF DOABLE BY LOCKIN NOW
    def start_sweep_dc_readout(self, stop, duration):
        """ Send the target values of the sweep to the PC and start the 
            sweep process. Then collect all the readout data """
        if self._mode != 'dc':
            raise AdwinModeError
        # start sweep
        self.start_sweep(stop, duration)
        # prepare readout
        expected_samples = self.adw.Get_Par(STEPS_PAR)
        readout = np.empty(expected_samples)
        readout.fill(np.NaN)
        recieved_samples = 0
        max_samples = 0
        # readout until all values are transmitted
        while recieved_samples < expected_samples:
            # minimal testing version without error handeling
            samples = self.adw.Fifo_Full(FIFO_DC_READOUT)
            if samples > 0:
                temp = self.adw.GetFifo_Float(FIFO_DC_READOUT, samples)
                for i in range(samples):
                    readout[recieved_samples + i] = temp[i]
            recieved_samples += samples
            # track the maximum transfered sample per cycle
            if samples > max_samples:
                max_samples = samples
        #calculate maximum utilization of the adwin fifo
        util = max_samples / FIFO_LEN_DC_RO * 100
        #log after readout
        log.info('Recieved %i samples @ maximum fifo utilization %.1f%%',
                 recieved_samples, util)
        return self.aio.bit2qty(readout, channel='readout', absolute=True)



if __name__ == '__main__':
    pass
