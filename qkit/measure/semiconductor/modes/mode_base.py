from abc import ABC, abstractmethod

class ModeBase(ABC):
    
    @abstractmethod
    def create_coordinates(self):
        pass
    @abstractmethod
    def reset(self):
        pass
    @abstractmethod
    def fill_file(self):
        pass
    def create_tag(self):
        self.tag = self.__class__.__name__
def main(): 
    pass
if __name__ == "__main__":
    main()