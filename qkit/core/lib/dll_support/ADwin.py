# -*- coding: cp1252 -*-
import ctypes, sys, os, array
if sys.platform == 'win32':
    import _winreg

# ADwin-Exception
class ADwinError(Exception):
    def __init__(self, functionName, errorText, errorNumber):
        self.functionName = functionName
        self.errorText = errorText
        self.errorNumber = errorNumber
    def __str__(self):
        if (sys.version_info[0] == 3):
            return 'Function %s, errorNumber %d: %s' % (self.functionName,  self.errorNumber, self.errorText.decode())
        else:
            return 'Function ' + self.functionName + ', errorNumber ' + str(self.errorNumber) + ': ' + self.errorText

class ADwin:
    __err = ctypes.c_long(0)
    __errPointer = ctypes.pointer(__err)

    def __init__(self, DeviceNo = 0x150, raiseExceptions = 1):

        if sys.platform == 'linux2':
            try:
                if (sys.version_info[0] == 3):
                    f = open('/etc/adwin/ADWINDIR', 'r')
                else:
                    f = file('/etc/adwin/ADWINDIR', 'r')
                self.ADwindir = f.readline()[:-1] + '/' # without newline at the end
                self.dll = ctypes.CDLL(self.ADwindir + 'lib/libadwin.so')
            except:
                raise ADwinError('__init__', 'shared library libadwin.so not found.', 200)
            f.close()
            self.dll.Set_DeviceNo(DeviceNo)
        elif sys.platform == 'darwin':
            try:
                if (sys.version_info[0] == 3):
                    f = open('/etc/adwin/ADWINDIR', 'r')
                else:
                    f = file('/etc/adwin/ADWINDIR', 'r')
                self.ADwindir = f.readline()[:-1] + '/' # without newline at the end
                self.dll = ctypes.CDLL('/Library/Frameworks/adwin32.framework/Versions/A/libadwin.5.dylib')
                self.dll.Set_DeviceNo(DeviceNo)
            except:
                raise ADwinError('__init__', 'shared library libadwin.5.dylib not found.', 200)
        else:
            try:
                aReg = _winreg.ConnectRegistry(None,_winreg.HKEY_CURRENT_USER)
                aKey = _winreg.OpenKey(aReg, r"SOFTWARE\Jäger Meßtechnik GmbH\ADwin\Directory")
                self.ADwindir = str(_winreg.EnumValue(aKey, 0)[1])
                _winreg.CloseKey(aKey)
                _winreg.CloseKey(aReg)
            except:
                raise ADwinError('__init__', 'Could not read Registry.', 200)
            try:
                self.dll = ctypes.WinDLL('ADWIN32')
                self.dll.DeviceNo = DeviceNo
            except:
                raise ADwinError('__init__', 'Windows-DLL adwin32.dll not found.', 200)
        self.raiseExceptions = raiseExceptions
        self.DeviceNo = DeviceNo
        self.version = '0.6'


    def __checkError(self, functionName):
        if self.__err.value != 0:
            if self.raiseExceptions != 0:
                raise ADwinError(functionName, self.Get_Last_Error_Text(self.__err.value), self.__err.value)

    # system control and system information
    def Boot(self, Filename):
        '''Boot initializes the ADwin system and loads the file of the operating system.'''
        if (sys.version_info[0] == 3):
            self.dll.e_ADboot(Filename.encode(), self.DeviceNo, 100000, 0, self.__errPointer)
        else:
            self.dll.e_ADboot(Filename, self.DeviceNo, 100000, 0, self.__errPointer)
        self.__checkError('Boot')

    def Test_Version(self):
        '''Test_Version checks, if the correct operating system for the processor has been loaded 
        and if the processor can be accessed.'''
        self.dll.e_ADTest_Version.restype = ctypes.c_short
        ret = self.dll.e_ADTest_Version(self.DeviceNo, 0, self.__errPointer)
        return ret

    def Processor_Type(self):
        '''Processor_Type returns the processor type of the system.'''
        ret = self.dll.e_ADProzessorTyp(self.DeviceNo, self.__errPointer)
        self.__checkError('Processor_Type')
        if (ret == 1000): ret = 9
        return ret

    def Workload(self):
        '''Workload returns the processor workload.'''
        ret = self.dll.e_AD_Workload(0, self.DeviceNo, self.__errPointer)
        self.__checkError('Workload')
        return ret

    def Free_Mem(self, Mem_Spec):
        '''Free_Mem determines the free memory for the different memory types.'''
        ret = self.dll.e_AD_Memory_all_byte(Mem_Spec, self.DeviceNo, self.__errPointer)
        self.__checkError('Free_Mem')
        return ret

    # Process control
    def Load_Process(self, Filename):
        '''Load_Process loads the binary file of a process into the ADwin system.'''
        if (sys.version_info[0] == 3):
            self.dll.e_ADBload(Filename.encode(), self.DeviceNo, 0, self.__errPointer)
        else:
            self.dll.e_ADBload(Filename, self.DeviceNo, 0, self.__errPointer)
        self.__checkError('Load_Process')

    def Start_Process(self, ProcessNo):
        '''Start_Process starts a process.'''
        self.dll.e_ADB_Start(ProcessNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Start_Process')

    def Stop_Process(self, ProcessNo):
        '''Stop_Process stops a process.'''
        self.dll.e_ADB_Stop(ProcessNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Stop_Process')

    def Clear_Process(self, ProcessNo):
        '''Clear_Process deletes a process from memory.'''
        self.dll.e_Clear_Process(ProcessNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Clear_Process')

    def Process_Status(self, ProcessNo):
        '''Process_Status returns the status of a process.'''
        ret = self.dll.e_Get_ADBPar(-100 + ProcessNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Process_Status')
        return ret

    def Get_Processdelay(self, ProcessNo):
        '''Get_Processdelay returns the parameter Processdelay for a process.'''
        ret = self.dll.e_Get_ADBPar(-90 + ProcessNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_Processdelay')
        return ret

    def Set_Processdelay(self, ProcessNo, Processdelay):
        '''Set_Processdelay sets the parameter Globaldelay for a process.'''
        self.dll.e_Set_ADBPar(-90 + ProcessNo, Processdelay, self.DeviceNo, self.__errPointer)
        self.__checkError('Set_Processdelay')

    # Transfer of global variables
    def Set_Par(self, Index, Value):
        '''Set_Par sets a global long variable to the specified value.'''
        self.dll.e_Set_ADBPar(Index, Value, self.DeviceNo, self.__errPointer)
        self.__checkError('Set_Par')
        
    def Get_Par(self, no):
        '''Get_Par returns the value of a global long variable.'''
        ret = self.dll.e_Get_ADBPar(no, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_Par')
        return ret

    def Get_Par_Block(self, StartIndex, Count):
        '''Get_Par_Block returns a number of global long variables, 
        which is to be indicated.'''
        dataType = ctypes.c_long * Count
        data = dataType(0)
        self.dll.e_Get_ADBPar_All(StartIndex, Count, data, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_Par_Block')
        return data

    def Get_Par_All(self):
        '''Get_Par_All returns all global long variables.'''
        dataType = ctypes.c_long * 80
        data = dataType(0)
        self.dll.e_Get_ADBPar_All(1, 80, data, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_Par_All')
        return data

    def Set_FPar(self, Index, Value):
        '''Set_FPar sets a global float variable to a specified value.'''
        _val = ctypes.c_float(Value)
        self.dll.e_Set_ADBFPar(Index, _val, self.DeviceNo, self.__errPointer)
        self.__checkError('Set_FPar')

    def Get_FPar(self, Index):
        '''Get_FPar returns the value of a global float variable.'''
        self.dll.e_Get_ADBFPar.restype = ctypes.c_float
        ret = self.dll.e_Get_ADBFPar(Index, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_FPar')
        return ret
        
    def Get_FPar_Block(self, StartIndex, Count):
        '''Get_FPar_Block returns a number of global float variables, 
        which is to be indicated.'''
        dataType = ctypes.c_float * Count
        data = dataType(0)
        self.dll.e_Get_ADBFPar_All(StartIndex, Count, data, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_FPar_Block')
        return data

    def Get_FPar_All(self):
        '''Get_Par_All returns all global float variables.'''
        dataType = ctypes.c_float * 80
        data = dataType(0)
        self.dll.e_Get_ADBFPar_All(1, 80, data, self.DeviceNo, self.__errPointer)
        self.__checkError('Get_FPar_All')
        return data

    # Transfer of data arrays
    def Data_Length(self, Data_No):
        '''Data_Length returns the length of an array, declared under ADbasic,
        that means the number of elements.'''
        ret = self.dll.e_GetDataLength(Data_No, self.DeviceNo, self.__errPointer)
        self.__checkError('Data_Length')
        return ret

    def SetData_Long(self, Data, DataNo, Startindex, Count):
        '''SetData_Long transfers long data from the PC into a DATA array
        of the ADwin system.'''
        if (type(Data) == list) or (type(Data) == array.array):
            # convert list to ctypes.c_long_Array
            dataType = ctypes.c_long * Count
            data = dataType(0)
            for i in range(Count):
                data[i] = Data[i]
        else: # ctypes-array
            data = Data
        self.dll.e_Set_Data(data, 2, DataNo, Startindex, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('SetData_Long')

    def GetData_Long(self, DataNo, StartIndex, Count):
        '''GetData_Long transfers long data from a DATA array of an ADwin system
        into an array.'''
        dataType = ctypes.c_long * Count
        data = dataType(0)
        self.dll.e_Get_Data(data, 2, DataNo, StartIndex, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('GetData_Long')
        return data

    def SetData_Float(self, Data, DataNo, Startindex, Count):
        '''SetData_Float transfers float data from the PC into a DATA array
        of the ADwin system.'''
        if (type(Data) == list) or (type(Data) == array.array):
            # convert list to ctypes.c_float_Array
            dataType = ctypes.c_float * Count
            data = dataType(0)
            for i in range(Count):
                data[i] = Data[i]
        else: # ctypes-array
            data = Data
        self.dll.e_Set_Data(data, 5, DataNo, Startindex, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('SetData_Float')

    def GetData_Float(self, DataNo, StartIndex, Count):
        '''GetData_Float transfers float data from a DATA array of an ADwin system
        into an array.'''
        dataType = ctypes.c_float * Count
        data = dataType(0)
        self.dll.e_Get_Data(data, 5, DataNo, StartIndex, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('GetData_Float')
        return data

    # Transfer of FIFO Arrays
    def Fifo_Empty(self, FifoNo):
        '''Fifo_Empty provides the number of free elements of a FIFO array.'''
        ret = self.dll.e_Get_Fifo_Empty(FifoNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Fifo_Empty')
        return ret

    def Fifo_Full(self, FifoNo):
        '''Fifo_Full provides the number of used elements of a FIFO array.'''
        ret = self.dll.e_Get_Fifo_Count(FifoNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Fifo_Full')
        return ret

    def Fifo_Clear(self, FifoNo):
        '''Fifo_Clear initializes the pointer for writing and reading a FIFO array.'''
        self.dll.e_Clear_Fifo(FifoNo, self.DeviceNo, self.__errPointer)
        self.__checkError('Fifo_Clear')

    def SetFifo_Long(self, FifoNo, Data, Count):
        '''SetFifo_Long transfers long data from the PC to a FIFO array of the ADwin system.'''
        if (type(Data) == list) or (type(Data) == array.array):
            # convert list to ctypes.c_long_Array
            dataType = ctypes.c_long * Count
            data = dataType(0)
            for i in range(Count):
                data[i] = Data[i]
        else: # ctypes-array
            data = Data
        self.dll.e_Set_Fifo(data, 2, FifoNo, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('SetFifo_Long')

    def GetFifo_Long(self, FifoNo, Count):
        '''GetFifo_Long transfers long FIFO data from the ADwin system to the PC.'''
        dataType = ctypes.c_long * Count
        data = dataType(0)
        self.dll.e_Get_Fifo(data, 2, FifoNo, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('GetFifo_Long')
        return data

    def SetFifo_Float(self, FifoNo, Data, Count):
        '''SetFifo_Float transfers float data from the PC into a FIFO array of the ADwin system.'''
        if (type(Data) == list) or (type(Data) == array.array):
            # convert list to ctypes.c_float_Array
            dataType = ctypes.c_float * Count
            data = dataType(0)
            for i in range(Count):
                data[i] = Data[i]
        else: # ctypes-array
            data = Data
        self.dll.e_Set_Fifo(data, 5, FifoNo, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('SetFifo_Float')

    def GetFifo_Float(self, FifoNo, Count):
        '''GetFifo_Float transfers float FIFO data from the ADwin system to the PC.'''
        dataType = ctypes.c_float * Count
        data = dataType(0)
        self.dll.e_Get_Fifo(data, 5, FifoNo, Count, self.DeviceNo, self.__errPointer)
        self.__checkError('GetFifo_Float')
        return data

    # Data arrays with string data
    def String_Length(self, DataNo):
        '''String_Length transfers the length of a data string to a DATA array.'''
        ret = self.dll.e_Get_Data_String_Length(DataNo, self.DeviceNo, self.__errPointer)
        self.__checkError('String_Length')
        return ret

    def SetData_String(self, DataNo, String):
        '''transfers a string into a DATA array.'''
        if (sys.version_info[0] == 3):
            self.dll.e_Set_Data_String(String.encode(), DataNo, self.DeviceNo, self.__errPointer)
        else:
            self.dll.e_Set_Data_String(String, DataNo, self.DeviceNo, self.__errPointer)
        self.__checkError('SetData_String')
        
    def GetData_String(self, DataNo, MaxCount):
        '''GetData_String transfers a string from a DATA array into a buffer.'''
        dataType = ctypes.c_char * (MaxCount + 2)
        data = dataType(' ')
        Count = self.dll.e_Get_Data_String(data, MaxCount+1, DataNo, self.DeviceNo, self.__errPointer)
        self.__checkError('GetData_String')
        if (sys.version_info[0] == 3):
            return data.value, Count
        else:
            return data, Count
        
    # Control and error handling
    def Get_Last_Error_Text(self, Last_Error):
        '''Get_Last_Error_Text returns an error text related to an error number.'''
        text = ctypes.create_string_buffer(256)
        pText = ctypes.byref(text)
        self.dll.ADGetErrorText(Last_Error, pText, 256)
        return text.value

    def Get_Last_Error(self):
        '''Get_Last_Error returns the number of the last error.'''
        return self.__err.value