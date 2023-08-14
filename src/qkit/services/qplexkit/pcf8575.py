import smbus
import logging


class IOPort(list):
    """
    Represents the PCF8575 IO port as a list of boolean values.
    """
    def __init__(self, pcf8575, *args, **kwargs):
        super(IOPort, self).__init__(*args, **kwargs)
        self.pcf8575 = pcf8575

    def __setitem__(self, key, value):
        """
        Sets an individual output pin to value.
        """
        self.pcf8575.set_output(key, value)
        logging.info(f'set port {key} to {value}')

    def __getitem__(self, key):
        """
        Gets an individual pin state.
        """
        return self.pcf8575.get_output(key)

    def __repr__(self):
        """
        Represent all ports as a list of booleans.
        """
        state = self.pcf8575.bus.read_word_data(self.pcf8575.address, 0)
        ret = []
        for i in range(16):
            ret.append(bool(state & 1 << 15 - i))
        return repr(ret)

    def __len__(self):
        return 16

    def __iter__(self):
        for i in range(16):
            yield self[i]

    def __reversed__(self):
        for i in range(16):
            yield self[15 - i]


class PCF8575(object):
    """
    A software representation of a single PCF8575 IO expander chip.
    """
    def __init__(self, i2c_bus_no, address):
        self.bus_no = i2c_bus_no
        self.bus = smbus.SMBus(i2c_bus_no)
        self.address = address

    def __repr__(self):
        return f'PCF8575(i2c_bus_no={self.bus_no:d}, address={self.address:#02x})'

    @property
    def port(self):
        """
        Represent IO ports as a list of boolean values.
        """
        return IOPort(self)

    @port.setter
    def port(self, value):
        """
        Set all ports using a list.
        """
        assert isinstance(value, list)
        assert len(value) == 16
        new_state = 0
        for i, val in enumerate(value):
            if val:
                new_state |= 1 << 15 - i
        self.bus.write_byte_data(self.address, new_state & 0xff, (new_state >> 8) & 0xff)

    def set_output(self, pin, value):
        """
        Sets a specific pin output to high (True) or low (False).
        """
        assert pin in range(16), "Output number must be an integer between 0 and 15"
        current_state = self.bus.read_word_data(self.address, 0)
        bit = 1 << 15 - pin
        new_state = current_state | bit if value else current_state & (~bit & 0xffff)
        self.bus.write_byte_data(self.address, new_state & 0xff, (new_state >> 8) & 0xff)

    def get_output(self, pin):
        """
        Gets the boolean state of an individual pin.
        """
        assert pin in range(16), "Pin number must be an integer between 0 and 15"
        state = self.bus.read_word_data(self.address, 0)
        return bool(state & 1 << 15 - pin)
