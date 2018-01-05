# -*- coding: utf-8 -*-
"""
@author: HR@KIT/2017
"""
import qkit
import logging
from qkit.core.lib.file_service.file_tools import create_database

def _load_file_service():
    create_database()
    qkit.update_datebase = create_database

if qkit.cfg.get('load_file_service',True):
    _load_file_service()