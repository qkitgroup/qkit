import os
import re

class DataInfo:

    RE_META = re.compile('\A\s*#\s*(\w+)\s*:\s*([\w\s,.:;]+)')
    RE_META_KEY = re.compile('\A\s*#\s*(\w+)\s*:')

    def __init__(self, fn):
        self._filename = None
        self._metadata = {}
        self.set_filename(fn)

    def set_filename(self, fn):
        self._filename = fn
        self.read_info()

    def get_filename(self):
        return self._filename

    def get_metadata(self):
        return self._metadata

    def read_info(self):
        self._metadata = {}
        self._metadata['header'] = []
        f = open(self._filename, 'r')
        for line in f:
            line = line.rstrip('\r\n')
            if not line.startswith('#') and line != '':
                break
            self._metadata['header'].append(line)

            m = self.RE_META.search(line)
            if m is not None:
                g = m.groups()
                self._metadata[g[0]] = g[1]
                continue

            m = self.RE_META_KEY.search(line)
            if m is not None:
                self._metadata[g[0]] = {}

        self._check_settings_file()

    def _check_settings_file(self):
        fn = os.path.splitext(self._filename)[0] + '.set'
        if os.path.exists(fn):
            self._metadata['settings'] = []
            f = open(fn)
            for line in f:
                line = line.rstrip('\r\n')
                self._metadata['settings'].append(line)

class Browser:

    def __init__(self, dir=None):
        self._dir = None
        self._entries = []
        self.set_dir(dir)

    def set_dir(self, dir):
        self._dir = dir
        self._entries = []
        self._walk_dir(self._dir, recurse=True)

    def get_entries(self):
        return self._entries

    def get_filenames(self, match='', starttime=None, endtime=None):
        '''
        Return filenames of entries matching 'match'. If match is an empty
        string it returns all filenames.
        Optionally, the 'starttime' and 'endtime' can be specified to select
        a specific range of the matched data files, based on the 6-digit
        timestamp at the front of a filename. 'starttime' and 'endtime' must
        be specified as a 6-digit string.
        '''

        usetimes = False
        if starttime is not None or endtime is not None:
            usetimes = True
            if starttime is None:
                starttime = '000000'
            if endtime is None:
                endtime = '240000'

        ret = []
        for info in self._entries:
            fn = info.get_filename()
            fnr = os.path.split(fn)[1]
            if not usetimes and fnr.count(match) > 0:
                ret.append(fn)
            elif usetimes and fnr.count(match) > 0 and starttime <= fnr[:6] <= endtime:
                ret.append(fn)
        ret.sort()
        return ret

    def get_entry(self, fn):
        for i in self._entries:
            if i.get_filename() == fn:
                return i
        return None

    def _walk_dir(self, dir, recurse=False):
        entries = os.listdir(dir)
        for i in entries:
            fullfn = os.path.join(dir, i)
            if os.path.isdir(fullfn):
                if recurse:
                    self._walk_dir(fullfn)
            else:
                fn, ext = os.path.splitext(i)
                if ext == '.dat':
                    self._add_data_entry(fullfn)

    def _add_data_entry(self, fn):
        self._entries.append(DataInfo(fn))

