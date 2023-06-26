# qsurveilkit
qsurveilkit framework -- a qkit module written in python 2.7
qsurveilkit is a generalization of the TIP module, originally started by HR@KIT 2011+

### Features:
  * general server based module for monitoring and logging purposes
  * multi-threading
  * threaded server client supporting qt GUI
  
### Coming up:
  * h5 logging, local GUI support via qviewkit
  * log file readout at data history request by a client
  
### Operation:
  * server start via executing 'server_main.py'
  * instrument driver is imported and data request objects are set in 'server_main.py'
  * parameter and host information stored and set in 'settings.cfg', must also be provided to all clients
  * 'settings.cfg' may be created by the user modifying the template file 'settings_template.cfg'
  * h5 logging requires a qkit copy public to the python path
  
  * clients start 'client_main.py' with the respective GUI file and 'settings.cfg' in a known directory
  * client GUI currently based on pyqtgraph

### Platform:
  The  framework has been tested under windows and with limits under macos x and linux. 
  The gui requires h5py, qt and pyqtgraph, which work fine on these platforms.
 
### Requirements:

  * An up to date python 2.7 distribution, including the qt gui libs.  
    e.g.  anaconda python http://continuum.io/downloads  
          python xy http://pythonxynews.blogspot.de/
  * h5py http://www.h5py.org/
  * pyqtgraph http://www.pyqtgraph.org/
  * rpyc https://rpyc.readthedocs.io/en/latest/

### Started 2016 by

J.C. Braumueller  
H. Rotzinger  
