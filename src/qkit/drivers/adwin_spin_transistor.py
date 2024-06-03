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
from math import ceil
from time import sleep
import numpy as np
import ADwin as adw
from qkit.core.instrument_base import Instrument
from qkit.drivers.adwinlib.io_handler import AdwinIO, AdwinModeError
from qkit.drivers.adwinlib.io_handler import AdwinLimitError
from qkit.drivers.adwinlib.io_handler import AdwinTransmissionError

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
FIFO_LENGTH = 10003
MIN_FREQUENCY = 20
MAX_FREQUENCY = 40E3
# only "sweep_DC_readout" file
REFRESH_RATE_DC = 500000    # refresh rate in "sweep_DC_readout" file
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
        mode='lockin',
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
        self._lockin_dc_process_no = 1
        self._lockin_dc_process = adbasic_dir / 'Pro2_T11_lockin_dc_readout.TB1'

        # create AdwinIO Instance
        self.aio = AdwinIO(hard_config, soft_config)

        # create ADwin instance
        self.adw = adw.ADwin(DeviceNo=devicenumber,
                             raiseExceptions=1,
                             useNumpyArrays=True)

        # Set 'bootload' to 'False' to not reboot the Adwin.
        if bootload:
            # boot adwin
            btl_name = f"ADwin{processor.replace('T', '')}.btl"
            btl_path = Path(self.adw.ADwindir) / btl_name
            self.adw.Boot(str(btl_path))
            self._state = 'freshly booted'

            # load processes
            if mode == 'lockin':
                log.info('Adwin loading: %s', self._lockin_process.name)
                self.adw.Load_Process(str(self._lockin_process))
                log.info('Adwin loading: %s', self._sweep_process.name)
                self.adw.Load_Process(str(self._sweep_process))
            elif mode == 'dc':
                log.info('Adwin loading: %s', self._dc_readout_process.name)
                self.adw.Load_Process(str(self._dc_readout_process))
            elif mode == 'lockin_dc_readout':
                log.info('Adwin loading: %s', self._lockin_dc_process.name)
                self.adw.Load_Process(str(self._lockin_dc_process))
                log.info('Adwin loading: %s', self._sweep_process.name)
                self.adw.Load_Process(str(self._sweep_process))
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
            self.add_function("lockin_readout")
        if mode == 'dc':
            self.add_function("start_sweep_dc_readout")
        if mode == 'lockin_dc_readout':
            self.add_function("lockin_dc_readout")

    def start_lockin(self, amplitude, frequency, tau, bias=0):
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
        self.adw.Set_FPar(TAO_FPAR, tau)
        # start lockin process
        log.info('Adwin starting: %s', self._lockin_process.name)
        self.adw.Start_Process(self._lockin_process_no)
        self._state = 'lockin_running'
        # get lockin (sample) frequency    
        self._lockin_freq = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)
        log.warning('Adwin lock-in frequency is %.2f Hz.',
                    self._lockin_freq)

    def no_comm_readout(self, stop, duration):
        ''' Start a sweep while measuring with lockin with minimal 
            communication between adwin-PC (buffering the measurement
            in fifo) '''
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
        return inph, quad

    def stop_lockin(self):
        """ Stops the lockin process. No lockin signal is applied and no
            readout is triggered by a sweep anymore. """
        if 'lockin' not in self._mode:
            raise AdwinModeError
        if self._state != 'lockin_running':
            log.warning('ADwin: Lockin not running? Stopping anyway.')
        log.info('Adwin stopping: %s', self._lockin_process.name)
        self.adw.Stop_Process(self._lockin_process_no)

    def read_outputs(self, channel=None):
        """ Read the current saved output values of the ADwin. After a 
            restart this might not be the correct values. """
        # Read all adwin parameters holding the current output values
        outs = np.empty(NO_OUTPUT_CHANNELS)
        outs.fill(np.NaN)
        for i, _ in enumerate(outs):
            val =  self.adw.Get_Par(i+1)
            outs[i] = self.aio.bit2qty(val, channel, absolute=True)
        return outs

    def start_sweep(self, stop, duration, start=None, wait=False):
        """ Send the target values of the sweep to the PC and start the 
            sweep process. If wait==True it waits for the sweep to be
            finished. """
        # set sweep parameters
        self.adw.Set_FPar(DURATION_FPAR, duration)
        # transform stop array/workin_point to bit list
        stop = self.aio.qty2bit(stop)
        self.adw.SetData_Long(stop, STOP_DATA, 1, len(stop))
        if isinstance(start, (list, dict)):
            start = self.aio.qty2bit(start)
            self.adw.SetData_Long(start, START_DATA, 1, len(start))
        if self._mode in ['lockin', 'lockin_dc_readout']:
            # clear lockin Fifo before start_sweep
            #########################self.adw.Fifo_Clear(FIFO_INPHASE)
            #########################self.adw.Fifo_Clear(FIFO_QUADRATURE)
            # start sweep process
            self.adw.Start_Process(self._sweep_process_no)
        elif self._mode == 'dc':
            self.adw.Fifo_Clear(FIFO_DC_READOUT)
            self.adw.Start_Process(self._dc_readout_process_no)
        log.info('Adwin started %.1f second sweep.', duration)
        while wait is True and self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 1:
            pass
        if wait is True:
            log.info('Adwin finished sweep.')
        else:
            log.info('Adwin sweeping untracked by "start_sweep".')

    def start_sweep_dc_readout(self, stop, duration, start=None):
        """ Send the target values of the sweep to the PC and start the 
            sweep process. Then collect all the readout data """
        if self._mode != 'dc':
            raise AdwinModeError
        # start sweep
        self.start_sweep(stop, duration, start)
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

    def stop_sweep(self):
        """ Stopping sweep process immediately """
        if self._mode in ['lockin', 'lockin_dc_readout']:
            log.info('Adwin stopping: %s', self._sweep_process.name)
            self.adw.Stop_Process(self._sweep_process_no)
        elif self._mode == 'dc':
            log.info('Adwin stopping: %s', self._dc_readout_process.name)
            self.adw.Stop_Process(self._dc_readout_process_no)

    def lockin_readout(self):
        """ read lockin data """
        if self._mode != 'lockin' or self._state != 'lockin_running':
            raise AdwinModeError
        # determine expected sample count
        data_rate = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)
        duration = self.adw.Get_FPar(DURATION_FPAR)
        expected_samples = int(ceil(data_rate * duration))
        # log before readout
        log.info('lockin reading:', extra={
            'data_rate': data_rate,
            'duration': duration,
            'expected_samples': expected_samples})
        # create output arrays
        inphase = np.empty(expected_samples)
        quadrature = np.empty(expected_samples)
        inphase.fill(np.NaN)
        quadrature.fill(np.NaN)
        # initilize variables for while loop
        recieved_samples = 0
        max_samples = 0
        no_samples_counter = 0

        while recieved_samples < expected_samples:
            # how many samples are in the fifo (always same for both)
            samples = self.adw.Fifo_Full(FIFO_INPHASE)
            if samples > 0: # there are samples to be recieved
                # get the same amount of values from both fifos
                quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
                inph = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
                # add the recieved samples to the predefined arrays
                for i in range(samples):
                    try:
                        inphase[recieved_samples + i] = inph[i]
                        quadrature[recieved_samples + i] = quad[i]
                    except IndexError as exc:
                        # if there is 3 or less extra samples
                        if not i + 1 == samples <= 3:
                            raise AdwinTransmissionError from exc
                        else:
                        # else: just ignore the extra sample
                            log.warning('ADwin lockin: %s extra samples have '
                                        'been ignored.', samples)
            else: # no samples to be taken can mean, that there is an
                  # error which has to be handled
                if self.adw.Get_Par(SWEEP_ACTIVE_PAR) == 0:
                    # measurement seem to be over but we did not get all
                    # the expected samples.
                    if no_samples_counter == 10:
                        if expected_samples - recieved_samples == 1:
                            break
                        log.critical('%s: Did not recieve enough samples',
                                     __name__)
                        raise AdwinTransmissionError
                    no_samples_counter += 1
                # else: measurement is still running. We are probably
                # just to fast in asking for new samples. Look again
            # add recieved samples number to total recieved sample count
            recieved_samples += samples
            # track the maximum transfered sample per cycle
            if samples > max_samples:
                max_samples = samples
        #calculate maximum utilization of the adwin fifo
        util = max_samples / FIFO_LENGTH * 100
        #log after readout
        log.info('Recieved %i samples @ maximum fifo utilization %.1f%%',
                 recieved_samples, util)
        # convert values to physical input properties
        inphase = self.aio.bit2qty(inphase, channel='readout', absolute=False)
        quadrature = self.aio.bit2qty(quadrature, channel='readout', absolute=False)
        return inphase, quadrature

    def lockin_readout_without_sweep(self, duration):
        """ read lockin data """
        if self._mode != 'lockin' or self._state != 'lockin_running':
            raise AdwinModeError
        # determine expected sample count
        #data_rate = self.adw.Get_FPar(REPORT_FREQUENCY_FPAR)
        data_rate = 500000
        expected_samples = int(ceil(data_rate * duration))
        # log before readout
        log.info('lockin reading:', extra={
                 'data_rate': data_rate,
                 'duration': duration,
                 'expected_samples': expected_samples})
        # create output arrays
        inphase = np.empty(expected_samples)
        quadrature = np.empty(expected_samples)
        # initilize variables for while loop
        recieved_samples = 0
        max_samples = 0

        ###########################Debug FIFO FILLING
        #self.adw.Set_Par(9, 0)
        #self.adw.Fifo_Clear(FIFO_INPHASE)
        #self.adw.Fifo_Clear(FIFO_QUADRATURE)
        #sleep(0.2)
        #self.adw.Set_Par(9, 1)
        #sleep(0.1)
        samples = int(expected_samples / 2)
        quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
        inph = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
        for i in range(samples):
            inphase[recieved_samples + i] = inph[i]
            quadrature[recieved_samples + i] = quad[i]
        quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
        inph = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
        recieved_samples += samples
        for i in range(samples):
            inphase[recieved_samples + i] = inph[i]
            quadrature[recieved_samples + i] = quad[i]
        # while recieved_samples < expected_samples:
        #     sleep(0.)
        #     # how many samples are in the fifo (always same for both)
        #     samples = int(data_rate * duration) #self.adw.Fifo_Full(FIFO_INPHASE)
        #     if samples > 50000: # there are samples to be recieved
        #         # In the last round we get too many samples -> change
        #         # the amount of sampled to be loaded in this case
        #         #if samples > expected_samples - recieved_samples:
        #         #    samples = expected_samples - recieved_samples
        #         # get the same amount of values from both fifos
        #         print(samples)
        #         quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, samples)
        #         inph = self.adw.GetFifo_Float(FIFO_INPHASE, samples)
        #         # add the recieved samples to the predefined arrays
        #         for i in range(samples):
        #             inphase[recieved_samples + i] = inph[i]
        #             quadrature[recieved_samples + i] = quad[i]
        #         recieved_samples += samples
        #         # track the maximum transfered sample per cycle
        #         if samples > max_samples:
        #             max_samples = samples
        #         print(f'read {samples} samples') ################# debug
        # #calculate maximum utilization of the adwin fifo
        # util = max_samples / FIFO_LENGTH * 100
        # #log after readout
        # log.info('Recieved %i samples @ maximum fifo utilization %.1f%%',
        #          recieved_samples, util)
        # # convert values to physical input properties
        # self.adw.Set_Par(9, 0) ######################debug
        # #inphase = self.aio.bit2qty(inphase, channel='vd', absolute=False)
        return inphase, quadrature

        inphase = self.aio.bit2qty(inphase, channel='readout', absolute=False)
        quadrature = self.aio.bit2qty(quadrature, channel='readout', absolute=False)
        return inphase, quadrature

    def lockin_dc_readout(self, expected_samples):
        ''' Read 'target_samnples' unfiltered adc values from the adwin ''' 
        # idea: lockin should be already running
        if self._mode != 'lockin_dc_readout':
            raise AdwinModeError
        if self._state != 'lockin_running':
            log.warning('Adwin lockin not running lockin_dc_readout!')
        # clear fifo
        self.adw.Fifo_Clear(FIFO_DC_READOUT)
        # read the defined amount of samples
        values = np.empty(expected_samples)
        recieved_samples = 0
        max_samples = 0
        while recieved_samples < expected_samples:
            samples = self.adw.Fifo_Full(FIFO_DC_READOUT)
            if samples > 0:
                # in the last round we will get too many samples, so change the
                # amount of sampled to be loaded in this case
                if samples > expected_samples - recieved_samples:
                    samples = expected_samples - recieved_samples
                # read samples
                val = self.adw.GetFifo_Float(FIFO_DC_READOUT, samples)
                for i in range(samples):
                    values[recieved_samples + i] = val[i]
                recieved_samples += samples
            # track the maximum transfered sample per cycle
                if samples > max_samples:
                    max_samples = samples
        #calculate maximum utilization of the adwin fifo
        util = max_samples / FIFO_LEN_DC_RO * 100
        log.info('Recieved %i samples @ maximum fifo utilization %.1f%%',
                 recieved_samples, util)
        # convert values to physical input properties
        values = self.aio.bit2qty(values, channel='readout', absolute=True)
        return values

    def lockin_readout_in_steps(self, expected_samples: int):
        """ read lockin data """
        inphase = np.empty(expected_samples)
        quadrature = np.empty(expected_samples)
        recieved_samples = 0
        while recieved_samples < expected_samples:
            new_samples = self.adw.Fifo_Full(FIFO_INPHASE)
            if new_samples >= int(expected_samples / 5):
                if new_samples > expected_samples - recieved_samples:
                    new_samples = expected_samples - recieved_samples
                quad = self.adw.GetFifo_Float(FIFO_QUADRATURE, new_samples)
                inph = self.adw.GetFifo_Float(FIFO_INPHASE, new_samples)
                for i in range(new_samples):
                    inphase[recieved_samples + i] = inph[i]
                    quadrature[recieved_samples + i] = quad[i]
            recieved_samples += new_samples
        return inphase, quadrature

    def lockin_readout_at_once(self, samples, fifo_no):
        ''' read samples from FIFOat once. '''
        return self.adw.GetFifo_Float(fifo_no, samples)


if __name__ == '__main__':
    pass
