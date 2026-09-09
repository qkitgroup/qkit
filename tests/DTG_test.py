import pytest
from qkit.storage.hdf_DateTimeGenerator import DateTimeGenerator
import qkit
import re

def test_DateTimeGenerator_no_extension():
    dtg = DateTimeGenerator()
    returndict = dtg.new_filename("test_file.h5")
    assert re.match("NO_RUN/John_Doe/......_test_file\\.h5", returndict['_relfolder']) 

def test_DateTimeGenerator_with_extension():
    qkit.cfg['path_extension'] = 'extension'
    dtg = DateTimeGenerator()
    returndict = dtg.new_filename("test_file.h5")
    assert re.match("NO_RUN/John_Doe/extension/......_test_file\\.h5", returndict['_relfolder']) 