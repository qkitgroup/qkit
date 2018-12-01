# LMX2595
# Grigorev Sasha 2018
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

# Refer to the 'MS2690A/MS2691A/MS2692A or MS2830A Signal
# Analyzer Operation Manual (Mainframe Remote Control)' for detailed
# specifications on IEEE488.2 common device messages and application
# common device messages.


from qkit.core.instrument_base import Instrument
import zerorpc
import logging
import types


def set_bit(value, index, bit):
    mask = 1 << index
    value &= ~mask
    if bit:
        value |= mask
    return value


def get_bit(value, bit):
    return (value & (1 << bit)) != 0


def to_bytes(number, leng):
    return [(number >> (8 * i)) & 0xff for i in range(leng - 1, -1, -1)]


def from_bytes(byte):
    a = []
    for j in range(len(byte)):
        for i in range(8):
            a.append((byte[len(byte) - j - 1] & 1 << i) * 2 ** (8 * j))
    return sum(a)


class Lmx2595(Instrument):
    """
    This is the driver for the TI Lmx2595 Signal Genarator

    Usage:
    Initialize with
    <name> = instruments.create('<name>', 'Lmx2595', address='<Ethernet address>)
    """

    def __init__(self, name, address, reset=True):
        """
        Initializes the Lmx2595, and communicates with the wrapper.

        Input:
            name (string)    : name of the instrument
            address (string) : Ethernet address

        Output:
            True if initialization was successful
        """
        logging.info(__name__ + ' : Initializing instrument Lmx2595')
        Instrument.__init__(self, name, tags=['physical'])
        self.c = zerorpc.Client()
        self.c.connect(address)
        self.r = 2
        self.params = {
            'StA': [44, 6, 1],
            'StB': [44, 7, 1],
            'Vco_calib_st': [0, 3, 1],
            'Reset_St': [0, 1, 1],
            'PowerA': [44, 8, 6],
            'PowerB': [45, 0, 6],
            'Num_b1': [43, 0, 16],
            'Num_b0': [42, 0, 16],
            'N_dev': [36, 0, 16],
            'ChDevA_st': [45, 11, 2],
            'ChDevB_st': [46, 0, 2]
        } # Dict contains address of register, start bit and length
        self.vco_max = 15e9  # default values according to manual
        self.vco_min = 7.5e9

        self.add_parameter('frequency', type=float, flags=Instrument.FLAG_GETSET, minval=200e6, maxval=14.9e9)

        if reset:
            self.reset()

    def _set_parameter(self, name, value, mode='full'):
        """
        Function to set internal Lmx2595 parameters

        Input:
            name: the name of parameter according to dictionary
            value: the value of the parameter
            mode: 'full' or 'part' depending on opportunity to write whole register or only part of it

        Output:
            None

        """
        if mode == 'full':  # So we do not care what is now written in the register and can overwrite it
            self.c.write_data([self.params[name][0], value[0], value[1]]) #Write the bytes
        if mode == 'part':  # Here we need to overwrite only sertain bits of the register using the function, written at script on rpi
            reg = self.c.read_data(self.params[name][0]) #Read the register value
            if self.params[name][1] < 8:  # That means that the value should be changed is the part of first byte
                wr_reg = reg[2]
                index = self.params[name][1]
                leng = self.params[name][2]
                for i in range(index, index + leng):
                    wr_reg = set_bit(wr_reg, i, get_bit(value, i - index))
                self.c.write_data([self.params[name][0], reg[1], wr_reg])  # Write the changed data
            else:
                wr_reg = reg[1]
                index = self.params[name][1] - 8
                leng = self.params[name][2]
                for i in range(index, index + leng):
                    wr_reg = set_bit(wr_reg, i, get_bit(value, i - index))
                self.c.write_data([self.params[name][0], wr_reg, reg[2]])  # Write the changed data

    def get_value(self, name, mode='full'):
        """
        Function for obtaining values of parameters

        Input:
            name: name of parameter
            mode: 'full' or 'part' depending on opportunity to read whole register or only part of it

        Output:
            Value of the parameter
        """
        if mode == 'full':
            return self.c.read_data(self.params[name][0])  # Just read the whole register and convert data into numbers
        if mode == 'part':
            reg = self.c.read_data(self.params[name][0])
            if self.params[name][1] < 8:  # The value we are interested in is in the first byte
                rd_reg = reg[2]
                index = self.params[name][1]
                leng = self.params[name][2]
                res = []
                for i in range(index, index + leng):
                    res.append(get_bit(rd_reg, i) * 2 ** (i - index))  # Read only part of a certain byte
                return sum(res)
            else:
                rd_reg = reg[1]
                index = self.params[name][1] - 8
                leng = self.params[name][2]
                res = []
                for i in range(index, index + leng):
                    res.append(get_bit(rd_reg, i) * 2 ** (i - index))  # Read only part of a certain byte
                return sum(res)

    def get_all(self):
        """
        This is the function to read all the parameters of the device

        Input:
            None

        Output:
            None
        """
        logging.info(__name__ + ' : get all')
        self.get_frequency()
        self.get_power_chA()
        self.get_power_chB()
        self.get_status_chA()
        self.get_status_chB()

    def set_status_chA(self, status):
        """
        Function to set output A status

        Input:
            Status: True (1) - turn on, False(0) - turn off (inverted in function due to device issues).

        Output:
            None
        """
        self._set_parameter('StA', ~status, mode='part')

    def set_status_chB(self, status):
        """
        Function to set output B status

        Input:
            Status: True (1) - turn on, False(0) - turn off (inverted in function due to device issues).

        Output:
            None
        """
        self._set_parameter('StB', ~status, mode='part')

    def get_status_chA(self):
        """
        Function to get output A status

        Input:
            None

        Output:
            Status: True -turned on, False - turned off
        """
        return self.get_value('StA', mode='part') != 1

    def get_status_chB(self):
        """
        Function to get output B status

        Input:
            None

        Output:
            Status: True -turned on, False - turned off
        """
        return self.get_value('StB', mode='part') != 1

    def set_power_chB(self, power):
        """
        Function to set the power value on B output of the device

        Input:
            power: value of register from 0 to 31. (Bigger value provides more power)

        Output:
            True if setting was successful
        """
        self._set_parameter('PowerB', power, mode='part')
        return True

    def set_power_chA(self, power):
        """
        Function to set the power value on A output of the device

        Input:
            power: value of register from 0 to 31. (Bigger value provides more power)

        Output:
            True if setting was successful
        """
        self._set_parameter('PowerA', power, mode='part')
        return True

    def get_power_chB(self):
        """
        Function to get the power value on B output of the device

        Input:
            None

        Output:
            Power: Value of register from 0 to 31. (Bigger value provides more power).
        """
        return self.get_value('PowerB', mode='part')

    def get_power_chA(self):
        """
        Function to get the power value on A output of the device

        Input:
            None

        Output:
            Power: Value of register from 0 to 31. (Bigger value provides more power).
        """
        return self.get_value('PowerA', mode='part')

    def do_set_frequency(self, freq):
        """
        This is the function to set the frequency in Hz of both outputs of the device

        Input:
            freq - frequency to be set

        Output:
            True if setting was successful
        """
        self.r = self._set_mode(freq)
        q = freq % 1e8 / 1e5 * self.r * 10 // 10000
        z = freq % 1e8 / 1e5 * self.r % 1000
        x = int(freq / 1e8) * self.r + int(q)
        n_dev = to_bytes(x, 2)
        num = to_bytes(int(z), 4)
        self._set_parameter('N_dev', n_dev, mode='full')
        self._set_parameter('Num_b1', [num[2], num[3]])
        self._set_parameter('Num_b0', [num[0], num[1]])
        self._vco_calib_reset()
        return True

    def do_get_frequency(self):
        """
        This is the function to get frequency in Hz of both output of the device

        Input:
            None

        Output:
            Frequency value
        """
        n_dev = from_bytes(self.get_value('N_dev', mode='full'))
        num = from_bytes(self.get_value('Num_b0', mode='full')+self.get_value('Num_b1', mode='full'))
        return (n_dev*1e8+num*1e5)/self.r

    def _set_mode(self, freq):
        """
        Function to set status and value of frequency dividers depending on frequency value. Used only inside 'set_frequency'
        function

        Input:
            freq - Frequency to be set

        Output:
            Channel divider value
        """
        cond = []
        a = [1, 2, 4, 6, 8, 12, 16, 24, 32, 48]  # possible devider values
        for i in a:
            cond.append(self.vco_min / i <= freq< self.vco_max / i)
        for i in range(len(cond)):
            if cond[i] and a[i] == 1:
                self._set_parameter('ChDevA_st', 1, mode='part') #Turn off ChDev chA
                self._set_parameter('ChDevB_st', 1, mode='part') #Turn_off ChDev chB
                return a[i]
            elif cond[i]:
                self._set_chdev_val(a[i])					 #Set ChDev Value
                self._set_parameter('ChDevA_st', 0, mode='part') #Turn on ChDev chA
                self._set_parameter('ChDevB_st', 0, mode='part') #Turn on ChDev chB
                return a[i]

    def _set_chdev_val(self, a):
        """
        Sets certain byte sequence for ChDev value is needed only use in setting frequency

        Input:
            a - ch_dev value

        Output:
            None
        """
        chd_dict_mask = {
            2: [0x4b, 0x08, 0x00],
            4: [0x4b, 0x08, 0x40],
            6: [0x4b, 0x08, 0x80],
            8: [0x4b, 0x08, 0xc0],
            12: [0x4b, 0x09, 0x00],
            16: [0x4b, 0x09, 0x40],
            24: [0x4b, 0x09, 0x80],
            32: [0x4b, 0x09, 0xC0],
            48: [0x4b, 0x0A, 0x00]
        }
        self.c.write_data(chd_dict_mask[a])

    def _vco_calib_reset(self):
        """
        This is function to reset Voltage controlled oscillator's calibration (used only in setting frequency)

        Input:
            None

        Output:
            None
        """
        self._set_parameter('Vco_calib_st', 1, mode='part')
        self._set_parameter('Vco_calib_st', 0, mode='part')

    def reset(self):
        """
        Function to load default value for all registers

        Input:
            None

        Output:
            None
        """

        self._set_parameter('Reset_St', 1, mode='part')
        self._set_parameter('Reset_St', 0, mode='part')
        default = {
            'R112':	0x700000,
            'R111':	0x6F0000,
            'R110':	0x6E0000,
            'R109':	0x6D0000,
            'R108':	0x6C0000,
            'R107':	0x6B0000,
            'R106':	0x6A0000,
            'R105':	0x690021,
            'R104':	0x680000,
            'R103':	0x670000,
            'R102':	0x660000,
            'R101':	0x650011,
            'R100':	0x640000,
            'R99':	0x630000,
            'R98':	0x620000,
            'R97':	0x610888,
            'R96':	0x600000,
            'R95':	0x5F0000,
            'R94':	0x5E0000,
            'R93':	0x5D0000,
            'R92':	0x5C0000,
            'R91':	0x5B0000,
            'R90':	0x5A0000,
            'R89':	0x590000,
            'R88':	0x580000,
            'R87':	0x570000,
            'R86':	0x560000,
            'R85':	0x550000,
            'R84':	0x540000,
            'R83':	0x530000,
            'R82':	0x520000,
            'R81':	0x510000,
            'R80':	0x500000,
            'R79':	0x4F0000,
            'R78':	0x4E0003,
            'R77':	0x4D0000,
            'R76':	0x4C000C,
            'R75':	0x4B0800,
            'R74':	0x4A0000,
            'R73':	0x49003F,
            'R72':	0x480001,
            'R71':	0x470081,
            'R70':	0x46C350,
            'R69':	0x450000,
            'R68':	0x4403E8,
            'R67':	0x430000,
            'R66':	0x4201F4,
            'R65':	0x410000,
            'R64':	0x401388,
            'R63':	0x3F0000,
            'R62':	0x3E0322,
            'R61':	0x3D00A8,
            'R60':	0x3C0000,
            'R59':	0x3B0001,
            'R58':	0x3A8001,
            'R57':	0x390020,
            'R56':	0x380000,
            'R55':	0x370000,
            'R54':	0x360000,
            'R53':	0x350000,
            'R52':	0x340820,
            'R51':	0x330080,
            'R50':	0x320000,
            'R49':	0x314180,
            'R48':	0x300300,
            'R47':	0x2F0300,
            'R46':	0x2E07FC,
            'R45':	0x2DC0DF,
            'R44':	0x2C1FE3,
            'R43':	0x2B0000,
            'R42':	0x2A0000,
            'R41':	0x290000,
            'R40':	0x280000,
            'R39':	0x2703E8,
            'R38':	0x260000,
            'R37':	0x250404,
            'R36':	0x24008C,
            'R35':	0x230004,
            'R34':	0x220000,
            'R33':	0x211E21,
            'R32':	0x200393,
            'R31':	0x1F43EC,
            'R30':	0x1E318C,
            'R29':	0x1D318C,
            'R28':	0x1C0488,
            'R27':	0x1B0002,
            'R26':	0x1A0DB0,
            'R25':	0x190624,
            'R24':	0x18071A,
            'R23':	0x17007C,
            'R22':	0x160001,
            'R21':	0x150401,
            'R20':	0x14E048,
            'R19':	0x1327B7,
            'R18':	0x120064,
            'R17':	0x11012C,
            'R16':	0x100080,
            'R15':	0x0F064F,
            'R14':	0x0E1E70,
            'R13':	0x0D4000,
            'R12':	0x0C5001,
            'R11':	0x0B0018,
            'R10':	0x0A10D8,
            'R9':	0x090604,
            'R8':	0x082000,
            'R7':	0x0740B2,
            'R6':	0x06C802,
            'R5':	0x0500C8,
            'R4':	0x040A43,
            'R3':	0x030642,
            'R2':	0x020500,
            'R1':	0x010808,
            'R0':	0x002518
            }
        num = []
        for i in range(112, -1, -1):
            num.append(default['R'+str(i)])
        bw = [to_bytes(i, 3) for i in num]
        for i in range(len(bw)):
            self.c.write_data(bw[i])
