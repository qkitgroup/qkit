<p align="center">
  <img src="./images/Qkit_Logo.png" alt="QKIT" width="300">
</p>


# Qkit - a quantum measurement suite in python

## Features:
  * a collection of ipython notebooks for measurement and data analysis tasks.
  * hdf5 based data storage of 1,2 and 3 dimensional data, including a viewer.
  * classes for data fitting, e.g. of microwave resonator data. This includes also a robust circle fit algorithm.
  * extended and maintained drivers for various low frequency and microwave electronics.

### Platform:
  The qkit framework has been tested under windows and with limits under macos x and linux. 
  The gui requires h5py, qt and pyqtgraph, which work fine on these platforms. 
  The core of the framework should run with python 2.7.x/3.4+
 
## Requirements:
This project uses python. An up to date installation of python is expected to be present.
The requirements are listed in the `requirements.txt` file. They can be installed automatically using
```bash
pip install -r requirements.txt
```
| Library | Usage |
| ------- | ----- |
| [pyqt5](https://pypi.org/project/PyQt5/) | GUI   | 
| [numpy](https://pypi.org/project/numpy/), [scipy](https://pypi.org/project/scipy/), [uncertainties](https://pypi.org/project/uncertainties/) | General Usage |
| [pyqtgraph](https://pypi.org/project/pyqtgraph/), [matplotlib](https://pypi.org/project/matplotlib/) | Plotting |
| [h5py](https://pypi.org/project/h5py/) | Data Stroage |
| [jupyterlab](https://pypi.org/project/jupyterlab/) | Interactive Notebooks |
| [jupyterlab-templates](https://pypi.org/project/jupyterlab-templates/) | Notebook Templating |
| [pyvisa](https://pypi.org/project/PyVISA/), [pyvisa-py](https://pypi.org/project/PyVISA-py/) | Communication with Devices |
| [zhinst](https://pypi.org/project/zhinst/) | Drivers for Zurich Instruments devices |
| [zeromq](https://pypi.org/project/pyzmq/) | Messaging |  

## Upgrading:
If you use an existing installation of qkit, where the Jupyter Notebooks are not located in `./notebooks`, then you will need to change one line in `jupyter_lab_config.py`:

```python 
# Set Notebook directory
notebook_dir = 'notebooks' # Change this line
```
On Windows, this might be set to:
```python 
# Set Notebook directory
notebook_dir = r'C:\notebooks' # Change this line
```

## Installation:
Clone this repository with
```bash
git clone https://github.com/qkitgroup/qkit.git
```
In this directory, create a virtual environment with the required dependencies. Should you not have `virtualenv` installed, see below.
```bash
virtualenv .venv
```
Depending on your operating system you need to run (Linux)
```bash
source .\.venv/Scripts/activate
```
or (Windows):
```ps1
.\.venv\Scripts\Activate.ps1
``` 
Now install the dependencies using
```bash
pip install -r requirements.txt
```

### Installing venv
If you don't have support for virtual environments, enable it by running
```bash
pip install virtualenv
```
### Optional: Adding QKIT to path
Add the qkit/qkit directory to your systems PYTHONPATH variable.

If you use the included scripts to run JupyterLab, then this step is not required.

## Running
Depending on your operating system, run `launch.ps1` (Windows) or `launch.sh`(Linux)