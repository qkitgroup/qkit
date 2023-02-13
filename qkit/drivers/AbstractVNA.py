from abc import ABC, abstractmethod
from qkit.core.instrument_base import Instrument
import numpy as np

class AbstractVNA(ABC):
    """
    This Abstract Base Class defines all the methods required and optionally available for VNA measurements.
    This Abstract Base Class expects the object to be a Instrument, but will not directly enforce this.
    We check the presence of the required methods before calling them.
    """

    def register_vna_functions(self):
        assert isinstance(self, Instrument)
        self.add_function('get_freqpoints')
        self.add_function('get_tracedata')
        self.add_function('get_sweeptime')
        self.add_function('get_sweeptime_averages')
        self.add_function('pre_measurement')
        self.add_function('start_measurement')
        self.add_function('ready')
        self.add_function('post_measurement')

    @abstractmethod
    def get_freqpoints(self) -> np.ndarray:
        """
        Return a list of frequencies the VNA is measuring at.
        This may be configurable with device specific methods.
        """
        pass

    def get_span(self) -> float:
        """
        Returns the length of the frequency interval to be analyzed.
        """
        freqs = self.get_freqpoints()
        return freqs[-1] - freqs[0]

    @abstractmethod
    def get_tracedata(self, RealImag = None) -> tuple((np.ndarray, np.ndarray)):
        """
        When the measurement succeeded, this method returns the resulting data.
        The behaviour depends on the [RealImag] keyword argument.
        If it is none, this method shall return (Amplitude, Phase)-Data.
        Otherwise, this method must return (I, Q)-Data.
        """
        pass

    @abstractmethod
    def get_sweeptime(self, query=True):
        """
        Report the expected sweep time for the GUI.
        """
        pass

    @abstractmethod
    def get_sweeptime_averages(self):
        """
        No idead what this does. TODO: Figure out.
        """
        pass

    
    def pre_measurement(self):
        """
        Optional hook to execute code before a measurement.
        If the device needs to be set up, between measurements,
        this is the point where you can do that.
        """
        pass

    @abstractmethod
    def start_measurement(self):
        """
        Trigger the actual measurement. If this is synchronous [ready] may return True.
        Otherwise, use [ready] to indicate when the measurement has completed.
        """
        pass

    @abstractmethod
    def ready(self) -> bool:
        """
        Report if this measurement has completed. If start_measurement returns on completion,
        this should be implmented to always return true.
        """
        pass

    def post_measurement(self):
        """
        Optional hook to execute code after a measurement has completed.
        """
        pass

    def get_all(self):
        """
        Support to efficiently retrieve all options about this device.
        """
        pass

    def get_nop(self):
        return len(self.get_freqpoints())

    def get_averages(self):
        return 1

    def get_Average(self):
        return False

    def avg_clear(self):
        pass