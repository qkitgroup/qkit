from typing import Optional

from laboneq import dsl
from laboneq.simple import *
from laboneq.core.types.enums import SectionAlignment
from laboneq.dsl.quantum import QPU
from laboneq.dsl import SweepParameter
from laboneq.dsl.experiment import Experiment
from laboneq.workflow.typing import QuantumElements
from laboneq_applications.core import validation
from laboneq_applications.experiments.options import TuneupExperimentOptions
from laboneq_applications.typing import *


### Rabi Experiment
@dsl.qubit_experiment
def create_experiment_rabi(
    qpu: QPU,
    qubits: QuantumElements,
    lengths: QubitSweepPoints,
    options: Optional[TuneupExperimentOptions]=None,
) -> Experiment:
    opts = TuneupExperimentOptions() if options is None else options
    qubits, lengths = validation.validate_and_convert_qubits_sweeps(qubits, lengths)

    time_sweep_pars = [
        SweepParameter(f"time_{q.uid}", q_lengths, axis_name=f"{q.uid}")
        for q, q_lengths in zip(qubits, lengths)
    ]

    max_measure_section_length = qpu.measure_section_length(qubits)
    qop = qpu.quantum_operations

    with dsl.acquire_loop_rt(
        count=opts.count,
        averaging_mode=opts.averaging_mode,
        acquisition_type=opts.acquisition_type,
        repetition_mode=opts.repetition_mode,
        repetition_time=opts.repetition_time,
        reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        with dsl.sweep(
            name="rabi_length_sweep",
            parameter=time_sweep_pars,
            alignment=SectionAlignment.RIGHT,  # keep readout time fixed
        ):
            # 1) Drive (length sweep) — inherit amplitude & shape from q.parameters
            with dsl.section(uid="main_excitation", alignment=SectionAlignment.LEFT):
                for q, qtimes in zip(qubits, time_sweep_pars):
                    qop.x180(q, length=qtimes, transition=opts.transition)  # <-- removed amplitude=1.0

            # 2) Measure (fixed section length)
            with dsl.section(uid="main_measure", alignment=SectionAlignment.LEFT):
                for q in qubits:
                    msec = qop.measure(q, dsl.handles.result_handle(q.uid))
                    msec.length = max_measure_section_length

            # 3) Reset (separate section, so it doesn’t collide with measure length)
            with dsl.section(uid="reset", alignment=SectionAlignment.LEFT):
                for q in qubits:
                    qop.passive_reset(q)


### Rabi with detuning Experiment
@dsl.qubit_experiment
def create_experiment_rabi_detuned(
        qpu: QPU,
        qubits: QuantumElements,
        lengths: QubitSweepPoints,
        detunings: QubitSweepPoints,
        options: Optional[TuneupExperimentOptions] = None,
) -> Experiment:
    opts = TuneupExperimentOptions() if options is None else options
    qubits, lengths = validation.validate_and_convert_qubits_sweeps(qubits, lengths)
    _, detunings = validation.validate_and_convert_qubits_sweeps(qubits, detunings)

    time_sweep_pars = [
        SweepParameter(f"time_{q.uid}", q_lengths, axis_name=f"{q.uid}_t")
        for q, q_lengths in zip(qubits, lengths)
    ]
    detune_sweep_pars = [
        SweepParameter(f"detuning_{q.uid}", q_dets, axis_name=f"{q.uid}_detuning")
        for q, q_dets in zip(qubits, detunings)
    ]

    max_measure_section_length = qpu.measure_section_length(qubits)
    qop = qpu.quantum_operations

    # >>> CHOOSE a guard >= 16 ns and multiple of 8 ns for SHFQA
    GUARD = 32e-9

    with dsl.acquire_loop_rt(
            count=opts.count,
            averaging_mode=opts.averaging_mode,
            acquisition_type=opts.acquisition_type,
            repetition_mode=opts.repetition_mode,
            repetition_time=opts.repetition_time,
            reset_oscillator_phase=opts.reset_oscillator_phase,
    ):
        # Outer sweep: detuning
        with dsl.sweep(name="detuning_sweep", parameter=detune_sweep_pars,
                       alignment=SectionAlignment.LEFT):
            for q, dpar in zip(qubits, detune_sweep_pars):
                qop.set_frequency(
                    q,
                    frequency=q.parameters.resonance_frequency_ge + dpar,
                    transition=opts.transition,
                    rf=True,
                )

            # Inner sweep: Rabi length (keep readout time fixed)
            with dsl.sweep(name="rabi_length_sweep", parameter=time_sweep_pars,
                           alignment=SectionAlignment.RIGHT):

                # 1) Drive
                with dsl.section(uid="main_excitation", alignment=SectionAlignment.LEFT):
                    for q, qtimes in zip(qubits, time_sweep_pars):
                        qop.x180(q, length=qtimes, transition=opts.transition)

                # >>> 1.5) GUARD — ADD THIS SECTION
                # >>> 1.5) GUARD — ADD/REPLACE THIS SECTION
                with dsl.section(uid="guard_before_measure", alignment=SectionAlignment.LEFT):
                    # helpers to pick the right logical signals from q.signals (dict)
                    READOUT_KEYS = ("readout", "measure")  # common names for the QA output
                    DRIVE_KEYS = ("drive", "drive_ge", "drive01")

                    def _pick_signal(q, candidates):
                        for k in candidates:
                            if k in q.signals:
                                return q.signals[k]
                        # fall back to "first available" to avoid crashing; you can remove this if you prefer strictness
                        return next(iter(q.signals.values()))

                    for q in qubits:
                        readout_sig = _pick_signal(q, READOUT_KEYS)
                        drive_sig = _pick_signal(q, DRIVE_KEYS)

                        dsl.delay(readout_sig, GUARD)
                        dsl.delay(drive_sig, GUARD)

                # 2) Measure (fixed section length)
                with dsl.section(uid="main_measure", alignment=SectionAlignment.LEFT):
                    for q in qubits:
                        msec = qop.measure(q, dsl.handles.result_handle(q.uid))
                        msec.length = max_measure_section_length

                # 3) Reset
                with dsl.section(uid="reset", alignment=SectionAlignment.LEFT):
                    for q in qubits:
                        qop.passive_reset(q)