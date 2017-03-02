# filename: dat_reader.py
# Jochen Braumueller <jochen.braumueller@kit.edu>, 01/2015
# updates: 2015, 06/2016
# data reading and fitting script mainly used during time domain measurements but also for various data post processing purpuses
# supported fit functions: 'lorentzian', 'lorentzian_sqrt', 'damped_sine', 'sine', 'exp', 'damped_exp'

# import and usage
"""
from qkit import dat_reader as dr
dr.fit_data(None, fit_function = 'exp')
"""
# for further information see doc strings


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

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import scipy.interpolate
#import fnmatch
import os, glob
import time
import logging

try:
    from qkit.storage import hdf_lib
except ImportError:
    logging.warning('hdf_lib not found')

no_do = False
try:
    import data_optimizer as do
except ImportError:
    logging.warning('data optimizer not available')
    no_do = True

no_qt = False
try:
    import qt
    data_dir_config = qt.config.get('datadir')
except ImportError:
    logging.warning('no qtLAB environment')
    no_qt = True


LORENTZIAN_SQRT = 0
LORENTZIAN = 1 
DAMPED_SINE = 2
SINE = 3
EXP = 4
DAMPED_EXP = 5

PARAMS = ( ['f0','k','a','offs'], #LORENTZIAN_SQRT
    ['f0','k','a','offs'], #LORENTZIAN
    ['fs','Td','a','offs','ph'], #DAMPED_SINE
    ['fs','a','offs','ph'], #SINE
    ['Td','a','offs'], #EXP
    ['fs','Td','a','offs','ph','d'] #DAMPED_EXP
    
)
    
    
'''
    rootPath = 'D:\\'
    pattern = '*.dat'
    
    for root, dirs, files in os.walk(rootPath):
        for filename in fnmatch.filter(files, pattern):
            print(os.path.join(root, filename))
'''

# =================================================================================================================

def find_latest_file(ftype=None):
    '''
    find latest file of type ftype in qt data directory
    priorize hdf file over dat file
    '''
    
    global no_qt
    
    '''
    no_qt = False
    data_dir_config = 'd:/qkit/qkit/analysis/data/'
    '''
    
    if ftype == None:
        ftype = 'h5'
    
    if no_qt:
        print 'Cannot retrieve datadir...aborting'
        return
    else:
        #extract newest file in specified folder
        data_dir = os.path.join(data_dir_config, time.strftime('%Y%m%d'))
        try:
            nfile = max(glob.iglob(str(data_dir)+'\*\*.'+ftype), key=os.path.getctime)   #find newest file in directory
        except ValueError:
            print 'no .%s file in todays directory '%ftype +str(data_dir)+':'

            i = 0
            while i < 10:
                data_dir = os.path.join(data_dir_config, time.strftime('%Y%m%d',time.localtime(time.time()-3600*24*(i+1))))   #check older directories
                try:
                    nfile = max(glob.iglob(str(data_dir)+'\*\*.'+ftype), key=os.path.getctime)
                    break
                except ValueError:
                    print 'no .%s file in the directory '%ftype +str(data_dir)
                    i+=1

            if i == 10:
                print 'no .%s files found within the last %i days...aborting' %(ftype,i)
                return
        except Exception as message:   #other exception than ValueError thrown
            print message
            return

    return str(nfile).replace('\\','/')

# =================================================================================================================

