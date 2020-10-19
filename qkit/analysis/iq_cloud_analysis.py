# IQ cloud analysis
# started by M. Spiecker, 06/2020
#
# This IQ cloud analysis class performs a gaussian mixture fit on the IQ data to directly map out
# the density matrix of the system under study. The fit uses the sci-kit learn library.
#
# HOW TO USE IT:
#
# 1. Create an instance of IQCloudAnalysis and set up a gaussian mixture model.
# So far only spherical covariance type is supported.
#
# 2. For a simple IQ analysis use analyse_qubit_clouds.
# It fits the IQ clouds and interprets the two most prominent states as the qubit system which is then characterized.
# 3.1 If the IQ data is recorded versus a sweep paramter (e.g. Rabi, T1, ...) use set_IQ_data_sweep.
# 4. Fitting the clouds:
# 4.1 If the position and weights of the clouds are unkonwn you have to use the standard gm fit fit_clouds.
# The states are unsortet and have to be sortet either bei weight or position.
# 4.2 For a qubit, when only the weights of the clouds are unkown, you can use the fast fit_clouds_weight function
# 5. Plot the gaussian mixture model on a given axes.



import numpy as np
from scipy import constants as pyc


from sklearn.mixture import GaussianMixture

class IQCloudAnalysis:

    def __init__(self):

        self.sweep_param = None
        self.data = None
        self.dist_avg = 0.0
        self.n_steps = 0

        # prior knowledge
        self.pos_given = None
        self.var_given = None

        # fit
        self.gmm = None
        self.n_states = 0
        self.positions = None
        self.weights = None
        self.variances = None

        # After sorting
        self.theta = 0.0
        self.angle = None
        self.separation = None
        self.temp = None

        self.amplitude = None
        self.phase = None

        # plots
        self.fig = None
        self.ax = None

    def set_figure(self, fig, ax):

        self.fig = fig
        self.ax = ax

    def set_up_gaussian_mixture_model(self, n_states=2, covariance_type='spherical'):

        self.n_states = n_states
        self.gmm = GaussianMixture(self.n_states, covariance_type=covariance_type)

    def analyse_qubit_clouds(self, I, Q, fq=-1):
        """
        This routine performs an IQ cloud analyis with the given gaussian mixture model and
        interprets the two most prominent states as the qubit system.
        The rotation, the angle and the separation of the qubit clouds is determined.
        If the qubit frequency is given the temperature is calculated.
        """
        self.data = np.vstack((I, Q)).T

        # scale data around unity - important for convergence
        self.dist_avg = np.mean(np.sqrt(self.data[:, 0]**2 + self.data[:, 1]**2))
        self.data /= self.dist_avg

        self.gmm.fit(self.data)

        self.n_steps = 1
        aw = np.argsort(self.gmm.weights_[:])[::-1]
        self.positions = self.gmm.means_[aw]
        self.weights = self.gmm.weights_[aw]
        self.variances = self.gmm.covariances_[aw]

        # calc theta
        di = self.positions[0, 0] - self.positions[1, 0]
        dq = self.positions[0, 1] - self.positions[1, 1]
        self.theta = np.sign(dq) * np.arccos(di / np.sqrt(di**2 + dq**2))

        a = np.linalg.norm(self.positions[0, :])
        b = np.linalg.norm(self.positions[1, :])
        self.separation = np.linalg.norm(self.positions[1, :] - self.positions[0, :])
        self.angle = np.arccos((a**2 + b**2 - self.separation**2) / (2 * a * b))

        # calc temperature in mK
        if fq > 0:
            self.temp = 1e3 * pyc.h * fq / (pyc.k * np.log(self.weights[0] / self.weights[1]))
        else:
            self.temp = -1

        # extend axis for plotting
        self.data = np.expand_dims(self.data, axis=0)
        self.positions = np.expand_dims(self.positions, axis=0)
        self.weights = np.expand_dims(self.weights, axis=0)
        self.variances = np.expand_dims(self.variances, axis=0)

    # TODO allow for sweep_param = None
    def set_IQ_data_sweep(self, sweep_param, I, Q):

        self.sweep_param = sweep_param
        data = np.dstack((I, Q))
        self.data = np.moveaxis(data, 1, 0)
        self.n_steps = self.data.shape[0]

        # scale data around unity - important for convergence
        self.dist_avg = np.mean(np.sqrt(self.data[:, :, 0]**2 + self.data[:, :, 1]**2), axis=(0, 1))
        self.data /= self.dist_avg

    def fit_clouds(self):
        """ Fit of the clouds with the given gaussian mixture model.
        The states ...
        """
        self.positions = np.zeros((self.n_steps, self.n_states, 2))
        self.weights = np.zeros((self.n_steps, self.n_states))
        self.variances = np.zeros((self.n_steps, self.n_states))

        for i in range(self.n_steps):

            self.gmm.fit(self.data[i])

            self.positions[i, :, :] = self.gmm.means_
            self.weights[i, :] = self.gmm.weights_
            self.variances[i, :] = self.gmm.covariances_

    # TODO check if k means gives different results
    def fit_clouds_k_means(self):

        pass

    def fit_clouds_weight(self):

        self.positions = np.zeros((self.n_steps, self.n_states, 2))
        self.weights = np.zeros((self.n_steps, self.n_states))
        self.variances = np.zeros((self.n_steps, self.n_states))

        for i in range(self.n_steps):

            self.positions[i, :] = self.pos_given
            self.variances[i, :] = self.var_given
            self.weights[i, :] = self.gaussian_mixture_fit(self.data[i])

    # so far for two states only
    def gaussian_mixture_fit(self, data):
        """ Fast maximum likelihood fit of the weights for two states.
        The position (self.pos_given) and the variance (self.var_given) must be given
        """
        v1 = self.var_given[0]
        v2 = self.var_given[1]

        dist = self.calc_dist(data, self.pos_given)

        e1 = np.exp(- dist[:, 0] / (2 * v1)) / v1
        e2 = np.exp(- dist[:, 1] / (2 * v2)) / v2

        c = (e1 + e2) / (e1 - e2)

        tol = 1e-6
        delta_left = -1.0
        delta_right = 1.0
        delta = 0.0

        while delta_right - delta_left > tol:

            df = np.sum(1 / (delta + c))

            if df > 0:
                delta_left = delta
                delta = (delta_right + delta_left) / 2
            else:
                delta_right = delta
                delta = (delta_right + delta_left) / 2

                            # final error of state population better than 0.5 * tol
        return 0.5 * (1 + delta), 0.5 * (1 - delta)

    # TODO can easily be generalized for squeezed states
    def calc_dist(self, data, positions):

        dist = np.empty((data.shape[0], self.n_states))

        for i in range(self.n_states):
            dist[:, i] = (data[:, 0] - positions[i, 0])**2 + (data[:, 1] - positions[i, 1])**2

        return dist

    def sort_peaks_positions(self, ref_pos=None):
        """ Sorts the states according to a reference positions.
        If ref_pos is None the first sweep position is chosen
        """
        if ref_pos is None:
            ref_pos = self.positions[0, :, :]

        label = np.zeros(self.n_states, dtype=np.int)

        for i in range(self.n_steps):
            for j in range(self.n_states):
                dist = (self.positions[i, j, 0] - ref_pos[:, 0])**2 + \
                       (self.positions[i, j, 1] - ref_pos[:, 1])**2

                label[j] = np.argmin(dist)

            self.positions[i, :, :] = self.positions[i, label, :]
            self.weights[i, :] = self.weights[i, label]
            self.variances[i, :] = self.variances[i, label]

    def sort_peaks_weights(self):
        """ Sorts the states according to their weight
        """
        for i in range(self.n_steps):

            aw = np.argsort(self.weights[i, :])[::-1]
            self.positions[i, :, :] = self.positions[i, aw, :]
            self.weights[i, :] = self.weights[i, aw]
            self.variances[i, :] = self.variances[i, aw]

    def calc_amplitude_phase(self):

        self.amplitude = np.linalg.norm(self.positions[:, :, :], axis=2)
        self.phase = np.arctan2(self.positions[:, :, 1], self.positions[:, :, 0])

    def calc_separation(self, state1=0, state2=1):

        return np.linalg.norm(self.positions[:, state1, :] - self.positions[:, state2, :], axis=1)

    # TODO extend for more states
    def calc_temperature(self, fq):

        self.temp = np.zeros(self.n_steps)

        for i in range(self.n_steps):
            ws = np.sort(self.weights[i, :])[::-1]
            self.temp[i] = 1e3 * pyc.h * fq / (pyc.k * np.log(ws[0] / ws[1]))  # in mK

    def plot_peaks(self, step=0):

        self.ax.scatter(self.data[step, :, 0], self.data[step, :, 1], 0.1)
        x = np.linspace(np.min(self.data[step, :, 0]), np.max(self.data[step, :, 0]), 101)
        y = np.linspace(np.min(self.data[step, :, 1]), np.max(self.data[step, :, 1]), 101)

        X, Y = np.meshgrid(x, y)

        iq = np.dstack((X, Y))
        iq = np.reshape(iq, (y.size * x.size, 2))
        dist = self.calc_dist(iq, self.positions[step, :, :])
        dist = np.reshape(dist, (y.size, x.size, self.n_states))

        Z = np.zeros_like(X)
        for i in range(self.n_states):
            Z += self.weights[step, i] * np.exp(- dist[:, :, i] / (2 * self.variances[step, i])) / (2 * np.pi * self.variances[step, i])

        self.ax.contour(X, Y, np.log(Z))

        # plot origin and position of states
        self.ax.plot(0.0, 0.0, 'r.')
        for i in range(self.n_states):
            self.ax.plot(self.positions[step, i, 0], self.positions[step, i, 1], 'k.')

        self.ax.axis("equal")


    def plot_probability_sweep(self):

        for i in range(self.n_states):
            self.ax.plot(self.sweep_param, self.weights[:, i], '.')







