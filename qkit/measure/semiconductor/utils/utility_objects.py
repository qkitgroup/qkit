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
    def __init__(self):
        #self._validate_core(core)
        #self.core = core
        self.registered_measurements = {}
        self.no_measurements = 0
        self.no_nodes = 0
    
    def register_measurement(self, name, unit, nodes, get_tracedata_func, *args, **kwargs):
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
        
        self.registered_measurements[name] = {"unit" : unit, "nodes" : nodes, "get_tracedata_func" : lambda: get_tracedata_func(*args, **kwargs), "active" : True}
        self.no_measurements = len(self.registered_measurements)
        self.no_nodes = 0
        for measurement in self.registered_measurements.values():
            self.no_nodes += len(measurement["nodes"])
    
    def activate_measurement(self, name):
        self.registerd_measurements[name]["active"] = True
    
    def deactivate_measurement(self, name):
        self.registerd_measurements[name]["active"] = False
        
    def prepare_measurement_datasets(self, coords):
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
        latest_data = {}
        for name, measurement in self.registered_measurements.items():
            if measurement["active"]:
                temp = measurement["get_tracedata_func"]()
                for node, value in temp.items():
                    latest_data[f"{name}.{node}"] = value
        return latest_data
        
class Watchdog:
    def __init__(self):
        self.stop = False
        self.message = ""
        self.measurement_bounds = {}
    
    def register_node(self, data_node, bound_lower, bound_upper):
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
        self.stop = False
        self.global_message = ""
    
    def limits_check(self, data_node, values):
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