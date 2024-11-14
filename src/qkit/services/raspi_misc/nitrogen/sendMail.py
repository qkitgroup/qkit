#-------------------------------------------------------------------------------
# Name:        SendMail
# Purpose:     Sends an eMail with topic, a message and an png-File as
#              attachment to several recipients.
#
# Author:      A.Tkalcec    (andrej.tkalcec@gmail.com)
# modified:    J. Braumueller (20.06.2014)
#
# Created:     08.02.2013
#-------------------------------------------------------------------------------

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


import smtplib
import time,os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

class SendMail(object):

    def __init__(self, source, subject):
        # Source = Name of the transmitter ["string"] shoud be in eMail
        # format like: xy@email.com (eMail does not have to exist)
        self.Source = source
        # Subject = Topic, information of the message, needs to be an array: ["string"]
        self.Subject = subject
        self.Recipients = "[jochen.braumueller@kit.edu]"
        self.Msg = MIMEMultipart()
        # For "single-line" messages
        self.lineList = []
        # To attach several images
        self.imgList = []
        #path to recipients.txt
        self.rptsPath = os.getcwd() + "/recipients.txt"
        
        
    def setRecipientsDir(self,rptsPath = os.getcwd() + "/recipients.txt"):
        self.rptsPath = rptsPath

    def setRecipients(self, rpts = ""):
 
        strTime = time.strftime('%X %x')
        if rpts != "":   #recipient specified
            try:
                self.Recipients = [rpts]
            except:
                print strTime + " sendMail: invalid recipient"
        else:   #use recipients.txt
            try:
                f1 = open(self.rptsPath, 'r')
                rpts_lines = f1.readlines()
                f1.close()
                self.Recipients = [l.strip() for l in rpts_lines]   #strip off \n
            except:
                print strTime + " sendMail: Failed to open or read recipients.txt"
            
    def add_txt_file(self, mesgPath):
        
        # mesgPath = Path of a TXT-File with the incl. information
        # Opens a plain text file for reading (ASCII)
        strTime = time.strftime('%X %x')
        try:
            f2 = open(mesgPath, 'rb')
            # Create a text/plain message
            self.lineList.append(f2.read())
            f2.close()
            # Create the body of the message.
        except IOError:
            print strTime+" sendMail: Faild to open or read txt-file for message!"
            self.add_Line("Faild to open or read txt-file for message!")


    def setImage(self, imgPath):
        
        strTime = time.strftime('%X %x')
        try:
            # imgPath = Path of a image-File as PNG ["string"]
            self.imgList.append(imgPath)
        except IOError:
            print strTime+" sendMail: Faild to read path for PNG!"
            self.add_Line("Faild to read path for PNG!")


    def sendEMail(self):
        
        strTime = time.strftime('%X %x')
        
        COMMASPACE = ', '
        # Create message container
        self.Msg['Subject'] = self.Subject
        self.Msg['From'] = self.Source
        self.Msg['To'] = COMMASPACE.join(self.Recipients)

       # Messages to concatenate
        if self.lineList != []:
             txt = MIMEText(''.join(self.lineList))
             self.Msg.attach(txt)
        else:
            txt = MIMEText("NO MESSAGE")
            self.Msg.attach(txt)

        # Attach image
        if self.imgList != []:
            try:
                for line in self.imgList:
                    f3 = open(line, 'rb')
                    img = MIMEImage(f3.read())
                    f3.close()
                    self.Msg.attach(img)
            except IOError:
                print strTime + " sendMail: Faild to open or read path for PNG!"

        # Send the message via local SMTP server.
        s = smtplib.SMTP('smtp.kit.edu',25)   #kit's smtp server, port 25
        #print "was here"
        # sendmail function takes 3 arguments: sender's address, recipient's
        # address and message to send
        s.sendmail(self.Source, self.Recipients, self.Msg.as_string())
        s.quit()
        print strTime + " sendMail: eMail sent to: " + str(self.Recipients)


    def add_Line(self, mesgLine):
        
        # Call this function for several "single-line" messages
        strTime = time.strftime('%X %x')
        try:
            #self.lineList.append("\n")
            self.lineList.append(mesgLine + '\n')
            #self.lineList.append("\n")
        except IOError:
            print strTime + " sendMail: Failed to write message to array (single-line)!"
            txt = MIMEText("Failed to write message to array (single-line)")
            self.Msg.attach(txt)

    def __del__(self):
        return True
