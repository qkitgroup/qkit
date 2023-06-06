# fridge_monitoring.py by JB@KIT 06/2014
# script for monitoring UFO temperature
# edits 08/2015, 05/2017
# the critical temperature in mK is passed as an argument

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

from sendMail import *
from tip_client import tip_client
import time
from numpy import mean
from numpy import abs
import sys


def _sendTemp(temp):
    
    strTime = time.strftime('%x %X')

    s = SendMail("UFO@kit.edu",strTime+" UFO monitoring")   #sender, subject
    
    s.setRecipients("")
    #s.add_Line("Hello, I am feeling great. Cool gases. Nice pressures.")
    s.add_Line(strTime)
    s.add_Line("Current base temperature: " + str(temp) + " mK")
    s.add_Line("")
    s.add_Line("Please reflect the above given value critically and make sure to interpret it in the right way.")
    s.add_Line("")
    s.add_Line("Best, UFO")
    
    s.sendEMail()
    print "Mail sent to recipients. Current base temperature: " + str(temp) + "."
    
    
def _getTemp(t):
    try:
        return round(float(t.r_get_T())*1000,2)   #T in mK
    except Exception as m:
        print 'Could not retrieve temperature', m
        return 0
    
def _parameters_critical(t,b,temp_critical):
    #returns True if a message is to be sent, False otherwise
    if b_mean > temp_critical and abs(b[-1]-b[-2]) < 15:   #if mean value of last [10] minutes > 35mK and the increase smooth
        if b[-2] > b[-1] or b[-1] < temp_critical:   #if temperature is decreasing
            return False
        else:
            return True
    else:
        return False


if __name__ == "__main__":
    
    t = tip_client('tip',address='pi-us74')   #tip raspberry
    
    # readout critical temperature argument
    if len(sys.argv) == 1:   #no argument passed -> set default 35mK
        temp_critical = 35
    else:
        temp_critical = float(sys.argv[1])   #in mK
    
    buffer = []
    for i in range(10):
        buffer.append(18.0)
    m_sent = False
    while True:
    time.sleep(59)
    if int(time.strftime('%M')) == 0:   #every full hour
        m_sent = False
    
    buffer.append(_getTemp(t))
    buffer = buffer[1:]
    b_mean = mean(buffer)
    print b_mean
    if _parameters_critical(t,buffer,temp_critical) and m_sent == False:   #if base T > 25mK
        _sendTemp(_getTemp(t))
            m_sent = True
            