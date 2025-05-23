import re

from qkit.storage.file_path_management import MeasurementFilePath

def test_defaults():
    mfp = MeasurementFilePath(measurement_name='test')
    rel_path = str(mfp.rel_path)
    assert re.match(r'^NO_RUN/John_Doe/[A-Z0-9]{6}_test/[A-Z0-9]{6}_test.h5$', rel_path)

def test_path_extension():
    mfp = MeasurementFilePath(measurement_name='test', additional_path_info=['special'])
    rel_path = str(mfp.rel_path)
    assert re.match(r'^NO_RUN/John_Doe/special/[A-Z0-9]{6}_test/[A-Z0-9]{6}_test.h5$', rel_path)