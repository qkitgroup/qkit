import zerorpc
from instrument import Instrument
import logging
import types
class StepMotor(Instrument):
    """
    driver for the step motor connected to the raspberry pi. Connection from PC to raspberry pi uses zerorpc.
    """
    def __init__(self, name, address="tcp://10.22.197.101:4242"):
        logging.warning("Please make sure that the phase shifter is in its lowest position, since the "
                        "rotation is tracked to prevent the damage of either motor or phase shifter")
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self.c = zerorpc.Client()
        self.c.connect(address)
        self.angle = 0
        self.min_angle = 0
        self.max_angle = 720

        self.add_parameter('angle', type=types.IntType, flags=Instrument.FLAG_GETSET, minval=0, maxval=720)
        self.add_parameter('waiting_time', type=types.FloatType, flags=Instrument.FLAG_GETSET,
                           minval=0.001, maxval=0.01)
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
        self.turn(difference)

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

    def do_set_waiting_time(self, waiting_time):
        """
        This is a function to specify the speed of your step motor. Please handle with care. The shorter
        the waiting time between steps the faster is your step motor
        :param waiting_time: time in sec between 0.001 and 0.01
        :return:
        """
        self.c.set_waiting_time(waiting_time)

    def do_get_waiting_time(self):
        """
        :return: the waiting time between steps and thus the speed of your step motor
        """
        return self.c.get_waiting_time()