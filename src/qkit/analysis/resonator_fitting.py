import numpy as np
from abc import ABC, abstractmethod
import scipy.optimize as spopt
import scipy.ndimage
import logging
from qkit.storage.store import Data as qkitData
from qkit.storage.hdf_dataset import hdf_dataset

class ResonatorFitBase(ABC):
    """
    Defines the core functionality any fit function should offer, namely freq, amp & phase in, simulated freq, amp, phase + extracted data out. 
    Contrary to previous version, fit-functionality is completely decoupled from the h5 file format, this should be handled in the respective measurement script instead. 
    Complex IQ data + view should be created in measurement script by default as well. 

    extract_data dict contains information like f_res, Qc, etc. and its (final) keys should be static accessible for each fit function class overriding this base implementation.
    This allows preparing hdf datasets for them without them being calculated yet
    """
    def __init__(self):
        self.freq_fit: np.ndarray[float] = None
        self.amp_fit: np.ndarray[float] = None
        self.pha_fit: np.ndarray[float] = None
        self.extract_data: dict[str, float] = {}
        self.out_nop = 501 # number of points the output fits are plotted with

    @abstractmethod
    def do_fit(self, freq: np.ndarray[float] = [0, 1], amp: np.ndarray[float] = None, pha: np.ndarray[float] = None):
        logging.error("Somehow ran into abstract resonator fit base class fit-function")
        self.freq_fit = np.linspace(np.min(freq), np.max(freq), self.out_nop)
        self.amp_fit = np.ones(self.out_nop)
        self.pha_fit = np.zeros(self.out_nop)
        self.extract_data = {}
        return self


