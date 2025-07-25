from abc import ABC, abstractmethod
from typing import Literal, Any

import numpy as np


class AbstractIVDevice(ABC):

    @abstractmethod
    def take_IV(self, sweep: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Perform an IV sweep. Returns (bias, sense).
        """
        pass

    @abstractmethod
    def get_sweep_mode(self) -> Literal[0, 1, 2]:
        """
        Get the sweep mode: 0 (VV-mode) | 1 (IV-mode) | 2 (VI-mode)
        """
        pass

    @abstractmethod
    def get_sweep_bias(self) -> Literal[0, 1]:
        """
        Get the sweep bias: 0 (current bias) | 1 (voltage bias)

        Only relevant for units.
        """
        pass

    @abstractmethod
    def get_sweep_channels(self) -> list:
        """
        Get a list of channels to sweep.
        """
        pass

    @abstractmethod
    def set_status(self, status: bool, channel: Any):
        """
        Sets the status of a channel.
        """
        pass

    def set_overall_status(self, status: bool):
        for channel in self.get_sweep_channels():
            self.set_status(status, channel)