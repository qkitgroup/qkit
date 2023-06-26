.. include:: global.rst.inc
.. _installation:

Installation
============

|project_name| requires:

* Python_ >= 2.7 
* some python dependencies, see install_requires in setup.py

Currently, only installation from git repo checkout is supported.

Use pip install -e . from the top-level |project_name| directory to install
it into same virtualenv as you use for |project_name_backup|.

To install the complete environment you can do the following: ::

    # Install Python code and dependencies:
    pip install package_XYZ
    git clone https://github.com/qkitgroup/qkit.git qkit
    # Add qkit to your python environment: 
    # e.g. by adding the qkit folder to your PYTHONPATH variable:
    # in a linux shell one would add the following line to the .bashrc:
    export PYTHONPATH=$PYTHONPATH:path_to_qkit/qkit


Configuration
=============

QKIT can be configured statically before it is started by making changes to 
qkit/config/local.py. This file has to be created, e.g. by copying the environment.py::
      cp environment.py local.py

Now you can make changes to local.py. The default values are commented, please remove the '#' and make your changes.

Another very handy way of configuring QKIT is to make changes to the setting after loading the main qkit object::
    import qkit
    # now the environment.py and local.py are loaded and 
    # the qkit.cfg dictionary is populated with variables:
    print qkit.cfg
    # non-static settings can now be changes by 
    qkit.cfg['variable'] = "NewValue"

This way of adjusting the QKIT environment is especially useful when working in Jupyter notebooks.

Startup
=======

After configuration, QKIT is initizlized by running::
      qkit.start()
This function executes a set of init routines located in qkit/core/s_init/



