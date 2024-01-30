# qfit.py
# based on dat_reader.py and data_optimizer.py by JB@KIT, 
# 2015-2018 by JB@KIT and the qkit team
# data reading and fitting

# import and basic usage

'''
usage:

.. code-block:: python

    from qkit import qfit as qfit
    qf = qfit.QFIT()
    qf.load('data/file.h5', entries=['time', 'phase'])
    qf.rotate_IQ_plane()
    qf.fit_exp()

'''
# a customized fit funcitoncan be set via directly writing in self.fit_function
# and providing full initial parameters
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

#\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

import numpy as np
plot_enable = False
try:
    import qkit
    if qkit.module_available("matplotlib"):
        import matplotlib.pyplot as plt
        plot_enable = True
except (ImportError, AttributeError):
    try:
        import matplotlib.pyplot as plt
        plot_enable = True
    except ImportError:
        plot_enable = False
from scipy.optimize import curve_fit
import scipy.interpolate
import os, glob
import time
import logging

try:
    from qkit.storage import store
except ImportError: pass

#\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

def _fill_p0(guesses,p0):
    '''
    Fill estimated guesses with specified initial values (in p0). 
    p0 can be a smaller list than len(guesses) and may contain 'None' entries 
    e.g. guesses=[0,0,0,0,0] and p0 = [None,1,2] then the resulting guesses = [0,1,2,0,0]
    '''
    if guesses is None: return p0
    if p0 is not None:
        try:
            for i,p in enumerate(p0):
                if p is not None:
                    guesses[i] = p
        except Exception:
            logging.error('List of given initial parameters invalid. Aborting.')
            raise ValueError
    return guesses

#\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

