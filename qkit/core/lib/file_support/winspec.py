# winspec.py, class for reading/writing winspec SPE files
# Reinier Heeres <reinier@heeres.eu>
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
from lib.namedstruct import *

class SPEFile:

    HDRNAMEMAX = 120
    USERINFOMAX = 1000
    COMMENTMAX = 80
    LABELMAX = 16
    FILEVERMAX = 16
    DATEMAX = 10
    ROIMAX = 10
    TIMEMAX = 7

    DTYPE_FLOAT = 0
    DTYPE_LONG = 1
    DTYPE_SHORT = 2
    DTYPE_USHORT = 3
    DSIZE = {
        DTYPE_FLOAT: (4, 'f', np.float32),
        DTYPE_LONG: (4, 'l', np.int32),
        DTYPE_SHORT: (2, 'h', np.int16),
        DTYPE_USHORT: (2, 'H', np.uint16)
    }

    _STRUCTINFO = [
        ('ControllerVersion', S16, 1), #0, Hardware Version
        ('LogicOutput', S16, 1), #2, Definition of Output BNC
        ('AmpHiCapLowNoise', U16, 1), #4, Amp Switching Mode
        ('xDimDet', U16, 1), #6, Detector x dimension of chip.
        ('mode', S16, 1), #8, timing mode
        ('exp_sec', FLOAT, 1), #10, alternitive exposure, in sec.
        ('VChipXdim', S16, 1), #14, Virtual Chip X dim
        ('VChipYdim', S16, 1), #16, Virtual Chip Y dim
        ('yDimDet', U16, 1), #18, y dimension of CCD or detector.
        ('date', STRING, DATEMAX), #20, date
        ('VirtualChipFlag', S16, 1), #30, On/Off
        ('Spare1', C, 2), #32
        ('noscan', S16, 1), #34, Old number of scans - should always be -1
        ('DetTemperature', FLOAT, 1), #36, Detector Temperature Set
        ('DetType', S16, 1), #40, CCD/DiodeArray type
        ('xdim', U16, 1), #42, actual # of pixels on x axis
        ('stdiode', S16, 1), #44, trigger diode
        ('DelayTime', FLOAT, 1), #46, Used with Async Mode
        ('ShutterControl', U16, 1), #50, Normal, Disabled Open, Disabled Closed
        ('AbsorbLive', S16, 1), #52, On/Off
        ('AbsorbMode', U16, 1), #54, Reference Strip or File
        ('CanDoVirtualChipFlag', S16, 1), #56, T/F Cont/Chip able to do Virtual Chip
        ('ThresholdMinLive', S16, 1), #58, On/Off
        ('ThresholdMinVal', FLOAT, 1), #60, Threshold Minimum Value
        ('ThresholdMaxLive', S16, 1), #64, On/Off
        ('ThresholdMaxVal', FLOAT, 1), #66, Threshold Maximum Value
        ('SpecAutoSpectroMode', S16, 1), #70, T/F Spectrograph Used
        ('SpecCenterWlNm', FLOAT, 1), #72, Center Wavelength in Nm
        ('SpecGlueFlag', S16, 1), #76, T/F File is Glued
        ('SpecGlueStartWlNm', FLOAT, 1), #78, Starting Wavelength in Nm
        ('SpecGlueEndWlNm', FLOAT, 1), #82, Starting Wavelength in Nm
        ('SpecGlueMinOvrlpNm', FLOAT, 1), #86, Minimum Overlap in Nm
        ('SpecGlueFinalResNm', FLOAT, 1), #90, Final Resolution in Nm
        ('PulserType', S16, 1), #94, 0=None, PG200=1, PTG=2, DG535=3
        ('CustomChipFlag', S16, 1), #96, T/F Custom Chip Used
        ('XPrePixels', S16, 1), #98, Pre Pixels in X direction
        ('XPostPixels', S16, 1), #100, Post Pixels in X direction
        ('YPrePixels', S16, 1), #102, Pre Pixels in Y direction
        ('YPostPixels', S16, 1), #104, Post Pixels in Y direction
        ('asynen', S16, 1), #106, asynchron enable flag  0 = off
        ('datatype', S16, 1), #108, experiment datatype
        ('PulserMode', S16, 1), #110, Repetitive/Sequential
        ('PulserOnChipAccums', U16, 1), #112, Num PTG On-Chip Accums
        ('PulserRepeatExp', U32, 1), #114, Num Exp Repeats (Pulser SW Accum)
        ('PulseRepWidth', FLOAT, 1), #118, Width Value for Repetitive pulse (usec)
        ('PulseRepDelay', FLOAT, 1), #122, Width Value for Repetitive pulse (usec)
        ('PulseSeqStartWidth', FLOAT, 1), #126, Start Width for Sequential pulse (usec)
        ('PulseSeqEndWidth', FLOAT, 1), #130, End Width for Sequential pulse (usec)
        ('PulseSeqStartDelay', FLOAT, 1), #134, Start Delay for Sequential pulse (usec)
        ('PulseSeqEndDelay', FLOAT, 1), #138, End Delay for Sequential pulse (usec)
        ('PulseSeqIncMode', S16, 1), #142, Increments: 1=Fixed, 2=Exponential
        ('PImaxUsed', S16, 1), #144, PI-Max type controller flag
        ('PImaxMode', S16, 1), #146, PI-Max mode
        ('PImaxGain', S16, 1), #148, PI-Max Gain
        ('BackGrndApplied', S16, 1), #150, 1 if background subtraction done
        ('PImax2nsBrdUsed', S16, 1), #152, T/F PI-Max 2ns Board Used
        ('minblk', U16, 1), #154, min. # of strips per skips
        ('numminblk', U16, 1), #156, # of min-blocks before geo skps
        ('SpecMirrorLocation', S16, 2), #158, Spectro Mirror Location, 0=Not Present
        ('SpecSlitLocation', S16, 4), #162, Spectro Slit Location, 0=Not Present
        ('CustomTimingFlag', S16, 1), #170, T/F Custom Timing Used
        ('ExperimentTimeLocal', STRING, TIMEMAX), #172, Experiment Local Time as hhmmss\0
        ('ExperimentTimeUTC', STRING, TIMEMAX), #179, Experiment UTC Time as hhmmss\0
        ('ExposUnits', S16, 1), #186, User Units for Exposure
        ('ADCoffset', U16, 1), #188, ADC offset
        ('ADCrate', U16, 1), #190, ADC rate
        ('ADCtype', U16, 1), #192, ADC type
        ('ADCresolution', U16, 1), #194, ADC resolution
        ('ADCbitAdjust', U16, 1), #196, ADC bit adjust
        ('gain', U16, 1), #198, gain
        ('Comments', C, 400), #200, File Comments
        ('geometric', U16, 1), #600, geometric ops: rotate 0x01,
        ('xlabel', STRING, LABELMAX), #602, intensity display string
        ('cleans', U16, 1), #618, cleans
        ('NumSkpPerCln', U16, 1), #620, number of skips per clean.
        ('SpecMirrorPos', S16, 2), #622, Spectrograph Mirror Positions
        ('SpecSlitPos', FLOAT, 4), #626, Spectrograph Slit Positions
        ('AutoCleansActive', S16, 1), #642, T/F
        ('UseContCleansInst', S16, 1), #644, T/F
        ('AbsorbStripNum', S16, 1), #646, Absorbance Strip Number
        ('SpecSlitPosUnits', S16, 1), #648, Spectrograph Slit Position Units
        ('SpecGrooves', FLOAT, 1), #650, Spectrograph Grating Grooves
        ('srccmp', S16, 1), #654, number of source comp. diodes
        ('ydim', U16, 1), #656, y dimension of raw data.
        ('scramble', S16, 1), #658, 0=scrambled,1=unscrambled
        ('ContinuousCleansFlag', S16, 1), #660, T/F Continuous Cleans Timing Option
        ('ExternalTriggerFlag', S16, 1), #662, T/F External Trigger Timing Option
        ('lnoscan', U32, 1), #664 Number of scans (Early WinX)
        ('lavgexp', U32, 1), #668 Number of Accumulations
        ('ReadoutTime', FLOAT, 1), #672, Experiment readout time
        ('TriggeredModeFlag', S16, 1), #676, T/F Triggered Timing Option
        ('Spare_2', C, 10), #678
        ('sw_version', STRING, FILEVERMAX), #688, Version of SW creating this file
        ('type', S16, 1), #704, 1 = new120 (Type II)
        ('flatFieldApplied', S16, 1), #706, 1 if flat field was applied.
        ('Spare_3', C, 16), #708,
        ('kin_trig_mode', S16, 1), #724, Kinetics Trigger Mode
        ('dlabel', STRING, LABELMAX), #726, Data label.
        ('Spare_4', C, 436), #742
        ('PulseFileName', STRING, HDRNAMEMAX), #1178, Name of Pulser File with
        ('AbsorbFileName', STRING, HDRNAMEMAX), #1298, Name of Absorbance File (if File Mode)
        ('NumExpRepeats', U32, 1), #1418, Number of Times experiment repeated
        ('NumExpAccums', U32, 1), #1422, Number of Time experiment accumulated
        ('YT_Flag', S16, 1), #1426, Set to 1 if this file contains YT data
        ('clkspd_us', FLOAT, 1), #1428, Vert Clock Speed in micro-sec
        ('HWaccumFlag', S16, 1), #1432, set to 1 if accum done by Hardware.
        ('StoreSync', S16, 1), #1434, set to 1 if store sync used
        ('BlemishApplied', S16, 1), #1436, set to 1 if blemish removal applied
        ('CosmicApplied', S16, 1), #1438, set to 1 if cosmic ray removal applied
        ('CosmicType', S16, 1), #1440, if cosmic ray applied, this is type
        ('CosmicThreshold', FLOAT, 1), #1442, Threshold of cosmic ray removal.
        ('NumFrames', U32, 1), #1446  number of frames in file.
        ('MaxIntensity', FLOAT, 1), #1450, max intensity of data (future)
        ('MinIntensity', FLOAT, 1), #1454, min intensity of data (future)
        ('ylabel', STRING, LABELMAX), #1458, y axis label.
        ('ShutterType', U16, 1), #1474, shutter type.
        ('shutterComp', FLOAT, 1), #1476, shutter compensation time.
        ('readoutMode', U16, 1), #1480, readout mode, full,kinetics, etc
        ('WindowSize', U16, 1), #1482, window size for kinetics only.
        ('clkspd', U16, 1), #1484, clock speed for kinetics & frame transfer
        ('interface_type', U16, 1), #1486, computer interface
        ('NumROIsInExperiment', S16, 1), #1488, May be more than the 10 allowed in
        ('Spare_5', C, 16), #1490,
        ('controllerNum', U16, 1), #1506, if multiple controller system will
        ('SWmade', U16, 1), #1508, Which software package created this file
        ('NumROI', S16, 1), #1510, number of ROIs used. if 0 assume 1.

        ('roi_info', U16, 10 * 6),

        ('FlatField', STRING, HDRNAMEMAX), #1632, Flat field file name.
        ('background', STRING, HDRNAMEMAX), #1752, background sub. file name.
        ('blemish', STRING, HDRNAMEMAX), #1872, blemish file name.
        ('file_header_ver', FLOAT, 1), #1992, version of this file header
        ('YT_info', C, 1000),
        ('WinView_id', U32, 1),

        ('xoffset', DOUBLE, 1), #3000, offset for absolute data scaling
        ('xfactor', DOUBLE, 1), #3008, factor for absolute data scaling
        ('xcurrent_unit', C, 1), #3016, selected scaling unit
        ('xreserved1', C, 1), #3017, reserved
        ('xstring', C, 40), #3018, special string for scaling
        ('xreserved2', C, 40), #3058, reserved
        ('xcalib_valid', U8, 1), #3098, flag if calibration is valid
        ('xinput_unit', U8, 1), #3099, current input units for
        ('xpolynom_unit', U8, 1), #3100, linear UNIT and used
        ('xpolynom_order', U8, 1), #3101, ORDER of calibration POLYNOM
        ('xcalib_count', U8, 1), #3102, valid calibration data pairs
        ('xpixel_position', DOUBLE, 10), #3103, pixel pos. of calibration data
        ('xcalib_value', DOUBLE, 10), #3183, calibration VALUE at above pos
        ('xpolynom_coeff', DOUBLE, 6), #3263, polynom COEFFICIENTS
        ('xlaser_position', DOUBLE, 1), #3311, laser wavenumber for relativ WN
        ('xreserved3', C, 1), #3319, reserved
        ('xnew_calib_flag', C, 1), #3320
        ('xcalib_label', C, 81), #3321, Calibration label (NULL term'd)
        ('xexpansion', C, 87), #3402, Calibration Expansion area

        ('yoffset', DOUBLE, 1), #3489, offset for absolute data scaling
        ('yfactor', DOUBLE, 1), #3497, factor for absolute data scaling
        ('ycurrent_unit', C, 1), #3505, selected scaling unit
        ('yreserved1', C, 1), #3506, reserved
        ('ystring', C, 40), #3507, special string for scaling
        ('yreserved2', C, 40), #3547, reserved
        ('ycalib_valid', U8, 1), #3587, flag if calibration is valid
        ('yinput_unit', U8, 1), #3588, current input units for
        ('ypolynom_unit', U8, 1), #3589, linear UNIT and used
        ('ypolynom_order', U8, 1), #3590, ORDER of calibration POLYNOM
        ('ycalib_count', U8, 1), #3591, valid calibration data pairs
        ('ypixel_position', DOUBLE, 10), #3592, pixel pos. of calibration data
        ('ycalib_value', DOUBLE, 10), #3672, calibration VALUE at above pos
        ('ypolynom_coeff', DOUBLE, 6), #3752, polynom COEFFICIENTS
        ('ylaser_position', DOUBLE, 1), #3800, laser wavenumber for relativ WN
        ('yreserved3', C, 1), #3808, reserved
        ('ynew_calib_flag', C, 1), #3809
        ('ycalib_label', C, 81), #3810, Calibration label (NULL term'd)
        ('yexpansion', C, 87), #3891, Calibration Expansion area

        ('Istring', STRING, 40), #3978, special intensity scaling string
        ('Spare_6', C, 25), #4018,
        ('SpecType', U8, 1), # 4043  spectrometer type (acton, spex, etc.)
        ('SpecModel', U8, 1), # 4044  spectrometer model (type dependent)
        ('PulseBurstUsed', U8, 1), # 4045  pulser burst mode on/off
        ('PulseBurstCount', U32, 1), #4046, pulser triggers per burst
        ('PulseBurstPeriod', DOUBLE, 1), #4050, pulser burst period (in usec)
        ('PulseBracketUsed', U8, 1), # 4058  pulser bracket pulsing on/off
        ('PulseBracketType', U8, 1), # 4059  pulser bracket pulsing type
        ('PulseTimeConstFast', DOUBLE, 1), #4060, pulser slow exponential time constant (in usec)
        ('PulseAmplitudeFast', DOUBLE, 1), #4068, pulser fast exponential amplitude constant
        ('PulseTimeConstSlow', DOUBLE, 1), #4076, pulser slow exponential time constant (in usec)
        ('PulseAmplitudeSlow', DOUBLE, 1), #4084, pulser slow exponential amplitude constant
        ('AnalogGain;', S16, 1), #4092, analog gain
        ('AvGainUsed', S16, 1), #4094, avalanche gain was used
        ('AvGain', S16, 1), #4096, avalanche gain value
        ('lastvalue', S16, 1), #4098, Always the LAST value in the header
    ]

    def __init__(self, filename=None):
        self._info = {}
        self._filename = ''
        self._data = None

        # Little-endian
        self._struct = NamedStruct(self._STRUCTINFO, alignment='<')

        if filename:
            self.load(filename)

    def load(self, filename):
        f = open(filename, 'rb')
        header = f.read(4100)
        info = self._struct.unpack(header)
        self._info = info

        typesize, formatchr, nptype = self.DSIZE[info['datatype']]
        formatstr = '%s%s' % (formatchr, formatchr)
        entries = info['xdim'] * info['ydim'] * info['NumFrames']
        self._data = np.zeros(entries, dtype=nptype)
        for i in range(entries):
            elem = f.read(typesize)
            if elem == '':
                print 'Error reading SPE-file: unexpected EOF'
                break
            self._data[i] = struct.unpack(formatchr, elem)[0]

    def convert_value(self, axis, value):
        if not self._info['%scalib_valid' % axis]:
            return value

        val = 0.0
        order = self._info['%spolynom_order' % axis]
        for power in range(order + 1):
            coef = self._info['%spolynom_coeff' % axis][power]
            val += coef * (value + 1) ** power

        return val

    def get_info(self):
        return self._info

    def get_data(self):
        xvals = np.array(
                [self.convert_value('x', i) for i in range(len(self._data))])
        yvals = np.array(
                [self.convert_value('y', i) for i in self._data])
        return np.column_stack((xvals, yvals))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        fname = sys.argv[1]
    else:
        fname = 'test.spe'
    spe = SPEFile(fname)
    info = spe.get_info()
    print 'Info:'
    for line in spe._STRUCTINFO:
        key = line[0]
        val = info[key]
        print '  %s => %r' % (key, val)

    import matplotlib.pyplot as plt
    xys = spe.get_data()
    xs, ys = xys[:,0], xys[:,1]
    plt.plot(xs, ys)
    plt.xlim(min(xs), max(xs))
    plt.show()

