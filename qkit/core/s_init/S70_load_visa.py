# -*- coding: utf-8 -*-
"""
@author: HR@KIT/2017
"""
import qkit
import logging
from pkgutil import find_loader


def _load_visa():
    try:
        import visa
    except Exception as e:
        logging.error("pyvisa not loaded %s"%e)
        qkit.cfg['load_visa'] = False
    else:
        from pkg_resources import get_distribution
        from distutils.version import LooseVersion
        if LooseVersion(get_distribution('pyvisa').version) < LooseVersion("1.5.0"):
            logging.warning("Old pyvisa version loaded. Please update to a version > 1.5.x")
            # compatibility with old visa lib
            qkit.visa = visa
            qkit.visa.__version__ = get_distribution('pyvisa').version
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


if qkit.cfg.get('load_visa',find_loader('pyvisa') is not None):
    qkit.cfg['load_visa'] = True
    _load_visa()
else:
    qkit.cfg['load_visa'] = False


"""
doc snipplet from 
https://pyvisa.readthedocs.io/en/stable/migrating.html
"""