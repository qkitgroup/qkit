import pickle

class SaverPickle:
    """Saves data to Pickle.
    """  
    def save(self, settings, data):
        path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/data_pickle"
        file = open(path, "wb")
        pickle.dump(data, file, pickle.HIGHEST_PROTOCOL)
        file.close()

