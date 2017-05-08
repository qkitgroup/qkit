import os
import logging

##################
#### settings file
##################

class SettingsFile():
    '''
    This class will read a settingsfile, and make it available as dict.
    For initializing both the <filename>.dat and the <filename>.set are
    allowed.
    '''

    def __init__(self, filepath):

        path, ext = os.path.splitext(filepath)
        self._filepath = path + '.set'

        self._metadata = {}
        self._settings = {}

        if not os.path.isfile(self._filepath):
            logging.warning('"%s" does not exist' % self._filepath)
            return

        self._parse_settings_file()

    def _parse_settings_file(self):

        f = file(self._filepath, 'r')

        curins = None
        for line in f:

            #remove trailing spaces
            line = line.rstrip(' \n\r\t')

            if line[:9] == 'Filename:':
                self._metadata['filename'] = line[10:]
            elif line[:10] == 'Timestamp:':
                self._metadata['timestamp'] = line[11:]
            elif len(line) == 0:
                pass
            elif line[:11] == 'Instrument:':
                fields = line.split()
                curins = fields[1]
                self._settings[curins] = {}
            elif line[:1] == '\t':
                line = line.lstrip('\t')
                pos = line.find(':')
                label = line[:pos]
                value = line[pos+2:]

                try:
                    value = eval(value)
                except:
                    pass

                self._settings[curins][label] = value

        f.close()

    def get_instruments(self):
        return self._settings.keys()

    def get_settings(self, instrument=None):
        if instrument is None:
            return self._settings
        elif self._settings.has_key(instrument):
            return self._settings[instrument]
        else:
            logging.warning('instrument %s does not exist in settingsfile' % instrument)
            return False

    def get(self, instrument, setting):
        if self._settings.has_key(instrument):
            if self._settings[instrument].has_key(setting):
                return self._settings[instrument][setting]
            else:
                logging.warning('instrument %s does not have setting %s' % (instrument, setting))
                return False
        else:
            logging.warning('instrument %s does not exist in settingsfile' % instrument)
            return False
