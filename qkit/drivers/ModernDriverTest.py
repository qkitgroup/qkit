from qkit.core.instrument_basev2 import QkitProperty, QkitFunction, interval_check, ModernInstrument
        

class Channel:

    def __init__(self, id):
        self.id = id

    @QkitProperty(type=float, units="A", tags=["Current Supply"])
    def amperage(self):
        """
        Provides the amperage of something.
        """
        return 3.14

    @amperage.setter
    def amperage(self, value):
        print(f"Set amp to {value}")

    @QkitFunction
    def do_something(self):
        return f"Maybe{self.id}"

class ModernDriverTest(ModernInstrument):

    def __init__(self, name):
        super().__init__(name)
        print("In init", name)
        self.channels = [Channel(i) for i in range(8)]
        self.discover_capabilities()

    @QkitProperty(type=float, units="V", tags=["Voltage Supply"], arg_checker=interval_check(0.0, 5.0))
    def voltage(self):
        """
        Measures the voltage of something.
        """
        return 5

    @voltage.setter
    def voltage(self, v):
        print(f"Set voltage to {v}")

    @QkitFunction
    def do_complicated_stuff(self):
        return "Nope"