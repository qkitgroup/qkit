# -*- coding: utf-8 -*-
"""
@author: MP, HR@KIT/2018
"""
import qkit
import logging
import sys
from qkit.core.lib.file_service.file_tools import store_db
#from qkit.core.lib.file_service.database_viewer import DatabaseViewer


def _load_file_service():
    logging.info("loading service: store_db")
    qkit.store_db = store_db()
    #if 'pandas' in sys.modules:
    #    qkit.dbv = DatabaseViewer()
    #else:
    #    logging.warning("pandas required for a data base of your measurement files")


if qkit.cfg.get('load_file_service', True):
    _load_file_service()
