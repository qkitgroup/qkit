"""
 ADwin-Pro II qkit driver - copy into qkit/drivers folder

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


'Parameters used on ADwin'
'Data_191[i]: output number variable => set output number on adwin module for each gate'
'Data_192[i]: voltage limit error variable => 1 if voltage limit exceeded or limits not set'
'Data_193[i]: module numbers of gates'
'Data_194[i]: individual lower voltage limit for output voltages, default=0V'
'Data_195[i]: individual upper voltage limit for output voltages, default=0V'
'Data_196[i]: time to ramp (in s) default=1s, '
'Data_197[i]: ramp start voltage value=> if no input, last set voltage is taken to be start voltage'
'Data_198[i]: write status variable => 1 while setting voltage to gate i'
'Data_199[i]: safe port bit => 1 if safe port, 0 if not (default)'
'Data_200[i]: ramp stop voltage value'
'Par_72:      test variable to read out input'
'Par_73:      module number test variable to read out input'
'Par_74:      output number test variable to read out input'
'Par_75:      number of gates used, default=200 '
'Par_76:      _activate_write_sequence variable => 1 if write sequence is activated'
"""

import ADwin as adw
import qkit
from qkit.core.instrument_base import Instrument
import logging
import time
import numpy as np
import sys

class ADwin_ProII_complete(Instrument):
    """
           DOCUMENTATION

           __init__: ADwin_ProII_SemiCon (parent class: ADwin_ProII)

             initialization parameters:

             name (STRING):
                 name of the device 
             processnumber (INT):
                 number of the process 
             processpath (STRING):
                 path to the process file *.TC1
             devicenumber (INT):
                 device number, see adconfig to identify device
             global_upper_limit_in_V (FLOAT):
                 global voltage limit for normal ports
                 normal ports are used for voltage gates
             global_lower(upper)_limit_in_V_safe_port (FLOAT):
                 global voltage limits for safe ports
                 safe ports are used by the current sources 

             work parameters (see methods descriptions for further information):

             safe_port (INT): safe ports have an inital ramping speed of 0.5V/s and 
                 a lower and upper voltage limit of 0V 
#            write_status (INT)
             output_voltage_in_V (FLOAT)
#            output_voltage_in_V_with_given_ramping_speed_in_V_per_s (FLOAT)
             ramping_time_in_s (FLOAT)
             number_of_gates (INT)
             individual_lower_voltage_limit_in_V (INT)
             individual_upper_voltage_limit_in_V (FLOAT)
             module_number (INT)
             output_number (INT)
             
             'channel' and 'gate' stand for the same thing.

    """
        
    def __init__(self, name, processnumber, processpath, devicenumber, global_lower_limit_in_V=0, 
                 global_upper_limit_in_V=0, global_lower_limit_in_V_safe_port=0, global_upper_limit_in_V_safe_port=0):
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical','ADwin_ProII'])
        
        #create ADwin instance 
        self.name = name
        self.adw = adw.ADwin(devicenumber,1)
        self.global_upper_limit_in_V = global_upper_limit_in_V
        self.global_lower_limit_in_V = global_lower_limit_in_V
        self.global_upper_limit_in_V_safe_port = global_upper_limit_in_V_safe_port
        self.global_lower_limit_in_V_safe_port = global_lower_limit_in_V_safe_port
        
        if self.global_upper_limit_in_V<self.global_lower_limit_in_V or self.global_upper_limit_in_V_safe_port<self.global_lower_limit_in_V_safe_port:
            logging.error(__name__+': lower voltage limit higher than upper limit')
            sys.exit()
        
        #boot  and load process
        self.process = processpath
        btl_dir = self.adw.ADwindir + "ADwin12.btl"
        self.adw.Boot(btl_dir)

        #load and start process
        self.processnumber=processnumber
        self.adw.Load_Process(self.process)
        time.sleep(1.0)
        self.adw.Start_Process(self.processnumber)

        #implement functions
        self.add_function('start_process')
        self.add_function('stop_process')
        self.add_function('load_process')
        self.add_function("digit_to_volt")
        self.add_function("volt_to_digit")
        self.add_function("digit_to_volt")
        self.add_function('individual_voltage_limits_setter_in_V')     
        
        
        #implement parameters

        #process delay
        self.add_parameter('process_delay', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=2147483647,
            tags=['sweep'])

        #Global LONG variables (Par_1 ... Par_80), see ADwin Driver Python documentation
        self.add_parameter('global_long', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,80), channel_prefix='Par_%d_',
            minval=-2147483648, maxval=2147483647,
            tags=['sweep'])

        #Global FLOAT variables (FPar_1 ... FPar_78), see ADwin Driver Python documentation 
        #possible input for values around zero |x|>=1.175494e-38
        self.add_parameter('global_float', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,80), channel_prefix='FPar_%d_',
            minval=-3.402823e38, maxval=3.402823e38,
            tags=['sweep'])
        
        
