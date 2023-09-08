# -*- coding: utf-8 -*-

# MMW@KIT
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

"""
References
----------
https://pypi.org/project/pcf8575/

Installation
------------
sudo apt-get update
sudo apt-get install libffi-dev
pip install pcf8575
"""

from qkit.config.services import cfg
import time
import logging
import os
import json

try:
    from qkit.services.qplexkit.pcf8575 import PCF8575
except ModuleNotFoundError:
    # logging.warning('qplexkit: Module PCF8575 for I2C-expander not found. Use dummy instead that just supports software debugging but no control of the qplexkit at all.')
    class PCF8575(object):
        """
        This is a dummy class that supports software debugging but no control of the qplexkit and is used for the qkit-driver.
        """
        def __init__(self, i2c_bus_no, address):
            print(i2c_bus_no, address)
            self.port = 16 * [True]



class qplexkit(object):
    """
    Qplexkit is a DC multiplexer for low level and low noise transport measurements of micro and nano circuits at low
    temperatures. It uses MDSM connectors with 25 pins and enables to measure 12 different 4-wire experiments with the
    same four lines in switching between them by means of low temperature applicable latching relays. The control unit
    at room temperature uses a Raspberry Pi Model B+ and provides 20 control lines connected to a current source to
    switch the relays. The control lines not required by the multiplexer can be used to switch cryogenic relays, e.g. to
    switch power dividers on or off for low-ohmic experiments to achieve better SNRs.
    A driver is embedded to Qkit - a quantum measurement suite in python.


    ##########################################################################
    #                            Cryostat circuit                            #
    ##########################################################################

                                                      bias                sense                                                     ---------------------------
                                                 │           │         │           │                                                CURRENT DIVIDER & AMPLIFIER
                                                 │           │       ╔═╧═╗       ╔═╧═╗
                                                 │    ╔═══╗  │    ┌──╢18 ╟──┐ ┌──╢18 ╟──┐
                                                 ├─■■─╢17 ╟──┤    │  ╚═══╝  / \  ╚═══╝  │                                           bias lines: 1/10 current divider
                                                 │ o──╢   ║  │    │  ╔═══╗ /___\        │                                           sense lines: amplifier
                                                 │    ╚═══╝  │    └──╢18 ╟──┘ └──╢18 ╟──┘
                                                 █    (13)   █       ╚═╤═╝  (14) ╚═╤═╝
                                                 │           │         │           │
                                                 │           │         │           │
                                                 └─────╥─────┘         └─────╥─────┘
                                                       ║                     ║                                                      =================== MDM-connectors (separate PCBs)
                                                       ║                     ║                                                      -------------------
                                                     ╔═╩═╗                 ╔═╩═╗                                                    PROTECTIVE RESISTOR
                                                (11) ║15 ╠════════╦════════╣16 ║ (12)
                                                     ╚═╦═╝        ║        ╚═╦═╝
                                                   10Ω █          ║          █ 10Ω                                                  protective resistor during switching
                                                       ║          ║          ║
                                                       ╨          ║          ╨
                                                      GND         ║         GND                                                     --------------
                                                                ╔═╩═╗                                                               DC MULTIPLEXER
                                  ╔═════════════════════════════╣ 0 ╠═════════════════════════════╗                                 relay layer A: <lay> = 0
                                  ║                             ╚═══╝                             ║
                                  ║                              (0)                              ║
                                ╔═╩═╗                                                           ╔═╩═╗
                  ╔═════════════╣ 1 ╠═════════════╗                               ╔═════════════╣ 2 ╠═════════════╗                 relay layer B: <lay> = 1
                  ║             ╚═══╝             ║                               ║             ╚═══╝             ║
                  ║              (1)              ║                               ║              (2)              ║
                ╔═╩═╗                           ╔═╩═╗                           ╔═╩═╗                           ╔═╩═╗
          ╔═════╣ 3 ╠═════╗               ╔═════╣ 4 ╠═════╗               ╔═════╣ 5 ╠═════╗               ╔═════╣ 6 ╠═════╗         relay layer C: <lay> = 2
          ║     ╚═══╝     ║               ║     ╚═══╝     ║               ║     ╚═══╝     ║               ║     ╚═══╝     ║
          ║      (3)      ║               ║      (4)      ║               ║      (5)      ║               ║      (6)      ║
        ╔═╩═╗           ╔═╩═╗           ╔═╩═╗           ╔═╩═╗           ╔═╩═╗           ╔═╩═╗           ╔═╩═╗           ╔═╩═╗
      ╔═╣ 7 ╠═╗       ╔═╣ 8 ╠═╗       ╔═╣ 9 ╠═╗       ╔═╣10 ╠═╗       ╔═╣11 ╠═╗       ╔═╣12 ╠═╗       ╔═╣13 ╠═╗       ╔═╣14 ╠═╗     relay layer D: <lay> = 3
      ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║       ║ ╚═══╝ ║     lrel: logical relay number
      ║  (7)  ║       ║  (8)  ║       ║  ---  ║       ║  ---  ║       ║  (9)  ║       ║ (10)  ║       ║  ---  ║       ║  ---  ║     <self._lrel2prel[<lrel>]>: (physical relay number)
    ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐   ┌─╨─┐
    │ 0 │   │ 1 │   │ 2 │   │ 3 │   │ 4 │   │ 5 │   │ 6 │   │ 7 │   │ 8 │   │ 9 │   │10 │   │11 │   │12 │   │13 │   │14 │   │15 │   <exp>                   : logical experiment number
    └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘   └───┘
     (0)     (1)     (2)     (3)     (4)     ---     (5)     ---     (6)     (7)     (8)     (9)    (10)     ---    (11)     ---    <self._exps(<exp>)>      : (physical experiment number)
    0000    0001    0010    0011    0100    0101    0110    0111    1000    1001    1010    1011    1100    1101    1110    1111    bin(<exp>)               : equals path through relays ABCD (0:left, 1:right)

    DC MULTIPLEX
    Each logical latching relay (double solid lined) switches all four measurement lines to select the wanted experiment
    (single solid line). The logical relay numbers 9, 10, 11, 12 are dummy relays that do not exist physically, but
    simplify the control logic by using bit operations of this obtained symmetric setup.

    CURRENT DIVIDER
    Above the DC multiplexer, latching relays (double solid lined) may connect
    a pair of two current lines with a 10Ω resistance (black box). Together
    with the down-streamed cables, filters etc (illustrated as resistances
    above) this forms switchable current dividers whose attenuation factor
    depends on the ratio of these resistances and attenuates both signal and
    noise. Since the added Nyquist noise depends on the square root of the
    temperature, this low temperature current divider provides better signal to
    noise ratios compared to those operating at room temperature.


    ##########################################################################
    #                        Room temperature circuit                        #
    ##########################################################################

    control lines for multiplexer relays

        VP2     VP3     VP4     VP9    VP10    VP11    VP12    VP15    VP16    VP17    VP22    VP23    VP24            physical control line (equals MDM pinout)
        (0)     (1)     (2)     (3)     (4)     (5)     (6)     (7)     (8)     (9)    (10)    (11)    (12)            (logical control line)
         │       │       │       │       │       │       │       │       │       │       │       │       │
         ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈       ≈             connection to cryostat circuit
         │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗
     ...─┴─╢ 0 ╟─┴─╢ 1 ╟─┴─╢ 2 ╟─┴─╢ 3 ╟─┴─╢ 4 ╟─┴─╢ 5 ╟─┴─╢ 6 ╟─┴─╢ 7 ╟─┴─╢ 8 ╟─┴─╢11 ╟─┴─╢12 ╟─┴─╢15 ╟─┴─╢16 ╟─...   logical relay number (see Cryostat circuit)
           ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝
            (0)     (1)     (2)     (3)     (4)     (5)     (6)     (7)     (8)     (9)    (10)    (11)    (12)


    control lines for supplementary relays

        VP1     VP7     VP8    VP14    VP20    VP21    VP25            physical control line (equals MDM pinout)
       (13)    (14)    (15)    (16)    (17)    (18)    (19)            (logical control line)
         │       │       │       │       │       │       │
         ≈       ≈       ≈       ≈       ≈       ≈       ≈             connection to cryostat circuit
         │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗ │ ╔═══╗
     ...─┴─╢17 ╟─┴─╢18 ╟─┴─╢19 ╟─┴─╢20 ╟─┴─╢21 ╟─┴─╢22 ╟─┴─╢23 ╟─...   logical relay number (see Cryostat circuit)
           ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝   ╚═══╝
           (13)    (14)    (15)    (16)    (17)    (18)    (19)

    To safe relay switch lines for low temperature relays (double solid lined), they are arranged ring-shaped where each
    line is connected to the relay coil '+' on the one side and to the relay '-' on the other side. At room temperature
    they are floating by default and can be connected either with HIGH or LOW by two non-latching relays (single solid
    lined) that are controlled by GPIOs of a Raspberry Pi 3 Model B.
    """

    def __init__(self):
        """
        Initiates variables to default configuration and sets raspberry up.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.cfg = cfg['qplexkit']
        ''' prepare raspberry pi '''
        # try:
        #     ## set board mode to Broadcom
        #     GPIO.setmode(GPIO.BCM)
        #     ## setup GPIO
        #     for pin in self._gpio.values():
        #          GPIO.setup(pin, GPIO.OUT)
        # except:
        #     logging.error('qplexkit: Cannot set up Raspberry Pi')
        #     raise RuntimeError('qplexkit: Cannot set up Raspberry Pi')
        ''' prepare I2C IO expander (PCF8575) '''
        self.pcf1 = PCF8575(i2c_bus_no=1, address=0x20)
        self.pcf2 = PCF8575(i2c_bus_no=1, address=0x21)
        self.pcf1.port[15] = False  # current source off (no inverted logic, as current source switches GND like the PCF8575)
        self.pcfs = {1: self.pcf1, 2: self.pcf2}
        ''' class variables '''
        self._switch_time = 10e-3
        ''' logical - physical relay '''
        self._lrel2prel = {0: 0,  # layer 0
                           1: 1, 2: 2,  # layer 1
                           3: 3, 4: 4, 5: 5, 6: 6,  # layer 2
                           7: 7, 8: 8, 9: None, 10: None, 11: 9, 12: 10, 13: None, 14: None,  # layer3
                           15: 11, 16: 12,  # relays for protective resistors
                           ### separate PCB ###
                           17: 13, 18: 14, 19: 15, 20: 16, 21: 17, 22: 18, 23: 19,  # supplementary relays
                           }  # logical relay to physical relay: physical relay number [logical relay number]
        self._prel2lrel = {val: key for key, val in self._lrel2prel.items()}  # physical relay to logical relay: logical relay number [physical relay number]
        del self._prel2lrel[None]
        self._lrel_num = len(self._lrel2prel)
        self._prel_num = len(self._prel2lrel)
        ''' logical - physical experiment '''
        self._lexp2pexp = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: None, 6: 5, 7: None,  # connector A
                           8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: None, 14: 11, 15: None,  # connector B
                           }  # logical experiment to physical experiment: physical experiment number [logical experiment number]
        self._pexp2lexp = {val: key for key, val in self._lexp2pexp.items()}  # physical experiment to logical experiment: logical experiment number [physical experiment number]
        del self._pexp2lexp[None]
        ''' logical relay control line - physical relay control line '''
        self._lline2pline = {0: 2, 1: 3, 2: 4, 3: 9, 4: 10, 5: 11, 6: 12, 7: 15, 8: 16, 9: 17, 10: 22,  # multiplexer
                             11: 23, 12: 24,  # relays for protective resistors
                             ### separate PCP ###
                             13: 1, 14: 7, 15: 8, 16: 14, 17: 20, 18: 21, 19: 25,  # supplementary relays
                             }
        ''' logical relay control line - physical relay control line '''
        self._pline2port = {1: (2, 3),  # K_OnOff_VP1 - 2.p03
                            2: (1, 2),  # K_OnOff_VP2 - 1.p02
                            3: (1, 3),  # K_OnOff_VP3 - 1.p03
                            4: (1, 4),  # K_OnOff_VP4 - 1.p04
                            7: (2, 0),  # K_OnOff_VP7 - 2.p00
                            8: (2, 1),  # K_OnOff_VP8 - 2.p01
                            9: (1, 5),  # K_OnOff_VP9 - 1.p05
                            10: (1, 6),  # K_OnOff_VP10 - 1.p06
                            11: (1, 7),  # K_OnOff_VP11 - 1.p07
                            12: (1, 8),  # K_OnOff_VP12 - 1.p08
                            14: (2, 2),  # K_OnOff_VP14 - 2.p02
                            15: (1, 9),  # K_OnOff_VP15 - 1.p09
                            16: (1, 10),  # K_OnOff_VP16 - 1.p10
                            17: (1, 11),  # K_OnOff_VP17 - 1.p11
                            20: (2, 4),  # K_OnOff_VP20 - 2.p04
                            21: (2, 5),  # K_OnOff_VP21 - 2.p05
                            22: (1, 12),  # K_OnOff_VP22 - 1.p12
                            23: (1, 13),  # K_OnOff_VP23 - 1.p13
                            24: (1, 14),  # K_OnOff_VP24 - 1.p14
                            25: (2, 6),  # K_OnOff_VP25 - 2.p06
                            '24>2': (1, 15),  # K_VP24>VP2 - 1.p17
                            '25>7': (2, 7),  # K_VP25>VP7 - 2.p07
                            'I_src_OnOff': (1, 0),  # I_SRC_OnOff - 1.p00
                            'I_src_out_toggle': (1, 1),  # I_SRC_OUT_TOGGLE - 1.p01
        }
        ''' Code condition register with current settings '''
        self._ccr_file = self.cfg['ccr_file']
        try:
            self._ccr = self.read_ccr()
        except (IOError, ValueError) as e:
            logging.error(f'qplexkit: Cannot read condition code register: {e}')
            logging.info('qplexkit: Reset qplexkit and create new json-file')
            self._ccr = 0
            self._create_ccr()
            self.reset()

    def set_switch_time(self, val):
        """
        Sets duration of the current pulse to <val>.

        Parameters
        ----------
        val: float
            Duration of the current pulse for switching the relays (in seconds).

        Returns
        -------
        None
        """
        self._switch_time = val
        return

    def get_switch_time(self):
        """
        Gets duration of the current pulse <val>.

        Parameters
        ----------
        None

        Returns
        -------
        val: float
            Duration of the current pulse for switching the relays (in seconds).
        """
        return self._switch_time

    def set_experiment(self, exp, protect=False, **kwargs):
        """
        Enables experiment <exp> by setting all relevant relays if necessary.

        Parameters
        ----------
        exp: int
            physical experiment number ∈ [0,11].
        protect: bool
            Measurement lines are connected using protective resistors to GND before and disconnected after changing to
            experiment <exp>. Default is False.
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        None
        """
        _ccr = kwargs.get('ccr', self._ccr)
        try:
            _lexp = self._pexp2lexp[exp]  # logical experiment number
            logging.info(f'Set experiment to {_lexp}({exp})')
            if protect:
                self.set_relay(rel=15, status=1)
                self.set_relay(rel=16, status=1)
            for lay in range(4):
                lrel = 2 ** lay - 1 + (_lexp >> 4 - lay)  # logical relay number
                lstatus = bool((_lexp >> 3 - lay) % 2)  # logical relay value
                if self.get_relay(rel=lrel, ccr=_ccr) ^ lstatus:  # if not already set correctly
                    self.set_relay(rel=lrel, status=lstatus, **kwargs)
            if protect:
                self.set_relay(rel=15, status=0)
                self.set_relay(rel=16, status=0)
        except (ValueError, KeyError) as e:
            logging.error(f'qplexkit: Cannot set experiment {exp}: {e}')
        return

    def get_experiment(self, **kwargs):
        """
        Sets experiment to <exp> in setting relevant relays if necessary.

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        exp: int
            physical experiment number ∈ [0,11].
        """
        _ccr = kwargs.get('ccr', self._ccr)
        exp = 4 * ['0']
        for lay in range(4):
            exp[lay] = str((_ccr >> int(self._lrel_num + 1 - 2 ** lay -
                                        sum([2 ** (lay - a) * int(exp[a - 1]) for a in range(1, 4)]))) % 2)
        return self._lexp2pexp[int(''.join(exp), 2)]

    def set_current_divider(self, status, **kwargs):
        """
        Sets current divider to <status> by setting relevant the relay if necessary.

        Parameters
        ----------
        status: bool
            current divider state
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        None
        """
        raise NotImplementedError("current divider hardware not yet implemented")
        if bool(status) ^ self.get_relay(rel=17, **kwargs):
            return self.set_relay(rel=17, status=status, **kwargs)
        else:
            return

    def get_current_divider(self, **kwargs):
        """
        Gets <status> of current divider.

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        status: bool
            current divider state
        """
        raise NotImplementedError("current divider hardware not yet implemented")
        return self.get_relay(rel=17, **kwargs)

    def set_amplifier(self, status, **kwargs):
        """
        Sets amplifier to <status> by setting relevant the relay if necessary.

        Parameters
        ----------
        status: bool
            amplifier state
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        None
        """
        raise NotImplementedError("voltage amplifier hardware not yet implemented")
        if bool(status) ^ self.get_relay(rel=18, **kwargs):
            return self.set_relay(rel=18, status=status, **kwargs)
        else:
            return

    def get_amplifier(self, **kwargs):
        """
        Gets <status> of amplifier.

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        status: bool
            amplifier state
        """
        raise NotImplementedError("voltage amplifier hardware not yet implemented")
        return self.get_relay(rel=18, **kwargs)

    def set_pcf_port(self, pcf, port, status):
        """
        Sets the port <port> of the I2C IO-Expander PCF8675 <pcf> to <status>. Note the inverted logic.

        Parameters
        ----------
        pcf: int
            PCF8575 number
        port: int
            Port number
        status: bool
            port status

        Returns
        -------
        None
        """
        self.pcfs[pcf].port[15 - port] = status  # inverse order of pcf8575.py is compensated by <15 - port>
        return


    def get_pcf_port(self, pcf, port):
        """
        Gets the status of port <port> of the I2C IO-Expander PCF8675 <pcf>. Note the inverted logic.

        Parameters
        ----------
        pcf: int
            PCF8575 number
        port: int
            Port number

        Returns
        -------
        status: bool
            port status
        """
        return self.pcfs[pcf].port[15 - port]  # inverse order of pcf8575.py is compensated by <15 - port>

    def set_current_source_status(self, status):
        """
        Sets current source to <status> to switch relays.

        Parameters
        ----------
        status: bool
            current source state

        Returns
        -------
        None
        """
        self.set_pcf_port(*self._pline2port['I_src_OnOff'], status)  # note not inversed polarity
        return

    def get_current_source_status(self):
        """
        Gets the status of the current source to switch relays.

        Parameters
        ----------
        None

        Returns
        -------
        status: bool
            current source state

        """
        return self.get_pcf_port(*self._pline2port['I_src_OnOff'])  # note not inversed polarity

    def set_relay(self, rel, status, **kwargs):
        """
        Sets relay number <rel> to <status> in sending a current pulse of duration <switch_time> on the control
        corresponding to <rel> with polarity corresponding to <status>

        Parameters
        ----------
        rel: int
            logical relay number <rel> ∈ [0:16]
        status: bool
            relay polarity
        **kwargs:
            switch_time: float
                duration of voltage pulse to switch relays
            ccr: int
                condition code register <ccr> of relay states
            ccr_file: str
                json-file to write <ccr>

        Returns
        -------
        None
        """
        _switch_time = kwargs.get('switch_time', self._switch_time)
        ## physical relay
        if rel not in self._prel2lrel.values():
            raise ValueError(f'Can not set relay {rel}, as it does not exist physically, but is rather a logical dummy relay.')
        _prel = self._lrel2prel[rel]  # physical relay number
        ## left and right logical relay control lines
        if _prel <= 12:  # multiplexer
            _lline_l = _prel
            _lline_r = (_prel + 1) % 13  # mod 13 closes cycle for last multiplexer relay
        elif 12 < _prel <= 19:  # supplementary relays
            _lline_l = _prel
            _lline_r = ((_prel + 1 - 13) % 7) + 13  # mod 7 closes cycle for last supplementary relay and +/- 13 shifts by the 13 multiplexer relays
        ## physical relay control lines
        _pline_l = self._lline2pline[_lline_l]  # left physical control line (connected to relay pin 8)
        _pline_r = self._lline2pline[_lline_r]  # right physical control line (connected to relay pin 1)
        print(f'qplexkit: Set relay {_prel}({rel}) to {status} with line {_lline_l} (VP{_pline_l}) and line {_lline_r} (VP{_pline_r})')
        logging.info(f'qplexkit: Set relay {_prel}({rel}) to {status} with line {_lline_l} (VP{_pline_l}) and line {_lline_r} (VP{_pline_r})')
        ## I2C ports
        self.set_pcf_port(*self._pline2port[_pline_l], False)  # enable physical control line to relay pin 8
        self.set_pcf_port(*self._pline2port[_pline_r], False)  # enable physical control line to relay pin 1
        self.set_pcf_port(*self._pline2port['I_src_out_toggle'], status ^ (_prel % 13) % 2)  # status xor parity of physical relay (mod 13 shift supplementary relays to zero in order to use parity analogue)
        if _prel == 12:
            ## invert physical line 24 to match with line 2
            self.set_pcf_port(*self._pline2port['24>2'], False)
        elif _prel == 19:
            ## invert physical line 25 to match with line 7
            self.set_pcf_port(*self._pline2port['25>7'], False)
        ''' send current pulse '''
        self.set_current_source_status(True)  # enable current source
        time.sleep(_switch_time)
        self.set_current_source_status(False)  # disable current source
        ''' disable all I2C ports '''
        self.pcf1.port = [True] * 16
        self.pcf2.port = [True] * 16
        #for (pcf, port) in self._pline2port.values():
        #    self.set_pcf_port(pcf, port, True)
        self.set_current_source_status(False)  # disable current source
        ''' save changes in ccr '''
        self._set_ccr(rel=rel, status=status, **kwargs)
        self._write_ccr(timestamp=True, **kwargs)
        return

    def get_relay(self, rel, **kwargs):
        """
        Gets value <status> of relay <rel> from a given condition code register <ccr>

        Parameters
        ----------
        rel: int
            logical relay number <rel> ∈ [0:16]
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        status: bool
            relay polarity
        """
        return self.get_ccr(rel, **kwargs)

    def get_relays(self, **kwargs):
        """
        Gets statuses <status> of all relays from a given condition code register <ccr>

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        status: bool
            relay polarity
        """
        return list(map(int, list(bin(kwargs.get('ccr', self._ccr))[2:].zfill(self._lrel_num + 1))))

    def _set_ccr(self, rel, status, **kwargs):
        """
        Sets condition code register <ccr> from a given relay <rel> with status <status>

        Parameters
        ----------
        rel: int
            logical relay number <rel> ∈ [0:16]
        status: bool
            relay polarity
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        None
        """
        _ccr = list(map(str, self.get_relays(**kwargs)))
        _ccr[rel] = str(int(status))
        self._ccr = int(''.join(_ccr), 2)
        return

    def get_ccr(self, rel, **kwargs):
        """
        Gets status <status> of relay <rel> from a given condition code register <ccr>

        Parameters
        ----------
        rel: int
            logical relay number <rel> ∈ [0:16]
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        status: bool
            relay polarity
        """
        return bool(int(kwargs.get('ccr', self._ccr) >> int(self._lrel_num - rel)) % 2)

    def _write_ccr(self, timestamp=True, **kwargs):
        """
        Writes a given condition code register <ccr> (and a current timestamp if wanted <timestamp>) to a json-file
        <ccr_file>. The format is for
        * timestamp = True: [{"ccr": <ccr>, "time": "yyyy-MM-dd HH:mm:ss"}]
        * timestamp = False: [<ccr>]

        Parameters
        ----------
        timestamp: bool
            Default is True.
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states
            ccr_file: str
                json-file to write <ccr>

        Returns
        -------
        None
        """
        try:
            _ccr = kwargs.get('ccr', self._ccr)
            _ccr_file = kwargs.get('ccr_file', self._ccr_file)
            with open(_ccr_file, 'r+') as f:
                try:
                    data = json.load(f)
                except ValueError as e:
                    logging.error(f'qplexkit: Cannot load json-file to append ccr: {e}')
                    data = []
                f.seek(0)
                if timestamp:
                    data.append({'ccr': _ccr, 'time': time.strftime('%Y-%m-%d %H:%M:%S')})
                else:
                    data.append(_ccr)
                json.dump(data, f)
        except IOError as e:
            logging.error(f'qplexkit: Cannot find json-file {_ccr_file}: {e}')
        return

    def read_ccr(self, n=-1, timestamp=False, **kwargs):
        """
        Reads the n-th condition code register <ccr> from a json-file <ccr_file>.

        Parameters
        ----------
        n: int
            List index in <ccr_file>
        timestamp: bool
            Default is False.
        **kwargs:
            ccr_file: str
                json-file to write <ccr>

        Returns
        -------
        ccr: int
            condition code register <ccr> of relay states
        """
        _ccr_file = kwargs.get('ccr_file', self._ccr_file)
        with open(_ccr_file, 'r+') as f:
            try:
                _ccr = json.load(f)[n]
                if isinstance(_ccr, dict):  # format of entry with timestamp: [{"ccr": <ccr>, "time": "yyyy-MM-dd HH:mm:ss"}]
                    if timestamp:
                        return _ccr['ccr'], _ccr['time']
                    else:
                        return _ccr['ccr']
                elif isinstance(_ccr, int):  # format of entry without timestamp: [<ccr>]
                    if timestamp:
                        raise AttributeError('No timestamp of requested ccr-entry available.')
                    else:
                        return _ccr
                else:
                    logging.error(f'qplexkit: Cannot handle data from json-file {_ccr_file}')
                    raise ValueError('Cannot read condition code register')
            except (ValueError, KeyError) as e:
                logging.error(f'qplexkit: Cannot find condition code register: {e}')
                raise ValueError('Cannot read condition code register')

    def _create_ccr(self, **kwargs):
        """
        Creates a json-file <ccr_file> and writes a condition code register <ccr>.

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states
            ccr_file: str
                json-file to write <ccr>

        Returns
        -------
        None
        """
        _ccr = kwargs.get('ccr', self._ccr)
        _ccr_file = kwargs.get('ccr_file', self._ccr_file)
        if not os.path.isfile(_ccr_file):
            with open(_ccr_file, 'w+') as f:
                json.dump([{'ccr': _ccr, 'time': time.strftime('%Y-%m-%d %H:%M:%S')}], f)
        return

    def print_ccr(self, **kwargs):
        """
        Prints the state of all physical relays from a code condition register <ccr>.

        Parameters
        ----------
        **kwargs:
            ccr: int
                condition code register <ccr> of relay states

        Returns
        -------
        None
        """
        print('relay:\tstate')
        for (_lrel, _prel), _state in zip(self._lrel2prel.items(), self.get_relays(**kwargs)):
            if _prel is not None:
                print(f'{_prel}:\t{_state}')

    def reset(self):
        """
        Reset every relay to False and condition code register to 0

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        logging.info('qplexkit: Reset every relay to False')
        for prel, lrel in self._prel2lrel.items():  # iterate over all physical relays
            self.set_relay(lrel, 0)  # set logical relay number
        self._ccr = 0
        self._write_ccr()
        return

