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
  The core of the framework should run with python 3.7+
 
## Installation:
If you intend to actively work on the code, look at the section for developing this code.
To install this package, run:
```bash
pip install 'qkit[jupyter,analysis] @ git+https://github.com/qkitgroup/qkit.git@master'
```
If you are simply using qkit, changes to files in `src/` **should not** be necessary. If you find things you need to change there, this might be a bug. Please report this.

If you intend to use the option to click on .h5 files in order to open them, don't install qkit in a virtual environment.

## Configuration
There are three sources of configuration, which are used to set up your environment
- qkit defaults (you shouldn't change those)
- local config file
- configuration in notebooks

### Local config file
On import, qkit will look for a file called `qkit_local_config.py` or `local.py` in your current working directory or any of its parents. Note, that in case of a jupyter notebook, the current working directory is the directory in which your notebook is located.

If you can't put such a configuration file into a suitable location, you can set the environment variable `QKIT_LOCAL_CONFIG` with a path pointing to such a configuration file. This variable circumvents the search, and the file is directly loaded.

## Developing
Clone this repository to wherever is convenient.
```bash
git clone https://github.com/qkitgroup/qkit
```

The following commands need to be run within the cloned repository.

It is recommended, but not required, to create a new virtual environment. This isolates this local environment from your global packages. This way, version conflicts can be avoided. If you choose to use a virtual environment, then it needs to be activated, otherwise, qkit and its dependencies will not be available. This also means double click to open .h5 files will not be available.
For more, look [here](https://docs.python.org/3/library/venv.html).
```bash
python -m venv .venv
```

Now, you can install qkit as an editable package. This means, that you can change files in the cloned repository. Changes will affect your python setup.

The brackets contain optional dependencies. This pulls the libraries needed for jupyter lab.

```bash
pip install --editable '.[jupyter,analysis]'
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

## Upgrading
If you use an existing installation of qkit, there might be some breaking changes. They are not major, but need to be taken care of.
### Migrating Configuration
Previously, the configuration of qkit was located in `qkit/config/local.py`. As this directory is now a child of `src/`, you are probably not supposed to touch this file. This method is deprecated (you will receive warnings).

Instead, in a parent directory, a file named `qkit_local_config.py` is used to configure your environment.

To migrate, copy the code in your old `local.py` into the new `qkit_local_config.py` file. Do note, however, that the `datadir` and `logdir` paths have changed. It is recommended to use the new values. Conflicting entries in your config may need to be deleted.

### "My changes to the configuration are not applied after upgrading"
If your notebooks do not reside in a child directory of qkit, the `qkit_local_config.py` may not be found, as each notebook launches a Python process in its location running itself. Thus `qkit_local_config.py` may not be in any of the notebooks parent directories. In this case, either set the environment variable `QKIT_LOCAL_CONFIG` to your configuration, or place the configuration in your notebook directory instead.

### Migrating Notebooks
The new setup assumes, that notebooks are located in `notebooks/`. This way, `qkit_local_config.py` is in a parent directory of your notebooks and is thus loaded when you initialize qkit in your notebooks.

On measurement computers, it is recommended to move your notebooks into that directory. Alternatively, update `jupyter_lab_config.py` to point to the notebook directory:

```python 
# Set Notebook directory
notebook_dir = 'notebooks' # Change this line
```
On Windows, this might be set to:
```python 
# Set Notebook directory
notebook_dir = r'C:\notebooks' # Change this line
```

Also, you will need to migrate your local config to a parent directory of your notebooks, or point to it using the environment variable `QKIT_LOCAL_CONFIG`. It is possible to set this environment variable in `jupyter_lab_config.py`, as environment variables are inherited to process children.

## Requirements
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
