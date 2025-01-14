from abc import ABC, abstractmethod
from typing import Any, Dict, List


class PlotterInterface(ABC):
    @abstractmethod
    def load_data(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def validate_input(self):
        pass

    @abstractmethod
    def plot(self):
        pass


class AnalyzerInterface(ABC):
    @abstractmethod
    def load_data(self, data: Dict[str, Any]):
        pass

    @abstractmethod
    def validate_input(self):
        pass

    @abstractmethod
    def analyze(self) -> Dict[str, Dict[str, Any]]:
        pass


class LoaderInterface(ABC):
    @abstractmethod
    def set_filepath(self, path: List[str]):
        pass

    @abstractmethod
    def load(self):
        pass
