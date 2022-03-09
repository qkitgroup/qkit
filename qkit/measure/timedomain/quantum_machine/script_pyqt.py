import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
import numpy as np

class ImageWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)

        # Interpret image data as row-major instead of col-major
        pg.setConfigOptions(imageAxisOrder='row-major')

        pg.mkQApp()
        self.win = pg.GraphicsLayoutWidget()
        self.win.setWindowTitle('pyqtgraph example: Image Analysis')

        # A plot1 area (ViewBox + axes) for displaying the image
        #self.plot1 = self.win.addItem() # addPlot()

        self.vb = pg.ViewBox(enableMouse=True, enableMenu=True)

        # Item for displaying image data
        self.item = pg.ImageItem()
        self.vb.addItem(self.item)
        self.win.addItem(self.vb, row=0, col=1)

        #self.vb.setAspectLocked()
        #self.vb.setRange(xRange=(0, 10), yRange=(0, 10))

        # Item for x-axis
        self.win.nextRow()
        self.xaxis = MyStringAxis(orientation="bottom", linkView=self.vb)
        self.xaxis.setLabel(text="x axis", units="arb.")
        self.yaxis = pg.AxisItem(orientation="left", linkView=self.vb)
        self.yaxis.setLabel(text="y axis", units="arb.")
        self.win.addItem(self.xaxis, row=1, col=1)
        self.win.addItem(self.yaxis, row=0, col=0)


        # Custom ROI for selecting an image region
        self.ROI = pg.ROI([-8, 14], [6, 5])
        self.ROI.addScaleHandle([0.5, 1], [0.5, 0.5])
        self.ROI.addScaleHandle([0, 0.5], [0.5, 0.5])
        self.vb.addItem(self.ROI)
        self.ROI.setZValue(10)  # make sure ROI is drawn above image

        # Isocurve drawing
        self.iso = pg.IsocurveItem(level=0.8, pen='g')
        self.iso.setParentItem(self.item)
        self.iso.setZValue(5)

        # Contrast/color control
        self.hist = pg.HistogramLUTItem()
        self.hist.setImageItem(self.item)
        self.win.addItem(self.hist, row=0, col=2)

        # Draggable line for setting isocurve level
        self.isoLine = pg.InfiniteLine(angle=0, movable=True, pen='g')
        self.hist.vb.addItem(self.isoLine)
        self.hist.vb.setMouseEnabled(y=False) # makes user interaction a little easier
        self.isoLine.setValue(0.8)
        self.isoLine.setZValue(1000) # bring iso line above contrast controls

        # Another plot1 area for displaying ROI data
        self.plot2 = self.win.addPlot(row=2, col=0, colspan=2)
        self.plot2.setMaximumHeight(250)
        self.win.resize(800, 800)
        self.win.show()

        # Generate image self.data
        self.data = np.random.normal(size=(200, 100))
        self.data[20:80, 20:80] += 2.
        self.data = pg.gaussianFilter(self.data, (3, 3))
        self.data += np.random.normal(size=(200, 100)) * 0.1
        self.item.setImage(self.data)
        self.hist.setLevels(self.data.min(), self.data.max())

        # build isocurves from smoothed self.data
        self.iso.setData(pg.gaussianFilter(self.data, (2, 2)))

        # set position and scale of image
        #self.item.scale(0.2, 0.2)
        #self.item.translate(-50, 0)

        ticks = np.arange(self.data.shape[1])
        tickDictMajor = []
        for i, tick in enumerate(ticks):
            tickDictMajor.append(str(i**2))
        self.xaxis.set_tick_dict(dict(enumerate(tickDictMajor)))

        #strings = self.xaxis.tickValues()

        # zoom to fit imageo
        #self.vb.autoRange()

        self.ROI.sigRegionChanged.connect(self.updatePlot)
        self.updatePlot()

        self.isoLine.sigDragged.connect(self.updateIsocurve)

    # Callbacks for handling user interaction
    def updatePlot(self):
        selected = self.ROI.getArrayRegion(self.data, self.item)
        self.plot2.plot(selected.mean(axis=0), clear=True)

    def updateIsocurve(self):
        self.iso.setLevel(self.isoLine.value())


class MyStringAxis(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        pg.AxisItem.__init__(self, *args, **kwargs)
        self.x_values = None
        self.x_strings = None

    def set_tick_dict(self, xdict):

        self.x_values = np.asarray(list(xdict.keys())) + 0.5
        self.x_strings = np.asarray(list(xdict.values()))

    def tickStrings(self, values, scale, spacing):
        strings = []
        for v in values:
            # vs is the original tick value
            vs = v * scale
            # if we have vs in our values, show the string
            # otherwise show nothing
            if vs in self.x_values:
                # Find the string with x_values closest to vs
                vstr = self.x_strings[np.abs(self.x_values - vs).argmin()]
            else:
                vstr = ""
            strings.append(vstr)
        return strings

    def tickSpacing(self, minVal, maxVal, size, offset=0.5):
        """Return values describing the desired spacing and offset of ticks.

        This method is called whenever the axis needs to be redrawn and is a
        good method to override in subclasses that require control over tick locations.

        The return value must be a list of tuples, one for each set of ticks::

            [
                (major tick spacing, offset),
                (minor tick spacing, offset),
                (sub-minor tick spacing, offset),
                ...
            ]
        """
        # First check for override tick spacing
        if self._tickSpacing is not None:
            return self._tickSpacing

        dif = abs(maxVal - minVal)
        if dif == 0:
            return []

        ## decide optimal minor tick spacing in pixels (this is just aesthetics)
        optimalTickCount = max(2., np.log(size))

        ## optimal minor tick spacing
        optimalSpacing = dif / optimalTickCount

        ## the largest power-of-10 spacing which is smaller than optimal
        p10unit = 10 ** np.floor(np.log10(optimalSpacing))

        ## Determine major/minor tick spacings which flank the optimal spacing.
        intervals = np.array([1., 2., 10., 20., 100.]) * p10unit
        minorIndex = 0
        while intervals[minorIndex + 1] <= optimalSpacing:
            minorIndex += 1

        levels = [
            (intervals[minorIndex + 2], offset),
            (intervals[minorIndex + 1], offset),
            # (intervals[minorIndex], offset)    ## Pretty, but eats up CPU
        ]

        if self.style['maxTickLevel'] >= 2:
            ## decide whether to include the last level of ticks
            minSpacing = min(size / 20., 30.)
            maxTickCount = size / minSpacing
            if dif / intervals[minorIndex] <= maxTickCount:
                levels.append((intervals[minorIndex], offset))

        return levels


## Start Qt event loop unless running in interactive mode or using     pyside.
if __name__ == '__main__':

    app = QtGui.QApplication([])
    app.setStyle(QtGui.QStyleFactory.create("Cleanlooks"))

    image_widget = ImageWidget()

    import sys
    if (sys.flags.interactive != 1) or not hasattr(QtCore,     'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
