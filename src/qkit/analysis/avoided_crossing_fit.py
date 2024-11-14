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

class ACF():
    """
    Avoided crossing fit class (AS@KIT 2017):
    Useful for extracting the coupling strenght from avoided level crossings between an arbirary number of functions.
    
        Attributes:
            set_xdata:     Set x-data for the fit.
            set_ydata:     Set y-data for the fit.
            set_functions: Set functions of the undressed/uncoupled systems. You can also define functions by yourself.
                           Here it is important, that the function input is formatted as: New_fct(x, par1, par2, ...)
            set_init_pars: Set initial parameters for the fit (not necessary for an anticrossing between two curves).
            set_all:       Set all afore mentioned variables.

            fit:            Perform fit and generate results attribute. The latter stores the fit results and corresponding errors (least squares).
            plot_init_pars: Plot xy-input coupled modes for the initial parameters. This can be useful for finding good starting values.
            plot_results:   Plot xy-input and fit results.
            crossing_fct:   Calculates the energy levels of a coupled system of an arbirary number of modes (assuming transverse/XX-coupling of the modes).
            print_results:  Print fit results (crudely formatted).
    """    
    def __init__(self):
        self.xdata = 0
        self.ydata = 0
        self.functions = None
        self.p0 = None
        self.fit_pars = 0
        self.cov_mat = 0
        self.results = 0
    
    # Small library of inbuilt functions:      
    def constant_line(self, x, a):
        """
        A constant line.

        Args:
            x: x-value (allows for the output of arrays)
            a: return value
        
        Returns:
            An array with same length as x and value: a
        """
        return a + 0 * x
    
    def straight_line(self, x, a, b):
        """
        A straight line with slope a and offset b.

        Args:
            x: x-value
            a: Slope
            b: Offset in y-direction
        
        Returns:
            An array with same length as x and return value: a * x + b
        """
        return a * x + b
    
    def parabola(self, x, a, b, c):
        """
        A parabola with curvature a around x = b with offset c.

        Args:
            x: x value
            a: second derivative / 2
            b: Offset in x-direction
            c: Offset in y-direction

        Returns:
            An array with same length as x and return value: a*(x - b)**2 + c
        """
        return a * (x - b)**2 + c

    def hyperbola(self, x, a, b, c):
        """
        A hyperbola around x = b with offset c.

        Args:
            x: x value
            a:
            b: Offset in x-direction
            c: Offset in y-direction

        Returns:
            An array with same length as x and return value: a*(x - b)**2 + c
        """
        return np.sqrt(a * (x - b) ** 2 + c)
    
    def transmon_f01(self, x, w0, L, I_ext, djj):
        """
        Dispersion of a tunable transmon qubit with junction asymmetry.

        Args:
            x:     x-value
            w0:    Maximum qubit frequency without detuning.
            L:     Oscillation period in current/x-value.
            I_ext: Offset current/x offset.
            djj:   Josephson junction asymmetry (Ic1 - Ic2)/(Ic1 + Ic2)
        
        Returns:
            Primal transition frequency of a transmon qubit.
        """
        return  w0 * (np.abs(np.cos(np.pi/L*(x - I_ext)))*(1 + djj**2*np.tan(np.pi/L*(x - I_ext))**2)**.5)**0.5
    

    def set_xdata(self, *args):
        """
        Set x-datasets for the fit.
        x-arrays should be ordered by eigenvalue of the y-arrays (ascending order).

        Args:
            x-arrays of the undressed modes (at least 2).
            A list of arrays is also allowed as input.
        """
        self.xdata = self._list_wrapper(args)
        self._xlen = len(self.xdata)
        if self._xlen <= 1:
            print("At least 2 x-arrays required.")
        return
    
    def set_ydata(self, *args):
        """
        Set y-datasets for the fit.
        y-arrays should be ordered by eigenvalue (ascending order).

        Args:
            y-arrays of the undressed modes (at least 2).
            A list of arrays is also allowed as input.
        """
        self.ydata = self._list_wrapper(args)
        self._ylen = len(self.ydata)
        if self._ylen <=1:
            print("At least 2 y-arrays required.")
        return
    
    def set_functions(self, *args):
        """
        Set functions for the fit.
        Each function should describe one of the undressed modes (i.e. without interaction/level repelling).

        Args:
            functions of the undressed modes (at least 2). 
            A list of functions is also allowed as input.
        """
        self.functions = self._list_wrapper(args)
        self._flen = len(self.functions)
        if self._flen <= 1:
            print("At least 2 functions are required.")
            return
        # Check if functions are callable. 
        # Determine number and name of free parameters of each function.
        self._fct_par_nums = []    # List of number of each functions parameters
        self._fct_par_names = []   # List of names of each functions parameters
        for fct in self.functions:
            if callable(fct):
                sig = inspect.signature(fct)
                par_names = list(sig.parameters.keys())
                try:
                    # Remove self as fct argument if function is from acf class
                    par_names.remove("self")
                except:
                    pass
                try:
                    # Remove x as fct argument
                    par_names.remove("x")
                except:
                    print("In " + fct.__name__ + ": No x argument found. Please rename axis variable to x.")
                self._fct_par_names.append(par_names)
                self._fct_par_nums.append(int(len(par_names)))
            else:
                print("At least one function is not callable.")
                return
        # Increase number of parameters by number of coupling coefficients
        self._fct_par_nums.append(int((self._flen**2 - self._flen)/2))
        
        return
    
    def set_init_pars(self, *args):
        """
        Set initial parameters for the fit.
        Order should be: parameter1 of fct1, par2 fct1, ..., g12, g13, ...
        If the number of input parameters is insuffcient they are later on set to 1.

        Args:
            List of initial parameters.
        """
        self.p0 = self._list_wrapper(args)
        self._p0len = len(self.p0)
        return
    
    def set_all(self, x, y, f = None, p0 = None):
        """
        Set initial parameters for the fit.

        Args:
            x:  x-datasets for the fit (at least 2 arrays, can be entered as a list).
                x-arrays should be ordered by eigenvalue (ascending order).
            y:  y-datasets for the fit (at least 2 arrays, can be entered as a list).
                y-arrays should be ordered by eigenvalue (ascending order).
            f:  functions for the fit (at least 2, can be entered as a list). 
                Each function should describe one of the undressed modes (i.e. without interaction/level repelling). 
                By default, functions are set to constant_line and straight_line.
            p0: Initial parameters for the fit. Order should be: parameter1 of fct1, par2 fct1, ..., g12, g13, .. 
                If no initial parameters are given all values are set to 1.
        """
        self.set_xdata(x)
        self.set_ydata(y)
        if f != None:
            self.set_functions(f)
        elif self.functions is None:
            print("Default functions set to constant_line and straight_line.\n")
            self.set_functions(self.constant_line, self.straight_line)
        if p0 != None:
            self.set_init_pars(p0)
        
        self._validity_check()
        self._check_p0()
        return
    
    def _list_wrapper(self, args):
        """
        Wraps input for x-data, y-data, functions and init_pars in a list.

        Args:
            List or touple.
        
        Returns:
            List of input arguments.
        """
        if len(args) > 1:
            return list(args)
        elif (len(args) == 1) and isinstance(args[0], list):
            return args[0]
        else:
            print("Wrong input format.")
            return [0]
    
    def _validity_check(self):
        """
        Checks if input (x-data, y-data, functions) is valid, i.e. have the same dimension/length.

        Returns:
            Bool for validity of the input.
        """
        valid = 1
        
        # Check if parameters have been set.
        if self.xdata is 0:
            print("No xdata found. Use set_xdata for input.")
            valid = 0
        if self.ydata is 0:
            print("No ydata found. Use set_ydata for input.")
            valid = 0
        if self.functions is None:
            print("No input functions found...")
            print("constant_line and straight_line set as default.\n")
            self.set_functions(self.constant_line, self.straight_line)
        if not valid:
            return

        # Check if the three lists are of the same length.
        if self._xlen != self._ylen:
            print("Number of x- (" + str(self._xlen) + ")  and y-arrays (" + str(self._ylen) + ") is incompatible.")
            valid = 0
        if self._xlen != self._flen:
            print("Number of x-arrays (" + str(self._xlen) + ") and number of functions (" + str(self._flen) + ") is incompatible.")
            valid = 0
        if self._ylen != self._flen:
            print("Number of y-arrays (" + str(self._ylen) + ") and number of functions (" + str(self._flen) + ") is incompatible.")
            valid = 0
        if not valid:
            return valid
        
        # Check if pairs of x- and y-arrays in xdata and ydata have the same length.
        for i in range(0, self._xlen):
            if len(self.xdata[i]) != len(self.ydata[i]):
                print("In xdata/ydata: Elements " + str(i) +" do not have the same lengths (" + str(len(self.xdata[i])) + ", " + str(len(self.ydata[i])) + ").")
                valid = 0
                
        return valid
    
    def _check_p0(self):
        """
        Checks if initial parameters p0 have the correct format.
        For an insufficent number of parameters the remaining ones are set to 1.
        If p0 is too long it is truncated to the necessary length.
        """
        p0_reset = False
        # If p0 is not set, set all values to 1.
        if self.p0 is None:
            self.p0 = [1]*int(sum(self._fct_par_nums))
            p0_reset = True
            print("No initial parameters given. Setting all values to 1.")
        # If number of initial parameters is to small/large -> cut/append.
        elif self._p0len < sum(self._fct_par_nums):
            self.p0 = np.append(self.p0, [1]*int(sum(self._fct_par_nums) - self._p0len))
            p0_reset = True
            print("Not enough initial parameters. Filling up with 1.")
        elif self._p0len > sum(self._fct_par_nums):
            self.p0 = self.p0[:int(sum(self._fct_par_nums))]
            p0_reset = True
            print("To many initial parameters given. Cutting off redundant values.")
        
        if p0_reset:
            self._p0len = sum(self._fct_par_nums)
            print("New initial parameters:\n p0 = " + str(self.p0))
        return
    
    def _sort(self):
        """
        Atempts to order the pairs of x-y-arrays by eigenvalue (ascending order).
        Sorting is necessary for the fit to converge properly.
        Here this is achieved by sorting according to the mean value of the y-datasets.
        """
        # Sort ydata by mean value.
        indices = np.argsort([np.mean(i) for i in self.ydata])
        self.xdata = [self.xdata[i] for i in indices]
        self.ydata = [self.ydata[i] for i in indices]    
        if min(np.gradient(indices)) < 0:
            print("\nChanging order of x- and y-data respectively...\n")
        return
    
    def _reshape(self, pars):
        """
        Reshape pars into a list of parameters, as is accepted by crossing_fct.

        Args:
            pars: Parameters to be reshaped.
        
        Returns:
            List of parameters, the i'th element contains the fit parameters of function i.
            The last element of fit_pars contains the values for the coupling strenghts.
        """
        pars_new = []
        for fct_par_num in self._fct_par_nums:
            pars_new.append(pars[0:fct_par_num])
            pars = pars[fct_par_num:]
            
        return pars_new
    
    def _generate_results(self):
        """
        Generates a list which contains the results and errors for all parameters.
        """
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
        self.results = list(zip(fct_ind, par_names, fit_pars, self.std_dev))
        return
    
    def _least_square_val(self, pars):
        """
        Calculates the deviation of the coupled mode functions from the xy-input values for input parameters.
        This is deviation is minimized in the fit routine (least squares).

        Args:
            pars: Parameters from the fit.
        
        Returns:
            Deviation of coupled mode functions from xy-input.
        """
        dev = []
        pars = self._reshape(pars)
        
        for i, fct in enumerate(self.functions):
            dev = np.append(dev, self.ydata[i] - self.crossing_fct(self.xdata[i], pars)[:, i])
            
        return dev
    
    def crossing_fct(self, x, pars):
        """
        Evaluates the functions of the coupled modes (diagonalizes the matrix).

        Input:
            x:        x-values where the the functions are to be evaluated
            fct_pars: List of arrays, each array contains parameters of the corresponding (undressed) function.
                      The last array in the list contains values for the coupling strenghts.
        
        Returns:
            List of arrays, where the i'th array cointains the y-values of branch i of the coupled system.
        """
        x = np.atleast_1d(x)
        fct_pars = pars[:-1]
        g = np.atleast_1d(pars[-1])

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
            for i, fct in enumerate(self.functions):
                d_mat[i,i] = fct(x[n], *fct_pars[i])
            
            mat = d_mat + int_mat
            func_vals[n, :] = np.linalg.eigvalsh(mat)

        return func_vals
    
    def fit(self, show_data = True, show_plot = True):
        """
        Fit functions of the coupled modes to the stored xy-data.
        Generates the results attribute, i.e. a list containing results for each free parameters:
            1. Index of the function the parameter belongs to
               For the coupling strenght this indicates the modes it belongs to
            2. Name of the parameter
            3. Value as extracted from the fit
            4. Standard deviation of the value
        
        Args:
            show_data: If true, fit data is displayed after the fit.
            show_plot: If true, plot is displayed after the fit.
        """
        # Check if fit is executable:
        if not self._validity_check():
            print("\nAddress problems before fit can be excecuted.")
            return
        
        self._check_p0()
        self._sort()
        
        fit_results = so.leastsq(self._least_square_val, self.p0, full_output = True)
        self.fit_pars, self.cov_mat = fit_results[0], fit_results[1]
        # Multiply covariance matrix with reduced chi squared to get standard deviation.
        if self.cov_mat is not None:
            self.cov_mat *= (sum(self._least_square_val(self.fit_pars)**2)/
                             (len(np.concatenate(self.xdata)) - float(len(self.p0))))
            # Calculate standard deviation
            self.std_dev = np.abs(np.diag(self.cov_mat))**0.5
        else:
            print("Covariance matrix could not be calculated.")
            self.std_dev = [float('nan')]*sum(self._fct_par_nums)
        
        # Reshape fit_pars into a list of parameters, as is accepted by crossing_fct.
        # After reshaping fit_pars is a list, where the element i contains the fit parameters of function i. 
        # The last element of fit_pars contains the coupling strenghts.
        self.fit_pars = self._reshape(self.fit_pars)
        self._generate_results()
        
        # Show output. Includes some crude formatting.
        if show_data:
            self.print_results()
                
        # Show plot.
        if show_plot:
            self.plot_results()

        return

    def print_results(self):
        """
        Prints the fit results in a legible form.
        """
        if self.fit_pars is 0:
            print("Fit was not yet performed. No data available.")
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
        """
        Plots the input xy-datasets, as well as the coupled modes for the input parameters.

        Args:
            pars: Parameters of coupled modes for the plot.
        """
        dat_cols = np.array(['#0000FF', '#FF0000', '#008000', '#00CCCC', '#FF7F0E', '#CC00CC', '#000000'])
        fct_cols = np.array(['#0000FF70', '#FF000070', '#00800070', '#00CCCC50', '#FF7F0E50', '#CC00CC50', '#00000050'])
        mrkr = "*"
        if self._flen > len(dat_cols):
            dat_cols *= np.ceil(float(self._flen)/float(len(dat_cols)))
            fct_cols *= np.ceil(float(self._flen)/float(len(dat_cols)))
        
        if (self.xdata is 0) or (self.ydata is 0):
                print("No data for plot available.")
                return
        for i in range(0, self._xlen):
            plt.plot(self.xdata[i], self.ydata[i], dat_cols[i], marker = mrkr, linewidth = 0)
        xlin = np.linspace(np.nanmin(np.concatenate(self.xdata)), np.nanmax(np.concatenate(self.xdata)), 1000)
        for i in range(self._flen):
            plt.plot(xlin, self.crossing_fct(xlin, pars)[:, i], fct_cols[i])
        plt.xlim(np.nanmin(np.concatenate(self.xdata)), np.nanmax(np.concatenate(self.xdata)))
        plt.ylim(np.nanmin(np.concatenate(self.ydata)), np.nanmax(np.concatenate(self.ydata)))
        plt.show()
        return
    
    def plot_init_pars(self):
        """
        Plot of input xy-datasets and coupled modes for the initial parameters.
        This is useful to find reasonable initial values for the fit.
        """
        self._check_p0()
        self._sort()
        self._plot(self._reshape(self.p0))
        return
    
    def plot_results(self):
        """
        Plot of input xy-datasets and the coupled modes using the fit results.
        """
        if self.fit_pars is 0:
            print("Fit was not yet performed. Use self.plot_init_pars() to look at your input.")
            return
        self._plot(self.fit_pars)
        return