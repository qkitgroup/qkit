# Parameters for magnets that are ramped using ADwin outputs:
translation_factor_x = 1.5 #factor (Ampere/Volts) that is used by the current sources from input to output
translation_factor_y = 1.5
translation_factor_z = 1.5


# 3D vector system by Julian:
x_calib = 0.18099845 #in Tesla/Amps
y_calib = 0.05994 #in Tesla/Amps
z_calib = 0.06324 #in Tesla/Amps

x_max_current = 5.6 # maximal current in Amps through coil x before quench
y_max_current = 5.4 # maximal current in Amps through coil y
z_max_current = 5.1 # maximal current in Amps through coil z



# 1D coil
#x_calib = 0.243780510641038  #0.24108176 #in Tesla/Amps
#y_calib = 1 #in Tesla/Amps
#z_calib = 1 #in Tesla/Amps

#x_max_current = 9.5 # Max by Thomas: 10.0A, quench @ 10.3A # maximal current in Amps through coil x before quench
#y_max_current = 0 # maximal current in Amps through coil y
#z_max_current = 0 # maximal current in Amps through coil z
