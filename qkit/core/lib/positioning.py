# positioning.py, helper functions to use noisy / step-based positioners
# to move to an absolute position.
# Reinier Heeres <reinier@heeres.eu>, 2009
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

import misc
import time
import numpy as np
from scipy.optimize import leastsq

class LinearGenerator:

    def __init__(self, a=0, b=0.1, noise=0.75):
        '''Generate Y as a + bx + noise.'''
        self._coeff = a, b, noise

    def get(self, x):
        c = self._coeff
        return c[0] + c[1] * x + (np.random.rand() - 0.5) * c[2]

def linear(p, x):
    return p[0] + x * p[1]

def res_linear(p, y, x):
    return y - linear(p, x)

class PositionEstimator:

    def __init__(self, npoints=20):
        self._npoints = npoints
        self.reset()

    def reset(self):
        self._list = []
        self._xlist = []
        self._xindex = 0

    def add(self, val, x=None):
        if len(self._list) == self._npoints:
            self._list.pop(0)
            self._xlist.pop(0)
        if x is None:
            x = self._xindex
            self._xindex += 1
        self._list.append(val)
        self._xlist.append(x)

        llen = len(self._list)
        if llen == 1:
            return val
        elif llen == 2:
            return (3 * self._list[1] + self._list[0]) / 4.0

        p0 = [self._list[0], float(self._list[-1] - self._list[0]) / llen]
        p, ret = leastsq(res_linear, p0, args=(np.array(self._list), np.array(self._xlist)))

        return p[0] + p[1] * self._xlist[-1]

def all_true(vec):
    for v in vec:
        if not v:
            return False
    return True

class DummyPositioner:

    def __init__(self, a=0, b=0.1, noise=0.5):
        '''Generate Y as a + bx + noise.'''
        self._coeff = a, b, noise
        self._xpos = 0

    def move_steps(self, chan, n):
        self._xpos += n

    def get_position(self, chan):
        c = self._coeff
        return c[0] + c[1] * self._xpos + (np.random.rand() - 0.5) * c[2]

class AbsolutePositioner:

    def __init__(self, posins, moveins,
                    startstep=4, maxstep=16, minstep=2, use_reset=False,
                    delay=0.05, channel_ofs=0):
        """
        Absolute positioner logic for read-out/positioner combo.

        Arguments:
            posins: position reading instrument (should implement 'get_position')
            moveins: position control instrument (should implement 'move_steps')

            startstep: start steps to use
            maxstep: maximum steps
            minstep: minimum steps for fine position
            use_reset: use reset on position estimator when changing direction

            delay: time delay after each step
            channel_ofs: if channels do not start counting at zero, change this
        """

        self._posins = posins
        self._moveins = moveins

        self._startstep = startstep
        self._maxstep = maxstep
        self._minstep = minstep
        self._use_reset = use_reset
        
        self._delay = delay
        self._channel_ofs = channel_ofs

    def move_to(self, newpos):
        '''
        Arguments:
            newpos: new position vector, the length of this vector sets which
                channels will be used.
        '''

        channels = len(newpos)
        pos = [self._posins.get_position(i) for i in range(channels)]
        stepspos = [0 for i in range(channels)]
        est = []
        for i in range(channels):
            e = PositionEstimator()
            e.add(pos[i], stepspos[i])
            est.append(e)
        delta = [newpos[i] - pos[i] for i in range(channels)]
        dist = [abs(delta[i]) for i in range(channels)]
        hold = [False for i in range(channels)]
        increase_steps = True
#        print 'move_to(): start pos = %r, delta = %r, dist = %r' % \
#            (pos, delta, dist)

        steps = [-misc.sign(delta[i]) * self._startstep for i in range(channels)]

        j = 0
        while j < 1000:

            # Move
            for i in range(channels):
                if not hold[i]:
                    self._moveins.move_steps(i + self._channel_ofs, steps[i])
                    stepspos[i] += steps[i]
            time.sleep(self._delay)

            # Update position
            pos2 = [self._posins.get_position(i) for i in range(channels)]
            realpos2 = pos2[0]
            delta2 = [newpos[i] - pos2[i] for i in range(channels)]
            dist2 = [abs(delta2[i]) for i in range(channels)]
            for i in range(channels):
                pos2[i] = est[i].add(pos2[i], stepspos[i])
#            print 'move_to(): pos = %r, delta2 = %r' % (pos2, delta2)

            # Increase step size exponentially
            if increase_steps:
                for i in range(channels):
                    if not hold[i]:
                        if misc.sign(delta2[i]) != misc.sign(delta[i]):
                            hold[i] = True
                        elif abs(steps[i]) != self._maxstep:
                            steps[i] = misc.sign(delta2[i]) * min(abs(steps[i]) * 2, self._maxstep)
#                            print 'move_to(): increasing stepsize for ch%d to %f' % (i, steps[i]) 

                if all_true(hold):
#                    print 'move_to(): increase_steps=False'
                    increase_steps = False
                    for i in range(channels):
                        hold[i] = False
                        if self._use_reset:
                            est[i].reset()
                    
            # Immediately reverse if we moved too far
            if not increase_steps:
                for i in range(channels):
                    if not hold[i]:
                        if misc.sign(delta2[i]) != misc.sign(delta[i]):
                            if abs(steps[i]) == self._minstep:
                                hold[i] = True
                            else:
                                steps[i] = int(misc.sign(delta2[i]) * max(round(abs(steps[i]) / 2), self._minstep))
                                if self._use_reset:
                                    est[i].reset()
#                                print 'move_to(): reversing and decreasing stepsize for ch%d to %f' % (i, steps[i])

                if all_true(hold):
#                    print 'move_to(): Moved to position!'
                    return realpos2

                # Remember relative position
                delta = delta2

            j += 1

def test_estimator():
    gen = LinearGenerator()
    est = PositionEstimator()
    xs, ys, yes, yerr = [], [], [], []
    for i in range(50):
        x = 0.2*i**2 + i
        genpos = gen.get(i)
        estpos = est.add(genpos, x=x)
        xs += [x]
        ys += [genpos]
        yes += [estpos]
        yerr += [i * 0.1 - estpos]
        print 'X: %f, generated: %f, estimated: %f' % (x, genpos, estpos)

    import matplotlib.pyplot as plt
    plt.plot(xs, ys, 'o')
    plt.plot(xs, yes, '--')
    plt.plot(xs, yerr, 's')
    plt.show()

def test_positioner():
    dummy = DummyPositioner()
    pos = AbsolutePositioner(dummy, dummy, delay=0)
    deltas = []
    for i in range(1000):
        newpos = pos.move_to([10.2])
        deltas.append(abs(10.2 - newpos))
        newpos = pos.move_to([3.4])
        deltas.append(abs(3.4 - newpos))
    deltas = np.array(deltas)
    print 'Deltas: avg=%f, std=%f' % (np.average(deltas), np.std(deltas))

if __name__ == '__main__':
    test_positioner()
    test_estimator()

