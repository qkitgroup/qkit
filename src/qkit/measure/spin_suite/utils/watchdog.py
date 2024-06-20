import numpy as np

class Watchdog:
    """
    An object containing restrictions and functions to check whether given values lie wihtin the boundaries given
    by the restrictions.
    
    Attributes
    ----------
   stop: bool
        Is True once a check finds a value which does not lie within the given restrictions

    message: string
        Is set once a check finds a value which does not lie within the given restrictions.
        Describes which restriction was violated.
    
    Methods
    -------
    register_node(data_node, bound_lower, bound_upper):
        Registers upper and lower bounds for a measurement node.

    reset():
        Sets the stop attribute to False, and the message attribute to an empty string.

    limits_check(self, data_node, values):
        Checks whether the values lie within the boundaries for the given data_node.
    """
    def __init__(self):
        self.stop = False
        self.message = ""
        self.measurement_bounds = {}
    
    def register_node(self, data_node, bound_lower, bound_upper):
        """
        Registers a measurement node.

        Parameters
        ----------
        data_node : string
            Name of the measurement node which is to be registered.
        bound_lower : float
            Lower bound of the allowed values for data_node.
        bound_upper : float
            Upper bound of the allowed values for data_node.

        Returns
        -------
        None

        Raises
        ------
        ValueError
            If the given bound_lower is larger or equals the bound_upper
        """
        if type(data_node) != str:
            raise TypeError(f"{__name__}: {data_node} is not a valid measurement node. The measurement node must be a string.")
        try:
            bound_lower = float(bound_lower)
        except Exception as e:
            raise type(e)(f"{__name__}: Cannot set {bound_lower} as lower measurement bound for node {data_node}. Conversion to float failed.")
        try:
            bound_upper = float(bound_upper)
        except Exception as e:
            raise type(e)(f"{__name__}: Cannot set {bound_lower} as lower measurement bound for node {data_node}. Conversion to float failed.")
        
        if bound_lower >= bound_upper:
            raise ValueError(f"{__name__}: Invalid bounds. {bound_lower} is larger or equal to {bound_upper}.")
        
        self.measurement_bounds[f"{data_node}"] = [bound_lower, bound_upper]
        
    def reset(self):
        """
        Resets the watchdog.
        """
        self.stop = False
        self.global_message = ""
    
    def limits_check(self, data_node, values):
        """
        Checks wether the values lie within the bounds for data_node.

        Parameters
        ----------
        data_node : string
            Name of the data_node the values belong to.
        values : int, float, list(int), list(float), np.array
            Values to be checked.

        Returns
        -------
        None

        Raises
        ------
        KeyError
            No bounds are defined for data_node.
        """
        if data_node not in self.measurement_bounds.keys():
            raise KeyError(f"{__name__}: No bounds are defined for {data_node}.")
        for value in np.atleast_1d(values):
            if value < self.measurement_bounds[data_node][0]:
                self.stop = True
                self.message = f"{__name__}: Lower measurement bound for {data_node} reached. Stopping measurement."
            elif value > self.measurement_bounds[data_node][1]:
                self.stop = True
                self.message = f"{__name__}: Upper measurement bound for {data_node} reached. Stopping measurement."