from lib_oled96 import ssd1306
from PIL import ImageFont
from smbus import SMBus
import logging
import numpy as np

i2cBus = SMBus(1)
oled = ssd1306(i2cBus)
draw = oled.canvas

fnt = ImageFont.truetype('FreeMonoBold.ttf', 17)

width = 16
height = 16
pos = [[], [4, 26], [24, 26], [44, 26], [4, 46], [24, 46], [44, 46]]


def draw_line():
    draw.rectangle((63, 0, 65, 64), outline=1, fill=1)


def draw_config(switch, config):
    add = 64 if switch == 1 else 0
    draw.text((5 + add, 5), "Sw: " + "AB"[switch], fill=1, font=fnt)
    for i in range(1, 7):
        fill = config[i - 1]
        if fill is None:
            draw.rectangle((pos[i][0] + add, pos[i][1], pos[i][0] + width + add, pos[i][1] + height), outline=1, fill=0)
            draw.text((pos[i][0] + 3 + add, pos[i][1] - 1), "?", fill=1, font=fnt)
        else:
            draw.rectangle((pos[i][0] + add, pos[i][1], pos[i][0] + width + add, pos[i][1] + height), outline=fill, fill=fill)
            draw.text((pos[i][0] + 3 + add, pos[i][1] - 1), str(i), fill=not fill, font=fnt)


import RPi.GPIO as GPIO
import time
from threading import Lock

# Set GPIO Mode
GPIO.setmode(GPIO.BOARD)

# GPIO Setup Pins
GPIO_OpAmp = 29  # OpAmp Signal
GPIO_SigInv = 31  # Invert polarity. Inverted when PIN is OFF!
PINS = [[32, 33, 36, 35, 38, 40], [7, 11, 12, 15, 16, 18]]
GPIO_ComGnd = 22  # Switch common Ground connection On/Off

# Set direction of GPIO Ports
for P in [GPIO_OpAmp, GPIO_SigInv, GPIO_ComGnd] + PINS[0] + PINS[1]:
    GPIO.setup(P, GPIO.OUT)


class Switch(object):
    def __init__(self):
        self._sw_pos = [[None] * 6, [None] * 6]
        self._pulse_len = [.08] * 2
        self._sleep_time = .2
        self._lock = Lock()
        self._update_display()
    
    def _pulse(self, switch, port, invert=False):
        with self._lock:
            if GPIO.input(GPIO_OpAmp):
                raise ValueError("OpAmp still enabled!")
            #GPIO.output(GPIO_ComGnd, True)
            GPIO.output(PINS[switch][port], True)
            GPIO.output(GPIO_SigInv, not invert)
            time.sleep(self._sleep_time)
            
            GPIO.output(GPIO_OpAmp, True)
            time.sleep(self._pulse_len[switch])
            GPIO.output(GPIO_OpAmp, False)
            
            time.sleep(self._sleep_time)
            GPIO.output(PINS[switch][port], False)
            GPIO.output(GPIO_SigInv, False)
            # Common ground is not switched off here.
            # GPIO.output(GPIO_ComGnd, False)
    
    def disable(self, switch, port):
        self._pulse(switch, port, True)
        self._sw_pos[switch][port] = False
        self._update_display()
    
    def enable(self, switch, port):
        self._pulse(switch, port, False)
        self._sw_pos[switch][port] = True
        #GPIO.output(GPIO_ComGnd, False)
        self._update_display()
    
    def switch_to(self, switch, port):
        if None in self._sw_pos[switch]:
            logging.warning("Not all switch positions are known for switch {0}. If you can tolerate heating, please use .reset_all(switch={0}).".format(switch))
        for i in np.where(self._sw_pos[switch])[0]:
            self.disable(switch, i)
        self.enable(switch, port)
    
    def reset_all(self, switch=None):
        if switch is None:
            self.reset_all(0)
            self.reset_all(1)
        else:
            for i in range(6):
                self.disable(switch, i)
            GPIO.output(GPIO_ComGnd, False)
        self._update_display()
    
    def get_switch_position(self, switch):
        return list(np.where(self._sw_pos[switch])[0])
    
    def set_pulse_length(self, length, switch=None):
        if switch is None:
            self._pulse_len = [length] * 2
        elif switch in [0, 1]:
            self._pulse_len[switch] = length
        else:
            raise ValueError("Only switch 0 or 1 are valid.")
    
    def get_pulse_length(self):
        return self._pulse_len
    
    def _update_display(self):
        oled.cls()
        draw_line()
        draw_config(0, self._sw_pos[0])
        draw_config(1, self._sw_pos[1])
        oled.display()
    
    def __del__(self):
        oled.cls()
        draw.text((20, 10), "SERVER", fill=1, font=fnt)
        draw.text((20, 25), "DOWN", fill=1, font=fnt)
        oled.display()
