# Filename: avoided_crossing_fit.py
# Alexander Stehli <alexander.stehli@kit.edu>, 05/2017
# Updates: 05/2017
# Extraction of coupling strenghts from avoided level crossings.

# Import and usage:
#    See Notebook.
# For further information see doc strings




import numpy as np
import scipy.optimize as so
import matplotlib.pyplot as plt
import inspect



class ACF_class():
    '''
    Avoided crossing fit class (AS@KIT 2017):
    Useful for extracting the coupling strenght from avoided level crossings between an arbirary number of functions.
    
        Setters:
            set_xdata     - Set xdata for the fit.
            set_ydata     - Set ydata for the fit.
            set_functions - Set functions of the undressed/uncoupled systems. You can also define functions by
                            yourself. Here it is important, that the function input is formatted as:
                            New_fct(x, par1, par2, ...).
            set_init_pars - Set initial parameters for the fit (not necessary for an anticrossing between
                            two curves).
            set_all       - Set all afore mentioned variables.
        
        Functions:
            fit            - Perform fit. This generates the results object, wherein fit results and 
                             errors are stored for all variables.
            
            plot_results   - Plot xy-input and fit results.
            
            plot_init_pars - Plot xy-input and coupled system as function of the initial parameters.
                             This can be useful for finding good starting values.
            
            crossing_fct   - Calculates the energy levels of a coupled system of an arbirary number of 
                             oscillators/qubits. The coupling is assumed XX-type (Jaynes-Cummings like).
            
            print_results  - Print fit results (crudely formatted).
    '''    
    def __init__(self):
        self.xdata = 0
        self.ydata = 0
        self.functions = 0
        self.p0 = 0
        self.fit_pars = 0
        self.cov_mat = 0
        self.results = 0
    
    
    # Small library of inbuilt functions:      
    def constant_line(self, x, a):
        '''
        Literally a constant line.
        y = a
        '''
        return a + 0*x
    
    
    def straight_line(self, x, a, b):
        '''
        A straight line, with slope a and offset b.
        y = a*x + b
        '''
        return a*x + b
    
       
    def parabola(self, x, a, b, c):
        '''
        A parabola with curvature a around x = b with offset c.
        y = a*(x - b)**2 + c
        '''
        return a*(x - b)**2 + c
    
    
    def transmon_f01(self, x, w0, L_eff, Phi_ext, djj, alpha):
        '''
        Input:
            w0      - Maximum frequency without detuning
            L_eff   - 2*pi*effective inductance/Phi0
            Phi_ext - Offset flux
            djj     - Josephson junction asymmetry i.e. (Ic1 - Ic2)/(Ic1 + Ic2)
            alpha   - Transmon anharmonicity
        Output:
            Primal transition frequency of a transmon qubit.
        
        Note: This function is oftentimes useless.
        ''' 
        return w0 * ((((np.cos(L_eff*x - Phi_ext))**2)**.5)*
                     (1+(djj**2)*(np.tan(L_eff*x - Phi_ext)**2)**.5)**.5)**.5 - alpha
    
    
    
    # Setter for xdata, ydata, functions and init_pars (p0).
    def set_xdata(self, *args):
        '''
        Set x datasets for the fit (at least 2 arrays, can be entered as a list).
        x arrays should be ordered by eigenvalue (ascending order).
        '''
        self.xdata = self._list_wrapper(args)
        self._xlen = len(self.xdata)
        if self._xlen <= 1:
            print "At least 2 x-arrays required."
        return


    def set_ydata(self, *args):
        '''
        Set y datasets for the fit (at least 2 arrays, can be entered as a list).
        y arrays should be ordered by eigenvalue (ascending order).
        '''
        self.ydata = self._list_wrapper(args)
        self._ylen = len(self.ydata)
        if self._ylen <=1:
            print "At least 2 y-arrays required."
        return


    def set_functions(self, *args):
        '''
        Set functions for the fit (at least 2, can be entered as a list).
        Each function should describe one of the undressed modes (i.e. without interaction/level repelling).
        '''
        self.functions = self._list_wrapper(args)
        self._flen = len(self.functions)
        if self._flen <= 1:
            print "At least 2 functions are required."
            return
        # Check if functions are callable. 
        # Determine number and name of free parameters of each function.
        self._fct_par_nums = []    # List of number of each functions parameters
        self._fct_par_names = []   # List of names of each functions parameters
        for fct in self.functions:
            if callable(fct):
                par_names = inspect.getargspec(fct)[0]
                try:
                    # Remove self as fct argument if function is from acf class
                    par_names.remove("self")
                except:
                    pass
                try:
                    # Remove x as fct argument
                    par_names.remove("x")
                except:
                    print "In " + fct.__name__ + ": No x argument found. Please rename axis variable to x."
                self._fct_par_names.append(par_names)
                self._fct_par_nums.append(len(par_names))
            else:
                print "At least one function is not callable."
                return
        # Increase number of parameters by number of coupling coefficients
        self._fct_par_nums.append((self._flen**2 - self._flen)/2)
        
        return


    def set_init_pars(self, *args):
        '''
        Set initial parameters for the fit.
        Order should be: parameter1 of fct1, par2 fct1, ..., g12, g13, ..
        '''
        self.p0 = self._list_wrapper(args)
        self._p0len = len(self.p0)
        return


    def set_all(self, x, y, f = None, p0 = None):
        '''
        Set initial parameters for the fit.
        x  - x datasets for the fit (at least 2 arrays, can be entered as a list).
             x arrays should be ordered by eigenvalue (ascending order).
        y  - y datasets for the fit (at least 2 arrays, can be entered as a list).
             y arrays should be ordered by eigenvalue (ascending order).
        f  - functions for the fit (at least 2, can be entered as a list). 
        Each function should describe one of the undressed modes (i.e. without interaction/level repelling). 
        Defaults are constant_line and straight_line.
        p0 - Initial parameters for the fit. Order should be: parameter1 of fct1, par2 fct1, ..., g12, g13, .. 
        If no initial parameters are given, all values are set to 1.
        '''
        self.set_xdata(x)
        self.set_ydata(y)
        if f != None:
            self.set_functions(f)
        elif self.functions == 0:
            print "Default functions set to constant_line and straight_line.\n"
            self.set_functions(self.constant_line, self.straight_line)
        if p0 != None:
            self.set_init_pars(p0)
        
        self._validity_check()
        self._check_p0()
        return


    def _list_wrapper(self, args):
        '''
        Wraps input for xdata, ydata, functions and init_pars in a list.
        '''
        if len(args) > 1:
            return list(args)
        elif (len(args) == 1) and isinstance(args[0], list):
            return args[0]
        else:
            print "Wrong input format."
            return [0]



    def _validity_check(self):
        '''
        Checks if input (xdata, ydata, functions) is valid.
        '''
        valid = 1
        
        # Check if parameters have been set.
        if self.xdata is 0:
            print "No xdata found. Use set_xdata for input."
            valid = 0
        if self.ydata is 0:
            print "No ydata found. Use set_ydata for input."
            valid = 0
        if self.functions is 0:
            print "No input functions found..."
            print "constant_line and straight_line set as default.\n"
            self.set_functions(self.constant_line, self.straight_line)
        if not valid:
            return

        # Check if the three lists are of the same length.
        if self._xlen != self._ylen:
            print("Number of x- (" + str(self._xlen) + ")  and y-arrays ("
                  + str(self._ylen) + ") is incompatible.")
            valid = 0
        if self._xlen != self._flen:
            print("Number of x-arrays (" + str(self._xlen) + ") and number of functions ("
                  + str(self._flen) + ") is incompatible.")
            valid = 0
        if self._ylen != self._flen:
            print ("Number of y-arrays (" + str(self._ylen) + ") and number of functions ("
                  + str(self._flen) + ") is incompatible.")
            valid = 0
        if not valid:
            return valid
        
        # Check if pairs of x- and y-arrays in xdata and ydata have the same length.
        for i in range(0, self._xlen):
            if len(self.xdata[i]) != len(self.ydata[i]):
                print("In xdata/ydata: Elements " + str(i) +" do not have the same lengths (" 
                      + str(len(self.xdata[i])) + ", " + str(len(self.ydata[i])) + ").")
                valid = 0
                
        return valid
        
    
    
    def _check_p0(self):
        '''
        Checks if initial parameters correspond to the system.
        '''
        p0_reset = False
        # If p0 is not set, set all values to 1.
        if self.p0 is 0:
            self.p0 = [1]*sum(self._fct_par_nums)
            p0_reset = True
            print "No initial parameters given. Setting all values to 1."
        # If number of initial parameters is to small/large -> cut/append.
        elif self._p0len < sum(self._fct_par_nums):
            self.p0 = np.append(self.p0, [1]*(sum(self._fct_par_nums) - self._p0len))
            p0_reset = True
            print "Not enough initial parameters. Filling up with 1."
        elif self._p0len > sum(self._fct_par_nums):
            self.p0 = self.p0[:sum(self._fct_par_nums)]
            p0_reset = True
            print "To many initial parameters given. Cutting off redundant values."
        
        if p0_reset:
            self._p0len = sum(self._fct_par_nums)
            print "New initial parameters:\n p0 = " + str(self.p0)
        return



    def _sort(self):
        '''
        Atempts to order the pairs of x-y-arrays by eigenvalue (ascending order), 
        which is necessary for the fit to converge properly.
        Here this is achieved by sorting according to the mean value of the ydata.
        '''
        # Sort ydata by mean value.
        indices = np.argsort([np.mean(i) for i in self.ydata])        
        self.xdata = list(np.array(self.xdata)[indices])
        self.ydata = list(np.array(self.ydata)[indices])
        if min(np.gradient(indices)) < 0:
            print "\nChanging order of x- and y-data respectively...\n"
        return



    def _reshape(self, pars):
        '''
        Reshape pars into a list of parameters, as is accepted by crossing_fct.
        Output:
            pars_new - list. Element i contains the fit parameters of function i.
                       The last element of fit_pars contains the coupling strenghts.
        '''
        pars_new = []
        for fct_par_num in self._fct_par_nums:
            pars_new.append(pars[0:fct_par_num])
            pars = pars[fct_par_num:]
            
        return pars_new



    def _generate_results(self):
        '''
        Generates a list which contains all results.
        '''
        # Generate list of function indices and parameter names
        fct_ind = []
        fit_pars = np.concatenate(self.fit_pars)
        par_names = np.concatenate(self._fct_par_names)
        for i in range(len(self._fct_par_nums) - 1):
            fct_ind.append([int(i + 1)]*self._fct_par_nums[i])
        fct_ind = np.concatenate(fct_ind)
        
        for i in range(self._flen - 1):
            for j in range(i + 1, self._flen):
                fct_ind = np.append(fct_ind, (i + 1)*10 + (j + 1))
                par_names = np.append(par_names, "g_" + str(fct_ind[-1]))
        self.results = zip(fct_ind, par_names, fit_pars, self.std_dev)
        return


    
    def _least_square_val(self, pars):
        '''
        Calculates the deviation of the input parameters from the current iteration of the fit function.
        This is minimized in the fit routine (methods of least squares).
        '''
        dev = []
        pars = self._reshape(pars)
        
        i=0
        for fct in self.functions:
            dev = np.append(dev, self.ydata[i] - self.crossing_fct(self.xdata[i], pars)[:, i])
            i += 1
            
        return dev



    def crossing_fct(self, x, pars):
        '''
        Evaluates the new shape of the coupled system.
       
        Input:
            x         - x values where the the coupled system is to be evaluated.
            fct_pars  - List of arrays. Each array contains parameters of the corresponding (undressed) function.
                        The last array in the list should contain the coupling strenghts.
        Output:
            func_vals - List of arrays. Array i cointains the y values of branch i of the coupled system.
        '''
        x = np.atleast_1d(x)
        fct_pars = pars[:-1]
        g = pars[-1]

        #Create the nondiagonal symmetric interaction matrix
        int_mat = np.zeros((self._flen, self._flen))
       
       
        for i in range(self._flen-1):
            int_mat[i, i+1:] = g[:np.size(int_mat[i,i+1:])]
            g = g[self._flen-1-i:]
        
        int_mat = int_mat+int_mat.T
        
        func_vals = np.zeros((np.size(x), self._flen))
        
        for n in range(np.size(x)):
            #Create diagonal parts of the matrix
            d_mat = np.zeros((self._flen, self._flen))
            i = 0
            for fct in self.functions:
                d_mat[i,i] = fct(x[n], *fct_pars[i])
                i += 1
            
            mat = d_mat + int_mat
            func_vals[n, :] = np.linalg.eigvalsh(mat)
        
        return func_vals



    def fit(self, show_data = True, show_plot = True):
        '''
        Input:
            show_data - If true, fit data is displayed after the fit.
            show_plot - If true, plot is displayed after the fit.
        Evalutates:
            fit_pars - Fit results.
            cov_mat  - Covariance matrix.
            std_dev  - Standard deviation.
            results  - List containing results for each free parameters.
                       1. Index of the function the parameter belongs to.
                          For the coupling strenght this indicates the modes which it belongs to.
                       2. Name of the parameter.
                       3. Value as extracted from the fit.
                       4. Standard deviation of the value.
                       
        Note: If the coupling strenght is zero for no reason, try switching the order of x1, x2, ... and
              y1, y2, ... Branches should be ordered such that their frequency increases.
        '''
        # Check if fit is executable:
        if not self._validity_check():
            print "\nAddress problems before fit can be excecuted."
            return
        
        self._check_p0()
        self._sort()
        
        fit_results = so.leastsq(self._least_square_val, self.p0, full_output = True)
        self.fit_pars, self.cov_mat = fit_results[0], fit_results[1]
        
        # Multiply covariance matrix with reduced chi squared to get standard deviation.
        if self.cov_mat is not None:
            self.cov_mat *= (sum(self._least_square_val(self.fit_pars)**2)/
                             (len(np.concatenate(self.xdata)) - float(len(self.p0))))
        # Check if covariance matrix calculation was successful.
        if self.cov_mat is not None:
            self.std_dev = np.abs(np.diag(self.cov_mat))**0.5
        else:
            print "Covariance matrix could not be calculated."
            self.std_dev = [float('nan')]*sum(self._fct_par_nums)
        
        # Reshape fit_pars into a list of parameters, as is accepted by crossing_fct.
        # After reshaping fit_pars is a list, where the element i contains the fit parameters of function i. 
        # The last element of fit_pars contains the coupling strenghts.
        self.fit_pars = self._reshape(self.fit_pars)
        # Change coupling to always have +sign
        self.fit_pars[-1] = np.abs(self.fit_pars[-1])
        self._generate_results()
        
        # Show output. Includes some crude formatting.
        if show_data:
            self.print_results()
                
        # Show plot.
        if show_plot:
            self.plot_results()
        
        return



    def print_results(self):
        '''
        Output: 
            Prints crudely formatted fit data.
        '''
        if self.fit_pars is 0:
            print "Fit was not yet performed. No data available."
            return
        format_str = " = ( {:7.4g} +- {:7.4g})"
        fct_index = 0
        for data_set in self.results:
            if (data_set[0] > fct_index) and (data_set[0] <= self._flen):
                print("\nCurve " + str(fct_index + 1) + " (" + self.functions[fct_index].__name__ + "):")
                fct_index += 1
            elif (fct_index == self._flen) and (data_set[0] > self._flen):
                fct_index += 1
                print("\nCoupling strengths:")
            print("    " + data_set[1] + format_str.format(data_set[2], data_set[3]))
        return



    def _plot(self, pars):
        '''
        Input:
            pars - Parameters for the plot.
        Output:
            Plot of input values and input parameters.
        '''
        dat_cols = np.array(['#0000FF', '#FF0000', '#008000', '#00CCCC', '#FF7F0E', '#CC00CC', '#000000'])
        fct_cols = np.array(['#0000FF70', '#FF000070', '#00800070', '#00CCCC50', '#FF7F0E50', '#CC00CC50', '#00000050'])
        mrkr = "*"
        if self._flen > len(dat_cols):
            dat_cols *= np.ceil(float(self._flen)/float(len(dat_cols)))
            fct_cols *= np.ceil(float(self._flen)/float(len(dat_cols)))
        
        if (self.xdata is 0) or (self.ydata is 0):
                print "No data for plot available."
                return
        for i in range(0, self._xlen):
            plt.plot(self.xdata[i], self.ydata[i], dat_cols[i], marker = mrkr, linewidth = 0)
        xlin = np.linspace(np.amin(np.concatenate(self.xdata)), np.amax(np.concatenate(self.xdata)), 1000)
        for i in range(self._flen):
            plt.plot(xlin, self.crossing_fct(xlin, pars)[:, i], fct_cols[i])
        plt.xlim(np.amin(np.concatenate(self.xdata)), np.amax(np.concatenate(self.xdata)))
        plt.ylim(np.amin(np.concatenate(self.ydata)), np.amax(np.concatenate(self.ydata)))
        return


    def plot_init_pars(self):
        '''
        Output:
            Plot of input values and initial parameters.
            This is useful to find good initial values for the fit.
        '''
        self._check_p0()
        self._sort()
        self._plot(self._reshape(self.p0))
        return
    

    def plot_results(self):
        '''
        Output:
            Plot of input values and fit.
        '''
        if self.fit_pars is 0:
            print "Fit was not yet performed. Use self.plot_init_pars() to look at your input."
            return
        self._plot(self.fit_pars)
        return
    
#  End of avoided_crossing_fit.py