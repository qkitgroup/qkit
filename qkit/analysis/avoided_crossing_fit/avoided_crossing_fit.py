'''
Avoided crossing module (ASt@KIT 2016):
	Contains:
	
		avoided_crossing: Function of an avoided crossing (as given by theory). Useful for plotting fits etc.
		
		avoided_crossing_peakdata: Takes a 2D input to calculate the peak positions of the crossing, as well as an educated guess
									of the initial parameters. Also provides the option to excecute a fit using crossing_fit.
									
		crossing_fit: Crossing to the peak data.
'''

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, sys, time
import logging

import numpy as np

import matplotlib.pyplot as plt

import scipy.constants as sc
import scipy.optimize as fit
import scipy.ndimage as scd

_dr_import = False
try:
	from qkit.analysis import dat_reader as dr
	_dr_import = True
except:
	logging.warning("dat_reader not found.")


def avoided_crossing(x, par=[1, 1, 1, 1], vz = 1):
	'''
	Avoided crossing function:
	par0=w1, par1=w2, par2=a (amplitude of tuning), par3=d (XX-interaction=0.5*maximal splitting)
	'''
	vz /= np.abs(vz)
	return (par[0]+par[1]+par[2]*x)/2+vz*np.sqrt(((par[0]+par[1]+par[2]*x)/2)**2-(par[0]+par[2]*x)*par[1]+par[3]**2)
	
# =================================================================================================================
	
#fit function for extrapolating the 2 segments
def _line(x, a, b):
	return a*x+b

# =================================================================================================================	
	
#Estimate crossing point and do rough fit
def _rough_fit(x1, x2, z1, z2):
	'''
	Avoided crossing function:
	par0=w1, par1=w2, par2=a (amplitude of tuning), par3=d (XX-interaction=0.5*maximal splitting)
	'''
	if np.mean(z1) > np.mean(z2):
		x1, x2 = x2, x1
		z1, z2 = z2, z1
		
	rough_fit = crossing_fit(x1, x2, z1, z2, show_plot = False, show_fitdata = False)[0]
		
	guess = rough_fit
	seg_params = np.array([0.5*guess[2], (guess[1]+guess[0])/2])
		
	return seg_params, guess
	
# =================================================================================================================

#Calculate delimiter
def _del_val(par, x, y):
	'''
	Calculate delimiter.
	'''
	xlen = np.size(x)
	ylen = np.size(y)
	
	delimiter = ((_line(x, par[0], par[1]) - min(y)*np.ones(xlen))*float(ylen-1)/(max(y)-min(y)))
	
	i = 0
	while delimiter[i] >= ylen or delimiter[i] < 0:
		delimiter[i] = 0
		i += 1
	
	i = xlen-1
	while delimiter[i] >= ylen or delimiter[i] < 0:
		delimiter[i] = ylen
		i -= 1
	
	delimiter = delimiter.astype(int)
	return delimiter
	
# =================================================================================================================



