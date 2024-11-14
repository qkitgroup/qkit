# -*- coding: utf-8 -*-
"""
keeping track of your measurement files 

@author: MP, AS, TW, HR@KIT / 2018
@license GPL


file info database
==================


lets introduce a set of 
fid configuration settings (defaults)
=====================================
fid_scan_datadir = True
    Indicates whether you want to scan your datadir for h5 files at startup.
fid_scan_hdf     = False
    This will open every h5 file found and extract attributes.
fid_init_viewer  = True
    Make a database out of the dictionary of h5 files.


databases
=========

h5_db
----------
This is the main database. It holds an index of UUID <-> h5-file path.
usage: 
qkit.fid.h5_db.get("UUID") or qkit.fid.get("UUID") returns the h5_file path

h5_info_db
----------
This database is only populated when the qkit.cfg setting 'fid_scan_hdf' is True.
The database holds an UUID index with extended informations about the hdf file. 
populating this database is much slower than h5_db therfore not on by default.

set_db and measure_db
------
Hold an UUID index with the settings for a h5_file


basic usage
===========

this is done automatically on qkit startup: (in n.op.)
-------------------------------------------
import qkit.core.lib.file_service.file_info_database as fid
qkit.fid = fid.fid()

qkit.view(file_id)
-----------
opens a qviewkit instance with the file_id


import and basic usage of the h5-grid-viewer
============================================
# qgrid is an interactive jupyter tool for pandas dataframe, which helps filtering your data
# for more information see https://github.com/quantopian/qgrid
# script works also well without qgrid
# you can simply access all the data via pandas commands, i.e., qkit.fid.df.columnname['uid']
# for further information see doc strings


after startup, the following main commands are available in a jupyter notebook:
-------------------------------------------------------------------------------
qkit.fid.show()
qkit.fid.view(file_id)

qkit.fid.get_uuid(time)
qkit.fid.get_time(uuid)
qkit.fid.get_date(uuid)
"""



import logging
import threading
from distutils.version import LooseVersion

import numpy as np

import qkit

found_qgrid = False
if qkit.module_available['pandas']:
    import pandas as pd
    if qkit.module_available['qgrid']:
        import qgrid as qd
        found_qgrid = True

from qkit.core.lib.file_service.file_info_database_lib import file_system_service

# display using qviewkit
from qkit.gui.plot.plot import plot

