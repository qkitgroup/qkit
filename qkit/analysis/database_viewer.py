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
import numpy as np
import logging
try:
    import qgrid as qd
except(ImportError):
    print 'qgrid required for nice tables'


class Database_Viewer():
    """class that creates a pandas data frame from your measurement
    data and allows to extract import values from h5-files"""

    def __init__(self):
        """instantiate a pandas dataframe from with the help of qkit.store_db"""
        self._update_database()
        self.df = pd.DataFrame()
        self._initiate_basic_df()

    def _update_database(self):
        """
        updates the database to find new added values. However if there are new measurements
        a new Database_Measurements object has to be initiated yet
        """
        qkit.store_db.update_database()
        self.db = qkit.store_db.h5_db

    def _initiate_basic_df(self):
        """
        reads out timestamp, name, run, user, comment from database and creates the dataframe
        """
        for i, j in self.db.items():
            try:
                dt = qkit.storage.hdf_DateTimeGenerator.decode_uuid(str(i))
                timestamp = pd.to_datetime(dt, unit='s')
                j_split = (j.replace('/', '\\')).split('\\')
                name = j_split[-1][7:-3]
                user = j_split[-3]
                run = j_split[-4]
                h5tmp = st.Data(qkit.store_db.h5_db[i])
                tmp = h5tmp.hf['/entry/data0']
                comment = tmp.attrs.get('comment')
                h5tmp.close()
                dftemp = pd.DataFrame({'timestamp': timestamp, 'run': run, 'user': user, 'name': name, 'comment': comment},
                                  index=[i])
                self.df = self.df.append(dftemp)
            except ValueError as e:
                    logging.error("database viewer: %s"%e)
        
        self.df = self.df[['timestamp', 'name', 'run', 'user', 'comment']]

    def _get_settings_column(self, device, setting, uid=None):

        dfsetting=pd.DataFrame()
        if uid is None:
            uid = self.df.index
        for i in uid:
            try:
                data = pd.read_csv(self.db[i].replace('.h5', '.set'), sep=' ', header=0, names=["Settings", "Values"])
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
            dftemp=pd.DataFrame({device + ' ' + setting: value}, index=[i])
            dfsetting=dfsetting.append(dftemp)
        return dfsetting

    def add_settings_column(self, device, setting, measurement_id=None):
        """
        Reads out a specific setting from your chosen device. If you provide a uid,
        then only these files will be considered
        :param device: your device name
        :type string
        :param setting: setting of your device
        :type string
        :param uid: measurement_id (list). If None (default), all are used
        :type string
        """
        settings_column=self._get_settings_column(device, setting, measurement_id)
        self.df=pd.concat([self.df, settings_column],axis=1)

    def add_fit_column(self, fit_variable, uid=None):
        """
        Extract fit_values of a chosen fit_variable from the h5-files if data has been fitted with the dat_reader
        :param fit_variable: fit_variable as specified in the dat_reader
        :param uid: measurement_id (list), if None (default) all are used
        :type string
        """
        self._update_database()
        if fit_variable in self.df.columns:  # avoiding more than one rating column after new ratings have been added
            self.remove_column(fit_variable)
        df_fit_value = pd.DataFrame()
        if uid is None:
            uid=self.df.index
        for i in uid:
            h5tmp = st.Data(qkit.store_db.h5_db[i])
            try:
                index = h5tmp.analysis.dr_values.attrs.get('comment').split(', ').index(fit_variable)
                fit_data = h5tmp.analysis.dr_values[index]
            except AttributeError:
                fit_data = None
            dftemp = pd.DataFrame({fit_variable: fit_data}, index=[i])
            df_fit_value = df_fit_value.append(dftemp)
        self.df = pd.concat([self.df, df_fit_value], axis=1)

    def remove_column(self, column):
        """
        If your data frame is getting too wide, you can remove single columns
        :param column: column name of your data frame
        :type string
        """
        self.df = self.df.drop([column], axis=1)

    def show_database(self):
        """
        used to show the data base as a qgrid object. This function requires a working qgrid
        :return: data frame as qgrid object
        """
        grid=qd.show_grid(self.df, grid_options={'editable': False}, show_toolbar=False)
        return grid

    def search(self, column, expression=None, value=None, bounds=None):
        """
        allows you to search a specific column for either a string, a value, or values within bounds.
        You have to pass exactly one variable. If you are only looking for the uids write ".index" behind it.
        :param column: name of the column you want to search
        :type string
        :param expression: if you wanna search for a string use this
        :type string
        :param value: if you wanna search for a value use this
        :type int or float
        :param bounds: list of lower and upper bound
        :type int
        :return: pandas data frame where the values you are searching for are included
        """
        if expression is not None and value is None and bounds is None:
            return self.df[self.df[column].str.contains(string, na=False)]
        if value is not None and expression is None and bounds is None:
            print [self.df[column] == value]
            return self.df[self.df[column] == value]
        if bounds is not None and value is None and expression is None:
            return self.df[((self.df[column] > bounds[0]) & (self.df[column] < bounds[1]))]
        else:
            print "You have to pass exactly one variable"

    def set_rating(self, uid, rating):
        """
        If you want to rate your measurements, so you can filter for good ones. You can add a rating into the analysis
        folder of the h5 file
        :param uid: uid of the measurement file you wanna rate
        :type basestring
        :param rating: a simple value to rate your measurement
        :type int, float
        """
        h5tmp = st.Data(qkit.store_db.h5_db[uid])
        ds = h5tmp.add_value_vector('rating', folder='analysis')
        ds.add([rating])
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
            uid=self.df.index
        for i in uid:
            h5tmp = st.Data(qkit.store_db.h5_db[i])
            try:
                rating = h5tmp.analysis.rating[0]
            except(AttributeError):
                rating = None
            h5tmp.close()
            dftemp = pd.DataFrame({'rating': rating}, index=[i])
            dfrating = dfrating.append(dftemp)
        self.df = pd.concat([self.df, dfrating], axis=1)