def _segmentation(x, y, z, threshold, sigma = 5, data_type = 0):
	'''
	This function calculates the "segments" of the data, i.e. the regions where the two curves of the crossing lie, which is 
	achieved with the following steps:
	- Take every value in the 2d array (or its derivative in case of the phase) which is larger than a given threshold and generate
	a boolean array.
	- Check if there is more than one "region" (i.e. an array of 1's which is not interrupted by a 0) and take the delimiter between
	them.
		1. case: There are slices where multiple peaks appear:
		-> Interpolate the delimiters linearly to get a better boundary, if this is not possible proceed as in case 2.
		2. case: There are no slices with multiple peaks:
		-> Check for the point where the two curves meet (in x direction).
		-> Take the maximum in the slices to the left and right respectively and execute a rough fit.
		-> Use the results from the rough fit to calculate the delimiter (which is a very steep line in this case)	
	
	-Visualize everything with the "segment" array:
	 Grey areas represent points in original array which are above the threshold.
	 Red and blue parts indicate association with a segment, ideally one curve should lie completely in the red, the other one in the
	 blue segment.
	 
	 Returns:
		segment: 2D array for visualization.
		delimiter: 1D array of the points delimiting the two curves.
		seg_par: parameters 
		guess: Initial guess of the parameters
	'''

	#threshold is the limit for limit for filtering the data
	xlen = np.size(x)
	ylen = np.size(y)
	
	if data_type == 0:
		dz = np.abs(np.gradient(z)[0])
	else:
		dz = z
	
	#Convolute data with gaussian function to reduce noise 
	dz = scd.filters.gaussian_filter1d(dz.T, sigma).T
	
	#Create segment depending on the value of threshold
	segment = np.logical_not(dz > threshold)
	
	delimiter = np.zeros(xlen)
	
	#Check how many dips are in a slice
	for j in range(0, xlen-1):
		i = 0
		lok_bool = 0
		lok_var = 0
		while not delimiter[j] and i < ylen:
			if not segment[i, j] and not lok_bool and not lok_var:
				lok_bool = 1
			elif segment[i, j] and lok_bool:
				lok_bool = 0
				lok_var = i
			elif not segment[i, j] and lok_var:
				delimiter[j] = int((i + lok_var)/2)
			i+=1
	
	delim_nonzero = np.nonzero(delimiter)[0]
	#extrapolate delimiter, find regions, only possible if delimiter has sufficient points:
	
	fit_success = False
	
	if np.size(delim_nonzero) > 0:
		if np.size(delim_nonzero) > 3:
			try:
				seg_par,seg_pcov = fit.curve_fit(_line, x[delim_nonzero], delimiter[delim_nonzero],
				p0=[max(delimiter), np.sum(np.gradient(delimiter[delim_nonzero]))])
				
				
				#change seg_par from index values to freq values
				seg_par *= (max(y)-min(y))/float(ylen-1)
				seg_par[1] += min(y)
				
				#extrapolate delimiter
				#->Look for 0 elements in delimiter which are not at the start or the end, which can happen if the threshold is to low in the crossing region.
				delimiter[min(delim_nonzero):max(delim_nonzero)+1] = _del_val(seg_par, x[min(delim_nonzero):max(delim_nonzero)+1], y)
				delimiter = delimiter.astype(int)
				delim_nonzero = np.nonzero(delimiter)[0]
				
				
				seg_par[0] *= (y[-1] - y[0])/np.abs(y[-1] - y[0])
				
				#Give an educated guess with delimiter parameters
				guess = np.array([(np.mean(y[delimiter[delim_nonzero].astype(int)])-2*seg_par[0]*(np.mean(x[delim_nonzero]))), #par0
								 np.mean(y[delimiter[delim_nonzero].astype(int)]), #par1
								 2*seg_par[0], #par2
								 0]) #par3
				
				
				delimiter[max(delim_nonzero)+1:] = ylen
				
				fit_success = True
				
			except:
				print("Not enough points to extrapolate delimiter.")
				print("Excecuting rough fit to determine shape.")
				
		if not fit_success:
			z_max  = y[np.argmax(np.abs(np.gradient(z)[0]),axis = 0)]
			x1, x2 = x[0:min(delim_nonzero)], x[max(delim_nonzero)+1:xlen]
			z1, z2 = z_max[0:min(delim_nonzero)], z_max[max(delim_nonzero)+1:xlen]
			try:
				seg_par, guess = _rough_fit(x1, x2, z1, z2)
				delimiter[min(delim_nonzero):max(delim_nonzero)+1] = _del_val(seg_par, x[min(delim_nonzero):max(delim_nonzero)+1], y)
				delim_nonzero = np.nonzero(delimiter)
				delimiter[max(delim_nonzero)+1:] = ylen
			except:
				print("Rough fit did not work. Please change threshold or prepare data manually and use crossing_fit routine"+
					  " or try changing threshold and sigma..")
	
	else:
		z_max  = y[np.argmax(np.abs(np.gradient(z)[0]), axis = 0)]
		zmax = np.argmax(np.gradient(z_max)/np.gradient(x))
		x1, x2 = x[0:zmax], x[zmax+1:xlen]
		z1, z2 = z_max[0:zmax], z_max[zmax+1:xlen]
		try:
			seg_par, guess = _rough_fit(x1, x2, z1, z2)
		except:
			print "Rough fit did not work. Please change threshold or prepare data manually and use crossing_fit routine."
			return np.logical_not(dz > threshold), 0, 0, 0
		
		delimiter[zmax] = _del_val(seg_par, x[zmax], y)
		delim_nonzero = np.nonzero(delimiter)[0]
		delimiter[zmax+1:] = ylen
		
			
	#Fill segment
	segment = np.zeros((ylen, xlen))
	for j in range(0, xlen):
		segment[delimiter[j]:, j] = np.ones(ylen - delimiter[j])
	
	seg_sgn = ((np.median(np.where(np.logical_not(dz > threshold)[:, np.where(delimiter == ylen)[0]] == False)[0])-
			   np.median(np.where(np.logical_not(dz > threshold)[:, np.where(delimiter == 0)[0]] == False)[0]))/
			   np.abs((np.median(np.where(np.logical_not(dz > threshold)[:, np.where(delimiter == ylen)[0]] == False)[0])-
					  np.median(np.where(np.logical_not(dz > threshold)[:, np.where(delimiter == 0)[0]] == False)[0]))))
	
	#Display segmentation nicely
	segment = 2*(0.5*np.ones((ylen, xlen)) - segment)*np.logical_not(dz > threshold)*seg_sgn
	if seg_sgn == 1 and np.size(delim_nonzero) != 0:
		segment[:, delim_nonzero] *= -1
		
	return segment, delimiter, seg_par, guess
	
