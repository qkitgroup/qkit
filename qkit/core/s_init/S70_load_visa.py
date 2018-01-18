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
        
    from pkg_resources import get_distribution
    if float(get_distribution('pyvisa').version) < 1.5:
        logging.warning("Old pyvisa version loaded. Please update to a version > 1.5.x")
        # compatibility with old visa lib
        qkit.visa = visa
    else:
        # active py visa version
        logging.info("Modern pyvisa version loaded. Version %s" % visa.__version__)
        try:
            rm = visa.ResourceManager()
            qkit.visa = rm
            qkit.visa.__version__ = visa.__version__
            
            def instrument(resource_name, **kwargs):
                return rm.open_resource(resource_name, **kwargs)
            qkit.visa.instrument = instrument
        except OSError:
            raise OSError('Failed creating ResourceManager. Check if you have NI VISA or pyvisa-py installed.')

if qkit.cfg.get('load_visa',True):
    _load_visa()

"""
doc snipplet from 
https://pyvisa.readthedocs.io/en/stable/migrating.html
"""