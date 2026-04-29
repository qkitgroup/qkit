import numpy as np
from typing import List, Callable

class FluxCompensator:
    """
    Set a desired flux point while compensating for flux cross-talk.
    """

    _compensation: np.ndarray
    _setters: List[Callable[[float], None]]

    def __init__(self, effects: np.ndarray, setters: List[Callable[[float], None]]):
        """
        Create an instance to compensate for flux cross-talk to precisely set flux points.

        Parameters:
        effects: 2D Array, where effects[i, j] is the effect of the ith qubits flux loop control parameter on the jth qubit flux/flux quantum.
        setters: List of functions to set the control parameter values for the ith qubit.

        Example:
            Qubit 1 and 2 have 1V/flux quantum, and 4V/flux quantum cross-talk. In this case the matrix becomes
            [[1, 0.25], [0.25, 1]].
        """
        self.compensation = np.linalg.inv(effects)
        self.setters = setters

    def set_flux(self, fluxes: np.ndarray):
        """
        Set the flux points to the provided values, compensating for flux cross-talk.
        """
        set_points = self.compensation @ fluxes
        for setter, set_point in zip(self.setters, set_points):
            setter(set_point)