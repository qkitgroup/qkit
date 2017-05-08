from instrument import Instrument
import types
import logging

class example(Instrument):

    def __init__(self, name, address=None, reset=False):
        Instrument.__init__(self, name, tags=['measure', 'example'])

        # minimum
        self.add_parameter('value1', type=types.FloatType,
                flags=Instrument.FLAG_GET)

        # tags, format, units and doc
        self.add_parameter('value2', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                tags=['measure'],
                format='%0.2e',
                units='mV',
                doc='some extra info')

        # set bounds and limit rate (stepdelay in ms)
        self.add_parameter('output1', type=types.FloatType,
                flags=Instrument.FLAG_SET,
                minval=0, maxval=10,
                maxstep=0.01, stepdelay=50)

        # option_list
        self.add_parameter('status', type=types.StringType,
                flags=Instrument.FLAG_GETSET,
                option_list=('on', 'off'))

        # format_map and get_after_set
        self.add_parameter('speed', type=types.IntType,
                flags=Instrument.FLAG_GETSET | \
                        Instrument.FLAG_GET_AFTER_SET,
                format_map={0: 'slow', 1: 'medium', 2: 'fast'})

        # channels
        self.add_parameter('input', type=types.FloatType,
                flags=Instrument.FLAG_GET,
                channels=(1, 4))

        # channels with prefix
        self.add_parameter('output', type=types.FloatType,
                flags=Instrument.FLAG_GETSET,
                channels=('A', 'B', 'C'), channel_prefix='ch%s_')

        # persist, softget
        self.add_parameter('gain', type=types.FloatType,
                flags=Instrument.FLAG_SET | \
                        Instrument.FLAG_SOFTGET | \
                        Instrument.FLAG_PERSIST)

        self.add_function('reset')
        self.add_function('get_all')
        self.add_function('step')

        # dummy values for simulating instrument
        self._dummy_value1 = 1.1
        self._dummy_value2 = 1.2
        self._dummy_output1= 1.3
        self._dummy_status = 'off'
        self._dummy_speed = 2
        self._dummy_input = [1, 4, 9, 16]
        self._dummy_output = {'A':0, 'B':1, 'C':2}
        self._dummy_gain = 10

        if address == None:
            raise ValueError('Example Instrument requires an address parameter')
        else:
            print 'Example Instrument  address %s' % address

        if reset:
            self.reset()
        else:
            self.get_all()

    def reset(self):
        """Reset example instrument"""

        logging.info('Resetting example instrument')

        self.set_output1(1.5)
        self.set_status('off')
        self.set_speed('slow')

        self.set_chA_output(0)
        self.set_chB_output(0)
        self.set_chC_output(0)

        self.set_gain(20)

        return True

    def get_all(self):

        self.get_value1()
        self.get_value2()
        self.get_status()
        self.get_speed()

        self.get_input1()
        self.get_input2()
        self.get_input3()
        self.get_input4()

        self.get_chA_output()
        self.get_chB_output()
        self.get_chC_output()

        self.get_gain()

        return True

    def do_get_value1(self):
        return self._dummy_value1

    def do_get_value2(self):
        return self._dummy_value2

    def do_set_output1(self, val):
        self._dummy_output1 = val

    def do_get_status(self):
        return self._dummy_status

    def do_set_status(self, val):
        self._dummy_status = val

    def do_get_speed(self):
        return self._dummy_speed

    def do_set_speed(self, val):
        self._dummy_speed = val

    def do_get_input(self, channel):
        return self._dummy_input[channel-1]

    def do_get_output(self, channel):
        return self._dummy_output[channel]

    def do_set_output(self, val, channel, times2=False):
        if times2:
            val *= 2
        self._dummy_output[channel] = val

    def do_set_gain(self, val):
        self._dummy_gain = val

    def step(self, channel, stepsize=0.1):
        '''Step channel <channel>'''
        print 'Stepping channel %s by %f' % (channel, stepsize)
        cur = self.get('ch%s_output' % channel, query=False)
        self.set('ch%s_output' % channel, cur + stepsize)

