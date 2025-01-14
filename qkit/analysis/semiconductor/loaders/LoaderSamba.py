import urllib
from smb.SMBHandler import SMBHandler # pip install pysmb 

class LoaderSamba:
    """Loads from a samba smb:// filepath.
    """  
    def load(self, filepath):
        director = urllib.request.build_opener(SMBHandler)
        fh = director.open(filepath)
        data = fh.read()
        fh.close()

        return data