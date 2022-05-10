import pickle

class LoaderPickle:
    """Extracts all data from pickle files and returns it.
    """  
    def load(self, settings):
        path = f"{settings['file_info']['absolute_path']}{settings['file_info']['date_stamp']}/{settings['file_info']['filename']}/data_pickle"
        file = open(path, "rb")
        data = pickle.load(file)
        file.close()

        return data

