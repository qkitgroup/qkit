# SMC100 motorized micromanipulator controller
# Guenevere Prawiroatmodjo <guen@vvtp.tudelft.nl>, 2011
# Reinier Heeres <reinier@heeres.eu>, 2008
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

from instrument import Instrument
import visa
from visa import vpp43
from lib import visafunc
import types
import logging
import time

class SMC100(Instrument):

    _state_map = {
        0x0A: 'NOT REFERENCED',
        0x0B: 'NOT REFERENCED',
        0x0C: 'NOT REFERENCED',
        0x0D: 'NOT REFERENCED',
        0x0E: 'NOT REFERENCED',
        0x0F: 'NOT REFERENCED',
        0x10: 'NOT REFERENCED',
        0x11: 'NOT REFERENCED',
        0x14: 'CONFIGURATION',
        0x1E: 'HOMING',
        0x1F: 'HOMING',
        0x28: 'MOVING',
        0x32: 'READY',
        0x33: 'READY',
        0x34: 'READY',
        0x35: 'READY',
        0x3C: 'DISABLE',
        0x3D: 'DISABLE',
        0x3E: 'DISABLE',
        0x46: 'JOGGING',
        0x47: 'JOGGING',
    }

    def __init__(self, name, address, ctr_addr=1, reset=False):
        Instrument.__init__(self, name)

        self._address = address
        self._visa = visa.instrument(self._address,
                        baud_rate=57600, data_bits=8, stop_bits=1,
                        parity=visa.no_parity, term_chars='\r\n')
        self._ctr_addr = ctr_addr

        self.add_parameter('position',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='mm')

        self.add_parameter('state',
            flags=Instrument.FLAG_GET,
            type=types.StringType)

        self.add_parameter('velocity',
            flags=Instrument.FLAG_GETSET,
            type=types.FloatType,
            units='mm/s')

        # Functions
        self.add_function('stop_motion')
        self.add_function('set_state_ready')
        self.add_function('get_error')
        self.add_function('go_home')
        self.add_function('go_left')
        self.add_function('go_right')

        if reset:
            self.reset()
        else:
            self.get_all()

    def raw_read(self):
        navail = visafunc.get_navail(self._visa.vi)
#        print 'Avail: %s' % (navail, )
        BUFSIZE = 4192
        ret = vpp43.ViUInt32()
        b = vpp43.create_string_buffer(BUFSIZE)
        try:
            test = vpp43.visa_library().viRead(self._visa.vi, b, navail, vpp43.byref(ret))
        except Exception, e:
            pass   # This seems to happen almost always...
#            print 'Error: %s' % (e, )

# Weird: sometimes seems to start with NULL byte
        ii = 0
        while b[ii] == '\x00' and ii < 16:
            ii += 1
        jj = ii
        while b[jj] != '\x00' and jj < BUFSIZE-1:
            jj += 1

        s = str(b[ii:jj]).rstrip()
        return s

    def reset(self):
        '''
        Reset the motor controller and do 'homing' calibration
        '''
        self.ask('TS')
        try:
            self.get_state()
        except:
            try:
                print self.get_error()
            except:
                print 'I/O error'
        self.go_home()

    def get_all(self):
        self.get_position()
        self.get_state()
        self.get_velocity()

    def ask(self, command):
        '''
        Write a command and read value from the device
        '''
        try:
            self.write(command)
            time.sleep(0.020)
            ret = self.raw_read()
#            print 'Read: %r' % (ret, )
            if len(ret) > len(command):
                return ret[len(command)+1:]
            else:
                return ret
        except Exception, e:
            print 'Error: %s' % (e, )
            return False

    def write(self, command):
        '''
        Write a command to the device
        '''
        cmd = '%d%s\r\n' % (self._ctr_addr, command)
#        print 'Sending %r' % (cmd, )
        self._visa.write(cmd)

    def do_get_state(self):
        '''
        Get the state of the controller.
        Values: not referenced, configuration, homing, moving, ready, disable or jogging.
        '''
        state = self.ask('TS')
        if(state!=False):
            state = int(state,16)
            return self._state_map[state]
        else:
            return False

    def set_state_ready(self):
        '''
        Set the state to 'ready'.
        '''
        state = self.get_state()
        if(state == 'DISABLE'):
            self.write('MM1')
        if(state == 'NOT REFERENCED'):
            self.write('OR') # Home search
        print self.get_error()

    def set_state_disabled(self):
        '''
        Set the state to 'disabled'.
        '''
        state = self.get_state()
        if(state == 'READY'):
            self.write('MM0')
        if(state == 'NOT REFERENCED'):
            self.write('OR') # Home search
            self.write('MM0')
        print self.get_error()

    def do_get_position(self):
        '''
        Get the current position (mm)
        '''
        return float(self.ask('TP'))

    def do_set_position(self,val):
        '''
        Set the absolute position (mm)
        '''
        # First check state and set to ready
#        if(self.get_state()!='READY'):
#            self.set_state_ready()

        # Use maximum of 5 digits
        self.write('PA%.5f' % val)

    def do_get_velocity(self):
        '''
        Get the current velocity (mm/s)
        '''
        return float(self.ask('VA?'))

    def do_set_velocity(self,val):
        '''
        Set the velocity (mm/s)
        '''
        self.set_state_disabled()
        self.write('VA%.5f' % val)
        self.set_state_ready()

    def stop_motion(self):
        '''
        Stop the motor motion
        '''
        self.write('ST')

    def get_error(self):
        '''
        Get error message
        '''
        result = self.ask('TB')
        if len(result) > 0 and result[0]!='@':
            return result
        else:
            return True

    def go_home(self):
        '''
        'Homing' calibration, go to position = 0
        '''
        self.write('OR')

    def go_left(self, value):
        '''
        Move position relative to the left
        '''
        pos = self.get_position()
        self.set_position(pos-value)

    def go_right(self, value):
        '''
        Move position relative to the left
        '''
        pos = self.get_position()
        print str(pos)
        self.set_position(pos+value)
