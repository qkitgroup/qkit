# filename: database_viewer.py
# Tim Wolz <tim.wolz@kit.edu>, 01/2018
# keeping track of your measurement files within a Jupyter notebook


# import and basic usage
"""
import qkit.analysis.database_viewer as dv
dbv= dv.Database_Viewer()
dbv.show_database() # with qgrid
dbv.df              # without qgrid
"""

# qgrid is an interactive jupyter tool for pandas dataframe, which helps filtering your data
# for more information see https://github.com/quantopian/qgrid
# script works also well without qgrid
# you can simply access all the data via pandas commands, i.e., dbv.df.columnname['uid']

# for further information see doc strings


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import pandas as pd
import qkit
import qkit.storage.store as st
import h5py
import numpy as np
import logging
import threading

try:
    import qgrid as qd
    found_qgrid = True
except ImportError:
    found_qgrid = False


class DatabaseViewer:
    """class that creates a pandas data frame from your measurement
    data and allows to extract import values from h5-files"""

    def __init__(self):
        """instantiate a pandas dataframe from with the help of qkit.store_db"""
        self.scan_h5 = qkit.cfg.get('file_service_scan_hdf', False)
        self._initiate_basic_df_threaded()

    def _update_database(self):
        """
        updates the database to find newly added measurement_files.
        """
        qkit.store_db.update_database()
        self._initiate_basic_df()

    def _initiate_basic_df(self):
        """
        creates the dataframe
        """
        qkit.store_db.updating_db.wait(40)
        if len(qkit.store_db.h5_info) is 0: # necessary if a data directory is chosen without any h5 file
            self.df = pd.DataFrame(columns=['datetime', 'name', 'run', 'user'])
        else:
            self.df = pd.DataFrame(qkit.store_db.h5_info).T
        if self.scan_h5:
            self.df = self.df[['datetime', 'name', 'run', 'user', 'comment', 'fit_time', 'fit_freq', 'rating']]
            self.df['rating'] = pd.to_numeric(self.df['rating'], errors='coerce')
            self.df['fit_time'] = pd.to_numeric(self.df['fit_time'], errors='coerce')
            self.df['fit_freq'] = pd.to_numeric(self.df['fit_freq'], errors='coerce')
        else:
            self.df = self.df[['datetime', 'name', 'run', 'user']]
        self.df['datetime'] = pd.to_datetime(self.df['datetime'], errors='coerce')

    def _get_settings_column(self, device, setting, uid=None):
        dfsetting = pd.DataFrame()
        if uid is None:
            uid = self.df.index
        for i in uid:
            try:
                data = pd.read_csv(qkit.store_db[i].replace('.h5', '.set'), sep=' ', header=0, names=["Settings", "Values"])
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

    def show(self):
        """
        used to show the data base as a qgrid object or if not installed pandas data frame
        :return: data frame as qgrid object or pandas object
        """
        if found_qgrid:
            self.grid = qd.show_grid(self.df, show_toolbar=False, grid_options={'enableColumnReorder': True})
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
        try:
            h5tmp = st.Data(qkit.store_db.h5_db[uid])
            ds = h5tmp.add_value_vector('rating', folder='analysis')
            ds.add([rating])
        finally:
            h5tmp.close()

    def add_ratings_column(self, uid=None):
        """
        adds a column with your previously defined ratings in the h5-file to the data frame, so you can filter for them
        :param uid: List of uids. If None (default) all are used.
        :return: None
        """
        self._update_database()
        if 'rating' in self.df.columns:  # avoiding more than one rating column after new ratings have been added
            self.remove_column('rating')
        dfrating = pd.DataFrame()
        if uid is None:
            uid = self.df.index
        for i in uid:
            h5tmp = st.Data(qkit.store_db.h5_db[i])
            try:
                rating = h5tmp.analysis.rating[0]
            except(AttributeError):
                rating = None
            finally:
                h5tmp.close()
            dftemp = pd.DataFrame({'rating': rating}, index=[i])
            dfrating = pd.concat([dfrating, dftemp])
        self.df = pd.concat([self.df, dfrating], axis=1)

    def _initiate_basic_df_threaded(self):
        t1 = threading.Thread(name= 'initiate_data_df', target=self._initiate_basic_df)
        t1.start()