def read_hdf_data(nfile,entries=None, show_output=True):
    '''
    - read hdf data file, store data in 2d numpy array and return
    - entries (optional): specify entries in h5 file to be read and returned
    - returns numpy data array
    
    - the function is used by the function load_data as part of the general fitter fit_data
    - currently one can pass a set of keywords (entries) in the form of a string array ['string1',string2',...,'stringn']
      with stringi the keywords to be read and returned as numpy array
    - when no entries are specified, read_hdf_data looks for a frequency axis or a pulse length axis for the numpy array's first axis
      and also searches amplitude_avg and phase_avg. If not present, regular amplitude and phase data is used
    - for the near future I have in mind that each data taking script saves a hint in the
      h5 file which entries to use for quick fitting with the dat_reader
    '''
    
    try:
        hf = hdf_lib.Data(path = nfile)
    except IOError,NameError:
        print 'Error: No h5 file read.'
        return
    
    keys = hf['/entry/data0'].keys()
    if show_output:
        print 'Data entries:', keys
    
    url_tree = '/entry/data0/'
    urls = []
    
    if entries == None:   #no entries specified
        for k in keys:   #go through all keys
            try:
                if str(k[:4]).lower() == 'freq' or str(k[:2]).lower() == 'f ' or str(k[:4]).lower() == 'puls' or str(k[:4]).lower() == 'dacf' or str(k[:5]).lower() == 'delay' or str(k[:8  ]).lower() == 'pi pulse':
                    urls.append(url_tree + k)
                    break
            except IndexError:
                print 'Entries cannot be identified. Parameter names too short. Aborting.'
                return
        if len(urls) == 0:
            print 'No parameter axis found. Aborting.'
            return
            
        for k in keys:
            try:
                if 'avg' in str(k).lower() and str(k[:3]).lower() == 'amp':
                    urls.append(url_tree + k)
                    break
            except IndexError:
                print 'Entries cannot be identified. Aborting.'
                return
            
        for k in keys:
            try:
                if 'avg' in str(k).lower() and str(k[:3]).lower() == 'pha':
                    urls.append(url_tree + k)
                    break
            except IndexError:
                print 'Entries cannot be identified. Aborting.'
                return
            
        if len(urls) != 3:
            for k in keys:
                try:
                    if str(k[:3]).lower() == 'amp':
                        urls.append(url_tree + k)
                        break
                except IndexError:
                    print 'Entries cannot be identified. No amplitude data found. Aborting.'
                    return
            for k in keys:
                try:
                    if str(k[:3]).lower() == 'pha':
                        urls.append(url_tree + k)
                        break
                except IndexError:
                    print 'Entries cannot be identified. No phase data found. Aborting.'
                    return
                
        #c1 = np.array(hf[urls[0]],dtype=np.float64)
        #amp = np.array(hf[urls[1]],dtype=np.float64)
        #pha = np.array(hf[urls[2]],dtype=np.float64)
        #return np.array([c1,amp,pha])
        
    else:   #use specified entries
        for e in entries:
            for k in keys:
                try:
                    if str(e).lower() in str(k).lower():
                        urls.append(url_tree + k)
                except IndexError:
                    print 'Entries cannot be identified. No data for >> %s << found. Aborting.'%str(e)
                    return
    if show_output:    
        print 'Entries identified:',urls
    data = []
    for u in urls:
        data.append(np.array(hf[u],dtype=np.float64))
    hf.close()
    return np.array(data), urls

# =================================================================================================================

def load_data(file_name = None,entries = None, show_output=True):
    '''
    load recent or specified data file and return the data array and the file name
    '''
    
    if file_name == None:
        #test whether hdf lib is available
        try:
            hdf_lib
            #raise NameError
        except NameError:
            ftype = 'dat'
        else:
            ftype = 'h5'
        nfile = find_latest_file(ftype)
    else:
        nfile = str(file_name).replace('\\','/')

    try:
        if show_output:
            print 'Reading file '+nfile
        if nfile[-2:] == 'h5':   #hdf file
            data, urls = read_hdf_data(nfile, entries, show_output)
        else:   #dat file
            data = np.loadtxt(nfile, comments='#').T
    except NameError:
        print 'hdf package not available...aborting'
        return
    except Exception as message:
        print 'invalid file name...aborting:', message
        return

    return data, nfile, urls

# =================================================================================================================

def _fill_p0(p0,ps):
    '''
    fill estimated p0 with specified initial values (in ps)
    '''
    
    if ps != None:
        try:
            for n in range(len(ps)):
                if ps[n] != None:
                    p0[n] = ps[n]
        except Exception as m:
            print 'list of given initial parameters invalid...aborting'
            raise ValueError
    return p0

# =================================================================================================================

