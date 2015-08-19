import SocketServer

import os,sys
sys.path.append('../')
from EdwardsBridgeReadout import Edwards_p_gauge   #import readout class

p = Edwards_p_gauge()

class TCPHandler_Edwards(SocketServer.BaseRequestHandler):
	"""
	The RequestHandler class for our server.

	It is instantiated once per connection to the server, and must
	override the handle() method to implement communication to the
	client.
	"""

	def handle(self):
		try:
			# self.request is the TCP socket connected to the client
			self.data = self.request.recv(1024).strip()
			if str(self.data) == 'get_p_cond':
				print 'condenser line pressure request from', str(format(self.client_address[0]))
				self.request.sendall(str(p.get_condenser_pressure()))
			elif str(self.data) == 'get_p_still':
				print 'still line pressure request from', str(format(self.client_address[0]))
				self.request.sendall(str(p.get_still_pressure()))
			else:
				print 'request string not recognized'
				self.request.sendall(0)
		except Exception as m:
			print 'Error in TCP server handler:', m

if __name__ == "__main__":
	HOST, PORT = 'pi-us74', 9955

	# Create the server, binding to localhost on port 9955
	server = SocketServer.TCPServer((HOST, PORT), TCPHandler_Edwards)

	# Activate the server; this will keep running until you
	# interrupt the program with Ctrl-C
	server.serve_forever()