# =================================================================================================================	
	
def _threshold(z, data_type):
	'''
	Returns the threshold for the segmentation.
	'''
	
	if data_type == 0:
		z = np.abs(np.gradient(z)[0])
		z = scd.filters.gaussian_filter1d(z.T, sigma=5).T
	return np.mean(z)+np.std(z), np.amax(z), np.amin(z)
	
# =================================================================================================================

#Max finder
def _val_max(x, y, pos = 0, d_type = 0, mode = 'max'):
	'''
	Returns the position of the peak/dip, which is determined by means of a fit or simply via the maximum in the interval.
	'''
	
	if d_type == 0:
		y = np.abs(np.gradient(y))
	
	if mode == 'max':
		return x[np.argmax(y)]
		
	elif mode == 'fit':
		#Redirect system output from dat_reader to log file
		save_stdout = sys.stdout
		try:
			f = open("dat_reader_log_" + "{0[0]}_{0[1]}_{0[2]}".format(time.localtime()) + ".txt", "r")
			data = f.read()
		except:
			print "Creating logfile as " + "dat_reader_log_" + "{0[0]}_{0[1]}_{0[2]}".format(time.localtime()) + ".txt"
			f = open("dat_reader_log_" + "{0[0]}_{0[1]}_{0[2]}".format(time.localtime()) + ".txt","w").close()
			data = ''
				
		with open("dat_reader_log_"+"{0[0]}_{0[1]}_{0[2]}".format(time.localtime()) + ".txt","w") as f:
			f.write(data)
			sys.stdout = f
			f.write("x-Position: " + str(pos) + "\n")
			try:
				val = dr.fit_data(file_name = "dat_import", fit_function = "lorentzian", data_c = 1, show_plot = False, data = np.array([x,y]), nfile='dat')[0]
			except:
				val = x[np.argmax(y)]
			f.write("\n")
			print("peak position at " + str(val))
			f.write("\n\n")
		#Return to normal output:
		sys.stdout = save_stdout
				
		return val

# ================================================================================================================= 

