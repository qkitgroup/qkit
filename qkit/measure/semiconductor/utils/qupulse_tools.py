#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Sep  7 11:05:12 2021

@author: lr1740
"""
import warnings
from numbers import Real
from typing import Any, Dict, Optional, Set, Tuple

import numpy as np
from cycler import cycler
from qupulse.pulses.plotting import render
from qupulse.pulses.pulse_template import PulseTemplate
from qupulse.utils.types import ChannelID


def plut(pulse: PulseTemplate,
         parameters: Dict[str, Real]=None,
         sample_rate: Real=10,
         axes: Any=None,
         show: bool=True,
         plot_channels: Optional[Set[ChannelID]]=None,
         plot_measurements: Optional[Set[str]]=None,
         plot_triggers: Optional[Set[ChannelID]] = None,
         stepped: bool=True,
         maximum_points: int=10**6,
         time_slice: Tuple[Real, Real]=None,
         xlabel: str = 'Time (ns)',
         ylabel: str = 'Voltage (a.u.)',
         trig_label: str = "Trigger level (a.u.)",
         **kwargs) -> Any:  # pragma: no cover
    """Plots a pulse using matplotlib.

    The given pulse template will first be turned into a pulse program (represented by a Loop object) with the provided
    parameters. The render() function is then invoked to obtain voltage samples over the entire duration of the pulse which
    are then plotted in a matplotlib figure.

    Args:
        pulse: The pulse to be plotted.
        parameters: An optional mapping of parameter names to Parameter
            objects.
        sample_rate: The rate with which the waveforms are sampled for the plot in
            samples per time unit. (default = 10)
        axes: matplotlib Axes object the pulse will be drawn into if provided
        show: If true, the figure will be shown
        plot_channels: If specified only channels from this set will be plotted. If omitted all channels will be.
        stepped: If true pyplot.step is used for plotting
        plot_measurements: If specified measurements in this set will be plotted. If omitted no measurements will be.
        maximum_points: If the sampled waveform is bigger, it is not plotted
        time_slice: The time slice to be plotted. If None, the entire pulse will be shown.
        xlabel: optional replacement for the standard xlabel
        ylabel: optional replacement for the standard ylabel
        trig_label: optional replacement for the standard trig_label
        kwargs: Forwarded to pyplot. Overwrites other settings.
    Returns:
        matplotlib.pyplot.Figure instance in which the pulse is rendered
    Raises:
        PlottingNotPossibleException if the sequencing is interrupted before it finishes, e.g.,
            because a parameter value could not be evaluated
        all Exceptions possibly raised during sequencing
    """
    from matplotlib import pyplot as plt

    channels = pulse.defined_channels

    if parameters is None:
        parameters = dict()

    program = pulse.create_program(parameters=parameters,
                                   channel_mapping={ch: ch for ch in channels},
                                   measurement_mapping={w: w for w in pulse.measurement_names})

    if program is not None:
        times, voltages, measurements = render(program,
                                               sample_rate,
                                               render_measurements=bool(plot_measurements),
                                               time_slice=time_slice)
    else:
        times, voltages, measurements = np.array([]), dict(), []

    duration = 0
    if times.size == 0:
        warnings.warn("Pulse to be plotted is empty!")
    elif times.size > maximum_points:
        # todo [2018-05-30]: since it results in an empty return value this should arguably be an exception, not just a warning
        warnings.warn("Sampled pulse of size {wf_len} is lager than {max_points}".format(wf_len=times.size,
                                                                                         max_points=maximum_points))
        return None
    else:
        duration = times[-1]

    if time_slice is None:
        time_slice = (0, duration)

    legend_handles = []
    if axes is None:
        # plot to figure
        plt.tight_layout()
        figure = plt.figure()
        axes = figure.add_subplot(111)
    
    if plot_triggers:
        triggers = {ch: voltage
                    for ch, voltage in voltages.items()
                    if ch in plot_triggers}
        invalid_trig = [trig for trig in plot_triggers if trig not in voltages.keys()]
        if invalid_trig:
            invalid_str = ", ".join(invalid_trig)
            raise ValueError(f"{__name__}: Cannot plot {invalid_str} on the trigger axis. Channels not defined")
        
        trig_max_voltage = max((max(channel, default=0) for chname, channel in triggers.items() if chname in plot_triggers), default=0)
        trig_min_voltage = min((min(channel, default=0) for chname, channel in triggers.items() if chname in plot_triggers), default=0)
        trig_voltage_difference = trig_max_voltage-trig_min_voltage
        
        axes_trig = axes.twinx()
        ax_color = "b"
        axes_trig.spines["right"].set_color(ax_color)
        axes_trig.tick_params(axis='y', colors=ax_color)
        axes_trig.yaxis.label.set_color(ax_color)
        axes_trig.set_ylabel(trig_label)        
        axes_trig.set_ylim(trig_min_voltage - 0.1*trig_voltage_difference, trig_max_voltage + 0.1*trig_voltage_difference)
        axes_trig.set_prop_cycle(cycler(color="bgrcmyk"))

        for ch_name, voltage in triggers.items():
            label = 'channel {}'.format(ch_name)       
            if stepped:
                line, = axes_trig.step(times, voltage, **{**dict(where='post', label=label), **kwargs})
            else:
                line, = axes_trig.plot(times, voltage, **{**dict(label=label), **kwargs})
            legend_handles.append(line)

    if plot_channels is not None:
        voltages = {ch: voltage
                    for ch, voltage in voltages.items()
                    if ch in plot_channels}

        
    for ch_name, voltage in voltages.items():
        label = 'channel {}'.format(ch_name)       
        if stepped:
            line, = axes.step(times, voltage, **{**dict(where='post', label=label), **kwargs})
        else:
            line, = axes.plot(times, voltage, **{**dict(label=label), **kwargs})
        legend_handles.append(line)    


    if plot_measurements:
        measurement_dict = dict()
        for name, begin, length in measurements:
            if name in plot_measurements:
                measurement_dict.setdefault(name, []).append((begin, begin+length))

        color_map = plt.cm.get_cmap('plasma')
        meas_colors = {name: color_map(i/len(measurement_dict))
                       for i, name in enumerate(measurement_dict.keys())}
        for name, begin_end_list in measurement_dict.items():
            for begin, end in begin_end_list:
                poly = axes.axvspan(begin, end, alpha=0.2, label=name, edgecolor='black', facecolor=meas_colors[name])
            legend_handles.append(poly)

    axes.legend(handles=legend_handles, loc = "best")

    max_voltage = max((max(channel, default=0) for channel in voltages.values()), default=0)
    min_voltage = min((min(channel, default=0) for channel in voltages.values()), default=0)
    
    # add some margins in the presentation
    axes.set_xlim(-0.5+time_slice[0], time_slice[1] + 0.5)
    voltage_difference = max_voltage-min_voltage
    if voltage_difference>0:
        axes.set_ylim(min_voltage - 0.1*voltage_difference, max_voltage + 0.1*voltage_difference)
    
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)

    if pulse.identifier:
        axes.set_title(pulse.identifier)

    if show:
        axes.get_figure().show()
    return axes.get_figure()