# qkit
Qkit framework -- an extension to qtlab

### Features:
  * a collection of ipython notebooks for measurement and data anaysis tasks 
  * hdf5 based data storage of 1,2 and 3 dimensional data, including a viewer for 1 and 2 dimensional data
  * classes for data fitting, e.g. of microwave resonator data. This includes also a robust circle fit algorithm.
  * extended and maintained drivers for various low frequency and microwave electronics.
  * large parts of the framework can be used independently of qtlab

### Platform:
  The qkit framework has been tested under windows and with limits under macos x and linux. 
  The gui requires h5py, qt and pyqtgraph, which work fine on these platforms.
 
### Requirements:
#### Basic:
  * An up to date python distribution, including the qt gui libs. 
    e.g.  anaconda python http://continuum.io/downloads 
          python xy http://pythonxynews.blogspot.de/
  * pyqtgraph is required by the viewer (qkit/gui/qviewkit) : http://www.pyqtgraph.org/


#### Full:
  * For a full installation, qtlab is required, e.g from https://github.com/heeres/qtlab


### Installation:
  * copy the qkit archive to an apropriate place
  Standalone:
  * add the qkit/qkit directory to your systems PYTHONPATH variable
  with Qtlab:
  * add the qkit/qkit directory to your systems PYTHONPATH variable
  * change the path variables in Qtlab's userconfig.py apropriately, e.g.
    config['user_insdir']
    config['scriptdirs'] 
    It useful to add it to system path like this: sys.path.append('path_of_qkit_folder')



### Extended 2015- by

J.C. Braumueller  
M. Pfirrmann  
S. Probst  
A. Schneider  
H. Rotzinger  
