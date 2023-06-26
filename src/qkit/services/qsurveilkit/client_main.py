# qsurveilkit client written by HR,AS,JB@KIT 2013, 2016

'''
qsurveilkit client example, may run on any machine in the local network 
of the machine running server_main.py
'''

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


import sys
from threading import Thread

from PyQt4.QtCore import QObject, pyqtSignal
from PyQt4.QtGui import QMainWindow, QApplication

from plasma1_gui import Ui_MainWindow

import argparse
try:
    from ConfigParser import RawConfigParser
except ImportError:
    from configparser import RawConfigParser
import time
from math import log10

import numpy as np
from scipy.signal import medfilt as medfilter

import rpyc


class AcquisitionThread(Thread,QObject):
    """
    Acquisition loop. This is the worker thread that retrieves data from the server.
    """
    update_sig = pyqtSignal()
    
    def __init__(self,DATA):
        Thread.__init__(self)
        QObject.__init__(self)
        DATA.wants_abort = False
        self.data = DATA   #client data object
        
    def setup_remote_connection(self):
        '''
        Setup rpyc server connection.
        '''
        self.c = rpyc.connect(self.data.localhost.ip,self.data.localhost.port)
        print('Connection established to %s via port %s.'%(str(self.data.localhost.ip),str(self.data.localhost.port)))
        
    def acquire_datapoint_from_remote(self,p):
        '''
        Acquire the most recent data point of parameter instance p of the local client data object.
        '''
        return self.c.root.get_last_value(p.attribute_name)

    def acquire_history(self,p):
        '''
        acquires data from the log file of parameter p
        '''
        acq = self.c.root.get_history(p.attribute_name,p.range)
        if len(acq) == 2:
            return acq
        else:   #error reading h5 file
            raise IOError
    
    def close_connection(self):
        self.c.close()

    def run(self):

        self.setup_remote_connection()

        print('Client started.')
        while not self.data.wants_abort:
            for p in self.data.parameters:
                #extract new data point
                new_timestamp, new_value = self.acquire_datapoint_from_remote(p)
                p.values = np.append(p.values,new_value)
                p.timestamps = np.append(p.timestamps,new_timestamp)
            
                #check for data history request
                # if logging is active and more data is requested by the local GUI
                if p.logging and p.check_history and time.time() - p.timestamps[0] < p.range*3600:
                    try:
                        timestamps, values = self.acquire_history(p)
                        if timestamps[0] < p.timestamps[0]:
                            p.timestamps = np.array(timestamps, dtype='float64')
                            p.values = np.array(values, dtype='float32')
                    except IOError:
                        print('Error retrieving history data for parameter %s.'%str(p.attribute_name))
                p.check_history = False   #switch off history request after one unsuccessful attempt
                
                #delete old data points
                data_points_out_of_range = np.where(time.time()-p.timestamps > p.range*3600)
                p.values = np.delete(p.values,data_points_out_of_range)
                p.timestamps = np.delete(p.timestamps,data_points_out_of_range)
                
            self.update_sig.emit()   #tell the GUI that the client data set has been updated
            
            time.sleep(self.data.update_interval)
            
        self.close_connection()
        print('Connection closed.')


