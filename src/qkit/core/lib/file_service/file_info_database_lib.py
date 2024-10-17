import qkit

import os
import threading
import logging
import time
import json
import numpy as np
import qkit.storage.hdf_DateTimeGenerator as dtg
from qkit.core.lib.file_service.breadcrumbs import BreadCrumbCreator
import h5py

try:
    import cPickle as pickle
except:
    import pickle

class UUID_base(object):
    _alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def get_uuid(self,time):
        """
        
        returns a UUID from a given time, e.g. returned by time.time()
        The UUID is returned with a precision of (integer) seconds 
        and has a fixed length of six characters.
        
        Derived from encode_uuid(), orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not value: value = self._unix_timestamp
        output = ''
        time = int(time)
        la = len(self._alphabet)
        while time:
            output += self._alphabet[time % la]
            time = int(time / la)
        return output[::-1]
    
    def get_time(self,uuid):
        """
        returns a integer time value from a given UUID timestamp (reverse of get_UUID())
        orginally located in hdf_DateTimeGenerator.py (AS/MP/HR)
        """
        # if not string: string = self._uuid
        output = 0
        multiplier = 1
        uuid = uuid[::-1].upper()
        la = len(self._alphabet)
        while uuid != '':
            f = self._alphabet.find(uuid[0])
            if f == -1:
                raise ValueError("fid.get_time: Can not decode this: {}<--".format(uuid[::-1]))
            output += f * multiplier
            multiplier *= la
            uuid = uuid[1:]
        return output
        
    def get_date(self,uuid):
        """
        Returns a date string from a given UUID timestamp (reverse of get_uuid())
        """
        return time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(self.get_time(uuid)))


class file_system_service(UUID_base):
    h5_db = {}
    set_db = {}
    measure_db = {}
    h5_info_db = {}

    _h5_n_mtime = {}
    
    _h5_mtime_db_path   = os.path.join(qkit.cfg['logdir'],"h5_mtime.db")
    _h5_info_cache_path = os.path.join(qkit.cfg['logdir'],"h5_info_cache.db")

    _breadcrumb_creator = BreadCrumbCreator()

    lock = threading.Lock()
    
    def _remove_cache_files(self):
        """
            remove cached files to recreate the database
        """
        for f in [self._h5_mtime_db_path,self._h5_info_cache_path]:
            if os.path.isfile(f):
                os.remove(f)

    def _load_cache_files(self):
        """ to speed up things, try to load the h5 
            information from previous runs. 
        """
        self._new_cache = False
        self._h5_mtime_db = {}
        self._h5_info_cache_db = {}
        self._n_mtime = {}
        try:
            with open(self._h5_mtime_db_path,'rb') as f:
                self._h5_mtime_db = pickle.load(f)
            with open(self._h5_info_cache_path,'rb') as f:
                self._h5_info_cache_db = pickle.load(f)
        except IOError as e:
            logging.info("m_time_db not found. Not using cached files for now. %s"%e)
            self._new_cache = True

    def _store_cache_files(self):
        """ writes the cached files on disk, 
        qkit.cfg['logdir'] is used by default.

        exeptions are not handled ... if something fails here 
        there is a severe general problem, e.g. the disk is full.
        """
        write_protocol = 2 # For Python 2 compatibility 0=text, 1...x binary, -1 highest binary. 
        with open(self._h5_mtime_db_path,'wb+') as f:
            pickle.dump(self._h5_n_mtime,f,protocol=write_protocol)
        with open(self._h5_info_cache_path,'wb+') as f:
            pickle.dump(self.h5_info_db,f,protocol=write_protocol)

    def _get_datadir(self):
        if qkit.cfg.get('fid_restrict_to_userdir',False):
            return os.path.split(dtg.DateTimeGenerator().new_filename()['_folder'])[0]
        else:
            return qkit.cfg['datadir']

    def update_file_db(self):
        with self.lock:
            start_time = time.time()
            self._load_cache_files()
            if qkit.cfg.get('fid_scan_datadir',True):
                qkit.cfg['fid_scan_datadir'] = True
                logging.debug("file info database: Start to update database.")
                for root, _ , files in os.walk(self._get_datadir()): # root, dirs, files
                    for f in files:
                        self._inspect_and_add_Leaf(f,root)
                logging.debug("file info database: Updating database done.")
            self._store_cache_files()
            print ("Initialized the file info database (qkit.fid) in %.3f seconds."%(time.time()-start_time))

    def _inspect_and_add_Leaf(self,fname,root):
        """
        inspect the filenames if .h5, .set or .measurement

        to speed up things, the files are only scanned 
        if something has changed (os.stat.m_time) on disk. 
        """

        # join to absolute path:
        fqpath = os.path.join(root, fname)

        # take the prefix ...
        uuid = fname[:6]

        # ... and check the suffix
        if fqpath[-3:] == '.h5':

            # save the path using uuids as an index
            # Note: All path entries with the same uuid are 
            # overwritten with the last found uuid indexed file
            self.h5_db[uuid] = fqpath
            self._breadcrumb_creator.append_entry(uuid, fqpath)

            # we only care about the mtime of .h5 files 
            mtime = os.stat(fqpath).st_mtime

            # store the file's modification time 
            self._h5_n_mtime[uuid] = mtime

            if mtime == self._h5_mtime_db.get(uuid,0):
                if self._h5_info_cache_db.get(uuid,0):
                    self.h5_info_db[uuid] = self._h5_info_cache_db.get(uuid)
                else:
                    self._collect_info(uuid, fqpath) # collect_info is expensive.
            else:
                self._collect_info(uuid, fqpath) # collect_info is expensive. 

        elif fqpath[-3:] == 'set':
            self.set_db[uuid] = fqpath
        elif fqpath[-3:] == 'ent':
            self.measure_db[uuid] = fqpath

    def _collect_info(self,uuid,path):
            tm = ""
            dt = ""
            j_split = (path.replace('/', '\\')).split('\\')
            name = j_split[-1][7:-3]
            if ord(uuid[0]) > ord('L'):
                try:
                    tm = self.get_time(uuid)
                    dt = self.get_date(uuid)
                    user = j_split[-3]
                    run = j_split[-4]
                except ValueError as e:
                    user = None
                    run = None
                    logging.info(e)
            else:
                tm = uuid
                try:
                    if j_split[-3][0:3] != 201:  # not really a measurement file then
                        dt = None
                    else:
                        dt = '{}-{}-{} {}:{}:{}'.format(j_split[-3][:4], j_split[-3][4:6], j_split[-3][6:], tm[:2], tm[2:4], tm[4:])
                except IndexError:
                    dt = None
                user = None
                run = None
            h5_info_db = {'time': tm, 'datetime': dt, 'run': run, 'name': name, 'user': user}
            
            if qkit.cfg.get('fid_scan_hdf', False):
                h5_info_db.update({'rating':10})
                try:
                    h5f=h5py.File(path,'r')
                    if "comment" in  h5f['/entry/data0'].attrs:
                        h5_info_db.update({'comment': h5f['/entry/data0'].attrs['comment']})
                    if "dr_values" in h5f['/entry/analysis0']:
                        try:
                            # this is legacy and should be removed at some point
                            # please use the entry/analysis0 attributes instead.
                            fit_comment = h5f['/entry/analysis0/dr_values'].attrs.get('comment',"").split(', ')
                            comm_begin = [i[0] for i in fit_comment]
                            try:
                                h5_info_db.update({'fit_freq': float(h5f['/entry/analysis0/dr_values'][comm_begin.index('f')])})
                            except (ValueError, IndexError):
                                pass
                            try:
                                h5_info_db.update({'fit_time': float(h5f['/entry/analysis0/dr_values'][comm_begin.index('T')])})
                            except (ValueError, IndexError):
                                pass
                        except (KeyError, AttributeError):
                            pass
                    if "measurement" in h5f['/entry/data0']:
                        try:
                            mmt = json.loads(h5f['/entry/data0/measurement'][0])
                            h5_info_db.update(
                                    {arg: mmt[arg] for arg in ['run_id', 'user', 'rating', 'smt'] if mmt.has_key(arg)}
                            )
                        except(AttributeError, KeyError):
                            pass
                    try:
                        h5_info_db.update(dict(h5f['/entry/analysis0'].attrs))
                    except(AttributeError, KeyError):
                        pass
                except KeyError as e:
                    logging.debug("fid could not index file {}, probably it is just new and empty. Original message: {}".format(path,e))
                except IOError as e:
                    logging.error("fid {}:{}".format(path,e))
                finally:
                    h5f.close()

            self.h5_info_db[uuid] = h5_info_db
    
    def add_h5_file(self, h5_filename):
        if qkit.cfg['fid_scan_datadir']:
            threading.Timer(20, function=self._add, kwargs={'h5_filename':h5_filename}).start()
        
    def _add(self, h5_filename):
        """
        Add a file to the database, where h5_filename should be the absolute filepath to the h5 file.
        """
        basename = os.path.basename(h5_filename)[:-2]
        dirname = os.path.dirname(h5_filename)
        uuid = basename[:6]
        self._breadcrumb_creator.append_entry(uuid, h5_filename)
        if h5_filename[-3:] != '.h5':
            logging.error("Tried to add '{:s}' to the qkit.fid database: Not a .h5 filename.".format(h5_filename))
        with self.lock:
            if os.path.isfile(h5_filename):
                logging.debug("Store_db: Adding manually h5: " + basename + 'h5')
                self._inspect_and_add_Leaf(basename + 'h5', dirname)
            else:
                logging.error("Tried to add '{:s}' to the qkit.fid database: File does not exist.".format(h5_filename))
            if os.path.isfile(h5_filename[:-2] + 'set'):
                logging.debug("Store_db: Adding manually set: " + basename + 'set')
                self._inspect_and_add_Leaf(basename + 'set', dirname)
            if os.path.isfile(h5_filename[:-2] + 'measurement'):
                logging.debug("Store_db: Adding manually measurement: " + basename + 'measurement')
                self._inspect_and_add_Leaf(basename + 'measurement', dirname)
        self.update_grid_db()


    def _set_hdf_attribute(self,UUID,attribute,value):
        h5_filepath = self.h5_db[UUID]
        h = h5py.File(h5_filepath,'r+')['entry']
        try:
            if not 'analysis0' in h:
                h.create_group('analysis0')
            if value=="":
                if attribute in h['analysis0'].attrs:
                    del h['analysis0'].attrs[attribute]
            else:
                if qkit.module_available['pandas']:
                    import pandas as pd
                    if pd.isnull(value):
                        if attribute in h['analysis0'].attrs:
                            del h['analysis0'].attrs[attribute]
                    else:
                        h['analysis0'].attrs[attribute] = value
                else:
                    h['analysis0'].attrs[attribute] = value
        finally:
            h.file.close()
        self.h5_info_db[UUID].update({attribute:value})
        
    def wait(self):
        with self.lock:
            pass
        qkit.flow.sleep(.1) #to prevent timing issues
        if self.lock.locked():
            self.wait()
        return True