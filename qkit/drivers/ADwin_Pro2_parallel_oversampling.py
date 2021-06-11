'''
TODO: 
    take out gatecheck in set_out IF its a time problem
    implement funktion _do_set_output_parallel with ADwin basic file
    ramping speed in ADwin basic file has to take voltage range into account
    check value of time.sleep=10-5s in set_outputs. maybe 10-6 is also ok and faster
    check maximal  averaging inputs
    check maximal gates that can be ramped parallel
    


'''

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
'Data_190[i]: analog input gate i'
'Data_191[i]: output number variable => set output number on adwin module for each gate'
'Data_192[i]: limit error variable => 1 if voltage limit exceeded or limits not set'
'Data_193[i]: module numbers of gates'
'Data_194[i]: individual lower limit for output voltages, default=0V'
'Data_195[i]: individual upper limit for output voltages, default=0V'
'Data_199[i]: safe port bit => 1 if safe port, 0 if not (default)'
'Data_200[i]: ramp stop value'

'Par_69:      number of averages for input measurement'
'Par_71:      analog input module number'
'Par_75:      number of gates used, default=200 '
'Par_76:      run variable => 1 if device is run'
'FPar_77:     ramping speed in Volts/second normal ports'
'Par_78:      channel which is ramped. only it will be changed during an event'
"""


import ADwin as adw
import qkit
from qkit.core.instrument_base import Instrument
import logging
import time
import numpy as np
import sys


class ADwin_Pro2_parallel_oversampling(Instrument):
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
                 normal ports have a initial ramping speed of 1V/s and a 
                 lower and upper voltage limit of 0V. These speeds are hard coded into 
                 the basic file.
                
                 out ; short for output_voltage_in_V(FLOAT)
                 number_of_gates (INT)
                 individual_lower_voltage_limit_in_V (INT)
                 individual_upper_voltage_limit_in_V (FLOAT)
                 module_number (INT)
                 output_number (INT)
             
             INPORTATANT FUNCTIONS:
                 set_out_parallel
                 initialize_gates(number, lower_limit, upper_limit)
                 set_field_1d(direction, amplitude)
                 set_field_3d(amplitude, theta, phi)
                 

    """
        
    def __init__(self, name, processnumber, processpath, devicenumber, global_lower_limit_in_V=0, 
                 global_upper_limit_in_V=0, global_lower_limit_in_V_safe_port=0, global_upper_limit_in_V_safe_port=0):
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical','ADwin_ProII'])
        
        #create ADwin instance 
        self.name = name
        self.processnumber=processnumber
        self.process = processpath
        self.adw = adw.ADwin(devicenumber,1)
        self.global_upper_limit_in_V = global_upper_limit_in_V
        self.global_lower_limit_in_V = global_lower_limit_in_V
        self.global_upper_limit_in_V_safe_port = global_upper_limit_in_V_safe_port
        self.global_lower_limit_in_V_safe_port = global_lower_limit_in_V_safe_port
        
        if self.global_upper_limit_in_V<self.global_lower_limit_in_V or self.global_upper_limit_in_V_safe_port<self.global_lower_limit_in_V_safe_port:
            logging.error(__name__+': lower voltage limit higher than upper limit')
            sys.exit()
        
        #stop all ADwin processes before and give them time to go to the Finish: part to ramp down voltages
        for i in range(1, 12+1):
            self.adw.Stop_Process(i)
        time.sleep(0.2)
        if self.adw.Get_Par(76) == -1:
            print("Ramping down all outputs (gates + current sources) to 0 Volts...\nGreen LED at DAC module indicates ongoing ramping action.")
            while self.adw.Get_Par(76) == -1:
                    time.sleep(0.1)  
            print("All outputs are ramped down to 0 Volts.")
        else:
            print("Outputs not being ramped down.")
        
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
        self.add_function('individual_voltage_limits_setter_in_V')     
        
        
        #implement parameters

        #process delay
        self.add_parameter('process_delay', type=int,
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
        
        #safe ports set via Data_199 array
        self.add_parameter('safe_port', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=0, maxval=1)
        
        #output voltage set via Data_200 array
        self.add_parameter('out', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(4,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        
        #output voltage set via Data_200 array
        self.add_parameter('output_voltage_current_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,3), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
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

        #analog input read out via Data_190 array
        self.add_parameter('input_voltage', type=float,
            flags=Instrument.FLAG_GET,
            channels=(1,200), channel_prefix='ch%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        
        #ramping speed normal ports in V/s
        self.add_parameter('ramping_speed_normal_ports', type=float,
            flags=Instrument.FLAG_GET,
            minval=0.0, maxval=100.0, #units='V/s',
            tags=['sweep'])
        
        #state of gate X if it uses oversampling =1 or not =0
        self.add_parameter('oversampling_state', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=0, maxval=1,
            tags=['sweep'])
        
        #global amount of oversampling divisions between two bits
        self.add_parameter('oversampling_divisions', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=1000,
            tags=['sweep'])
        
        #voltage ranges of outputs. symmetric around 0V. 
        #a value of 10 means +-10V
        self.add_parameter('voltage_range', type=float,
            flags=Instrument.FLAG_GET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        

        
    # def bootload_process(self):
    #     '''bootloads the process given in the processpath.
    #     '''
    #     btl_dir = self.adw.ADwindir + "ADwin12.btl"
    #     self.adw.Boot(btl_dir) 

    def start_process(self):
        """start process (done automatically when creating ADwin_ProII instance)
        """
        #stop all ADwin processes before and give them time to go to the Finish: part to ramp down voltages
        for i in range(1, 12+1):
            self.adw.Stop_Process(i)
        time.sleep(1)
        while self.get_Par_76_global_long() != 0:
                time.sleep(0.1)
        logging.debug(__name__+'process status: %d'%self.adw.Process_Status(self.processnumber))
        logging.info(__name__ +': starting process')
        self.adw.Start_Process(self.processnumber)
        logging.debug(__name__+'process status: %d'%self.adw.Process_Status(self.processnumber))

    def stop_process(self):
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        logging.info(__name__ +': stopping process')
        self.adw.Stop_Process(self.processnumber)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        time.sleep(0.2)
        if self.adw.Get_Par(76) == -1:
            print("Ramping down all gates to 0 Volts...\nGreen LED at DAC module indicates ongoing ramping action.")
            while self.adw.Get_Par(76) == -1:
                    time.sleep(0.1)  
            print("All outputs are ramped down to 0 Volts.")
        else:
            print("Outputs not being ramped down.")

    def load_process(self):
        #stop all ADwin processes before and give them time to go to the Finish: part to ramp down voltages
        for i in range(1, 12+1):
            self.adw.Stop_Process(i)
        time.sleep(1)
        while self.get_Par_76_global_long() != 0:
                time.sleep(0.1)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        logging.info(__name__ +': loading process')
        self.adw.Load_Process(self.process)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))  
    
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
        
    def _do_get_input_voltage(self, channel, averages=100):
        """Read out voltage of analog input 'X' (ADwin parameter: Data_190[X]).
        module number is fixed in basic file and cannot be changed by driver yet.
        
        averages: 0 means no averaging so only one data point 
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        if averages >= 0 and averages<60000: 
            #set number of averages
            self.set_Par_69_global_long(averages)
            #activate input readout
            self._activate_ADwin(2)
            #wait for ADwin to finish:
            while self.get_Par_76_global_long() != 0:
                time.sleep(1e-4)          
            digitvalue=self.adw.GetData_Long(190, channel, 1)[0]
            voltvalue=self.digit_to_volt(digitvalue, channel)
            logging.info(__name__ +': reading voltage analog input %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
            return voltvalue
        else:
            logging.warning(__name__+': number of averages must bigger than 0 and smaller than 60 000!.')
            input("Press Enter to continue.")
            sys.exit() 
          
    
    def _do_set_process_delay(self,new):
        """set process_delay in cycles (1e-9s) of the ADwin.
        """
        logging.info(__name__ +': setting process_delay of process Nr.%s to %f s' % (self.processnumber, new*1e-9))
        logging.debug(__name__ +': setting process_delay of process Nr.%s to %d digits' % (self.processnumber,new))
        self.adw.Set_Processdelay(self.processnumber,new)

    def _do_get_process_delay(self):
        """get process delay in cycles. 
        """
        resultdigits = self.adw.Get_Processdelay(self.processnumber)
        result = resultdigits*1e-9
        logging.info(__name__ +': reading process_delay of process Nr.%s : %f s'% (self.processnumber, result))
        logging.debug(__name__ +': reading process_delay of process Nr.%s : %d digits'% (self.processnumber,resultdigits))
        return resultdigits
    
    def _do_set_ramping_speed_normal_ports(self, speed):
        '''sets the ramping speed in Volts/seconds for normal ports
        '''
        logging.info(__name__ +': setting ramping speed for normal ports of process Nr.%s to %f s' % (self.processnumber, speed))
        self.set_FPar_77_global_float(speed)
        
    def _do_get_ramping_speed_normal_ports(self):
        '''gets the ramping speed in Volts/seconds for normal ports
        '''
        return self.get_FPar_77_global_float()
          
    def digit_to_volt(self, digit, gate, bit_format=16):
        """function to convert digits in voltage (input can be single value, python list of np.array)
        """
        #get voltage range of the gate
        V_max = self.get('gate%d_voltage_range'%gate)
        logging.debug(__name__ + ' : converting digits to V, digit value: '+ str(digit))
        #check if input is list
        if isinstance(digit, list):
            #create list of zeros
            temp_list = [0]*len(digit)
            #convert values and input into list to return
            for i in range(len(digit)):
                temp_list[i] = digit[i] * 2*V_max/(2**bit_format) - V_max
            result=temp_list
        #same procedure with np.ndarray
        elif isinstance(digit, np.ndarray):
            result=digit * 2*V_max/(2**bit_format) - V_max
        #same procedure with single value
        else:
            result=digit * 2*V_max/(2**bit_format) - V_max
        logging.debug(__name__ + ' : converting digits to V, voltage value: '+ str(result)+'\n')
        return result

    def volt_to_digit(self, volt, gate, bit_format=16):
        """function to convert voltage in digits (input can be single value, python list or np.array)
        If it is given a single voltage value, a list is return with the first entry being the
        digital value and the second being the step number to stay in the lower bit for 
        oversampling. 
        """
        #get voltage range of the gate
        V_max = self.get('gate%d_voltage_range'%gate)
        if abs(volt)>abs(V_max):
            logging.warning(__name__+': voltage bigger than voltage range of output.')
            input("Press Enter to continue.")
            sys.exit() 
        else:
            logging.debug(__name__ + ' : converting V to digits, voltage value: '+ str(volt))
            #check if input is list
            if isinstance(volt, list):
                #create list of zeros
                temp_list = [0]*len(volt)
                #convert values and input into list to return
                for i in range(len(volt)):
                    temp_list[i] = int(round((volt[i] + V_max) / (2*V_max/(2**bit_format))))
                result=temp_list
            #same procedure with np.ndarray
            elif isinstance(volt, np.ndarray):
                result=np.around((volt + V_max) / (2*V_max/(2**bit_format))).astype(int)
            #same procedure with single value. Second value being the step length 
            #to stay in the lower bit while oversampling.
            else:
                result_bits= ((volt + V_max) / (2*V_max/(2**bit_format)))
                #for oversampling:
                #number of steps to stay in lower bit= round(overall_number_steps(1- (bits%1)))
                steps_lower_bit = int(round(self.get_oversampling_divisions()*(1- (result_bits%1))))
                result = [int(round(result_bits)), steps_lower_bit] 
                
            logging.debug(__name__ + ' : converting V to digits, digit value: '+ str(result)+'\n')
            return result
    
    def _do_set_out(self, new, channel):
        """Set output voltage of gate 'X' (ADwin parameter: Data_200[X]). 
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        
        parameters:
        new (FLOAT): new voltage in V 
        channel (INT): gate index 'X'
        """
        if int(self.adw.GetData_Long(188, channel, 1)[0])==1:
            #oversampling is on so the length in which the lower bit ist kept 
            #has to be given to the ADwin
            value, steps_lower_bit = self.volt_to_digit(new, channel)
            self.adw.SetData_Long([steps_lower_bit], 187, channel, 1)
            logging.info(__name__ +': setting number of oversampling steps in lower bit to %d.'%steps_lower_bit)
        else:
            value, _ =self.volt_to_digit(new, channel)
            
        logging.info(__name__ +': setting output voltage gate %d to %f V'%(channel,new))
        self.adw.SetData_Long([value], 200, channel, 1)
        self.set_Par_78_global_long(channel)            
        #activate ADwin to ramp input
        self._activate_ADwin(1)
        #wait for ADwin to finish
        while self.get_Par_76_global_long() != 0:
            time.sleep(1e-5)
                   
        #check if voltage limit was exceeded. 
        if self.adw.GetData_Long(192,channel,1)[0] == 1:
            logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
            input("Press Enter to continue.")
            #set limit error variable back to 0
            self.adw.SetData_Long([0], 192, channel, 1)
            sys.exit() 
        else:
            logging.info(__name__+': voltage set to gate')
            
        
    def _do_get_out(self, channel):
        """Read out constant output voltage of gate 'X' (ADwin parameter: Data_200[X]).
        OVERSAMPLING NOT INCLUDED IN VALUE!
        
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(200, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue, channel)
        logging.info(__name__ +': reading output voltage gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue
    
    
    def set_out_parallel(self, voltage, channel):
        '''Set output voltage of many channels in the array 'channel' to values in the array 'voltage'.
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        
        parameters:
            new (FLOAT): new voltage in V 
            channel (INT): gate index 'X'
        '''
        if len(voltage)==len(channel) and isinstance(voltage, list) and isinstance(channel, list):
            for gate in channel:
                volts = voltage[channel.index(gate)]
                if int(self.adw.GetData_Long(188, gate, 1)[0])==1:
                    #oversampling is on so the length in which the lower bit ist kept 
                    #has to be given to the ADwin
                    value, steps_lower_bit = self.volt_to_digit(volts, gate)
                    self.adw.SetData_Long([steps_lower_bit], 187, gate, 1)
                    logging.info(__name__ +': setting number of oversampling steps in lower bit to %d.'%steps_lower_bit)
                else:
                    value, _ =self.volt_to_digit(volts, gate)
                    
                logging.info(__name__ +': setting output voltage gate %d to %f V'%(gate, volts))
                self.adw.SetData_Long([value], 200, gate, 1)
                #setting to be ramped gates to 1 in Data_185:
                self.adw.SetData_Long([1], 185, gate, 1)
              
            #activate ADwin to ramp input
            self._activate_ADwin(3)
            #wait for ADwin to finish
            while self.get_Par_76_global_long() != 0:
                time.sleep(1e-5)
                       
            #check if voltage limit was exceeded. 
            if self.adw.GetData_Long(192,channel,1)[0] == 1:
                logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
                input("Press Enter to continue.")
                #set limit error variable back to 0
                self.adw.SetData_Long([0], 192, channel, 1)
                sys.exit() 
            else:
                for gate in channel:
                    logging.info(__name__+': voltage set to gate %d.'%gate)
                    
        else:
            logging.warning(__name__+': voltage and channel must be a list of equal length!')
            input("Press Enter to continue.")
            sys.exit() 
    
    
    def _do_set_output_current_voltage_in_V(self, new, channel): #For current sources! NO EXTERNAL USE!
        """Set output voltage of current gate 'X' (1-3) (ADwin parameter: Data_200[X]). 
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        
        parameters:
        new (FLOAT): new voltage in V (possible values: -10 to 10)
        channel (INT): gate index 'X'
        """
        value, _ =self.volt_to_digit(new, channel)
        logging.info(__name__ +': setting output voltage gate %d to %f V'%(channel,new))
        self.adw.SetData_Long([value], 200, channel, 1)
        self.set_Par_78_global_long(channel)            
        #activate ADwin to ramp input
        self._activate_ADwin(1)
        #wait for ADwin to finish
        while self.get_Par_76_global_long() != 0:
            time.sleep(1e-5)
                   
        #check if voltage limit was exceeded. 
        if self.adw.GetData_Long(192,channel,1)[0] == 1:
            logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
            input("Press Enter to continue.")
            #set limit error variable back to 0
            self.adw.SetData_Long([0], 192, channel, 1)
            sys.exit() 
        else:
            logging.info(__name__+': voltage set to gate')
    
    
    def _do_get_output_current_voltage_in_V(self,channel): #For current sources!
        """Read out output voltage of gate 'X' (1-3) (ADwin parameter: Data_200[X]).
        
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(200, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue, channel)
        logging.info(__name__ +': reading output voltage gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue
    

    def _activate_ADwin(self, value):
        """Internal function, (de)activate ADwin processes (ADwin parameter: Par_76).
        
        parameters:
        value (INT): 0 = deactivate,
                     1 = activate ramping outputs, 
                     2 = activate reading inputs  
                     3 = activate ramping outputs in parallel 
        """
        if value==1:
            logging.info(__name__+': write sequence initiated')
            self.set_Par_76_global_long(1)
        elif value==2:
            logging.info(__name__+': reading inputs initiated')
            self.set_Par_76_global_long(2)   
        elif value==3:
            logging.info(__name__+': write outputs in parallel')
            self.set_Par_76_global_long(3) 
        else:
            self.set_Par_76_global_long(0)
            logging.info(__name__+': ADwin stopped')
            
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
            value, _ =self.volt_to_digit(new, channel)
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
        voltvalue=self.digit_to_volt(digitvalue, channel)
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
            value, _ =self.volt_to_digit(new, channel)
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
        voltvalue=self.digit_to_volt(digitvalue, channel)
        logging.info(__name__ +': reading individual upper voltage limit gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue

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


    def initialize_gates(self, number,  lower_limit=0, upper_limit=0, speed=0.2):
        '''This function sets the number of  gates (including current sources)
        and distributes them on the modules starting at module 1 and filling up
        all 8 outputs. Then module 2 etc. is filled up. The modules have to exist.
        Gates 1-3 are reserved for the current sources, meaning voltage gates 
        from 4 to n are initialized.
        
        parameters:
            number: number of voltage gates including current sources.
            lower_limit: initializes voltage gates with given lower limit
            upper_limit: initializes voltage gates with given uppper limit
        '''
        #Since this function is excecuted mostly directly after creating the ADwin instrument, the low priority 
        #initialization of the ADwin should be given time to execute. A sleep of 2s should be sufficient. 
        time.sleep(2)
        
        #initailize gates 
        if number < 0:
            logging.warning(__name__+': number of gates must not be negative!')
            input("Press Enter to continue.")
            sys.exit()
        else:
            #set voltage range for all gates on ADwin
            for gate in range(1,200):
                #change for modified outputs!
                self.set('gate%d_voltage_range'% gate, 10)
                #set oversampling to off
                self.set('gate%d_oversampling_state'% gate, 0)
                
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
                
            #set ramping speed. I don't know why self.set_ramping_speed_normal_ports(speed) does not work...
            self._do_set_ramping_speed_normal_ports(speed)
            
            #set all outputs to 0 Volts
            for gate in range(1, 3+1):  #current sources
                self.set('gate%d_output_current_voltage_in_V'% gate, 0)
            
            for gate in range(4, number+1):  
                self.set('gate%d_out'% gate, 0)
                
            
            
    #The following functions are for the use of current sources that are set with a voltage 
    #by the ADwin
    def set_field_1d(self, direction, amplitude):
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
        translation_factor_x = -2.0 #factor (Ampere/Volts) that is used by the current sources from input to output
        translation_factor_y = -2.0
        translation_factor_z = -2.0
        
        #coil calibration parameters
        x_calib = 0.180 #in Tesla/Amps
        y_calib = 0.056 #in Tesla/Amps
        z_calib = 0.060 #in Tesla/Amps
        
        x_max_current = 8.34 #maximal current in Amps through coil x before quench
        y_max_current = 5.0 #maximal current in Amps through coil y
        z_max_current = 7.0 #maximal current in Amps through coil z
        
        #set  voltage 
        if direction == 1:
            voltage_x = amplitude / x_calib / translation_factor_x
            if abs(voltage_x) <=  10 and abs(voltage_x) <= abs(x_max_current / translation_factor_x):
                self.set_gate1_output_current_voltage_in_V(voltage_x)
            else:
                logging.warning(__name__+': voltage in x-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 2:
            voltage_y = amplitude / y_calib / translation_factor_y
            if abs(voltage_y) <=  10 and abs(voltage_y) <= abs(y_max_current / translation_factor_y):
                self.set_gate2_output_current_voltage_in_V(voltage_y)
            else:
                logging.warning(__name__+': voltage in y-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 3:
            voltage_z = amplitude / z_calib / translation_factor_z
            if abs(voltage_z) <=  10 and abs(voltage_z) <= abs(z_max_current / translation_factor_z):
                self.set_gate3_output_current_voltage_in_V(voltage_z)
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
        translation_factor_x = -2.0 #factor (Ampere/Volts) that is used by the current sources from input to output
        translation_factor_y = -2.0
        translation_factor_z = -2.0
        
        #coil calibration parameters
        x_calib = 0.180 #in Tesla/Amps
        y_calib = 0.056 #in Tesla/Amps
        z_calib = 0.060 #in Tesla/Amps
        
        x_max_current = 8.34 #maximal current in Amps through coil x before quench
        y_max_current = 5.0 #maximal current in Amps through coil y
        z_max_current = 7.0 #maximal current in Amps through coil z
        
        #calculate field components in carthesian coordinates
        amplitude_x = amplitude * np.sin(np.deg2rad(theta+theta_corr)) * np.cos(np.deg2rad(phi+phi_corr))
        amplitude_y = amplitude * np.sin(np.deg2rad(theta+theta_corr)) * np.sin(np.deg2rad(phi+phi_corr))
        amplitude_z = amplitude * np.cos(np.deg2rad(theta+theta_corr))
        
        #setting voltages
        #set x voltage 
        voltage_x = amplitude_x / x_calib / translation_factor_x
        if abs(voltage_x) <=  10 and abs(voltage_x) <= abs(x_max_current / translation_factor_x):
            self.set_gate1_output_current_voltage_in_V(voltage_x) 
        else:
            logging.warning(__name__+': voltage in x-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set y voltage 
        voltage_y = amplitude_y / y_calib / translation_factor_y
        if abs(voltage_y) <=  10 and abs(voltage_y) <= abs(y_max_current / translation_factor_y):
            self.set_gate2_output_current_voltage_in_V(voltage_y)
        else:
            logging.warning(__name__+': voltage in y-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set z voltage 
        voltage_z = amplitude_z / z_calib / translation_factor_z
        if abs(voltage_z) <=  10 and abs(voltage_z) <= abs(z_max_current / translation_factor_z):
            self.set_gate3_output_current_voltage_in_V(voltage_z)
        else:
            logging.warning(__name__+': voltage in z-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
    def IV_curve(self, output=None, input_gate=None, V_min=0.0, V_max=0.001, V_div=1, samples=10, 
                 IV_gain=1e6, I_max=1e-9, averages=1000):
        '''Produces an IV curve. A voltage is applied at the DUT and the resulting current 
        is converted by an IV converter. It's output voltage is measured by the ADwin. 
        
        Returns:
            (Voltage_points, Current_points)
        
        Parameters:
            V_min: minimum voltage applied by ADwin BEFORE voltage divider in Volts
            V_max: maximum voltage applied by ADwin BEFORE voltage divider in Volts
            samples: number of voltage values applied in given interval
            V_div: Voltage divider applied in 1/V_div
            IV_gain: gain of current to voltage converter
            I_max: maximum current after with the I_V curve ends
        '''
        V_step = (V_max - V_min)/samples
        V_values_negative = np.arange(0, V_min - V_step, -V_step)
        V_values_positive = np.arange(0, V_max + V_step, V_step)
        
        data_V = []
        data_I = []
        
        if output != None and input_gate!= None:
            for voltage in V_values_negative:        
                data_V.append(voltage/V_div*1000) #voltage in mV
                self.set('gate%d_out'% output, voltage)
                time.sleep(1e-6)
                current = self.get('ch%d_input_voltage'% input_gate, averages)/IV_gain
                data_I.append(current) 
                if abs(current) > I_max:
                    break
            for voltage in V_values_positive:        
                data_V.append(voltage/V_div*1000) #voltage in mV
                self.set('gate%d_out'% output, voltage)
                time.sleep(1e-6)
                current = self.get('ch%d_input_voltage'% input_gate, averages)/IV_gain
                data_I.append(current) 
                if abs(current) > I_max:
                    break
            self.set('gate%d_out'% output, 0)
        else: 
            print("Input or output not defined!")
            
        return (data_V, data_I)    
        
    
    
    def _do_set_oversampling_state(self, state, channel):
        '''Setting oversamping on gate "channel" on=1 or off=0.
        
        '''
        if state in [0, 1]:
            logging.info(__name__ +': setting oversampling state of gate %d to %d.' %(channel, state))
            self.adw.SetData_Long([state], 188, channel, 1) 
            
        else:
            logging.warning(__name__+': oversampling state must be 0 (=off) or 1 (=on).')
            input("Press Enter to continue.")
            sys.exit() 
    
    
    def _do_get_oversampling_state(self, channel):
        '''Getting oversamping state of gate.
        
        '''
        state = self.adw.GetData_Long(188, channel, 1)[0]
        logging.info(__name__ +': oversampling state of gate %d is %d.' %(channel, state))
        return state
    
    
    def _do_set_oversampling_divisions(self, divisions):
        '''BEWARE IF CHANGED ON THE FLY! This will lead to oversampled channels 
        outputting wrong voltages since the period for switching between bits is 
        changed by the function. To resolve the issue set the output voltages of 
        the oversampled gates again. 
        
        Sets the global number of divisions between two bits.
        '''
        logging.info(__name__ +': setting global number of oversampling divisions to %d.' %divisions)
        self.set_Par_68_global_long(divisions)  

    
    def _do_get_oversampling_divisions(self):
        '''Gets the global number of divisions between two bits.
        '''
        divisions = int(self.get_Par_68_global_long())
        logging.info(__name__ +': number of oversampling divisions is %d.' %divisions)
        return divisions
    
    def _do_set_voltage_range(self, range, channel):
        '''Sets the voltage range of gate "channel".
        '''
        logging.info(__name__ +': setting voltage range of gate %d to %f.' %(channel, range))
        self.adw.SetData_Float([range], 186, channel, 1) 
        
    
    def _do_get_voltage_range(self, channel):
        '''Gets the voltage range of gate "channel".
        '''
        range = self.adw.GetData_Float(186, channel, 1)[0]
        logging.info(__name__ +': voltage range of gate %d is %f.' %(channel,range))
        return range
    
   
if __name__ == "__main__":

    ##device test routine
    ##**************************************************************

    qkit.start()
    #1)create instance - implement global voltage limits when creating instance
    bill = qkit.instruments.create('bill', 'ADwin_Pro2', processnumber=1, processpath='C:/Users/Daniel/SEMICONDUCTOR/code/ADwin/ramp_input.TC1',
                                   devicenumber=1, global_lower_limit_in_V=-1, global_upper_limit_in_V=3, global_lower_limit_in_V_safe_port=-1, 
                                   global_upper_limit_in_V_safe_port=3)

    print(10*'*'+'Initialization complete'+10*'*')
    bill.initialize_gates(8, -1, 1, speed=1)
    bill.set_gate2_out(0.5)
    bill.get_ch1_input_voltage()
    