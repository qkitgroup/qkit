import numpy as np

from qkit.analysis.circle_fit.circle_fit_2019.circuit import circuit
from qkit.measure.unified_measurements import AnalysisTypeAdapter, MeasurementTypeAdapter, DataView, DataViewSet, \
    DataReference


class CircleFitAnalysis(AnalysisTypeAdapter):
    """
    Perform circle fit analysis on a spectroscopy measurement.
    """

    def __init__(self, ports = 2):
        self._ports = ports

    def expected_structure(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> tuple[
        'MeasurementTypeAdapter.DataDescriptor', ...]:
        """
        We expect the synthesized circle (real and imag) and the fit parameters.
        """
        frequency_axis = parent_schema[0].axes
        return (
            MeasurementTypeAdapter.DataDescriptor("real", frequency_axis, "real", "data"),
            MeasurementTypeAdapter.DataDescriptor("imag", frequency_axis, "imag", "data"),
            MeasurementTypeAdapter.DataDescriptor("fit_real", frequency_axis, "mag", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("fit_imag", frequency_axis, "imag", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("fit_mag", frequency_axis, "mag", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("fit_phase", frequency_axis, "rad", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_c", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_c_abs", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_c_min", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_c_max", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_i", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_i_min", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_i_max", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_i_no_dia_corr", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("Q_l", (), "", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("a", (), "mag", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("alpha", (), "rad", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("delay", (), "s", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("delay_remaining", (), "s", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("f_res", (), "Hz", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("phi", (), "rad", "analysis"),
            MeasurementTypeAdapter.DataDescriptor("theta", (), "rad", "analysis"),
        )

    def default_views(self, parent_schema: tuple['MeasurementTypeAdapter.DataDescriptor', ...]) -> dict[
        str, "DataView"]:
        frequency = parent_schema[0].axes[0]
        parent_amp_name = [entry.name for entry in parent_schema if 'amp' in entry.name][0]
        parent_phase_name = [entry.name for entry in parent_schema if 'phase' in entry.name][0]
        return {
            "circle_fit": DataView(
                view_params={
                    "labels": ("real", "imag"),
                    "plot_style": 1,
                    "markersize": 5
                },
                view_sets=[
                    DataViewSet( # Real data
                        x_path=DataReference("real", category='analysis'),
                        y_path=DataReference("imag", category='analysis'),
                    ),
                    DataViewSet( # Fit result
                        x_path=DataReference("fit_real", category='analysis'),
                        y_path=DataReference("fit_imag", category='analysis')
                    )
                ]
            ),
            "phase_fit": DataView(
                view_params={
                    "labels": ("frequency", "phase"),
                    "plot_style": 1,
                    "markersize": 5
                },
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(frequency.name),
                        y_path=DataReference(parent_phase_name)
                    ),
                    DataViewSet(
                        x_path=DataReference(frequency.name),
                        y_path=DataReference("fit_phase", category='analysis')
                    )
                ]
            ),
            "mag_fit": DataView(
                view_params={
                    "labels": ("frequency", "mag"),
                    "plot_style": 1,
                    "markersize": 5
                },
                view_sets=[
                    DataViewSet(
                        x_path=DataReference(frequency.name),
                        y_path=DataReference(parent_amp_name)
                    ),
                    DataViewSet(
                        x_path=DataReference(frequency.name),
                        y_path=DataReference("fit_mag", category='analysis')
                    )
                ]
            )
        }

    def perform_analysis(self, data: tuple['MeasurementTypeAdapter.GeneratedData', ...]) -> tuple[
        'MeasurementTypeAdapter.GeneratedData', ...]:
        amp_data = [datum for datum in data if 'amp' in datum.descriptor.name][0]
        phase_data = [datum for datum in data if 'phase' in datum.descriptor.name][0]

        frequencies = amp_data.descriptor.axes[0].range
        amplitudes = amp_data.data
        phases = phase_data.data
        z_data = amplitudes * np.exp(1j * phases)

        # precompute for storage later.
        imag = np.imag(z_data)
        real = np.real(z_data)

        # Perform the fit
        fit = circuit(frequencies, z_data)
        fit.n_ports = self._ports
        fit.autofit()

        results = [
            real, imag, # Converted measured data
            fit.z_data_sim.real, fit.z_data_sim.imag, fit.z_data_sim.mag, fit.z_data_sim.phase, # Fitted data
            # The fit parameters
            # Quality factors
            fit.Qc, fit.absQc, fit.Qc_min, fit.Qc_max,
            fit.Qi, fit.Qi_min, fit.Qi_max, fit.Qi_no_dia_corr,
            fit.Ql,
            # Center parameters
            fit.a, fit.alpha,
            # Delay
            fit.delay, fit.delay_remaining,
            # Misc
            fit.fr,
            fit.phi, fit.theta,
        ]

        declared_shape = self.expected_structure(tuple(datum.descriptor for datum in data))
        return tuple(desc.with_data(data) for desc, data in zip(declared_shape, results))

