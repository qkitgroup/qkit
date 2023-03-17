<p align="center">
  <img src="https://github.com/qkitgroup/qkit/blob/master/images/Qkit_Logo.png" alt="QKIT" width="300">
</p>


### Qkit - a quantum measurement suite in python

### Features:
  * a collection of ipython notebooks for measurement and data analysis tasks.
  * hdf5 based data storage of 1,2 and 3 dimensional data, including a viewer.
  * classes for data fitting, e.g. of microwave resonator data. This includes also a robust circle fit algorithm.
  * extended and maintained drivers for various low frequency and microwave electronics.

### Platform:
  The qkit framework has been tested under windows and with limits under macos x and linux. 
  The gui requires h5py, qt and pyqtgraph, which work fine on these platforms. 
  The core of the framework should run with python 2.7.x/3.4+
 
### Requirements:
#### Basic:
  * An up to date python distribution, including the qt gui libs, numpy and scipy.  
    e.g.  anaconda python http://continuum.io/downloads  
  * h5py http://www.h5py.org/ for saving data
  * pyqtgraph is required by the viewer (qkit/gui/qviewkit) : http://www.pyqtgraph.org/
  * Optional: We use ipython/jupyter notebooks for the measurement scripts: http://jupyter.org
  * Optional: Messages are distributed with zmq: http://zeromq.org (also used by jupyter)
  * Optional: To use Zurich Instruments devices, `zhinst-toolkit` is required
  * Optional: `pyvisa` in combination with `pyvisa-py`
  
  

### Installation:
  * copy the qkit archive to an apropriate place
  * and add the qkit/qkit directory to your systems PYTHONPATH variable
