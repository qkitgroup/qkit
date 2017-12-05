import numpy
import sys
#import scipy.optimize as spopt
#from scipy import stats


class IV_curve(object):
    def __init__(self):
        pass
    
    
    def get_Ic(self, V, I, direction=1):
        dVdI = numpy.gradient(V)/numpy.gradient(I)
        delta = 1e6
        maxima = {'index':[], 'y':[], 'x':[]}
        maxima, minima = self.get_peaks(y=dVdI, delta=1e6, x=I)
        while maxima['index'] == []:
            maxima, minima = self.get_peaks(y=dVdI, delta=delta, x=I)
            delta = delta/10.
        if direction == 1:
            Ic = maxima['x'][0]
        elif direction == -1:
            Ic = maxima['x'][-1]
        return Ic
    
    
    def get_peaks(self, y, delta, x=None):
        '''
        Gets the local maxima and minima <Output> in the vector <y>.    
        A point is considered a local maximum if it has the maximal value, and was preceded (to the left) by a value lower by <delta>.
        
        Input:
            y (arr(float))
            delta (float)
            x (arr(float))
        Output:
            maxima {'index', 'y', 'x'}
            minima {'index', 'y', 'x'}
        '''
        ## motivated by https://gist.github.com/endolith/250860 
        
        min_js, min_ys, min_xs = [], [], []
        max_js, max_ys, max_xs = [], [], []
           
        if x is None:
            x = [None]*len(y)
        y = numpy.asarray(y)
        
        if len(y) != len(x):
            sys.exit('Input vectors y and x must have same length')
        
        if not numpy.isscalar(delta):
            sys.exit('Input argument delta must be a scalar')
        
        if delta <= 0:
            sys.exit('Input argument delta must be positive')
        
        min_y, max_y = numpy.Inf, -numpy.Inf
        min_x, max_x = numpy.NaN, numpy.NaN
        
        lookformax = True
        
        for j, val in enumerate(y):
            if val > max_y:
                max_j = j
                max_y = val
                max_x = x[j]
            if val < min_y:
                min_j = j
                min_y = val
                min_x = x[j]
            
            if lookformax:
                if val < max_y-delta:
                    max_js.append(max_j)
                    max_ys.append(max_y)
                    max_xs.append(max_x)
                    min_y = val
                    min_x = x[j]
                    lookformax = False
            else:
                if val > min_y+delta:
                    min_js.append(min_j)
                    min_ys.append(min_y)
                    min_xs.append(min_x)
                    max_y = val
                    max_x = x[j]
                    lookformax = True
        
        maxima = {'index':max_js, 'y':max_ys, 'x':max_xs}
        minima = {'index':min_js, 'y':min_ys, 'x':min_xs}
        
        return maxima, minima