# -*- coding: utf-8 -*-
"""
@author: MP, HR@KIT/2018
"""
import qkit
import logging
from qkit.core.lib.file_service.file_tools import store_db 

def _load_file_service():
    logging.info("loading service: store_db")
    qkit.store_db = store_db()

if qkit.cfg.get('load_file_service',True):
    _load_file_service()