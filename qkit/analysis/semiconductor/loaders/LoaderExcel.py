import pandas as pd
import numpy as np

class LoaderExcel():
    """Loads our special Excel file and packs each column in a dict. 
    """
    def load(self, path, ignored_rows, sample_name):
        self.data = []
        df = pd.read_excel(path, skiprows=np.arange(ignored_rows))
        for measurement in range(len(df["Biascooling (V)"].to_numpy())):
            self.data.append({"bias_V" : df["Biascooling (V)"].to_numpy()[measurement],
                        "cooldown_nr" : df["Cooldown"].to_numpy()[measurement],
                        "person" : df["Person"].to_numpy()[measurement],
                        "first_acc_V" : df["Left demod0. gates (V)"].to_numpy()[measurement],
                        "date" : df["Date Start"].to_numpy()[measurement],
                        "RT_cooldown" : df["RT cooldown"].to_numpy()[measurement],
                        "sample" : sample_name,
                        "second_acc_V" : "",
                        "SET_left_TG" : df["Links demod0. TG G4 (V)"].to_numpy()[measurement],
                        "SET_left_G5" : df["G5"].to_numpy()[measurement],
                        "SET_left_G7" : df["G7"].to_numpy()[measurement],
                        "SET_right_TG" : df["Rechts demod4. G14 TG (V)"].to_numpy()[measurement],
                        "SET_right_G15" : df["G15"].to_numpy()[measurement],
                        "SET_right_G17" : df["G17"].to_numpy()[measurement],
                        "SET_other_gates" : df["Other gates (V)"].to_numpy()[measurement],
                        }) 
        return self.data


