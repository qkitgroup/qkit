from abc import ABC, abstractmethod

class ModeBase(ABC):
    
    @abstractmethod
    def create_coordinates(self):
        pass
    @abstractmethod
    def create_datasets(self):
        pass
    @abstractmethod
    def reset(self):
        pass
    @abstractmethod
    def fill_file(self):
        pass

def main(): 
    pass
if __name__ == "__main__":
    main()