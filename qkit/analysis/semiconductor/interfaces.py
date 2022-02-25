from abc import ABC, abstractmethod

class PlotterInterface(ABC):
    @abstractmethod
    def validate_input():
        pass

    @abstractmethod
    def plot():
        pass

class AnalyzerInterface(ABC):
    @abstractmethod
    def validate_input():
        pass

    @abstractmethod
    def analyze():
        pass

class LoaderInterface(ABC):
    @abstractmethod
    def load():
        pass