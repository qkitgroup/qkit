# IQ cloud analysis
# started by M. Spiecker, 06/2020
#
# This IQ cloud analysis class performs a gaussian mixture fit on the IQ data to directly map out
# the density matrix of the system under study. The fit uses the sci-kit learn library.
#
# HOW TO USE IT:
# Either use the qubit cloud analysis routine
#
# or for more elaborate fits
#
# 0. Create an instance of IQCloudAnalysis
# 1. Load the I, Q data - (averages, sweep parameter)
# 2. Set up a gaussian mixture model.
# 4. Fit the clouds:
# 4.1 If the position and weights of the clouds are unkonwn you have to use the fit_clouds routine
#    The states are unsortet and have to be sortet either by weight or position.
# 4.2 For a qubit, when only the weights of the clouds are unkown, you can use the fast fit_clouds_weight function
# 5. Plot the gaussian mixture model on a given axes.
#
# Check out the notebook for examples!


import numpy as np
from scipy.optimize import fsolve
from scipy import constants as pyc
from sklearn.mixture import GaussianMixture

from matplotlib import colors


class IQCloudAnalysis:

    def __init__(self):

        self.sweep_param = None
        self.data = None
        self.dist_avg = 0.0
        self.n_steps = 0

        # fit
        self.gmm = None
        self.covariance_type=None
        self.n_states = 0
        self.positions = None
        self.weights = None
        self.covariances = None
        self.precisions = None
        self.max_variance = None
        self.generalized_variance = None

        # After sorting
        self.theta = 0.0
        self.angle = None
        self.separation = None
        self.beta = None
        self.temp = None

        self.amplitude = None
        self.phase = None

        # plots
        self.fig = None
        self.ax = None


    #######  out of the box usage for the two qubit clouds ################

    def analyse_qubit_clouds(self, I, Q, fq=-1,
                             pos_init=None, weights_init=None, precisions_init=None):
        """
        This routine performs an IQ cloud analyis with the given gaussian mixture model and
        interprets the two most prominent states as the qubit system.
        The rotation, the angle and the separation of the qubit clouds is determined.
        When the qubit frequency is given the temperature is calculated.
        """

        # 1. load data
        I = I[:, np.newaxis]  # extend the sweep axis
        Q = Q[:, np.newaxis]
        self.set_IQ_data_sweep(I, Q)

        # 2. set up gaussian micture model
        self.set_up_gaussian_mixture_model(self.n_states, covariance_type=self.covariance_type,
                                           pos_init=pos_init, weights_init=weights_init, precisions_init=precisions_init)

        # 3. fit clouds
        self.fit_clouds()

        # 4. sort clouds
        self.sort_clouds_weights()

        # analyze qubit clouds
        step = 0

        # calc theta
        di = self.positions[step, 0, 0] - self.positions[step, 1, 0]
        dq = self.positions[step, 0, 1] - self.positions[step, 1, 1]
        distance = np.sqrt(di**2 + dq**2)
        self.theta = np.sign(dq) * np.arccos(di / distance)

        # calc separation and angle
        a = np.linalg.norm(self.positions[step, 0, :])
        b = np.linalg.norm(self.positions[step, 1, :])
        self.separation = distance / np.sum(np.sqrt(self.generalized_variance[0,:2]) )  # lower bound for the separation
        self.angle = np.arccos((a**2 + b**2 - distance**2) / (2 * a * b))

        # calc temperature in mK
        if fq > 0:
            self.temp = 1e3 * pyc.h * fq / (pyc.k * np.log(self.weights[step, 0] / self.weights[step, 1]))
        else:
            self.temp = -1


    ################ load and manipulate data  ##############

    def set_IQ_data_sweep(self, I, Q, sweep_param=None, dist_avg=-1):
        """ Load 2-dimensional IQ data in the form [avg, sweep]
            If needed scale the data with a given dist_avg
        """

        data = np.dstack((I, Q))
        self.data = np.moveaxis(data, 1, 0)
        self.n_steps = self.data.shape[0]

        if sweep_param is None:
            self.sweep_param = np.arange(self.n_steps)
        else:
            self.sweep_param = sweep_param

        # scale data around unity - important for convergence
        if dist_avg == -1:
            self.dist_avg = np.mean(np.sqrt(self.data[:, :, 0]**2 + self.data[:, :, 1]**2), axis=(0, 1))
        else:
            self.dist_avg = dist_avg
        self.data /= self.dist_avg


    def rotate_data(self, theta):

        data = np.empty_like(self.data)
        data[:, :, 0] = np.cos(theta) * self.data[:, :, 0] - np.sin(theta) * self.data[:, :, 1]
        data[:, :, 1] = np.sin(theta) * self.data[:, :, 0] + np.cos(theta) * self.data[:, :, 1]
        self.data = data


    ######## gaussian mixture routines ############

    def set_up_gaussian_mixture_model(self, n_states=2, covariance_type='spherical',
                                      pos_init=None, weights_init=None, precisions_init=None, tol=1e-3):

        self.n_states = n_states
        self.covariance_type = covariance_type
        self.gmm = GaussianMixture(self.n_states, covariance_type=covariance_type,
                                   means_init=pos_init, weights_init=weights_init, precisions_init=precisions_init, tol=tol)

    def calc_covariance_properties(self, step):

        generalized_variance = np.empty(self.n_states)

        if self.covariance_type == "spherical":
            max_variance = np.max(self.covariances[step])
            generalized_variance[:] = self.covariances[step]
        elif self.covariance_type == "tied":
            e = np.linalg.eigvalsh(self.covariances[step])
            max_variance = np.max(e)
            generalized_variance[:] = np.linalg.det(self.covariances[step])
        elif self.covariance_type == "diag":
            max_variance = np.max(self.covariances[step])
            generalized_variance[:] = self.covariances[step][:, 0]**2 + self.covariances[step][:, 1]**2
        elif self.covariance_type == "full":
            max_variance = 0.0
            for i in range(self.n_states):
                e = np.linalg.eigvalsh(self.covariances[step][i, :, :])
                if np.max(e) > max_variance:
                    max_variance = np.max(e)
                generalized_variance[i] = np.linalg.det(self.covariances[step][i, :, :])

        return generalized_variance, max_variance

    def fit_clouds(self):
        """
        Fit of the clouds with the given gaussian mixture model.
        The clouds are randomly numerated and have to be sorted later on
        TODO: include option to use warm start of GaussianMixture to speed up convergence (using previous fit result)
        TODO: it would be nice if one could also set the inits in this routine: means_init=None, weights_init=None, precisions_init=None
        """
        self.positions = np.zeros((self.n_steps, self.n_states, 2))
        self.weights = np.zeros((self.n_steps, self.n_states))
        self.covariances = np.zeros(self.n_steps, dtype=object)
        self.precisions = np.zeros(self.n_steps, dtype=object)
        self.generalized_variance = np.zeros((self.n_steps, self.n_states))
        self.max_variance = np.zeros(self.n_steps)
        self.separations = np.zeros(self.n_steps)

        for i in range(self.n_steps):

            self.gmm.fit(self.data[i])

            self.positions[i, :, :] = self.gmm.means_
            self.weights[i, :] = self.gmm.weights_
            self.covariances[i] = self.gmm.covariances_
            self.precisions[i] = self.gmm.precisions_
            self.generalized_variance[i], self.max_variance[i] = self.calc_covariance_properties(i)
            di = self.positions[i, 0, 0] - self.positions[i, 1, 0]
            dq = self.positions[i, 0, 1] - self.positions[i, 1, 1]
            distance = np.sqrt(di ** 2 + dq ** 2)
            self.separations[i] = distance / np.sum(np.sqrt(self.generalized_variance[i,:2]))


    def fit_clouds_weight(self, ref_pos, ref_covar):
        """ Maximum likelihood fit of the weights.
            Simple implementation only for 2 states possible.
            TODO: for more states a warm start could give similar results
        """

        self.positions = np.zeros((self.n_steps, self.n_states, 2))
        self.weights = np.zeros((self.n_steps, self.n_states))
        self.covariances = np.zeros(self.n_steps, dtype=object)
        self.precisions = np.zeros(self.n_steps, dtype=object)
        self.generalized_variance = np.zeros((self.n_steps, self.n_states))
        self.max_variance = np.zeros(self.n_steps)

        if self.covariance_type == "spherical":
            ref_precs = 1 / ref_covar
        elif self.covariance_type == "tied":
            ref_precs = np.linalg(ref_covar)
        elif self.covariance_type == "diag":
            ref_precs = 1 / ref_covar
        elif self.covariance_type == "full":
            ref_precs = np.empty_like(ref_covar)
            for i in range(self.n_states):
                ref_precs[i, :, :] = np.linalg.inv(ref_covar[i, :, :])

        for i in range(self.n_steps):

            self.positions[i, :, :] = ref_pos
            self.covariances[i] = ref_covar
            self.precisions[i] = ref_precs
            self.generalized_variance[i], self.max_variance[i] = self.calc_covariance_properties(i)

            if self.n_states == 1:
                self.weights[i, 0] = 1.0
            if self.n_states == 2:
                self.weights[i, :] = self.weights_fit(i)
            else:
                print("Fitting of specific parameters is not supported by scikit-learn."
                      "You can try fitting with a warm start. TODO: implement it!")


    def weights_fit(self, step):
        """ Fast maximum likelihood fit of the weights for two states.
            The position and the variance must be given
        """
        s1 = np.sqrt(self.generalized_variance[step, 0])
        s2 = np.sqrt(self.generalized_variance[step, 1])
        dist = 0.5 * self.calc_mahalanobis_dist(self.data[step], self.positions[step], self.precisions[step])

        e = s2 / s1 * np.exp(dist[:, 1] - dist[:, 0])
        c = (e + 1) / (e - 1)

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

                            # final numerical error of state population better than 0.5 * tol
        return 0.5 * (1 + delta), 0.5 * (1 - delta)


    def calc_mahalanobis_dist(self, data, positions, precisions):
        """
        Returns the squared mahalanobis distance
        """

        dist = np.empty((data.shape[0], self.n_states))

        for i in range(self.n_states):

            v = data - positions[i]
            if self.covariance_type == 'spherical':
                dist[:, i] = precisions[i] * np.einsum('ij,ij->i', v, v)
            elif self.covariance_type == 'tied':
                dist[:, i] = np.einsum('ij,ji->i', v, np.einsum('kj,ij->ki', precisions, v))
            elif self.covariance_type == 'diag':
                dist[:, i] = np.einsum('ij,ij->i', v, np.einsum('j,ij->ij', precisions[i], v))
            elif self.covariance_type == 'full':
                dist[:, i] = np.einsum('ij,ji->i', v, np.einsum('kj,ij->ki', precisions[i], v))

        return dist


    ####### different cloud sorting routines  ################

    def sort_clouds_positions(self, ref_pos=None):
        """ Sorts the states according to a reference positions.
            If ref_pos is None the first position of the sweep is chosen as reference.
        """
        if ref_pos is None:
            ref_pos = self.positions[0, :, :]

        label = np.zeros(self.n_states, dtype=int)

        for i in range(self.n_steps):
            for j in range(self.n_states):
                dist = (self.positions[i, j, 0] - ref_pos[:, 0])**2 + \
                       (self.positions[i, j, 1] - ref_pos[:, 1])**2

                label[j] = np.argmin(dist)

            self.positions[i, :, :] = self.positions[i, label, :]
            self.weights[i, :] = self.weights[i, label]
            if self.covariance_type != "tied":
                self.covariances[i][:] = self.covariances[i][label]
                self.precisions[i][:] = self.precisions[i][label]
            self.generalized_variance[i, :] = self.generalized_variance[i, label]


    def sort_clouds_weights(self):
        """ Sorts the states according to their weight
        """
        for i in range(self.n_steps):

            aw = np.argsort(self.weights[i, :])[::-1]
            self.positions[i, :, :] = self.positions[i, aw, :]
            self.weights[i, :] = self.weights[i, aw]
            if self.covariance_type != "tied":
                self.covariances[i][:] = self.covariances[i][aw]
                self.precisions[i][:] = self.precisions[i][aw]
            self.generalized_variance[i, :] = self.generalized_variance[i, aw]


    ###### cloud evaluation ##########

    def calc_amplitude_phase(self):

        self.amplitude = np.linalg.norm(self.positions[:, :, :], axis=2)
        self.phase = np.arctan2(self.positions[:, :, 1], self.positions[:, :, 0])

    def calc_cloud_distance(self, cloud_a, cloud_b):

        return np.linalg.norm(self.positions[:, cloud_b, :] - self.positions[:, cloud_a, :], axis=1)


    def calc_temperature(self, cloud_a, cloud_b, delta_freq):
        """
        Calculates the temperature from the weights for the
        corresponding frequencies of the states which must be given in units of Hz.
        If freq.size = n_states - 1 the zero ground state energy is automatically added.
        Consequently, for two states freq can also just be a number i.e. the frequency of the excited state
        """

        beta = np.log(self.weights[:, cloud_a] / self.weights[:, cloud_b]) / delta_freq

        self.temp = 1e3 * pyc.h / (pyc.k * beta)        # in mK
        self.beta = pyc.k * beta / pyc.h                # in 1 / K


    ###################### plotting #############################

    def set_axes(self, ax):
        self.ax = ax

    def plot_clouds(self, step=0, style="histogram", bin_size=0.015):

        x_range = [np.floor(np.min(self.data[step, :, 0]) / bin_size) * bin_size, np.ceil(np.max(self.data[step, :, 0]) / bin_size) * bin_size]
        y_range = [np.floor(np.min(self.data[step, :, 1]) / bin_size) * bin_size, np.ceil(np.max(self.data[step, :, 1]) / bin_size) * bin_size]
        bins_x = np.arange(x_range[0] - bin_size / 2, x_range[1] + bin_size, bin_size)
        bins_y = np.arange(y_range[0] - bin_size / 2, y_range[1] + bin_size, bin_size)

        im = None

        if style == "scatter":
            if self.data.shape[1] < 1e6:
                self.ax.scatter(self.data[step, :, 0], self.data[step, :, 1], 0.1)
            else:
                style = "histogram"
                print("More than 1e6 points - falling back on histogram!")

        if style == "histogram":

            H, _, _ = np.histogram2d(self.data[step, :, 0], self.data[step, :, 1], bins=[bins_x, bins_y])

            hmax = np.max(H)
            H[H < 1] = hmax + 1   # trick to get a white color for all zero entries

            im = self.ax.imshow(H.T, origin="lower", extent=(bins_x[0], bins_x[-1], bins_y[0], bins_y[-1]), cmap="terrain",
                      norm=colors.LogNorm(vmin=1, vmax=hmax), interpolation="none")

        # contour plot
        x = np.linspace(bins_x[0], bins_x[-1], 101)
        y = np.linspace(bins_y[0], bins_y[-1], 101)

        X, Y = np.meshgrid(x, y)

        iq = np.dstack((X, Y))
        iq = np.reshape(iq, (y.size * x.size, 2))
        dist = self.calc_mahalanobis_dist(iq, self.positions[step, :, :], self.precisions[step])
        dist = np.reshape(dist, (y.size, x.size, self.n_states))

        Z = np.zeros_like(X)
        for i in range(self.n_states):
            Z += self.weights[step, i] * np.exp(- 0.5 * dist[:, :, i]) / (2 * np.pi * np.sqrt(self.generalized_variance[step, i]))
        self.ax.contour(X, Y, np.log(Z))

        # TODO plot sigma areas of individual clouds
        # sigma areas of the individual states
        #s = np.linspace(0, 2 * np.pi, 101)
        #for i in range(self.n_states):
        #    self.ax.plot(self.positions[step, i, 0] + np.dot(np.cos(s), self.positions[step, i, 0] + np.sin(s))

        # plot origin and position of states
        # self.ax.plot(0.0, 0.0, 'r.')
        for i in range(self.n_states):
            self.ax.plot(self.positions[step, i, 0], self.positions[step, i, 1], 'k.')

        self.ax.set_xlim(bins_x[0], bins_x[-1])
        self.ax.set_ylim(bins_y[0], bins_y[-1])
        self.ax.axis("equal")

        return im


    def plot_weights(self):

        for i in range(self.n_states):
            self.ax.plot(self.sweep_param, self.weights[:, i], '.')







