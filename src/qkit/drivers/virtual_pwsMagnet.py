import qkit
from qkit.core.instrument_base import Instrument
import types
import logging
import numpy as np
import time

global conversion_factor
conversion_factor = 52.02477434  # mT/A, solenoid in white fridge


class virtual_pwsMagnet(Instrument):
    '''
    This is the driver for a virtual Power Supply for the solenoid coil

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Tektronix_PWS4205', address='<USB address>, reset=<bool>')
    USB address e.g. USB0::0x0699::0x0390::C010427::INSTR
    '''

    def __init__(self, name, PWS1='PWS1', PWS2='PWS2'):
        '''
        Initializes a virtual magnet built upon two PWS4205 wired in parallel
        connected to solenoid coil in the white fridge
        both current sources deliver up to 5A, but coil will quench
        lower
        
        Input:
          name (string)    : name of the instrument
          PWS1 (string) : name of the first power source, default=PWS1
          PWS2 (string) : name of the second power source, default=PWS2
        '''
        logging.info(__name__ + ' : Initializing instrument virtual power source')
        Instrument.__init__(self, name, tags=['virtual'])
        try:
            self._PWS1 = qkit.instruments.get(PWS1)
        except:
            logging.error('no PWS1 found ... aborting')
            return
        try:
            self._PWS2 = qkit.instruments.get(PWS2)
        except:
            logging.error('no PWS2 found ... aborting')
            return

        self.add_parameter('current', type=float,
                           flags=Instrument.FLAG_GETSET, units='A')
        self.add_parameter('voltage', type=float,
                           flags=Instrument.FLAG_GET, units='V')
        self.add_parameter('status', type=bool,
                           flags=Instrument.FLAG_GETSET)
        self.add_parameter('magneticField', type=float,
                           flags=Instrument.FLAG_GET, units='mT')

        self.add_function('get_all')
        self.add_function('ramp_current')
        self.add_function('ramp_magenticField')
        self.add_function('check_for_quench')
        self.add_function('on')
        self.add_function('off')
        self.get_all()

    def get_all(self):
        '''
        Reads all implemented parameters from the instrument,
        and updates the wrapper.

        Input:
            None

        Output:
            None
        '''
        logging.debug(__name__ + 'get_all()')
        self.get('current')
        self.get('voltage')
        self.get('status')
        self.get('magneticField')

    def do_get_current(self):
        '''
        Reads the current signal from the instrument

        Input:
            None

        Output:
            current (float) : current in amps
        '''
        logging.debug(__name__ + 'do_get_current()')
        self._current = getattr(self._PWS1, 'get_current')() + getattr(self._PWS2, 'get_current')()
        return self._current

    def do_set_current(self, curr, wait=0.2):
        '''
        Sets the Amplitude of the signal

        Input:
            curr (float) : current in amps
            wait (float) : waiting time in sec, default=0.2

        Output:
            None
        '''
        if curr < 0:
            logging.error('Negative currents now allowed!')
            return
        logging.debug(__name__ + 'do_set_current()')
        getattr(self._PWS1, 'set_current')(curr / 2.)
        time.sleep(wait)
        getattr(self._PWS2, 'set_current')(curr / 2.)
        time.sleep(wait)
        self._current = self.do_get_current()
        self.get_all()

    def do_get_voltage(self):
        '''
        Reads the voltage signal from the instrument

        Input:
            None

        Output:
            volt (float) : Voltage in Volts
        '''
        logging.debug(__name__ + 'do_get_voltage()')
        self._voltage = (getattr(self._PWS1, 'get_voltage')() + getattr(self._PWS2, 'get_voltage')()) / 2.
        return self._voltage

    def do_get_status(self):
        '''
        Reads the output status from the instrument
        'On' only whene all sub-instruments are on
        Input:
            None

        Output:
            status (boolean)
        '''
        logging.debug(__name__ + 'do_get_status()')
        status1 = bool(getattr(self._PWS1, 'get_status')())
        status2 = bool(getattr(self._PWS2, 'get_status')())
        if status1 and status2:
            self._status = status1
        else:
            self._status = False
            getattr(self._PWS1, 'off')()
            getattr(self._PWS2, 'off')()
        return bool(self._status)

    def do_set_status(self, status):
        '''
        Sets the output status of the instrument with
        additional status check

        Input:
            status (boolean) 

        Output:
            None
        '''
        logging.debug(__name__ + 'do_set_status()')
        getattr(self._PWS1, 'set_status')(status)
        getattr(self._PWS2, 'set_status')(status)
        self._status = self._do_get_statur()

    def do_get_magneticField(self):
        logging.debug(__name__ + 'do_get_magneticField()')
        self._magneticField = (getattr(self._PWS1, 'get_current')() + getattr(self._PWS2,
                                                                              'get_current')()) * conversion_factor
        return self._magneticField

    def ramp_magenticField(self, target, step=conversion_factor * 1e-2, wait=0.2, showvalue=True):
        '''
        Ramps the Amplitude of the signal
        Calls ramp_current with the input values convrted to current units

        Input:
            target (float) : target magentic field in mT
            step (float) : magnetic field steps in mT
            wait (float) : waiting time in sec, default=0.2
            showvalue (bool) : print values, default=True

        Output:
            None
        '''
        logging.debug(__name__ + 'ramp_magneticField()')
        target_current = target / conversion_factor
        step_current = step / conversion_factor
        self.ramp_current(self, target=target_current, step=step_current, wait=wait, showvalue=showvalue,
                          print_mag=True)

    def ramp_current(self, target, step=1e-2, wait=0.2, showvalue=True, print_mag=False):
        '''
        Ramps the Amplitude of the signal

        Input:
            target (float) : target current in amps
            step (float) : current steps in amps, default=1e-2
            wait (float) : waiting time in sec, default=0.2
            showvalue (bool) : print values, default=True
            print_mag (bool) : prints values in magentic field units, default=False

        Output:
            None
        '''
        logging.debug(__name__ + 'ramp_current()')
        voltage = self.do_get_voltage()
        current = self.do_get_current()
        if voltage > 0.95:
            print "WARNING! Magnet quench!! ramping down the coil..."
            self.ramp_current(0., 2e-3, wait=wait, showvalue=showvalue)
            return
        else:
            if target < current: step = -step
            Is = np.arange(current, target + step, step)
            for I in Is:
                self.do_set_current(I, wait)
                """
                if print_mag:
                    value_print = 'B = ' + str(self.do_get_current()*conversion_factor) + 'mT'
                else:
                    value_print = 'I = ' + str(self.do_get_current()) + 'A'
                #if showvalue:
                    #print value_print+ ", V1=" + str(getattr(self._PWS1, 'get_voltage')()) + "V, " + "V2=" + str(getattr(self._PWS2, 'get_voltage')()) + "V"
                    """
        voltage = self.do_get_voltage()
        current = self.do_get_current()
        if target != 0:
            res = int(np.trunc(voltage / current * 1000))
        else:
            res = 0
        """
        if print_mag:
            value_print = 'B= '+str(current*conversion_factor) + 'mT'
        else:
            value_print = 'I= '+str(current) + 'A'
        print "Target value reached: " + value_print+", Voltage is " + str(voltage) + " V, resistance = " + str(res) + " mOhm"
        """

    def check_for_quench(self, wait=5, threshold=0.95, repetitions=1000):
        '''
        Checks the magent for quench

        Input:
            wait (float) : waiting time in sec, default=5
            threshold (float) : maximum voltage in volts, default=0.95
            repetitions (int) : number of times quenching is checked, default=1000

        Output:
            None
        '''
        logging.debug(__name__ + 'check_for_quench()')
        for i in range(repetitions):
            time.sleep(wait)
            voltage = self.do_get_voltage()
            current = self.do_get_current()
            print "V=" + str(np.trunc(voltage * 1000) / 1000.) + "V, I=" + str(
                np.trunc(current * 1000) / 1000.) + "A, R=" + str(int(np.trunc(voltage / current * 1000))) + "mOhm"
            if voltage > threshold:
                print "WARNING! Magnet quench!! ramping down the coil..."
                self.ramp_current(0., 2e-3, wait=0.2, showvalue=True)
                return

    def off(self):
        '''
        Sets status to False

        Input:
            None

        Output:
            None
        '''
        self.set_status(False)

    def on(self):
        '''
        Sets status to True

        Input:
            None

        Output:
            None
        '''
        self.set_status(True)
