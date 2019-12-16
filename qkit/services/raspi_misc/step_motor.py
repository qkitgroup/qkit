# Taken from the manual belonging to the joy it step motor
# and applied to work remotely with zerorpc
# rotation is threaded to give feedback during the rotation

from time import sleep
import RPi.GPIO as gpio
import numpy as np
import zerorpc
import threading

class StepMotor(object):
    """
    This class controls the step motor via GPIO Pins and
    opens a zerorpc server for connection with other pcs
    Make sure this file is executable and you start it on reboot with
    cronjob for example
    """
    def __init__(self, initial_position=0):
        gpio.setmode(gpio.BCM)

        # Pin-Assignment
        self.A = 18
        self.B = 23
        self.C = 24
        self.D = 25
        self.wait = 0.001  # this is a good value for half step_op
        self.sequence = []
        self.set_operation_mode(1)
        self.rotations = initial_position
        self.steps = 0
        self.max_steps = 0
        self.stop = False
        # defining the PINs
        gpio.setup(self.A, gpio.OUT)
        gpio.setup(self.B, gpio.OUT)
        gpio.setup(self.C, gpio.OUT)
        gpio.setup(self.D, gpio.OUT)
        gpio.output(self.A, 0)
        gpio.output(self.B, 0)
        gpio.output(self.C, 0)
        gpio.output(self.D, 0)

    # defining the 8 steps
    def step1(self):
        gpio.output(self.D, 1)
        sleep(self.wait)
        gpio.output(self.D, 0)

    def step2(self):
        gpio.output(self.D, 1)
        gpio.output(self.C, 1)
        sleep(self.wait)
        gpio.output(self.D, 0)
        gpio.output(self.C, 0)

    def step3(self):
        gpio.output(self.C, 1)
        sleep(self.wait)
        gpio.output(self.C, 0)

    def step4(self):
        gpio.output(self.C, 1)
        gpio.output(self.B, 1)
        sleep(self.wait)
        gpio.output(self.C, 0)
        gpio.output(self.B, 0)

    def step5(self):
        gpio.output(self.B, 1)
        sleep(self.wait)
        gpio.output(self.B, 0)

    def step6(self):
        gpio.output(self.B, 1)
        gpio.output(self.A, 1)
        sleep(self.wait)
        gpio.output(self.B, 0)
        gpio.output(self.A, 0)

    def step7(self):
        gpio.output(self.A, 1)
        sleep(self.wait)
        gpio.output(self.A, 0)

    def step8(self):
        gpio.output(self.A, 1)
        gpio.output(self.D, 1)
        sleep(self.wait)
        gpio.output(self.A, 0)
        gpio.output(self.D, 0)
            
    def turn(self, angle):
        self.steps = 0
        self.max_steps = int(float(angle)*512/360*27)  # 512 steps for one rotation at stepper motor times 27 due to gearbox
        rotations = self.rotations + float(angle)/360
        if rotations <= 0 or rotations >= 17.5:
            return
        else:
            self.rotations = rotations
            self.t = threading.Thread(target=self._rotate)
            self.t.start()
                
    def get_max_steps(self):
        return self.max_steps
        
    def get_steps(self):
        return self.steps
                    
    def _rotate(self):
        print 'rotating'
        if self.max_steps > 0:
            for i in np.arange(self.max_steps):
                if self.stop:
                    break
                for s in self.sequence:
                    s()
                self.steps = i
        else:
            for i in np.arange(-1*self.max_steps):
                if self.stop:
                    break
                for s in self.sequence[::-1]:
                    s()
                self.steps = i
        self.stop = False
        self.max_steps = 0

    def set_operation_mode(self, mode):
        """ 0 for full step mode (rougher but faster)
            1 for half step mode
        """
        # if mode == 0:
            # self. sequence = [self.step2, self.step4, self.step6, self.step8]
        if mode == 1:
            self.sequence = [self.step1, self.step2, self.step3, self.step4,
                             self.step5, self.step6, self.step7, self.step8]
        else:
            print 'wrong input'
                
    def stop_rotation(self):
        # ToDo: implement correct tracking in case code is used directly on raspi
        self.stop = True

    def get_operation_mode(self):
        if len(self.sequence) == 8:
            return 'half-step'
        elif len(self.sequence) == 4:
            return 'full-step'
        else:
            return 'Error'
            
    def set_waiting_time(self, waiting_time):
        """controls the speed"""
        self.wait = waiting_time

    def get_waiting_time(self):
        return self.wait

    def get_connection(self):
        return True


if __name__ == '__main__':
    s = zerorpc.Server(StepMotor())
    s.bind("tcp://0.0.0.0:4242")
    s.run()