class fid(file_system_service):
    def __init__(self):
        self._batch_update = False
        self.column_sorting = ['datetime', 'name', 'run', 'user', 'comment', 'rating']
        self.columns_ignore = ['time']
        self.df = None
        # create initial database in the background. This can take a while...
        self.create_database()
        self._selected_df = []
        self.found_qgrid = found_qgrid
        

    history = property(lambda self: sorted(self.h5_db.keys()))
    
    def get_last(self):
        return sorted(self.h5_db.keys())[-1]
        
    def __getitem__(self, key):
        with self.lock:
            if type(key) == int:
                return sorted(self.h5_db.keys())[key]
            try:
                return self.h5_db[key]
            except KeyError as e:
                raise KeyError("Can not find your UUID '{}' in qkit.fid database.".format(key))

    def get(self, key, args=None):
        with self.lock:
            if key not in self.h5_db:
                logging.error("Can not find your UUID '{}' in qkit.fid database.".format(key))
            return self.h5_db.get(key, args)

    def view(self, file_id=None):
        """
        view a datafile with qviewkit
        =============================
    
        Args:
           file_id (str):  identifier for a data file.
           
           file_id can be 
           
           None (empty): then the latest file is opened
           
           int: e.g. -1, 100 
                then the number is opened from the last list
           list: e.g ['UUID1' , 'UUID2']
               each UUID is opened
           uuid:
               the data file is looked up via the h5_db and opened
           path:
               the data file is opened using the path 

        Returns:
            None
        """

        def plotif(filename):
            if filename:
                plot(filename, live=False)

        if qkit.module_available['pandas']:
            if type(file_id) is pd.Index:
                file_id = list(file_id)
        
        if file_id is None:
            plotif(self.h5_db.get(self.get_last()))
        elif type(file_id) is int:
            plotif(self.h5_db.get(self.history[file_id]))
        elif type(file_id) is list:
            for i in file_id:
                plotif(self.h5_db.get(i, False))
        elif type(file_id) is str:
            plotif(self.h5_db.get(file_id, False))

    def create_database(self,block=False):
        t1 = threading.Thread(name='creating_db', target=self.update_all)
        t1.start()
        if block:
            t1.join()
    
    def recreate_database(self):
        '''
            Deletes all cached database files and rescans the whole directory tree.
            Use this if your database looks strange.
        '''
        self.h5_db = {}
        self.set_db = {}
        self.measure_db = {}
        self.h5_info_db = {}
        self._h5_n_mtime = {}
        
        self._remove_cache_files()
        self.create_database()

    def update_all(self):
        """ updates file and grid database if activated
        """
        self.update_file_db()
        self.update_grid_db()

    def update_grid_db(self):
        with self.lock:
            if qkit.cfg.get('fid_init_viewer',qkit.module_available['pandas']):  # Pandas ist needed here, so if fid_init_viewer is not set, we make it dependent on pandas
                qkit.cfg['fid_init_viewer'] = True
                if not qkit.module_available['pandas']:
                    raise ImportError("pandas not found. Pandas is needed for the fid viewer.\nInstall pandas or set qkit.cfg['fid_init_viewer']=False")
                self._initiate_basic_df()
            else:
                qkit.cfg['fid_init_viewer'] = False
    
    def _get_setting_from_set_file(self, filename, instrument, value):
        try:
            with open(filename, 'r') as f:
                i_name = False
                return_dict = {}
                for line in f:
                    if line.startswith("Instrument: "):
                        if line[12:].strip() in instrument:
                            i_name = line[12:].strip()
                        else:
                            i_name = False
                    elif i_name:
                        p = line.strip().split(":")
                        if p[0] in value:
                            for i in range(len(instrument)):
                                if p[0] == value[i] and i_name == instrument[i]:
                                    try:
                                        return_dict.update({i_name+":"+p[0] : float(p[1][1:])})
                                    except(ValueError,TypeError):
                                        return_dict.update({i_name + ":" + p[0]: p[1][1:]})
                return return_dict
        except(IOError):
            return {}

    def set_rating(self, uid, rating):
        """
        If you want to rate your measurements, so that you can filter for good ones. You can add a rating into the analysis
        folder of the h5 file
        :param uid: uid of the measurement file you wanna rate
        :type str
        :param rating: a simple value to rate your measurement. Default is 10, Rating <=0 is masked by default.
        :type int, float
        """
        return self._set_hdf_attribute(uid, "rating", rating)

    if qkit.module_available['pandas']:
    
        def _initiate_basic_df(self):
            """
            Creates a pandas data frame from your measurement
            data and allows to extract import values from h5-files
            """
        
            if len(self.h5_info_db) == 0:  # necessary if a data directory is chosen without any h5 file
                self.df = pd.DataFrame(columns=['datetime', 'name', 'run', 'user'])
            else:
                self.df = pd.DataFrame(self.h5_info_db).T
        
            if qkit.cfg.get('fid_scan_hdf', False):
                # self.df = self.df[['datetime', 'name', 'run', 'user', 'comment', 'fit_time', 'fit_freq', 'rating']]
                for key in ['rating', 'fit_time', 'fit_freq']:
                    if key in self.df.keys():
                        self.df[key] = pd.to_numeric(self.df[key], errors='coerce')
            else:
                self.df = self.df[['datetime', 'name', 'run', 'user']]
            self.df['datetime'] = pd.to_datetime(self.df['datetime'], errors='coerce')
            self.df.fillna("", inplace=True)  # Replace NAs with empty string to be able to detect changes
        
        def _get_settings_column(self, device, setting, uid=None, update_hdf=False):
            dfsetting = pd.DataFrame()
            if not isinstance(device, (tuple, list)):
                device = [device]
            if not isinstance(setting, (tuple, list)):
                setting = [setting]
            if len(device) != len(setting):
                raise ValueError("Please specify 'device' and 'setting' as equally long lists, where teir individual entries correspond to each other.")
            if uid is None:
                uid = self.df.index
            for i in uid:
                values = self._get_setting_from_set_file(self.h5_db[i].replace('.h5', '.set'), device, setting)
                if update_hdf:
                    for p, v in values.items():
                        self._set_hdf_attribute(i, p, v)
                dfsetting = pd.concat([dfsetting,
                                       pd.DataFrame(values, index=[i])
                                       ], sort=False)
            return dfsetting
    
        def add_settings_column(self, device, setting, measurement_id=None):
            """
            Reads out a specific setting from your chosen device. If you provide a uid,
            then only these files will be considered
            :param device: your device name
            :type str
            :param setting: setting of your device
            :type str
            :param uid: measurement_id (list). If None (default), all are used
            :type str
            """
            settings_column = self._get_settings_column(device, setting, measurement_id, update_hdf=qkit.cfg.get('fid_scan_hdf', False))
            for key in settings_column.keys():
                if key in self.df.keys():
                    self.df.update(settings_column.loc[:, key])
                else:
                    self.df = pd.concat([self.df, settings_column.loc[:, key]], axis=1)
        
        def open_in_filemanager(self):
            ids = self._selected_df.index
            if len(ids) > 10:
                logging.error("You are trying to open more than 10 files, are you sure?")
                return
            from platform import system
            _os = system()
            if _os == "Windows":
                from subprocess import Popen
                for i in ids:
                    Popen(r'explorer /select,"{}"'.format(self.h5_db[i]))
            else:
                logging.error("File Manager currently only supported for Windows")
                return
    
        def remove_column(self, column):
            """
            If your data frame is getting too wide, you can remove single columns
            :param column: column name of your data frame
            :type str
            """
            self.df = self.df.drop([column], axis=1)
    
        def _on_row_selected(self, row):
            self._selected_df = self.grid.get_selected_df()
    
        def _on_openSelected_clicked(self, b):
            uuid = self._selected_df.index
            logging.info("Open qviekit with uuid:%s" % uuid)
            self.view(uuid)
    
        def _grid_observer(self, change):
            logging.debug('grid observer called, batch_update: ' + str(self._batch_update))
            c = self.grid
            keys = [i for i in list(c.df.keys()) if i != "qgrid_unfiltered_index"]
            if self._batch_update:
                self._batch_update = False
                changed_df = c.df
            else:
                changed_df = c.get_changed_df()
            try:
                uuids = [i for i in list(changed_df.index) if i in self.df.index]
                indices = np.where(self.df.loc[uuids, keys] != changed_df.loc[uuids, keys])
                logging.debug("I found {} changes".format(len(indices[0])))
                for i in range(len(indices[0])):
                    index = uuids[indices[0][i]]
                    key = keys[indices[1][i]]
                    new_value = changed_df.loc[index, key]
                    if self.df.loc[index, key] != new_value:
                        self._set_hdf_attribute(index, key, new_value)
                        logging.debug("{}[{}] '{}'-> '{}'".format(index, key, self.df.loc[index, key], new_value))
                        self.df.loc[index, key] = new_value
            except(ValueError, KeyError):
                logging.info("Updating the measurment database failed.")
                self.debug = [self.df.copy(), changed_df, keys]
    
        def _batch_change_attribute(self, b):
            tmp = self.grid.get_changed_df()
            tmp.loc[self._selected_df.index, b.key_dd.value] = b.value_tf.value
            self._batch_update = True
            self.grid.df = tmp
    
        def show(self, show_raw=False):
            """
            used to show the data base as a qgrid object or if not installed pandas data frame
            :return: data frame as qgrid object or pandas object
            """
            self.wait()
            if self.found_qgrid:
                if LooseVersion(qd.__version__) < LooseVersion("1.3.0") and LooseVersion(pd.__version__) >= LooseVersion("1.0"):
                    logging.warning("qgrid < v1.3 is incompatible with pandas > v1.0. Check for a new version of qgrid or downgrade pandas to v0.25.3")
                    self.found_qgrid = False
            if self.found_qgrid:
                from IPython.display import display
                import ipywidgets as widgets
                rows = [d for d in self.column_sorting if d in list(self.df.keys()) and d not in self.columns_ignore]
                rows += [d for d in list(self.df.keys()) if d not in self.column_sorting and d not in self.columns_ignore]
            
                _openSelected = widgets.Button(description='open selected', disabled=False,
                                               button_style='', tooltip='open selected')
                _openSelected.on_click(self._on_openSelected_clicked)
            
                _batch_modifier = widgets.Button(description='for all selected rows',
                                                 tooltip='Change the selected attribute to the specified value for all rows selected.')
                _batch_modifier.key_dd = widgets.Dropdown(options=rows, description="Set")
                _batch_modifier.value_tf = widgets.Text(value='', placeholder='Value', description='to:')
                _batch_modifier.on_click(self._batch_change_attribute)
            
                display(widgets.HBox([_openSelected, _batch_modifier.key_dd, _batch_modifier.value_tf, _batch_modifier]))
            
                if show_raw or "rating" not in self.df.keys():
                    df = self.df.copy()
                else:
                    df = self.df.copy()[pd.to_numeric(self.df['rating']) > 0]
                self.grid = qd.show_grid(df[rows], show_toolbar=False, grid_options={'enableColumnReorder': True})
                self.grid.observe(self._on_row_selected, names=['_selected_rows'])
                self.grid.observe(self._grid_observer, names=[
                    '_selected_rows'])  # Quick fix to also work with newer versions of qgrid. Should be changed to the .on() event mechanism at some point, but this requires newer qgrid version.
                return self.grid
            else:
                if show_raw or "rating" not in self.df.keys():
                    return self.df
                else:
                    return self.df[self.df['rating'] > 0]
    
        def get_filtered_uuids(self):
            """
            Thsi function gives you a list of UUIDs in your current view.
            If you have selected more than one line, only the selection is returned.
            Otherwise, all measurements in the current view are given.
            This is especially handy if you did some filtering beforehand
            
            This of course only works if qgrid is installed.
            
            :return: list of UUIDs
            """
            if self.found_qgrid:
                if len(self._selected_df) > 1:
                    return list(self._selected_df.index)
                else:
                    return list(self.grid.get_changed_df().index)
            else:
                logging.warning("Module qgrid is not installed. Filtering the database is only supported with qgrid.")
                return False
        
        def search(self, column, expression=None, value=None, bounds=None):
            """
            allows you to search a specific column for either a string, a value, or values within bounds.
            You have to pass exactly one variable. If you are only looking for the uids write ".index" behind it.
            :param column: name of the column you want to search
            :type str
            :param expression: if you wanna search for a string use this
            :type str
            :param value: if you wanna search for a value use this
            :type int or float
            :param bounds: list of lower and upper bound
            :type int
            :return: pandas data frame where the values you are searching for are included
            """
            if expression is not None and value is None and bounds is None:
                return self.df[self.df[column].str.contains(expression, na=False)]
            if value is not None and expression is None and bounds is None:
                print([self.df[column] == value])
                return self.df[self.df[column] == value]
            if bounds is not None and value is None and expression is None:
                return self.df[((self.df[column] > bounds[0]) & (self.df[column] < bounds[1]))]
            else:
                print("You have to pass exactly one variable")
    
        def add_column(self, colname, value=" "):
            """
            Add a new (empty) column to your dataframe. This will be displayed in the view after qkit.fid.show() and you can manipulate the individual values there.
            :param colname: Name of your column. A ValueError is raised if this already exists.
            :param value: Default value for all entries. Should not be empty string '' but space ' ' as changes can not be detected otherwise.
            """
            if colname in self.df:
                raise ValueError("Column {} is already in your dataset. Can not be added twice".format(colname))
            else:
                self.df.loc[:, colname] = pd.Series(value, index=self.df.index)
    else:
        # If pandas is not installed, raise an error if the public functions are called
        
        def void_func(self):
            raise ImportError("This function requires pandas to be installed.")

        add_settings_column = open_in_filemanager = remove_column = show = get_filtered_uuids = search = add_column = void_func

    def enlarge_notebook(self,width=100):
        from IPython.core.display import display, HTML
        display(HTML("<style>.container { width:%i%% !important; }</style>"%width))