# wrapper for TwoPortSwitch_RT by JB@KIT 04/2015 jochen.braumueller@kit.edu
# two port switch at room temperature to in situ (re)calibrate the qubit manipulation IQ-mixer
# model: Raspberry Pi running Raspian, Radiall Switch R572.432.000 (latching, no 50Ohms termination at open port) integrated in rack slot
# use: connect mixer output line to 'C', switchable connectors 1,2 to the inlet of the cryostat and the spectrum analyzer

from instrument import Instrument
import instruments
import types
import logging
#import numpy as np
import time,sys
import socket
import sys

class TwoPortSwitch_RT(Instrument):

	def __init__(self, name, host='pi-us83', port=9988):

		Instrument.__init__(self, name, tags=['physical'])
		
		self.add_parameter('position',
			type=types.FloatType,
			flags=Instrument.FLAG_GETSET)
			
		self.HOST, self.PORT = host, port

	def do_set_switch(self, position):
		if position == '1' or position == '2':
			try:
				# Create a socket (SOCK_STREAM means a TCP socket)
				sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				#connect
				sock.connect((self.HOST, self.PORT))
				sock.sendall('switch ' + str(position) + '\n')
				#receive confirmation from server and shut down connection
				rec = sock.recv(1024)
				sock.close()
			except Exception as detail:
				print "Error: ", detail
				return 0
			
			if rec == 'ok':   #switching successful
				return True
			else:
				return False
			
		else:
			print 'invalid given switch setting...no action'
			return False
			
	def do_get_switch(self):
		try:
			# Create a socket (SOCK_STREAM means a TCP socket)
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			#connect
			sock.connect((self.HOST, self.PORT))
			sock.sendall('get_position' + '\n')
			#receive data from the server and shut down connection
			rec = sock.recv(1024)
			sock.close()
			return rec
		except Exception as detail:
			print "Error: ", detail
			return 0
 