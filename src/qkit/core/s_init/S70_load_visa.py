# -*- coding: utf-8 -*-
"""
@author: MiWi,HR,S1@KIT/2017,2018
"""
import qkit
import logging
from pkgutil import find_loader


def _load_visa():
    try:
        try:
            import pyvisa as visa
        except:
            import visa
    except Exception as e:
        qkit.cfg['load_visa'] = False
        raise type(e)('Failed loading visa. Check if you have NI VISA or pyvisa-py installed. Original error: ' + str(e))
    else:
        from pkg_resources import get_distribution
        from distutils.version import LooseVersion
        if LooseVersion(get_distribution('pyvisa').version) < LooseVersion("1.5.0"):
            logging.warning("Old pyvisa version loaded. Please update to a version > 1.5.x")
            # compatibility with old visa lib
            qkit.visa = visa
            qkit.visa.__version__ = get_distribution('pyvisa').version
            qkit.visa.qkit_visa_version = 1 #This makes it just much easier to distinguish between the main versions
        else:
            # active py visa version
            logging.info("Modern pyvisa version loaded. Version %s" % visa.__version__)
            try:
                rm = visa.ResourceManager(qkit.cfg.get('visa_backend',""))
                qkit.visa = rm
                qkit.visa.__version__ = visa.__version__
                qkit.visa.qkit_visa_version = 2
                qkit.visa.VisaIOError = visa.VisaIOError
                
                def instrument(resource_name, **kwargs):
                    return rm.open_resource(resource_name, **kwargs)
                qkit.visa.instrument = instrument
                # define data types:
                qkit.visa.double = "d"
                qkit.visa.single = "f"
                qkit.visa.dtypes = {1:qkit.visa.single,
                                    3:qkit.visa.double,
                                    "d":"d","f":"f"}
            except OSError:
                raise OSError('Failed creating ResourceManager. Check if you have NI VISA or pyvisa-py installed.')

class DummyVisa(object):
    def __getattr__(self,name):
        raise qkit.QkitCfgError("Please set qkit.cfg['load_visa'] = True if you need visa.")

if qkit.cfg.get('load_visa',False):
    _load_visa()
else:
    qkit.visa = DummyVisa()

"""
doc snipplet from 
https://pyvisa.readthedocs.io/en/stable/migrating.html
"""