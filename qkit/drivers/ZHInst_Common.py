import zhinst
import logging
from typing import List, Union
import enum
import time
import os

from qkit.core.instrument_base import Instrument

class ZHInst_Path:
    """
    An object representing a path node in the LabOne API hierarchy.
    Allows setting and getting relative paths.
    """

    def __init__(self, accessor: Union[zhinst.ziPython.ziDAQServer, 'ZHInst_Path'], path: str):
        """
        Initializes this Path wrapper.
        If the accessor is a ziDAQServer, then this is considered a root node.
        If the accessor, however, is an instance of ZHInst_Path, then this object will be a child of the provided instance,
        deriving its _daq from it and treating the provided path as a relative path.
        """
        if isinstance(accessor, zhinst.ziPython.ziDAQServer):
            self._daq = accessor
            self._element_path = path
        elif isinstance(accessor, ZHInst_Path):
            self._daq = accessor._daq
            self._element_path = accessor.build_key(path)

    def build_key(self, path: str):
        """
        Builds the path to access the data.

        Parameters:
        path: The path to the data, not including the device id.
        """
        return f'{self._element_path}/{path}'

    def getDouble(self, rel_path: str) -> float:
        return self._daq.getDouble(self.build_key(rel_path))

    def setDouble(self, rel_path: str, value: float) -> bool:
        self._daq.setDouble(self.build_key(rel_path), value)

    def getInt(self, rel_path: str) -> int:
        return self._daq.getInt(self.build_key(rel_path))

    def setInt(self, rel_path: str, value: int):
        self._daq.setInt(self.build_key(rel_path), value)

    def getString(self, rel_path: str):
        return self._daq.getString(self.build_key(rel_path))

    def setBool(self, rel_path: str, boolean: bool):
        if boolean:
            actual_val = 1
        else:
            actual_val = 0
        return self.setInt(rel_path, actual_val)

    def getBool(self, rel_path: str) -> bool:
        return self.getInt(rel_path) == 1

    def setVector(self, rel_path: str, json: str):
        self._daq.setVector(self.build_key(rel_path), json)

class ZHInst_Device(ZHInst_Path, Instrument):
    """
    This is the base class for all Zurich Instrument devices.
    It establishes the network connection to the management interface and registers itself as a measurement device.
    Further, it allows child objects to wrap around paths and to mix in other features, such as the `ZHInst_AWG_Mixin`
    to provide access to AWG features and program compilation.
    """

    def __init__(self, name, device_id, server="localhost", port=8004, interface="1GbE"):
        logging.info(__name__ + ' : Initializing instrument id '+ device_id)
        Instrument.__init__(self, name, tags=['physical'])

        daq = zhinst.ziPython.ziDAQServer(host=server, port=port, api_level=6)
        daq.connectDevice(device_id, interface)
        zhinst.utils.api_server_version_check(daq)
        logging.info(__name__ + ' : Connected to server.')

        ZHInst_Path.__init__(self, daq, f'/DEV{device_id}')


class ZHInst_AWG_Mixin:
    """
    This class is a mixin, i.e. it can be added to other instrument classes. It is not supposed to be used standalone.
    This mixin provides access to the AWG features found in many Zurich Instrument devices.
    """

    def compile_sequencer_program(self, seq_id: int, programm: str):
        """
        Compiles the program text in `programm` and uploads it to the AWG as sequence `seq_id`.

        """
        [channel.set_enabled(False) for channel in self.channels]
        awg = self._daq.awgModule()
        awg.set("device", self.device_id)
        awg.set("index", seq_id)
        awg.execute()

        awg.set("compiler/sourcestring", programm)
        _monitor_compilation(awg, 10)
        _monitor_upload(awg, 10)

        self._daq.sync()



class AWGCompilation(enum.IntEnum):
    """
    More useful names for the AWG Compilation progress constants.
    """
    IDLE = -1
    SUCCESS = 0
    FAILED = 1
    WARNINGS = 2

def _monitor_compilation(awg, timeout: float):
    """
    Monitors the awg compilation progress, fails if the timeout is exceeded.
    If the compilation succeeds, the status flag will transition form IDLE (-1)
    to any other state indicating, Success(0), Failure(1) or Warnings(2).

    This function monitors this flags with a timeout and reports back failures.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.1)
        status = AWGCompilation(awg.getInt("compiler/status"))
        if status == AWGCompilation.IDLE:
            # Compilation is still ongoing. Wait.
            continue
        elif status == AWGCompilation.SUCCESS:
            # Compilation finished susccessfully
            return
        else:
            # We hit a failure mode
            status_string = awg.getString("compiler/statusstring")
            raise AssertionError(f"Unsuccessfull compilation with status {status}!",
                                 f"Status: {status_string}")

    # Compilation timeout
    status_string = awg.getString("compiler/statusstring")
    raise AssertionError(f"Compilation did not finish within {timeout}s timeout.",
                         f"Status: '{status_string}'")

class AWGUpload(enum.IntEnum):
    """
    More useful names for the AWG Upload progress constants.
    """
    IDLE = -1
    SUCCESS = 0
    FAILED = 1
    IN_PROGRESS = 2

def _monitor_upload(awg, timeout: float):
    """
    Monitor the awg upload progress. If the upload succeeds, the elf/status flag will transition
    to AWG_SUCCESS, while the progress indicator will hit 1.0.

    Upload failure is indicated by the status flag transitioning to AWG_FAILURE
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        time.sleep(0.1)
        status = AWGUpload(awg.getInt("elf/status"))
        if status == AWGUpload.IDLE or status == AWGUpload.IN_PROGRESS:
            # Compilation is still ongoing. Wait.
            continue
        elif status == AWGUpload.SUCCESS or awg.getDouble("progress") == 1.0:
            # Compilation finished susccessfully
            return
        else:
            # We hit a failure mode.
            status_string = awg.getString("compiler/statusstring")
            raise AssertionError(f"Unsuccessfull upload with status {status}!",
                                 f"Status: {status_string}")

    # Compilation timeout
    status_string = awg.getString("compiler/statusstring")
    raise AssertionError(f"Upload timed out with {timeout}s timeout.",
                         f"Status: '{status_string}'")

def load_file_string(fname):
    """
    Loads a file given by  `fname` as a string and returns it.
    """
    with open(fname, "r") as f:
        return f.read()

WAVEFORM_PATH = "ZHInst_Waveforms"

def load_common_sample(id):
    """
    Loads a commonly used sample.
    """
    script_path = os.Path(os.path.abspath(os.path.dirname(__file__)))
    file_path = script_path / WAVEFORM_PATH / id
    return load_file_string(file_path)