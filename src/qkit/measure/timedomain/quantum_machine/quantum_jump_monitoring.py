# Quantum machines coherence library
# started by M. Spiecker, 06.2020
#
# TODO add text

# HOW TO USE IT:
# Since the quantum machines card is a very versatile machine,
# the setup and the experiments will be very different.
# Thus use this file as template and look up for your experiments.



import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt

from qm.qua import *
from qm import SimulationConfig
from qm import LoopbackInterface

from qm.QuantumMachinesManager import QuantumMachinesManager
from qkit.measure.timedomain.quantum_machine.qm_qkit_wrapper import QmQkitWrapper

bit_shift = 12

class QuantumJumpMonitoring(QmQkitWrapper):

    def __init__(self, qm_config):

        QmQkitWrapper.__init__(self)

        self.qm_config = qm_config

        # global experiment settings
        self.wait_before = 250  # times 4 for ns

        self.program = None

        # Output
        self.I = None
        self.Q = None
        self.state = None
        self.t = None

        self.data = None

        # plots
        self.fig = None

    def set_figure(self, fig):
        self.fig = fig

    # Experiments

    @QmQkitWrapper.measure
    def quantum_jump_test(self, n_measure, ref_pos, dist, t_wait=25, plot=True):

        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()
        var1 = dist[0].item()
        var2 = dist[1].item()

        with program() as quantumJumps:
            N = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(bool)
            #state = declare(int)

            with for_(N, 0, N < n_measure, N + 1):

                # measurement block:
                measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                wait(t_wait, "signal")

                # calculations:
                assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                assign(state, d1 < d2)
                # with if_(d1 < var1):
                #    assign(state, -1)
                # with else_():
                #    with if_(d2 < var2):
                #        assign(state, 1)
                #    with else_():
                #        assign(state, 0)

                # save to client:
                save(I, "I")
                save(Q, "Q")
                save(d1, "d1")
                save(d2, "d2")
                save(state, "state")

        self.program = quantumJumps
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.I = res.variable_results.I.values
        self.Q = res.variable_results.Q.values
        d1 = res.variable_results.d1.values
        d2 = res.variable_results.d2.values
        self.state = res.variable_results.state.values
        self.t = res.variable_results.state.ts_nsec

        # qkit data storage
        self.exp_name = "quantum_jumps_{}us".format(4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t": [self.t / 1000, "us"]}
        self.values = {"state": [state, ["t"], "sate"],
                       "I": [self.I, ["t"], "V"], "Q": [self.Q, ["t"], "V"]}

        if plot:
            self.fig.clear()
            grid = self.fig.add_gridspec(ncols=1, nrows=4, height_ratios=[1, 1, 1, 2])

            ax1 = self.fig.add_subplot(grid[0, 0])
            ax1.plot(np.arange(n_measure), self.I)
            ax1.plot(np.arange(n_measure), self.Q)

            ax2 = self.fig.add_subplot(grid[1, 0])
            ax2.plot(np.arange(n_measure), d1)
            ax2.plot(np.arange(n_measure), d2)

            ax3 = self.fig.add_subplot(grid[2, 0])
            ax3.plot(np.arange(n_measure), self.state)

            ax4 = self.fig.add_subplot(grid[3, 0])
            ax4.scatter(self.I, self.Q, 0.1)
            s = np.linspace(0, 2 * np.pi)
            ax4.plot(ref_pos[0, 0] + np.sqrt(var1) * np.cos(s), ref_pos[0, 1] + np.sqrt(var1) * np.sin(s), 'k')
            ax4.plot(ref_pos[1, 0] + np.sqrt(var2) * np.cos(s), ref_pos[1, 1] + np.sqrt(var2) * np.sin(s), 'k')
            ax4.plot(0.0, 0.0, 'r.')
            ax4.axis("equal")

    @QmQkitWrapper.measure
    def quantum_jump_hist_test(self, n_measure, ref_pos, dist, t_wait=25, plot=True):
        """
        The regions defined by the variance must not overlap
        """

        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()

        # var1 = dist[0].item()
        # var2 = dist[1].item()
        sigma1 = dist[0].item()
        sigma2 = dist[1].item()

        with program() as quantumJumps:

            N = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(int, value=-1)  # latch filter : value = -1 (ground state)
            # state = declare(int, value=0) # not latch filter: value = 0,
            count = declare(int, value=0)

            with for_(N, 0, N < n_measure, N + 1):
                # measurement block:
                measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                wait(t_wait, "signal")

                # calculations:
                assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                # assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                # assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                assign(d1, pos1x - I)
                assign(d2, I - pos2x)

                # latch filter
                with if_(state == -1):
                    with if_(d2 > sigma2):
                        assign(count, count + 1)
                    with else_():
                        save(count, "hist_down")
                        assign(count, 0)  # start counting from zero
                        assign(state, 1)

                with else_():
                    with if_(d1 > sigma1):
                        assign(count, count + 1)
                    with else_():
                        save(count, "hist_up")
                        assign(count, 0)  # start counting from zero
                        assign(state, -1)

                # no latch filter
                # with if_(d1 < sigma1):
                #     with if_(state == -1):
                #         assign(count, count + 1)
                #     with else_():
                #         with if_(state == 1):
                #             save(count, "hist_up")
                #         assign(count, 0)  # start counting from zero
                #         assign(state, -1)
                # with else_():
                #     with if_(d2 < sigma2):
                #         with if_(state == 1):
                #             assign(count, count + 1)
                #         with else_():
                #             with if_(state == -1):
                #                 save(count, "hist_down")
                #             assign(count, 0)  # start counting from zero
                #             assign(state, 1)
                #     with else_():
                #         with if_(state == 1):
                #             save(count, "hist_up")
                #         with if_(state == -1):
                #             save(count, "hist_down")
                #         assign(state, 0)

                # save to client:
                save(I, "I")
                save(Q, "Q")
                save(d1, "d1")
                save(d2, "d2")
                save(state, "state")
                save(count, "count")

        self.program = quantumJumps
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.program = quantumJumps
        self.I = res.variable_results.I.values
        self.Q = res.variable_results.Q.values
        d1 = res.variable_results.d1.values
        d2 = res.variable_results.d2.values
        self.state = res.variable_results.state.values
        self.t = res.variable_results.state.ts_nsec
        count = res.variable_results.count.values
        hist_up = res.variable_results.hist_up.values
        hist_down = res.variable_results.hist_down.values

        hist_up, _ = np.histogram(hist_up[1:-1], bins=np.arange(hist_up.max() + 2) - 0.5)   # Throw out first and last jump
        hist_down, _ = np.histogram(hist_down[1:-1], bins=np.arange(hist_down.max() + 2) - 0.5)  # Throw out first and last jump

        # qkit data storage
        self.exp_name = "quantum_jumps_{}us".format(4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t": [self.t / 1000, "us"]}
        self.values = {"state": [state, ["t"], "sate"],
                       "I": [self.I, ["t"], "V"], "Q": [self.Q, ["t"], "V"]}

        if plot:
            self.fig.clear()
            grid = self.fig.add_gridspec(ncols=1, nrows=6, height_ratios=[1, 1, 1, 2, 1, 1])

            ax1 = self.fig.add_subplot(grid[0, 0])
            #ax1.plot(np.arange(n_measure), self.I)
            #ax1.plot(np.arange(n_measure), self.Q)
            ax1.plot(np.arange(n_measure), d1)
            ax1.plot(np.arange(n_measure), d2)

            ax2 = self.fig.add_subplot(grid[1, 0])
            ax2.plot(np.arange(n_measure), self.state)

            ax3 = self.fig.add_subplot(grid[2, 0])
            ax3.plot(np.arange(n_measure), count)

            ax4 = self.fig.add_subplot(grid[3, 0])
            ax4.scatter(self.I, self.Q, 0.1)
            # s = np.linspace(0, 2 * np.pi)
            # ax4.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
            # ax4.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
            ax4.plot(0.0, 0.0, 'r.')
            ax4.axvline(pos1x - sigma1, color='C0')
            ax4.axvline(pos2x + sigma2, color='C1')
            ax4.axis("equal")

            ax5 = self.fig.add_subplot(grid[4, 0])
            ax5.bar(np.arange(hist_down.size), hist_down, color="C0", width=1.0, alpha=0.8)
            ax5.set_yscale("symlog")

            ax6 = self.fig.add_subplot(grid[5, 0])
            ax6.bar(np.arange(hist_up.size), hist_up, color="C1", width=1.0, alpha=0.8)
            ax6.set_yscale("symlog")

    @QmQkitWrapper.measure
    def quantum_jump_hist(self, n_measure, ref_pos, dist, t_wait=25, plot=True):
        """
        The regions defined by the variance must not overlap
        """

        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()

        # var1 = dist[0].item()
        # var2 = dist[1].item()
        sigma1 = dist[0].item()
        sigma2 = dist[1].item()

        with program() as quantumJumps:

            N = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(int, value=0)
            count = declare(int)

            with for_(N, 0, N < n_measure, N + 1):
                # measurement block:
                measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                wait(t_wait, "signal")

                # calculations:
                assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                # assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                # assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                assign(d1, pos1x - I)
                assign(d2, I - pos2x)

                # latch filter
                with if_(state == -1):
                    with if_(d2 > sigma2):
                        assign(count, count + 1)
                    with else_():
                        save(count, "hist_down")
                        assign(count, 0)  # start counting from zero
                        assign(state, 1)
                with else_():
                    with if_(state == 1):
                        with if_(d1 > sigma1):
                            assign(count, count + 1)
                        with else_():
                            save(count, "hist_up")
                            assign(state, -1)
                            assign(count, 0)  # start counting from zero
                    with else_():  # initialize here to have the first jump length correct
                        with if_(d1 < sigma1):
                            assign(state, -1)
                            assign(count, 0)
                        with else_():
                            with if_(d2 < sigma2):
                                assign(state, 1)
                                assign(count, 0)

                # no latch filter
                # with if_(d1 < sigma1):
                #     with if_(state == -1):
                #         assign(count, count + 1)
                #     with else_():
                #         with if_(state == 1):
                #             save(count, "hist_up")
                #         assign(count, 0)  # start counting from zero
                #         assign(state, -1)
                # with else_():
                #     with if_(d2 < sigma2):
                #         with if_(state == 1):
                #             assign(count, count + 1)
                #         with else_():
                #             with if_(state == -1):
                #                 save(count, "hist_down")
                #             assign(count, 0)  # start counting from zero
                #             assign(state, 1)
                #     with else_():
                #         with if_(state == 1):
                #             save(count, "hist_up")
                #         with if_(state == -1):
                #             save(count, "hist_down")
                #         assign(state, 0)

                # save to client:
                save(I, "I")
                save(Q, "Q")
                save(state, "state")


        self.program = quantumJumps
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.I = res.variable_results.I.values
        self.Q = res.variable_results.Q.values
        self.state = res.variable_results.state.values
        self.t = res.variable_results.state.ts_nsec
        hist_up = res.variable_results.hist_up.values
        hist_down = res.variable_results.hist_down.values

        hist_up, _ = np.histogram(hist_up[:-1], bins=np.arange(hist_up.max() + 1) + 0.5)
        hist_down, _ = np.histogram(hist_down[:-1], bins=np.arange(hist_down.max() + 1) + 0.5)

        # qkit data storage
        self.exp_name = "quantum_jump_hist_{}us".format(4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t": [self.t / 1000, "us"],
                       "hist_up": [hist_up, "1"],
                       "hist_down": [hist_down, "1"]}   # "hist_down_range": [np.arange(hist_down.size) + 1, "1"]
        self.values = {"state": [self.state, ["t"], "state"],
                       "I": [self.I, ["t"], "V"], "Q": [self.Q, ["t"], "V"]}

        if plot:
            t_rep = np.median(self.t[1:] - self.t[:-1]) / 1000

            self.fig.clear()
            grid = self.fig.add_gridspec(ncols=1, nrows=3, height_ratios=[2, 1, 1])

            ax1 = self.fig.add_subplot(grid[0, 0])
            ax1.scatter(self.I, self.Q, 0.1)
            #s = np.linspace(0, 2 * np.pi)
            #ax1.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
            #ax1.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
            ax1.plot(0.0, 0.0, 'r.')
            ax1.axvline(pos1x - sigma1, color='C0')
            ax1.axvline(pos2x + sigma2, color='C1')
            ax1.axis("equal")

            # Maximum likelihood fits and histogram plots
            m = np.sum(hist_down)
            n = np.sum(hist_down * np.arange(hist_down.size))
            p = n / (m + n)
            t_up = - t_rep / np.log(p)
            p_down = m * (1 - p) * p ** np.arange(hist_down.size)

            ax2 = self.fig.add_subplot(grid[1, 0])
            ax2.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\uparrow$= {:.6f}'.format(t_up),
                     horizontalalignment='right', verticalalignment='top', transform=ax2.transAxes)
            ax2.bar(np.arange(hist_down.size), hist_down, color="C0", width=1.0, alpha=0.8)
            ax2.plot(np.arange(hist_down.size), p_down, color="C0")
            ax2.set_yscale("symlog")

            m = np.sum(hist_up)
            n = np.sum(hist_up * np.arange(hist_up.size))
            p = n / (m + n)
            t_down = - t_rep / np.log(p)
            p_up = m * (1 - p) * p ** np.arange(hist_up.size)

            ax3 = self.fig.add_subplot(grid[2, 0])
            ax3.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\downarrow$ = {:.6f}'.format(t_down),
                     horizontalalignment='right', verticalalignment='top', transform=ax3.transAxes)
            ax3.bar(np.arange(hist_up.size), hist_up, color="C1", width=1.0, alpha=0.8)
            ax3.plot(np.arange(hist_up.size), p_up, color="C1")
            ax3.set_yscale("symlog")

    @QmQkitWrapper.measure
    def quantum_jump_hist_stab(self, n_measure, n_stab, ref_pos, dist, t_wait=25,
                               stab_state=True, start_state=False, plot=True):
        """ Workaround
        The regions defined by the variance must not overlap
        """
        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()

        # var1 = dist[0].item()
        # var2 = dist[1].item()
        sigma1 = dist[0].item()
        sigma2 = dist[1].item()

        threshold = (pos1x + pos2x) / 2

        if start_state:
            init_state = 1
        else:
            init_state = -1

        with program() as quantumJumps:

            N = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(int, value=init_state)
            count = declare(int, value=0)

            with for_(N, 0, N < n_measure, N + 1):

                with if_(N < n_stab):

                    wait(t_wait, "qubit")  # wait between measurements

                    # measurement block:
                    align("qubit", "signal", "reference")
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))

                    # wait ring down resonator TODO???

                    align("qubit", "signal", "reference")
                    if stab_state:
                        # excited
                        play("pi_pulse", "qubit", condition=I > threshold)  # excited
                        with if_(I > threshold):
                            save(N, "flip")
                        with else_():
                            wait(12, "qubit")  # qubit pulse length

                    else:
                        play("pi_pulse", "qubit", condition=I < threshold)
                        with if_(I < threshold):
                            save(N, "flip")
                        with else_():
                            wait(12, "qubit")  # qubit pulse length

                with else_():
                    with if_(N == n_stab):
                        if (start_state != stab_state):
                            play("pi_pulse", "qubit")
                        else:
                            wait(12, "qubit")  # qubit pulse length
                    with else_():

                        wait(t_wait, "signal")

                        # measurement block:
                        align("qubit", "signal", "reference")
                        measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                        measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                        # calculations:
                        assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                        assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                        # assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                        # assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                        assign(d1, pos1x - I)
                        assign(d2, I - pos2x)

                        # latch filter
                        with if_(state == -1):
                            with if_(d2 > sigma2):
                                assign(count, count + 1)
                            with else_():
                                save(count, "hist_down")
                                assign(count, 0)  # start counting from zero
                                assign(state, 1)
                        with else_():
                            with if_(d1 > sigma1):
                                assign(count, count + 1)
                            with else_():
                                save(count, "hist_up")
                                assign(state, -1)
                                assign(count, 0)  # start counting from zero

                        # save to client:
                        save(I, "I")
                        save(Q, "Q")
                        save(state, "state")

        self.program = quantumJumps
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.I = res.variable_results.I.values
        self.Q = res.variable_results.Q.values
        self.state = res.variable_results.state.values
        self.t = res.variable_results.state.ts_nsec
        hist_up = res.variable_results.hist_up.values
        hist_down = res.variable_results.hist_down.values

        hist_up, _ = np.histogram(hist_up[:-1], bins=np.arange(hist_up.max() + 1) + 0.5)
        hist_down, _ = np.histogram(hist_down[:-1], bins=np.arange(hist_down.max() + 1) + 0.5)

        flip = res.variable_results.flip.values
        t_flip = res.variable_results.flip.ts_nsec
        flip_hist, _ = np.histogram(flip, bins=np.arange(n_stab + 1) - 0.5)

        # qkit data storage
        self.exp_name = "quantum_jump_hist_stab_{}_{}_{}_{}us".format(n_stab, stab_state, start_state, 4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t": [self.t / 1000, "us"],
                       "hist_up": [hist_up, "1"],
                       "hist_down": [hist_down, "1"],
                       "flip_index": [np.arange(n_stab), "#"],
                       "flip": [flip, "1"],
                       "t_flip": [t_flip / 1000, "ns"]}
        self.values = {"state": [self.state, ["t"], "state"],
                       "I": [self.I, ["t"], "V"], "Q": [self.Q, ["t"], "V"],
                       "flip_hist": [flip_hist, ["flip_index"], "1"]}

        if plot:
            t_rep = np.median(self.t[1:] - self.t[:-1]) / 1000

            self.fig.clear()
            grid = self.fig.add_gridspec(ncols=1, nrows=3, height_ratios=[2, 1, 1])

            ax1 = self.fig.add_subplot(grid[0, 0])
            ax1.scatter(self.I, self.Q, 0.1)
            # s = np.linspace(0, 2 * np.pi)
            # ax1.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
            # ax1.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
            ax1.plot(0.0, 0.0, 'r.')
            ax1.axvline(pos1x - sigma1, color='C0')
            ax1.axvline(pos2x + sigma2, color='C1')
            ax1.axis("equal")

            # Maximum likelihood fits and histogram plots
            m = np.sum(hist_down)
            n = np.sum(hist_down * np.arange(hist_down.size))
            p = n / (m + n)
            t_up = - t_rep / np.log(p)
            p_down = m * (1 - p) * p ** np.arange(hist_down.size)

            ax2 = self.fig.add_subplot(grid[1, 0])
            ax2.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\uparrow$= {:.6f}'.format(t_up),
                     horizontalalignment='right', verticalalignment='top', transform=ax2.transAxes)
            ax2.bar(np.arange(hist_down.size), hist_down, color="C0", width=1.0, alpha=0.8)
            ax2.plot(np.arange(hist_down.size), p_down, color="C0")
            ax2.set_yscale("symlog")

            m = np.sum(hist_up)
            n = np.sum(hist_up * np.arange(hist_up.size))
            p = n / (m + n)
            t_down = - t_rep / np.log(p)
            p_up = m * (1 - p) * p ** np.arange(hist_up.size)

            ax3 = self.fig.add_subplot(grid[2, 0])
            ax3.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\downarrow$ = {:.6f}'.format(t_down),
                     horizontalalignment='right', verticalalignment='top', transform=ax3.transAxes)
            ax3.bar(np.arange(hist_up.size), hist_up, color="C1", width=1.0, alpha=0.8)
            ax3.plot(np.arange(hist_up.size), p_up, color="C1")
            ax3.set_yscale("symlog")

    @QmQkitWrapper.measure
    def quantum_jump_hist_average(self, n_measure, ref_pos, dist, t_wait=25, avg=10, plot=True):
        """
        The regions defined by the variance must not overlap
        """

        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()

        # var1 = dist[0].item()
        # var2 = dist[1].item()
        sigma1 = dist[0].item()
        sigma2 = dist[1].item()

        with program() as quantumJumps:

            N = declare(int)
            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(int)  # latch filter : value = -1 (ground state)
            count = declare(int)
            i = declare(int)
            iter_done = declare(int, value=-1)

            with for_(i, 0, i < avg, i + 1):

                assign(state, 0)  # needed for initialization

                wait(4, "qubit")  # 60ms maximum

                # qubit operation
                # ...

                # align("qubit", "signal", "reference")
                with for_(N, 0, N < n_measure, N + 1):

                    # measurement block:
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    wait(t_wait, "signal")

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                    assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                    # assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                    # assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                    assign(d1, pos1x - I)
                    assign(d2, I - pos2x)

                    # latch filter
                    with if_(state == -1):
                        with if_(d2 > sigma2):
                            assign(count, count + 1)
                        with else_():
                            save(count, "hist_down")
                            assign(state, 1)
                            assign(count, 0)  # start counting from zero
                    with else_():
                        with if_(state == 1):
                            with if_(d1 > sigma1):
                                assign(count, count + 1)
                            with else_():
                                save(count, "hist_up")
                                assign(state, -1)
                                assign(count, 0)  # start counting from zero
                        with else_():  # initialize here to have the first jump length correct
                            with if_(d1 < sigma1):
                                assign(state, -1)
                                assign(count, 0)
                            with else_():
                                with if_(d2 < sigma2):
                                    assign(state, 1)
                                    assign(count, 0)

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")
                    save(state, "state")

                save(iter_done, "hist_down")
                save(iter_done, "hist_up")

        self.program = quantumJumps
        job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)
        job.wait_for_all_results()
        res = job.get_results()

        self.I = res.variable_results.I.values
        self.Q = res.variable_results.Q.values
        self.state = res.variable_results.state.values
        self.t = res.variable_results.state.ts_nsec
        hist_up = res.variable_results.hist_up.values
        hist_down = res.variable_results.hist_down.values

        hist_up, _ = np.histogram(hist_up[1:-1], bins=np.arange(hist_up.max() + 1) + 0.5)
        hist_down, _ = np.histogram(hist_down[1:-1], bins=np.arange(hist_down.max() + 1) + 0.5)

        # qkit data storage
        self.exp_name = "quantum_jump_hist_{}us".format(4 * t_wait / 1000).replace('.', 'p')
        self.coords = {"t": [self.t / 1000, "us"],
                       "hist_up": [hist_up, "1"],
                       "hist_down": [hist_down, "1"]}  # "hist_down_range": [np.arange(hist_down.size) + 1, "1"]
        self.values = {"state": [self.state, ["t"], "state"],
                       "I": [self.I, ["t"], "V"], "Q": [self.Q, ["t"], "V"]}

        if plot:

            t_rep = np.median(self.t[1:] - self.t[:-1]) / 1000

            self.fig.clear()
            grid = self.fig.add_gridspec(ncols=1, nrows=3, height_ratios=[2, 1, 1])

            self.ax1 = self.fig.add_subplot(grid[0, 0])
            self.ax1.scatter(self.I, self.Q, 0.1)
            # s = np.linspace(0, 2 * np.pi)
            # self.ax1.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
            # self.ax1.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
            self.ax1.plot(0.0, 0.0, 'r.')
            self.ax1.axvline(pos1x - sigma1, color='C0')
            self.ax1.axvline(pos2x + sigma2, color='C1')
            self.ax1.axis("equal")

            # Maximum likelihood fits and histogram plots
            m = np.sum(hist_down)
            n = np.sum(hist_down * np.arange(hist_down.size))
            p = n / (m + n)
            t_up = - t_rep / np.log(p)
            p_down = m * (1 - p) * p ** np.arange(hist_down.size)

            ax2 = self.fig.add_subplot(grid[1, 0])
            ax2.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\uparrow$= {:.6f}'.format(t_up),
                     horizontalalignment='right', verticalalignment='top', transform=ax2.transAxes)
            ax2.bar(np.arange(hist_down.size), hist_down, color="C0", width=1.0, alpha=0.8)
            ax2.plot(np.arange(hist_down.size), p_down, color="C0")
            ax2.set_yscale("symlog")

            m = np.sum(hist_up)
            n = np.sum(hist_up * np.arange(hist_up.size))
            p = n / (m + n)
            t_down = - t_rep / np.log(p)
            p_up = m * (1 - p) * p ** np.arange(hist_up.size)

            ax3 = self.fig.add_subplot(grid[2, 0])
            ax3.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\downarrow$ = {:.6f}'.format(t_down),
                     horizontalalignment='right', verticalalignment='top', transform=ax3.transAxes)
            ax3.bar(np.arange(hist_up.size), hist_up, color="C1", width=1.0, alpha=0.8)
            ax3.plot(np.arange(hist_up.size), p_up, color="C1")
            ax3.set_yscale("symlog")

    @QmQkitWrapper.measure
    def quantum_jump_hist_stab_avg(self, n_measure,  n_stab, ref_pos, dist, t_stab=200, t_measure=200,
                                   stab_state=False, start_state=False, avg=100, plot=True):
        """
        The regions defined by the variance must not overlap
        """

        pos1x = ref_pos[0, 0].item()
        pos1y = ref_pos[0, 1].item()
        pos2x = ref_pos[1, 0].item()
        pos2y = ref_pos[1, 1].item()

        sigma1 = dist[0].item()
        sigma2 = dist[1].item()

        threshold = (pos1x + pos2x) / 2
        print(threshold)

        with program() as quantumJumps:

            n = declare(int)
            i = declare(int)
            j = declare(int)
            iter_done = declare(int, value=-1)

            Is = declare(fixed)
            Qs = declare(fixed)
            Ir = declare(fixed)
            Qr = declare(fixed)
            I = declare(fixed)
            Q = declare(fixed)

            d1 = declare(fixed)
            d2 = declare(fixed)
            state = declare(int)
            count = declare(int)

            with for_(i, 0, i < avg, i + 1):

                save(iter_done, "flip")
                save(iter_done, "hist_down")
                save(iter_done, "hist_up")

                assign(state, 0)  # initialization

                # measurement block:
                measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                # calculations:
                assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))

                with for_(j, 0, j < n_stab, j + 1):  # stabilization for n_stab

                    # wait ring down resonator to have a more precise pi pulse???

                    if stab_state:
                        # excited
                        play("pi_pulse", "qubit", condition=I > threshold)  # excited
                        with if_(I > threshold):
                            save(j, "flip")
                        with else_():
                            wait(12, "qubit")  # qubit pulse length

                    else:
                        play("pi_pulse", "qubit", condition=I < threshold)
                        with if_(I < threshold):
                            save(j, "flip")
                        with else_():
                            wait(12, "qubit")  # qubit pulse length

                    wait(t_stab, "qubit")  # wait between measurements

                    # measurement block:
                    align("qubit", "signal", "reference")
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))

                align("qubit", "signal", "reference")
                if start_state:
                    # excited
                    play("pi_pulse", "qubit", condition=I > threshold)  # excited
                    with if_(I > threshold):
                        save(j, "flip")
                    with else_():
                        wait(12, "qubit")  # qubit pulse length

                else:
                    play("pi_pulse", "qubit", condition=I < threshold)
                    with if_(I < threshold):
                        save(j, "flip")
                    with else_():
                        wait(12, "qubit")  # qubit pulse length

                align("qubit", "signal", "reference")
                with for_(n, 0, n < n_measure, n + 1):

                    # measurement block:
                    measure("readout_sig", "signal", None, ("integW_Is", Is), ("integW_Qs", Qs))
                    measure("readout_ref", "reference", None, ("integW_Ir", Ir), ("integW_Qr", Qr))

                    wait(t_measure, "signal")

                    # calculations:
                    assign(I, (Is << bit_shift) * (Ir << bit_shift) + (Qs << bit_shift) * (Qr << bit_shift))
                    assign(Q, (Is << bit_shift) * (Qr << bit_shift) - (Qs << bit_shift) * (Ir << bit_shift))

                    # assign(d1, (I - pos1x) * (I - pos1x) + (Q - pos1y) * (Q - pos1y))
                    # assign(d2, (I - pos2x) * (I - pos2x) + (Q - pos2y) * (Q - pos2y))

                    assign(d1, pos1x - I)
                    assign(d2, I - pos2x)

                    # latch filter
                    with if_(state == -1):
                        with if_(d2 > sigma2):
                            assign(count, count + 1)
                        with else_():
                            save(count, "hist_down")
                            assign(count, 0)  # start counting from zero
                            assign(state, 1)
                    with else_():
                        with if_(state == 1):
                            with if_(d1 > sigma1):
                                assign(count, count + 1)
                            with else_():
                                save(count, "hist_up")
                                assign(state, -1)
                                assign(count, 0)  # start counting from zero
                        with else_():  # initialize here to have the first jump length correct
                            with if_(d1 < sigma1):
                                assign(state, -1)
                                assign(count, 0)
                            with else_():
                                with if_(d2 < sigma2):
                                    assign(state, 1)
                                    assign(count, 0)

                    # save to client:
                    save(I, "I")
                    save(Q, "Q")
                    save(state, "state")

                align("qubit", "signal", "reference")
                wait(250, "qubit")  # 10ms

        self.program = quantumJumps
        job = self.qm_config.qm.simulate(self.program, SimulationConfig(100000))
        samples = job.get_simulated_samples()

        result = job.result_handles
        j_handle = result.get("flip")
        print(j_handle.fetch_all())

        samples.con1.plot()
        plt.show()


        #if plot:
        #    self.fig.clear()
        #    grid = self.fig.add_gridspec(ncols=1, nrows=3, height_ratios=[2, 1, 1])
        #
        #    ax1 = self.fig.add_subplot(grid[0, 0])
        #    ax1.plot(samples., self.Q, 0.1)
        #    # s = np.linspace(0, 2 * np.pi)
        #    # self.ax1.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
        #    # self.ax1.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
        #    ax1.plot(0.0, 0.0, 'r.')


        #job = self.qm_config.qm.execute(self.program, duration_limit=0, data_limit=0)

        # job.wait_for_all_results()
        # res = job.get_results()
        #
        # self.I = np.reshape(res.variable_results.I.values, (avg, n_measure))
        # self.Q = np.reshape(res.variable_results.Q.values, (avg, n_measure))
        # self.state = np.reshape(res.variable_results.state.values, (avg, n_measure))
        # self.t = np.reshape(res.variable_results.state.ts_nsec, (avg, n_measure))
        # self.t -= self.t[:, 0, np.newaxis]
        #
        # list_up = res.variable_results.hist_up.values
        # list_down = res.variable_results.hist_down.values
        # hist_up_avg, _ = np.histogram(list_up[:-1], bins=np.arange(list_up.max() + 1) + 0.5)
        # hist_down_avg, _ = np.histogram(list_down[:-1], bins=np.arange(list_down.max() + 1) + 0.5)
        #
        # flip = res.variable_results.flip.values
        # t_flip = res.variable_results.flip.ts_nsec
        # flip_hist, _ = np.histogram(flip, bins=np.arange(n_stab + 1) - 0.5)
        #
        # # qkit data storage
        # self.exp_name = "quantum_jump_hist_stabilized_{}_{}_{}".format(n_stab, stab_state, start_state)
        # self.coords = {"avg": [np.arange(avg), "#"],
        #                "n_measure": [np.arange(n_measure), "#"],
        #                "list_up": [list_up, "1"],
        #                "list_down": [list_down, "1"],
        #                "hist_up_avg": [hist_up_avg, "1"],
        #                "hist_down_avg": [hist_down_avg, "1"],
        #                "flip_index": [np.arange(n_stab), "#"],
        #                "flip": [flip, "1"],
        #                "t_flip": [t_flip / 1000, "ns"]}
        # self.values = {"state": [self.state, ["avg", "n_measure"], "state"],
        #                "t": [self.t / 1000, ["avg", "n_measure"], "us"],
        #                "I": [self.I, ["avg", "n_measure"], "V"], "Q": [self.Q, ["avg", "n_measure"], "V"],
        #                "flip_hist": [flip_hist, ["flip_index"], "1"]}
        #
        # if plot:
        #
        #     t_rep = np.mean(self.t[:, 1:] - self.t[:, :-1]) / 1000
        #
        #     self.fig.clear()
        #     grid = self.fig.add_gridspec(ncols=1, nrows=3, height_ratios=[2, 1, 1])
        #
        #     ax1 = self.fig.add_subplot(grid[0, 0])
        #     ax1.scatter(self.I, self.Q, 0.1)
        #     # s = np.linspace(0, 2 * np.pi)
        #     # self.ax1.plot(ref_pos[0, 0] + np.sqrt(var) * np.cos(s), ref_pos[0, 1] + np.sqrt(var) * np.sin(s), 'k')
        #     # self.ax1.plot(ref_pos[1, 0] + np.sqrt(var) * np.cos(s), ref_pos[1, 1] + np.sqrt(var) * np.sin(s), 'k')
        #     ax1.plot(0.0, 0.0, 'r.')
        #     ax1.axvline(pos1x - sigma1, color='C0')
        #     ax1.axvline(pos2x + sigma2, color='C1')
        #     ax1.axis("equal")
        #
        #     # Maximum likelihood fit
        #
        #     m = np.sum(hist_down_avg)
        #     n = np.sum(hist_down_avg * np.arange(hist_down_avg.size))
        #     p = n / (m + n)
        #     t_up = - t_rep / np.log(p)
        #     p_down = m * (1 - p) * p ** np.arange(hist_down_avg.size)
        #
        #     ax2 = self.fig.add_subplot(grid[1, 0])
        #     ax2.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\uparrow$= {:.6f}'.format(t_up),
        #              horizontalalignment='right', verticalalignment='top', transform=ax2.transAxes)
        #     ax2.bar(np.arange(hist_down_avg.size), hist_down_avg, color="C0", width=1.0, alpha=0.8)
        #     ax2.plot(np.arange(hist_down_avg.size), p_down, color="C0")
        #     ax2.set_yscale("symlog")
        #
        #     m = np.sum(hist_up_avg)
        #     n = np.sum(hist_up_avg * np.arange(hist_up_avg.size))
        #     p = n / (m + n)
        #     t_down = - t_rep / np.log(p)
        #     p_up = m * (1 - p) * p ** np.arange(hist_up_avg.size)
        #
        #     ax3 = self.fig.add_subplot(grid[2, 0])
        #     ax3.text(0.9, 0.9, r'$p$ = {:.6f}'.format(p) + "\n" + r'$t_\downarrow$ = {:.6f}'.format(t_down),
        #              horizontalalignment='right', verticalalignment='top', transform=ax3.transAxes)
        #     ax3.bar(np.arange(hist_up_avg.size), hist_up_avg, color="C1", width=1.0, alpha=0.8)
        #     ax3.plot(np.arange(hist_up_avg.size), p_up, color="C1")
        #     ax3.set_yscale("symlog")