# Driver for a StepMotor to rotate a phase shifter
# @KIT 2018 TW
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

import zerorpc
from qkit.core.instrument_base import Instrument
import logging
import types
from qkit.gui.notebook.Progress_Bar import Progress_Bar


class StepMotor(Instrument):
    """
    Driver for the step motor connected to a raspberry pi. Connection from PC to raspberry pi uses zerorpc.
    Driver tracks the rotation of the phase shifter to not cause any damage. That means you have to provide it's
    initial position in rotations (float). Phase shifter can have a max of 17.5 rotations. Counting positive in the
    mathematical sense if you look onto the screw from the motor's perspective. (Between motor and phase shifter is
    a 27:1 gearbox. This means rotations are rather slow.)
    """

    def __init__(self, name, address="tcp://10.22.197.112:4242", initial_position=0):

        self.c = zerorpc.Client()
        self.c.connect(address)

        if self.c.get_connection():
            print 'connected to Raspberry Pi'
        else:
            logging.error('No connection to Raspberry Pi')

        if initial_position == 0:
            logging.warning("You didn't provide an inital position. Please make sure that the phase shifter "
                            "is in its lowest position, since the rotation is tracked to prevent the damage of "
                            "either motor or phase shifter. Or alternatively change the rotations."
                            "Please also think of that when manually changing the phase shifter")
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self.angle = initial_position * 360
        self.min_angle = 0
        self.max_angle = 17.5 * 360
        self.rotations = initial_position
        self.show_progress_bar = True

        self.add_parameter('angle', type=int, flags=Instrument.FLAG_GETSET, minval=0, maxval=17.5 * 360)
        self.add_parameter('waiting_time', type=float, flags=Instrument.FLAG_GETSET,
                           minval=0.0001, maxval=0.01)
        self.add_parameter('rotations', type=float, flags=Instrument.FLAG_GETSET, minval=0, maxval=17.5 * 360)
        self.add_function('turn')

    def do_get_angle(self):
        """
        :return: the current angle of the phase shifter. (Works only if the phase shifter was in the "zero"-state
                at the beginning
        """
        return self.angle

    def do_set_angle(self, angle):
        """
        Sets the phase shifter to a given value.
        :param angle:
        :return: None
        """
        difference = angle - self.angle
        self.c.turn(difference)

    def turn(self, angle):
        """
        Turns the step motor and thus the phase shifter at a given angle
        :param angle: value in degrees positive or negative.
        :return: None
        """
        self.angle += angle
        if self.angle < self.min_angle or self.angle > self.max_angle:
            logging.error("Out of range, operation aborted to prevent damage!")
            self.angle -= angle
        else:
            self.c.turn(angle)
            max_steps = self.c.get_max_steps()
            if self.show_progress_bar:
                pb = Progress_Bar(max_steps - 2)
            try:
                while self.c.get_steps() < max_steps - 1:
                    if self.show_progress_bar:
                        for i in range(self.c.get_steps() - pb.progr):
                            pb.iterate()
                    else:
                        pass
            except KeyboardInterrupt:
                logging.warning("KeyboardInterrupt: Rotation stopped!")
                self.c.stop_rotation()
                self.angle -= int(angle * (float(max_steps - self.c.get_steps())) / max_steps)

    def do_set_waiting_time(self, waiting_time):
        """
        This is a function to specify the speed of your step motor. Please handle with care. The shorter
        the waiting time between steps the faster is your step motor (default = 0.0001 sec)
        :param waiting_time: time in sec between 0.0001 and 0.01
        :return:
        """
        self.c.set_waiting_time(waiting_time)

    def do_get_waiting_time(self):
        """
        :return: the waiting time between steps and thus the speed of your step motor
        """
        return self.c.get_waiting_time()

    def do_get_rotations(self):
        """
        :return: the current position of the phase shifter if correctly initialized
        """
        self.rotations = float(self.angle) / 360
        return self.rotations

    def do_set_rotations(self, position):
        """
        Used to set the position of the phase shifter if manually changed in rotations from lowest postion.
        positive rotation in the mathematical sense when looking from motor perspective
        :param position: number of rotations of the phase shifter from zero (float)
        :return: None
        """
        self.rotations = position
