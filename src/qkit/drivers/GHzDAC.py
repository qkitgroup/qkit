# This is the qtlab driver for Martinis' GHzDAC devices.
# It interfaces to a local or remote instance of the EthernetServer instrument to communicate with the pysical device.
# Markus Jerger <jerger@kit.edu>, 2011
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

# TO DO
#
#

from qkit.core.instrument_base import Instrument
import types
import logging
# comms and byte packing
import ctypes
import socket
import dpkt
import struct
import numpy
# waiting
import time

class GHzDAC(Instrument):
    '''
    This instrument controls a GHzDAC device via the EthernetServer instrument.

    Usage:
    Initialize with
    <name> = qt.instruments.create('name', 'GHzDAC', MAC=<mac>, ip_host=<ip_host>, ip_port=<ip_port>)
    <mac> = MAC address of the device, 00:01:CA:AA:00:XX, where XX is determined by dip switches on the device
    <ip_host>:<ip_port> = 127.0.0.1:413 the EthernetServer instance to connect to
    '''

    # maximum packet size
    RECV_SIZE = 2048
    # device properties
    SRAM_SIZE = 2**13

    def __init__(self, name, MAC, ip_host = '127.0.0.1', ip_port = 413, ip_timeout = 10.):
        '''
        Initializes the Oxford Instruments Kelvinox IGH Dilution Refrigerator.

        Input:
            name (string) : name of the instrument
            MAC (string) : MAC address of the target device
            ip_host:ip_port : UDP interface address of an EthernetServer 

        Output:
            None
        '''
        logging.debug(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical'])

        self.do_set_MAC(MAC)
        self._ip_host = ip_host
        self._ip_port = int(ip_port)
        self._ip_timeout = float(ip_timeout)

        # add parameters
        self.add_parameter('MAC', type=str, flags=Instrument.FLAG_GETSET)
        self.add_parameter('ip_host', type=str, flags=Instrument.FLAG_GET)
        self.add_parameter('ip_port', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('ip_timeout', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('rcvbuf', type=int, flags=Instrument.FLAG_GETSET)
        self.add_function('get_regfile')
        self.add_function('set_regfile')
        self.add_function('set_sram')
        self.add_function('get_all')
        self.add_function('seq_start')
        self.add_function('seq_stop')
        self.add_function('seq_single')
        self.add_function('seq_loop')

        # open sockets
        self._init_udp()

        # initialize hardware
        self._reg = None
        self.init_pll()
        self.init_dac(0, signed = True)
        self.init_dac(1, signed = True)
        
        # trigger register readback
        self._reg = None
        self.update_regfile()

        # update ui
        self.get_all()

    def __del__(self):
        ''' clean up '''
        pass

    def _init_udp(self):
        ''' open udp socket to EthernetServer '''
        logging.debug(__name__ + ' : Connecting to %s:%d.'%(self._ip_host, self._ip_port))
        self._udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._udp_socket.settimeout(self._ip_timeout)
        self._udp_socket.connect((self._ip_host, self._ip_port))

    def get_all(self):
        ''' call all getters to update the ui '''
        self.get_MAC()
        self.get_ip_host()
        self.get_ip_port()
        self.get_ip_timeout()
        self.get_rcvbuf()

    #
    # data structures
    #

    class sram_write:
        '''
        write-to-sram packet
        '''
        def __init__(self, addr_start, samples, markers = None):
            '''
            create new sram write packet

            Input:
                addr_start - first write address
                samples, markers - initializers; see pack_samples
            '''
            self.addr_start = addr_start
            self.samples = (256*ctypes.c_uint32).from_buffer(self.pack_samples(samples, markers).data)

        def pack_samples(self, channels, markers = None):
	        '''
	        pack sample data into 32bit ints

	        In the current hardware, each analog channel has a resolution of 14bits 
	        and each marker has a resolution of one bit.

	        Input:
		        channels - 2xN array of integers
		        markers  - 4xN array of bools
	        Output:
		        N array of packet samples
	        '''
	        if len(channels) != 2:
		        print 'pack_samples requires exactly 2 analog channels'
	        if (markers != None) and (len(markers) != 4):
		        print 'pack_samples requires exactly 4 marker channels'
	        channels = numpy.array(channels, numpy.uint32)
	        samples =  (channels[0,:] & 0x00003FFF)
	        samples |= (channels[1,:] & 0x00003FFF) << 14
	        if(markers != None):
		        markers = numpy.array(markers, numpy.uint32)
		        samples |= (1<<31)*markers[0] + (1<<30)*markers[1] + (1<<29)*markers[2] + (1<<28)*markers[3]
	        return samples

        def pack(self):
            ''' return string reprentation of this sram write packet '''
            if(len(self.samples) != 256):
                logging.warning(__name__ + ' : number of samples per packet must be 256.')
            return struct.pack('<H256I', self.addr_start, *self.samples)

    class regfile:
        '''
        GHZdac register file

        r/w:
            sequencer - SEQ_* sequencer mode
            readback - REG_* readback mode
            i2c_stop, i2c_rw, i2c_ack_tx - unknown I2C stuff
            i2c_data_tx - unknown array of 7 I2C data bytes
            registers - array of 30 register bytes
            slave - daisy-chain master/slave select
            delay - start delay, in ns?, 8bit
            sync - master start delay, in 4ns clock cycles
            daclk - DACLK_* d/a converter clocking flags
            serial_tx - unknown, 32 bits
        r/o:
            build - FPGA code build number
            memsum - memory checksum (all zeros)
            serial_rx - byte received from serial DAC interface
            clkmon - clock status
        '''
        # constants
        # register file packet size
        SIZE_TX = 56+14
        SIZE_RX = 70+14

        # sequencer starting mode
        SEQ_STOP = 0x0
        SEQ_MEMORY = 0x1
        SEQ_TEST = 0x2
        SEQ_LOOP = 0x3 # stop with SEQ_SINGLE or SEQ_STOP
        SEQ_SINGLE = 0x4
        SEQ_PAGE0 = 0x00
        SEQ_PAGE1 = 0x80

        # register readback mode
        REG_NOREADBACK = 0x00 	# no readback
        REG_READDELAY = 0x01 	# readback after 2us
        REG_READI2C = 0x02	# readback synchronized to I2C
        REG_READSTREAM = 0x03	# continuous readback (stream timing data)

        # D/A converter clocking
        DACLK_A_EN = 0x10
        DACLK_B_EN = 0x20
        DACLK_A_INV = 0x01
        DACLK_B_INV = 0x02
        DACLK_RESET = 0x80

        # r/w registers
        sequencer = SEQ_STOP
        readback = REG_NOREADBACK
        i2c_stop = 0x0
        i2c_rw = 0x0
        i2c_ack_tx = 0x0
        i2c_data_tx = numpy.zeros(8, numpy.uint8)
        registers = numpy.zeros(30, numpy.uint8)
        slave = False
        delay = 0
        sync = 0
        daclk = DACLK_A_EN | DACLK_B_EN
        serial_tx = 0x00000000
        # r/o registers
        build = None
        memsum = None
        sermon = None
        serial_rx = None
        clkmon = None
        i2c_ack_rx = None
        i2c_data_rx = None
	
        def __init__(self, **kwargs):
	        '''
	        initialize object, copying keyword args into properties of the same name
	        '''
	        for key, value in kwargs.iteritems():
		        if hasattr(self, key):
			        setattr(self, key, value)
		        else:
			        print 'reg: unsupported property %s'%key

        def pack(self):	
	        '''
	        update device registers

	        Output:
		        ethernet packet type number and payload string
	        '''
	        i2c_data_tx = str(numpy.array(self.i2c_data_tx, numpy.uint8).data)
	        registers = str(numpy.array(self.registers, numpy.uint8).data)
	        slave = numpy.uint8(self.slave)
	        length = 56
	        payload = struct.pack(
		        '<BB BBB8s 30s BBBB i xxxxx', 
		        self.sequencer, self.readback, 
		        self.i2c_stop, self.i2c_rw, self.i2c_ack_tx, i2c_data_tx, 
		        registers, 
		        slave, self.delay, self.sync, self.daclk,
		        self.serial_tx
	        )
	        return (length, payload)

        def unpack(self, payload):
	        '''
	        parse register file sent by device

	        Input:
		        payload of a register readback packet sent by the device
	        '''
	        (
		        self.sequencer, self.readback, 
		        self.i2c_stop, self.ic2c_rw, self.i2c_ack_tx, i2c_data_tx, 
		        registers,
		        slave, self.delay, self.sync, self.daclk, 
		        self.serial_tx,
		        self.build, self.memsum, self.serial_rx, self.sermon, self.clkmon,
		        self.i2c_ack_rx, i2c_data_rx
	        ) = struct.unpack( '<BB BBB8s 30s BBBB I BIBBB xx B8s', payload)
	        self.registers = numpy.fromstring(registers, numpy.uint8)
	        self.i2c_data_tx = numpy.fromstring(i2c_data_tx, numpy.uint8)
	        self.i2c_data_rx =  numpy.fromstring(i2c_data_rx, numpy.uint8)

        def __str__(self):
	        '''
	        return string representation of self
	        '''
	        props = []
	        for prop in dir(self): 
		        if not callable(getattr(self, prop)):
			        props += ['%s: %s'%(prop, getattr(self, prop))]
	        return '\n'.join(props)

    #
    # communication-related parameters
    #

    def do_set_MAC(self, MACin):
        '''
            convert mac address to byte string
            expected input format is 01:23:45:67:89:AB
        '''
        # split input and convert the parts to ints
        MAC = [int(byte, base = 16) for byte in str(MACin).split(':')]
        # merge the parts into a byte string
        self._MAC = struct.pack('>6B', *MAC)

    def do_get_MAC(self):
        ''' return device MAC address '''
        return '%02x:%02x:%02x:%02x:%02x:%02x'%(struct.unpack('>6B', self._MAC))
 
    def do_get_ip_host(self):
        ''' return hostname of the udp socket '''
        return self._ip_host

    def do_get_ip_port(self):
        ''' return port number of the udp socket '''
        return self._ip_port

    def do_set_ip_timeout(self, timeout):
        ''' set timeout for socket operations '''
        self._ip_timeout = timeout
        self._udp_socket.settimeout(timeout)

    def do_get_ip_timeout(self):
        ''' get timeout for socket operations '''
        return self._udp_socket.gettimeout()

    def do_set_rcvbuf(self, bufsize):
        ''' set the receive buffer size of the raw socket '''
        self._udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, int(bufsize))

    def do_get_rcvbuf(self):
        ''' get the receive buffer size of the raw socket '''
        return self._udp_socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    #
    # device initialization
    #
    def SPI(self, sel, sequence):
        '''
        send a sequence of words over the SPI bus
        the PLL and DACs are connected to SPI

        Input:
            sel - hardware to send to (1: PLL, 2: DAC A, 3: DAC B)
            sequence - sequence of 24bit words to transmit
        '''
        reg = self._reg if (self._reg != None) else self.regfile()
        result = []
        for data in sequence:
            reg.serial_tx = (data << 8) | sel
            self.update_regfile(reg)
            result += [self._reg.serial_rx]
            time.sleep(0.01)
        reg.serial_tx = 0
        return result


    def init_pll(self):
        '''
        program AD4107 PLL to generate 1GHz output clock for the DACs and digital outputs

        setup:
	        prescaler P=8
	        clk/ref ratio = 100 = (P*B+A)/R
	        choosing R=1, B=12, A=4
        latches:
	        24bit values, last two bits are latch selection (C2, C1)
	        (1, 1) initialize  = 	0x1fc093
	        (1, 0) function = 	0x1fc092 (negative pd polarity, output lock detect on mux, high current out)
	        (0, 0) R = 		0x000004 (14bit R)
	        (0, 1) N = 		0x000C11 (13bit B, 3..8191), (6 bit A), high precision
        sequence:
	        initialize, function, R, N

        Output:
	        an array of 32bit values to place into GHZdac serial registers
        '''
        #return [0x00008301, 0x00008201, 0x10000401, 0x000C1101, 0x00009201]
        sel = 0x01 # PLL
        seq = [0x1FC093, 0x1FC092, 0x100004, 0x000C11]
        self.SPI(sel, seq)

    def init_dac(self, channel, signed = True):
        '''
        program ADxxxx DAC

        Input:
            channel number - integer (0 or 1)
            signed - dac input signed/unsigned flag
        '''
        seq = [0x000024, 0x000004, 0x001603, 0x000500] if signed else \
              [0x000026, 0x000006, 0x001603, 0x000500] # 0x050000 
        sel = 0x02 + channel
        self.SPI(sel, seq)

    def init_lvds(self, channel):
        '''
            calibrate LVDS receivers in the DACS to the center of the data eye
            the calibration procedure is found in the AD9736 data sheet
            and Martinis' control software

        Input:
            channel number - 0 or 1
        '''
        op = 2+channel # SPI operation code for DAC operation

        # vary delay until we hit a clock edge
        seq = lambda t: [0x000500 + 0x10*t, 0x008700] # adjust lvds delay
        # change of status indicates that we cross a clock edge
        t = 0
        stat0 = self.SPI(op, seq(t))[1]
        while True:
            t += 1
            if(t == 16):
                logging.error(__name__ + ' : failed to find DAC clock edge')
                return False
            stat1 = self.SPI(op, seq(t))[1]
            if(stat0 != stat1): break
        logging.debug(__name__ +  ' : clock edge at %d.'%t)
        self.SPI(op, seq((t+1) % 16))
        time.sleep(0.05)

        # adjust fifo counter to half-full
        seq = [0x0700, 0x8700, 0x0701, 0x8700, 0x0702, 0x8700, 0x0703, 0x8700]
        stat = self.SPI(op, seq)
        stat = [(stat[i] >> 4) & 0x0f for i in [1, 3, 5, 7]]
        # optimum read counter value is 3
        delay = numpy.argmin(numpy.abs(numpy.array(stat)-3))
        seq = lambda t: [0x0700 + 0x10*t, 0x8700]
        self.SPI(op, seq(delay))
        if(stat[delay] != 3):
            logging.error(__name__ + ' : failed to set fifo read counter to 3.')
            return False
        return True

    #
    # device configuration
    #
    def update_regfile(self, reg = None):
        '''
        transmit the current or an empty register file to the device and request register readback
        '''
        if(reg == None): reg = self._reg if (self._reg != None) else self.regfile()
        reg.readback = self.regfile.REG_READDELAY
        self.set_regfile(reg)

    def get_regfile(self):
        '''
        return buffered register file
        '''
        return self._reg

    def set_regfile(self, reg):
        '''
        transmit a register file packet to the device
        '''
        self._reg = reg
        length, payload = reg.pack()
        packet = dpkt.ethernet.Ethernet(dst = self._MAC, type = length, data = payload)
        self._udp_socket.send(packet.pack())
        if(reg.readback == self.regfile.REG_READDELAY):
            reg = self.read_regfile()
            if(reg != None): self._reg = reg

    def read_regfile(self):
        '''
        wait for a register readback packet
        '''
        try:
            packet_raw = self._udp_socket.recv(self.RECV_SIZE)
        except Exception as e:
            logging.error(__name__ + ' : register readback failed. reason: %s.'%(e))
            return None
        # basic sanity checks
        if(len(packet_raw) != self.regfile.SIZE_RX):
            logging.error(__name__ + ' : register readback from %s has unexpected length %d.'%(self.do_get_MAC(), len(packet_raw)))
            return None
        packet = dpkt.ethernet.Ethernet(packet_raw)
        if(packet.src != self._MAC):
            logging.error(__name__ + ' : register readback MAC address does not match.')
            return None
        # parse register file
        reg = self.regfile()
        reg.unpack(packet.data)
        return reg

    def set_sram(self, addr_start, samples, markers = None):
        '''
        send write-to-sram packet to the device 
        '''
        if(addr_start >= self.SRAM_SIZE):
            print 'sram_write: start address must be smaller than sram memory size'
        payload = self.sram_write(addr_start, samples, markers).pack()
        packet = dpkt.ethernet.Ethernet(dst = self._MAC, type = len(payload), data = payload)
        self._udp_socket.send(packet.pack())

    def seq_start(self):
        self._reg.sequencer = self._reg.SEQ_START
        self.update_regfile()
    def seq_stop(self):
        self._reg.sequencer = self._reg.SEQ_STOP
        self.update_regfile()
    def seq_single(self):
        self._reg.sequencer = self._reg.SEQ_SINGLE
        self.update_regfile()
    def seq_loop(self):
        self._reg.sequencer = self._reg.SEQ_LOOP
        self.update_regfile()
