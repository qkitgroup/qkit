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
 
## Installation:
If you intend to actively work on the code, look at the section for developing this code.
To install this package, run:
```bash
pip install 'qkit[jupyter,analysis] @ git+https://github.com/qkitgroup/qkit.git@master'
```

## Developing
Clone this repository to wherever is convenient and run
```bash
python -m venv .venv
pip install --editable .
```
## Running
You will most likely want to run a JupyterLab Server to work with qkit. Download `jupyter_lab_config.py`.
In this file, you might want to change this line:
```python 
# Set Notebook directory
notebook_dir = r'C:\notebooks' # Change this line
```
to point to an existing notebook directory. Then run
```bash
jupyter lab --config=./jupyter_lab_config.py
```

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

Also, you will need to migrate your local config to your `cwd`, or point to it using the environment variable `QKIT_LOCAL_CONFIG`

## Requirements:
This project uses python. An up to date installation of python is expected to be present.
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
| [toml](https://pypi.org/project/toml/) | Configuration |