def _extract_initial_oscillating_parameters(data,data_c,damping,asymmetric_exp = False):
    '''
    find initial parameters for oscillating fits
    '''
    
    #offset
    # testing last 25% of data for its maximum slope; take offset as last 10% of data for a small slope (and therefore strong damping)
    if np.max(np.abs(np.diff(data[data_c][int(0.75*len(data[data_c])):]))) < 0.3*np.abs(np.max(data[data_c])-np.min(data[data_c]))/(len(data[0][int(0.75*len(data[0])):])*(data[0][-1]-data[0][int(0.75*len(data[data_c]))])):   #if slope in last part small
        s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])
    else:   #larger slope: calculate initial offset from min/max in data
        s_offs = (np.max(data[data_c]) + np.min(data[data_c]))/2
    #print s_offs
    
    if damping:
        #amplitude
        if asymmetric_exp:
            s_a = np.abs(np.max(data[data_c]) - np.min(data[data_c]))
            if np.abs(np.max(data[data_c]) - s_offs) < np.abs(np.min(data[data_c]) - s_offs):   #if maximum closer to offset than minimum
                s_a = -s_a
        a1 = np.abs(np.max(data[data_c]) - s_offs)
        a2 = np.abs(np.min(data[data_c]) - s_offs)
        s_a = np.max([a1,a2])
        #print s_a
        
        #damping
        a_end = np.abs(np.max(data[data_c][int(0.7*len(data[data_c])):]))   #scan last 30% of values -> final amplitude
        #print a_end
        # -> calculate Td
        t_end = data[0][-1]
        try:
            s_Td = -t_end/(np.log((np.abs(a_end-np.abs(s_offs)))/s_a))
        except RuntimeWarning:
            logging.warning('Invalid value encountered in log. Continuing...')
            s_Td = float('inf')
        if np.abs(s_Td) == float('inf'):
            s_Td = float('inf')
            logging.warning('Consider using the sine fit routine for non-decaying sines.')
        #print 'assume T =', str(np.round(s_Td,4))
    
    else:
        s_a = 0
        s_Td = 0
    
    #frequency
    #s_fs = 1/data[0][int(np.round(np.abs(1/np.fft.fftfreq(len(data[data_c]))[np.where(np.abs(np.fft.fft(data[data_c]))==np.max(np.abs(np.fft.fft(data[data_c]))[1:]))]))[0])] #@andre20150318
    roots = 0   #number of offset line crossings ~ period of oscillation
    for dat_p in range(len(data[data_c])-1):
        if np.sign(data[data_c][dat_p] - s_offs) != np.sign(data[data_c][dat_p+1] - s_offs):   #offset line crossing
            roots+=1
    s_fs = float(roots)/(2*data[0][-1])   #number of roots/2 /measurement time
    #print s_fs
    
    #phase offset
    dmax = np.abs(data[data_c][0] - np.max(data[data_c]))
    dmean = np.abs(data[data_c][0] - np.mean(data[data_c]))
    dmin = np.abs(data[data_c][0] - np.min(data[data_c]))
    if dmax < dmean:   #start on upper side -> offset phase pi/2
        s_ph = np.pi/2
    elif dmin < dmean:   #start on lower side -> offset phase -pi/2
        s_ph = -np.pi/2
    else:   #ordinary sine
        s_ph = 0
    #print s_ph
    
    return s_offs, s_a, s_Td, s_fs, s_ph

# =================================================================================================================

def _safe_fit_data_in_h5_file(fname,x_vec,fvalues,entryname='',x_url='',data_url=''):
    '''
    appends fitted data to the h5 file in folder analysis with a newly created parameter axis containing
     a fixed number of points
     
    fname: file name of the h5 file
    x_vec: generated x vector (parameter vector) of constant length
    fvalues: fitted function values, array of length len(x_vec)
    entryname: suffix to be added to the name of analysis entry
    x_url: url of coordinate axis
    data_url: url of data entry
    
    So far I hope that hdf_lib throws away old fit data when refitting and generating the same axes in the analysis folder. (JB)
    '''
    
    try:
        hf = hdf_lib.Data(path=fname)
        hdf_x = hf.add_coordinate('param'+entryname,folder='analysis')
        hdf_x.add(x_vec)
        hdf_fit = hf.add_value_vector('fit'+entryname, folder='analysis', x = hdf_x)
        hdf_fit.append(np.array(fvalues))
        
        ds_x = hf.get_dataset(x_url)
        ds_data = hf.get_dataset(data_url)
        joint_view = hf.add_view('joint_view', x = hdf_x, y = hdf_fit)
        joint_view.add(x = ds_x, y = ds_data)
        
        hf.close_file()
    except Exception as m:
        print 'Error while attempting to save fit data in h5 file:', m
        return False
    return True