def avoided_crossing_peakdata(x, y, z, data_type = 0, mode = 'max', save_fig = False):
	'''
	Input is:
		x: x axis parameter (e.g. current)
		y: frequency
		z: 2d matrix with phase or magnitude. IMPORTANT: z data (or gradient in case of phase) should have peeks not dips (add a "-").
		Should be fixed in future versions. Input phase data should already consider cable delay.
		data_type: Default is assumed to be phase (in order to find peak one needs to calculate a gradient in case of phase data),
		change to basically anything
		apart from 0 if you do not want gradient to be calculated.
		lorentzian 
		mode: Determines how the peaks are calculated. 'max' simply looks for the maximum value in the given interval. 'fit' uses 
		dat_reader 'fit_data' and fits a
		lorentzian function. dat_reader output is saved in a file.
		save_fig: If true and you also choose to run the fit the resulting image will be saved.
		
	Uses "_segmentation" to find out which parts of the z array should be used to calculate the peaks, also to find out which curve
	a peak belongs to.
	After segmentation the user is able to change the threshold and sigma for the Gaussian convolution manually. Automatic threshold
	finding fails freqently for noisy data. In this case generally a lower threshold is a better choice.
	This is only necessary if you are not happy with the result.
	In case everything is ok a fit to each slice in each region where a peak is expected determines the exact position of said peak.
	Finally an overlay of the original data with the peak values of the two curves is displayed.
	At last, you can decide whether you want to immediately execute a fit to the data.
	
	Returns:
		No immediate fit:
			peak_pos: 2D array, 2 columns for the peaks in 2 regions. Length is equal to length of x. Elements are 0 when there is 
			no peak.
			guess: Initial guess of the crossing parameters (see 'avoided_crossing' function).
		Immediate fit:
			See crossing_fit.
	'''
	
	y = y*10**-9   #frequency in GHz
	
	xlen = np.size(x)
	ylen = np.size(y)
	sigma = 5   #seems good
	
	if data_type == 0:
		c_label = '\phi'
	else:
		c_label = 'mag'
	
	if not _dr_import:
		mode = 'max'
	
	if xlen*ylen != np.size(z):
		print "x and y dimensions have to match z dimensions!"
		return np.zeros((xlen, 2)), np.zeros(4)
	
	threshold, tmax, tmin = _threshold(z, data_type)

	inpt = "" 
	while inpt != 'y':
		segment, delimiter, seg_par, guess = _segmentation(x, y, z, threshold, sigma, data_type)
		#Show segmentation and decide whether to proceed
		#Append x array by 1 element, if this is not done the last slice will not show with pcolormesh
		pltx = np.append(x, 2*x[-1] - x[xlen-2])
		plt.pcolormesh(pltx, y, segment, cmap = "coolwarm", vmin = segment.min(), vmax = segment.max())
		plt.colorbar()
		plt.axis([pltx.min(), pltx.max(), y.min(), y.max()])
		plt.show()
	
		print "threshold = {0}, min/max = {1}/{2}".format(threshold, tmin, tmax)
		
		inpt = raw_input("Change threshold? (t) Change gaussian sigma? (s) Proceed? (y) Abort? (Any other key)\n")
		if inpt == 't':
			threshold = input("Enter new threshold:")
		elif inpt == 's':
			sigma = input("Enter new sigma:")
		elif inpt != 'y':
			print "Process aborted."
			return np.zeros((xlen, 2)), np.zeros(4)
		elif inpt == 'y':
			print "\n\n"
		
			
			#If segmentation worked properly
			peak_pos = np.zeros((xlen,2))
			
			#Fill peak_pos with peak values from the respective segment
			i = 0
			while delimiter[i] == 0:
				p_index = int(0.5*(np.sign(np.mean(segment[:, i])) + 1))
				peak_pos[i, p_index] = _val_max(y[0:ylen], z[0:ylen, i], x[i], data_type, mode)
				i += 1
				
			j = xlen - 1
			while delimiter[j] == ylen:
				p_index = int(0.5*(np.sign(np.mean(segment[:, j])) + 1))
				peak_pos[j, p_index] = _val_max(y[0:ylen], z[0:ylen, j], x[j], data_type, mode)
				j -= 1
			
			for l in range(i, j+1):
				p_index = int(0.5*(np.sign(np.mean(segment[0:delimiter[l],l]))+1))
				peak_pos[l, p_index] = _val_max(y[0:delimiter[l]], z[0:delimiter[l], l], x[l], data_type, mode)
				peak_pos[l, not p_index] = _val_max(y[delimiter[l]:ylen], z[delimiter[l]:ylen, l], x[l], data_type, mode)
			
			
			index_p0 = np.where((peak_pos[:, 0] > _line(x, seg_par[0], seg_par[1])) & (peak_pos[:, 0] != 0))
			index_p1 = np.where((peak_pos[:, 1] < _line(x, seg_par[0], seg_par[1])) & (peak_pos[:, 1] != 0))
			peak_pos[index_p0, 1], peak_pos[index_p0, 0] = peak_pos[index_p0, 0], peak_pos[index_p0, 1]
			peak_pos[index_p1, 0], peak_pos[index_p1, 1] = peak_pos[index_p1, 1], peak_pos[index_p1, 0]
						
			
			#Guess half the minimal peak distance as coupling strength
			if np.size(delimiter[(delimiter != 0) & (delimiter != ylen)]) != 0:
				guess[3] = 0.5*min(np.abs(peak_pos[:, 0] - peak_pos[:, 1]))
				
			pltx = pltx - .5*(pltx[1]- pltx[0])*np.ones(pltx.shape)
			plt.pcolormesh(pltx, y, z, cmap = "coolwarm", vmin = z.min(), vmax = z.max())
			cbar = plt.colorbar()
			xlin = np.linspace(min(pltx), max(pltx), 100)
			plt.plot(xlin, avoided_crossing(xlin, guess, -1), "b", linewidth = 1)
			plt.plot(xlin, avoided_crossing(xlin, guess, +1), "r", linewidth = 1)
			plt.plot(x[np.nonzero(peak_pos[:, 0])[0]], peak_pos[np.nonzero(peak_pos[:, 0])[0], 0], "b*", markersize = 7)
			plt.plot(x[np.nonzero(peak_pos[:, 1])[0]], peak_pos[np.nonzero(peak_pos[:, 1])[0], 1], "r*", markersize = 7)
			
			plt.xlim(min(pltx), max(pltx))
			plt.ylim(min(y), max(y))
			plt.xlabel(r'$x_{par}\,(\mathrm{a.u.})$', fontsize = 15)
			plt.ylabel(r'$f\,(\mathrm{Hz})$', fontsize = 15)
			cbar.set_label(r'$'+c_label+'\,(\mathrm{a.u.})$', rotation='90', fontsize = 15, labelpad = 5)
			plt.show()
			inpt = raw_input("Continue with fit? (y/n)")
			if inpt == 'y':
				nz0=np.nonzero(peak_pos[:,0])[0]
				nz1=np.nonzero(peak_pos[:,1])[0]
				fdat, ferr= crossing_fit(x[nz0], x[nz1], peak_pos[nz0,0], peak_pos[nz1,1], show_plot = False, show_fitdata = True)
				
				plt.pcolormesh(pltx, y, z, cmap = "coolwarm", vmin = z.min(), vmax = z.max())
				cbar = plt.colorbar()
				plt.xlim(min(pltx), max(pltx))
				plt.ylim(min(y), max(y))
				plt.plot(xlin, avoided_crossing(xlin, fdat, -1), "b", linewidth = 1)
				plt.plot(xlin, avoided_crossing(xlin, fdat, +1), "r", linewidth = 1)
				plt.xlabel(r'$x_{par}\,(\mathrm{a.u.})$', fontsize = 15)
				plt.ylabel(r'$f\,(\mathrm{GHz})$', fontsize = 15)
				cbar.set_label(r'$'+c_label+'\,(\mathrm{a.u.})$', rotation='90', fontsize = 15, labelpad = 5)
				if save_fig:
					plt.savefig('avoided_crossing_'+"{0[0]}_{0[1]}_{0[2]}".format(time.localtime())+'.png', dpi = 500)
				plt.show()
				return fdat, ferr
			else:
				return peak_pos, guess