#        #data array, see ADwin Driver Python documentation
#        #fifo and string arrays not implemented
#        #NOT WORKING with _do_get and _do_set, see file adwin_proii_do_get_do_set 
#        self.add_parameter('data_array', type=int,
#            flags=Instrument.FLAG_GETSET,
#            channels=(1,200), channel_prefix='Data_%d_',
#            tags=['sweep'])
       
        
        #safe ports set via Data_199 array
        self.add_parameter('safe_port', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=0, maxval=1)
        
#        #write status get via Data_198 array
#        self.add_parameter('write_status', type=int,
#            flags=Instrument.FLAG_GET,
#            channels=(1,200), channel_prefix='gate%d_',
#            minval=0, maxval=1)
        
        #output voltage set via Data_200 array
        self.add_parameter('output_voltage_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        # #output voltage with given ramping speed (in V/s) set via Data_200 array
        # #get output voltage with get_output_voltage_in_V()
        # self.add_parameter('output_voltage_in_V_with_given_ramping_speed_in_V_per_s', type=list,
        #     flags=Instrument.FLAG_SET,
        #     channels=(1,200), channel_prefix='gate%d_',
        #     minval=[-10, 1e-6], maxval=[10, 1e10], units='V',
        #     tags=['sweep'])

        #ramping time in s set via Data_196 array
        self.add_parameter('ramping_time_in_s', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=1e-6, maxval=1e10, units='s',
            tags=['sweep'])

        #number of gates used set via Par_75
        self.add_parameter('number_of_gates', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=200,
            tags=['sweep'])

        #lower individual voltage limits set via Data_194 array
        self.add_parameter('individual_lower_voltage_limit_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        #upper individual voltage limits set via Data_195 array
        self.add_parameter('individual_upper_voltage_limit_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        #module number set via Data_193 array
        self.add_parameter('module_number', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=1, maxval=20,
            tags=['sweep'])

        #output number set via Data_191 array
        self.add_parameter('output_number', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=1, maxval=8,
            tags=['sweep'])

    def start_process(self, process_number):
        """start process (done automatically when creating ADwin_ProII instance)
        """
        logging.debug(__name__+'process status: %d'%self.adw.Process_Status(process_number))
        logging.info(__name__ +': starting process')
        self.adw.Start_Process(process_number)
        logging.debug(__name__+'process status: %d'%self.adw.Process_Status(process_number))

    def stop_process(self, process_number):
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(process_number))
        logging.info(__name__ +': stopping process')
        self.adw.Stop_Process(process_number)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(process_number))

    def load_process(self, process, process_number):
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(process_number))
        logging.info(__name__ +': loading process')
        self.adw.Load_Process(process)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(process_number))
     
    