# =================================================================================================================

def spline_smooth_data(x_data, y_data, spline_order=1):
    '''
    applies a spline fit of order spline_order (default: 1) to the data, usually prior to fitting
    returns the smoothened data (only)
    '''
    #spline smoothing
    return scipy.interpolate.UnivariateSpline(x_data, y_data, s=spline_order)(x_data)
    
# =================================================================================================================

def fit_data(file_name = None, fit_function = LORENTZIAN, data_c = 2, ps = None, xlabel = '', ylabel = '', show_plot = True, show_output = True, save_pdf = False, data=None, nfile=None, opt=None, entryname = '', spline_order=None):
    '''
    fit the data in file_name to a function specified by fit_function
    setting file_name to None makes the code try to find the newest .dat file in today's data_dir
    works only in qtLAB invironment where qt.config.get('data_dir') is defined
    
    dat_reader supports the h5 file format. In case the hf libraries are available when setting file_name to None (automatic search for latest data file),
     dat_reader looks for the latest h5 file
    
    fit_function (optional, default = LORENTZIAN): can be LORENTZIAN, LORENTZIAN_SQRT, DAMPED_SINE, SINE, EXP, DAMPED_EXP
    data_c (optional, default = 2, phase): specifies the data column to be used (next to column 0 that is used as the coordinate axis)
     string specifying 'amplitude' or 'phase' or similar spellings are accepted as well
     when data is read from h5 file, the usual column ordering is [freq,amp,pha], [0,1,2]
    ps (optional): start parameters, can be given in parts, set parameters not specified to None
    xlabel (optional): label for horizontal axis
    ylabel (optional): label for vertical axis
    show_plot (optional): show the plot (optional, default = True)
    save_pdf (optional): save plot also as pdf file (optional, default = False)
    data, nfile: pass data object and file name which is used when file_name == 'dat_import'
    opt: bool, set to True if data is to be optimized prior to fitting using the data_optimizer
    entryname: suffix to be added to the name of analysis entry
    
    returns fit parameters, standard deviations concatenated: [popt1,pop2,...poptn,err_popt1,err_popt2,...err_poptn]
    in case fit does not converge, errors are filled with 'inf'
    WARNING: errors might be returned as 'inf' which is 'nan'
    frequency units in GHz
    
    f_Lorentzian expects its frequency parameter to be stated in GHz
    '''
    
    if type(fit_function)==str:
        logging.warning('using strings as fit function is depreciated. Use e.g dr.LORENTZIAN instead.')
        fit_function = {'lorentzian':LORENTZIAN, 'lorentzian_sqrt':LORENTZIAN_SQRT, 'damped_sine':DAMPED_SINE, 'sine':SINE, 'exp':EXP, 'damped_exp':DAMPED_EXP}[fit_function]
        
    
    def f_Lorentzian_sqrt(f, f0, k, a, offs):
        return np.sign(a) * np.sqrt(np.abs(a**2*(k/2)**2/((k/2)**2+(f-f0)**2)))+offs
        
    def f_Lorentzian(f, f0, k, a, offs):
        return a*k/(2*np.pi)/((k/2)**2+(f-f0)**2)+offs
        
    def f_damped_sine(t, fs, Td, a, offs, ph):
        if a < 0: return np.NaN #constrict amplitude to positive values
        if fs < 0: return np.NaN
        if Td < 0: return np.NaN
        #if ph < -np.pi or ph > np.pi: return np.NaN #constrict phase
        return a*np.exp(-t/Td)*np.sin(2*np.pi*fs*t+ph)+offs
        
    def f_sine(t, fs, a, offs, ph):
        if a < 0: return np.NaN #constrict amplitude to positive values
        return a*np.sin(2*np.pi*fs*t+ph)+offs
        
    def f_exp(t, Td, a, offs):
        return a*np.exp(-t/Td)+offs
        
    def f_damped_exp(t, fs, Td, a, offs, ph, d):
        return a*np.exp(-t/Td)*0.5*(1+d*np.cos(2*np.pi*fs*t+ph))+offs

    entries = None
    if isinstance(data_c,(list, tuple, np.ndarray)):   #got list of entries to be plotted
        entries = data_c
        data_c = 1
        
    if file_name == 'dat_import':
        if show_output: print 'use imported data'
        data_c = 1
    else:
        #load data
        data, nfile, urls = load_data(file_name, entries, show_output)
        x_url = urls[0]
        data_url = urls[data_c]

    #check column identifier
    if type(data_c) == str:
        if 'amp' in str(data_c).lower():
            data_c = 1
        else:
            data_c = 2
            data_url = urls[2]
    if data_c >= len(data):
        print 'bad data column identifier, out of bonds...aborting'
        return
        
    #data optimization
    if opt:
        if no_do:
            logging.warning('Data is not optimized since package is not loaded.')
        data = do.optimize(data,data_c,data_c+1)
        data_c = 1
        
    if spline_order != None:
        try:
            data[data_c] = spline_smooth_data(data[0],data[data_c],spline_order)
            print 'spline smoothing applied'
        except ValueError:
            logging.error('spline order has to be of type float')
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    plt.figure('dat_reader')
    if fit_function==LORENTZIAN or fit_function==LORENTZIAN_SQRT:
    
        #check for unit in frequency
        if np.mean(data[0]) > 100:
            if show_output:
                print 'frequency given in Hz'
                
            freq_conversion_factor = 1e-9
        else:
            if show_output:
                print 'frequency given in GHz'
            freq_conversion_factor = 1

        #plot data, f in GHz
        
        #if show_plot:   
        plt.plot(data[0]*freq_conversion_factor,data[data_c],'*')
        x_vec = np.linspace(data[0][0]*freq_conversion_factor,data[0][-1]*freq_conversion_factor,200)
    
        #start parameters ----------------------------------------------------------------------
        s_offs = np.mean(np.array([data[data_c,:int(np.size(data,1)/10)],data[data_c,np.size(data,1)-int(np.size(data,1)/10):]])) #offset is calculated from the first and last 10% of the data to improve fitting on tight windows @andre20150318
        if np.abs(np.max(data[data_c]) - np.mean(data[data_c])) > np.abs(np.min(data[data_c]) - np.mean(data[data_c])):
            #expect a peak
            if show_output:
                print 'expecting peak'
            s_a = np.abs((np.max(data[data_c])-np.mean(data[data_c])))
            s_f0 = data[0][np.where(data[data_c] == max(data[data_c]))[0][0]]*freq_conversion_factor
            #print s_f0
            #print s_a
            #print s_offs
        else:
            if show_output:
                print 'expecting dip'
            s_a = -np.abs((np.min(data[data_c])-np.mean(data[data_c])))
            s_f0 = data[0][np.where(data[data_c] == min(data[data_c]))[0][0]]*freq_conversion_factor
        
        #estimate peak/dip width
        mid = s_offs + 0.5*s_a   #estimated mid region between base line and peak/dip
        #print mid
        m = []   #mid points
        for dat_p in range(len(data[data_c])-1):
            if np.sign(data[data_c][dat_p] - mid) != np.sign(data[data_c][dat_p+1] - mid):   #mid level crossing
                m.append(dat_p)   #frequency of found mid point

        if len(m) > 1:
            s_k = (data[0][m[-1]]-data[0][m[0]])*freq_conversion_factor
            if show_output:
                print 'assume k = %.2e'%s_k
        else:
            s_k = 0.15*(data[0][-1]-data[0][0])*freq_conversion_factor   #try 15% of window
            
        p0 = _fill_p0([s_f0, s_k, s_a, s_offs],ps)

        if fit_function == LORENTZIAN_SQRT:
            #lorentzian sqrt fit ----------------------------------------------------------------------
            try:
                popt, pcov = curve_fit(f_Lorentzian_sqrt, data[0]*freq_conversion_factor, data[data_c], p0 = p0)
                if show_output:
                    print 'QL:', np.abs(np.round(float(popt[0])/popt[1]))
            except:
                print 'fit not successful'
                popt = p0
                pcov = None
            finally:
                #if show_plot:
                    fvalues = f_Lorentzian_sqrt(x_vec, *popt)
                    plt.plot(x_vec, fvalues)
                    ax = plt.gca()
                    if xlabel == '':
                        ax.set_xlabel('f (GHz)', fontsize=13)
                        pass
                    else:
                        ax.set_xlabel(str(xlabel), fontsize=13)
                    if ylabel == '':
                        ax.set_ylabel('arg(S21) (a.u.)', fontsize=13)
        
        else:
            #regular lorentzian fit ----------------------------------------------------------------------
            try:
                popt, pcov = curve_fit(f_Lorentzian, data[0]*freq_conversion_factor, data[data_c], p0 = p0)
                if show_output:
                    print 'QL:', np.abs(np.round(float(popt[0])/popt[1]))
            except:
                print 'fit not successful'
                popt = p0
                pcov = None
            finally:
                #if show_plot:
                    fvalues = f_Lorentzian(x_vec, *popt)
                    plt.plot(x_vec, fvalues)
                    ax = plt.gca()
                    if xlabel == '':
                        ax.set_xlabel('f (GHz)', fontsize=13)
                        pass
                    else:
                        ax.set_xlabel(str(xlabel), fontsize=13)
                    if ylabel == '':
                        #ax.set_ylabel('arg(S21) (a.u.)', fontsize=13)
                        pass
                    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
    elif fit_function == DAMPED_SINE:
        #plot data
        #if show_plot:   
        plt.plot(data[0],data[data_c],'*')
        x_vec = np.linspace(data[0][0],data[0][-1],400)
    
        #start parameters ----------------------------------------------------------------------
        s_offs, s_a, s_Td, s_fs, s_ph = _extract_initial_oscillating_parameters(data,data_c,damping=True)
        p0 = _fill_p0([s_fs, s_Td, s_a, s_offs, s_ph],ps)

        #damped sine fit ----------------------------------------------------------------------
        try:
            popt, pcov = curve_fit(f_damped_sine, data[0], data[data_c], p0 = p0,maxfev=200*len(data[0]))
        except Exception as e:
            print 'fit not successful'
            print e
            popt = p0
            pcov = None
        finally:
            #if show_plot:
                fvalues = f_damped_sine(x_vec, *popt)
                plt.plot(x_vec, fvalues)
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif fit_function == SINE:
        #plot data
        #if show_plot:   
        plt.plot(data[0],data[data_c],'*')
        x_vec = np.linspace(data[0][0],data[0][-1],200)
    
        #start parameters ----------------------------------------------------------------------
        s_offs, s_a, s_Td, s_fs, s_ph = _extract_initial_oscillating_parameters(data,data_c,damping=False)
        s_offs = np.mean(data[data_c])
        s_a = 0.5*np.abs(np.max(data[data_c]) - np.min(data[data_c]))
        p0 = _fill_p0([s_fs, s_a, s_offs, s_ph],ps)
        #print p0
            
        #sine fit ----------------------------------------------------------------------
        try:
            popt, pcov = curve_fit(f_sine, data[0], data[data_c], p0 = p0)
        except:
            print 'fit not successful'
            popt = p0
            pcov = None
        finally:
           # if show_plot:
                fvalues = f_sine(x_vec, *popt)
                plt.plot(x_vec, fvalues)
    
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif fit_function == EXP:
    
        x_vec = np.linspace(data[0][0],data[0][-1],200)
        
        #start parameters ----------------------------------------------------------------------
        s_offs = np.mean(data[data_c][int(0.9*len(data[data_c])):])   #average over the last 10% of entries
        s_a = data[data_c][0] - s_offs
        s_Td = np.abs(float(s_a)/np.mean(np.gradient(data[data_c],data[0][1]-data[0][0])[:5]))   #calculate gradient at t=0 which is equal to (+-)a/T
        #s_Td = data[0][-1]/5   #assume Td to be roughly a fifth of total measurement range
        
        p0 = _fill_p0([s_Td, s_a, s_offs],ps)

        #exp fit ----------------------------------------------------------------------
        try:
            popt, pcov = curve_fit(f_exp, data[0], data[data_c], p0 = p0)
            if xlabel == None:
                if show_output:
                    print "decay time:",str(popt[0]), 'us'
            else:
                if show_output:
                    print "decay time:",str(popt[0]), str(xlabel[-4:])
        except:
            print 'fit not successful'
            popt = p0
            pcov = None
        finally:
            #plot data
            #if show_plot:
                plt.close('dat_reader')
                fig, axes = plt.subplots(1, 2, figsize=(15,4),num='dat_reader')
                
                axes[0].plot(data[0],data[data_c],'*')
                fvalues = f_exp(x_vec, *popt)
                axes[0].plot(x_vec, fvalues)
                if xlabel == '':
                    axes[0].set_xlabel('t (us)', fontsize=13)
                    pass
                else:
                    axes[0].set_xlabel(str(xlabel), fontsize=13)
                if ylabel == '':
                    axes[0].set_ylabel('arg(S11) (a.u.)', fontsize=13)
                    pass
                else:
                    axes[0].set_ylabel(str(ylabel), fontsize=13)
                #axes[0].set_title('exponential decay', fontsize=15)
                axes[0].set_title(str(['%.4g'%entry for entry in popt]), fontsize=15)
                
                axes[1].plot(data[0],np.abs(data[data_c]-popt[2]),'*')
                axes[1].plot(x_vec, np.abs(f_exp(x_vec, *popt)-popt[2]))   #subtract offset for log plot
                axes[1].set_yscale('log')
                if xlabel == '':
                    axes[1].set_xlabel('t (us)', fontsize=13)
                    pass
                else:
                    axes[1].set_xlabel(str(xlabel), fontsize=13)
                if ylabel == '':
                    axes[1].set_ylabel('normalized log(arg(S21)) (a.u.)', fontsize=13)
                    pass
                else:
                    axes[1].set_ylabel(str(ylabel), fontsize=13)
                
                #axes[1].set_title('exponential decay', fontsize=15)
                fig.tight_layout()
                
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    elif fit_function == DAMPED_EXP:
    
        #plot data
        #if show_plot:   
        plt.plot(data[0],data[data_c],'*')
        x_vec = np.linspace(data[0][0],data[0][-1],400)

        #start parameters ----------------------------------------------------------------------
        s_offs, s_a, s_Td, s_fs, s_ph = _extract_initial_oscillating_parameters(data,data_c,damping=True)
        # 1-d = (scaled) distance between first extremum and baseline
        d_diff = np.gradient(data[data_c],data[0][1]-data[0][0])
        i = 0
        for i in range(len(data[0])):
            if np.sign(d_diff[i]) != np.sign(d_diff[i+1]):   #go to first sign change -> extremum
                break
            i+=1
        if show_output:
            print 'first extremum detected at %.4g' %(data[0][i])
        s_d = 1 - np.abs(data[data_c][i] - s_offs)
        p0 = _fill_p0([s_fs, s_Td, s_a, s_offs, s_ph, s_d],ps)

        #damped sine fit ----------------------------------------------------------------------
        try:
            popt, pcov = curve_fit(f_damped_exp, data[0], data[data_c], p0 = p0)
        except:
            print 'fit not successful'
            popt = p0
            pcov = None
        finally:
            #if show_plot:
                fvalues = f_damped_exp(x_vec, *popt)
                plt.plot(x_vec, fvalues)
    
    else:
        print 'fit function not known...aborting'
        return
    
    #if show_plot:
    if fit_function != EXP:
        if xlabel != '':
            plt.xlabel(xlabel)
        if ylabel != '':
            plt.ylabel(ylabel)
        plt.title(str(['%.4g'%entry for entry in popt]),y=1.03)
        
    try:
        plt.savefig(nfile.replace('.dat','_dr.png').replace('.h5','_dr.png'), dpi=300)
        if save_pdf:
            plt.savefig(nfile.replace('.dat','_dr.pdf').replace('.h5','_dr.pdf'), dpi=300)
        if show_output:
            print 'plot saved:', nfile.replace('.dat','_dr.png').replace('.h5','_dr.png')
    except Exception as m:
        if show_output:
            print 'figure not stored:', m
        
    if pcov != None and nfile!= None and nfile[-2:] == 'h5':   #in case fit was successful
        if _safe_fit_data_in_h5_file(nfile,x_vec,np.array(fvalues),entryname,x_url,data_url):
            if entryname == '':
                if show_output:
                    print 'Fit data successfully stored in h5 file.'
            else:
                if show_output:
                    print 'Fit data successfully stored in h5 file: fit%s'%entryname
    if show_plot: plt.show()
    plt.close('dat_reader')
    
    if pcov == None:
        return popt,float('inf')*np.ones(len(popt)) #fill up errors with 'inf' in case fit did not converge
    else:
        return popt,np.sqrt(np.diag(pcov))
