# 
# Copyright (C) 2011 Martijn Schaafsma
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import _ftd2xx as f
from _ftd2xx.defines import *
from time import sleep

from instrument import Instrument
import types
import logging

class ThorlabsFTD2XX(Instrument):

  def __init__(self,name, HWSerialNumber='83828433', StageType='PRM1MZ8'):

    logging.info(__name__ + ' : Initializing instrument Thorlabs driver')
    Instrument.__init__(self, name, tags=['physical'])
    
    # TODO: Fix when device is already initialized and driver is reloaded!!
    # Obtain handle from driver itself

    try:
      L = f.listDevices()
    except f.DeviceError:
      print "No active devices!!"
      L = ['None']

    print L
    
    if '83828433' in L:
      self.g = f.openEx('83828433')
    else:
      # Alternative load
      f.createDeviceInfoList()
      t = f.getDeviceInfoDetail()
      if '83828433' == t['serial']:
        h = t['handle']
        H = h.value
        self.g = f.FTD2XX(H)
    
    
    self.g.setBaudRate(115200)
    self.g.setDataCharacteristics(f.defines.BITS_8, f.defines.STOP_BITS_1, f.defines.PARITY_NONE)

    sleep(0.2)
    self.g.purge(f.defines.PURGE_RX | f.defines.PURGE_TX)
    sleep(0.2)

    self.g.resetDevice()
    self.g.setFlowControl(f.defines.FLOW_RTS_CTS,0,0)
    self.g.setRts()
    
    # Add functions
    self.add_function('Identify')
    self.add_function ('GoHome')
    self.add_function ('Close')
    self.add_function ('StopMoving')
    self.add_function ('EnableChannel1')
    self.add_function ('DisableChannel1')
    self.add_function ('MoveJogPos')
    self.add_function ('MoveJogNeg')
    self.add_function ('MoveRelative')
    self.add_function ('ReturnStatus')

    # Add parameters
    self.add_parameter('Position',
      flags=Instrument.FLAG_GETSET, units='deg', minval=-720, maxval=720, type=types.FloatType)    
    self.add_parameter('IsMoving',
      flags=Instrument.FLAG_GET, type=types.BooleanType)    
    

    self.status = {}
    self.get_Position()

    
#  def __del__(self):
#    print "Bye!!"
#    self.g.close()
#  Fixme: release handle
    
  def Identify(self):
    self.g.write("\x23\x02\x00\x00\x50\x01")

  def GoHome(self):
    self.g.write("\x43\x04\x01\x00\x50\x01")

  def Close(self):
    self.g.close()
    
  def ReadBuffer(self):
    n = self.g.getQueueStatus()
    return self.g.read(n)
    
  def StatusbytesToPosition(self, blist):
    ## Add stuff to analyse the statusbits and return a dict
    status = {}
    
    pos = ord(blist[8]) + 256*ord(blist[9]) + 256*256*ord(blist[10]) + 256*256*256*ord(blist[11])
    status1 = ord(blist[16])
    status2 = ord(blist[17])
    status3 = ord(blist[18])
    status4 = ord(blist[19])
    
    status['pos']=pos
    
    if status1%2>0:
      status['CW_HW_lim'] = True
      pass
    else:
      status['CW_HW_lim'] = False
      pass
    if status1%4>1:
      status['CCW_HW_lim'] = True
      pass
    else:
      status['CCW_HW_lim'] = False
      pass
    if status1%8>2:
      status['CW_SW_lim'] = True
      pass
    else:
      status['CW_SW_lim'] = False
      pass
    if status1%16>4:
      status['CCW_SW_lim'] = True
      pass
    else:
      status['CCW_SW_lim'] = False
      pass
    if status1%32>8:
      status['Moving_CW'] = True
      pass
    else:
      status['Moving_CW'] = False
      pass
    if status1%64>16:
      status['Moving_CCW'] = True
      pass
    else:
      status['Moving_CCW'] = False
      pass
    if status1%128>32:
      status['Jogging_CW'] = True
      pass
    else:
      status['Jogging_CW'] = False
      pass
    if status1%256>64:
      status['Jogging_CCW'] = True
      pass
    else:
      status['Jogging_CCW'] = False
      pass
    
    if status2%2>0:
      status['Connected'] = True
      pass
    else:
      status['Connected'] = False
      pass
    if status2%4>1:
      status['Homing'] = True
      pass
    else:
      status['Homing'] = False
      pass
    if status2%8>2:
      status['Homed'] = True
      pass
    else:
      status['Homed'] = False
      pass
    if status2%16>4:
      status['Misc'] = True
      pass
    else:
      status['Misc'] = False
      pass
    if status2%32>8:
      status['Interlock'] = True
      pass
    else:
      status['Interlock'] = False
      pass
    self.status = status  
    return status
    
  def ReturnStatus(self):
    return self.status  

  def do_get_IsMoving(self):
    self.ReadBuffer()
    self.g.write('\x90\x04\x01\x00\x50\x01')
    sleep(0.1)
    while(self.g.getQueueStatus()==0): # This is dangerous!!
      sleep(0.5)
    stat = (self.StatusbytesToPosition(self.ReadBuffer()))
    return (stat['Moving_CW'] or stat['Moving_CCW'])
    
  def do_get_Position(self):  
    self.ReadBuffer()
    self.g.write('\x90\x04\x01\x00\x50\x01')
    sleep(0.1)
    while(self.g.getQueueStatus()==0): # This is dangerous!!
      sleep(0.5)
    valold = (self.StatusbytesToPosition(self.ReadBuffer()))['pos']      
    if valold >= 2147483648:
      val = (valold-4294967296)/1920.0    
    else:  
      val = valold/1920.0    
    return val

  def do_set_Position(self,pos):
    num = int(pos*1920)
    byte1 = num%256
    byte2 = int(num/256)%256
    byte3 = int(num/256/256)%256
    byte4 = int(num/256/256/256)%256
    str = '\x53\x04\x06\x00\x80\x01\x01\x00' + chr(byte1) + chr(byte2) + chr(byte3) + chr(byte4)      
    self.g.write(str)
    
  def MoveRelative(self,move):
    num = int(move*1920)
    byte1 = num%256
    byte2 = int(num/256)%256
    byte3 = int(num/256/256)%256
    byte4 = int(num/256/256/256)%256
    str = '\x48\x04\x06\x00\x80\x01\x01\x00' + chr(byte1) + chr(byte2) + chr(byte3) + chr(byte4)      
    self.g.write(str )
    
  def StopMoving(self):
    self.g.write('\x65\x04\x01\x02\x50\x01')
    
  def EnableChannel1(self):
    self.g.write('\x10\x02\x01\x01\x50\x01')
    
  def DisableChannel1(self):
    self.g.write('\x10\x02\x01\x01\x50\x01')
    
  def MoveJogPos(self):
    self.g.write('\x6A\x04\x01\x02\x50\x01')
    
  def MoveJogNeg(self):
    self.g.write('\x6A\x04\x01\x02\x50\x01')
