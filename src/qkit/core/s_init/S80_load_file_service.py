# -*- coding: utf-8 -*-
"""
@author: MP, TW, HR@KIT/2018
"""
import qkit
import logging
from qkit.core.lib.file_service.file_info_database import fid


def _load_file_service():
    logging.info("loading service: file info database (fid)")
    qkit.fid = fid()
    #info: qkit.store_db does not exist anymore: use qkit.fid instead.

if qkit.cfg.get('fid_scan_datadir', True):
    _load_file_service()
