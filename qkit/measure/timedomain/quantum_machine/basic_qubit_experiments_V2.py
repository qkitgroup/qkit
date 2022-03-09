# Quantum machines qubit library
# started by M. Spiecker, 06.2020
#
# TODO add text
#
#
# HOW TO USE IT:
# Since the quantum machines card is a very versatile machine,
# the setup and the experiments will be very different.
# Thus use this file as template and look up for your experiments.


import inspect
import time
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from qm.qua import *
from qm import SimulationConfig
from qm import LoopbackInterface
from qm.QuantumMachinesManager import QuantumMachinesManager

from qkit.measure.timedomain.quantum_machine.qm_qkit_wrapper import QmQkitWrapper

bit_shift = 12

class BasicQubitExperiments(QmQkitWrapper):

    def __init__(self, qm_config):

        QmQkitWrapper.__init__(self)

        self.qm_config = qm_config

        # global experiment settings
        self.wait_before = 250000  # time 4 for ns   # TODO wir nicht automatisch abgespeichert
        self.wait_end = 250000  # time 4 for ns

        self.program = None

        # Output
        self.I = None
        self.Q = None
        self.I_avg = None
        self.Q_avg = None
        self.data = None

        # plots
        self.fig = None
        self.ax = None

    def set_figure(self, fig, ax=None):
        self.fig = fig
        self.ax = ax

    # Experiments

    @QmQkitWrapper.measure
    def adc_data_test(self, f_list, avg=1000):

        self.I = np.zeros((avg, f_list.size))
        self.Q = np.zeros((avg, f_list.size))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        # qkit data storage
        self.exp_name = "qubit_spectroscopy"
        self.coords = {"QB_IF_freq": [f_list, "Hz"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["QB_IF_freq", "avg"], "V"], "Q": [self.Q.T, ["QB_IF_freq", "avg"], "V"],
                       "I_avg": [self.I_avg, ["QB_IF_freq"], "V"], "Q_avg": [self.Q_avg, ["QB_IF_freq"], "V"]}


    @QmQkitWrapper.measure
    def adc_data(self, plot=True):

        with program() as adc:
            # measurement block:
            stream = declare_stream(adc_trace=True)

            reset_phase("resonator")
            measure("readout", "resonator", stream)

            with stream_processing():
                stream.input1().save_all("I_stream")
                stream.input2().save_all("Q_stream")

        self.program = adc
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)

        I_stream_handle = job.result_handles.get("I_stream")
        I_stream_handle.wait_for_all_values()
        adci = I_stream_handle.fetch(slice(I_stream_handle.count_so_far()))["value"][0]

        Q_stream_handle = job.result_handles.get("Q_stream")
        Q_stream_handle.wait_for_all_values()
        adcq = Q_stream_handle.fetch(slice(Q_stream_handle.count_so_far()))["value"][0]

        # qkit data storage
        self.exp_name = "adc_data"
        self.coords = {"time_i": [np.arange(adci.size), "ns"], "time_q": [np.arange(adcq.size), "ns"]}
        self.values = {"adci": [adci, ["time_i"], "V"], "adcq": [adcq, ["time_q"], "V"]}
        self.sourcecode = inspect.getsource(self.adc_data)

        if plot:
            self.ax.clear()
            self.ax.plot(adci)
            self.ax.plot(adcq)

        return adci,  adcq

    @QmQkitWrapper.measure
    def qubit_spectroscopy(self, f_vec, a=1.0 , avg=100, plot=True):

        if np.min(f_vec) < 50e6 or np.max(f_vec) > 100e6:
            b = (f_vec >= 50e6) & (f_vec <= 100e6)
            f_vec = f_vec[b]
            print("IF frequency needs to be between 50 and 100 MHz. \nFrequency vector was adjusted.")

        f_list = f_vec.astype(int).tolist()

        with program() as qbSpec:

            N = declare(int)
            f = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):

                with for_each_(f, f_list):

                    wait(self.wait_before, "qubit")  # times 4 for ns

                    update_frequency('qubit', f)
                    play('pi' * amp(a), 'qubit')

                    # measurement block:
                    align("resonator", "qubit")
                    play('pi' * amp(a) , 'qubit')

                    measure("readout", "resonator", None, dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))


                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        job = self.qm_config.qm.execute(qbSpec, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()
        job.result_handles.get("Q").wait_for_all_values()

        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, len(f_list)))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, len(f_list)))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "qubit_spectroscopy"
        self.coords = {"QB_IF_freq": [f_list, "Hz"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["QB_IF_freq", "avg"], "V"], "Q": [self.Q.T, ["QB_IF_freq", "avg"], "V"],
                       "I_avg": [self.I_avg, ["QB_IF_freq"], "V"], "Q_avg": [self.Q_avg, ["QB_IF_freq"], "V"]}

        if plot:
            self.ax.clear()
            self.ax.plot(f_vec, self.I_avg)
            self.ax.plot(f_vec, self.Q_avg)

    @QmQkitWrapper.measure
    def ac_stark_spectroscopy(self, f_vec, avg=100, plot=True):

        if np.min(f_vec) < 50e6 or np.max(f_vec) > 100e6:
            b = (f_vec >= 50e6) & (f_vec <= 100e6)
            f_vec = f_vec[b]
            print("IF frequency needs to be between 50 and 100 MHz. \nFrequency vector was adjusted.")

        f_list = f_vec.astype(int).tolist()

        with program() as qbSpec:

            N = declare(int)
            f = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):
                with for_each_(f, f_list):

                    wait(self.wait_before, "qubit")  # times 4 for ns

                    update_frequency('qubit', f)
                    align("signal", "reference", "qubit")
                    play('saturation_pulse', 'qubit')
                    play('saturation_pulse', 'signal')


                    # measurement block:
                    align("signal", "reference", "qubit")
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                    assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        job = self.qm_config.qm.execute(qbSpec, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.I = np.reshape(res.variable_results.I.values, (avg, len(f_list)))
        self.Q = np.reshape(res.variable_results.Q.values, (avg, len(f_list)))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "ac_stark_spectroscopy"
        self.coords = {"QB_IF_freq": [f_list, "Hz"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["QB_IF_freq", "avg"], "V"], "Q": [self.Q.T, ["QB_IF_freq", "avg"], "V"],
                       "I_avg": [self.I_avg, ["QB_IF_freq"], "V"], "Q_avg": [self.Q_avg, ["QB_IF_freq"], "V"]}

        if plot:
            self.ax.clear()
            self.ax.plot(f_vec, self.I_avg)
            self.ax.plot(f_vec, self.Q_avg)

    @QmQkitWrapper.measure
    def iq_clouds(self, n_points, plot=True):

        with program() as clouds:

            N = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < n_points, N + 1):
                wait(self.wait_before, "qubit")

                measure("readout", "resonator", None, dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                                                      ,dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                # save to client:
                save(I, "I")
                save(Q, "Q")

        job = self.qm_config.qm.execute(clouds, duration_limit=0, data_limit=0)

        job.result_handles.get("I").wait_for_all_values()
        self.I = job.result_handles.get("I").fetch_all()["value"]
        job.result_handles.get("Q").wait_for_all_values()          #TODO is this nessecary?
        self.Q = job.result_handles.get("Q").fetch_all()["value"]
        self.I_avg = None
        self.Q_avg = None


        # qkit data storage
        self.exp_name = "iq_clouds"
        self.coords = {"n_points": [np.arange(n_points), "#"]}
        self.values = {"I": [self.I, ["n_points"], "#"], "Q": [self.Q, ["n_points"], "#"]}
        self.logs = {}

        if plot:
            self.ax.clear()
            self.ax.hist2d(self.I, self.Q, bins=100, cmin=1, norm=mpl.colors.LogNorm())
            self.ax.plot(0.0, 0.0, 'r.')
            self.ax.axis("equal")
        #return self.I, self.Q

    def auto_calibrate_theta(self, iqcloud, output=True):

        time.sleep(1)

        self.qm_config.set_theta(0.0)
        self.wait_before = 250   # make sure the resonator rings down
        self.iq_clouds(50000, plot=False)
        iqcloud.analyse_qubit_clouds(self.I, self.Q)

        if output:
            print("theta = {}".format(iqcloud.theta))

        self.qm_config.set_theta(- iqcloud.theta)

        time.sleep(1)

    @QmQkitWrapper.measure
    def power_rabi(self, a_vec, n_pulses=1, avg=100, plot=True):

        a_list = a_vec.tolist()

        with program() as powerRabi:

            N = declare(int)
            a = declare(fixed)
            i = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):

                with for_each_(a, a_list):

                    wait(self.wait_before, "qubit")

                    with for_(i, 0, i < n_pulses, i + 1):
                        play("pi" * amp(a), "qubit")

                    # measurement block:
                    measure("readout", "resonator", None, dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        job = self.qm_config.qm.execute(powerRabi, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        #Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, len(a_list)))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, len(a_list)))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "power_rabi"
        self.coords = {"amp": [a_list, "1"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["amp", "avg"], "V"], "Q": [self.Q.T, ["amp", "avg"], "V"],
                       "I_avg": [self.I_avg, ["amp"], "V"], "Q_avg": [self.Q_avg, ["amp"], "V"]}

        if plot:
            self.ax.clear()
            self.ax.plot(a_vec, self.I_avg)
            self.ax.plot(a_vec, self.Q_avg)

    @QmQkitWrapper.measure
    def pi_pulse_calibration(self, n_pulses, dn=1, avg=100, plot=True):

        with program() as powerRabi:

            N = declare(int)
            n = declare(int)
            i = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):

                with for_(n, 0, n < n_pulses, n + dn):

                    wait(self.wait_before, "qubit")  # times 4 for ns

                    with for_(i, 0, i < n, i + 1):
                        play("pi", "qubit")

                    # measurement block:
                    align("resonator", "qubit")
                    measure("readout", "resonator", None, dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        self.program = powerRabi
        job = self.qm_config.qm.execute(powerRabi, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, (n_pulses - 1) // dn + 1))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, (n_pulses - 1) // dn + 1))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "pulse_calibration"
        self.coords = {"pi_pulses": [np.arange(0, n_pulses, dn), "1"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["pi_pulses", "avg"], "V"], "Q": [self.Q.T, ["pi_pulses", "avg"], "V"],
                       "I_avg": [self.I_avg, ["pi_pulses"], "V"], "Q_avg": [self.Q_avg, ["pi_pulses"], "V"]}

        if plot:
            self.ax.clear()
            self.ax.plot(np.arange(0, n_pulses, dn), self.I_avg)
            self.ax.plot(np.arange(0, n_pulses, dn), self.Q_avg)

    def prepare_waiting_list(self, t_vec):

        t_vec = t_vec.astype(int)

        if np.min(t_vec) < 4:
            b = t_vec < 4
            t_vec[b] = 4
            print("Minimum waiting time 4 clock cycles, which corresponds to 16ns. \nWaiting time vector was adjusted")

        return t_vec

    @QmQkitWrapper.measure
    def t1(self, t_vec, n_pulses, t_wait=-1, active_reset=False, start_state=True, threshold=0.0, avg=100, plot=True):

        t_vec = self.prepare_waiting_list(t_vec)
        t_list = t_vec.tolist()

        with program() as measureT1:

            N = declare(int)
            t = declare(int)
            i = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):
                with for_each_(t, t_list):

                    # control block
                    wait(self.wait_before, "qubit")

                    if t_wait < 0:
                        with for_(i, 0, i < n_pulses, i + 1):
                            play("pi", "qubit")
                    else:
                        with for_(i, 0, i < n_pulses, i + 1):
                            play("pi", "qubit")
                            wait(t_wait, "qubit")

                    if active_reset:
                        # measurement block:
                        align("resonator", "qubit")
                        measure("readout", "resonator", None,
                                dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                                , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))


                        if start_state:
                            play("pi", "qubit", condition=I > threshold)  # excited
                        else:
                            play("pi", "qubit", condition=I < threshold)

                    elif t_wait > -1:
                        play("pi", "qubit")

                    wait(t, "qubit")

                    # measurement block:
                    align("resonator", "qubit")
                    measure("readout", "resonator", None, dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        self.program = measureT1
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, t_vec.size))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, t_vec.size))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "T1"
        self.coords = {"t_wait": [4 * t_vec / 1000, "us"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["t_wait", "avg"], "V"], "Q": [self.Q.T, ["t_wait", "avg"], "V"],
                      "I_avg": [self.I_avg, ["t_wait"], "V"], "Q_avg": [self.Q_avg, ["t_wait"], "V"]}

        if plot:

            t_us = t_vec * 4 / 1000

            self.ax.clear()
            self.ax.plot(t_us, self.I_avg, marker='x')
            self.ax.plot(t_us, self.Q_avg, marker='x')
            self.ax.set_xlabel('t (us)')

    @QmQkitWrapper.measure
    def t2(self, t_vec, echo=0, avg=100, plot=True):
        """ Simple Hahn echo experiment with constant number of pi-pulses
        If echo = 0 a normal ramsey experiment is performed
        """
        if echo > 0:
            t_vec_half = t_vec / (2 * echo)

            t_vec_half = self.prepare_waiting_list(t_vec_half)
            t_vec = 2 * t_vec_half
            t_mat = np.stack((t_vec_half, t_vec))
            t_list = t_mat.tolist()

            t_vec = t_vec * echo
        else:
            t_vec = self.prepare_waiting_list(t_vec)
            t_mat = np.stack((t_vec, t_vec))  # needed for qua loop
            t_list = t_mat.tolist()

        with program() as measureT2:

            N = declare(int)
            t2 = declare(int)
            t = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            i = declare(int)

            with for_(N, 0, N < avg, N + 1):

                with for_each_((t2, t), t_list):

                    wait(self.wait_before, "qubit")

                    # control block
                    if echo == 0:
                        play("pi/2", "qubit")
                        wait(t, "qubit")
                        play("pi/2", "qubit")
                    else:
                        play("pi/2", "qubit")
                        wait(t2, "qubit")
                        with for_(i, 0, i < echo - 1, i + 1):
                            play("pi", "qubit")
                            wait(t, "qubit")
                        play("pi", "qubit")
                        wait(t2, "qubit")
                        play("pi/2", "qubit")

                    # measurement block:
                    align("resonator", "qubit")
                    measure("readout", "resonator", None,
                            dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:

                    save(I, "I")
                    save(Q, "Q")

        self.program = measureT2
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, t_vec.size))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, t_vec.size))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        if echo == 0:
            self.exp_name = "T2_ramsey"
        else:
            self.exp_name = "T2_echo_{}_pulses".format(echo)
        self.coords = {"t_wait": [4 * t_vec / 1000, "us"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["t_wait", "avg"], "V"], "Q": [self.Q.T, ["t_wait", "avg"], "V"],
                       "I_avg": [self.I_avg, ["t_wait"], "V"], "Q_avg": [self.Q_avg, ["t_wait"], "V"]}

        if plot:

            t_us = t_vec * 4 / 1000

            self.ax.clear()
            self.ax.plot(t_us, self.I_avg, marker='x')
            self.ax.plot(t_us, self.Q_avg, marker='x')
            self.ax.set_xlabel('t (us)')

    @QmQkitWrapper.measure
    def t2_cpmg(self, t, dt2, zrot=np.pi / 2, n_points=100, avg=100, plot=True):
        """ Time between pi/2 pulses is held constant.
            dt2 must be larger than 4
        """

        dt = 2 * dt2
        n = int(np.ceil(t / dt))  # make sure t is reached

        dn = int(np.ceil(n / n_points))  # make sure n_points is not exceeded
        n_pulses = np.arange(1, n + 1, dn)
        t_vec = dt * n_pulses

        n_list = n_pulses.tolist()

        with program() as measureT2:

            N = declare(int)
            n = declare(int)
            I = declare(fixed)
            Q = declare(fixed)
            i = declare(int)

            with for_(N, 0, N < avg, N + 1):

                with for_each_(n, n_list):

                    wait(self.wait_before, "qubit")

                    # control block
                    play("pi/2", "qubit")
                    frame_rotation_2pi(zrot, "qubit")
                    wait(dt2, "qubit")
                    with for_(i, 0, i < n - 1, i + 1):
                        play("pi", "qubit")
                        wait(dt, "qubit")
                    play("pi", "qubit")
                    wait(dt2, "qubit")
                    frame_rotation_2pi(- zrot, "qubit")
                    play("pi/2", "qubit")

                    # measurement block:
                    align("resonator", "qubit")
                    measure("readout", "resonator", None,
                            dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        self.program = measureT2
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, t_vec.size))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, t_vec.size))
        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "T2_cpmg_{:.3f}us".format(4 * dt / 1000).replace(".", "p")
        self.coords = {"t_wait": [4 * t_vec / 1000, "us"], "avg": [np.arange(avg), "#"]}
        self.values = {"I": [self.I.T, ["t_wait", "avg"], "V"], "Q": [self.Q.T, ["t_wait", "avg"], "V"],
                       "I_avg": [self.I_avg, ["t_wait"], "V"], "Q_avg": [self.Q_avg, ["t_wait"], "V"]}

        if plot:
            t_us = t_vec * 4 / 1000

            self.ax.clear()
            self.ax.plot(t_us, self.I_avg, marker='x')
            self.ax.plot(t_us, self.Q_avg, marker='x')
            self.ax.set_xlabel('t (us)')

    @QmQkitWrapper.measure
    def t1_qndness(self, n_measure, t_vec, avg=100, plot=True):

        t_vec = self.prepare_waiting_list(t_vec)
        t_list = t_vec.tolist()

        with program() as T1measure:

            N = declare(int)
            t = declare(int)
            i = declare(int)
            I = declare(fixed)
            Q = declare(fixed)


            with for_(N, 0, N < avg, N + 1):

                with for_each_(t, t_list):

                    wait(self.wait_before, "qubit")

                    # control block

                    play("pi", "qubit")
                    #wait(25, "qubit")  # make sure the pulse is faster in the fridge than the measurement pulse

                    with for_(i, 0, i < n_measure, i + 1):
                        align("resonator", "qubit")
                        measure("readout", "resonator", None,
                                dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                                , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))



                        # save to client:
                        save(I, "I")
                        save(Q, "Q")

                        wait(t, "resonator")

        job = self.qm_config.qm.execute(T1measure, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"], (avg, t_vec.size, n_measure))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"], (avg, t_vec.size, n_measure))

        ts_nsec_I = np.reshape(job.result_handles.get("I").fetch_all()["timestamp"], (avg, t_vec.size, n_measure))
        ts_nsec_Q = np.reshape(job.result_handles.get("Q").fetch_all()["timestamp"], (avg, t_vec.size, n_measure))
        ts_nsec_I = ts_nsec_I[0, :, :]
        ts_nsec_Q = ts_nsec_Q[0, :, :]
        ts_nsec_I -= ts_nsec_I[:, 0, np.newaxis]
        ts_nsec_Q -= ts_nsec_Q[:, 0, np.newaxis]

        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)

        # qkit data storage
        self.exp_name = "T1_qndness"
        self.coords = {"avg": [np.arange(avg), "#"], "t_wait": [4 * t_vec / 1000, "us"],
                       "n_measure": [np.arange(n_measure), "#"]}
        self.values = {"I": [np.moveaxis(self.I, 0, 2), ["t_wait", "n_measure", "avg"], "V"],
                       "Q": [np.moveaxis(self.Q, 0, 2), ["t_wait", "n_measure", "avg"], "V"],
                       "I_avg": [self.I_avg, ["t_wait", "n_measure"], "V"],
                       "Q_avg": [self.Q_avg, ["t_wait", "n_measure"], "V"],
                       "t": [ts_nsec_I / 1000, ["t_wait", "n_measure"], "us"]}

        if plot:

            t_us = ts_nsec_I / 1000

            self.ax.clear()
            self.ax.plot(t_us.T, self.I_avg.T, marker='x')
            self.ax.plot(t_us.T, self.Q_avg.T, marker='x')
            self.ax.set_xlabel('t (us)')

    # active reset experiments

    @QmQkitWrapper.measure
    def active_reset_from_thermal_state(self, state, threshold, n_points=1000, plot=True):

        with program() as activeReset:

            N = declare(int)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < n_points, N + 1):
                measure("readout", "resonator", None,
                        dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                        , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))


                if state:
                    play("pi", "qubit", condition=I > threshold)  # excited state
                else:
                    play("pi", "qubit", condition=I < threshold)

                wait(50, "qubit")

                # measurement block:
                align("resonator", "qubit")
                measure("readout", "resonator", None,
                        dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                        , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                # save to client:
                save(I, "I")
                save(Q, "Q")

                wait(self.wait_end, "resonator")  # wait until qubit is thermally populated again

        # job = self.qm_config.qm.simulate(activeReset, SimulationConfig(800, False, False, LoopbackInterface([("con1", 1, "con1", 1)])))
        #samples = job.get_simulated_samples(include_digital=False)
        # samples.con1.plot(analog_ports={"1"})
        # res = job.get_results()
        # I_vals = res.variable_results.I.values
        # Q_vals = res.variable_results.Q.values

        job = self.qm_config.qm.execute(activeReset, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = job.result_handles.get("I").fetch_all()["value"]
        self.Q = job.result_handles.get("Q").fetch_all()["value"]
        self.I_avg = None
        self.Q_avg = None

        # qkit data storage
        self.exp_name = "Active_reset"
        self.coords = {"n_points": [np.arange(n_points), "#"]}
        self.values = {"I": [self.I.T, ["n_points"], "V"], "Q": [self.Q.T, ["n_points"], "V"]}

        if plot:
            self.ax.clear()
            self.ax.hist2d(self.I, self.Q, bins=100, cmin=1, norm=mpl.colors.LogNorm())
            self.ax.axvline(threshold)
            self.ax.plot(0.0, 0.0, 'r.')
            self.ax.axis("equal")

    @QmQkitWrapper.measure
    def t1_stabilized_V2(self, t_vec, n_stab, threshold, stab_state=False, start_state=False, t_wait=25, avg=1000, plot=True):

        t_vec = self.prepare_waiting_list(t_vec)
        t_list = t_vec.tolist()

        with program() as T1_stab:

            N = declare(int)
            t = declare(int)
            i = declare(int)
            iter_done = declare(int, value=-1)

            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):
                with for_each_(t, t_list):

                    wait(self.wait_before, "qubit")

                    ###################################

                    with for_(i, 0, i < n_stab, i + 1):  # stabilization for n_stab

                        wait(t_wait, "qubit")  # wait between measurements

                        # measurement block:
                        align("resonator", "qubit")
                        measure("readout", "resonator", None,
                                dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                                , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                        # wait ring down resonator TODO???

                        align("resonator", "qubit")
                        if stab_state:
                            # excited
                            play("pi", "qubit", condition=I > threshold)  # excited
                            with if_(I > threshold):
                                save(i, "flip")
                            with else_():
                                wait(12, "qubit")  # qubit pulse length

                        else:
                            play("pi", "qubit", condition=I < threshold)
                            with if_(I < threshold):
                                save(i, "flip")
                            with else_():
                                wait(12, "qubit")  # qubit pulse length

                    if(start_state !=  stab_state):
                        play("pi", "qubit")

                    # control block
                    wait(t, "qubit")

                    # measurement block:
                    align("resonator", "qubit")
                    measure("readout", "resonator", None,
                            dual_demod.full('integ_w1_I', 'out1', 'integ_w2_I', 'out2', I)
                            , dual_demod.full('integ_w1_Q', 'out1', 'integ_w2_Q', 'out2', Q))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")
                    save(iter_done, "flip")

        self.program = T1_stab
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.result_handles.get("I").wait_for_all_values()

        # Get data
        self.I = np.reshape(job.result_handles.get("I").fetch_all()["value"],(avg, t_vec.size))
        self.Q = np.reshape(job.result_handles.get("Q").fetch_all()["value"],(avg, t_vec.size))

        flip = job.result_handles.get("flip").fetch_all()["value"]
        t_flip = job.result_handles.get("flip").fetch_all()["timestamp"]

        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)
        flip_hist, _ = np.histogram(flip, bins=np.arange(n_stab + 1) - 0.5)

        # qkit data storage
        self.exp_name = "T1_stabilized_{}_{}_{}_{}us".format(n_stab, stab_state, start_state, 4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t_wait": [4 * t_vec / 1000, "us"], "avg": [np.arange(avg), "#"],
                       "flip_index": [np.arange(n_stab), "#"],
                       "flip": [flip, "1"],
                       "t_flip": [t_flip / 1000, "ns"]}
        self.values = {"I": [self.I.T, ["t_wait", "avg"], "V"], "Q": [self.Q.T, ["t_wait", "avg"], "V"],
                       "I_avg": [self.I_avg, ["t_wait"], "V"], "Q _avg": [self.Q_avg, ["t_wait"], "V"],
                       "flip_hist": [flip_hist, ["flip_index"], "1"]}

        if plot:
            t_us = t_vec * 4 / 1000

            self.fig.clear()
            ax1 = self.fig.add_subplot(121)
            ax1.plot(t_us, self.I_avg, marker='x')
            ax1.plot(t_us, self.Q_avg, marker='x')
            ax1.set_xlabel('t (us)')

            ax2 = self.fig.add_subplot(122)
            ax2.bar(np.arange(n_stab), flip_hist, width=1.0)
            ax2.set_xlabel('flip index')

    @QmQkitWrapper.measure
    def t1_measurement_heat(self, t_vec, n_stab, threshold, start_state=False, avg=1000, plot=True):

        t_vec = self.prepare_waiting_list(t_vec)
        t_list = t_vec.tolist()

        with program() as T1_stab:

            N = declare(int)
            t = declare(int)
            i = declare(int)

            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            with for_(N, 0, N < avg, N + 1):
                with for_each_(t, t_list):

                    #wait(self.wait_before - t, "signal")
                    wait(self.wait_before - t, "qubit")

                    with for_(i, 0, i < n_stab, i + 1):  # stabilization for n_stab

                        play("pi_pulse", "qubit")
                        wait(160, "qubit")
                        # measurement block:
                        # measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                        # measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                        # calculations:
                        # assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))

                        wait(25, "qubit")

                    # measurement block:
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))

                    wait(25, "signal")

                    align("qubit", "signal", "reference")

                    if start_state:
                        # excited
                        play("pi_pulse", "qubit", condition=I > threshold)  # excited
                        with if_(I > threshold):
                            save(i, "flip")

                    else:
                        play("pi_pulse", "qubit", condition=I < threshold)
                        with if_(I < threshold):
                            save(i, "flip")

                    # control block
                    wait(t, "qubit")

                    # measurement block:
                    align("qubit", "signal", "reference")
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                    assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")

        job = self.qm_config.qm.execute(T1_stab, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.program = T1_stab
        self.I = np.reshape(res.variable_results.I.values, (avg, t_vec.size))
        self.Q = np.reshape(res.variable_results.Q.values, (avg, t_vec.size))
        flip = res.variable_results.flip.values

        self.I_avg = np.mean(self.I, axis=0)
        self.Q_avg = np.mean(self.Q, axis=0)
        flip_hist, _ = np.histogram(flip, bins=np.arange(n_stab + 1) - 0.5)

        self.data = (flip, flip_hist)

        # qkit data storage
        self.exp_name = "T1_measurement_heat_{}_{}".format(n_stab, start_state)
        self.coords = {"t_wait": [4 * t_vec / 1000, "us"], "avg": [np.arange(avg), "#"],
                       "flip index": [np.arange(n_stab), "#"]}
        self.values = {"I": [self.I.T, ["t_wait", "avg"], "V"], "Q": [self.Q.T, ["t_wait", "avg"], "V"],
                       "I_avg": [self.I_avg, ["t_wait"], "V"], "Q _avg": [self.Q_avg, ["t_wait"], "V"],
                       "flip_hist": [flip_hist, ["flip index"], "1"]}

        if plot:
            t_us = t_vec * 4 / 1000

            self.fig.clear()
            ax1 = self.fig.add_subplot(121)
            ax1.plot(t_us, self.I_avg, marker='x')
            ax1.plot(t_us, self.Q_avg, marker='x')
            ax1.set_xlabel('t (us)')

            ax2 = self.fig.add_subplot(122)
            ax2.bar(np.arange(n_stab), flip_hist, width=1.0)
            ax2.set_xlabel('flip index')