#    def set_data_array(self, channel, new, startindex, count, datatype=int):
#        """set data_array
#        using SetData_Float or SetData_Int, see ADwin Driver Python documentation
#        input: channel
#        new: array to transmit to adwin
#        datatype: float or int 
#        """
#        logging.info(__name__ +': setting array variable Data_%d'%channel)
#        _parametername='Data_%d_data_array'%channel
#
#        self.set_parameter_options(_parametername,**{'type':datatype})
#
#        if datatype==float:
#            logging.debug(__name__+': data type: float')
#            self.adw.SetData_Float(new,channel,startindex,count)
#
#        if datatype==int:
#            logging.debug(__name__+': data type: int')
#            self.adw.SetData_Long(new,channel, startindex,count)
#          
#    def get_data_array(self, channel, startindex, count):   
#        logging.info(__name__ +': reading array variable Data_%d'%channel)
#        _parametername='Data_%d_data_array'%channel
#        datatype=self.get_parameter_options(_parametername)['type']
#
#        if datatype==float:
#            return self.adw.GetData_Float(channel,startindex,count)
#
#        if datatype==int:
#            return self.adw.GetData_Long(channel, startindex,count)
#   
    
    def _do_get_data_length(self,data_array_number):
        """Data_Length, see ADwin Driver Python documentation
        """
        logging.info(__name__ +': reading length of data array Data_%d'%data_array_number)
        return self.adw.Data_Length(data_array_number)

    def _do_set_global_float(self,new,channel):
        logging.info(__name__ +': setting Global FLOAT variable FPar_%d to value: %d'%(channel,new))
        self.adw.Set_FPar(channel,new)

    def _do_get_global_float(self,channel):
        logging.info(__name__ +': reading Global FLOAT variable FPar_%d'%channel)
        return self.adw.Get_FPar(channel)

    def _do_get_global_float_par_block(self, startindex, count):
        """Get_FPar_Block, see ADwin Driver Python documentation
        """
        logging.debug(__name__ +': reading Global FLOAT variable block: startindex %d, count %d'%(startindex,count))
        return self.adw.Get_FPar_Block(startindex, count)

    def _do_get_global_float_par_all(self):
        """Get_FPar_All, see ADwin Driver Python documentation
        """
        logging.debug(__name__ +': reading all Global FLOAT variables')
        return self.adw.Get_FPar_All()

    def _do_set_global_long(self,new,channel):
        logging.info(__name__ +': setting Global LONG variable Par_%d to value: %d'%(channel,new))
        self.adw.Set_Par(channel,new)

    def _do_get_global_long(self,channel):
        logging.info(__name__ +': reading Global LONG variable Par_%d'%channel)
        return self.adw.Get_Par(channel)

    def _do_get_global_long_par_block(self, startindex, count):
        """Get_Par_Block, see ADwin Driver Python documentation
        """
        logging.debug(__name__ +': reading Global LONG variable block: startindex %d, count %d'%(startindex,count))
        return self.adw.Get_Par_Block(startindex, count)

    def _do_get_global_long_par_all(self):
        """Get_Par_All, see ADwin Driver Python documentation
        """
        logging.debug(__name__ +': reading all Global LONG variables')
        return self.adw.Get_Par_All()

    def _do_set_process_delay(self,new):
        """set process_delay in s
        """
        _delayvalue=new*1e-9
        logging.info(__name__ +': setting process_delay of process Nr.%s to %f s' % (self.processnumber,_delayvalue))
        logging.debug(__name__ +': setting process_delay of process Nr.%s to %d digits' % (self.processnumber,new))
        self.adw.Set_Processdelay(self.processnumber,int(new))

    def _do_get_process_delay(self):
        """get process delay in s 
        """
        resultdigits=self.adw.Get_Processdelay(self.processnumber)
        result=resultdigits*1e-9
        logging.info(__name__ +': reading process_delay of process Nr.%s : %f s'% (self.processnumber,result))
        logging.debug(__name__ +': reading process_delay of process Nr.%s : %d digits'% (self.processnumber,resultdigits))
        return result

    def digit_to_volt(self,digit, bit_format=16):
        """function to convert digits in voltage (input can be single value, python list of np.array)
        """
        logging.debug(__name__ + ' : converting digits to V, digit value: '+ str(digit))
        #check if input is list
        if isinstance(digit, list):
            #create list of zeros
            temp_list = [0]*len(digit)
            #convert values and input into list to return
            for i in range(len(digit)):
                temp_list[i] = digit[i] * 20/(2**bit_format) - 10
            result=temp_list
        #same procedure with np.ndarray
        elif isinstance(digit, np.ndarray):
            result=digit * 20/(2**bit_format) - 10
        #same procedure with single value
        else:
            result=digit * 20/(2**bit_format) - 10
        logging.debug(__name__ + ' : converting digits to V, voltage value: '+ str(result)+'\n')
        return result

    def volt_to_digit(self,volt, bit_format=16):
        """function to convert voltage in digits (input can be single value, python list of np.array)
        """
        logging.debug(__name__ + ' : converting V to digits, voltage value: '+ str(volt))
        #check if input is list
        if isinstance(volt, list):
            #create list of zeros
            temp_list = [0]*len(volt)
            #convert values and input into list to return
            for i in range(len(volt)):
                temp_list[i] = int(round((volt[i] + 10) / (20/(2**bit_format))))
            result=temp_list
        #same procedure with np.ndarray
        elif isinstance(volt, np.ndarray):
            result=np.around((volt + 10) / (20/(2**bit_format))).astype(int)
        #same procedure with single value
        else:
            result=int(round((volt + 10) / (20/(2**bit_format))))
        logging.debug(__name__ + ' : converting V to digits, digit value: '+ str(result)+'\n')
        return result
    
    def _do_set_output_voltage_in_V(self,new,channel):
        """Set output voltage of gate 'X' (ADwin parameter: Data_200[X]). 
        If the ramping time was not set using set_gateX_ramping_time() or 
        set_output_voltage_in_V_with_given_ramping_speed_in_V_per_s(),
        initial voltage ramping time is 1µs. 
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. If the ramping speed is higher than 0.5V/s the ADwin will set it
        to 0.5V/s but there won't be any error message! The feedback is left out for 
        faster setting times.
        
        parameters:
        new (FLOAT): new voltage in V (possible values: -10 to 10)
        channel (INT): gate index 'X'
        """
        #check if channel is set:
        if channel > self.get_number_of_gates():
            logging.warning(__name__+': gate has not been set before! Voltaage not set!')
            input("Press Enter to continue.")
            sys.exit()   
        else:
            value=self.volt_to_digit(new)
            logging.info(__name__ +': setting output voltage gate %d to %f V'%(channel,new))
            self.adw.SetData_Long([value], 200, channel, 1)
            self._apply_voltage_and_check_write_status()
            #check if voltage limit was exceeded. 
            if self.adw.GetData_Long(192,channel,1)[0] == 1:
                logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
                input("Press Enter to continue.")
                #set limit error variable back to 0
                self.adw.SetData_Long([0], 192, channel, 1)
                sys.exit()        

    def _do_get_output_voltage_in_V(self,channel):
        """Read out output voltage of gate 'X' (ADwin parameter: Data_200[X]).
        
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        #check if channel is set:
        if channel > self.get_number_of_gates():
            logging.warning(__name__+': gate has not been set before! Voltaage not set!')
            input("Press Enter to continue.")
            sys.exit()
        else:
            digitvalue=self.adw.GetData_Long(200, channel, 1)[0]
            voltvalue=self.digit_to_volt(digitvalue)
            logging.info(__name__ +': reading output voltage gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
            return voltvalue
    
    # def _do_set_output_voltage_in_V_with_given_ramping_speed_in_V_per_s(self, V_and_speed, channel):
    #     """ramp voltage with given speed in V/s, ramping time accuracy = +-1ms
    #     Set output voltage of gate 'X' (ADwin parameter: Data_200[X]) with a given ramping speed.
    #     The global ramping speed of this gate will be changed, too! So setting an output voltage without speed
    #     will use the new global ramping speed.
    #     Ramping time accuracy is approximately 1 ms.
        
    #     parameters:
    #     new (FLOAT): new voltage in V (possible values: -10 to 10)
    #     channel (INT): gate index 'X' 
    #     speed (FLOAT): voltage ramping speed in V/s
    #     """
    #     new = V_and_speed[0]
    #     speed = V_and_speed[1]
    #     #check if channel is set:
    #     if channel > self.get_number_of_gates():
    #         logging.warning(__name__+': gate has not been set before! Voltaage not set!')
    #         input("Press Enter to continue.")
    #         sys.exit()
    #     else:
    #         #set limit error variable back to 0
    #         self.adw.SetData_Long([0], 192, channel, 1)
    #         #calculate and set ramping time with given speed
    #         beginningoframpvoltage=self.digit_to_volt(self.adw.GetData_Long(200,channel,1)[0]) 
    #         duration=abs((new-beginningoframpvoltage)/speed)
    #         exec('self.set_gate%d_ramping_time_in_s(%f)'%(channel,duration))
    #         #set voltage
    #         logging.info(__name__ +': setting output voltage gate %d to  %f V with ramping speed %d V/s'%(channel,new,speed))
    #         endoframpvoltage=self.volt_to_digit(new)
    #         self.adw.SetData_Long([endoframpvoltage], 200, channel, 1)
    #         self._apply_voltage_and_check_write_status()
    #         #check if voltage limit was exceeded using error variable
    #         if self.adw.GetData_Long(192,channel,1)[0] == 1:
    #             logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
    #             input("Press Enter to continue.")
    #             sys.exit()
        
    # def _do_get_output_voltage_in_V_with_given_ramping_speed_in_V_per_s(self, channel):
    #     #code copy from _do_get_output_voltage_in_V()
    #     """Read out output voltage of gate 'X' (ADwin parameter: Data_200[X]).
        
    #     return value (FLOAT): voltage in V (possible values: -10 to 10)
    #     """
    #     #check if channel is set:
    #     if channel > self.get_number_of_gates():
    #         logging.warning(__name__+': gate has not been set before! Voltaage not set!')
    #         input("Press Enter to continue.")
    #         sys.exit()
    #     else:
    #         digitvalue=self.adw.GetData_Long(200, channel, 1)[0]
    #         voltvalue=self.digit_to_volt(digitvalue)
    #         logging.info(__name__ +': reading output voltage gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
    #         speed = self._do_get_ramping_time_in_s(channel)
    #         return [voltvalue, speed]

    def _activate_write_sequence(self, value):
        """Internal function, (de)activate ADwin write sequence for gate 'X' (ADwin parameter: Par_76).
        
        parameters:
        value (INT): 0=activate, 1=deactivate    
        """
        if value==1:
            logging.info(__name__+': write sequence initiated')
            self.set_Par_76_global_long(1)
        else:
            self.set_Par_76_global_long(0)
            logging.info(__name__+': write sequence stopped')

    def _do_set_output_number(self,value,channel):
        """Allocate ADwin output number to gate 'X' (ADwin parameter: Data_191[X]).
        
        parameters: 
        value (INT): output number (possible values: 1 to 200) (INT): gate index
        """
        logging.info(__name__ + ': setting output number of gate %d to %d'%(channel,value))
        self.adw.SetData_Long([value], 191, channel, 1)

    def _do_get_output_number(self,channel):
        """Read out ADwin output number of gate 'X' (ADwin parameter: Data_191[X]).
        
        parameters: 
        X (INT): gate index 
        return value (INT): output number (possible values: 1 to 200)
        """
        output=self.adw.GetData_Long(191, channel, 1)[0]
        logging.info(__name__ + ': reading output number of gate %d : %d' %(channel,output))
        return output

    def _do_set_module_number(self,value,channel):
        """Allocate ADwin module number to gate 'X' (ADwin parameter: Data_193[X]).
        
        parameters: 
        value (INT): module number (possible values: 1 to 20)
        X (INT): gate index
        """
        logging.info(__name__ + ': setting module number of gate %d to %d'%(channel,value))
        self.adw.SetData_Long([value], 193, channel, 1)

    def _do_get_module_number(self,channel):
        """Read out ADwin module number of gate 'X' (ADwin parameter: Data_193[X]).
        
        parameters: 
        X (INT): gate index 
        return value (INT): module number (possible values: 1 to 20)
        """
        output=self.adw.GetData_Long(193, channel, 1)[0]
        logging.info(__name__ + ': reading module number of gate %d : %d' %(channel,output))
        return output

    def individual_voltage_limits_setter_in_V(self, value1, value2, gate):
        """Set individual upper and lower voltage limits for a gate 'X' and prevent from 
        initial error caused if the voltage limits are not set (Error variable - ADwin parameter: Data_192[X]).
        The minimum and the maximum of (value1, value2) are determined and set as lower or 
        upper voltage limits using individual_lower(upper)_voltage_limit_in_V(), respectively.
        
        parameters:
        value1(2) (FLOAT): voltage limits in V (possible values: -10 to 10)
        gate (INT): gate index 'X' 
        """
        lowerlimit=min(value1,value2)
        upperlimit=max(value1,value2)
        exec("self.set_gate%d_individual_lower_voltage_limit_in_V(lowerlimit)"% gate)
        exec("self.set_gate%d_individual_upper_voltage_limit_in_V(upperlimit)"% gate)
        logging.info(__name__ +': individual voltage limits gate %d: %d , %d'%(gate,lowerlimit,upperlimit))

    def _do_set_individual_lower_voltage_limit_in_V(self,new,channel):
        """Set individual lower voltage limit in V for gate 'X' (ADwin parameter: Data_194[X]). 
        The value set has to be within the boundaries given by global_lower(upper)_limit_in_V_(safe_port).
        
        parameters:
        new (FLOAT): individual lower voltage limit in V (possible values: -10 to 10)
        X (INT): gate index
        """
        #set limit error variable back to 0
        self.adw.SetData_Long([0], 192, channel, 1)
        #compare with global limit depending on safe port bit
        safeportbit=self.adw.GetData_Long(199, channel, 1)[0]
        if safeportbit:
            globallowerlimit=self.global_lower_limit_in_V_safe_port
            globalupperlimit=self.global_upper_limit_in_V_safe_port
        else:
            globallowerlimit=self.global_lower_limit_in_V
            globalupperlimit=self.global_upper_limit_in_V

        if new<=globalupperlimit and new>=globallowerlimit:
            value=self.volt_to_digit(new)
            self.adw.SetData_Long([value], 194, channel, 1)
            logging.info(__name__ +': setting individual lower voltage limit gate %d to  %f V'%(channel,new))
        else:
            logging.error(__name__+': given lower voltage limit not in global limits')
            sys.exit()

    def _do_get_individual_lower_voltage_limit_in_V(self,channel):
        """Read out individual lower voltage limit of gate 'X' in V (ADwin parameter: Data_194[X]).
        
        parameters:
        X (INT): gate index 
        return value (FLOAT): Individual lower voltage limit in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(194, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading individual lower voltage limit gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue

    def _do_set_individual_upper_voltage_limit_in_V(self,new,channel):
        """Set individual upper voltage limit in V for gate 'X' (ADwin parameter: Data_195[X]). 
        The value set has to be within the boundaries given by global_lower(upper)_limit_in_V_(safe_port).
        
        parameters:
        new (FLOAT): individual upper voltage limit in V (possible values: -10 to 10)
        X (INT): gate index
        """
        #set limit error variable back to 0
        self.adw.SetData_Long([0], 192, channel, 1)
        #compare with global limit depending on safe port bit
        safeportbit=self.adw.GetData_Long(199, channel, 1)[0]
        if safeportbit:
            globallowerlimit=self.global_lower_limit_in_V_safe_port
            globalupperlimit=self.global_upper_limit_in_V_safe_port
        else:
            globallowerlimit=self.global_lower_limit_in_V
            globalupperlimit=self.global_upper_limit_in_V

        if new<=globalupperlimit and new>=globallowerlimit:
            value=self.volt_to_digit(new)
            logging.info(__name__ +': setting individual upper limit gate %d to  %f V'%(channel,new))
            self.adw.SetData_Long([value], 195, channel, 1)
        else:
            logging.error(__name__+': given upper limit not in global limits')
            sys.exit()
    
    def _do_get_individual_upper_voltage_limit_in_V(self,channel):
        """Read out individual upper voltage limit of gate 'X' in V (ADwin parameter: Data_195[X]).
        
        parameters:
        X (INT): gate index 
        return value (FLOAT): Individual upper voltage limit in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(195, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading individual upper voltage limit gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue

    def _apply_voltage_and_check_write_status(self):
        """Internal function, apply voltage to gate 'X' and check write status in while loop 
        (Status variable - ADwin parameter: Data_198[X]). Python script will only continue if 
        write status is switched back from 1 to 0 on all gates after applying voltage to gate.
        """
        nrofgates=self.get_number_of_gates()
        write_status_variables=np.ones(nrofgates)
        checksum=1

        #activate write sequence - adwin starts ramping up from this point
        self._activate_write_sequence(1)
        #check write status
        #takes approximately .7ms per cycle in for loop below => the time between two ramps is 
        #in the order of the number of gates times .7ms, the ramping time of itself is not
        #affected by this
        while checksum!=0:
            for channel in range(1,nrofgates+1):
                value=self.adw.GetData_Long(198,channel,1)[0]
                write_status_variables[channel-1]=value
                ##To see if ADwin is setting voltages check:
                #print(write_status_variables)
                checksum=np.sum(write_status_variables)

        #stop write sequence
        self._activate_write_sequence(0)
        logging.info(__name__+': voltage set to gate')

    def _do_set_number_of_gates(self,value):
        """Set number of gates used in setup (ADwin parameter: Par_75).
        Initial number is 200.
        
        parameters:
        value (INT): number of gates (possible values: 1 to 200)
        """
        logging.info(__name__ + ': setting number of gates to %d'%(value))
        self.set_Par_75_global_long(value)

    def _do_get_number_of_gates(self):
        """Read out number of gates used in setup (ADwin parameter: Par_75).
        
        return value (INT): number of gates (possible values: 1 to 200)
        """
        output=self.get_Par_75_global_long()
        logging.info(__name__ + ': reading number of gates: %d ' % output)
        return output

    def _do_set_ramping_time_in_s(self,value,channel):
        """Set voltage ramping time in s for gate 'X' (ADwin parameter: Data_196[X]). 
        This function will be overrun if set_gateX_output_voltage_in_V_with_given_ramping_speed_in_V_per_s() is used. 
        default value: 1µs 
        
        parameters:
        value (FLOAT): ramping time in s (possible values: 1e-6 to 1e10)
        X (INT): gate index
        """
        logging.info(__name__ + ': setting time to ramp to %f s'%(value))
        microseconds=int(value*1e6)
        #check if given ramping time is an integer value of µs
        if microseconds%1!=0:
            logging.warning(__name__ +': time has to be an integer value of µs')
            value=input("New ramping time value: ")
        self.adw.SetData_Long([microseconds], 196, channel, 1)

    def _do_get_ramping_time_in_s(self,channel):
        """Read out voltage ramping time in s of gate 'X' (ADwin parameter: Data_196[X]).
        
        parameters: 
        X (INT): gate index 
        return value (FLOAT): voltage ramping time in s (possible values: 1e-6 to 1e10)
        """
        output=self.adw.GetData_Long(196, channel, 1)[0]
        output=output*1e-6
        logging.info(__name__ + ': reading time to ramp for gate %d : %d s' %(channel,output))
        return output
    
    def _do_set_safe_port(self,new,channel):
        """Set gate 'X' as safe port (ADwin parameter: Data_199[X]).
        
        parameters: 
        new (INT): 1=safe port, 0=no safe port (possible values: 1, 0)
        X (INT): gate index
        """
        logging.info(__name__ + ': configuring gate %d as a safe port (0: False, 1: True): %d'%(channel,new))
        self.adw.SetData_Long([new], 199, channel, 1)

    def _do_get_safe_port(self,channel):
        """Read out if gate 'X' is a safe port (ADwin parameter: Data_199[X]).
        
        return value (INT): 1=safe port, 0=no safe port (possible values: 1, 0)
        """
        value=self.adw.GetData_Long(199, channel, 1)[0]
        logging.info(__name__ + ': reading if gate %d is a safe port (0: False, 1: True): %d'%(channel,value))
        return value

#    def _do_get_write_status(self, **kwarg):
#        pass
#
#    def _do_set_write_status(self, **kwarg):
#        pass
#        
#    def _do_get_data_array(self, **kwarg):
#        pass
#    
#    def _do_set_data_array(self, **kwarg):
#        pass

    def initialize_gates(self, number,  lower_limit=0, upper_limit=0):
        '''This function sets the number of  gates (including current sources)
        and distributes them on the modules
        starting at module 1 and filling up all 8 outputs. Then module 2 etc. is
        filled up. The modules have to exist.
        Gates 1-3 are reserved for the current sources, meaning voltage gates 
        from 4 to n are initialized.
        
        parameters:
            number: number of voltage gates NOT including current sources.
            lower_limit: initializes voltage gates with given lower limit
            upper_limit: initializes voltage gates with given uppper limit
        '''
        #initailize gates 
        if number < 0:
            logging.warning(__name__+': number of gates must not be negative!')
            input("Press Enter to continue.")
            sys.exit()
        else:
            number = number 
            self.set_number_of_gates(number)
            rest = int(number % 8)
            full_modules = int(np.trunc(number / 8))
        
            #fill up modules:
            gate = 1  
            #fill up full modules
            for module in range(1,full_modules+1):
                for output in range(1,8+1):
                    self.set('gate%d_module_number'% gate, module)
                    self.set('gate%d_output_number'% gate, output)
                    if gate in [1, 2, 3]:
                        self.set('gate%d_safe_port'% gate, 1)    
                    gate = gate +1
                
            #fill up not full module:
            for output in range(1, rest+1):
                self.set('gate%d_module_number'% gate, full_modules+1)
                self.set('gate%d_output_number'% gate, output)
                if gate in [1, 2, 3]:
                        self.set('gate%d_safe_port'% gate, 1) 
                gate = gate +1
                
            if (gate-1) != (number):
                logging.warning(__name__+': Error while initializing voltage gates!')
                input("Press Enter to continue.")
                sys.exit()
       
        #initialize voltage limits 
        #limits for current sources:
        for gate in range(1, 3+1):
            self.individual_voltage_limits_setter_in_V(-10, 10, gate)
            
        #initialize voltage limits for votage gates:
        for gate in range(4, number+1):
            self.individual_voltage_limits_setter_in_V(lower_limit, upper_limit, gate)
            
            
    #The following functions are for the use of current sources that are set with a voltage 
    #by the ADwin
    def set_field_1d(self, direction, field):
        '''Sets a magnetic field in a direction (1=x, 2=y, 3=z) in Tesla.
        This function is for current sources that adjust their current
        linearly to the output voltage that the ADwin gives out. The
        gates are initialized as safe ports.
        Negative field values invert the direction.
        DOES NOT OVERRIDE FIELD VALUES OF OTHER DIRECTIONS PREVIOUSLY SET!
        
        Gate 1 = x-direction
        Gate 2= y-direction
        Gate 3 = z-direction
        
        '''
        translation_factor = 2 #factor (Ampere/Volts) that is used by the current sources from input to output
        
        #coil calibration parameters
        x_calib = 1 #in Tesla/Amps
        y_calib = 1 #in Tesla/Amps
        z_calib = 1 #in Tesla/Amps
        
        x_max_current = 10 #maximal current in Amps through coil x
        y_max_current = 10 #maximal current in Amps through coil y
        z_max_current = 10 #maximal current in Amps through coil z
        
        #set  voltage 
        if direction == 1:
            voltage_x = field / x_calib / translation_factor
            if abs(voltage_x) <=  10 and abs(voltage_x) <= (x_max_current / translation_factor):
                self.set_gate1_output_voltage_in_V(voltage_x)
            else:
                logging.warning(__name__+': voltage in x-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 2:
            voltage_y = field / y_calib / translation_factor
            if abs(voltage_y) <=  10 and abs(voltage_y) <= (y_max_current / translation_factor):
                self.set_gate2_output_voltage_in_V(voltage_y)
            else:
                logging.warning(__name__+': voltage in y-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 3:
            voltage_z = field / z_calib / translation_factor
            if abs(voltage_z) <=  10 and abs(voltage_z) <= (z_max_current / translation_factor):
                self.set_gate3_output_voltage_in_V(voltage_z)
            else:
                logging.warning(__name__+': voltage in z-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction < 1 or direction > 3:
            logging.warning(__name__+': direction parameter has to be 1, 2, or 3.')
            input("Press Enter to continue.")
            sys.exit()
              
            
    def set_field_3d(self, amplitude, theta, phi, theta_corr=0, phi_corr=0):
        '''Sets a magnetic field using spherical coordinates in degrees.
        Negative amplitudes invert the carthesian direction.
        
        Parameters:
            amplitude: field strengh in Tesla
            theta: azimuthal angle between 0 and 180°
            phi: polar angle betweeen 0 and 360°
            theta_corr: correction angle added to theta
            phi_corr: correction angle added to phi
        '''
        translation_factor = 2 #factor (Ampere/Volts) that is used by the current sources from input to output
        
        #coil calibration parameters
        x_calib = 1 #in Tesla/Amps
        y_calib = 1 #in Tesla/Amps
        z_calib = 1 #in Tesla/Amps
        
        x_max_current = 10 #maximal current in Amps through coil x
        y_max_current = 10 #maximal current in Amps through coil y
        z_max_current = 10 #maximal current in Amps through coil z
        
        #calculate field components in carthesian coordinates
        amplitude_x = amplitude * np.sin(np.deg2rad(theta+theta_corr)) * np.cos(np.deg2rad(phi+phi_corr))
        amplitude_y = amplitude * np.sin(np.deg2rad(theta+theta_corr)) * np.sin(np.deg2rad(phi+phi_corr))
        amplitude_z = amplitude * np.cos(np.deg2rad(theta+theta_corr))
        
        #setting voltages
        #set x voltage 
        voltage_x = amplitude_x / x_calib / translation_factor
        if abs(voltage_x) <=  10 and abs(voltage_x) <= (x_max_current / translation_factor):
            self.set_gate1_output_voltage_in_V(voltage_x) 
        else:
            logging.warning(__name__+': voltage in x-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set y voltage 
        voltage_y = amplitude_y / y_calib / translation_factor
        if abs(voltage_y) <=  10 and abs(voltage_y) <= (y_max_current / translation_factor):
            self.set_gate2_output_voltage_in_V(voltage_y)
        else:
            logging.warning(__name__+': voltage in y-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set z voltage 
        voltage_z = amplitude_z / z_calib / translation_factor
        if abs(voltage_z) <=  10 and abs(voltage_z) <= (z_max_current / translation_factor):
            self.set_gate3_output_voltage_in_V(voltage_z)
        else:
            logging.warning(__name__+': voltage in z-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
            
            


if __name__ == "__main__":

    ##device test routine
    ##**************************************************************

    qkit.start()
    #1)create instance - implement global voltage limits when creating instance
    bill = qkit.instruments.create('bill', 'ADwin_ProII_complete', processnumber=1, processpath='/V/GroupWernsdorfer/People/Sven/ramptest.TC1',
                                   devicenumber=1, global_lower_limit_in_V=-1, global_upper_limit_in_V=3, global_lower_limit_in_V_safe_port=-1, 
                                   global_upper_limit_in_V_safe_port=3)

    print(10*'*'+'Initialization complete'+10*'*')
#
#
#    #2)set number of gates
#    logging.debug(__name__+": test routine : 2)set total number of gates")
#    bill.set_number_of_gates(8)
#    bill.get_number_of_gates()
#
#    #3)set module numbers and output numbers
#    logging.debug(__name__+": test routine : 3a)module numbers of the gates")
#    #here: outputs on module 4
#    for gate in range(1,bill.get_number_of_gates()+1):
#        exec('bill.set_gate%d_module_number(2)'%gate)
#        exec('bill.get_gate%d_module_number()'%gate)
#
#    logging.debug(__name__+": test routine : 3b)output numbers of the gates")
#    #here: outputs on module 4
#    for gate in range(1,bill.get_number_of_gates()+1):
#        exec('bill.set_gate%d_output_number(gate)'%gate)
#        exec('bill.get_gate%d_output_number()'%gate)
#
#    #4)set ramping times for each gate in s
#    # necessary for set_out without given speed
#    #bill.set_gate1_ramping_time_in_s(0.1)
#    #bill.get_gate1_ramping_time_in_s()
#
#    #5)set safe ports
#    logging.debug(__name__+": test routine : 5)set safe ports")
#    bill.set_gate1_safe_port(0)
#    bill.get_gate1_safe_port()
#
#    #6)set individual voltage limits => have to be set, otherwise limits=0V, error
#    #set limits before setting voltages, otherwise limits and inputs will be compared, which can return errors
#    for i in range(1,bill.get_number_of_gates()+1):
#        bill.individual_voltage_limits_setter_in_V(-1,3,i)
#
#
#    #7)set voltages
#    logging.debug(__name__+": test routine : 7)set voltages in V and ramping speed in V/s")
#    for j in range(0,3):
#        print("setting to 1V")
#        bill.set_gate1_output_voltage_in_V_with_given_ramping_speed_in_V_per_s(1,speed=0.5)
#        print("setting to 0V")
#        bill.set_gate1_output_voltage_in_V_with_given_ramping_speed_in_V_per_s(0,speed=0.5)
#
#    #uncomment the following lines to read documentation
#    **************************************************************
#
#    print(ADwin_ProII.__init__.__doc__)
#    print(ADwin_ProII._do_set_output_voltage_in_V_with_given_ramping_speed_in_V_per_s.__doc__)
#    print(ADwin_ProII._activate_write_sequence.__doc__)
#    print(ADwin_ProII._do_set_output_number.__doc__)
#    print(ADwin_ProII._do_get_output_number.__doc__)
#    print(ADwin_ProII._do_set_module_number.__doc__)
#    print(ADwin_ProII._do_get_module_number.__doc__)
#    print(ADwin_ProII.individual_voltage_limits_setter_in_V.__doc__)
#    print(ADwin_ProII._do_set_individual_lower_voltage_limit_in_V.__doc__)
#    print(ADwin_ProII._do_get_individual_lower_voltage_limit_in_V.__doc__)
#    print(ADwin_ProII._do_set_individual_upper_voltage_limit_in_V.__doc__)
#    print(ADwin_ProII._do_get_individual_upper_voltage_limit_in_V.__doc__)
#    print(ADwin_ProII._apply_voltage_and_check_write_status.__doc__)
#    print(ADwin_ProII._do_set_number_of_gates.__doc__)
#    print(ADwin_ProII._do_get_number_of_gates.__doc__)
#    print(ADwin_ProII._do_set_ramping_time_in_s.__doc__)
#    print(ADwin_ProII._do_get_ramping_time_in_s.__doc__)
#    print(ADwin_ProII._do_set_out.__doc__)
#    print(ADwin_ProII._do_get_output_voltage_in_V.__doc__)
#    print(ADwin_ProII._do_set_safe_port.__doc__)
#    print(ADwin_ProII._do_get_safe_port.__doc__)
