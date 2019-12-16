import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate as si

class CurveXtractor():
    """
    Class for graphical curve extraction.
    Use the mouse to find points in your data.
    Use the keyboard to generate a spline following your points.
    Finally, extract a curve from the data, which is in the vicinity of the spline.
    Note, use of the module requires the widget backend for matplotlib.
    
    Attributes:
    
    set_data: set x-, y- and zdata from which curves will be extracted.
    set_smoothness: set smoothness of the splines used to approximate the curves in the data.
    set_points: manually add points and curves you want to extract from the data.
    extract_points: extract curves from the data, which are follow the splines.
    plot_results: plot extracted points.
    
    """
    def __init__(self, xdata = [0], ydata = [0], zdata = [0], smoothness = 0.1):
        """
        Inits CurveXtractor with xdata, ydata, zdata and smoothness of the splines.
        
        Args:
            xdata:      xaxis data
            ydata:      yaxis data
            zdata:      2d matix of zdata
            smoothness: smoothness of the spline (can also be changed later on in the procedure).
        """
        if plt.get_backend().find("nbagg") == -1:
            print("Module requires using the widget backend for matplotlib.\nActivate with %matplotlib widget.")
            return
        self.xvals = 0 
        self.yvals = 0 
        self.zvals = 0
        self._smoothness = smoothness
        
        self._status = True
        self._infotxt = 0
        
        self._points_x = []
        self._points_y = []
        self._curve_x = []
        self._curve_y = []
        self._x_results = []
        self._y_results = []
        
        self._col = ["w", "C1", "C3", "C6", "C8"]
        self._pointplots = [[]]
        self._curveplots = []
        self._result_plots = []
        self._xlim = (min(xdata), max(xdata))
        self._ylim = (min(ydata), max(ydata))
        
        self._splines = []


    def set_data(self, xdata, ydata, zdata):
        """
        Adds x-, y- and zdata.
        
        Args:
            xdata: xaxis data
            ydata: yaxis data
            zdata: 2d matix of zdata
        """
        self.xvals = xdata
        self.yvals = ydata
        self.zvals = zdata
        self._xlim = (min(xdata), max(xdata))
        self._ylim = (min(ydata), max(ydata))
        return True


    def set_smoothness(self, smoothness):
        """
        Set smoothness of the splines.
        
        Args:
            smoothness: Smoothness parameter. Small smoothness forces the spline closer to the points used to generate it.
                        Higher smoothness allows the spline to deviate more strongly from the given curve.
        
        """
        self._smoothness = smoothness
        return True


    def _click_event(self, event):
        """
        button_press_event:
            left_mouse:  add a point (mouse position) to the current curve.
            right_mouse: unify previously added points to a new curve and initialize a new curve.
        """
        if self._infotxt != 0:
            self._removeinfo()
            return True
        if self._status:
            if event.button == 1:
                # add point to plot on left mouse click
                if (event.xdata < self._xlim[-1]) and (event.xdata > self._xlim[0]) and (event.ydata < self._ylim[-1]) and (event.ydata > self._ylim[0]):
                    self._addpoint(event.xdata, event.ydata)
            elif (event.button == 3) and (len(self._points_x) > 1):
                # group current points as new curve on right mouse click
                self._addcurve()
        return


    def _key_event(self, event):
        """
        key_press_event:
            enter:  generate splines from previously added points. Or revert to point adding mode.
            delete: remove latest point or curve from data and plot.
        """
        if self._infotxt != 0:
            self._removeinfo()
            return True
        if (event.key == "delete") and self._status:
            self._del_last()
        elif event.key == "enter":
            if len(self._curveplots) > 0:
                for plot in self._curveplots:
                    plot.pop(0).remove()
                self._curveplots = []
                self._splines = []
                if self._status:
                    self._generate_splines()
                else:
                    for i in range(0, len(self._curve_x)):
                        temp_plot = plt.plot(np.array(self._curve_x[i])[np.argsort(self._curve_x[i])],
                                             np.array(self._curve_y[i])[np.argsort(self._curve_x[i])],
                                             self._col[i % len(self._col)] + ".--")
                        self._curveplots.append(temp_plot)
                plt.xlim(self._xlim)
                plt.ylim(self._ylim)
                self._status = not self._status
        return


    def set_points(self, show_info = True):
        """
        This routine starts the graphical interface for adding points.
        
        Use left mouse button to add points to the current curve.
        Use right mouse button to add another curve.
        Press delete (entf) to remove the last point.
        
        Once you are finished press enter to calculate splines following your curves.
        If you are satisfied with the result, continue with extract_points.
        In case you want to change something, press enter to return to the editing mode.
        
        Args:
            show_info: show the information of the doc string in the plot.
        """
        self._fig = plt.figure(figsize = (9, 6))
        plt.pcolormesh(self.xvals, self.yvals, self.zvals)
        info = ("""Use left mouse button to add points to the current curve.\nUse right mouse button to add another curve.\nPress delete (entf) to remove the last point.\n
        
        Once you are finished press enter to calculate splines following your curves.
        If you are satisfied with the result, continue with extract_points.
        In case you want to change something, press enter to return to the editing mode.""")

        self._cid = self._fig.canvas.mpl_connect("button_press_event", self._click_event)
        self._cid = self._fig.canvas.mpl_connect("key_press_event", self._key_event)
        if show_info:
            self._showinfo(info)
        return True


    def _addpoint(self, x, y):
        """
        Add point (x,y) to plot and (points_x, points_y).
        
        Args:
            x: x coord of the point.
            y: y coord of the point.
        """
        temp_plot = plt.plot([x], [y], self._col[len(self._curve_x)%len(self._col)] + ".")
        self._pointplots[-1].append(temp_plot)
        self._points_x.append(x)
        self._points_y.append(y)
        return True


    def _del_last(self):
        """
        Remove last point or curve from plot and data.
        """
        if (len(self._pointplots[-1]) == 0) and (len(self._pointplots) > 1):
            del self._pointplots[-1]
        if len(self._points_x) > 0:
            self._pointplots[-1][-1].pop(0).remove()
            del self._pointplots[-1][-1]
            self._points_x = self._points_x[:-1]
            self._points_y = self._points_y[:-1]
        elif len(self._curve_x) > 0:
            self._points_x = self._curve_x[-1]
            self._points_y = self._curve_y[-1]
            self._curve_x = self._curve_x[:-1]
            self._curve_y = self._curve_y[:-1]
            self._curveplots[-1].pop(0).remove()
            self._curveplots = self._curveplots[:-1]
        return True


    def _addcurve(self):
        """
        Unify previously added points to a curve.
        Start a new curve.
        """
        temp_plot = plt.plot(np.array(self._points_x)[np.argsort(self._points_x)],
                             np.array(self._points_y)[np.argsort(self._points_x)],
                             self._col[len(self._curve_x)%len(self._col)] + ".--")
        self._curveplots.append(temp_plot)
        self._curve_x.append(self._points_x)
        self._curve_y.append(self._points_y)
        self._pointplots.append([])
        self._points_x = []
        self._points_y = []
        return True


    def _generate_splines(self):
        """
        For each curve, calculate a function (spline), following the points which were added to the curve.
        If there are only 3 points given, a parabola is calculated.
        For 2 points, a straight line is used.
        """
        warning = ""
        for i in range(0, len(self._curve_x)):
            if len(self._curve_x[i]) == 3:
                # if only 3 points are given, calculate exact parabola
                warning += "In curve " + str(i) + ", only 3 points are given.\n" + "A parabola is used instead of a spline.\n\n"
                g = (self._curve_y[i][0] - self._curve_y[i][1])/(self._curve_y[i][2] - self._curve_y[i][1])
                x0 = 0.5 * ((self._curve_x[i][0]**2 - self._curve_x[i][1]**2 * (1 - g) - g*self._curve_x[i][2]**2)/
                            (self._curve_x[i][0] - self._curve_x[i][1] - g*(self._curve_x[i][2] - self._curve_x[i][1])))
                m = (self._curve_y[i][1] - self._curve_y[i][0])/((self._curve_x[i][1] - x0)**2 - (self._curve_x[i][0] - x0)**2)
                c = self._curve_y[i][0] - m*(self._curve_x[i][0] - x0)**2
                fct = lambda x: m * (x - x0)**2 + c
            elif len(self._curve_x[i]) == 2:
                # if only 2 points are given, a straight line is used
                warning += "In curve " + str(i) + ", only 2 points are given.\n" + "A straight line is used instead of a spline.\n\n"
                m = (self._curve_y[i][1] - self._curve_y[i][0])/(self._curve_x[i][1] - self._curve_x[i][0])
                c = self._curve_y[i][1] - m * self._curve_x[i][1]
                fct = lambda x: m * x + c
            else:
                # if there are more than 3 points given, an acutual spline is calculated.
                try:
                    fct = si.UnivariateSpline(np.array(self._curve_x[i])[np.argsort(self._curve_x[i])],
                                              np.array(self._curve_y[i])[np.argsort(self._curve_x[i])],
                                              s = self._smoothness)
                except ValueError:
                    warning += "Points in curve " + str(i) + " too dense.\n" + "Removing every 2nd point.\n\n"
                    for plot in self._pointplots[-len(self._curve_x[i]):][::2]:
                        plot.pop(0).remove()
                    self._pointplots = self._pointplots[::2]
                    self._curve_x[i] = self._curve_x[i][::2]
                    self._curve_y[i] = self._curve_y[i][::2]
                    try:
                        fct = si.UnivariateSpline(np.array(self._curve_x[i])[np.argsort(self._curve_x[i])],
                                                  np.array(self._curve_y[i])[np.argsort(self._curve_x[i])],
                                                  s = self._smoothness)
                    except:
                        warning += "Although points were removed from curve " + str(i) + " a spline could not be calculated.\n"
                        warning += "Please try again later.\n\n"
                        fct = lambda x: x * 0
            
            self._splines.append(fct)
            temp_plot = plt.plot(self.xvals, fct(self.xvals), self._col[i % len(self._col)] + "--")
            self._curveplots.append(temp_plot)
        if len(warning) > 0:
            self._showinfo(warning[:-2])
        return True


    def _showinfo(self, string):
        """
        Show a given string as text in the plot.
        
        Args:
            string: text to be shown in the plot.
        """
        self._infotxt = plt.text(np.mean(self._xlim), np.mean(self._ylim), string,
                                 horizontalalignment = "center", verticalalignment = "center",
                                 bbox=dict(boxstyle="square", ec=(1,0,0), fc=(1,1,1)))
        return True


    def _removeinfo(self):
        """
        Remove a text previously (added with _showinfo) from the plot.
        """
        self._infotxt.remove()
        self._infotxt = 0
        return True
    
    
    def find_along_splines(self, width = 0, peak = False):
        """
        Search the extremum along the spline functions, in a certain width.

        Args:
            width: Width (in units of y-axis) around which points are considered for the search.
                This can also be an array, each element corresponding to one curve.
                The default value for width is 5% of the y-range.
            peak:  If True/False, the maximum/minimum in the specified region is returned.
        """
        fct_num = len(self._splines)
        self._x_results = [[] for i in range(fct_num)]
        self._y_results = [[] for i in range(fct_num)]

        if width == 0:
            width = 0.05 * (np.amax(self.yvals) -np.amin(self.yvals))

        for i, x in enumerate(self.xvals):
            for j, fct in enumerate(self._splines):
                val = fct(x)
                ind_min = np.argmin(np.abs(self.yvals - (val - width/2.)))
                ind_max = np.argmin(np.abs(self.yvals - (val + width/2.)))
                temp_data = self.zvals[ind_min:ind_max, i]
                if len(temp_data) > 0:    
                    if peak:
                        y = self.yvals[ind_min + np.argmax(temp_data)]
                    else:
                        y = self.yvals[ind_min + np.argmin(temp_data)]
                    self._x_results[j].append(x)
                    self._y_results[j].append(y)
        return True


    def plot_results(self):
        """
        Plot results from find_along_splines.
        """
        for plot in self._result_plots:
            plot.pop(0).remove()
        self._result_plots = []
        if (len(self._x_results) > 0):
            for i in range(len(self._x_results)):
                temp_plot = plt.plot(self._x_results[i], self._y_results[i], self._col[i % len(self._col)])
                self._result_plots.append(temp_plot)
        return True


    def get_results(self):
        """
        Get results from find_along_splines.

        Returns:
            x_results: list of arrays containing x values (1 for each spline).
            y_results: list of arrays containing y values (1 for each spline).
        """
        return self._x_results, self._y_results