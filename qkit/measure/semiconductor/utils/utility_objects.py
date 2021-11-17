#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 10:56:35 2021

@author: lr1740
"""
from collections.abc import MutableMapping
import qkit.measure.measurement_base as mb
import numpy as np

class Multiplexer:
    """
    A sequential multiplexer.
    
    Attributes
    ----------
    no_active_nodes: int
        The total number of data_nodes which belong to currently active measurements
    
    Methods
    -------
    register_measurement(name, unit, nodes, get_tracedata_func, *args, **kwargs):
        Registers a measurement.

    activate_measurement(measurement):
        Activates the given measurement.

    deactivate_measurement(measurement):
        Deactivates the given measurement.

    prepare_measurement_datasets(coords):
        Creates qkit.measure.measurement_base.MeasureBase.Data objects along the coords for each active measurement.

    measure(): 
        Calls all active measurements sequentially.
    """
    def __init__(self):
        self.registered_measurements = {}
        self.no_measurements = 0
    
    @property
    def no_active_nodes(self):
        no_nodes = 0
        for measurement in self.registered_measurements.values():
            if measurement["active"]:
                no_nodes += len(measurement["nodes"])
        return no_nodes

    def register_measurement(self, name, unit, nodes, get_tracedata_func, *args, **kwargs):
        """
        Registers a measurement.

        Parameters
        ----------
        name : string
            Name of the measurement the measurement which is to be registered.
        unit : string
            Unit of the measurement.
        nodes : list(string)
            The data nodes of the measurement
        get_tracedata_func : callable
            Callable object which produces the data for the measurement which is to be registered.
        *args, **kwargs:
            Additional arguments which are passed to the get_tracedata_func during registration.

        Returns
        -------
        None
        """
        if type(name) != str:
            raise TypeError(f"{__name__}: {name} is not a valid experiment name. The experiment name must be a string.")
        if type(unit) != str:
            raise TypeError(f"{__name__}: {unit} is not a valid unit. The unit must be a string.")
        if type(nodes) != list:
            raise TypeError(f"{__name__}: {nodes} are not valid data nodes. The data nodes must be a list of strings.")
        else:
            for node in nodes:
                if type(node) != str:
                    raise TypeError(f"{node} is not a valid data node. A data node must be a string.")
        if not callable(get_tracedata_func):
            raise TypeError("%s: Cannot set %s as get_value_func. Callable object needed." % (__name__, get_tracedata_func))
        
        self.registered_measurements[name] = {"unit" : unit, "nodes" : nodes, "get_tracedata_func" : lambda: get_tracedata_func(*args, **kwargs), "active" : False}
        self.no_measurements = len(self.registered_measurements)
    
    def activate_measurement(self, name):
        """
        Activates the given measurement.

        Parameters
        ----------
        measurement : string
            Name of the measurement the measurement which is to be activated.

        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If the given measurement doesn't exist.
        """
        if name not in self.registered_measurements.keys():
            raise KeyError(f"{__name__}: {name} is not a registered measurement. Cannot activate.")
        self.registered_measurements[name]["active"] = True
    
    def deactivate_measurement(self, name):
        """
        Deactivates the given measurement.

        Parameters
        ----------
        measurement : string
            Name of the measurement the measurement which is to be deactivated.

        Returns
        -------
        None
        
        Raises
        ------
        KeyError
            If the given measurement doesn't exist.
        """
        if name not in self.registered_measurements.keys():
            raise KeyError(f"{__name__}: {name} is not a registered measurement. Cannot deactivate.")
        self.registered_measurements[name]["active"] = False
        
    def prepare_measurement_datasets(self, coords):
        """
        Creates qkit.measure.measurement_base.MeasureBase.Data objects along the coords for each active measurement.

        Parameters
        ----------
        coords : list(qkit.measure.measurement_base.MeasureBase.Coordinate)
            The measurement coordinates along which Data objects will be created.

        Returns
        -------
        datasets : list(qkit.measure.measurement_base.MeasureBase.Data)
        """
        datasets = []
        for name, measurement in self.registered_measurements.items():
            if measurement["active"]:
                for node in measurement["nodes"]:
                    datasets.append(mb.MeasureBase.Data(name = f"{name}.{node}",
                                              coords = coords,
                                              unit = measurement["unit"],
                                              save_timestamp = False))
        return datasets
    
    def measure(self):
        """
        Sequentially calls the measurement functions of each active measurement.

        Returns
        -------
        latest_data : dict()
        """
        latest_data = {}
        for name, measurement in self.registered_measurements.items():
            if measurement["active"]:
                temp = measurement["get_tracedata_func"]()
                for node, value in temp.items():
                    latest_data[f"{name}.{node}"] = value
        return latest_data
        
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

class TransformedDict(MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys"""

    def __init__(self, mapping, *args, **kwargs):
        self.mapping = mapping
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[key]

    def __setitem__(self, key, value):
        self.store[self._keytransform(key)] = value

    def __delitem__(self, key):
        del self.store[key]

    def __iter__(self):
        return iter(self.store)
    
    def __len__(self):
        return len(self.store)
    
    def __str__(self):
        return self.store.__str__()

    def _keytransform(self, key):
        return self.mapping[key]
    
class Mapping_handler:
    def __init__(self, dictionary, mapping = None):
        if type(dictionary) != dict:
            raise TypeError(f"{__name__}: Cannot map {dictionary}. Must be a dictionary.")
        self.dictionary = dictionary
        
        if mapping == None:
            self.mapping = {entry : entry for entry in self.dictionary.keys()}
        else:
            self.mapping = mapping        
        if type(mapping) != dict:
            raise TypeError(f"{__name__}: Cannot use {mapping} as mapping. Must be a dictionary.")
        
        self._expand_mapping()
        self._create_inverse_mapping()
        
        try:
            self.mapped = TransformedDict(self.mapping, dictionary)
        except KeyError:
            self.mapped = TransformedDict(self.inverse_mapping, dictionary)        
        self.not_mapped = self.dictionary
    
    def _expand_mapping(self):
        additional_mapping = {entry : entry for entry in self.dictionary.keys()\
                                  if entry not in self.mapping.values() and entry not in self.mapping.keys()}
        self.mapping.update(additional_mapping)
        
    def _create_inverse_mapping(self):
        self.inverse_mapping = {v : k for k, v in self.mapping.items()}