class QFIT(object):
    def __init__(self):

        self.cfg = {'show_plot' : True,
                    'show_output' : True,
                    'save_png' : True,
                    'save_pdf' : False,
                    'show_complex_plot' : True,             #show complex plot during optimize
                    'data_column' : 2,                      #data column entry if entry list is longer than 2
                    'spline_knots' : 1.e-3,                 #spacing between knots used during spline fitting, smaller number = more accurate
                    'figsize' : (15,7),                     #figure size setting
                    'debug' : False,                        #debug mode
                    'analysis_folder' : 'analysis',         #folder in h5 file where data is to be stored
                    'datafolder_structure' : 'day_time'}    #day_time or epoche_key

        try:
            import qkit
            self.cfg['data_dir'] = qkit.cfg.get('datadir').replace('\\','/')
            if qkit.cfg.get('datafolder_structure',1) == 2:   #new data structure with epoche key in qkit settings
                try:
                    self.run_id = qkit.cfg['run_id']
                    self.user = qkit.cfg['user']
                    self.cfg['datafolder_structure'] = 'epoche_key'
                except KeyError:
                    logging.error('No run_id and user entry found in qkit.cfg. Falling back to old style data folder structure.')
            else:
                self.cfg['datafolder_structure'] = 'day_time'
        except (ImportError, AttributeError):
            logging.warning('Running outside of qkit environment.')
            self.cfg['data_dir'] = os.getcwd()

        try:
            store
            self.cfg['store'] = True
        except ImportError:
            logging.warning('Package store not found.')
            self.cfg['store'] = False
        self.cfg['matplotlib'] = plot_enable

    # fit function definitions --------------------------------------------------------------------------------------

    def __f_Lorentzian_sqrt(self, f, f0, k, a, offs):
        return np.sign(a) * np.sqrt(np.abs(a**2*(k/2)**2/((k/2)**2+(f-f0)**2)))+offs
        
    def __f_Lorentzian(self, f, f0, k, a, offs):
        return a*k/(2*np.pi)/((k/2)**2+(f-f0)**2)+offs

    def __f_Skewed_Lorentzian(self, f, f0, k, a, offs, tilt, skew):
        return (a + skew * (f - f0)) * k / (2 * np.pi) / ((k / 2) ** 2 + (f - f0) ** 2) + offs + tilt * (f - f0)

    #def __f_general_reflection(f, f0, kc, ki, a, offs):
    #    return a*(4*kc*(4*(f-f0)**2+kc**2-ki**2))/(16*(f-f0)**4+8*(f-f0)**2*kc**2+8*(f-f0)**2*ki**2+kc**4-2*kc**2*ki**2+ki**4)+offs
        
    def __f_damped_sine(self, t, fs, Td, a, offs, ph):
        if a < 0: return np.NaN #constrict amplitude to positive values
        if fs < 0: return np.NaN
        if Td < 0: return np.NaN
        #if ph < -np.pi or ph > np.pi: return np.NaN #constrict phase
        return a*np.exp(-t/Td)*np.sin(2*np.pi*fs*t+ph)+offs
        
    def __f_sine(self, t, fs, a, offs, ph):
        if a < 0: return np.NaN #constrict amplitude to positive values
        return a*np.sin(2*np.pi*fs*t+ph)+offs
        
    def __f_exp(self, t, Td, a, offs):
        return a*np.exp(-t/Td)+offs
        
    def __f_exp_sine(self, t, fs, Td, a, offs, ph, d):
        return a*np.exp(-t/Td)*0.5*(1+d*np.cos(2*np.pi*fs*t+ph))+offs

    def __get_parameters(self, fit_function):
        '''
        Parameters of known fit functions used for plotting purposes.
        '''
        return {self.__f_Lorentzian_sqrt: ['f0','k','a','offs'],
            self.__f_Lorentzian: ['f0','k','a','offs'],
            self.__f_Skewed_Lorentzian:['f0','k','a','offs','tilt','skew'],
            self.__f_sine: ['f','a','offs','ph'],
            self.__f_exp: ['Td','a','offs'],
            self.__f_damped_sine: ['f','Td','a','offs','ph','d']
        }.get(fit_function)

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def load(self, *args, **kwargs):
        '''
        Load data from either:
         - numpy arrays: must specify keyword arguments 'coordinate' and 'data'
         - numpy arrays: must specify keyword arguments 'coordinate' and 'amplitude' and 'phase'
         - data file (h5 or text based file): specify filename
         - recent data file in data_dir: no arguments provided

        h5 entries need to be given with keyword 'entries'.
        '''

        if 'coordinate' in kwargs.keys() and 'data' in kwargs.keys():
            self.coordinate = kwargs['coordinate']
            self.data = kwargs['data']
            self.amplitude = None
            self.phase = None
            self.urls = None
            self.file_name = 'data_import'
            self.coordinate_label = ''
            self.data_label = ''
            return
        elif 'coordinate' in kwargs.keys() and 'amplitude' in kwargs.keys() and 'phase' in  kwargs.keys():
            #print("loading amplitude and phase signal from np array")
            self.coordinate = kwargs['coordinate']
            self.data = None
            self.amplitude = kwargs['amplitude']
            self.phase = kwargs['phase']
            self.urls = None
            self.file_name = 'data_import'
            self.coordinate_label = ''
            self.data_label = ''
            return
        elif len(args) == 0:   #no file name provided
            if self.cfg['store']: ftype = 'h5'
            else: ftype = 'dat'
            if self.find_latest_file(ftype) == 0:
                return
        elif os.path.isfile(args[0]):   #test for file existence
            self.file_name = args[0]
        else:
            logging.error('Error parsing function arguments.')

        if 'entries' in kwargs.keys():   #h5 file mode
            entries = kwargs['entries']
        else: entries = None

        if 'return_data' in kwargs.keys():
            return self.__acquire(entries=entries, return_data = kwargs['return_data'])
        else:
            self.__acquire(entries=entries, return_data = False)

    def __acquire(self, entries, return_data):
        self.errors = None
        self.optimized = False
        if self.file_name[-2:] == 'h5':
            self.discover_hdf_data(entries = entries)
            return self.read_hdf_data(return_data = return_data)
        else: #looks like a text file
            data = np.loadtxt(self.file_name, comments='#').T
            self.coordinate = self.coordinate
            self.data = data[self.cfg['data_column']]
            self.data_label = None
            if return_data: return data

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def read_hdf_data(self, return_data = False):
        '''
        Read hdf data and set attributes self.coordinate, self.data. 
        Return data as a numpy array if requested by 'return_data' argument.
        '''
        try:
            self.hf = store.Data(self.file_name)
        except (IOError,NameError):
            logging.error('Could not read h5 file.')
            return

        #read hdf data
        data = []
        for u in self.urls:
            data.append(np.array(self.hf[u],dtype=np.float64))
        self.hf.close()

        #fill coordinate and data attributes
        if len(self.urls) == 2:   #for only two urls, it is clear what to do
            self.coordinate = data[0]
            self.data = data[1]
            self.data_label = self.urls[1].split('/')[-1]
            self.data_url = self.urls[1]
        elif len(self.urls) > 2:   #if more than two, read out the data_column set in the config
            self.coordinate = data[0]
            self.data = data[self.cfg['data_column']]
            self.data_label = self.urls[self.cfg['data_column']].split('/')[-1]
            self.data_url = self.urls[self.cfg['data_column']]
        else:
            logging.warning('Coordinate and data attributes not assigned properly.')
        self.coordinate_label = self.urls[0].split('/')[-1]
        if return_data:
            return data, self.urls

    def find_latest_file(self, ftype):
        '''
        Find latest file of type 'ftype' in the data directory. 
        The file name (including absolute path) is stored in self.file_name.
        '''
     
        if self.cfg['datafolder_structure'] == 'day_time':
            self.data_dir = self.cfg['data_dir']
        else:
            self.data_dir = os.path.join(self.cfg['data_dir'], self.run_id, self.user)
        try:
            nfile = max(glob.iglob(str(self.data_dir)+'/*/*.'+ftype), key=os.path.getctime)   #find newest file in directory
        except ValueError:
            logging.error('No .{:s} file located in directory {:s}.'.format(str(ftype), str(self.data_dir)))
            return
        
        self.file_name = str(nfile).replace('\\','/')
        if self.cfg['show_output']: print('Latest file: {:s}'.format(self.file_name))

    def discover_hdf_data(self, entries=None):
        '''
        Read hdf data file and store urls that match entries or seem reasonable. 
        - Inputs: entries (optional): specifies entries in h5 file whose urls to be returned
        
        - entries can be a list of string keywords (entries) in the form ['string1',string2',...,'stringn']
        - when no entries are specified, discover_hdf_data looks for a frequency axis or a pulse length axis
          for the (first) coordinate axis and also searches amplitude_avg and phase_avg. If not present,
          the urls of 'amplitude' and 'phase' data are discovered

        - TODO: a nice feature would be to save a hint in each h5 file which entries to use for quick fitting
        '''
        
        try:
            self.hf = store.Data(self.file_name)
        except (IOError,NameError):
            logging.error('Could not read h5 file.')
            return
        
        keys = self.hf['/entry/data0'].keys()
        if self.cfg['show_output']: print('Available data entries:', keys)
        # only show the available data entries, but analysis entries can still be accessed
        
        url_tree = '/entry/data0/'
        urls = []
        
        if entries is None:   #no entries specified
            for k in keys:   #go through all keys
                try:
                    #search for parameter axis
                    if str(k[:4]).lower() == 'freq' or str(k[:2]).lower() == 'f ' or str(k[:4]).lower() == 'puls' or str(k[:4]).lower() == 'dacf' or str(k[:5]).lower() == 'delay' or str(k[:8  ]).lower() == 'pi pulse':
                        urls.append(url_tree + k)
                        break
                except IndexError:
                    logging.error('Entries cannot be identified. Parameter names too short. Aborting.')
                    return
            if len(urls) == 0:
                logging.error('No parameter axis found. Aborting.')
                return
                
            #first look for amplitude_avg and phase_avg entries -> time domain
            for k in keys:
                try:
                    if 'avg' in str(k).lower() and str(k[:3]).lower() == 'amp':
                        urls.append(url_tree + k)
                        break
                except IndexError:
                    logging.error('Entries cannot be identified. Aborting.')
                    return
                
            for k in keys:
                try:
                    if 'avg' in str(k).lower() and str(k[:3]).lower() == 'pha':
                        urls.append(url_tree + k)
                        break
                except IndexError:
                    logging.error('Entries cannot be identified. Aborting.')
                    return

            #if nothing found previously, then use amplitude and phase entries
            if len(urls) != 3:
                for k in keys:
                    try:
                        if str(k[:3]).lower() == 'amp':
                            urls.append(url_tree + k)
                            break
                    except IndexError:
                        logging.error('Entries cannot be identified. Aborting.')
                        return
                for k in keys:
                    try:
                        if str(k[:3]).lower() == 'pha':
                            urls.append(url_tree + k)
                            break
                    except IndexError:
                        logging.error('Entries cannot be identified. Aborting.')
                        return
            
        else:   #use specified entries
            entrytypes = self.hf['/entry/'].keys()
            try: entrytypes.remove('views')
            except (ValueError,AttributeError): pass
            for et in entrytypes:
                for e in entries:
                    for k in self.hf['/entry/'+et].keys():
                        try:
                            if e == et+k or (e == k and et == 'data0'):
                                urls.append('/entry/'+et+'/'+k)
                        except IndexError:
                            logging.error('Entries cannot be identified. No data for >> {:s} << found. Aborting.'.format(str(e)))
                            return

        self.hf.close()                
        #cast to real strings in case the urls ended up to be unicode
        self.urls = [str(u) for u in urls]
        if self.cfg['show_output']: print('Entries identified:', self.urls)

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def spline_smooth(self):
        '''
        Spline smooth the data set in self.data. The smoothing parameter is set via the 'spline_knots' entry in self.cfg.
        '''
        self.data = scipy.interpolate.UnivariateSpline(self.coordinate, self.data, s=self.cfg['spline_knots'])(self.coordinate)

    def phase_grad(self,spline = False):
        '''
        Unwrap, (optionally) spline smooth, and differentiate phase data. 
        The freuqnecy derivative of transmission or reflection phase data that follows 
        a arctan function yields a Lorentzian distribution.
        '''
        self.data = np.unwrap(self.data)
        if spline: self.spline_smooth()
        self.data = np.gradient(self.data)
        self._save_opt_data()

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def rotate_IQ_plane(self,entries=None):
        '''
        The data optimizer is fed with microwave data of both quadratures, typically amplitude and phase.
        It effectively performs a principle axis transformation in the complex plane of all data points
        that are located along a line for a typical projective qubit state measurement without single-shot
        fidelity and using a ADC acquisition card. Successively, data optimizer returns a projection along
        the in-line direction quadrature containing maximum information. Indeally, no information is lost
        as no data is left in the orthogonal quadrature.

        The algorithm locates one of the edge data points on either end of the line-shaped data point distribution
        by summing and maximizing the mutual distances between data points. It then calculates the distance
        of each data point with respect to this distinct extremal data point.

        We assume that the possible outcomes of a strong and projective quantum measurement, i.e. the qubit
        states |0>, |1>, result in two distinct locations in the complex plane, corresponding to signatures
        of the dispersive readout resonator. In the absence of single-shot readout fidelity, the pre-averaging
        that is perfomed by the ADC card in the complex plane leads to counts in between the piles denoting |0>
        and |1>. The points laong this line are distributed due to statistical measurement noise and ultimately
        due to the quantum uncertainty. As the averaging takes place in the complex plane, all points recorded
        in such a measurement should be located on a line. In case of a phase sensitive reflection measurement
        at a high internal quality cavity, points may span a segment of a circle that can be caused by noise
        caused measurements of the resonator position away from the two quantumn positions.

        The line shape of the data distribution generally justifies the projection of measurement data to an
        arbitrary axis without altering the internal data shape.

        Errors are calculated projected on the axis complex data points are aligned along. Data is normalized
        prior to returning.

        Requires coordinate, amplitude, and phase data to be specified via entries keyword. 
        self.amplitude and self.phase can be lists of vectors or a single (averaged) data set.
        '''

        if self.file_name[-2:] == 'h5':
            self.discover_hdf_data(entries = entries)
            if len(self.urls) != 3:
                logging.error('Invalid entry specification. Aborting.')
                return
            self.coordinate, self.amplitude, self.phase = self.read_hdf_data(return_data = True)[0]
        elif (self.amplitude is not None) and (self.phase is not None):
            pass
        else:
            logging.warning('Reading out amplitude and phase attributes.')

        #generate complex data array
        self.c_raw = np.array(self.amplitude) * np.exp(1j*np.array(self.phase))

        if len(self.c_raw.shape) > 1:
            #calculate mean of complex data
            c = np.mean(self.c_raw,axis=0)
        else:   #given data is already averaged
            c = self.c_raw

        #point in complex plane with maximum sumed mutual distances
        s = np.zeros_like(np.abs(c))
        for i in range(len(c)):
            for p in c:
                s[i]+=np.abs(p-c[i])
        cmax = np.extract(s == np.max(s),c)

        #calculate distances
        data_opt = np.abs(c - cmax)

        if len(self.c_raw.shape) > 1: #calculate errors in line direction
            #find maximum complex point in maximum distance
            d = 0
            for p in c:
                if np.abs(p-cmax) > d:
                    d = np.abs(p-cmax)
                    cdist = p
            #find unit vector in line direction
            vunit = (cdist - cmax)/np.abs(cdist - cmax)

            #calculate projected distances via dot product, projecting along the data direction
            #errors via std
            dist_proj = [0]*len(c)
            errs = np.zeros_like(c)
            for i,ci in enumerate(self.c_raw.T):   #for each iteration
                dist_proj[i] = [np.abs(np.vdot([np.real(vunit),np.imag(vunit)],[np.real(cr)-np.real(c[i]),np.imag(cr)-np.imag(c[i])])) for cr in ci]
                errs[i] = np.std(dist_proj[i])/np.sqrt(len(dist_proj[i]))
        
        #normalize optimized data
        data_opt -= np.min(data_opt)
        maxv = np.max(data_opt)
        data_opt /= maxv
        if len(self.c_raw.shape) > 1:
            errs /= maxv
        
        #gauss plane plot
        if self.cfg['show_complex_plot'] and self.cfg['matplotlib']:
            if len(self.c_raw.shape) > 1:
                plt.figure(figsize=(10,13))
                ax1 = plt.subplot2grid((4, 1), (0, 0))
                ax2 = plt.subplot2grid((4, 1), (1, 0), rowspan = 3)
                ax1.errorbar(data_opt,np.zeros_like(data_opt),xerr=np.real(errs),color='blue',fmt='o',elinewidth=0.8,capsize=5,markersize=8,ecolor='red')
                ax1.plot([0],[0],'*',color='red',markersize=20)
                prange = np.max(data_opt)-np.min(data_opt)
                ax1.set_xlim(np.min(data_opt)-0.05*prange,np.max(data_opt)+0.05*prange)
                
                ax2.plot(np.real(c),np.imag(c),'.')
                ax2.plot(np.real(c)[:10],np.imag(c)[:10],'.',color='r')   #show first 10 data points in red
                ax2.plot(np.real(cmax),np.imag(cmax),'*',color='black',markersize=15)
                self.errors = np.real(np.array(errs))
            else:
                plt.figure(figsize=(10,10))
                plt.plot(np.real(c),np.imag(c),'.')
                plt.plot(np.real(c)[:10],np.imag(c)[:10],'.',color='r')   #show first 10 data points in red
                plt.plot(np.real(cmax),np.imag(cmax),'*',color='black',markersize=15)

                self.errors = None
            
        self.data = np.real(np.array(data_opt))
        self._save_opt_data()

    def _save_opt_data(self):
        '''
        Saves optimized data in the h5 file and a respective view.
        '''
        if self.urls is not None:
            self.hf = store.Data(self.file_name)
    
            hdf_data_opt = self.hf.add_value_vector(self.data_label+'_data_opt', folder=self.cfg['analysis_folder'], x = self.hf.get_dataset(self.urls[0]))
            hdf_data_opt.append(np.array(self.data))
            self.optimized = True
            
            try:
                self.errors
                if self.errors is None: raise NameError
            except NameError: #no errors
                pass
            else:
                #write errors
                hdf_error = self.hf.add_value_vector(self.data_label+'_errors', folder=self.cfg['analysis_folder'])
                hdf_error.append(np.array(self.errors))
    
                #error plot view
                joint_error_view = self.hf.add_view(self.data_label+'_err_plot', x = self.hf.get_dataset(self.urls[0]),
                    y = hdf_data_opt, error = hdf_error)
            
            self.hf.close_file()

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=
    
    def _store_fit_data(self, fit_params, fit_covariance):
        '''
        Appends fitted data to the h5 file in the specified analysis folder. As the fit is a fixed length array,
        a respective parameter axis is created and also stored in the h5 file.

        If data was optimized and stored with the method 'optimize', all rlevant joint views are created in the h5 file.
        
        inputs:
        - fit_params: np array of the resulting fit parameters
        - fit_covariance:  estimated covariances of the fit_params as returned by curve_fit
        '''
        
        try:
            self.hf = store.Data(self.file_name)
            
            #create coordinate and fit data vector
            hdf_x = self.hf.add_coordinate(self.data_label+'_coordinate',folder=self.cfg['analysis_folder'])
            hdf_x.add(self.x_vec)
            if self.optimized:
                hdf_y = self.hf.add_value_vector(self.data_label+'_opt_fit', folder=self.cfg['analysis_folder'], x = hdf_x)
            else:
                hdf_y = self.hf.add_value_vector(self.data_label+'_fit', folder=self.cfg['analysis_folder'], x = hdf_x)
            hdf_y.append(np.array(self.fvalues))
            
            #parameter entry including errors
            hdf_params = self.hf.add_coordinate(self.data_label+'_'+self.fit_function.__name__+'_params',folder=self.cfg['analysis_folder'])
            hdf_params.add(np.array(list(fit_params)+list(fit_covariance)))

            if self.data_label+'_data_opt' in self.hf[os.path.join('/entry/',self.cfg['analysis_folder']+'0').replace('\\','/')].keys():
                #create joint view with fit, data, and errors if existing
                try:
                    self.errors
                    if self.errors is None: raise NameError
                except NameError: #no errors
                    joint_view = self.hf.add_view(self.data_label+'_opt_fit', x = hdf_x, y = hdf_y)   #fit
                    joint_view.add(x = self.hf.get_dataset(self.urls[0]),
                        y = self.hf.get_dataset(os.path.join('/entry/', self.cfg['analysis_folder']+'0', self.data_label+'_data_opt').replace('\\','/')))   #data
                else: #inlcuding errors
                    joint_error_view_fit = self.hf.add_view(self.data_label+'_err_plot_fit', x = self.hf.get_dataset(self.urls[0]),
                        y = self.hf.get_dataset(os.path.join('/entry/', self.cfg['analysis_folder']+'0', self.data_label+'_data_opt').replace('\\','/')),
                        error = self.hf.get_dataset(os.path.join('/entry/', self.cfg['analysis_folder']+'0', self.data_label+'_errors').replace('\\','/')))   #errorplot
                    joint_error_view_fit.add(x = hdf_x, y = hdf_y)   #fit
            else:   #no optimization
                joint_view = self.hf.add_view(self.data_label+'_fit', x = hdf_x, y = hdf_y)   #fit
                joint_view.add(x = self.hf.get_dataset(self.urls[0]),
                    y = self.hf.get_dataset(self.data_url))   #data
            
            self.hf.close_file()
        except NameError as m:
            logging.error('Error while attempting to save fit data in h5 file: {:s}'.format(str(m)))

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def _guess_lorentzian_parameters(self):
        s_offs = np.mean(np.append(self.data[:int(0.1*len(self.data))],self.data[int(0.9*len(self.data)):]))
        #offset is calculated from the first and last 10% of the data to improve fitting on tight windows @andre20150318
        if np.abs(np.max(self.data) - np.mean(self.data)) > np.abs(np.min(self.data) - np.mean(self.data)):
            #expect a peak
            s_a = np.abs((np.max(self.data)-np.mean(self.data)))
            s_f0 = self.coordinate[np.where(self.data == max(self.data))[0][0]]*self.freq_conversion_factor
            if self.cfg['debug']:
                print('expecting peak')
                print(s_f0)
                print(s_a)
                print(s_offs)
        else:
            s_a = -np.abs((np.min(self.data)-np.mean(self.data)))
            s_f0 = self.coordinate[np.where(self.data == min(self.data))[0][0]]*self.freq_conversion_factor
            if self.cfg['debug']:
                print('expecting dip')
                print(s_f0)
                print(s_a)
                print(s_offs)
        
        #estimate peak/dip width
        mid = s_offs + 0.5*s_a   #estimated mid region between base line and peak/dip
        if self.cfg['debug']: print(mid)
        m = []   #mid points
        for dat_p in range(len(self.data)-1):
            if np.sign(self.data[dat_p] - mid) != np.sign(self.data[dat_p+1] - mid):   #mid level crossing
                m.append(dat_p)   #frequency of found mid point

        if len(m) > 1:
            s_k = (self.coordinate[m[-1]]-self.coordinate[m[0]])*self.freq_conversion_factor
            if self.cfg['show_output']: print('assume k = {:.3g}'.format(s_k))
        else:
            s_k = 0.15*(self.coordinate[-1]-self.coordinate[0])*self.freq_conversion_factor   #try 15% of window

        return [s_f0, s_k, s_a, s_offs]

    def _guess_oscillating_parameters(self,damping,asymmetric_exp = False):
        '''
        find initial parameters for oscillating fits
        
        data: data array
        data_c: (int) data column
        damping: (bool) switch for decaying/non-decaying fit functions
        asymmetric_exp
        '''
        
        #offset
        # testing last 25% of data for its maximum slope; take offset as last 10% of data for a small slope (and therefore strong damping)
        if np.max(np.abs(np.diff(self.data[int(0.75*len(self.data)):]))) < 0.3*np.abs(np.max(self.data)-np.min(self.data))/(len(self.coordinate[int(0.75*len(self.coordinate)):])*(self.coordinate[-1]-self.coordinate[int(0.75*len(self.data))])):   #if slope in last part small
            s_offs = np.mean(self.data[int(0.9*len(self.data)):])
        else:   #larger slope: calculate initial offset from min/max in data
            s_offs = (np.max(self.data) + np.min(self.data))/2
        #print s_offs
        
        if damping:
            if asymmetric_exp:
                s_a = np.abs(np.max(self.data) - np.min(self.data))
                if np.abs(np.max(self.data) - s_offs) < np.abs(np.min(self.data) - s_offs):   #if maximum closer to offset than minimum
                    s_a = -s_a
            else:
                a1 = np.abs(np.max(self.data) - s_offs)
                a2 = np.abs(np.min(self.data) - s_offs)
                s_a = np.max([a1,a2])
            #print s_a
            
            #damping
            a_end = np.abs(np.max(self.data[int(0.7*len(self.data)):]))   #scan last 30% of values -> final amplitude
            #print a_end
            # -> calculate Td
            t_end = self.coordinate[-1]
            try:
                s_Td = -t_end/(np.log((np.abs(a_end-np.abs(s_offs)))/s_a))
            except RuntimeWarning:
                if self.cfg['show_output']: logging.warning('Invalid value encountered in log. Continuing...')
                s_Td = float('inf')
            if np.abs(s_Td) == float('inf') and not asymmetric_exp:
                s_Td = float('inf')
                if self.cfg['show_output']: logging.warning('Consider using the sine fit routine for non-decaying sines.')
            if self.cfg['debug']: print('assume T = {:s}'.format(round(s_Td,4)))
        
        else:
            s_offs = np.mean(self.data)
            s_a = 0.5*np.abs(np.max(self.data) - np.min(self.data))
            s_Td = 0
        
        #frequency
        roots = 0   #number of offset line crossings ~ period of oscillation
        for dat_p in range(len(self.data)-1):
            if np.sign(self.data[dat_p] - s_offs) != np.sign(self.data[dat_p+1] - s_offs):   #offset line crossing
                roots+=1
        s_fs = float(roots)/(2*self.coordinate[-1])   #number of roots/2 /measurement time
        
        #phase offset calculation
        #the d are relative distances of the first data point
        dmax = np.abs(self.data[0] - np.max(self.data))
        dmean = np.abs(self.data[0] - np.mean(self.data))
        dmin = np.abs(self.data[0] - np.min(self.data))
        if dmax < dmean:   #start on upper side -> offset phase pi/2
            s_ph = np.pi/2
        elif dmin < dmean:   #start on lower side -> offset phase -pi/2
            s_ph = -np.pi/2
        else:   # sine or -sin?
            if np.sum(np.gradient(self.data)[:int(0.05*len(self.coordinate))]) > 0: #positive slope -> sin
                s_ph = 0
            else: #negative slope -> -sin
                s_ph = np.pi
        if self.cfg['debug']: print('assume phase = {:.3g}'.format(s_ph))
        
        if damping:
            return [s_fs, s_Td, s_a, s_offs, s_ph]
        else:
            return [s_fs, s_a, s_offs, s_ph]

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def fit_Lorentzian(self, p0=None):
        '''
        Regular Lorentzian fit.
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_Lorentzian
        self.fit(p0=p0)

    def fit_Skewed_Lorentzian(self, p0=None):
        self.fit_function = self.__f_Skewed_Lorentzian
        self.fit(p0=p0)
    
    def fit_Lorentzian_sqrt(self, p0=None):
        '''
        Square root of a Lorentzian fit e.g. for resonator magnitude data (since only the squared linear magnitude data 
        typically results in a Lorentzian response).
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_Lorentzian_sqrt
        self.fit(p0=p0)

    def fit_damped_sine(self, p0=None):
        '''
        Damped sine fit to be used e.g. to fit Rabi/Ramsey oscillations.
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_damped_sine
        self.fit(p0=p0)

    def fit_sine(self, p0=None):
        '''
        Sine fit to be used to fit non-decaying harmonic oscillations.
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_sine
        self.fit(p0=p0)

    def fit_exp(self, p0=None):
        '''
        Simple exponential fit.
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_exp
        self.fit(p0=p0)

    def fit_exp_sine(self, p0=None):
        '''
        Asymmetric exponential sine fit to be used to fit e.g. Vacuum Rabi oscillations.
        Optional Input: list of start parameters p0: Can be a smaller list than the actual number of parameters 
        (addressing only the first n start parameters). p0 can also contain 'None' entries in order to select 
        specific entries to set manually.
        '''
        self.fit_function = self.__f_exp_sine
        self.fit(p0=p0)

    #\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=\./=

    def fit(self,p0=None):
        '''
        Perform fitting and plotting based on the function stored in self.fit_function. 
        self.fit_function may be set manually with an arbitrary function before executing fit(self):

        .. code-block:: python
        
            def f_custom(coordinate, p1, p2, p3):
                return (coordinate+p1)*p2+np.exp(p3)
            self.fit_function = f_custom
            self.p0 = [1,2,3]   #must be provided
            self.fit()
            
        '''

        #check for unit in frequency
        if np.mean(self.coordinate) > 1.e6:
            self.freq_conversion_factor = 1e-9
            if self.cfg['show_output']: logging.warning('Frequency given in Hz. Conversion to GHz applied.')
        else:
            self.freq_conversion_factor = 1
    
        #start parameters
        if self.fit_function == self.__f_Lorentzian or self.fit_function == self.__f_Lorentzian_sqrt:
            self.guesses = self._guess_lorentzian_parameters()
        elif self.fit_function == self.__f_sine:
            self.guesses = self._guess_oscillating_parameters(damping=False,asymmetric_exp=False)
        elif self.fit_function == self.__f_damped_sine:
            self.guesses = self._guess_oscillating_parameters(damping=True,asymmetric_exp=False)
        elif self.fit_function == self.__f_exp_sine:
            self.guesses = self._guess_oscillating_parameters(damping=True,asymmetric_exp=True)
            d_diff = np.gradient(self.data,self.coordinate[1]-self.coordinate[0])  #true gradient
            i = 0
            for i in range(len(self.coordinate)):
                if np.sign(d_diff[i]) != np.sign(d_diff[i+1]):   #go to first sign change -> extremum
                    break
                i+=1
            if self.cfg['debug']: print('first extremum detected at {:.4g}'.format(self.coordinate[i]))
            s_offs = self.guesses[-1]
            s_d = 1 - np.abs(self.data[i] - s_offs)
            self.guesses += [s_d]
        elif self.fit_function == self.__f_exp:
            s_offs = np.mean(self.data[int(0.9*len(self.data)):])   #average over the last 10% of entries
            s_a = self.data[0] - s_offs
            #calculate gradient at t=0 which is equal to (+-)a/T
            s_Td = np.abs(float(s_a)/np.mean(np.gradient(self.data,self.coordinate[1]-self.coordinate[0])[:5]))
            self.guesses = [s_Td, s_a, s_offs]
        elif self.fit_function == self.__f_Skewed_Lorentzian:
            self.guesses = np.append(self._guess_lorentzian_parameters(), [1e-3, 1e-2]).tolist()
            self.p0 = _fill_p0(self.guesses, p0)
            try:
                self.popt, self.pcov = curve_fit(self.__f_Lorentzian, self.coordinate * self.freq_conversion_factor, self.data, p0=self.p0[:4], maxfev=10000)
            except Exception as e:
                logging.warning('Fit not successful.' + str(e))
                self.popt = self.p0[:4]
                self.pcov = None
            self.p0[:4] = self.popt
        else:
            self.guesses = None
            logging.warning('Fit function unknown. No guesses available but I will continue with the specified fit function.')
        self.p0 = _fill_p0(self.guesses,p0)

        try:
            self.popt, self.pcov = curve_fit(self.fit_function, self.coordinate*self.freq_conversion_factor, self.data, p0 = self.p0,maxfev=10000)
            if self.cfg['show_output'] and (self.fit_function == self.__f_Lorentzian or self.fit_function == self.__f_Lorentzian_sqrt):
                print('QL = {:.4g}'.format(np.abs(np.round(float(self.popt[0]) / self.popt[1]))))
        except:
            logging.warning('Fit not successful.')
            self.popt = self.p0
            self.pcov = None
        finally:
            self.x_vec = np.linspace(self.coordinate[0],self.coordinate[-1],500)

            self.fvalues = self.fit_function(self.x_vec * self.freq_conversion_factor, *self.popt)
            #plot
            create_plots = self.cfg['matplotlib'] and (
                self.cfg['show_plot'] or (
                    (self.cfg['save_png'] or self.cfg['save_pdf']) and self.file_name != "data_import"
                )
            )
            if create_plots:
                if self.fit_function == self.__f_exp:
                    #create pair of regular and logarithmic plot
                    self.fig, self.axes = plt.subplots(1, 2, figsize=(15,4))
                    
                    self.axes[0].plot(self.coordinate,self.data,'o')
                    self.axes[0].plot(self.x_vec, self.fvalues)
                    self.ax = self.axes[0]
                    
                    # log plot
                    self.axes[1].plot(self.coordinate,np.abs(self.data-self.popt[2]),'o')   #subtract offset for log plot
                    self.axes[1].plot(self.x_vec, np.abs(self.__f_exp(self.x_vec, *self.popt)-self.popt[2]))
                    self.axes[1].set_yscale('log')
                    self.axes[1].set_xlabel(self.coordinate_label, fontsize=13)
                    self.axes[1].set_ylabel('log('+self.data_label+')', fontsize=13)

                else:
                    #regular data plot
                    self.fig = plt.figure(figsize=self.cfg['figsize'])   #open and address plot instance
                    plt.plot(self.coordinate*self.freq_conversion_factor,self.data,'o')

                    plt.plot(self.x_vec*self.freq_conversion_factor, self.fvalues)
                    self.ax = plt.gca()

                self.ax.set_xlabel(self.coordinate_label, fontsize=13)
                self.ax.set_ylabel(self.data_label, fontsize=13)
                if self.guesses:
                    self.fig.suptitle(str(['{:s} = {:.4g}'.format(p, entry) for p, entry in zip(self.__get_parameters(self.fit_function), self.popt)]))
                    self.parameter_list = self.__get_parameters(self.fit_function)
                self.fig.tight_layout(rect=[0, 0, 1, 0.95])
                
                if self.cfg['save_png'] and self.file_name != "data_import": plt.savefig(self.file_name.strip('.h5')+'.png', dpi=self.cfg.get('dpi',200))
                if self.cfg['save_pdf'] and self.file_name != "data_import": plt.savefig(self.file_name.strip('.h5')+'.pdf', dpi=self.cfg.get('dpi',200))
                if self.cfg['show_plot']: plt.show()
                plt.close(self.fig)

        if self.pcov is not None and self.urls is not None: #if fit successful and data based on h5 file
            self._store_fit_data(fit_params=self.popt, fit_covariance=np.sqrt(np.diag(self.pcov)))
        if self.pcov is None:
            self.std = float('inf')*np.ones(len(self.popt)) #fill up errors with 'inf' in case fit did not converge
        else:
            self.std = np.sqrt(np.diag(self.pcov))
