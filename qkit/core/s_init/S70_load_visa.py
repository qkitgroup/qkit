# -*- coding: utf-8 -*-
"""
@author: HR@KIT/2017
"""
import qkit
import logging

def _load_visa():
    try:
        import visa
    except ImportError as e:
        logging.error("pyvisa not loaded %s"%e)
        
    from distutils.version import LooseVersion
    if  LooseVersion(visa.__version__) < LooseVersion("1.5.0"):
        logging.warning("Old pyvisa version loaded. Please update to a version > 1.5.x")
        # compatibility with old visa lib
        qkit.visa = visa
    else:
        # active py visa version
        logging.info("Modern pyvisa version loaded. Version %s" % visa.__version__)
        rm = visa.ResourceManager()
        qkit.visa = rm
    def instrument(name): 
        return rm.open_resource(name)
    #qkit.visa.instrument = instrument

if qkit.cfg.get('load_visa',False):
    _load_visa()

"""
doc snipplet from 
https://pyvisa.readthedocs.io/en/stable/migrating.html
>>> import visa
>>> keithley = visa.instrument("GPIB::12")
>>> print(keithley.ask("*IDN?"))
change it to:

>>> import visa
>>> rm = visa.ResourceManager()
>>> keithley = rm.open_resource("GPIB::12")
>>> print(keithley.query("*IDN?"))
"""