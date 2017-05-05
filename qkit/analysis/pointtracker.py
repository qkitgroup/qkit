# -*- coding: utf-8 -*-
"""
data point tracker by YS @ KIT / 2017
"""

import peakutils
import numpy as np


class pointtracker():
    """
    New point tracking routine, successor to the soon deprecated ac_preparation.
    Used to detect peaks or dips along branches (e.g. of anticrossings) in a 2d spectrum.
    
    Functions (incomplete):
        set_data         -- defining the data set to be handled
        set_searchparams -- setting the parameters for the search: start, span and point type
        start_tracking   -- starting the actual point tracking routine
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
            print "Please run set_data first"
            return
        
        # if dips are searched invert the dataset
        if dips: self.data = -self.data
        
        # find closest real data point to given start_coords and translate in indices
        self.start_coords = []
        self.start_coords.append(np.argmin(np.abs(self.xdata-start_coords[0])))
        self.start_coords.append(np.argmin(np.abs(self.ydata-start_coords[1])))
        
        # translate given span in span of indices
        self.span=int(span/((self.ydata[-1]-self.ydata[0])/len(self.ydata)))
        
        
    def set_peakutils_params(self, thres, min_dist):
        """
        If necessary, change the parameters of the used peakutils
            
        Keyword arguments:
            thres (float)  -- normalized threshold
                              only peaks with amp higher than this will be detected
            min_dist (int) -- minimum distance between each detected peak
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
            search_indices[1]-self.span/2.<0 or search_indices[1]+self.span/2.>=len(self.ydata)):
            print "Reached boundary of dataset"
            return
        
        search_data = self.data[search_indices[0],search_indices[1]-self.span/2.:search_indices[1]+self.span/2.]

        indexes_found = peakutils.indexes(search_data,thres=self._thres,min_dist=self._min_dist)

        # add found peaks to arrays, and repeat recursively with shifted search_indices
        if indexes_found.size>=1:
            y_new = search_indices[1] - int(self.span/2) + indexes_found[0]
            self._points_y = np.append(self._points_y,y_new)
            self._points_x = np.append(self._points_x,search_indices[0])
            
            # If more than one peak found, print it and take the first one
            if indexes_found.size>1:
                print "Found more than one peak in trace " + str(search_indices[0])
                print "First found peak added"
                
        # If no peak found, print it and continue with next current trace        
        else:
            print "No peak found in trace " + str(search_indices[0])
            # Add distance between to last found peaks to shift
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