# Zurich Instruments UHFQA driver by Andras Di Giovanni
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
from zhinst.toolkit import Session
import time
from time import sleep
import qkit
from qkit.core.instrument_base import Instrument
import time
import numpy as np
from qkit.drivers.visa_prologix import instrument
import zhinst.ziPython as zi
import zhinst.utils as utils
from zhinst.toolkit import Session
server_host = '127.0.0.1'
server_port = 8004
apilevel_example=6

daq = zi.ziDAQServer(host=server_host, port=server_port, api_level=6)
print("Connected to ziDAQ server.")
daq.sync()
device_interface = '1gbe'
daq.connectDevice("dev2772", device_interface)

print('UHFQA ready to use in 1 second.')

class zi_uhfqa(Instrument):
    """
    This is the python driver for the SHFSG, more commonly called SHF

    Initialise with shfsg = qkit.instruments.create("zi_uhfqa", "zi_uhfqa")
    """

    def __init__(self, name, **kwargs):



        Instrument.__init__(self, name,  tags=['physical'])



        # QA Setup parameters
        self.add_function('get_result')
        self.add_parameter('mixermatrix00', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('mixermatrix01', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('mixermatrix10', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('mixermatrix11', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('integrationlength', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('integrationtrigger', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('delay', type=float, flags=Instrument.FLAG_GETSET)

        self.add_parameter('threshold1', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold2', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold3', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold4', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold5', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold6', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold7', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold8', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold9', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('threshold10', type=float, flags=Instrument.FLAG_GETSET)

        #QA Result Logger
        self.add_parameter('resultsource', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('resultlength', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('resultaverages', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('resultreset', type=int, flags = Instrument.FLAG_SET)

        #QA Awg
        self.add_parameter('rerun', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('samplingrate', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('amplitude1', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('amplitude2', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('mode1', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('mode2', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('anatrig1signal', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('anatrig1slope', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('anatrig1level', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('anatrig1hysteresis', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('digtrig1signal', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('digtrig1slope', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('memoryusage', type=float, flags=Instrument.FLAG_GET)


        #QA InOut
        self.add_parameter('sigIn1range', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigIn2range', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigIn1scaling', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigIn2scaling', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut1on', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut2on', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut1range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut2range', type=int, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut1offset', type=float, flags=Instrument.FLAG_GETSET)
        self.add_parameter('sigOut2offset', type=float, flags=Instrument.FLAG_GETSET)


#QA setup and calibration
    def calibrate(self):
        daq.setInt('/dev2772/system/calib/calibrate', 1)
    def do_get_mixermatrix00(self):
        return daq.getDouble('/dev2772/qas/0/deskew/rows/0/cols/0')
    def do_set_mixermatrix00(self, x):
        daq.setDouble('/dev2772/qas/0/deskew/rows/0/cols/0', x)
    def do_get_mixermatrix01(self):
        return daq.getDouble('/dev2772/qas/0/deskew/rows/0/cols/1')
    def do_set_mixermatrix01(self, x):
        daq.setDouble('/dev2772/qas/0/deskew/rows/0/cols/1', x)
    def do_get_mixermatrix10(self):
        return daq.getDouble('/dev2772/qas/0/deskew/rows/1/cols/0')
    def do_set_mixermatrix10(self, x):
        daq.setDouble('/dev2772/qas/0/deskew/rows/1/cols/0', x)
    def do_get_mixermatrix11(self):
        return daq.getDouble('/dev2772/qas/0/deskew/rows/1/cols/1')
    def do_set_mixermatrix11(self, x):
        daq.setDouble('/dev2772/qas/0/deskew/rows/1/cols/1', x)
    def do_get_integrationlength(self):
        return daq.getInt('/dev2772/qas/0/integration/length')
    def do_set_integrationlength(self,x):
        daq.setInt('/dev2772/qas/0/integration/length', 0)
    def do_get_delay(self):
        return daq.getInt('/dev2772/qas/0/delay')
    def do_set_delay(self,x):
        daq.setInt('/dev2772/qas/0/delay', x)
    def do_get_integrationtrigger(self):
        return daq.getInt('/dev2772/qas/0/integration/trigger/channel')
    def do_set_integrationtrigger(self, x):
        daq.setInt('/dev2772/qas/0/integration/trigger/channel', x)

    def do_get_threshold1(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/0/level')
    def do_set_threshold1(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/0/level', x)
    def do_get_threshold2(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/1/level')
    def do_set_threshold2(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/1/level', x)
    def do_get_threshold3(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/2/level')
    def do_set_threshold3(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/2/level', x)
    def do_get_threshold4(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/3/level')
    def do_set_threshold4(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/3/level', x)
    def do_get_threshold5(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/4/level')
    def do_set_threshold5(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/4/level', x)
    def do_get_threshold6(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/5/level')
    def do_set_threshold6(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/5/level', x)
    def do_get_threshold7(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/6/level')
    def do_set_threshold7(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/6/level', x)
    def do_get_threshold8(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/7/level')
    def do_set_threshold8(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/7/level', x)
    def do_get_threshold9(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/8/level')
    def do_set_threshold9(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/8/level', x)
    def do_get_threshold10(self):
        return daq.getDouble('/dev2772/qas/0/thresholds/9/level')
    def do_set_threshold10(self, x):
        return daq.setDouble('/dev2772/qas/0/thresholds/9/level', x)
#QA result
    def set_result(self, x):
        daq.setInt('/dev2772/qas/0/result/enable', x)

    def do_get_resultsource(self):
        return daq.getInt('/dev2772/qas/0/result/source')
    def do_set_resultsource(self, x):
        daq.setInt('/dev2772/qas/0/result/source', x)
    def do_get_resultlength(self):
        daq.getInt('/dev2772/qas/0/result/length')
    def do_set_resultlength(self, x):
        daq.setInt('/dev2772/qas/0/result/length', x)
    def do_get_resultaverages(self):
        return daq.getInt('/dev2772/qas/0/result/averages')
    def do_set_resultaverages(self, x):
        daq.setInt('/dev2772/qas/0/result/averages', x)
    def do_set_resultreset(self):
        daq.setInt('/dev2772/qas/0/result/reset', 1)

#QA AWG

    def do_get_rerun(self):
        if daq.getInt('/dev2772/awgs/0/single') ==1:
            return 0
        elif daq.getInt('/dev2772/awgs/0/single')==0:
            return 1
    def do_set_rerun(self, x):
        if x==0:
            daq.setInt('/dev2772/awgs/0/single', 1)
        elif x == 1:
            return daq.setInt('/dev2772/awgs/0/single', 0)
    def do_get_samplingrate(self):
        return daq.getInt('/dev2772/awgs/0/time')
    def do_set_samplingrate(self, x):
        daq.setInt('/dev2772/awgs/0/time', x)
    def do_get_amplitude1(self):
        return daq.getDouble('/dev2772/awgs/0/outputs/0/amplitude')
    def do_set_amplitude1(self, x):
        daq.setDouble('/dev2772/awgs/0/outputs/0/amplitude', x)
    def do_get_amplitude2(self):
        return daq.getDouble('/dev2772/awgs/0/outputs/1/amplitude')
    def do_set_amplitude2(self, x):
        daq.setDouble('/dev2772/awgs/0/outputs/1/amplitude', x)
    def do_get_mode1(self):
        return daq.getInt('/dev2772/awgs/0/outputs/0/mode')
    def do_set_mode1(self, x):
        daq.setInt('/dev2772/awgs/0/outputs/0/mode', x)
    def do_get_mode2(self):
        return daq.getInt('/dev2772/awgs/0/outputs/1/mode')
    def do_set_mode2(self, x):
        daq.setInt('/dev2772/awgs/0/outputs/1/mode',x)
    def do_get_anatrig1signal(self):
        return daq.getInt('/dev2772/awgs/0/triggers/0/channel')
    def do_set_anatrig1signal(self, x):
        daq.setInt('/dev2772/awgs/0/triggers/0/channel', x)
    def do_get_anatrig1slope(self):
        return daq.getInt('/dev2772/awgs/0/triggers/0/slope')
    def do_set_anatrig1slope(self, x):
        daq.setInt('/dev2772/awgs/0/triggers/0/slope', x)
    def do_get_anatrig1level(self):
        return daq.getDouble('/dev2772/awgs/0/triggers/0/level')
    def do_set_anatrig1level(self, x):
        daq.setDouble('/dev2772/awgs/0/triggers/0/level', x)
    def do_get_anatrig1hysteresis(self):
        return daq.getDouble('/dev2772/awgs/0/triggers/0/hysteresis/absolute')
    def do_set_anatrig1hysteresis(self, x):
        daq.setDouble('/dev2772/awgs/0/triggers/0/hysteresis/absolute', x)
    def do_get_digtrig1signal(self):
        return daq.getInt('/dev2772/awgs/0/auxtriggers/0/channel')
    def do_set_digtrig1signal(self, x):
        daq.setInt('/dev2772/awgs/0/auxtriggers/0/channel', x)
    def do_get_digtrig1slope(self):
        return daq.getInt('/dev2772/awgs/0/auxtriggers/0/slope')
    def do_set_digtrig1slope(self, x):
        daq.setInt('/dev2772/awgs/0/auxtriggers/0/slope', x)
    def do_get_memoryusage(self):
        return daq.getDouble('/dev2772/awgs/0/waveform/memoryusage')

#QA InOut

    def do_get_sigIn1range(self):
        return daq.getDouble('/dev2772/sigins/0/range')
    def do_set_sigIn1range(self, x):
        daq.setDouble('/dev2772/sigins/0/range', x)
    def do_get_sigIn2range(self):
        return daq.getDouble('/dev2772/sigins/1/range')
    def do_set_sigIn2range(self, x):
        daq.setDouble('/dev2772/sigins/1/range', x)
    def do_get_sigIn1scaling(self):
        return daq.getDouble('/dev2772/sigins/0/scaling')
    def do_set_sigIn1scaling(self, x):
        daq.setDouble('/dev2772/sigins/0/scaling', x)
    def do_get_sigIn2scaling(self):
        return daq.getDouble('/dev2772/sigins/1/scaling')
    def do_set_sigIn2scaling(self, x):
        daq.setDouble('/dev2772/sigins/1/scaling', x)
    def do_get_sigOut1on(self):
        return daq.getInt('/dev2772/sigouts/0/on')
    def do_set_sigOut1on(self, x):
        daq.setInt('/dev2772/sigouts/0/on', x)
    def do_get_sigOut2on(self):
        return daq.getInt('/dev2772/sigouts/1/on')
    def do_set_sigOut2on(self, x):
        daq.setInt('/dev2772/sigouts/1/on', x)
    def do_get_sigOut1range(self):
        return daq.getInt('/dev2772/sigouts/0/range')
    def do_set_sigOut1range(self, x):
        daq.setInt('/dev2772/sigouts/0/range', x)
    def do_get_sigOut2range(self):
        return daq.getInt('/dev2772/sigouts/1/range')
    def do_set_sigOut2range(self, x):
        daq.setInt('/dev2772/sigouts/1/range', x)
    def do_get_sigOut1offset(self):
        return daq.getDouble('/dev2772/sigouts/0/offset')
    def do_set_sigOut1offset(self, x):
        daq.setDouble('/dev2772/sigouts/0/offset', x)
    def do_get_sigOut2offset(self):
        return daq.getDouble('/dev2772/sigouts/1/offset')
    def do_set_sigOut2offset(self, x):
        daq.setDouble('/dev2772/sigouts/1/offset', x)


    def get_result(self):
       return daq.get("/DEV2772/QAS/0/RESULT/DATA/0/WAVE")["dev2772"]["qas"]["0"]["result"]["data"]["0"]["wave"][0]["vector"]

    #uploading string and starting AWGs

    def upload_awg(self, ccode):

        awg_uhfqa = daq.awgModule()
        awg_uhfqa.set('device', 'DEV2772')
        awg_uhfqa.execute()
        daq.sync()
        awg_uhfqa.set('compiler/sourcestring', ccode)
        daq.sync()
        sleep(0.05)

    def start_awg(self):
        awg_uhfqa = daq.awgModule()
        awg_uhfqa.set('device', 'DEV2772')
        awg_uhfqa.execute()
        daq.sync()
        awg_uhfqa.set('awg/enable', 1)

    def sync(self):
        daq.sync()

    def isReady(self):
        if (daq.getInt("/dev2772/qas/0/result/acquired")>0):
            return False
        else:
            return True

    def set_uhfqa_freq(self, freq):
        awg_uhfqa = daq.awgModule()
        awg_uhfqa.set('device', 'DEV2772')
        awg_uhfqa.execute()
        daq.sync()
        awg_uhfqa.set('awg/enable', 0)
        seq = """const multiplier = """ + str(freq) + """/1e6/4/450;
        const DELAY =0;
        const LENGTH = 800.0;

        wave i = sine(LENGTH, 1, 0, LENGTH*multiplier);
        wave q = cosine(LENGTH, 1, 0, LENGTH*multiplier);


        wave z = zeros(DELAY);

        i= join(z, i);
        q= join(z,q);

        wave ii = i;


        while (true) {
          waitDigTrigger(1, 1);
          resetOscPhase();
          playWave(q, ii);
          //playZero(0);
          startQA(QA_INT_0, true);

        }"""

        timey = np.arange(0, daq.getInt('/dev2772/qas/0/integration/length'), 1)

        theta1 = 0
        theta2 = np.pi / 2

        frequency = freq
        amplitude = 1

        qwave = amplitude * np.sin(2 * np.pi * frequency * timey / 1.8e9 + theta1)
        iwave = amplitude * np.sin(2 * np.pi * frequency * timey / 1.8e9 + theta2)
        # plt.plot(iwave)
        # plt.plot(qwave)
        # plt.show()
        arr_imag = np.array(iwave)
        arr_real = np.array(qwave)

        daq.set('/dev2772/QAS/0/INTEGRATION/WEIGHTS/0/IMAG', arr_imag)
        daq.set('/dev2772/QAS/0/INTEGRATION/WEIGHTS/0/REAL', arr_real)
        daq.sync()

        awg_uhfqa.set('compiler/sourcestring', seq)

        sleep(0.1)
        awg_uhfqa.set('awg/enable', 1)