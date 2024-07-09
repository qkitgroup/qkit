''' adjusted spin_tune class for trace measurement at ST'''
import qkit
from qkit.gui.notebook.Progress_Bar import Progress_Bar
from qkit.measure.spin_suite.spin_tune import Tuning

class Tuning_ST(Tuning):

    def measure1D(self,data_to_show = None):
        """
        Starts a 1D - measurement, along the x coordinate.
        
        Parameters
        ----------
        data_to_show : List of strings, optional
            Name of Datasets, which qviewkit opens at measurement start.
        """
        assert self._x_parameter, f"{__name__}: Cannot start measure1D. x_parameters required."
        self._measurement_object.measurement_func = "%s: measure1D" % __name__

        self._open_qviewkit(datasets = data_to_show)
        try:
            latest_trace = self.multiplexer.measure()
            self._append_vector(latest_trace, self._datasets,direction = 1)
        finally:
            self.watchdog.reset()
            self._end_measurement()


    def measure2D(self, data_to_show = None):
        """
        Starts a 2D - measurement, with y being the inner and x the outer loop coordinate.
        
        Parameters
        ----------
        data_to_show : List of strings, optionals
            Name of Datasets, which qviewkit opens at measurement start.
        """
        assert self._x_parameter, f"{__name__}: Cannot start measure2D. x_parameters required."
        assert self._y_parameter, f"{__name__}: Cannot start measure2D. y_parameters required."
        self._measurement_object.measurement_func = "%s: measure2D" % __name__
        pb = Progress_Bar(len(self._x_parameter.values))

        self._open_qviewkit(datasets = data_to_show)

        try:
            for x_val in self._x_parameter.values:
                # x_wait = self._x_parameter.wait_time
                self._x_parameter.set_function(x_val)
                self._acquire_log_functions()
                latest_trace = self.multiplexer.measure()
                self._append_vector(latest_trace, self._datasets, direction = 1)
                pb.iterate(addend = 1)
                if self.watchdog.stop: break 

        finally:
            self.watchdog.reset()
            self._end_measurement()