#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 10:56:35 2021

@author: lr1740
"""
from collections.abc import MutableMapping

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

class Mapping_handler2:
    def __init__(self, channel_mapping = {}, measurement_mapping = {}) -> None:
        self.channel_mapping = channel_mapping
        self.measurement_mapping = measurement_mapping

    def map_channels(self, dict):
        display_names = dict.keys()
        for display_name, name in self.channel_mapping.items():
            if display_name in display_names:
                dict[name] = dict.pop(display_name)
        return dict

    def map_measurements(self, dict):
        display_names = dict.keys()
        for display_name, name in self.measurement_mapping.items():
            
            if display_name in display_names:
                dict[name] = dict.pop(display_name)
        return dict
    
    def map_channels_inv(self, dict):
        names = dict.keys()
        for display_name, name in self.channel_mapping.items():
            if name in names:
                dict[display_name] = dict.pop(name)
        return dict

    def map_measurements_inv(self, dict):
        names = dict.keys()
        for display_name, name in self.measurement_mapping.items():
            if name in names:
                dict[display_name] = dict.pop(name)
        return dict