# two_port_switch_manual_client.py by JB@KIT 04/2015 jochen.braumueller@kit.edu
# client script to be run on the control machine (Raspberry Pi) to enable manual switching
# use: execute after starting the server

import socket
import sys
from time import sleep

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)   #use RPi.GPIO layout

BUT1 = 13   #gpio27
BUT2 = 15   #gpio22   #button inputs
GPIO.setup(BUT1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUT2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)   #connect buttons to +Vcc=3.3V

HOST, PORT = 'pi-us83', 9988

def button1():
	return GPIO.input(BUT1) == 1
def button2():
	return GPIO.input(BUT2) == 1

if __name__ == "__main__":

	data = ''
	while True:
		if button1():
			data = 'switch 1'
		if button2():
			data = 'switch 2'
		if data != '':
			try:
				# Create a socket (SOCK_STREAM means a TCP socket)
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				# Connect to server and send data
				sock.connect((HOST, PORT))
				sock.sendall(data + "\n")
				# Receive data from the server and shut down
				received = sock.recv(1024)
			finally:
				print data
				data = ''
				sock.close()
				sleep(1)