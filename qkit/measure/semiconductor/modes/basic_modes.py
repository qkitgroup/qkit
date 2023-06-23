import numpy as np
import collections

from qkit.measure.semiconductor.modes.mode_base import ModeBase

def makehash():
    return collections.defaultdict(makehash)

class PulseParameter(ModeBase):
    def __init__(self, fh, measurement_settings) -> None:
        self.fh = fh
        self.measurement_settings = measurement_settings
        self.unit = "a.u."        
        self.total_sum = makehash()
        self.divider = makehash()
        self.create_tag()
        self.reset()

    def create_coordinates(self):
        all_coords = {}
        for measurement_name, measurement in self.measurement_settings.items():
            x_coord = {"values" : measurement["loop_range_pp"],
            "coordname" : f"{self.tag}:{measurement['loop_step_name_pp']}.{measurement_name}",
            "unit" : self.unit,}
            all_coords[measurement_name] = [x_coord]
        return all_coords  

    def fill_file(self, latest_data, data_location):
        for measurement_name, node_values in latest_data.items():
            #If latest data is empty for one measurement, skip it
            first_node = list(node_values.keys())[0]
            collected_averages = len(node_values[first_node])
            if collected_averages== 0: continue
            self.divider[measurement_name] += collected_averages
            for node_name, node_value in node_values.items():
                self.total_sum[measurement_name][node_name] += np.sum(np.average(node_value, axis = 2), axis = 0)
                value = self.total_sum[measurement_name][node_name]/self.divider[measurement_name]
                self.fh.write_to_file(f"{self.tag}:{measurement_name}.{node_name}", value, data_location)    
    
    def reset(self):
        for name, measurement in self.measurement_settings.items():
            self.divider[name] = 0
            for node in measurement["data_nodes"]:
                self.total_sum[name][node] = 0

class NoAvg(ModeBase):
    def __init__(self, fh, measurement_settings) -> None:
        self.fh = fh
        self.measurement_settings = measurement_settings
        self.column = makehash()
        self.create_tag()
        self.reset()

    def create_coordinates(self):
        all_coords = {}
        for measurement_name, measurement in self.measurement_settings.items():
            x_coord = {"values" :  np.arange(measurement["averages"] * measurement["measurement_count"]),
            "coordname" : f"{self.tag}:iterations.{measurement_name}",
            "unit" : "#",}
            y_coord = {"values" :  measurement["loop_range_tt"],
            "coordname" : f"{self.tag}:{measurement['loop_step_name_tt']}.{measurement_name}",
            "unit" : "s",}
            all_coords[measurement_name] = [x_coord, y_coord]
        return all_coords
        
    def fill_file(self, latest_data, data_location):
        for measurement_name, node_values in latest_data.items():
            #If latest data is empty for one measurement, skip it
            first_node = list(node_values.keys())[0]
            collected_averages = len(node_values[first_node])
            if collected_averages== 0: continue
            for node_name, node_value in node_values.items():
                for grid in node_value:
                    for single_trace in grid:
                        position = data_location + (self.column[measurement_name][node_name],)
                        self.fh.write_to_file(f"{self.tag}:{measurement_name}.{node_name}", single_trace, 
                        position)
                        self.column[measurement_name][node_name] += 1
    
    def reset(self):
        for name, measurement in self.measurement_settings.items():
            for node in measurement["data_nodes"]:
                self.column[name][node] = 0

