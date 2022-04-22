#%%
from qkit.analysis.semiconductor.plotters import PlotterBiascoolingAccumulation

bias_cool_data = [
    {"date" : "04.01.22", "sample" : "P35_B1", "bias_V" : -3, "first_acc_V" : -0.355, 
    "second_acc_V" : 0.11, "SET_TG_demod0" : 0.9, "SET_TG_demod4" : 1.8},

    {"date" : "08.01.22", "sample" : "P35_B1", "bias_V" : -3, "first_acc_V" : -0.150, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "12.01.22", "sample" : "P35_B1", "bias_V" : 0, "first_acc_V" : 0.630, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "14.01.22", "sample" : "P35_B1", "bias_V" : 0, "first_acc_V" : 0.640, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "19.01.22", "sample" : "P35_B1", "bias_V" : -1, "first_acc_V" : 0.025, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "21.01.22", "sample" : "P35_B1", "bias_V" : -1, "first_acc_V" : 0.008, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "24.01.22", "sample" : "P35_B1", "bias_V" : -1, "first_acc_V" : 0.100, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "27.01.22", "sample" : "P35_B1", "bias_V" : -0.5, "first_acc_V" : 0.394, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},

    {"date" : "03.02.22", "sample" : "P35_B1", "bias_V" : +0.5, "first_acc_V" : 1.055, 
    "second_acc_V" : None, "SET_TG_demod0" : None, "SET_TG_demod4" : None},
  
    ]


#%%
plotter = PlotterBiascoolingAccumulation()
plotter.plot(bias_cool_data)
# %%
