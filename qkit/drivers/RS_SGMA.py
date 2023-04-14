import logging

from qkit import visa

from qkit.drivers.AbstractMicrowaveSource import AbstractMicrowaveSource


class RS_SGMA(AbstractMicrowaveSource):

    def __init__(self, name, address, reset=False):
        logging.info(__name__ + ' : Initializing instrument R&S SGS100A Microwave Source')
        super().__init__(name, tags=['physical'])

        self._address = address
        self._visainstrument = visa.instrument(self._address)
        if (reset):
            self.reset()
        else:
            self.get_all()

    def reset(self):
        logging.info(__name__ + ' : resetting instrument')
        self._visainstrument.write('*RST')
        self.get_all()

    def do_get_power(self):
        logging.debug(__name__ + ' : get power')
        return float(self._visainstrument.query('POW:POW?'))

    def do_set_power(self, amp):
        logging.debug(__name__ + ' : set power to %f' % amp)
        self._visainstrument.write('POW:POW %s' % amp)

    def do_get_frequency(self):
        logging.debug(__name__ + ' : get frequency')
        return float(self._visainstrument.query('FREQ:CW?'))

    def do_set_frequency(self, freq):
        logging.debug(__name__ + ' : set frequency to %f' % freq)
        self._visainstrument.write('FREQ:CW %s' % freq)

    def do_get_status(self):
        logging.debug(__name__ + ' : get status')
        return bool(int(self._visainstrument.query('OUTP?')))

    def do_set_status(self, status):
        logging.debug(__name__ + ' : set status to %s' % status)

        if status == True:
            self._visainstrument.write('OUTP ON')
        elif status == False:
            self._visainstrument.write('OUTP OFF')
        else:
            raise ValueError('set_status(): can only set True or False')
