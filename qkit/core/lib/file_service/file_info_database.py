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



import qkit
import os

import threading
import logging
import time
import json
import numpy as np

try:
    import pandas as pd
    import qgrid as qd
    found_qgrid = True
except ImportError:
    found_qgrid = False

from file_info_database_lib import file_system_service

# display using qviewkit
from qkit.gui.plot.plot import plot

class fid(file_system_service):
    def __init__(self):
        self.column_sorting = ['datetime', 'name', 'run', 'user', 'comment', 'rating']
        self.columns_ignore = ['time']
        self.df = None
        # create initial database in the background. This can take a while...
        self.create_database()
            
    def __getitem__(self, key):
        with self.lock:
            return self.h5_db.get(key, None)
    
    def get(self, key, args=None):
        with self.lock:
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
        #print ("hallo",type(file_id))
        if file_id is None:
            return None
        elif type(file_id) is int:
            return(None)
        elif type(file_id) is pd.Index or  type(file_id) is list:
            for i in file_id:
                filepath = self.h5_db.get(i, False)
                if filepath:
                    plot(filepath, live=False)
        elif type(file_id) is str:
            filepath = self.h5_db.get(file_id, False)
            if filepath:
                plot(filepath, live=False)

    def create_database(self):
        t1 = threading.Thread(name='creating_db', target=self.update_all)
        t1.start()

    def update_all(self):
        """ updates file and grid database if activated
        """
        self.update_file_db()
        self.update_grid_db()

    def update_grid_db(self):
        with self.lock:
            if qkit.cfg.get('fid_init_viewer',True):
                qkit.cfg['fid_init_viewer'] = True
                self._initiate_basic_df()
            else:
                qkit.cfg['fid_init_viewer'] = False
    
    def _initiate_basic_df(self):
        """
        Creates a pandas data frame from your measurement
        data and allows to extract import values from h5-files
        """
        
        if len(self.h5_info_db) is 0: # necessary if a data directory is chosen without any h5 file
            self.df = pd.DataFrame(columns=['datetime', 'name', 'run', 'user'])
        else:
            self.df = pd.DataFrame(self.h5_info_db).T
            
        if qkit.cfg.get('fid_scan_hdf', False):
            #self.df = self.df[['datetime', 'name', 'run', 'user', 'comment', 'fit_time', 'fit_freq', 'rating']]
            for key in ['rating','fit_time','fit_freq']:
                if key in self.df.keys():
                    self.df[key] = pd.to_numeric(self.df[key], errors='coerce')
        else:
            self.df = self.df[['datetime', 'name', 'run', 'user']]
        self.df['datetime'] = pd.to_datetime(self.df['datetime'], errors='coerce')

    def _get_settings_column(self, device, setting, uid=None):
        dfsetting = pd.DataFrame()
        if uid is None:
            uid = self.df.index
        for i in uid:
            try:
                data = pd.read_csv(self.h5_db[i].replace('.h5', '.set'), sep=' ', header=0, names=["Settings", "Values"])
                # only looking at the right instrument
                all_ins_index = data.index[data['Settings']=='Instrument:']
                index_start = data.index[data['Values']==device][0]
                index_index = np.where(all_ins_index == index_start)[0]
                if all_ins_index[index_index][0] == index_start:
                    index_stop = len(data.index)
                else:
                    index_stop = all_ins_index[index_index+1][0]
                value_index = data.index[data['Settings']=='\t'+setting+':']
                value_index = value_index[np.where(np.isin(value_index, range(index_start, index_stop)))][0]
                try:
                    value = float(data.iloc[value_index, 1])
                except(ValueError):
                    value = data.iloc[value_index, 1]
            except(IOError, IndexError):
                value = None
            dftemp = pd.DataFrame({device + ' ' + setting: value}, index=[i])
            dfsetting = pd.concat([dfsetting,dftemp])
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
        settings_column=self._get_settings_column(device, setting, measurement_id)
        self.df=pd.concat([self.df, settings_column],axis=1)

    def remove_column(self, column):
        """
        If your data frame is getting too wide, you can remove single columns
        :param column: column name of your data frame
        :type str
        """
        self.df = self.df.drop([column], axis=1)

    def _on_row_selected(self,row):
        # index = row.new[0]
        self._selected_df = self.grid.get_selected_df()
        
    def _on_openSelected_clicked(self, b):
        uuid = self._selected_df.index
        logging.info("Open qviekit with uuid:%s"%uuid)
        self.view(uuid)
        
    def show(self):
        """
        used to show the data base as a qgrid object or if not installed pandas data frame
        :return: data frame as qgrid object or pandas object
        """
        if found_qgrid:
            from IPython.display import display
            import ipywidgets as widgets
            _openSelected = widgets.Button(description='open selected',disabled=False,
                                           button_style='',tooltip='open selected')
            display(_openSelected)
            _openSelected.on_click(self._on_openSelected_clicked)
            
            rows =  [d for d in self.column_sorting  if d     in list(self.df.keys()) and d not in self.columns_ignore]
            rows += [d for d in list(self.df.keys()) if d not in self.column_sorting  and d not in self.columns_ignore]
            self.grid = qd.show_grid(self.df[rows], show_toolbar=False, grid_options={'enableColumnReorder': True})
            self.grid.observe(self._on_row_selected, names=['_selected_rows'])
            return self.grid
        else:
            return self.df

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
            print [self.df[column] == value]
            return self.df[self.df[column] == value]
        if bounds is not None and value is None and expression is None:
            return self.df[((self.df[column] > bounds[0]) & (self.df[column] < bounds[1]))]
        else:
            print "You have to pass exactly one variable"

    def set_rating(self, uid, rating):
        """
        If you want to rate your measurements, so that you can filter for good ones. You can add a rating into the analysis
        folder of the h5 file
        :param uid: uid of the measurement file you wanna rate
        :type str
        :param rating: a simple value to rate your measurement
        :type int, float
        """
        """
        # Fixme: no qkit.store_db anymore
        try:
            h5tmp = st.Data(qkit.store_db.h5_db[uid])
        except Exception as e:    
            print(str(e)+': unable to open h5 file with uuid '+str(uid))
        else:
            h5tmp.hf.agrp.attrs['rating'] = rating
            h5tmp.close()
        """
        pass

    def add_ratings_column(self, uid=None):
        """
        adds a column with your previously defined ratings in the h5-file to the data frame, so you can filter for them
        :param uid: List of uids. If None (default) all are used.
        :return: None
        """
        #Fixme: not using qkit.store_db,etc.
        """
        if 'rating' in self.df.columns:  # avoiding more than one rating column after new ratings have been added
            self.remove_column('rating')
        dfrating = pd.DataFrame()
        if uid is None:
            uid = self.df.index
        for i in uid:
            h5tmp = st.Data(qkit.store_db.h5_db[i])
            rating = h5tmp.hf.agrp.get('rating', None)
            h5tmp.close()
            dftemp = pd.DataFrame({'rating': rating}, index=[i])
            dfrating = pd.concat([dfrating, dftemp])
        self.df = pd.concat([self.df, dfrating], axis=1)
        """
        pass
