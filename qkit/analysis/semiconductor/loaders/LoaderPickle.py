import pickle

class LoaderPickle:
    """Extracts all data from pickle files and returns it.
    """  
    def load(self, settings):
        path = (f"{settings['file_info']['absolute_path']}"
        f"{settings['file_info']['date_stamp']}/"
        f"{settings['file_info']['filename']}/"
        "data_pickle")
        
        with open(path, "rb") as file:
            data = pickle.load(file)

        return data