class MainWindow(QMainWindow, Ui_MainWindow):

    def myquit(self):
        exit()

    def __init__(self,DATA):
        
        self.data = DATA

        QMainWindow.__init__(self)
        # set up User Interface (widgets, layout...)
        self.setupUi(self)
        
        # --- specify graph and label objects as declared in the gui file
        self.data.pLL.graph = self.graph_LL
        self.data.pLL.label = self.label_LL
        self.data.pMC.graph = self.graph_MC
        self.data.pMC.label = self.label_MC
        
        #combo box entries, dictionary
        self.cb_scale_entries = {0:24,1:2,2:1,3:0.16}
        
        
        self.range = self._get_range()
        for p in self.data.parameters: p.range = self._get_range()
        
        self._setup_signal_slots()
        self._setup_graphs()
        
        self._start_acquisition()
        
        
    def _setup_signal_slots(self):
        self.cb_scale.currentIndexChanged.connect(self._range_changed)   #combo box
        
    def closeEvent(self,event):
        self.data.wants_abort = True
        print('Client closing ...')
        event.accept()
    
    def _setup_graphs(self):
        self.data.pLL.graph.setLabel('left',"LL pressure (mbar)")
        self.data.pLL.graph.setLabel('bottom',"time (h)")
        self.data.pLL.graph.plt = self.graph_LL.plot(pen='b')
        self.data.pLL.graph.setLogMode(y=True)
        
        self.data.pMC.graph.setLabel('left',"MC pressure (mbar)")
        self.data.pMC.graph.setLabel('bottom',"time (h)")
        self.data.pMC.graph.plt = self.graph_MC.plot(pen='b')
        self.data.pMC.graph.setLogMode(y=True)
        
    def _update_labels(self):
        self.data.pLL.label.setText('LL: %.3g mbar'%self.data.pLL.values[-1])
        self.data.pMC.label.setText('MC: %.3g mbar'%self.data.pMC.values[-1])
        
    def _autorange_plots(self):
        for p in self.data.parameters:
            p.graph.enableAutoRange()
        
    def _get_range(self):
        return self.cb_scale_entries[self.cb_scale.currentIndex()]
        
    def _range_changed(self):   #combo box change event
        if self.data.debug: print('range_changed')
        for p in self.data.parameters:
            p.range = self._get_range()
            p.check_history = True
        
    def _start_acquisition(self):
        print('Start acquisition.')
        self.acquisition_thread = AcquisitionThread(self.data)
        self.acquisition_thread.update_sig.connect(self._update_gui)
        self.acquisition_thread.start()
            
        
    @pyqtSlot(float)
    def _update_gui(self):
        for p in [self.data.pLL,self.data.pMC]:
            #remove error entries from values
            for i in range(1,len(p.values)-1):
                if len(p.values[i-4:i]) > 0 and len(p.values[i+1:i+5]) > 0:
                    median = np.sort(p.values[i-4:i+5])[int(0.5*len(p.values[i-4:i+5]))]
                    if np.abs(log10(p.values[i] / median)) > 6 and np.abs(log10(p.values[i] / p.values[i-1])) > 6:
                        #if jumps detected collecting more than 5 orders of magnitude back or forth
                        p.values[i] = median
                        if self.data.debug: print('runaway detected in {:s}, segment #{:d}'.format(p.attribute_name,i))
            p.graph.plt.setData(x=np.array((p.timestamps-time.time())/3600), y=p.values)
            self._autorange_plots()
            self._update_labels()

class DATA(object):
    '''
    Client data class. The __init__ method accesses the same cfg file as the server.
    '''
    class LOCALHOST(object):
        def __init__(self,config):
            self.name = config.get('LOCALHOST','name')
            self.ip   = config.get('LOCALHOST','ip')
            self.port = config.getint('LOCALHOST','port')
    class PARAMETER(object):
        '''
        Parameter class. Information is extracted from the cfg file.
        '''
        def __init__(self,config,p_index,p_attr):
            self.p_index = p_index
            self.attribute_name = str(p_attr)
            self.name = config.get(str(p_attr),'name')
            self.values = np.array([])
            self.timestamps = np.array([])
            self.logging = bool(int(config.get(str(p_attr),'logging')))
            self.check_history = False
        
    def __init__(self,config):
        self.debug = True
        self.wants_abort = False
        
        self.update_interval = config.getfloat('gui','update_interval')
        
        p_instances = config.get('parameters','p').split(",")   #parameter instance names
        #instanciate parameter objects
        self.parameters = [self.PARAMETER(config,i,p) for i,p in enumerate(p_instances)]   #instanciate parameter array
        for i,p_i in enumerate(p_instances):   #create human readable aliases, such that objects are accessible from clients according to the seetings.cfg entry in []
            setattr(self,str(p_i),self.parameters[i])
            
        self.localhost = self.LOCALHOST(config)
 
def main(argv):

    parser = argparse.ArgumentParser(
        description="Derived from TIP v0.1 (HR@KIT 2011), updated and generalized by HR,JB@KIT 2016")

    parser.add_argument('ConfigFile', nargs='?', default='settings.cfg',
                        help='Configuration file name')
    args=parser.parse_args()
    
    Conf = RawConfigParser()
    Conf.read(args.ConfigFile)
    
    data = DATA(Conf)
    data.config = Conf

    try:
        # create Qt application
        app = QApplication(argv,True)
        # create main window
        wnd = MainWindow(data) # classname
        wnd.show()
        
        # Connect signal for app finish
        app.connect(app, SIGNAL("lastWindowClosed()"), app, SLOT("quit()"))
        
        # Start the app up
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        data.wants_abort = True
        print('Exiting client.')
        exit()
        
    
if __name__ == "__main__":
    main(sys.argv)