def autofit_file(file: qkitData | str, fit_func: ResonatorFitBase, f_min: float = None, f_max: float = None):
    # ensure file is qkit.storage.store.Data
    if type(file) == str:
        try:
            file = qkitData(file) # assume path
        except:
            logging.error("'{}' is not a valid path".format(file))
            raise AttributeError
    # check if file has freq, amp, phase
    try: 
        freq_data = np.array(file.data.frequency)
        amp_data = np.array(file.data.amplitude)
        pha_data = np.array(file.data.phase)
    except:
        logging.error("Could not access frequency, amplitude and/or phase. Is this really a VNA measurement?")
        raise AttributeError
    # do not allow overriding existing fits
    try: 
        dummy = file.analysis._fit_frequency
        logging.error("File already contains fit data. Please access and store everything manually.")
        raise ValueError
    except:
        pass
    # add frequency coordinate
    f_min = -np.inf if f_min is None else f_min
    f_max = np.inf if f_max is None else f_max
    selly = (freq_data >= f_min) & (freq_data <= f_max)
    file_freq_fit = file.add_coordinate("_fit_frequency", unit="Hz", folder="analysis")
    file_freq_fit.add(np.linspace(np.min(freq_data[selly]), np.max(freq_data[selly]), fit_func.out_nop))
    file_extracts: dict[str, hdf_dataset] = {}

    if len(amp_data.shape) == 1: # 1D measurement
        # add result datastores
        file_amp_fit = file.add_value_vector("_fit_amplitude", x=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_vector("_fit_phase", x=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_vector("_fit_real", x=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_vector("_fit_imag", x=file_freq_fit, unit="", folder="analysis")
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_coordinate("fit_" + key, folder="analysis")
        # actual fitting
        fit_func.do_fit(freq_data[selly], amp_data[selly], pha_data[selly])
        # fill entries
        file_amp_fit.append(fit_func.amp_fit)
        file_pha_fit.append(fit_func.pha_fit)
        file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
        file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
        for key, val in fit_func.extract_data.items():
            file_extracts[key].add(np.array([val]))
    
    elif len(amp_data.shape) == 2: # 2D measurement
        # add result datastores
        file_amp_fit = file.add_value_matrix("_fit_amplitude", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_matrix("_fit_phase", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_matrix("_fit_real", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_matrix("_fit_imag", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file_freq_fit, unit="", folder="analysis")
        buffer_extracts: dict[str, np.ndarray] = {}
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_value_vector("fit_" + key, x=file.get_dataset(file.data.amplitude.x_ds_url), folder="analysis")
            buffer_extracts[key] = np.full(file[file.data.amplitude.x_ds_url].shape[0], np.nan)
        for ix in range(amp_data.shape[0]):
            # actual fitting
            fit_func.do_fit(freq_data[selly], amp_data[ix, selly], pha_data[ix, selly])
            # fill entries
            file_amp_fit.append(fit_func.amp_fit)
            file_pha_fit.append(fit_func.pha_fit)
            file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
            file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
            for key, val in fit_func.extract_data.items():
                buffer_extracts[key][ix] = val
                file_extracts[key].append(buffer_extracts[key], reset=True)

    elif len(amp_data.shape) == 3: # 3D measurement
        # add result datastores
        file_amp_fit = file.add_value_box("_fit_amplitude", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="arb. unit", folder="analysis")
        file_pha_fit = file.add_value_box("_fit_phase", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="rad", folder="analysis")
        file_real_fit = file.add_value_box("_fit_real", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="", folder="analysis")
        file_imag_fit = file.add_value_box("_fit_imag", x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), z=file_freq_fit, unit="", folder="analysis")
        for key in fit_func.extract_data.keys():
            file_extracts[key] = file.add_value_matrix("fit_" + key, x=file.get_dataset(file.data.amplitude.x_ds_url), y=file.get_dataset(file.data.amplitude.y_ds_url), folder="analysis")
        buffer_extracts: dict[str, np.ndarray] = {}
        import itertools # alternative to nested loops that allows easier breaking when fill is reached
        for ix, iy in itertools.product(range(amp_data.shape[0]), range(amp_data.shape[1])):
            if iy == 0:
                for key in fit_func.extract_data.keys():
                     buffer_extracts[key] = np.full(file[file.data.amplitude.y_ds_url].shape[0], np.nan)
            # actual fitting
            fit_func.do_fit(freq_data[selly], amp_data[ix, iy, selly], pha_data[ix, iy, selly])
            # fill entries
            file_amp_fit.append(fit_func.amp_fit)
            file_pha_fit.append(fit_func.pha_fit)
            file_real_fit.append(fit_func.amp_fit*np.cos(fit_func.pha_fit))
            file_imag_fit.append(fit_func.amp_fit*np.sin(fit_func.pha_fit))
            for key, val in fit_func.extract_data.items():
                buffer_extracts[key][iy] = val
                file_extracts[key].append(buffer_extracts[key], reset=(iy != 0))
            if (ix + 1 == file.data.amplitude.fill[0]) & (iy + 1 == file.data.amplitude.fill[1]):
                # The measurement stopped somewhere in the middle of a xy-sweep, no more data to analyze
                break
            if iy + 1 == amp_data.shape[1]:
                file_amp_fit.next_matrix()
                file_pha_fit.next_matrix()
                file_real_fit.next_matrix()
                file_imag_fit.next_matrix()
    else:
        logging.error("What?")
        raise NotImplementedError()
    
    # add/update views
    file["/entry/views/IQ"].attrs.create("xy_1", "/entry/analysis0/_fit_real:/entry/analysis0/_fit_imag")
    file["/entry/views/IQ"].attrs.create("xy_1_filter", "None")
    file["/entry/views/IQ"].attrs.create("overlays", 1)
    file.add_view("AmplitudeFit", file.data.frequency, file.data.amplitude).add(file_freq_fit, file_amp_fit)
    file.add_view("PhaseFit", file.data.frequency, file.data.phase).add(file_freq_fit, file_pha_fit)


class CircleFit(ResonatorFitBase):
    def __init__(self, n_ports: int, fit_delay_max_iterations: int = 5, fixed_delay: float = None, isolation: int = 15, guesses: list[float] = None):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Qc": None, 
            #"Qc_err": None, 
            "Qc_no_dia_corr": None,
            "Qc_no_dia_corr_err": None,
            "Qc_max": None, 
            "Qc_min": None,
            "Qi": None, 
            "Qi_err": None, 
            "Qi_no_dia_corr": None,
            "Qi_no_dia_corr_err": None,
            "Qi_max": None, 
            "Qi_min": None,
            "Ql": None, 
            "Ql_err": None, 
            "a": None,
            "alpha": None,
            "chi_square": None, 
            "delay": None, 
            "delay_remaining": None,
            "fano_b": None, 
            "phi": None, 
            "phi_err": None, 
            "theta": None, 
        }
        # fit parameters
        self.n_ports = n_ports # 1: reflection port, 2: notch port
        self.fit_delay_max_iterations = fit_delay_max_iterations
        self.fixed_delay = fixed_delay
        self.isolation = isolation
        self.guesses = guesses # init guess (f_res, Ql, delay) for phase fit
    
    def do_fit(self, freq: np.ndarray[float], amp: np.ndarray[float], pha: np.ndarray[float]):
        z = amp*np.exp(1j*pha)
        # init with empty data
        self.freq_fit = np.linspace(np.min(freq), np.max(freq), self.out_nop)
        self.amp_fit = np.full(self.out_nop, np.nan)
        self.pha_fit = np.full(self.out_nop, np.nan)
        for key in self.extract_data.keys():
            self.extract_data[key] = np.nan
        """ helper functions"""
        _phase_centered = lambda f, fr, Ql, theta, delay=0: theta - 2*np.pi*delay*(f-fr) + 2.*np.arctan(2.*Ql*(1. - f/fr))
        _periodic_boundary = lambda angle: (angle + np.pi) % (2*np.pi) - np.pi
        Sij = lambda f, fr, Ql, Qc, phi=0, a=1, alpha=0, delay=0: a*np.exp(1j*(alpha-2*np.pi*f*delay)) * (1 - 2*Ql/(Qc*np.cos(phi)*np.exp(-1j*phi)*self.n_ports*(1 + 2j*Ql*(f/fr-1))))
        def _fit_circle(z_data: np.ndarray):
            """
            Analytical fit of a circle to  the scattering data z_data. Cf. Sebastian
            Probst: "Efficient and robust analysis of complex scattering data under
            noise in microwave resonators" (arXiv:1410.3365v2)
            """
            
            # Normalize circle to deal with comparable numbers
            x_norm = 0.5*(np.max(z_data.real) + np.min(z_data.real))
            y_norm = 0.5*(np.max(z_data.imag) + np.min(z_data.imag))
            z_data = z_data[:] - (x_norm + 1j*y_norm)
            amp_norm = np.max(np.abs(z_data))
            z_data = z_data / amp_norm
            
            # Calculate matrix of moments
            xi = z_data.real
            xi_sqr = xi*xi
            yi = z_data.imag
            yi_sqr = yi*yi
            zi = xi_sqr+yi_sqr
            Nd = float(len(xi))
            xi_sum = xi.sum()
            yi_sum = yi.sum()
            zi_sum = zi.sum()
            xiyi_sum = (xi*yi).sum()
            xizi_sum = (xi*zi).sum()
            yizi_sum = (yi*zi).sum()
            M =  np.array([
                [(zi*zi).sum(), xizi_sum, yizi_sum, zi_sum],
                [xizi_sum, xi_sqr.sum(), xiyi_sum, xi_sum],
                [yizi_sum, xiyi_sum, yi_sqr.sum(), yi_sum],
                [zi_sum, xi_sum, yi_sum, Nd]
            ])
        
            # Lets skip line breaking at 80 characters for a moment :D
            a0 = ((M[2][0]*M[3][2]-M[2][2]*M[3][0])*M[1][1]-M[1][2]*M[2][0]*M[3][1]-M[1][0]*M[2][1]*M[3][2]+M[1][0]*M[2][2]*M[3][1]+M[1][2]*M[2][1]*M[3][0])*M[0][3]+(M[0][2]*M[2][3]*M[3][0]-M[0][2]*M[2][0]*M[3][3]+M[0][0]*M[2][2]*M[3][3]-M[0][0]*M[2][3]*M[3][2])*M[1][1]+(M[0][1]*M[1][3]*M[3][0]-M[0][1]*M[1][0]*M[3][3]-M[0][0]*M[1][3]*M[3][1])*M[2][2]+(-M[0][1]*M[1][2]*M[2][3]-M[0][2]*M[1][3]*M[2][1])*M[3][0]+((M[2][3]*M[3][1]-M[2][1]*M[3][3])*M[1][2]+M[2][1]*M[3][2]*M[1][3])*M[0][0]+(M[1][0]*M[2][3]*M[3][2]+M[2][0]*(M[1][2]*M[3][3]-M[1][3]*M[3][2]))*M[0][1]+((M[2][1]*M[3][3]-M[2][3]*M[3][1])*M[1][0]+M[1][3]*M[2][0]*M[3][1])*M[0][2]
            a1 = (((M[3][0]-2.*M[2][2])*M[1][1]-M[1][0]*M[3][1]+M[2][2]*M[3][0]+2.*M[1][2]*M[2][1]-M[2][0]*M[3][2])*M[0][3]+(2.*M[2][0]*M[3][2]-M[0][0]*M[3][3]-2.*M[2][2]*M[3][0]+2.*M[0][2]*M[2][3])*M[1][1]+(-M[0][0]*M[3][3]+2.*M[0][1]*M[1][3]+2.*M[1][0]*M[3][1])*M[2][2]+(-M[0][1]*M[1][3]+2.*M[1][2]*M[2][1]-M[0][2]*M[2][3])*M[3][0]+(M[1][3]*M[3][1]+M[2][3]*M[3][2])*M[0][0]+(M[1][0]*M[3][3]-2.*M[1][2]*M[2][3])*M[0][1]+(M[2][0]*M[3][3]-2.*M[1][3]*M[2][1])*M[0][2]-2.*M[1][2]*M[2][0]*M[3][1]-2.*M[1][0]*M[2][1]*M[3][2])
            a2 = ((2.*M[1][1]-M[3][0]+2.*M[2][2])*M[0][3]+(2.*M[3][0]-4.*M[2][2])*M[1][1]-2.*M[2][0]*M[3][2]+2.*M[2][2]*M[3][0]+M[0][0]*M[3][3]+4.*M[1][2]*M[2][1]-2.*M[0][1]*M[1][3]-2.*M[1][0]*M[3][1]-2.*M[0][2]*M[2][3])
            a3 = (-2.*M[3][0]+4.*M[1][1]+4.*M[2][2]-2.*M[0][3])
            a4 = -4.
        
            def char_pol(x):
                return a0 + a1*x + a2*x**2 + a3*x**3 + a4*x**4
        
            def d_char_pol(x):
                return a1 + 2*a2*x + 3*a3*x**2 + 4*a4*x**3
        
            eta = spopt.newton(char_pol, 0., fprime=d_char_pol)
        
            M[3][0] = M[3][0] + 2*eta
            M[0][3] = M[0][3] + 2*eta
            M[1][1] = M[1][1] - eta
            M[2][2] = M[2][2] - eta
            
            U,s,Vt = np.linalg.svd(M)
            A_vec = Vt[np.argmin(s),:]
        
            xc = -A_vec[1]/(2.*A_vec[0])
            yc = -A_vec[2]/(2.*A_vec[0])
            # The term *sqrt term corrects for the constraint, because it may be
            # altered due to numerical inaccuracies during calculation
            r0 = 1./(2.*np.absolute(A_vec[0]))*np.sqrt(
                A_vec[1]*A_vec[1]+A_vec[2]*A_vec[2]-4.*A_vec[0]*A_vec[3]
            )

            return xc*amp_norm+x_norm, yc*amp_norm+y_norm, r0*amp_norm
        def _fit_phase(z_data: np.ndarray, guesses = self.guesses):
            """
            Fits the phase response of a strongly overcoupled (Qi >> Qc) resonator
            in reflection which corresponds to a circle centered around the origin
            (cf. phase_centered()).

            inputs:
            - z_data: Scattering data of which the phase should be fit. Data must be
                    distributed around origin ("circle-like").
            - guesses (opt.): If not given, initial guesses for the fit parameters
                            will be determined. If given, should contain useful
                            guesses for fit parameters as a tuple (fr, Ql, delay)

            outputs:
            - fr: Resonance frequency
            - Ql: Loaded quality factor
            - theta: Offset phase
            - delay: Time delay between output and input signal leading to linearly
                    frequency dependent phase shift
            """
            phase = np.unwrap(np.angle(z_data))
            
            # For centered circle roll-off should be close to 2pi. If not warn user.
            if np.max(phase) - np.min(phase) <= 2*np.pi/4:
                logging.warning(
                    "Data does not cover a full circle (only {:.1f}".format(
                        np.max(phase) - np.min(phase)
                    )
                +" rad). Increase the frequency span around the resonance?"
                )
                roll_off = np.max(phase) - np.min(phase)
            elif np.max(phase) - np.min(phase) <= 2*np.pi*4/5:
                logging.debug(
                    "Data does not cover a full circle (only {:.1f}".format(
                        np.max(phase) - np.min(phase)
                    )
                +" rad). Increase the frequency span around the resonance?"
                )
                roll_off = np.max(phase) - np.min(phase)
            else:
                roll_off = 2*np.pi
            
            # Set useful starting parameters
            if guesses is None:
                # Use maximum of derivative of phase as guess for fr
                phase_smooth = scipy.ndimage.gaussian_filter1d(phase, 30)
                phase_derivative = np.gradient(phase_smooth)
                fr_guess = freq[np.argmax(np.abs(phase_derivative))]
                Ql_guess = 2*fr_guess / (freq[-1] - freq[0])
                # Estimate delay from background slope of phase (substract roll-off)
                slope = phase[-1] - phase[0] + roll_off
                delay_guess = -slope / (2*np.pi*(freq[-1]-freq[0]))
            else:
                fr_guess, Ql_guess, delay_guess = guesses
            # This one seems stable and we do not need a manual guess for it
            theta_guess = 0.5*(np.mean(phase[:5]) + np.mean(phase[-5:]))
            
            # Fit model with less parameters first to improve stability of fit
            
            def residuals_Ql(params):
                Ql, = params
                return residuals_full((fr_guess, Ql, theta_guess, delay_guess))
            def residuals_fr_theta(params):
                fr, theta = params
                return residuals_full((fr, Ql_guess, theta, delay_guess))
            def residuals_delay(params):
                delay, = params
                return residuals_full((fr_guess, Ql_guess, theta_guess, delay))
            def residuals_fr_Ql(params):
                fr, Ql = params
                return residuals_full((fr, Ql, theta_guess, delay_guess))
            def residuals_full(params):
                return np.pi - np.abs(np.pi - np.abs(phase - _phase_centered(freq, *params)))

            p_final = spopt.leastsq(residuals_Ql, [Ql_guess])
            Ql_guess, = p_final[0]
            p_final = spopt.leastsq(residuals_fr_theta, [fr_guess, theta_guess])
            fr_guess, theta_guess = p_final[0]
            p_final = spopt.leastsq(residuals_delay, [delay_guess])
            delay_guess, = p_final[0]
            p_final = spopt.leastsq(residuals_fr_Ql, [fr_guess, Ql_guess])
            fr_guess, Ql_guess = p_final[0]
            p_final = spopt.leastsq(residuals_full, [fr_guess, Ql_guess, theta_guess, delay_guess])
            
            return p_final[0]      

        """delay"""
        if self.fixed_delay is not None:
            delay = self.fixed_delay
        else:
            xc, yc, r0 = _fit_circle(z)
            z_data = z - complex(xc, yc)
            fr, Ql, theta, delay = _fit_phase(z_data)
            delay *= 0.05

            for i in range(self.fit_delay_max_iterations):
                # Translate new best fit data to origin
                z_data = z * np.exp(2j*np.pi*delay*freq)
                xc, yc, r0 = _fit_circle(z_data)
                z_data -= complex(xc, yc)
                
                # Find correction to current delay
                guesses = (fr, Ql, 5e-11)
                fr, Ql, theta, delay_corr = _fit_phase(z_data, guesses)
                
                # Stop if correction would be smaller than "measurable"
                phase_fit = _phase_centered(freq, fr, Ql, theta, delay_corr)
                residuals = np.unwrap(np.angle(z_data)) - phase_fit
                if 2*np.pi*(np.max(freq) - np.min(freq))*delay_corr <= np.std(residuals):
                    break
                
                # Avoid overcorrection that makes procedure switch between positive
                # and negative delays
                if delay_corr*delay < 0: # different sign -> be careful
                    if abs(delay_corr) > abs(delay):
                        delay *= 0.5
                    else:
                        delay += 0.1*np.sign(delay_corr)*5e-11
                else: # same direction -> can converge faster
                    if abs(delay_corr) >= 1e-8:
                        delay += min(delay_corr, delay)
                    elif abs(delay_corr) >= 1e-9:
                        delay *= 1.1
                    else:
                        delay += delay_corr
            
            if 2*np.pi*(freq[-1]-freq[0])*delay_corr > np.std(residuals):
                logging.debug("Delay could not be fit properly!")

        self.extract_data["delay"] = delay

        """calibrate"""
        z_data = z*np.exp(2j*np.pi*delay*freq) # correct delay
        xc, yc, r0 = _fit_circle(z_data)
        z_data -= complex(xc, yc)
        
        # Find off-resonant point by fitting offset phase
        # (centered circle corresponds to lossless resonator in reflection)
        fr, Ql, theta, delay_remaining = _fit_phase(z_data)
        theta = _periodic_boundary(theta)
        beta = _periodic_boundary(theta - np.pi)
        offrespoint = complex(xc, yc) + r0*np.exp(1j*beta)
        a = np.absolute(offrespoint)
        alpha = np.angle(offrespoint)
        phi = _periodic_boundary(beta - alpha)
        
        r0 /= a
        
        # Store results in dictionary 
        self.extract_data["delay_remaining"] = delay_remaining
        self.extract_data["a"] = a
        self.extract_data["alpha"] = alpha
        self.extract_data["theta"] = theta
        self.extract_data["phi"] = phi
        self.extract_data["f_res"] = fr
        self.extract_data["Ql"] = Ql

        """normalize"""
        z_norm = z/a*np.exp(1j*(-alpha + 2.*np.pi*delay*freq))

        """extract Qs"""
        absQc = Ql / (self.n_ports*r0)
        # For Qc, take real part of 1/(complex Qc) (diameter correction method)
        Qc = absQc / np.cos(phi)
        Qi = 1/(1/Ql - 1/Qc)
        Qi_no_dia_corr = 1/(1/Ql - 1/absQc)

        self.extract_data["Qc"] = Qc
        self.extract_data["Qc_no_dia_corr"] = absQc
        self.extract_data["Qi"] = Qi
        self.extract_data["Qi_no_dia_corr"] = Qi_no_dia_corr

        """errors"""
        residuals = z_norm - Sij(freq, fr, Ql, Qc, phi)
        chi = np.abs(residuals)
        # Unit vectors pointing in the correct directions for the derivative
        directions = residuals / chi
        # Prepare for fast construction of Jacobian
        conj_directions = np.conj(directions) 
    
        # Construct transpose of Jacobian matrix
        Jt = np.array([
            np.real(-4j*Ql**2*np.exp(1j*phi)*freq / (self.n_ports * absQc*(fr+2j*Ql*(freq-fr))**2)*conj_directions),
            np.real(-2*np.exp(1j*phi) / (self.n_ports * absQc*(1+2j*Ql*(freq/fr-1))**2)*conj_directions),
            np.real(2*Ql*np.exp(1j*phi) / (self.n_ports * absQc**2 * (1+2j*Ql*(freq/fr-1)))*conj_directions),
            np.real(-2j*Ql*np.exp(1j*phi) / (self.n_ports * absQc * (1.+2j*Ql*(freq/fr-1)))*conj_directions)
        ])
        A = np.dot(Jt, np.transpose(Jt))
        # 4 fit parameters reduce degrees of freedom for reduced chi square
        chi_square = 1/float(len(freq)-4) * np.sum(chi**2)
        try:
            cov = np.linalg.inv(A)*chi_square
        except:
            logging.warning("Error calculation failed!")
            cov = None
    
        if cov is not None:
            fr_err, Ql_err, absQc_err, phi_err = np.sqrt(np.diag(cov))
            # Calculate error of Qi with error propagation
            # without diameter correction
            dQl = 1/((1/Ql - 1/absQc) * Ql)**2
            dabsQc = -1/((1/Ql - 1/absQc) * absQc)**2
            Qi_no_dia_corr_err = np.sqrt(dQl**2*cov[1][1] + dabsQc**2*cov[2][2] + 2.*dQl*dabsQc*cov[1][2])
            # with diameter correction
            dQl = 1/((1/Ql - 1/Qc) * Ql)**2
            dabsQc = -np.cos(phi) / ((1/Ql - 1/Qc) * absQc)**2
            dphi = -np.sin(phi) / ((1/Ql - 1/Qc)**2 * absQc)
            Qi_err = np.sqrt(dQl**2*cov[1][1] + dabsQc**2*cov[2][2] + dphi**2*cov[3][3] + 2*(dQl*dabsQc*cov[1][2]+ dQl*dphi*cov[1][3]+ dabsQc*dphi*cov[2][3]))

            self.extract_data["f_res_err"] = fr_err
            self.extract_data["Ql_err"] = Ql_err
            self.extract_data["Qc_no_dia_corr_err"] = absQc_err
            self.extract_data["phi_err"] = phi_err
            self.extract_data["Qi_err"] = Qi_err
            self.extract_data["Qi_no_dia_corr_err"] = Qi_no_dia_corr_err
            self.extract_data["chi_square"] = chi_square

        """calc fano range"""
        b = 10**(-self.isolation/20)
        b = b / (1 - b)
        
        if np.sin(phi) > b:
            logging.warning("Measurement cannot be explained with assumed Fano leakage!")
        
        # Calculate error on radius of circle
        R_mid = r0 * np.cos(phi)
        R_err = r0 * np.sqrt(b**2 - np.sin(phi)**2)
        R_min = R_mid - R_err
        R_max = R_mid + R_err
        
        # Convert to ranges of quality factors
        Qc_min = Ql / (self.n_ports*R_max)
        Qc_max = Ql / (self.n_ports*R_min)
        Qi_min = Ql / (1 - self.n_ports*R_min)
        Qi_max = Ql / (1 - self.n_ports*R_max)
        
        # Handle unphysical results
        if R_max >= 1/self.n_ports:
            Qi_max = np.nan
        
        self.extract_data["Qc_min"] = Qc_min
        self.extract_data["Qc_max"] = Qc_max
        self.extract_data["Qi_min"] = Qi_min
        self.extract_data["Qi_max"] = Qi_max
        self.extract_data["fano_b"] = b

        """model data"""
        z_fit = Sij(self.freq_fit, fr, Ql, Qc, phi, a, alpha, delay)
        self.amp_fit = np.abs(z_fit)
        self.pha_fit = np.angle(z_fit)

        return self
    

class LorentzianFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Ql": None, 
            "Ql_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt it yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Ql"] = 1 
        self.extract_data["Ql_err"] = 0.5
        return super().do_fit(freq, amp, pha)
        """
        Old implementation:

        def residuals(p,x,y):
            f0,k,a,offs=p
            err = y-(a/(1+4*((x-f0)/k)**2)+offs)
            return err
        
        self._fit_all = fit_all

        if not self._datasets_loaded:
            self._get_datasets()

        self._update_data()
        self._prepare_f_range(f_min,f_max)
        if self._first_lorentzian:
            self._prepare_lorentzian()
            self._first_lorentzian=False

        '''
        fit_amplitude is always 2dim np array.
        for 1dim data, shape: (1, # fit frequency points)
        for 2dim data, shape: (# amplitude slices (i.e. power values in scan), # fit frequency points)
        '''
        if not self._fit_all:
            self._get_last_amp_trace()

        for amplitudes in self._fit_amplitude:
            amplitudes = np.absolute(amplitudes)
            amplitudes_sq = amplitudes**2
            '''extract starting parameter for lorentzian from data'''
            s_offs = np.mean(np.array([amplitudes_sq[:int(np.size(amplitudes_sq)*.1)], amplitudes_sq[int(np.size(amplitudes_sq)-int(np.size(amplitudes_sq)*.1)):]]))
            '''offset is calculated from the first and last 10% of the data to improve fitting on tight windows'''

            if np.abs(np.max(amplitudes_sq)-np.mean(amplitudes_sq)) > np.abs(np.min(amplitudes_sq)-np.mean(amplitudes_sq)):
                '''peak is expected'''
                s_a = np.abs((np.max(amplitudes_sq)-np.mean(amplitudes_sq)))
                s_f0 = self._fit_frequency[np.argmax(amplitudes_sq)]
            else:
                '''dip is expected'''
                s_a = -np.abs((np.min(amplitudes_sq)-np.mean(amplitudes_sq)))
                s_f0 = self._fit_frequency[np.argmin(amplitudes_sq)]

            '''estimate peak/dip width'''
            mid = s_offs + .5*s_a #estimated mid region between base line and peak/dip
            m = [] #mid points
            for i in range(len(amplitudes_sq)-1):
                if np.sign(amplitudes_sq[i]-mid) != np.sign(amplitudes_sq[i+1]-mid):#mid level crossing
                    m.append(i)
            if len(m)>1:
                s_k = self._fit_frequency[m[-1]]-self._fit_frequency[m[0]]
            else:
                s_k = .15*(self._fit_frequency[-1]-self._fit_frequency[0]) #try 15% of window
            p0=[s_f0, s_k, s_a, s_offs]
            try:
                fit = leastsq(residuals,p0,args=(self._fit_frequency,amplitudes_sq))
            except:
                self._lrnz_amp_gen.append(np.array([np.nan for f in self._fit_frequency]))
                self._lrnz_f0.append(np.nan)
                self._lrnz_k.append(np.nan)
                self._lrnz_a.append(np.nan)
                self._lrnz_offs.append(np.nan)
                self._lrnz_Ql.append(np.nan)
                self._lrnz_chi2_fit.append(np.nan)
            else:
                popt=fit[0]
                chi2 = self._lorentzian_fit_chi2(popt,amplitudes_sq)
                self._lrnz_amp_gen.append(np.sqrt(np.array(self._lorentzian_from_fit(popt))))
                self._lrnz_f0.append(float(popt[0]))
                self._lrnz_k.append(float(np.fabs(float(popt[1]))))
                self._lrnz_a.append(float(popt[2]))
                self._lrnz_offs.append(float(popt[3]))
                self._lrnz_Ql.append(float(float(popt[0])/np.fabs(float(popt[1]))))
                self._lrnz_chi2_fit.append(float(chi2))
        def _lorentzian_from_fit(self,fit):
            return fit[2] / (1 + (4*((self._fit_frequency-fit[0])/fit[1]) ** 2)) + fit[3]

        def _lorentzian_fit_chi2(self, fit, amplitudes_sq):
            chi2 = np.sum((self._lorentzian_from_fit(fit)-amplitudes_sq)**2) / (len(amplitudes_sq)-len(fit))
            return chi2
        """


class SkewedLorentzianFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Ql": None, 
            "Ql_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt it yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Qc"] = 1 
        self.extract_data["Qc_err"] = 0.5
        return super().do_fit(freq, amp, pha)
        """
        Old implementation:

                '''
        def residuals(p,x,y):
            A2, A4, Qr = p
            err = y -(A1a+A2*(x-fra)+(A3a+A4*(x-fra))/(1.+4.*Qr**2*((x-fra)/fra)**2))
            return err
        def residuals2(p,x,y):
            A1, A2, A3, A4, fr, Qr = p
            err = y -(A1+A2*(x-fr)+(A3+A4*(x-fr))/(1.+4.*Qr**2*((x-fr)/fr)**2))
            return err

        self._fit_all = fit_all

        if not self._datasets_loaded:
            self._get_datasets()
        self._update_data()

        self._prepare_f_range(f_min,f_max)
        if self._first_skewed_lorentzian:
            self._prepare_skewed_lorentzian()
            self._first_skewed_lorentzian = False

        '''
        fit_amplitude is always 2dim np array.
        for 1dim data, shape: (1, # fit frequency points)
        for 2dim data, shape: (# amplitude slices (i.e. power values in scan), # fit frequency points)
        '''
        if not self._fit_all:
            self._get_last_amp_trace()

        for amplitudes in self._fit_amplitude:
            "fits a skewed lorenzian to reflection amplitudes of a resonator"
            # prefilter the data
            amplitudes = self._pre_filter_data(amplitudes)

            amplitudes = np.absolute(amplitudes)
            amplitudes_sq = amplitudes**2

            A1a = np.minimum(amplitudes_sq[0],amplitudes_sq[-1])
            A3a = -np.max(amplitudes_sq)
            fra = self._fit_frequency[np.argmin(amplitudes_sq)]

            p0 = [0., 0., 1e3]

            try:
                p_final = leastsq(residuals,p0,args=(self._fit_frequency,amplitudes_sq))
                A2a, A4a, Qra = p_final[0]

                p0 = [A1a, A2a , A3a, A4a, fra, Qra]
                p_final = leastsq(residuals2,p0,args=(self._fit_frequency,amplitudes_sq))
                popt=p_final[0]
            except:
                self._skwd_amp_gen.append(np.array([np.nan for f in self._fit_frequency]))
                self._skwd_f0.append(np.nan)
                self._skwd_a1.append(np.nan)
                self._skwd_a2.append(np.nan)
                self._skwd_a3.append(np.nan)
                self._skwd_a4.append(np.nan)
                self._skwd_Qr.append(np.nan)
                self._skwd_chi2_fit.append(np.nan)
            else:
                chi2 = self._skewed_fit_chi2(popt,amplitudes_sq)
                amp_gen = np.sqrt(np.array(self._skewed_from_fit(popt)))

                self._skwd_amp_gen.append(amp_gen)
                self._skwd_f0.append(float(popt[4]))
                self._skwd_a1.append(float(popt[0]))
                self._skwd_a2.append(float(popt[1]))
                self._skwd_a3.append(float(popt[2]))
                self._skwd_a4.append(float(popt[3]))
                self._skwd_Qr.append(float(popt[5]))
                self._skwd_chi2_fit.append(float(chi2))

            self._skwd_Qi.append(self._skewed_estimate_Qi(popt))
        
        
        def _skewed_fit_chi2(self, fit, amplitudes_sq):
            chi2 = np.sum((self._skewed_from_fit(fit)-amplitudes_sq)**2) / (len(amplitudes_sq)-len(fit))
            return chi2

        def _skewed_from_fit(self,p):
            A1, A2, A3, A4, fr, Qr = p
            return A1+A2*(self._fit_frequency-fr)+(A3+A4*(self._fit_frequency-fr))/(1.+4.*Qr**2*((self._fit_frequency-fr)/fr)**2)

        def _skewed_estimate_Qi(self,p):

            #this is a very clumsy numerical estimate of the Qi factor based on the +3dB method.#
            A1, A2, A3, A4, fr, Qr = p
            def skewed_from_fit(p,f):
                A1, A2, A3, A4, fr, Qr = p
                return A1+A2*(f-fr)+(A3+A4*(f-fr))/(1.+4.*Qr**2*((f-fr)/fr)**2)

            #df = fr/(Qr*10000)
            fmax = fr+fr/Qr
            fs = np.linspace(fr,fmax,1000,dtype=np.float64)
            Amin = skewed_from_fit(p,fr)
            #print("---")
            #print("Amin, 2*Amin",Amin, 2*Amin)

            for f in fs:
                A = skewed_from_fit(p,f)
                #print(A, f)
                if A>2*Amin:
                    break
            qi = fr/(2*(f-fr))
            #print("f, A, fr/2*(f-fr)", f,A, qi)

            return float(qi)
        """


class FanoFit(ResonatorFitBase):
    def __init__(self):
        super().__init__()
        self.extract_data = {
            "f_res": None, 
            "f_res_err": None, 
            "Qc": None, 
            "Qc_err": None, 
            # TODO
        }

    def do_fit(self, freq, amp, pha):
        # TODO 
        logging.error("Lorentzian Fit not yet implemented. Feel free to adapt it yourself based on old resonator class")
        self.extract_data["f_res"] = 1 
        self.extract_data["f_res_err"] = 0.5
        self.extract_data["Qc"] = 1 
        self.extract_data["Qc_err"] = 0.5
        return super().do_fit(freq, amp, pha)
        """
        Old implementation:

        
        self._fit_all = fit_all
        if not self._datasets_loaded:
            self._get_datasets()
        self._update_data()
        self._prepare_f_range(f_min,f_max)
        if self._first_fano:
            self._prepare_fano()
            self._first_fano = False

        '''
        fit_amplitude is always 2dim np array.
        for 1dim data, shape: (1, # fit frequency points)
        for 2dim data, shape: (# amplitude slices (i.e. power values in scan), # fit frequency points)
        '''
        if not self._fit_all:
            self._get_last_amp_trace()

        for amplitudes in self._fit_amplitude:
            amplitude_sq = (np.absolute(amplitudes))**2
            try:
                fit = self._do_fit_fano(amplitude_sq)
                amplitudes_gen = self._fano_reflection_from_fit(fit)

                '''calculate the chi2 of fit and data'''
                chi2 = self._fano_fit_chi2(fit, amplitude_sq)

            except:
                self._fano_amp_gen.append(np.array([np.nan for f in self._fit_frequency]))
                self._fano_q_fit.append(np.nan)
                self._fano_bw_fit.append(np.nan)
                self._fano_fr_fit.append(np.nan)
                self._fano_a_fit.append(np.nan)
                self._fano_chi2_fit.append(np.nan)
                self._fano_Ql_fit.append(np.nan)
                self._fano_Q0_fit.append(np.nan)

            else:
                ''' save the fitted data to the hdf_file'''
                self._fano_amp_gen.append(np.sqrt(np.absolute(amplitudes_gen)))
                self._fano_q_fit.append(float(fit[0]))
                self._fano_bw_fit.append(float(fit[1]))
                self._fano_fr_fit.append(float(fit[2]))
                self._fano_a_fit.append(float(fit[3]))
                self._fano_chi2_fit.append(float(chi2))
                self._fano_Ql_fit.append(float(fit[2])/float(fit[1]))
                q0=self._fano_fit_q0(np.sqrt(np.absolute(amplitudes_gen)),float(fit[2]))
                self._fano_Q0_fit.append(q0)

        def _fano_reflection(self,f,q,bw,fr,a=1,b=1):
            '''
            evaluates the fano function in reflection at the
            frequency f
            with
            resonator frequency fr
            attenuation a (linear)
            fano-factor q
            bandwidth bw
            '''
            return a*(1 - self._fano_transmission(f,q,bw,fr))

        def _fano_transmission(self,f,q,bw,fr,a=1,b=1):
            '''
            evaluates the normalized transmission fano function at the
            frequency f
            with
            resonator frequency fr
            attenuation a (linear)
            fano-factor q
            bandwidth bw
            '''
            F = 2*(f-fr)/bw
            return ( 1/(1+q**2) * (F+q)**2 / (F**2+1))

        def _do_fit_fano(self, amplitudes_sq):
            # initial guess
            bw = 1e6
            q  = 1 #np.sqrt(1-amplitudes_sq).min()  # 1-Amp_sq = 1-1+q^2  => A_min = q
            fr = self._fit_frequency[np.argmin(amplitudes_sq)]
            a  = amplitudes_sq.max()

            p0 = [q, bw, fr, a]

            def fano_residuals(p,frequency,amplitude_sq):
                q, bw, fr, a = p
                err = amplitude_sq-self._fano_reflection(frequency,q,bw,fr=fr,a=a)
                return err

            p_fit = leastsq(fano_residuals,p0,args=(self._fit_frequency,np.array(amplitudes_sq)))
            #print(("q:%g bw:%g fr:%g a:%g")% (p_fit[0][0],p_fit[0][1],p_fit[0][2],p_fit[0][3]))
            return p_fit[0]

        def _fano_reflection_from_fit(self,fit):
            return self._fano_reflection(self._fit_frequency,fit[0],fit[1],fit[2],fit[3])

        def _fano_fit_chi2(self,fit,amplitudes_sq):
            chi2 = np.sum((self._fano_reflection_from_fit(fit)-amplitudes_sq)**2) / (len(amplitudes_sq)-len(fit))
            return chi2

        def _fano_fit_q0(self,amp_gen,fr):
            '''
            calculates q0 from 3dB bandwidth above minimum in fit function
            '''
            amp_3dB=10*np.log10((np.min(amp_gen)))+3
            amp_3dB_lin=10**(amp_3dB/10)
            f_3dB=[]
            for i in range(len(amp_gen)-1):
                if np.sign(amp_gen[i]-amp_3dB_lin) != np.sign(amp_gen[i+1]-amp_3dB_lin):#crossing@amp_3dB
                    f_3dB.append(self._fit_frequency[i])
            if len(f_3dB)>1:
                q0 = fr/(f_3dB[1]-f_3dB[0])
                return float(q0)
            else: return np.nan
        """
    

FitNames: dict[str, ResonatorFitBase] = {
    'lorentzian': LorentzianFit, 
    'skewed_lorentzian': SkewedLorentzianFit, 
    'circle_fit_reflection': CircleFit, 
    'circle_fit_notch': CircleFit,
    'fano': FanoFit, 
}