from abc import ABC, abstractmethod
from typing import Any, Literal


class AbstractThermometer(ABC):
    """
    The interface for a generic multichannel thermometer.

    It measures in [unit] (to be implemented). Returns measurement via get_temperature.
    """

    @property
    def unit(self) -> Literal['K', '°C']:
        """
        The unit of the measurement. Override to change.
        """
        return 'K'

    @abstractmethod
    def get_temperature(self, channel: Any) -> float:
        pass