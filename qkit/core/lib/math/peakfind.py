# peakfind.py, functions for finding peaks
# Reinier Heeres <reinier@heeres.eu>, 2011
#
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
import fit

FIT_LORENTZIAN = 1
FIT_GAUSSIAN = 2

class PeakFinderBase:

    def __init__(self, data1, data2=None, **kwargs):
        if data2 is None:
            self._ydata = data1
            self._xdata = np.arange(0, len(self._ydata))
        else:
            self._xdata = data1
            self._ydata = data2

        self._maxpeaks = kwargs.get('maxpeaks', 20)

class PeakFinder(PeakFinderBase):

    def __init__(self, *args, **kwargs):
        '''
        Keyword arguments:
        - fit: fitting function, FIT_LORENTZIAN or FIT_GAUSSIAN
        - fitwidth: number of data points around maximum to use for fit
        - threshold: the threshold for detecting a peak (# of standard dev.)
        '''

        self._fit = kwargs.get('fit', FIT_LORENTZIAN)
        self._fitwidth = kwargs.get('fitwidth', 30)
        self._threshold = kwargs.get('threshold', 3)
        PeakFinderBase.__init__(self, *args, **kwargs)

    def _fit_bg(self, order):
        f = fit.Polynomial(self._xdata, self._ydata, order=order)
        p0 = [0.1/(i+1) for i in range(order+1)]
        p0[0] = np.average(self._ydata)
        p = f.fit(p0)
        return f.func(p)

    def find(self, sign=1, bgorder=0):
        '''
        Return a list of (position, height, width) tuples for all peaks that
        are located.

        sign should be 1 to find peaks, -1 to find valleys
        '''

        if bgorder > 0:
            bg = self._fit_bg(bgorder)
            self._ydata -= bg

        i = 0
        peaks = []
        while i < self._maxpeaks:
            avg = np.average(self._ydata)
            std = np.std(self._ydata)

            if sign > 0:
                maxloc = np.argmax(self._ydata)
                maxval = self._ydata[maxloc]
                if maxval < avg + self._threshold * std:
                    break
            else:
                maxloc = np.argmin(self._ydata)
                maxval = self._ydata[maxloc]
                if maxval > avg - self._threshold * std:
                    break

            mini = max(0, maxloc - self._fitwidth / 2)
            maxi = min(len(self._xdata) - 1, maxloc + self._fitwidth / 2)
            dx = abs((self._xdata[maxi] - self._xdata[mini]) / (maxi - mini))

            if self._fit == FIT_LORENTZIAN:
                f = fit.Lorentzian(self._xdata[mini:maxi], self._ydata[mini:maxi])
            elif self._fit == FIT_GAUSSIAN:
                f = fit.Gaussian(self._xdata[mini:maxi], self._ydata[mini:maxi])
            else:
                print 'Unknown fit requested'
                return

            p = f.fit([avg, sign*3*std, self._xdata[maxloc], 3 * dx])
            pos = p[2]
            w = f.get_fwhm()
            if sign * p[1] < 0:
                print 'Peak of wrong sign found'
            h = f.get_height() + sign * p[0]   # Height including background
            peaks.append([pos, h, w])

            import matplotlib.pyplot as plt
            plt.plot(self._xdata, self._ydata + 2 * i)
            plt.plot(f._xdata, f.func(p) + 2 * i)

            w = max(w, dx * 1.1)    # At least dx wide
            mask = ((self._xdata > (p[2] - w)) & (self._xdata < (p[2] + w)))
            self._ydata[mask] = avg - sign * std

            i += 1

        return peaks

if __name__ == "__main__":
    maxx = 20
    xdata = np.arange(0, maxx, 0.1)
    for sign in (1, -1):
        ydata = np.random.random([len(xdata)])
        ydata += -0.05 * (xdata - maxx * np.random.rand())**2
        for i in range(3):
            xpos = maxx * np.random.random()
            print 'Putting peak at %r' % (xpos, )
            ydata += sign * 5 * np.exp(-(xdata - xpos)**2 / 0.5**2)

        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(xdata, ydata)

        p = PeakFinder(xdata, ydata, maxpeaks=3)
        peaks = p.find(sign=sign, bgorder=2)
        print 'Peaks at: %r' % (peaks, )

