# -*- coding: utf-8 -*-
"""
Start remote interface service (RIS)
@author: HR@KIT/2018
"""
import qkit
import logging


def _load_ri_service():
    logging.info(__file__+": loading remote interface service")
    from qkit.core.lib.com.ri_service import RISThread
    qkit.ris = RISThread()

if qkit.cfg.get('load_ri_service',False):
    qkit.cfg['load_ri_service']=True
    _load_ri_service()
else:
    qkit.cfg['load_ri_service']=False