# ================================================================================================================= 
   
def _deviation(pars, x1, x2, y1, y2):
	'''
	Returns the deviation of the two peak data sets (x1, y1), (x2, y2) from the avoided crossing curve(s).
	'''
	dev1 = y1-avoided_crossing(x1, pars, -1)
	dev2 = y2-avoided_crossing(x2, pars, +1)
	return np.concatenate((dev1, dev2))

# ================================================================================================================= 

def crossing_fit(x_data1, x_data2, y_data1, y_data2, guess = [0, 0, 0, 0], show_plot = True, show_fitdata = True):
	'''
	Input is:
		x_data1, y_data1, x_data2, y_data2: Peak data sets. When using 'avoided_crossing_peakdata', remove 0 elements first 
		(e.g. peak_pos[np.nonzero(peak_pos)]). Be careful! If your frequency input is in Hz numerical errors might occur.
		guess: Initial guess of the parameters. If no input is given an appropriate guess will be calculated.
		show_plot: If true a plot is shown.
		show_fitdata: If true the fit results will be printed.
	
	Uses scipy.optimize.leastsq to calculate the optimal fit parameters.
		
	Returns:
		fit_params: Array containing the fit parameters.
		pcov: Array containing the standard deviation of the fit parameters.
	'''
	if np.size(x_data1) != np.size(y_data1) or np.size(x_data2) != np.size(y_data2):
		raise ValueError("x and y data need the same dimension.")
	
	if np.all(guess == 0): 
		guess = np.array([min(np.append(y_data1, y_data2))
						 -2*np.mean(gradient(np.append(y_data1, y_data2))*min(np.append(x_data1, x_data2))),#par0
						 np.mean(np.append(y_data1, y_data2)), #par1
						 2*(np.mean(gradient(y_data1)) + np.mean(gradient(y_data2))), #par2
						 np.abs(min(y_data2) - max(y_data1))/2]) #par3
	
	
	fit_params, pcov, infodict, message, ier = fit.leastsq(_deviation, guess, args = (x_data1, x_data2, y_data1, y_data2), full_output = True)
	
	#Multiply covariance matrix pcov with reduced chi squared to get error
	pcov *= sum(_deviation(fit_params, x_data1, x_data2, y_data1, y_data2)**2)/(float(np.size(y_data1) + np.size(y_data2)) - float(np.size(fit_params)))
	
	
	#Change coupling to always have +sign
	fit_params[3] = np.abs(fit_params[3])
	
	if show_plot:
		xmin, xmax = min(np.append(x_data1, x_data2)), max(np.append(x_data1, x_data2))
		ymin, ymax = min(np.append(y_data1, y_data2)), max(np.append(y_data1, y_data2))
		dx = 0.02*(xmax - xmin)
		dy = 0.02*(ymax - ymin)
		x = np.linspace(xmin - dx, xmax + dx, 150)
		plt.plot(x, avoided_crossing(x, fit_params, -1), "b", linewidth = 1)
		plt.plot(x, avoided_crossing(x, fit_params, 1), "r", linewidth = 1)
		plt.plot(x_data1, y_data1,  "b*", markersize = 7)
		plt.plot(x_data2, y_data2,  "r*", markersize = 7)
		plt.xlim(xmin - dx, xmax + dx)		  
		plt.ylim(ymin - dy, ymax + dy)
		
	if show_fitdata:
		print("w1 = ( {0:7.3f} +- {1:8.3f}) GHz".format(fit_params[0], (np.diag(pcov)[0])**0.5))
		print("w2 = ( {0:7.3f} +- {1:8.3f}) GHz".format(fit_params[1], (np.diag(pcov)[1])**0.5))
		print("a  = ( {0:7.3f} +- {1:8.3f}) GHz/[x]".format(fit_params[2], (np.diag(pcov)[2])**0.5))
		print("g  = ( {0:7.3f} +- {1:8.3f}) MHz".format(fit_params[3]*1000, 1000*(np.diag(pcov)[3])**0.5))
		
	return fit_params, pcov







