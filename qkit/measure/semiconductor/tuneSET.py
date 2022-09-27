class TuneSET():
    def __init__(self, TG:list, B1:list, B2:list):
        self.TG = TG
        self.B1 = B1
        self.B2 = B2
        
        self.accumulation_value = 0.03
        self.is_accumulated = None
        
        #parameters for finding oscillation window
        self.accumulation_threshold = 0.8
        self.shutoff_value = 1e-3
        self.shift_value = 10e-3
        self.spacer_right = 0.08
        self.spacer_up = 0.08
        self.windowsize = 0.1
        
        self.number_iterations = 4
        
        #parameter for 2D sweep
        self.vstep = 5e-3

        #parameters for finding peaks in 2D sweep
        self.x_start = None 
        self.y_start = None
        self.x_shutoff = None
        self.y_shutoff = None
        self.peak_threshold = 8e-3
        self.max_distance_to_center = 0.01
        self.digits = 4 
        
        self.all_SET_gates = self.TG + self.B1 + self.B2
        self.sweep_gates = self.B1+self.B2
        
        
       
        self.regf = {} #registered functions
        self.watchdog = Watchdog()
        self.watchdog.register_node("feedback", 0, self.accumulation_value)

        """
        TG: list(int) 
            Topgate
        B1: list(int)
            sweep gate(s) on x-axis
            usually barrier gate to the left of the sensor dot
        B2: list(int)
            sweep gate(s) on y-axis
            usually barrier gate to the right of the sensor dot
            
        accumulation_value: float
            feedback value above which sample is considered as "accumulated", meaning conducting
        is_accumulated: NoneType or Boolean
            accumulation status of the sample. Default: None. 
        accumulation_threshold: float
           share of accumulation_value below which sample is not considered as fully "accumulated", meaning that restore_accumulation
           can take place before the find_oscillation_window function is called, raising the feedback value to 100% accumulation_value
        
        shutoff_value: float
            feedback value below which sample is considered as non-conducting
        shift_value: float
            amount by which the voltage is shifted during the search of the conduction shutoff point, recommended: 0.01 V
        spacer_right: float
            distance from conduction-shutoff point to right end of 2D sweep window, recommended: 0.08 V for a 100x100 mV windowsize
        spacer_up: float
            distance from conduction-shutoff point to upper end of 2D sweep window, recommended: 0.08 V for a 100x100 mV windowsize
        windowsize: float
            length of an axis of a 2D sweep measurement (quadratic window)
        number_iterations: int
            number of iterations of the find-oscillation-window algorithm. The algorithm stops if the same window is found twice or the number of search iterations equals number_iterations
        
        vstep: float
            resolution of 2D sweep, 5e-3 V for good resolution, 10e-3 V for fast measurement
            
        peak_threshold: float
            minimum signal of a peak to be considered as good peak for SET tuning
        max_distance_to_center: float
            voltage difference to the diagonal of the 2D sweep up to which a peak is considered as good peak. A measure for how symmetric the barriers must be
        digits: int
            number of digits printed in the findpeaks function (only for beauty reasons)
        
        sweep_gates: list(int)
            all sweepgates (B1 and B2)
        all_SET_gates: list(int)
            all sweepgates and the topgate (B1, B2, TG)

        
        regf["feedback"]: getter function of signal output, in case of locke: get_r_value(0) or get_r_value(4)
        regf["sg_get"]: getter function of gate input, in case of adwin: bill.get_out()
        regf["sg_set"] : setter function of gate input, in case of adwin: bill.set_out_parallel()
        regf["accumulation"](sweep_gates, accumulation_value): accumulation with selected gates until accumulation_value is reached
        regf["restore_accumulation"]: ramps sweepgates up until sweep_gates reach topgate value or feeadback reaches accumulation_value
        regf["2Dsweep"]: executes a 2D sweep
        self.find_oscillation_window: finds a measurement window containing a Coulomb oscillation of an SET
        self.find_peaks_in_2Dsweep: finds a peak in the Coulomb oscillation and sets the gates according to this peak
        
        """ 
    @property
    def TG(self):
        return self._TG
    
    @TG.setter
    def TG(self, TG):
        if not isinstance(TG, list):
                raise TypeError('TG must be a list.')
        else:
            self._TG = TG
            
    @property
    def B1(self):
        return self._B1
    
    @B1.setter
    def B1(self, B1):
        if not isinstance(B1, list):
                raise TypeError('B1 must be a list.')
        else:
            self._B1 = B1
            
    @property
    def B2(self):
        return self._B2
    
    @B2.setter
    def B2(self, B2):
        if not isinstance(B2, list):
                raise TypeError('B2 must be a list.')
        else:
            self._B2 = B2
            
    @property
    def accumulation_value(self):
        return self._accumulation_value
    
    @accumulation_value.setter
    def accumulation_value(self, accumulation_value):
        if not isinstance(accumulation_value, float):
                raise TypeError('accumulation_value must be a float.')
        else:
            self._accumulation_value = accumulation_value
            
    @property
    def accumulation_threshold(self):
        return self._accumulation_threshold
    
    @accumulation_threshold.setter
    def accumulation_threshold(self, accumulation_threshold):
        if not isinstance(accumulation_threshold, float):
                raise TypeError('accumulation_threshold must be a float.')
        else:
            self._accumulation_threshold = accumulation_threshold
            
    @property
    def shutoff_value(self):
        return self._shutoff_value
    
    @shutoff_value.setter
    def shutoff_value(self, shutoff_value):
        if not isinstance(shutoff_value, float):
                raise TypeError('shutoff_value must be a float.')
        else:
            self._shutoff_value = shutoff_value
            
    @property
    def shift_value(self):
        return self._shift_value
    
    @shift_value.setter
    def shift_value(self, shift_value):
        if not isinstance(shift_value, float):
                raise TypeError('shift_value must be a float.')
        else:
            self._shift_value = shift_value
            
    @property
    def spacer_right(self):
        return self._spacer_right
    
    @spacer_right.setter
    def spacer_right(self, spacer_right):
        if not isinstance(spacer_right, float):
                raise TypeError('spacer_right must be a float.')
        else:
            self._spacer_right = spacer_right
            
    @property
    def spacer_up(self):
        return self._spacer_up
    
    @spacer_up.setter
    def spacer_up(self, spacer_up):
        if not isinstance(spacer_up, float):
                raise TypeError('spacer_up must be a float.')
        else:
            self._spacer_up = spacer_up
            
    @property
    def windowsize(self):
        return self._windowsize
    
    @windowsize.setter
    def windowsize(self, windowsize):
        if not isinstance(windowsize, float):
                raise TypeError('windowsize must be a float.')
        else:
            self._windowsize = windowsize
            
    @property
    def number_iterations(self):
        return self._number_iterations
    
    @number_iterations.setter
    def number_iterations(self, number_iterations):
        if not isinstance(number_iterations, int):
                raise TypeError('number_iterations must be an int.')
        else:
            self._number_iterations = number_iterations
            
    @property
    def vstep(self):
        return self._vstep
    
    @vstep.setter
    def vstep(self, vstep):
        if not isinstance(vstep, float):
                raise TypeError('vstep must be a float.')
        else:
            self._vstep = vstep
   
    @property
    def peak_threshold(self):
        return self._peak_threshold
    
    @peak_threshold.setter
    def peak_threshold(self, peak_threshold):
        if not isinstance(peak_threshold, float):
                raise TypeError('peak_threshold must be a float.')
        else:
            self._peak_threshold = peak_threshold      
    
    @property
    def max_distance_to_center(self):
        return self._max_distance_to_center
    
    @max_distance_to_center.setter
    def max_distance_to_center(self, max_distance_to_center):
        if not isinstance(max_distance_to_center, float):
                raise TypeError('max_distance_to_center must be a float.')
        else:
            self._max_distance_to_center = max_distance_to_center    
    
    @property
    def digits(self):
        return self._digits
    
    @digits.setter
    def digits(self, digits):
        if not isinstance(digits, int):
                raise TypeError('digits must be an int.')
        else:
            self._digits = digits
        
    def _register_function(self, purpose, func, *args, **kwargs):
        print(func)
        if not callable(func):
            raise TypeError(("%s: Cannot set %s as get_value_func. Callable object needed." % (__name__, func)))                
        self.regf[purpose] = func
        
    def _register_function_preloaded(self, purpose, func, *args, **kwargs):
        print(func)
        if not callable(func):
            raise TypeError(("%s: Cannot set %s as get_value_func. Callable object needed." % (__name__, func)))                
        self.regf[purpose] = lambda : func(*args, **kwargs)
        
    def register_sweepgate_get(self, get_func, *args, **kwargs):
        self._register_function("sg_get", get_func, *args, **kwargs)
    
    def register_sweepgate_set(self, set_func, *args, **kwargs):
        self._register_function("sg_set", set_func, *args, **kwargs)

    def register_feedback(self, get_func, *args, **kwargs):
        self._register_function_preloaded("feedback", get_func,  *args, **kwargs)
        
    def register_accumulation(self, set_func, *args, **kwargs):
        self._register_function("accumulation", set_func, *args, **kwargs)
        
    def register_2Dsweep(self, func, *args, **kwargs):
        self._register_function("2Dsweep", func,  *args, **kwargs)
        
    def register_access_data(self, func, *args, **kwargs):
        self._register_function_preloaded("access_data", func,  *args, **kwargs)

    def check_whether_accumulated(self):
        if self.regf["feedback"]() >= self.accumulation_threshold*self.accumulation_value:
            self.is_accumulated = True
            print(f"Sample feedback is above {100*self.accumulation_threshold} \% of {self.accumulation_value} V, feedback is {self.regf['feedback']()} V")
        else:
            self.is_accumulated = False
            print(f"Sample feedback is below {100*self.accumulation_threshold} \% of {self.accumulation_value} V, feedback is {self.regf['feedback']()} V")
    
    def restore_accumulation(self):
        if self.is_accumulated == False:
            print("Restore accumulation")
            if self.regf["sg_get"](self.B1[0])>self.regf["sg_get"](self.B2[0]):
                print("Set sweep_gate(s) {self.B2} to value of sweep_gate {self.B1[0]}")
                self.regf["sg_set"](self.B2, self.regf["sg_get"](self.B1[0]))
            else:
                print(f"Set sweep_gate(s) {self.B1} to value of sweep_gate {self.B2[0]}")
                self.regf["sg_set"](self.B1, self.regf["sg_get"](self.B2[0]))
        
        self.check_whether_accumulated()
        if self.is_accumulated == False:
            if self.regf["sg_get"](self.B1[0])<self.regf["sg_get"](self.TG[0]):
                print(f"Ramp up sweep_gates {self.sweep_gates} to value of gate {self.TG} or until feedback {self.accumulation_value} V is reached.")
                self.regf["accumulation"](self.sweep_gates, self.regf["sg_get"](self.B1[0]), self.regf["sg_get"](self.TG[0]), self.accumulation_value)
        print("Accumulation restored.")
            
        
    def find_oscillation_window(self):
        x_start = self.regf["sg_get"](self.B1[0])
        y_start = self.regf["sg_get"](self.B2[0])
        start_values_x = []
        start_values_y = []
        
        self.check_whether_accumulated()
        if self.is_accumulated == False:
            self.restore_accumulation()
        for i in range(self.number_iterations):        
            while self.regf["feedback"]()>=self.shutoff_value:
                self.regf["sg_set"](self.B1, self.regf["sg_get"](self.B1[0])-self.shift_value)
                x_start = self.regf["sg_get"](self.B1[0]) + self.spacer_right
                print(f'Gate(s) {self.B1}: ', self.regf["sg_get"](self.B1[0]))
                time.sleep(0.2)
            
            self.regf["sg_set"](self.B1, x_start)
    
            while self.regf["feedback"]()>=self.shutoff_value:
                self.regf["sg_set"](self.B2, self.regf["sg_get"](self.B2[0])-self.shift_value)
                y_start = self.regf["sg_get"](self.B2[0]) + self.spacer_up
                print(f'Gate(s) {self.B2}: ', self.regf["sg_get"](self.B2[0]))
                time.sleep(0.2)
            
            self.regf["sg_set"](self.B2, y_start)
                
            start_values_x.append(x_start)
            start_values_y.append(y_start)
            
            if i>0 and round(start_values_x[i],2)==round(start_values_x[i-1],2) and round(start_values_y[i],2) == round(start_values_y[i-1],2):
                print('Same window found twice. Start 2D measurement.')
                break
            elif i == self.number_iterations-1:
                print(f'Searched {self.number_iterations} times. Optimal window may have not been found yet. Start 2D measurement anyway.')
        
        self.x_start = x_start
        self.y_start = y_start
        self.x_shutoff = self.x_start - self.spacer_right #save for later
        self.y_shutoff = self.y_start - self.spacer_up
        
        print("x_start: ", round(self.x_start, self.digits))
        print("y_start: ", round(self.y_start, self.digits))
        
        print("\nx_shutoff: ", round(self.x_shutoff,self.digits))
        print("y_shutoff: ", round(self.y_shutoff,self.digits))
              
        self.regf["2Dsweep"](self.B1, self.B2, self.vstep, self.vstep, self.x_start, self.x_start-self.windowsize, self.y_start, self.y_start-self.windowsize)

        
        
    
        
    def check_center(self, x,y, window_radius):
        if y >= x-window_radius and y<= x+window_radius:
            return True
            
    def check_height(self, z, threshold):
        if z>=threshold:
            return True
            
    def is_below_cutoff(self, x,y,cutoff_x, cutoff_y):
        if x <= cutoff_x or y<= cutoff_y:
            return True
        
    def myround(self,x):
        return self.vstep * round(x/self.vstep)
        
    def find_peaks_in_2Dsweep(self):
        data = self.regf["access_data"]()
        x = data['x']
        y = data['y']
        z =  data['z']
   
        #change coordinate system: x_start = 0, y_start = 0
        x -= np.ones(len(x))*self.x_start
        y -= np.ones(len(y))*self.y_start
        
        fp = findpeaks(method='topology', scale=True, denoise='fastnl', togray=False, imsize=(100,100))
        ## imsize must be (100,100)
        results = fp.fit(z)
        fp.plot(results)
        counter=0
        peak=[]
        for yv in range(100):
            for xv in range(100):
                if((results['Xdetect'][xv][yv]))>0:
                    #print(f'Detected Peaks: xv: {xv}, yv: {yv}')
                    peak.append([-xv*0.001,-yv*0.001])
                    counter += 1

        #print('\nNumber of peaks found: ', counter)
       
        
        z_values_peaks = []
        x_values_peaks = []
        y_values_peaks = []
        
        
        #check whether peak values coincide with data and save the peaks
        for k in range(counter-1):
            for i in range(len(x)):
                if self.myround(x[i])==self.myround(peak[k][0]):
                    #print('found x value: ', x[i])
                    for j in range(len(y)):
                        if self.myround(y[j])==self.myround(peak[k][1]):
                            x_values_peaks.append(x[i])
                            y_values_peaks.append(y[j])
                            z_values_peaks.append(z[i][j])
                    #print('found y value: ', y [j])

        x_good_peaks =[]
        y_good_peaks =[]
        z_good_peaks =[]
        if self.x_shutoff != None and self.y_shutoff != None:
            for l in range(len(z_values_peaks)):
                if self.check_center(x_values_peaks[l], y_values_peaks[l], self.max_distance_to_center)==True and self.check_height(z_values_peaks[l], self.peak_threshold) == True and self.is_below_cutoff(x_values_peaks[l], y_values_peaks[l], self.x_shutoff,self.y_shutoff):
                    #print(f'Good Peak found. x={x_values_peaks[l]}, y={y_values_peaks[l]}, z={z_values_peaks[l]}')
                    x_good_peaks.append(x_values_peaks[l])
                    y_good_peaks.append(y_values_peaks[l])
                    z_good_peaks.append(z_values_peaks[l])
        else:
            print("\nx_shutoff and y_shutoff  not given. In order to consider the below-cutoff-criteria, enter shutoff_x and shutoff_y or perform a new 2D sweep.")
            for l in range(len(z_values_peaks)):
                if self.check_center(x_values_peaks[l], y_values_peaks[l], self.max_distance_to_center)==True and self.check_height(z_values_peaks[l], self.peak_threshold) == True:
                    #print(f'Good Peak found. x={x_values_peaks[l]}, y={y_values_peaks[l]}, z={z_values_peaks[l]}')
                    x_good_peaks.append(x_values_peaks[l])
                    y_good_peaks.append(y_values_peaks[l])
                    z_good_peaks.append(z_values_peaks[l])
                    
                    
        if len(x_good_peaks)==0:
            if self.x_shutoff != None and self.y_shutoff != None:
                for l in range(len(z_values_peaks)):
                    if self.check_center(x_values_peaks[l], y_values_peaks[l], self.max_distance_to_center*3)==True and self.check_height(z_values_peaks[l], self.peak_threshold) == True and self.is_below_cutoff(x_values_peaks[l], y_values_peaks[l],self.x_shutoff,self.y_shutoff):
                        print(f'\nNo peak found in center of picture. Peak found for increased search radius from {self.max_distance_to_center} V to 3*{self.max_distance_to_center} V:')
                        print(f'x={x_values_peaks[l]}, y={y_values_peaks[l]}, r={z_values_peaks[l]}')
                        x_good_peaks.append(x_values_peaks[l])
                        y_good_peaks.append(y_values_peaks[l])
                        z_good_peaks.append(z_values_peaks[l])
            else: 
                print("\nx_shutoff and y_shutoff not given. In order to consider the below-cutoff-criteria, enter shutoff_x and shutoff_y or perform a new 2D sweep.")
                for l in range(len(z_values_peaks)):
                    print(f'\n No peak found in center of picture. Peak found for increased search window radius from {self.max_distance_to_center} V to 3*{self.max_distance_to_center} V:')
                    print(f'x={x_values_peaks[l]}, y={y_values_peaks[l]}, r={z_values_peaks[l]}')
                    x_good_peaks.append(x_values_peaks[l])
                    y_good_peaks.append(y_values_peaks[l])
                    z_good_peaks.append(z_values_peaks[l])
        
        

        if len(x_good_peaks)==0:
            print('No peaks found. Some possible reasons: \n A) 2D sweep window not centered. \n B) There is no dot formed yet.')         
        
        sel_peak = dict()
        
        for m in range(len(z_good_peaks)):
            if z_good_peaks[m] == min(z_good_peaks):
                sel_peak['x'] = x_good_peaks[m]
                sel_peak['y'] = y_good_peaks[m]
                sel_peak['z'] = z_good_peaks[m]
        print('\n')
        #print(f"Selected peak (relative values): {sel_peak}")
         
        ##Shift coordinate system back to get values in 2D sweep picture
        sel_peak['x'] += self.x_start
        sel_peak['y'] += self.y_start
        
        for m in range(len(z_good_peaks)):
            x_good_peaks[m] += self.x_start
            y_good_peaks[m] += self.y_start
            print(f'Good peak: x: {round(x_good_peaks[m],self.digits)}, y: {round(y_good_peaks[m],self.digits)}, z: {round(z_good_peaks[m],self.digits)}')
         #x_good_peaks += np.ones(len(x_good_peaks))*self.x_start
        #y_good_peaks += np.ones(len(y_good_peaks))*self.y_start
        print('\n \n')
        print(f"Selected peak (values in 2D sweep): \n x: {round(sel_peak['x'],self.digits)}, y: {round(sel_peak['y'],self.digits)}, z: {round(sel_peak['z'],self.digits)} ")
        print('\n \n')
       
        self.regf["sg_set"](self.B1, sel_peak['x'])
        self.regf["sg_set"](self.B2, sel_peak['y'])
        