class PpvsT(ModeBase):
    def __init__(self, fh, measurement_settings) -> None:
        self.fh = fh
        self.measurement_settings = measurement_settings
        self.unit_pp = "a.u."
        self.unit_tt = "s"
        self.total_sum = makehash()
        self.divider = makehash()
        self.create_tag()
        self.reset()

    def create_coordinates(self):
        all_coords = {}
        for measurement_name, measurement in self.measurement_settings.items():
            x_coord = {"values" :  measurement["loop_range_pp"],
            "coordname" : f"{self.tag}:{measurement['loop_step_name_pp']}.{measurement_name}",
            "unit" : "a.u.",}
            y_coord = {"values" :  measurement["loop_range_tt"],
            "coordname" : f"{self.tag}:{measurement['loop_step_name_tt']}.{measurement_name}",
            "unit" : "s",}
            all_coords[measurement_name] = [x_coord, y_coord]
        return all_coords

    """def create_coordinates2(self):
        for name, measurement in self.measurement_settings.items():
            self.fh.update_coordinates(f"{self.tag}.pp", measurement["loop_range_pp"], 
                                        f"{self.tag}:{measurement['loop_step_name_pp']}.{name}",
                                        name, self.unit_pp)
            self.fh.update_coordinates(f"{self.tag}.tt", measurement["loop_range_tt"], 
                                        f"{self.tag}:{measurement['loop_step_name_tt']}.{name}",
                                        name, self.unit_tt)
    
    def create_datasets(self, additional_coords):
        for name, measurement in self.measurement_settings.items():
            for node in measurement["data_nodes"]:
                coords = additional_coords + [self.fh.multiplexer_coords[f"{self.tag}.pp"][name], self.fh.multiplexer_coords[f"{self.tag}.tt"][name]]
                self.fh.add_dset(f"{self.tag}:{name}.{node}", coords, measurement["unit"]) """

    def fill_file(self, latest_data, data_location):
        for measurement_name, node_values in latest_data.items():
            #If latest data is empty for one measurement, skip it
            first_node = list(node_values.keys())[0]
            collected_averages = len(node_values[first_node])
            if collected_averages== 0: continue
            self.divider[measurement_name] += collected_averages
            for node_name, node_value in node_values.items():
                self.total_sum[measurement_name][node_name] += np.sum(node_value, axis = 0)
                value = self.total_sum[measurement_name][node_name]/self.divider[measurement_name]
                self.fh.write_to_file(f"{self.tag}:{measurement_name}.{node_name}", value, data_location)
    
    def reset(self):
        for name, measurement in self.measurement_settings.items():
            self.divider[name] = 0
            for node in measurement["data_nodes"]:
                self.total_sum[name][node] = 0

class TimeTrace(ModeBase):
    def __init__(self, fh, measurement_settings) -> None:
        self.fh = fh
        self.measurement_settings = measurement_settings
        self.unit = "s"        
        self.total_sum = makehash()
        self.divider = makehash()
        self.create_tag()
        self.reset()

    def create_coordinates(self):
        all_coords = {}
        for measurement_name, measurement in self.measurement_settings.items():
            x_coord = {"values" :  measurement["loop_range_tt"],
            "coordname" : f"{self.tag}:{measurement['loop_step_name_tt']}.{measurement_name}",
            "unit" : "a.u.",}
            all_coords[measurement_name] = [x_coord]
        return all_coords

    """ def create_coordinates(self):
        for name, measurement in self.measurement_settings.items():
            self.fh.update_coordinates(self.tag, measurement["loop_range_tt"], 
                                        f"{self.tag}:{measurement['loop_step_name_tt']}.{name}",
                                        name, self.unit)
    
    def create_datasets(self, additional_coords):
        for name, measurement in self.measurement_settings.items():
            for node in measurement["data_nodes"]:
                coords = additional_coords + [self.fh.multiplexer_coords[self.tag][name]]
                self.fh.add_dset(f"{self.tag}:{name}.{node}", coords, measurement["unit"]) """

    def fill_file(self, latest_data, data_location):
        for measurement_name, node_values in latest_data.items():
            #If latest data is empty for one measurement, skip it
            first_node = list(node_values.keys())[0]
            collected_averages = len(node_values[first_node])
            if collected_averages== 0: continue
            self.divider[measurement_name] += collected_averages
            for node_name, node_value in node_values.items():
                self.total_sum[measurement_name][node_name] += np.sum(np.average(node_value, axis = 1), axis = 0)
                value = self.total_sum[measurement_name][node_name]/self.divider[measurement_name]
                self.fh.write_to_file(f"{self.tag}:{measurement_name}.{node_name}", value, data_location)
    
    def reset(self):
        for name, measurement in self.measurement_settings.items():
            self.divider[name] = 0
            for node in measurement["data_nodes"]:
                self.total_sum[name][node] = 0