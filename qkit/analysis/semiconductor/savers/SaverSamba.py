import urllib
from smb.SMBHandler import SMBHandler # pip install pysmb 

class SaverSamba:
    """Saves data to Pickle with a samba smb:// filepath.
    """  
    def save(self, filepath, data_in):
        director = urllib.request.build_opener(SMBHandler)
        fh = director.open(filepath, data=data_in)
        fh.close()