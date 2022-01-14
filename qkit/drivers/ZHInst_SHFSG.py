# Zurich Instruments SHFSG driver by András, Thilo, 2021
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
# along with this program; if not, query to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
import enum
import time
from typing import List, Union

import os
from pathlib import Path
import qkit
from qkit.core.instrument_base import Instrument
from qkit import visa
import logging
import numpy
import zhinst
from zhinst import utils
from qkit.drivers.ZHInst_Common import ZHInst_Path, ZHInst_Device, ZHInst_AWG_Mixin, load_common_sample


class ZHInst_SHFSG(ZHInst_Device, ZHInst_AWG_Mixin):
    """
    This is the python driver for Zurich Instruments SHFSG Signal Generator.
    It wraps the zurich instrument python driver.

    Usage:
    Initialise with
    <name> = instruments.create('<name>', device_id=<Numerical Device ID>, server_host=<ZI Server host>, server_port=<ZI Server Port>, interface=<Device Interface>)

    """

    channels: List['Channel']
    synthesizers: List['Synthesizer']

    def __init__(self, name, address="nop", device_id="12064", server_host="localhost", server_port=8004, interface="1GbE"):
        """
        Initializes a connection to the SHFSG Signal Generator.

        We assume, that by default, the Zurich Instrument server runs on localhost with standard configuration
        and that the signal generator is connected via Ethernet.

        Input:
            name (string)    : name of the instrument
            address (string) : GPIB address
        """

        ZHInst_Device.__init__(self, name, device_id, server=server_host, port=server_port, interface=interface)

        num_synth = 4  # Common for all devices of this type.
        self.synthesizers = [self.Synthesizer(self, synth_id) for synth_id in range(num_synth)]

        num_chan = int(self.getString("FEATURES/DEVTYPE")[-1])

        def build_channel(index):
            synth_id = self.getInt(f"SGCHANNELS/{index}/SYNTHESIZER")
            synth = self.synthesizers[synth_id]
            return self.Channel(self, index, synth)

        self.channels = [build_channel(i) for i in range(num_chan)]


        # Implement parameters, Example:
        # self.add_parameter('nop', type=int,
        #                    flags=Instrument.FLAG_GETSET,
        #                    minval=1, maxval=100001,
        #                    tags=['sweep'])

        # Configure per channel parameters
        minfreq = self._daq.getDouble(self.build_key("SYSTEM/PROPERTIES/MINFREQ"))
        maxfreq = self._daq.getDouble(self.build_key("SYSTEM/PROPERTIES/MAXFREQ"))

        # for channel_id in range(1, 9):
        #     self.build_centerfreq_for_channel(channel_id)
        #     self.build_channel_configuration(channel_id)
        #     self.build_set_channel_mode(channel_id)
        #     self.build_command_table_upload(channel_id)'

        # Configure global parameters:
        self.add_parameter('fpga_temperature', type=float, flags=Instrument.FLAG_GET, unit="°C")
        self.add_parameter('time', type=int, flags=Instrument.FLAG_GET)
        self.add_parameter('reference_clock_frequency', type=float, flags=Instrument.FLAG_GET, units="Hz")

        # Implement functions
        #self.add_function('get_freqpoints')

    class Channel(ZHInst_Path):
        """
        Represents a device channel.
        """

        def __init__(self, accessor, channel_id: int, synthesizer: 'ZHInst_SHFSG.Synthesizer'):
            ZHInst_Path.__init__(self, accessor, f"SGCHANNELS/{channel_id}")
            self._synthesizer = synthesizer
            self.channel_id = channel_id

        def get_synthesizer(self) -> 'ZHInst_SHFSG.Synthesizer':
            """
            Return the synthesizer used by this channel.
            """
            return self._synthesizer

        def set_mode(self, mode: str):
            """
            Sets the operation mode of this channel, either 'rf' or 'lf'
            """
            lower_mode = mode.strip().lower()
            if mode == "lf":
                self.setInt("OUTPUT/RFLFPATH", 0)
            elif mode == "rf":
                self.setInt("OUTPUT/RFLFPATH", 1)
            else:
                raise AssertionError(f"Invalid channel mode '{mode}'.")

        def get_mode(self) -> str:
            """
            Gets the operation mode of this channel and returns it.

            Will return either 'rf' or 'lf'
            """
            int_mode = self.getInt("OUTPUT/RFLFPATH")
            if int_mode == 0:
                return 'lf'
            elif int_mode == 1:
                return 'rf'
            else:
                raise  AssertionError(f"API returned invalid RFLFPATH '{int_mode}'")

        def set_enabled(self, enabled: bool):
            """
            Enables or disables this channel
            """
            self.setBool("OUTPUT/ON", enabled)

        def get_enabled(self) -> bool:
            """
            Returns wether this channel is enabled or not.
            """
            return self.getBool("OUTPUT/ON")

        def set_output_range(self, output_power):
            """
            Sets the output power range.
            """
            self.setDouble("OUTPUT/RANGE", output_power)

        def get_output_range(self):
            """
            Gets the output power range.
            """
            return self.getDouble("OUTPUT/RANGE")

        def set_awg_enabled(self, enabled: bool):
            """
            Enables or disables the Arbitrary Waveform Generator for this channel.
            """
            self.setBool("AWG/ENABLE", enabled)

        def get_awg_enabled(self) -> bool:
            return self.getBool("AWG/ENABLE")

        def set_awg_single_mode(self, single: bool):
            """
            Enables or disables the AWG single mode.
            """
            self.setBool("AWG/SINGLE", single)

        def get_awg_single_mode(self) -> bool:
            return self.getBool("AWG/SINGLE")

        def set_awg_digital_modulation(self, enabled: bool):
            """
            Enables or disables digital moudlation of the awg.
            """
            self.setBool("AWG/MODULATION/ENABLE", enabled)

        def get_awg_digital_modulation(self) -> bool:
            return self.getBool("AWG/MODULATION/ENABLE")

        @enum.unique
        class MarkerSource(enum.IntEnum):
            AWG_TRIGGER0 = 0
            AWG_TRIGGER1 = 1
            AWG_TRIGGER2 = 2
            AWG_TRIGGER3 = 3
            OUTPUT0_MARKER0 = 4
            OUTPUT0_MARKER1 = 5
            OUTPUT1_MARKER0 = 6
            OUTPUT1_MARKER1 = 7
            TRIGIN0 = 8
            TRIGIN1 = 9
            TRIGIN2 = 10
            TRIGIN3 = 11
            TRIGIN4 = 12
            TRIGIN5 = 13
            TRIGIN6 = 14
            TRIGIN7 = 15
            HIGH = 16
            LOW = 17

        def set_marker_source(self, source: MarkerSource):
            """
            Sets the marker source. See enum MarkerSource
            """
            self.setInt("MARKER/SOURCE", source.value)

        def get_marker_source(self) -> MarkerSource:
            """
            Gets the marker source. See enum MarkerSource
            """
            return MarkerSource(self.getInt("MARKER/SOURCE"))

        def set_oscillator_frequency(self, oscillator_index: int, frequency: float):
            self.setDouble(f"OSCS/{oscillator_index}/FREQ", frequency)

        def get_oscillator_frequency(self, oscillator_index: int) -> float:
            return self.getDouble(f"OSCS/{oscillator_index}/FREQ")

        def set_sine_oscillator_selection(self, sine_index: int, oscillator_index: int):
            self.setInt(f"SINES/{sine_index}/OSCSELECT", oscillator_index)

        def get_sine_oscillator_selection(self, sine_index: int) -> int:
            return self.getInt(f"SINES/{sine_index}/OSCSELECT")

        def set_sine_harmonic(self, sine_index: int, harmonic: float):
            self.setDouble(f"SINES/{sine_index}/HARMONIC", harmonic)

        def get_sine_harmonic(self, sine_index: int) -> float:
            return self.getDouble(f"SINES/{sine_index}/HARMONIC")

        def set_sine_phaseshift(self, sine_index: int, phase: float):
            self.setDouble(f"SINES/{sine_index}/PHASESHIFT", phase)

        def get_sine_phaseshift(self, sine_index: int) -> float:
            return self.getDouble(f"SINES/{sine_index}/PHASESHIFT")

        def upload_command_table(self, command_table_json: str):
            self.setVector("AWG/COMMANDTABLE/DATA", command_table_json)

        def reference_configuration(self, rf_freq, osc_freq, output_power):
            self.get_synthesizer().set_centerfreq(rf_freq * 1e9)
            self.set_enabled(True)
            self.set_output_range(output_power)
            self.set_mode("rf")

            self.set_oscillator_frequency(0, osc_freq * 1e6)
            self.set_sine_oscillator_selection(0, 0)
            self.set_sine_harmonic(0, 1)
            self.set_sine_phaseshift(0, 0)
            self.set_awg_digital_modulation(True)

            self.set_marker_source(self.MarkerSource.AWG_TRIGGER0)

        def configure_sine_modulation(self, sine_index: int, enable_i: bool, enable_q: bool, ica: float, isa: float, qca: float, qsa: float):
            """
            Configure modulation with I and Q components defined via sine and cosine amplitudes.
            """
            self.setBool(f"SINES/{sine_index}/I/ENABLE", enable_i)
            self.setBool(f"SINES/{sine_index}/Q/ENABLE", enable_q)
            self.setDouble(f"SINES/{sine_index}/I/COS/AMPLITUDE", ica)
            self.setDouble(f"SINES/{sine_index}/I/SIN/AMPLITUDE", isa)
            self.setDouble(f"SINES/{sine_index}/Q/COS/AMPLITUDE", qca)
            self.setDouble(f"SINES/{sine_index}/Q/SIN/AMPLITUDE", qsa)

    class Synthesizer(ZHInst_Path):
        """
        Represents a synthesizer.
        """

        def __init__(self, accessor, synth_id: int):
            ZHInst_Path.__init__(self, accessor, f"SYNTHESIZERS/{synth_id}")
            self.synth_id = synth_id

        def set_centerfreq(self, freq):
            """
            Set the centerfrequency of this synthesizer.
            """
            self.setDouble("CENTERFREQ", freq)

        def get_centerfreq(self):
            """
            Get the center frequency of this synthesizer.
            """
            return self.getDouble("CENTERFREQ")


    def do_get_fpga_temperature(self):
        return self.getDouble("STATS/PHYSICAL/FPGA/TEMP")

    def do_get_time(self):
        return self.getInt("STATUS/TIME")

    def do_get_reference_clock_frequency(self):
        return self.getDouble("SYSTEM/CLOCKS/REFERENCECLOCK/IN/FREQ")

    """
    Zurich Instrument Example waveforms provided by their GitHub Repo.
    See: https://github.com/zhinst/labone-api-examples
    """
    def load_rabi(self, channel_id, rf_freq, osc_freq, output_power):
        """
        Load the standard rabi sequence on channel `channel`.
        `rf_freq` is given in GHz.
        `osc_freq` is given in MHz.
        """
        channel = self.channels[channel_id]
        channel.reference_configuration(rf_freq, osc_freq, output_power)

        self.compile_sequencer_program(load_common_sample("rabi.seq"))
        channel.upload_command_table(load_common_sample("rabi.json"))

        channel.set_awg_single_mode(True)
        channel.set_enabled(True)

    def load_ramsey(self, channel_id, rf_freq, osc_freq, output_power):
        """
        Load the standard ramsey sequence on channel `channel`.
        `rf_freq` is given in GHz.
        `osc_freq` is given in MHz.
        """
        channel = self.channels[channel_id]
        channel.reference_configuration(rf_freq, osc_freq, output_power)

        self.compile_sequencer_program(load_common_sample("ramsey.seq"))
        channel.upload_command_table(load_common_sample("ramsey.json"))

        channel.set_awg_single_mode(True)
        channel.set_enabled(True)

    def load_cpmg(self, channel_id, rf_freq, osc_freq, output_power):
        """
        Load the standard CPMG (Carl-Purcell-Meiboom-Gill) sequence on channel `channel`.
        `rf_freq` is given in GHz.
        `osc_freq` is given in MHz.
        """
        channel = self.channels[channel_id]
        channel.reference_configuration(rf_freq, osc_freq, output_power)

        self.compile_sequencer_program(load_common_sample("CPMG.seq"))
        channel.upload_command_table(load_common_sample("CPMG.json"))

        channel.set_awg_single_mode(True)
        channel.set_enabled(True)

    def load_sine(self, channel_id, rf_freq, osc_freq, output_power, gain):
        """
        Load a sine wave modulation.
        `rf_freq` is given in GHz.
        `osc_freq` is given in MHz.
        """
        channel = self.channels[channel_id]
        channel.get_synthesizer().set_centerfreq(rf_freq * 1e9)
        channel.set_enabled(True)
        channel.set_output_range(output_power)
        channel.set_mode("rf")
        channel.set_oscillator_frequency(0, osc_freq * 1e6)
        channel.configure_sine_modulation(0, True, True, gain, -gain, gain, gain)