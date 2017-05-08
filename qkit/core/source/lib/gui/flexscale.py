import gtk
import math

class FlexScale(gtk.VBox):

    SCALE_LINEAR = 0
    SCALE_SQUARE = 1
    SCALE_SQRT = 2
    SCALE_LOG = 3

    def __init__(self, minval, maxval, scaling=None):
        gtk.VBox.__init__(self)

        self._min = minval
        self._max = maxval

        if scaling == None:
            self._scaling = self.SCALE_LINEAR
        else:
            self._scaling = scaling

        self._vscale = gtk.VScale()
        self._vscale.set_draw_value(False)
        self._vscale.set_size_request(50, 100)
        self._vscale.set_range(0, 1)

        self.pack_start(gtk.Label('%r' % minval), False, False)
        self.pack_start(self._vscale, False, False)
        self.pack_start(gtk.Label('%r' % maxval), False, False)
        self.show_all()

        self._vscale.connect('change-value', self._change_value_cb)

    def _change_value_cb(self, sender, scroll, value):
        d = self._max - self._min
        mid = (self._max + self._min) / 2
        if value < 0.5:
            sign = -1
        else:
            sign = 1
        if value < 0 or value > 1:
            return True

        if self._scaling == self.SCALE_LINEAR:
            map_val = self._min + d * value
        elif self._scaling == self.SCALE_SQUARE:
            factor = 2 * (value - 0.5) ** 2
            map_val = mid + sign * d * factor
        elif self._scaling == self.SCALE_SQRT:
            factor = math.sqrt(abs((value - 0.5))) / math.sqrt(2)
            map_val = mid + sign * d * factor

        print 'map_val: %r, sign: %r, factor: %r' % (map_val, sign, factor)
