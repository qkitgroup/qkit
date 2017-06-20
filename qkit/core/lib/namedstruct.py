# namedstruct.py, module to (un)pack C structures by name to/from a dictionary
# Reinier Heeres <reinier@heeres.eu>, 2008
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

import struct
import types

S8 = 'b'        # Signed byte, unpacked as list of ints
U8 = 'B'        # Unsigned byts, unpacked as list of ints
S16 = 'h'       # Signed short, unpacked as list of ints
U16 = 'H'       # Unsigned short, unpacked as list of ints
S32 = 'i'       # Signed int, unpacked as list of ints
U32 = 'I'       # Unsigned int, unpacked as list of ints
S64 = 'q'       # Signed long long, unpacked as list of longs
U64 = 'Q'       # Unsigned long long, unpacked as list of longs
S = 's'         # String, unpacked as string with exact length 
STRING = 's2'   # String, unpacked as string chopped at terminating 0-byte
C = 'c'         # List of characters
FLOAT = 'f'     # Float
DOUBLE = 'd'    # Double

TYPE_LEN = {
    S8: 1,
    U8: 1,
    S16: 2,
    U16: 2,
    S32: 4,
    U32: 4,
    S64: 8,
    U64: 8,
    C: 1,
    S: 1,
    STRING: 1,
    FLOAT: 4,
    DOUBLE: 8,
}

def format_to_structstr(format, alignment='='):
    '''Return struct module format string for a format array.'''

    formatcnt = {}
    structstr = alignment

    ofs = 0
    for line in format:
        name, type, dlen = line
        if type == STRING:
            type = S

        if dlen == 1:
            structstr += type
        else:
            structstr += '%d%s' % (dlen, type)
#        print 'ofs %d, name %s, type %s, num %d' % (ofs, name, type, dlen)

        if type in TYPE_LEN:
            ofs += dlen * TYPE_LEN[type]

        if type not in formatcnt:
            formatcnt[type] = 1
        else:
            formatcnt[type] += 1

    return structstr

def unpack(buf, format, alignment='='):
    '''Unpack a buffer according to a format array.'''

    if isinstance(format, struct.Struct):
        list = format.unpack(buf)
    else:
        structstr = format_to_structstr(format, alignment=alignment)
        list = struct.unpack(structstr, buf)

    ret = {}
    i = 0
    for line in format:
        name, dtype, dlen = line
        if dtype == STRING:
            ret[name] = str(list[i])
            zeropos = ret[name].find('\x00')
            if zeropos != -1:
                ret[name] = ret[name][:zeropos]
            i += 1
        elif dtype == S:
            ret[name] = list[i]
            i += 1
        else:
            if dlen == 1:
                ret[name] = list[i]
            else:
                ret[name] = list[i:i+dlen]
            i += dlen

    return ret

# FIXME: add alignment flag in a proper way
def pack(format, **kwargs):
    list = []
    for line in format:
        name, dtype, dlen = line
        if name in kwargs:
            if type(kwargs[name]) in (types.TupleType, types.ListType):
                for element in kwargs[name]:
                    list.append(element)
            else:
                list.append(kwargs[name])
            del kwargs[name]
        elif dtype in [S, STRING]:
            list.append('')
        elif dtype in (U8, S8, U16, S16, U32, S32, U64, S64):
            for i in range(dlen):
                list.append(0)
        else:
            for i in range(dlen):
                list.append(None)

    if len(kwargs.keys()) > 0:
        print 'namedstruct.pack(): arguments not converted: %r' % kwargs.keys()

    if isinstance(format, struct.Struct):
        return format.pack(*list)
    else:
        structstr = format_to_structstr(format)
        return struct.pack(structstr, *list)

def calcsize(format, alignment='='):
    structstr = format_to_structstr(format, alignment=alignment)
    return struct.calcsize(structstr)

class NamedStruct:

    def __init__(self, format, alignment='='):
        self._format = format
        self._alignment = alignment
        self._structstr = format_to_structstr(self._format, alignment=alignment)
        self.struct = struct.Struct(self._structstr)
        self.size = self.struct.size

    def pack(self, **kwargs):
        return pack(self.struct, **kwargs)

    def unpack(self, buf):
        return unpack(buf, self._format, alignment=self._alignment)
