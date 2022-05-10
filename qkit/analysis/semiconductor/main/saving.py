import pathlib
import os


def create_saving_path(settings, name, filetype=".png"):
    """Creats a folder with the name of settings["file_info"]["savepath"] if it's not existent and returns path to it. 
    """
    path = os.path.join(settings['file_info']['absolute_path'], 
    settings['file_info']['date_stamp'], settings['file_info']['filename'], 
    settings['file_info']['savepath'])
    
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)
    path = os.path.join(path, name) + filetype
      
    return path

