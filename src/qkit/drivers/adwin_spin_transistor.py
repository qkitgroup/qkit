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
from qkit.drivers.adwinlib.io_handler import AdwinLimitError, AdwinArgumentError
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
FIFO_INPHASE = 1            # Inphase Fifo number
FIFO_QUADRATURE = 2         # Quadrature Fifo number
LOCKIN_CARD = 3             # Hard coded DAC card for lockin output
LOCKIN_CHANNEL = 8          # Hard coded DAC channel for lockin output
LOCKIN_LEN = 8003           # Length of lockin output/reference arrays
# SWEEP PROCESS
SWEEP_ACTIVE_PAR = 20       # Active sweep by setting to "2" and check
                            # rate by looking for "1".
NB_OUTS = 8                 # number of Adwin outputs
DURATION_FPAR = 20          # Target duration of sweep
REPORT_DURATION_FPAR = 21   # Real duration of sweep due to 2us resolution
TARGET_DATA = 20            # Target values of the next sweep.

# RESULTING FROM ADBASIC FILES
MIN_FREQUENCY = 62.48
MAX_FREQUENCY = 40E3 # too high frequency might suffer from jitter


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
        hard_config=None,
        soft_config=None):

        log.info('Initializing instrument in "%s" mode.', mode)
        Instrument.__init__(self, name, tags=['physical','ADwin_ProII'])

        self._state = 'init'
        self._params = {'freq': None, 'sample_rate': None}
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

            self._state = 'processes loaded'

        # implement general functions
        self.add_function("start_lockin")
        self.add_function("start_dc")
        self.add_function("stop_lockin")
        self.add_function("read_outputs")
        self.add_function("ramp_outputs")
        self.add_function("stop_sweep")
        self.add_function("set_output_buffer")
        # perform sweep while applying lockin signal and demodulation
        self.add_function("sweep_lockin_readout")
        # perfprm sweep while applying lockin signal but measuring
        # the raw dc input (to measure noise in real world example)
        self.add_function("sweep_lockin_dc_readout")
        # apply lockin signal, but measre raw dc input without sweep
        # for noise analysis
        self.add_function("lockin_dc_readout")
        # perform sweep without applying lockin signal and measure raw
        # dc input
        self.add_function("sweep_dc_readout")

    def start_lockin(self, amplitude, frequency, tao, sample_rate, bias=0):
        """ Sets the lockin parameters and starts the lockin process.
            From that time on the lockin signal is applied """
        # check if parameters are supported
        if not MIN_FREQUENCY <= frequency <= MAX_FREQUENCY:
            raise AdwinLimitError
        # stop old lockin process (only applied if active)
        if self._state in ['lockin_running', 'lockin_bypassed']:
            self.adw.Stop_Process(self._lockin_process_no)
        # lockin bias to bits
        bias_bits = self.aio.qty2bit(bias, LOCKIN_CHANNEL)
        # lockin amplitude is relative not nezo not absolute DAC output.
        amp_bits = self.aio.qty2bit(amplitude, LOCKIN_CHANNEL, absolute=False)
        self.adw.Set_Par(LOCKIN_BIAS_PAR, bias_bits)
        self.adw.Set_Par(AMPLITUDE_PAR, amp_bits)
        self.adw.Set_FPar(FREQUENCY_FPAR, frequency)
        self.adw.Set_FPar(TAO_FPAR, tao)
        self.adw.Set_FPar(SAMPLERATE_FPAR, sample_rate)
        self.adw.Set_Par(LOCKIN_OR_DC_PAR, 1)
        # start lockin process
        log.info('Adwin starting: %s', self._lockin_process.name)
        self.adw.Start_Process(self._lockin_process_no)
        # get actual parameters
        self._params['sample_rate'] = self.adw.Get_FPar(REPORT_SAMPLERATE_FPAR)
        self._params['freq'] = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)

        self._state = 'lockin_running'

        log.warning('ADwin: lock-in: frequency = %s Hz. amplitdue = '
                    + '%s V, tao = %s s, sample_rate = %s',
                    self._params['freq'], amplitude, tao,
                    self._params['sample_rate'])

    def start_dc(self, sample_rate, bias=0):
        """ Prepare the dc measurement by settin sample rate and start
            bias voltage """
        self.start_lockin(0, 62.5, 0.01, sample_rate, bias)
        self.adw.Set_Par(LOCKIN_OR_DC_PAR, 0)
        log.warning('ADwin: correction: bypassed lockin by 0 amplitude')
        self._state = 'lockin_bypassed'


    def sweep_lockin_readout(self, target, duration):
        ''' Start a sweep while measuring with lockin with minimal 
            communication between adwin-PC (buffering the measurement
            in fifo). The sample rate is determined by the lockin
            process which needs to be already running. '''
        # lockin must already be running
        if self._state != 'lockin_running':
            log.critical('ADwin: Lockin must be running for readout.Abort')
            raise AdwinModeError
        self._start_sweep(target, duration)
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
        return inph, quad

    def sweep_lockin_dc_readout(self, target, duration):
        ''' Start a sweep while measuring the raw dc input with lockin
            process active and minimal communication between adwin-PC
            (buffering the -measurement in fifo). The sample rate is 
            defined by the lockin process (500kHz) which needs to be
            already running. '''
        # lockin must already be running
        if self._state != 'lockin_running':
            log.critical('ADwin: Lockin must be running for readout.Abort')
            raise AdwinModeError
        if duration * self._params['sample_rate'] > FIFO_LEN:
            log.warning('ADwin: Fifo holds values for max %s seconds.',
                        FIFO_LEN / self._params['sample_rate'])
        # start sweep
        self._start_sweep(target, duration)
        sleep(duration)
        # check if sweep has ended
        while self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        # read dc data from fifo
        dc = self._read_single_fifo(FIFO_INPHASE)
        return dc

    def lockin_dc_readout(self, duration):
        ''' Measure DC input for duration with full 500kHz sample rate
            for duration seconds. If no lockin should be applied, start
            lockin process with amplitude zero. Amount of collectable
            data is limited by fifo buffer length. '''
        # lockin must already be running
        if self._state != 'lockin_running':
            log.critical('ADwin: Lockin must be running for readout.Abort')
            raise AdwinModeError
        # check that FIFO is long enough to hold all values
        if duration * self._params['sample_rate'] > FIFO_LEN:
            log.warning('ADwin: Fifo holds values for max %s seconds.',
                        FIFO_LEN / self._params['sample_rate'])
        # enable data aquisition
        self.adw.Set_Par(MEASURE_ACTIVE_PAR, 1)
        sleep(duration)
        # disable data aquisition
        self.adw.Set_Par(MEASURE_ACTIVE_PAR, 0)
        # read dc data from fifo
        dc = self._read_single_fifo(FIFO_INPHASE)
        return dc

    def sweep_dc_readout(self, target, duration):
        # lockin must already be running with zero amplitude (=bypassed)
        if self._state != 'lockin_bypassed':
            raise AdwinModeError
        # check that FIFO is long enough to hold all values
        if duration * self._params['sample_rate'] > FIFO_LEN:
            log.warning('ADwin: Fifo holds values for max %s seconds.',
                        FIFO_LEN / self._params['sample_rate'])
        # start sweep
        self._start_sweep(target, duration)
        sleep(duration)
        # check if sweep has ended
        while self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        # read dc data from fifo
        dc = self._read_single_fifo(FIFO_INPHASE)
        return dc

    def stop_lockin(self):
        """ Stops the lockin process. No lockin signal is applied and no
            readout is triggered by a sweep anymore. """
        if self._state not in ['lockin_running', 'lockin_bypassed']:
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

    def ramp_outputs(self, target, duration, wait=True):
        """ Ramp the outputs of the  Send the target values of the sweep to the PC and start the 
            sweep process. If wait==True it waits for the sweep to be
            finished. """
        self._start_sweep(target, duration)
        while wait is True and self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        if wait is True:
            log.info('Adwin finished sweep.')
        else:
            log.info('Adwin sweeping with no idea, when it ends.')

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
        self.adw.SetData_Long(target_bits, TARGET_DATA, 1, len(target_bits))
        log.info('Adwin starting %.1f second sweep with readout.', duration)
        # initialize process
        self.adw.Start_Process(self._sweep_process_no)
        # start process after small delay to wait for init to calm down
        sleep(delay)
        self.adw.Set_Par(SWEEP_ACTIVE_PAR, 1)

    def _read_single_fifo(self, fifo_no, qty=True):
        ''' Read FIFO with fifo_no, and clear the other fifo '''
        samples = self.adw.Fifo_Full(fifo_no)
        data = self.adw.GetFifo_Float(fifo_no, samples)
        # clear the other fifo
        if fifo_no == FIFO_INPHASE:
            clear_fifo_no = FIFO_QUADRATURE
        elif fifo_no == FIFO_QUADRATURE:
            clear_fifo_no = FIFO_INPHASE
        else:
            raise AdwinArgumentError
        self.adw.Fifo_Clear(clear_fifo_no)
        if qty:
            data = self.aio.bit2qty(data, 'readout', False)
        return data

if __name__ == '__main__':
    pass
