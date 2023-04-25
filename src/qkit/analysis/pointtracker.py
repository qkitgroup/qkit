# -*- coding: utf-8 -*-
"""
Data point tracker by YS @ KIT / 2017
"""

import peakutils
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm


class pointtracker():
    """
    New point tracking routine, successor to the soon deprecated ac_preparation.
    Used to detect peaks or dips along branches (e.g. of anticrossings) in a 2d spectrum.
    
    Functions:
        set_data             -- defining the data set to be handled
        set_searchparams     -- setting the parameters for the search: start, span and point type
        set_peakutils_params -- if necessary, change the parameters of the used peakutils
        start_tracking       -- starting the actual point tracking routine
        del_trace            -- remove one of the detected point traces
        cut                  -- remove a given amount of detected points from a given trace
        del_points           -- remove a specific set of points from a given trace
        plot                 -- plot the data with an overlay of the detected points
        get_results          -- return the results in dimensions of xdata and ydata
    """
    
    def __init__(self):
        # initialize arrays
        self.x_results = []
        self.y_results = []
        
        # set default parameters for peakutils
        self._thres = 0.3
        self._min_dist = 1
   
    
    def set_data(self, xdata, ydata, data):
        """
        Defines the data arrays to be used by the pointtracker.
        Requires 3 arrays of a 2d spectrum
        
        Keyword arguments:
            xdata -- array of the sweep coordinates (e.g. current values)
            ydata -- usually the frequency array
            data  -- usually amplitude data, in the form of [len(xdata),len(ydata)]
        """
        
        self.xdata = xdata
        self.ydata = ydata
        self.data = data
        
        
    def set_searchparams(self, start_coords, span, dips=True):
        """
        Set the parameters for the search: start, span and point type
        Requires set_data to be run before
        
        Keyword arguments:
            start_coords -- guessed arbitrary point on branch in form [x,y]
                            and units of xdata and ydata
            span         -- the span along the y-axis in units of ydata
            dips         -- search for dips instead of peaks (default True)
        """
        
        try: self.data
        except AttributeError:
            print("Please run set_data first")
            return
        
        # if dips are searched invert the dataset
        if dips: self._sig = -1
        else: self._sig = +1
        
        # find closest real data point to given start_coords and translate in indices
        self.start_coords = []
        self.start_coords.append(np.argmin(np.abs(self.xdata-start_coords[0])))
        self.start_coords.append(np.argmin(np.abs(self.ydata-start_coords[1])))
        
        # translate given span in span of indices
        self.span=int(span/((self.ydata[-1]-self.ydata[0])/len(self.ydata)))
        
        
    def set_peakutils_params(self, thres=0.3, min_dist=1):
        """
        If necessary, change the parameters of the used peakutils
            
        Keyword arguments:
            thres (float)  -- normalized threshold (default: 0.3)
                              only peaks with amp higher than this will be detected
            min_dist (int) -- minimum distance between each detected peak (default: 1)
        """
        
        self._thres = thres
        self._min_dist = min_dist
        
    
    def start_tracking(self):
        """
        Start the actual point tracking routine.
        Requires set_data and set_searchparams to be run before.
        The points found along one branch are sorted and stored as numpy arrays of their
        x- and ydata indices which are appended to the x_results and y_results lists.
        """
        
        # initialize temporary point arrays
        self._points_x = np.array([],dtype="int")
        self._points_y = np.array([],dtype="int")
        
        # recursively find points
        self._track_points(self.start_coords, direction=0)
        
        # sort point arrays
        self._points_y = self._points_y[np.argsort(self._points_x)]
        self._points_x = np.sort(self._points_x)
        
        # append results to result arrays
        self.x_results.append(self._points_x)
        self.y_results.append(self._points_y)
        
        # clean up
        self._points_x = np.array([],dtype="int")
        self._points_y = np.array([],dtype="int")

    
    def _track_points(self, search_indices, direction):
        """
        The actual point tracking routine.
        Should only be run via the start_tracking function.
        Calls itself recursively and walks along one branch in both directions,
        starting from given start_coords and detects peaks or dips in a given span.
        For the next call, the search_indices are shifted depending on the distance
        between the last found points.
        Recursion stops as soon as the boundary of the dataset is reached in both directions.
        Detected points are added to the hidden _points_x and _points_y arrays.
        """
        
        # Test if still in data
        if (search_indices[0]<0 or search_indices[0]>=len(self.xdata) or
            search_indices[1]-self.span/2<0 or search_indices[1]+self.span/2>=len(self.ydata)):
            print("Reached boundary of dataset")
            return
        
        search_data = self._sig * self.data[int(search_indices[0]), int(search_indices[1]-self.span/2) : int(search_indices[1]+self.span/2)]

        indexes_found = peakutils.indexes(search_data, thres=self._thres, min_dist=self._min_dist)

        # add found peaks to arrays, and repeat recursively with shifted search_indices
        if indexes_found.size>=1:
            y_new = search_indices[1] - int(self.span/2) + indexes_found[0]
            self._points_y = np.append(self._points_y,y_new)
            self._points_x = np.append(self._points_x,search_indices[0])
            
            # If more than one peak found, print it and take the first one
            if indexes_found.size>1:
                print("Found more than one peak in trace " + str(search_indices[0]))
                print("First found peak added")
                
        # If no peak found, print it and continue with next current trace
        else:
            print("No peak found in trace " + str(search_indices[0]))
            # Add distance between two last found peaks to shift
            if len(self._points_y) >= 2:
                y_new = self._points_y[-1] + (self._points_y[-1] - self._points_y[-2])
            else:
                y_new = search_indices[1]
             
        # shift search intervall (if not the first point) and search in shifted intervall
        if direction==0:
            self._track_points([search_indices[0]+1,search_indices[1]], direction=1)
            self._track_points([search_indices[0]-1,search_indices[1]], direction=-1)
        else:
            search_indices[1] = search_indices[1] + (y_new - search_indices[1])
            self._track_points([search_indices[0]+direction,search_indices[1]], direction=direction)
            
            
    def del_trace(self, trace=-1, all=False):
        """
        Remove one of the detected point traces (default: last one).
        
        Keyword arguments:
            trace (int) -- # of trace to remove from results
            all (bool)  -- clear results
        """
        
        if all:
            for i in range(0,len(self.x_results)):
                self.x_results.pop(-1)
                self.y_results.pop(-1)
        else:
            self.x_results.pop(trace)
            self.y_results.pop(trace)
            
            
    def cut(self, amount=0, trace=-1, end="high"):
        """
        Remove a given amount (default: 0) of detected points from a given trace (default: -1).
        It starts from the given end (default: high end in x dimensions).
        
        Keyword arguments:
            amount (int) -- amount of points to be removed from the end of the trace
            trace (int)  -- # of trace to remove points from
            end (str)    -- from which end to start ("high" or "low")
        """
        
        if amount == 0:
            n = None
        else:
            if end == "high":
                n = -amount
                self.x_results[trace] = self.x_results[trace][0:n]
                self.y_results[trace] = self.y_results[trace][0:n] 
            else:
                n = amount
                self.x_results[trace] = self.x_results[trace][n:None]
                self.y_results[trace] = self.y_results[trace][n:None]        


    def del_points(self, indices=[], trace=-1):
        """
        Remove a specific set of points (default : []) from a given trace (default: -1).
        
        Keyword arguments:
            indices ([int]) -- list of indices of points to be removed from the trace
            trace (int)     -- # of trace to remove points from
        """
        
        self.x_results[trace] = np.delete(self.x_results[trace], indices)
        self.y_results[trace] = np.delete(self.y_results[trace], indices)
        
        
    def plot(self, all=True, amount=1, log=False):
        """
        Plot the data with an overlay of the detected points.
        
        Keyword arguments:
            all (bool)   -- plot all detected traces (default: True)
            amount (int) -- plot given amount of traces (default: 1)
            log (bool)   -- plot data logarithmically (default: False)
        """
        
        fig, axes = plt.subplots(figsize=(16,8))
        
        
        if log==False:
            plt.pcolormesh(self.xdata, self.ydata, self.data.T, cmap="viridis")
        else:
            plt.pcolormesh(self.xdata, self.ydata, self.data.T, cmap="viridis", norm=LogNorm(vmin=self.data.min(), vmax=self.data.max()))
        plt.xlim(min(self.xdata), max(self.xdata))
        plt.ylim(min(self.ydata), max(self.ydata))
        plt.colorbar()
        
        if all:
            n = len(self.x_results)
        else:
            n = amount
        col = ["r", "w", "m", "k", "b", "g", "c", "y"]
        if n>len(col):
            m=int(n/len(col)+1)
            col=m*col
        
        for i in range(0,n):
            plt.plot(self.xdata[self.x_results[i]], self.ydata[self.y_results[i]], col[i]+"x", label="Trace %d"%(i))
        
        plt.legend()
        
        
    def get_results(self):
        """
        Return the results in dimensions of xdata and ydata.
        Returns a list of two lists (for x and y) of numpy arrays (with the detected points).
        """
        
        xres = []
        yres = []
        
        for i in range(0,len(self.x_results)):
            xres.append(self.xdata[self.x_results[i]])
            yres.append(self.ydata[self.y_results[i]])
        
        return [xres,yres]