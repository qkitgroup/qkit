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

from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy as np

class Keithley_2230(Instrument):
    '''
    This is the driver for the Keithley 2230 Tripple Channel DC Power Supply

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Keithley_2230', address='<GBIP address>',
        reset=<bool>)
    '''
    
    def __init__(self, name, address, reset=False):
        """
        Parameters
        ----------
        name : str
            Name of the instrument
        address : str
            GPIB address of the instrument
        reset : bool, optional
            Initialization resets instrument to default settings
        """
        
        # Initialize wrapper functions
        logging.info(__name__ + ' : Initializing instrument Keithley_2230')
        Instrument.__init__(self, name, tags=['physical'])

        # Add some global constants
        self._address = address
        self._visainstrument = visa.open_resource(self._address)
        
        self.add_parameter("out_V", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), units = 'V',
                           minval = 0, maxval = 30,
                           channel_prefix = "ch%d_")
        
        self.set_parameter_bounds(name = "ch3_out_V", minval = 0, maxval = 6)
        
        self.add_parameter("out_I", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), units = "I",
                           minval = 0, maxval = 1.5,
                           channel_prefix = "ch%d_")
        
        self.set_parameter_bounds(name = "ch3_out_I", minval = 0, maxval = 5)
        
        self.add_parameter("out_V_limit", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), units = 'V',
                           minval = 0, maxval = 30,
                           channel_prefix = "ch%d_")
        
        self.set_parameter_bounds(name = "ch3_out_V_limit", minval = 0, maxval = 6)

        self.add_parameter("enable_output", type = bool,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), channel_prefix = "ch%d_")
        
        self.add_parameter("selected_channel", type = int,
                           flags = Instrument.FLAG_GETSET)
        
        self.add_parameter("timer_state", type = bool,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), channel_prefix = "ch%d")
        
        self.add_parameter("timer_in_s", type = float,
                           flags = Instrument.FLAG_GETSET,
                           channels = (1,3), units = "s",
                           minval = 0.01, maxval = 60000,
                           channel_prefix = "ch%d")
        
        
        self.add_function("turn_on")
        self.add_function("turn_off")
        self.add_function("get_status")
        self.add_function("set_out_V")
        self.add_function("get_out_V")
        self.add_function("set_out_I")
        self.add_function("get_out_I")
        
    def _do_set_out_V(self, voltage, channel):
        self._visainstrument.write("instrument:select ch%s" % channel)
        if self._do_get_out_V_limit(channel) < voltage:
            print("Given voltage is above voltage limit.")
        else:
            logging.debug(__name__ + " : setting voltage on channel %s to %s V." %(channel, voltage))
            self._visainstrument.write("voltage:amplitude %s" % voltage)
        
    def _do_get_out_V(self, channel):
        logging.debug(__name__ + " : getting voltage on channel %s" % channel)
        return float(self._visainstrument.query("measure:voltage? ch%s" % channel)[:-1])
    
    
    def _do_set_out_I(self, current, channel):
        logging.debug(__name__ + " : setting voltage on channel %s to %s V." %(channel, current))
        self._visainstrument.write("instrument:select ch%s" % channel)
        self._visainstrument.write("current:amplitude %s" % current)
        
    def _do_get_out_I(self, channel):
        logging.debug(__name__ + " : getting voltage on channel %s" % channel)
        return float(self._visainstrument.query("measure:current? ch%s" % channel)[:-1])
    
    
    def _do_set_out_V_limit(self, voltage, channel):
        logging.debug(__name__ + " : setting voltage limit of channel %s to %s V." %(channel, voltage))
        self.set_selected_channel(channel)
        self._visainstrument.write("voltage:limit %s" % voltage)
        
    def _do_get_out_V_limit(self, channel):
        logging.debug(__name__ + " :getting voltage limit of channel %s." % channel)
        self.set_selected_channel(channel)
        return float(self._visainstrument.query("voltage:limit?")[:-1])
    
    
    def _do_set_enable_output(self, on_off, channel):
        if on_off:
            logging.debug(__name__ + ' : activating output channel %s.' % channel)
        else:
            logging.debug(__name__ + ' : deactivating output channel %s.' % channel)
        self.set_selected_channel(channel)
        self._visainstrument.write("output:enable %s" % on_off)
        
    def _do_get_enable_output(self, channel):
        logging.debug(__name__ + ' : getting status of output channel %s.' % channel)
        self.set_selected_channel(channel)
        return int(self._visainstrument.query("output:enable?")[:-1])
    
        
    def _do_set_selected_channel(self, channel_num):
        logging.debug(__name__ + " : selecting channel %s." % channel_num)
        self._visainstrument.write("instrument:select ch%s" % channel_num)
        
    def _do_get_selected_channel(self):
        logging.debug(__name__ + " : getting selected channel.")
        return int(self._visainstrument.query("instrument:select?")[2:-1])
    
    
    def _do_set_timer_state(self, on_off, channel):
        if on_off:
            logging.debug(__name__ + ' : activating timer of channel %s.' % channel)
            self._visainstrument.write("output:timer:state:enable ON")
        else:
            logging.debug(__name__ + ' : deactivating timer of channel %s.' % channel)
            self._visainstrument.write("output:timer:state:enable OFF")
    
    def _do_get_timer_state(self, channel):
        logging.debug(__name__ + " : getting status of channel %s timer." % channel)
        self.set_selected_channel(channel)
        return int(self._visainstrument.query("output:timer:state?")[:-1])
    
    
    def _do_set_timer_in_s(self, time, channel):
        logging.debug(__name__ + " : setting timer of channel %s" % channel)
        self.set_selected_channel(channel)
        self._visainstrument.write("output:timer:delay" % time)
        
    def _do_get_timer_in_s(self, channel):
        logging.debug(__name__ + " : getting timer of channel %s" % channel)
        self.set_selected_channel(channel)
        return float(self._visainstrument.query("output:timer:delay?" )[:-1])
        
        
    def turn_on(self):
        logging.debug(__name__ + " : enabling device.")
        self._visainstrument.write("output on")
        
    def turn_off(self):
        logging.debug(__name__ + " : disabling device.")
        self._visainstrument.write("output off")
    
    def get_status(self):
        logging.debug(__name__ + " : getting device status.")
        status = int(self._visainstrument.query("output?")[:-1])
        if status:
            return("Keithley 2230 ready for takeoff.")
        else:
            return("Keithley 2230 is in a coffee break.")
    
    def set_out_V(self, channel, voltage):
        '''Allows easier access to set function for all channels
        '''
        self.set('ch%s_out_V'% channel, voltage)
        
    def get_out_V(self, channel):
        '''Allows easier access to get function for all channels.
        '''
        return self.get('ch%s_out_V'% channel)
    
    def set_out_I(self, channel, current):
        '''Allows easier access to set function for all channels
        '''
        self.set('ch%s_out_I'% channel, current)
        
    def get_out_I(self, channel):
        '''Allows easier access to get function for all channels.
        '''
        return self.get('ch%s_out_I'% channel)
    
    
    
    
        