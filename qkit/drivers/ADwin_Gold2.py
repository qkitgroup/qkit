'''
ADwin ProII driver written by S. Fuhrmann und D. Schroller

TO-DO: 
    set_out_parallel may not log changes -> get_out afterwads helps

IMPORTANT:
This file is using the ADwin process ramp_input_V2.TC1

If ADwin is not booted then it has to be booted manually with ADbasic once. 


Copy driver into qkit/drivers folder.

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
'''


"""
#Define voltage_range_Data Data_186 '[200] voltage range of outputs. 10 means +-10V. This is only a storage for QKit calculations. Not used by ADwin directly
#Define input_gate_Data Data_190 ' [8] analog input gate i' in digit
#Define output_number_Data Data_191 '[200] contains the number allocated to each output, it should look like [0,1,2,3,4,5,6,7,8,0,0,0,0,...] the first 0 doesn(t correspond to an output
#Define limit_error_Data Data_192 '[200] for each output, it contains a bit: 1==> voltage limit exceeded or limits not set, 0==> all is fine
#Define lower_limit_Data Data_194 '[200] for each output, it contains the lower voltage limit
#Define upper_limit_Data Data_195 '[200] for each output, it contains the upper voltage limit
#Define safe_bit_Data Data_199  '[200]   for each output, 1==> safe port (maximum ramping speed is defined), 0==> default
#Define ramp_stop_Data Data_200  '[200]  for each output, target voltage of a ramp

#Define averages_Par Par_69 'number of time each inputs are averaged (typically: 100-1000)
#Define input_mask_Par Par_72 'NEW bit mask defining which inputs are used (most of the time it is only one input)
#Define gate_number_Par Par_75 'number of ouputs used, default=200 
#Define run_Par Par_76 'variable defining which process is running, ie: setting output OR getting inputs
#Define ramping_speed_FPar FPar_77 'output ramping speed in V/s (only for non safe port)
#Define channel_Par Par_78 'number of the ramped output
"""

'''
TODO: create the functions _do_get_LI_imag, and _do_get_LI_real, check how it is done for _do_get_INvoltage and _do_set_OUTvoltage
TODO: create the short versions functions get_LI_imag, and get_LI_real (or even get_lock_in, see with Julian about a set_get_funct with two outputs...)
TODO: move check with correct voltage_range from the function "digit_to_volt" and "volt_to_digit" to the function "_do_set_OUTvoltage"
'''

import ADwin as adw
import qkit
from qkit.core.instrument_base import Instrument
import logging
import time
import numpy as np
import sys


class ADwin_Gold2_v3_withLI(Instrument):
    """
           DOCUMENTATION

           __init__: 

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
                 set_gate5_out(1)
                 set_out(5, 1)     shorthand of previous function
                 set_out_parallel([gates], [voltages])
                 initialize_gates(number, lower_limit, upper_limit, speed)
                 get_ch1_input_voltage(averages=1000)
                 get_input(1)      shorthand of previous function
                 set_gate5_oversampling_state(1)
                 set_oversampling_division(10)
                 set_gate5_voltage_range(2)
                 set_field_1d(direction, amplitude)
                 set_field_3d(amplitude, theta, phi)
                 

    """
        
    def __init__(self, name, processnumber, processpath, devicenumber, global_lower_limit_in_V=0, 
                 global_upper_limit_in_V=0, global_lower_limit_in_V_safe_port=0, global_upper_limit_in_V_safe_port=0):
        logging.info(__name__ + ' : Initializing instrument')
        Instrument.__init__(self, name, tags=['physical','ADwin_GoldII'])
        
        #create ADwin instance 
        self.name = name
        self.processnumber=processnumber
        self.processpath = processpath
        self.adw = adw.ADwin(devicenumber,1)
        self.global_upper_limit_in_V = global_upper_limit_in_V
        self.global_lower_limit_in_V = global_lower_limit_in_V
        self.global_upper_limit_in_V_safe_port = global_upper_limit_in_V_safe_port
        self.global_lower_limit_in_V_safe_port = global_lower_limit_in_V_safe_port
        
        if self.global_upper_limit_in_V<self.global_lower_limit_in_V or self.global_upper_limit_in_V_safe_port<self.global_lower_limit_in_V_safe_port:
            logging.error(__name__+': lower voltage limit higher than upper limit')
            sys.exit()
        
        #VERY IMPORTANT TO INCLUCE! stopping the running ADwin process before and give it time to go to the Finish part to ramp down voltages
        self.stop_process()
           
        #bootload
        self.bootload_process()
        
        #load and start process
        self.processnumber=processnumber
        self.load_process()
        time.sleep(1.0)
        self.start_process()
        
        
        #implement functions
        self.add_function('start_process')
        self.add_function('stop_process')
        self.add_function('load_process')
        self.add_function("digit_to_volt")
        self.add_function("volt_to_digit")
        self.add_function('individual_voltage_limits_setter_in_V')    
        self.add_function('set_output_voltage')
        self.add_function('get_output_voltage')
        self.add_function('set_out_parallel')
        self.add_function('set_out_dict')
        self.add_function('oversampled_gates')
        self.add_function('get_input')
        self.add_function('set_field_1d')
        self.add_function('set_field_3d')
        self.add_function('initialize_outputs')
        self.add_function('IV_curve')
        
        
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
            channels=(1,8), channel_prefix='output%d_',
            minval=0, maxval=1)
        
        #output voltage set via Data_200 array
        self.add_parameter('OUTvoltage', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(4,8), channel_prefix='output%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        
        #output voltage set via Data_200 array
        #outputs 1, 2, 3 are used for current sources
        self.add_parameter('output_current_voltage_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,3), channel_prefix='output%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        """
        #number of gates used set via Par_75
        self.add_parameter('number_of_gates', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=200,
            tags=['sweep'])
        """

        #lower individual voltage limits set via Data_194 array
        self.add_parameter('individual_lower_voltage_limit_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,8), channel_prefix='output%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        #upper individual voltage limits set via Data_195 array
        self.add_parameter('individual_upper_voltage_limit_in_V', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,8), channel_prefix='output%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        """
        #module number set via Data_193 array
        self.add_parameter('module_number', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,200), channel_prefix='gate%d_',
            minval=1, maxval=20,
            tags=['sweep'])
        """
        """
        #output number set via Data_191 array
        self.add_parameter('output_number', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,8), channel_prefix='output%d_',
            minval=1, maxval=8,
            tags=['sweep'])
        """

        #analog input read out via Data_190 array
        self.add_parameter('INvoltage', type=float,
            flags=Instrument.FLAG_GET,
            channels=(1,8), channel_prefix='input%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])

        # #analog input read out via Data_198 array
        # self.add_parameter('LI_real', type=float,
        #     flags=Instrument.FLAG_GET,
        #     channels=(1,8), channel_prefix='input%d_',
        #     minval=-10, maxval=10, units='S',
        #     tags=['sweep'])

        # #analog input read out via Data_197 array
        # self.add_parameter('LI_imag', type=float,
        #     flags=Instrument.FLAG_GET,
        #     channels=(1,8), channel_prefix='input%d_',
        #     minval=-10, maxval=10, units='S',
        #     tags=['sweep'])
        
        #ramping speed normal ports in V/s
        self.add_parameter('ramping_speed_normal_ports', type=float,
            flags=Instrument.FLAG_GETSET,
            minval=0.0, maxval=100.0)
        
        #state of gate X if it uses oversampling =1 or not =0
        self.add_parameter('oversampling_state', type=int,
            flags=Instrument.FLAG_GETSET,
            channels=(1,8), channel_prefix='output%d_',
            minval=0, maxval=1,
            tags=['sweep'])
        
        #global amount of oversampling divisions between two bits
        self.add_parameter('oversampling_divisions', type=int,
            flags=Instrument.FLAG_GETSET,
            minval=1, maxval=1000,
            tags=['sweep'])
        

        #voltage ranges of outputs, a value of 10 means +-10V
        #set via data_186
        self.add_parameter('voltage_range', type=float,
            flags=Instrument.FLAG_GETSET,
            channels=(1,8), channel_prefix='output%d_',
            minval=-10, maxval=10, units='V',
            tags=['sweep'])
        

        
    def bootload_process(self):
        '''bootloads the process given in the processpath.
        '''
        btl_dir = self.adw.ADwindir + "\\ADwin11.btl"
        self.adw.Boot(btl_dir) 

    def start_process(self):
        """start process (done automatically when creating ADwin_ProII instance)
        """
        self.stop_process()
        logging.info(__name__ +': starting process')
        self.adw.Start_Process(self.processnumber)
        logging.debug(__name__+'process status: %d'%self.adw.Process_Status(self.processnumber))

    def stop_process(self):
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        logging.info(__name__ +': stopping process')
        self.adw.Stop_Process(self.processnumber)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        print("Ramping down all outputs (gates + current sources) to 0 Volts if possible...\nGreen LED at DAC module indicates ongoing ramping action.")
        while True:
            try:   #if all outputs were at 0V then the process is already dead
                if self.adw.Get_Par(76)==-1:
                    time.sleep(0.1)
                else:
                    print("All outputs are ramped down to 0 Volts. No exception.")
                    break
            except:
                #The FINISH part in the ADwin has finished ramping down all outputs and the process is dead
                print("All outputs are ramped down to 0 Volts.")
                break

    def load_process(self):
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))
        logging.info(__name__ +': loading process')
        self.adw.Load_Process(self.processpath)
        logging.debug(__name__+': process status: %d'%self.adw.Process_Status(self.processnumber))  
        
    def workload(self):
        '''Gets the workload of ADwin in percent.
        '''
        return self.adw.Workload()
    
    # def _do_get_data_length(self,data_array_number):
    #     """Data_Length, see ADwin Driver Python documentation
    #     """
    #     logging.info(__name__ +': reading length of data array Data_%d'%data_array_number)
    #     return self.adw.Data_Length(data_array_number)
    
    def _do_set_global_float(self,new,channel):
        logging.info(__name__ +': setting Global FLOAT variable FPar_%d to value: %d'%(channel,new))
        self.adw.Set_FPar(channel,new)

    def _do_get_global_float(self,channel):
        logging.info(__name__ +': reading Global FLOAT variable FPar_%d'%channel)
        return self.adw.Get_FPar(channel)
    
    # def _do_get_global_float_par_block(self, startindex, count):
    #     """Get_FPar_Block, see ADwin Driver Python documentation
    #     """
    #     logging.debug(__name__ +': reading Global FLOAT variable block: startindex %d, count %d'%(startindex,count))
    #     return self.adw.Get_FPar_Block(startindex, count)
    
    
    # def _do_get_global_float_par_all(self):
    #     """Get_FPar_All, see ADwin Driver Python documentation
    #     """
    #     logging.debug(__name__ +': reading all Global FLOAT variables')
    #     return self.adw.Get_FPar_All()
    
    def _do_set_global_long(self,new,channel):
        logging.info(__name__ +': setting Global LONG variable Par_%d to value: %d'%(channel,new))
        self.adw.Set_Par(channel,new)

    def _do_get_global_long(self,channel):
        logging.info(__name__ +': reading Global LONG variable Par_%d'%channel)
        return self.adw.Get_Par(channel)
    
    # def _do_get_global_long_par_block(self, startindex, count):
    #     """Get_Par_Block, see ADwin Driver Python documentation
    #     """
    #     logging.debug(__name__ +': reading Global LONG variable block: startindex %d, count %d'%(startindex,count))
    #     return self.adw.Get_Par_Block(startindex, count)

    # def _do_get_global_long_par_all(self):
    #     """Get_Par_All, see ADwin Driver Python documentation
    #     """
    #     logging.debug(__name__ +': reading all Global LONG variables')
    #     return self.adw.Get_Par_All()


    def get_Lock_In(self, input_port, output_port, frequency, amplitude, period_average, gain, divider):
        
        #TODO: Add safety checks over the type of inputs, ie: INT has to be INT
        """
        apply an AC-modulation on the output port, and demodulation + low-pass filterig on the read input port

        Parameters:
        
        input_port (INT): input port on which the read-out (demodulation + filtering) is performed. (values ranging from 1 to 8, up to now)

        output_port (INT): output port the AC-modulation is applied to. (values ranging from 1 to 8)

        frequency (FLOAT): frequency at which the lock-in measurement is performed (modulation + demodulation). (typical values between 100Hz to 500Hz)

        amplitude (FLOAT): positive value in voltage of the voltage modulation (half of peak-to-peak) at the level of the device (typical values are 10µV to 50µV)
        
        period_average (INT): number of period over which the average is performed, typically between 2 and 10 periods, where a period is defined by the LI_frequency

        gain (INT): Gain of the transimpedance voltage amplifier

        divider (INT): value of the voltage divider. In case of a divider x1/100, it is equal to 100.

        result = [LI_real, LI_imag, LI_amplitude, LI_phase]
        """

        #set input port number
        self.set_Par_21_global_long(input_port)

        #set output port number
        self.set_Par_22_global_long(output_port)

        #set lock-in parameters
        self.set_FPar_20_global_float(frequency)

        amplitude_digit, _ =self.volt_to_digit(amplitude*divider) # multiplication by divider has to be done before volt to digit conversion

        self.set_Par_20_global_long(amplitude_digit)

        self.set_FPar_23_global_float(period_average)

        self.set_Par_24_global_long(gain)

        self.set_Par_25_global_long(divider)

        input_bitmask = 2**(input_port-1)
        self.set_Par_72_global_long(input_bitmask)

        if type(period_average) is not int:
            logging.warning(__name__+': the number of period average has to be an integer.')
            input("Press Enter to continue.")
            sys.exit() 

        dc_output_value = self.get('output%d_OUTvoltage'% output_port)
        if abs(dc_output_value) + divider*amplitude > 10:
            logging.warning(__name__+': DC + AC modulation exceed the 10 volts range of the output.')
            input("Press Enter to continue.")
            sys.exit() 
        else:
            self._activate_ADwin(3)
            #wait for ADwin to finish:
            while self.get_Par_76_global_long() != 0:
                pass      

            result = np.zeros(4)  
            digitvalue_real=self.adw.GetData_Long(198, input_port, 1)[0]
            print(digitvalue_real)
            voltvalue_real=self.digit_to_volt(digitvalue_real, bit_format=16)
            result[0] = voltvalue_real/gain # this normalisation has to be done after digit to volt conversion, otherwise it might result in digit_value < 0 which produce volt_value = 0

            digitvalue_imag=self.adw.GetData_Long(197, input_port, 1)[0]
            voltvalue_imag=self.digit_to_volt(digitvalue_imag, bit_format=16)
            result[1] = voltvalue_imag/gain # this normalisation has to be done after digit to volt conversion, otherwise it might result in digit_value < 0 which produce volt_value = 0

            result[2] = np.sqrt(result[1]**2 + result[0]**2) # contains amplitude of lock-in signal
            result[3] = -np.arctan(result[1]/result[0]) # contains phase of lock-in signal

            logging.info(__name__ +': reading lock-in real part on input %d : %f S , %d digits'%(input_port, result[0], digitvalue_real))
            logging.info(__name__ +': reading lock-in imag part on input %d : %f S , %d digits'%(input_port, result[1], digitvalue_imag))
            
            return result


    def get_DCcurrent_LIreal_LIimag(self, input_port, output_port, frequency, amplitude, period_average, gain, divider):
        
        """
        apply an AC-modulation on the output port, and demodulation + low-pass filterig on the read input port
        Parameters:
        
        input_port (INT): input port on which the read-out (demodulation + filtering) is performed. (values ranging from 1 to 8, up to now)

        output_port (INT): output port the AC-modulation is applied to. (values ranging from 1 to 8)

        frequency (FLOAT): frequency at which the lock-in measurement is performed (modulation + demodulation). (typical values between 100Hz to 500Hz)

        amplitude (FLOAT): positive value in voltage of the voltage modulation (half of peak-to-peak) at the level of the device (typical values are 10µV to 50µV)
        
        period_average (INT): number of period over which the average is performed, typically between 2 and 10 periods, where a period is defined by the LI_frequency

        gain (INT): Gain of the transimpedance voltage amplifier

        divider (INT): value of the voltage divider. In case of a divider x1/100, it is equal to 100.

        result = [current_DC, LI_real, LI_imag, LI_amplitude, LI_phase]
        """

        #set input port number
        self.set_Par_21_global_long(input_port)

        #set output port number
        self.set_Par_22_global_long(output_port)

        #set lock-in parameters
        self.set_FPar_20_global_float(frequency)

        amplitude_digit, _ =self.volt_to_digit(amplitude*divider) # multiplication by divider has to be done before volt to digit conversion

        self.set_Par_20_global_long(amplitude_digit)

        self.set_FPar_23_global_float(period_average)
        #self.set_Par_23_global_long(period_average)

        self.set_Par_24_global_long(gain)

        self.set_Par_25_global_long(divider)
        
        input_bitmask = 2**(input_port-1)
        self.set_Par_72_global_long(input_bitmask)

        if type(period_average) is not int:
            logging.warning(__name__+': the number of period average has to be an integer.')
            input("Press Enter to continue.")
            sys.exit()

        dc_output_value = self.get('output%d_OUTvoltage'% output_port)

        if abs(dc_output_value) + divider*amplitude > 10:
            logging.warning(__name__+': DC + AC modulation exceed the 10 volts range of the output.')
            input("Press Enter to continue.")
            sys.exit() 
        else:
            self._activate_ADwin(4)
            #wait for ADwin to finish:
            while self.get_Par_76_global_long() != 0:
                # time.sleep(0.4)
                pass     
            result = np.zeros(5) 
            digitvalue_dc=self.adw.GetData_Long(190, input_port, 1)[0]
            voltvalue_dc=self.digit_to_volt(digitvalue_dc, bit_format=16)
            result[0] = voltvalue_dc/gain # this normalisation has to be done after digit to volt conversion, otherwise it might result in digit_value < 0 which produce volt_value = 0

            digitvalue_real=self.adw.GetData_Long(198, input_port, 1)[0]
            voltvalue_real=self.digit_to_volt(digitvalue_real, bit_format=16)
            result[1] = voltvalue_real/gain # this normalisation has to be done after digit to volt conversion, otherwise it might result in digit_value < 0 which produce volt_value = 0

            digitvalue_imag=self.adw.GetData_Long(197, input_port, 1)[0]
            voltvalue_imag=self.digit_to_volt(digitvalue_imag, bit_format=16)
            result[2] = voltvalue_imag/gain # this normalisation has to be done after digit to volt conversion, otherwise it might result in digit_value < 0 which produce volt_value = 0

            result[3] = np.sqrt(result[1]**2 + result[0]**2) # contains amplitude of lock-in signal
            result[4] = -np.arctan(result[1]/result[0]) # contains phase of lock-in signal

            logging.info(__name__ +': reading DC current on input %d : %f A , %d digits'%(input_port, result[0], digitvalue_dc))
            logging.info(__name__ +': reading lock-in real part on input %d : %f S , %d digits'%(input_port, result[1], digitvalue_real))
            logging.info(__name__ +': reading lock-in imag part on input %d : %f S , %d digits'%(input_port, result[2], digitvalue_imag))

            return result

    

    def _do_get_INvoltage(self, channel, averages=1000):
        """Read out voltage of analog input 'X' (ADwin parameter: Data_190[X]).
        wrapped as self.get_ch1_input_voltage()
        18bit resulution, bit format is 16bit 
        
        averages: 0 means no averaging so only one data point 
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        input_bitmask = 2**(channel-1)
        self.set_Par_72_global_long(input_bitmask)

        if averages >= 0 and averages<=10000: 
            #set number of averages
            self.set_Par_69_global_long(averages)
            #activate input readout
            self._activate_ADwin(2)
            #wait for ADwin to finish:
            while self.get_Par_76_global_long() != 0:
                pass         
            digitvalue=self.adw.GetData_Long(190, channel, 1)[0]
            voltvalue=self.digit_to_volt(digitvalue, bit_format=16)
            logging.info(__name__ +': reading voltage analog input %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
            return voltvalue
        else:
            logging.warning(__name__+': number of averages must bigger than 0 and smaller than 10 000!.')
            input("Press Enter to continue.")
            sys.exit() 
    
    def get_input(self, channel, averaging):
        '''Short version of get_gateX_input_voltage().
        get_input(channel, averaging)
        '''
        return self.get("input%d_INvoltage"%channel, averages=averaging)
    
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
        '''sets the ramping speed in Volts/seconds for normal ports. 
        For non-safeports, the rampiing speed is adjusted with the voltage range in the ADwin process. 
        So a set voltage range of +-1V (with 1/10 external voltage divider) will increase the ramping on that 
        gate by a factor of 10 to reach the desired speed. 
        '''
        logging.info(__name__ +': setting ramping speed for normal ports of process Nr.%s to %f s' % (self.processnumber, speed))
        self.set_FPar_77_global_float(speed)
        
    def _do_get_ramping_speed_normal_ports(self):
        '''gets the ramping speed in Volts/seconds for normal ports
        '''
        return self.get_FPar_77_global_float()
          
    def digit_to_volt(self, digit, bit_format=16):
        """function to convert digits in voltage (input can be single value, python list of np.array)
        """
        #get voltage range of the gate
        #V_max = self.get('output%d_voltage_range'%output)
        V_max = 10
        logging.debug(__name__ + ' : converting digits to V, digit value: '+ str(digit))
        result= (digit * 2*10/(2**bit_format) - 10)*(V_max/10)
        logging.debug(__name__ + ' : converting digits to V, voltage value: '+ str(result)+'\n')
        return result


    def volt_to_digit(self, volt, bit_format=16):
        """function to convert voltage in digits. A list is returnd with the first entry being the
        digital value and the second being the step number to stay in the lower bit for 
        oversampling. 
        """
        # V_max = self.get('output%d_voltage_range'%output)
        V_max = 10
        """
        if abs(volt)>abs(V_max):
            logging.warning(__name__+': voltage bigger than voltage range of output.')
            input("Press Enter to continue.")
            sys.exit() 
        else:
        """
        result_bits= ((volt*(10/V_max) + 10) / (2*10/(2**bit_format)))
        #for oversampling:
        #number of steps to stay in lower bit= round(overall_number_steps(1- (bits%1)))
        steps_lower_bit = int(round(self.get_oversampling_divisions()*(1- (result_bits%1))))
        result = [int(np.trunc(result_bits)), steps_lower_bit] 
        if steps_lower_bit==0:
            result[0] = result[0] + 1
            result[1] = 10
        #print(result)
        logging.debug(__name__ + ' : converting V to digits, digit value: '+ str(result)+'\n')
        return result
    
    def _do_set_OUTvoltage(self, new, channel):
        """Set voltage of output 'X' (ADwin parameter: Data_200[X]). 
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        
        parameters:
        new (FLOAT): new voltage in V 
        channel (INT): output index 'X'
        """
        if self.get('output%d_oversampling_state'%channel)==1:
            #oversampling is on so the length in which the lower bit ist kept 
            #has to be given to the ADwin
            value, steps_lower_bit = self.volt_to_digit(new)
            self.adw.SetData_Long([steps_lower_bit], 187, channel, 1)
            logging.info(__name__ +': setting number of oversampling steps in lower bit to %d.'%steps_lower_bit)
        else:
            value, _ =self.volt_to_digit(new)
            logging.info(__name__ +': oversampling not used on output %d.'%channel)
            
        logging.info(__name__ +': setting output %d to %f V'%(channel,new))
        self.adw.SetData_Long([value], 200, channel, 1)
        self.set_Par_78_global_long(channel)            
        #activate ADwin to ramp input
        self._activate_ADwin(1)
        #wait for ADwin to finish
        while self.get_Par_76_global_long() != 0:
            pass
            
            
                   
        #check if voltage limit was exceeded. 
        if self.adw.GetData_Long(192,channel,1)[0] == 1:
            logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set, output voltage will remain unchanged.')
            input("Press Enter to continue.")
            #set limit error variable back to 0
            self.adw.SetData_Long([0], 192, channel, 1)
            sys.exit() 
        else:
            logging.info(__name__+': voltage set to output')
            
        
    def _do_get_OUTvoltage(self, channel):
        """Read out constant voltage of output 'X' (ADwin parameter: Data_200[X]).
        OVERSAMPLING NOT INCLUDED IN VALUE!
        
        return value (FLOAT): voltage in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(200, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading voltage of output %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue
    
    def set_output_voltage(self, output, voltage):
        '''Allows easier access to set function for many gates.
        '''
        self.set('output%d_OUTvoltage'% output, voltage)

        
    def get_output_voltage(self, output):
        '''Allows easier access to get function for many gates.
        '''
        return self.get('output%d_OUTvoltage'% output)


    def set_out_parallel(self, channels, voltages):
        '''set_out_parallel(channels, voltages)
        Set output voltage of many channels in the array 'channel' to values in the array 'voltage'.
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        The gates which are set in parallel are given to the Data_185 array. Voltage limit errors
        are reported in Data_192[i] of each channel.
        
        parameters:
            channels (list(INT)): gates to be set
            voltages (list(FLOAT)): new voltages in V 
        '''
        #The maximum number of gates which can be set in parallel as defined by the for-loop in the ADbasic file:
        max_num_channels = 10
        #the gates which are reseved for the current sources cannot be accessed with set_out_parallel
        field_gates = [1, 2, 3]
        
        if len(voltages)==len(channels) and isinstance(voltages, list) and isinstance(channels, list) and len(voltages)<=max_num_channels:
            #setting to be ramped gates as an array to Data_185. Initialized as zeros:
            channel_list = [0]*max_num_channels
            for gate in channels:
                if (gate in field_gates):
                    logging.warning(__name__+': voltage at outputs for current sources cannot be changed with this funcion. ')
                    input("Press Enter to continue.")
                    sys.exit() 
                elif channels.count(gate)>1:
                    logging.warning(__name__+': same gate used multiple times. ')
                    input("Press Enter to continue.")
                    sys.exit()
                else:
                    index_channels = channels.index(gate)
                    channel_list[index_channels] = gate
                    volts = voltages[index_channels]
                    
                    if self.get('output%d_oversampling_state'%gate)==1:
                        #oversampling is on so the length in which the lower bit ist kept 
                        #has to be given to the ADwin
                        value, steps_lower_bit = self.volt_to_digit(volts)
                        self.adw.SetData_Long([steps_lower_bit], 187, gate, 1)
                        logging.info(__name__ +': setting number of oversampling steps in lower bit to %d for gate %d.'%(steps_lower_bit, gate))
                    else:
                        value, _ =self.volt_to_digit(volts)
                        logging.info(__name__ +': not oversampling gate %d.'%gate)
                        
                    logging.info(__name__ +': setting output voltage gate %d to %f V'%(gate, volts))
                    self.adw.SetData_Long([value], 200, gate, 1)
              
           
            #setting array of ramped channels to Data_185
            self.adw.SetData_Long(channel_list, 185, 1, max_num_channels)
            
            #setting number of to be ramped gates to Par_70
            self.set_Par_70_global_long(len(channels)) 
            
            #activate ADwin to ramp input
            self._activate_ADwin(3)
            #wait for ADwin to finish
            while self.get_Par_76_global_long() != 0:
                pass
                       
            #check if voltage was out of bounds:
            limit_error_Data = list(self.adw.GetData_Long(192,1,self.get_number_of_gates()))
            #print("limit error Data: ", str(limit_error_Data))
            if 1 in limit_error_Data:
                logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set on channels. ')
                input("Press Enter to continue.")
                #set limit error variable back to 0
                self.adw.SetData_Long([0], 192, 1, 200)
                sys.exit() 
            else:
                for gate in channels:
                    logging.info(__name__+': voltage set to gate %d.'%gate)
                    
        else:
            logging.warning(__name__+': voltage and channel must be a list of equal length!')
            input("Press Enter to continue.")
            sys.exit() 
 
    def set_out_dict(self, values_dict):
        '''set_out_dict({gatenumber: voltage,...})
        Set output voltage of many channels of the dictionary.
        Safe ports will respect the maximum ramping speed of 0.5V/s which is checked 
        in the ADwin file. 
        The gates which are set in parallel are given to the Data_185 array. Voltage limit errors
        are reported in Data_192[i] of each channel.
        
        parameters:
            values_dict = {gatenumber: voltage in V,...}
        '''
        #The maximum number of gates which can be set in parallel as defined by the for-loop in the ADbasic file:
        max_num_channels = 10
        #the gates which are reseved for the current sources cannot be accessed with set_out_parallel
        field_gates = [1, 2, 3]
        
        #check if there are empty values 
        if (not bool(len(["" for x in values_dict.values() if not x]))) and len(values_dict)<=max_num_channels:
            #Transformation of dictionary in two arrays:
            channels = list(values_dict.keys())
            voltages = list(values_dict.values())
            
            #setting to be ramped gates as an array to Data_185. Initialized as zeros:
            channel_list = [0]*max_num_channels
            for gate in channels:
                if (gate in field_gates):
                    logging.warning(__name__+': voltage at outputs for current sources cannot be changed with this funcion. ')
                    input("Press Enter to continue.")
                    sys.exit() 
                elif channels.count(gate)>1:
                    logging.warning(__name__+': same gate used multiple times. ')
                    input("Press Enter to continue.")
                    sys.exit()
                else:
                    index_channels = channels.index(gate)
                    channel_list[index_channels] = gate
                    volts = voltages[index_channels]
                    
                    if self.get('gate%d_oversampling_state'%gate)==1:
                        #oversampling is on so the length in which the lower bit ist kept 
                        #has to be given to the ADwin
                        value, steps_lower_bit = self.volt_to_digit(volts)
                        self.adw.SetData_Long([steps_lower_bit], 187, gate, 1)
                        logging.info(__name__ +': setting number of oversampling steps in lower bit to %d for gate %d.'%(steps_lower_bit, gate))
                    else:
                        value, _ =self.volt_to_digit(volts)
                        logging.info(__name__ +': not oversampling gate %d.'%gate)
                        
                    logging.info(__name__ +': setting output voltage gate %d to %f V'%(gate, volts))
                    self.adw.SetData_Long([value], 200, gate, 1)
              
           
            #setting array of ramped channels to Data_185
            self.adw.SetData_Long(channel_list, 185, 1, max_num_channels)
            
            #setting number of to be ramped gates to Par_70
            self.set_Par_70_global_long(len(channels)) 
            
            #activate ADwin to ramp input
            self._activate_ADwin(3)
            #wait for ADwin to finish
            while self.get_Par_76_global_long() != 0:
                pass
                       
            #check if voltage was out of bounds:
            limit_error_Data = list(self.adw.GetData_Long(192,1,8))
            #print("limit error Data: ", str(limit_error_Data))
            if 1 in limit_error_Data:
                logging.warning(__name__+': voltage limit exceeded or individual voltage limit not set on channels. ')
                input("Press Enter to continue.")
                #set limit error variable back to 0
                self.adw.SetData_Long([0], 192, 1, 200)
                sys.exit() 
            else:
                for gate in channels:
                    logging.info(__name__+': voltage set to gate %d.'%gate)
                    
        else:
            logging.warning(__name__+': dictionary not processable!')
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
        value, _ =self.volt_to_digit(new)
        logging.info(__name__ +': setting output voltage gate %d to %f V'%(channel,new))
        self.adw.SetData_Long([value], 200, channel, 1)
        self.set_Par_78_global_long(channel)            
        #activate ADwin to ramp input
        self._activate_ADwin(1)
        #wait for ADwin to finish
        while self.get_Par_76_global_long() != 0:
            pass
                   
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
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading output voltage gate %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue
    

    def _activate_ADwin(self, value):
        """Internal function, (de)activate ADwin processes (ADwin parameter: Par_76).
        
        parameters:
        value (INT): 0 = deactivate,
                     1 = activate ramping outputs, 
                     2 = activate reading inputs  
                     3 = activate lock-in measurement
                     4 = activate lock-in measurement + reading inputs
        """
        if value==1:
            logging.info(__name__+': ramping sequence initiated')
            self.set_Par_76_global_long(1)
        elif value==2:
            logging.info(__name__+': reading inputs initiated')
            self.set_Par_76_global_long(2)   
        elif value==3:
            logging.info(__name__+': Lock-in measurement')
            self.set_Par_76_global_long(3) 
        elif value==4:
            logging.info(__name__+': Lock-in measurement and DC read-out')
            self.set_Par_76_global_long(4)
        else:
            self.set_Par_76_global_long(0)
            logging.info(__name__+': ADwin stopped')
         
    # def _do_set_output_number(self,value,channel):
    #     """Allocate ADwin output number to gate 'X' (ADwin parameter: Data_191[X]).
        
    #     parameters: 
    #     value (INT): output number (possible values: 1 to 200) (INT): gate index
    #     """
    #     logging.info(__name__ + ': setting output number of gate %d to %d'%(channel,value))
    #     self.adw.SetData_Long([value], 191, channel, 1)

    # def _do_get_output_number(self,channel):
    #     """Read out ADwin output number of gate 'X' (ADwin parameter: Data_191[X]).
        
    #     parameters: 
    #     X (INT): gate index 
    #     return value (INT): output number (possible values: 1 to 200)
    #     """
    #     output=self.adw.GetData_Long(191, channel, 1)[0]
    #     logging.info(__name__ + ': reading output number of gate %d : %d' %(channel,output))
    #     return output
    
    # def _do_set_module_number(self,value,channel):
    #     """Allocate ADwin module number to gate 'X' (ADwin parameter: Data_193[X]).
        
    #     parameters: 
    #     value (INT): module number (possible values: 1 to 20)
    #     X (INT): gate index
    #     """
    #     logging.info(__name__ + ': setting module number of gate %d to %d'%(channel,value))
    #     self.adw.SetData_Long([value], 193, channel, 1)

    # def _do_get_module_number(self,channel):
    #     """Read out ADwin module number of gate 'X' (ADwin parameter: Data_193[X]).
        
    #     parameters: 
    #     X (INT): gate index 
    #     return value (INT): module number (possible values: 1 to 20)
    #     """
    #     output=self.adw.GetData_Long(193, channel, 1)[0]
    #     logging.info(__name__ + ': reading module number of gate %d : %d' %(channel,output))
    #     return output

    def individual_voltage_limits_setter_in_V(self, value1, value2, output):
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
        exec("self.set_output%d_individual_lower_voltage_limit_in_V(lowerlimit)"% output)
        exec("self.set_output%d_individual_upper_voltage_limit_in_V(upperlimit)"% output)
        logging.info(__name__ +': individual voltage limits output %d: %d , %d'%(output,lowerlimit,upperlimit))

    def _do_set_individual_lower_voltage_limit_in_V(self, new, channel):
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
            value, _ =self.volt_to_digit(new)
            self.adw.SetData_Long([value], 194, channel, 1)
            logging.info(__name__ +': setting individual lower voltage limit output %d to  %f V'%(channel,new))
        else:
            logging.error(__name__+': given lower voltage limit not in global limits')
            sys.exit()

    def _do_get_individual_lower_voltage_limit_in_V(self, channel):
        """Read out individual lower voltage limit of output 'X' in V (ADwin parameter: Data_194[X]).
        
        parameters:
        X (INT): output index 
        return value (FLOAT): Individual lower voltage limit in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(194, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading individual lower voltage limit output %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue

    def _do_set_individual_upper_voltage_limit_in_V(self, new, channel):
        """Set individual upper voltage limit in V for output 'X' (ADwin parameter: Data_195[X]). 
        The value set has to be within the boundaries given by global_lower(upper)_limit_in_V_(safe_port).
        
        parameters:
        new (FLOAT): individual upper voltage limit in V (possible values: -10 to 10)
        X (INT): output index
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
            value, _ =self.volt_to_digit(new)
            logging.info(__name__ +': setting individual upper limit output %d to  %f V'%(channel,new))
            self.adw.SetData_Long([value], 195, channel, 1)
        else:
            logging.error(__name__+': given upper limit not in global limits')
            sys.exit()
    
    def _do_get_individual_upper_voltage_limit_in_V(self, channel):
        """Read out individual upper voltage limit of output 'X' in V (ADwin parameter: Data_195[X]).
        
        parameters:
        X (INT): output index 
        return value (FLOAT): Individual upper voltage limit in V (possible values: -10 to 10)
        """
        digitvalue=self.adw.GetData_Long(195, channel, 1)[0]
        voltvalue=self.digit_to_volt(digitvalue)
        logging.info(__name__ +': reading individual upper voltage limit output %d : %f V , %d digits'%(channel,voltvalue, digitvalue))
        return voltvalue

    
    # def _do_set_number_of_gates(self,value):
    #     """Set number of gates used in setup (ADwin parameter: Par_75).
    #     Initial number is 200.
        
    #     parameters:
    #     value (INT): number of gates (possible values: 1 to 200)
    #     """
    #     logging.info(__name__ + ': setting number of gates to %d'%(value))
    #     self.set_Par_75_global_long(value)
    
    
    # def _do_get_number_of_gates(self):
    #     """Read out number of gates used in setup (ADwin parameter: Par_75).
        
    #     return value (INT): number of gates (possible values: 1 to 200)
    #     """
    #     output=self.get_Par_75_global_long()
    #     logging.info(__name__ + ': reading number of gates: %d ' % output)
    #     return output
    

    def _do_set_safe_port(self,new,channel):
        """Set gate 'X' as safe port (ADwin parameter: Data_199[X]).
        
        parameters: 
        new (INT): 1=safe port, 0=no safe port (possible values: 1, 0)
        X (INT): gate index
        """
        logging.info(__name__ + ': configuring output %d as a safe port (0: False, 1: True): %d'%(channel,new))
        self.adw.SetData_Long([new], 199, channel, 1)

    def _do_get_safe_port(self,channel):
        """Read out if gate 'X' is a safe port (ADwin parameter: Data_199[X]).
        
        return value (INT): 1=safe port, 0=no safe port (possible values: 1, 0)
        """
        value=self.adw.GetData_Long(199, channel, 1)[0]
        logging.info(__name__ + ': reading if output %d is a safe port (0: False, 1: True): %d'%(channel,value))
        return value
    
    
        
    
    def _do_set_oversampling_state(self, state, channel):
        '''Setting oversamping on gate "channel" on=1 or off=0.
        Data_188: list of length 20 that lists the oversampled gates unorderd. 
        
        '''
        #maximal number of oversampled gates define by the Adbasic file:
        max_numb_oversampling = 5 #good number if 10 gates are ramped in parallel at the same time
        oversampled_gates_Data = [i for i in  self.adw.GetData_Long(188, 1, max_numb_oversampling) if i != 0]
        if channel <= 8:
            if state==0:
                if channel in oversampled_gates_Data:
                    #remove channel from oversampled_gates_Data
                    oversampled_gates_new = [i for i in oversampled_gates_Data if i!=channel]
                    oversampled_gates_new.extend([0] * (max_numb_oversampling - len(oversampled_gates_new)))
                    self.adw.SetData_Long(oversampled_gates_new, 188, 1, max_numb_oversampling)
                    logging.info(__name__ +': gate %d oversampling stopped.' %channel)
                else:
                    logging.info(__name__ +': oversampling state of gate %d is alread 0.' %channel)
                    
            elif state==1:
                if channel in oversampled_gates_Data:
                    logging.info(__name__ +': gate %d already oversampled.' %channel)
                else:
                    #add channel 
                    oversampled_gates_new = oversampled_gates_Data + [channel]
                    oversampled_gates_new.extend([0] * (max_numb_oversampling - len(oversampled_gates_new)))
                    logging.info(__name__ +': enabling oversampling state of gate %d.' %channel)
                    self.adw.SetData_Long(oversampled_gates_new, 188, 1, max_numb_oversampling)
                
            else:
                logging.warning(__name__+': oversampling state must be 0 (=off) or 1 (=on).')
                input("Press Enter to continue.")
                sys.exit() 
        else:
            logging.warning(__name__+': gate is not defined!')
            input("Press Enter to continue.")
            sys.exit() 
    
    def _do_get_oversampling_state(self, channel):
        '''Getting oversamping state of gate.
        
        '''
        oversampled_gates_Data = [i for i in  self.adw.GetData_Long(188, 1, 200) if i != 0]
        logging.info(__name__ + ": oversampled gates are: " + str(oversampled_gates_Data))
        if channel in oversampled_gates_Data:
            return 1
        else:
            return 0
        
    def oversampled_gates(self):
        '''returns a list of all oversampled gates.
        '''
        oversampled_gates_Data = [i for i in  self.adw.GetData_Long(188, 1, 200) if i != 0]
        return oversampled_gates_Data
    
    
    def _do_set_oversampling_divisions(self, divisions):
        '''BEWARE IF CHANGED ON THE FLY! This will lead to oversampled channels 
        outputting wrong voltages since the period for switching between bits is 
        changed by the function. To resolve the issue set the output voltages of 
        the oversampled gates again. 
        
        Sets the global number of divisions between two bits.
        '''
        if divisions>0 and divisions<1000:
            logging.info(__name__ +': setting global number of oversampling divisions to %d.' %divisions)
            self.set_Par_68_global_long(divisions)  
        else:
            logging.warning(__name__+': divisions must be between 1 and 1000!')
            input("Press Enter to continue.")
            sys.exit()
    
    def _do_get_oversampling_divisions(self):
        '''Gets the global number of divisions between two bits.
        '''
        divisions = int(self.get_Par_68_global_long())
        logging.info(__name__ +': number of oversampling divisions is %d.' %divisions)
        return divisions
    
    def _do_set_voltage_range(self, V_range, channel):
        '''Sets the voltage range of output "channel". This takes into account voltage dividers.
        If a voltage divider of 1/100 (so V_range=0.1V) is employed, the output voltage will be 100 times higher then
        the value you put as a value. 
        It is always initialized as the maximum (10 Volts).
        '''
        if channel<=8 and V_range<=10 and V_range>0: 
            #getting voltage limits set before with "old" voltage range:
            upper_limit = self.get('output%d_individual_upper_voltage_limit_in_V'% channel)
            lower_limit = self.get('output%d_individual_lower_voltage_limit_in_V'% channel)
            
            if V_range<abs(upper_limit) or V_range<abs(lower_limit):
                logging.warning(__name__+': individual voltage limits are higher than voltage range! Please change them beforehand so they fit into the new voltage range!')
                input("Press Enter to continue.")
                sys.exit()
            else:    
                logging.info(__name__ +': setting voltage range of output %d to %f.' %(channel, V_range))
                self.adw.SetData_Float([V_range], 186, channel, 1) 
                
                #renew value of voltage limits with new voltage range:
                self.set('output%d_individual_upper_voltage_limit_in_V'% channel, upper_limit)
                self.set('output%d_individual_lower_voltage_limit_in_V'% channel, lower_limit)
  
        else:
            logging.warning(__name__+': voltage range or channel out of bounds!')
            input("Press Enter to continue.")
            sys.exit()
    
    def _do_get_voltage_range(self, channel):
        '''Gets the voltage range of output "channel".
        '''
        V_range = self.adw.GetData_Float(186, channel, 1)[0]
        logging.info(__name__ +': voltage range of output %d is %f.' %(channel, V_range))
        return V_range


    def initialize_outputs(self, lower_limit=0, upper_limit=0, speed=0.2):
        '''This function sets the number of  gates (including current sources)
        and distributes them on the 8 outputs.
        Gates 1-3 are reserved for the current sources, and are defined as safe port.
        -voltage range is set to 10 for all outputs.
        
        parameters:
            lower_limit: initializes voltage gates with given lower limit
            upper_limit: initializes voltage gates with given uppper limit
            speed: ramping speed in V/s use to set a voltage.
        '''
        #Since this function is excecuted mostly directly after creating the ADwin instrument, the low priority 
        #initialization of the ADwin should be given time to execute. A sleep of 2s should be sufficient. 
        time.sleep(2)
        
        #initailize outputs 
        
         #set voltage range for all gates on ADwin
        for output in range(1,8+1):
            #change for modified outputs!
            #I don't know why self.set_gateX_voltage_range does not work...
            self._do_set_voltage_range(10, output)
               
        #set oversampling to off
        for output in range(1, 8+1):
            self.set('output%d_oversampling_state'% output, 0) 
        
        for output in [1, 2, 3]:
                self.set('output%d_safe_port'% output, 1)    
       
        #initialize voltage limits for current sources:
        for output in range(1, 3+1):
            self.individual_voltage_limits_setter_in_V(-10, 10, output)
                
        #initialize voltage limits for votage gates:
        for output in range(4, 8+1):
            self.individual_voltage_limits_setter_in_V(lower_limit, upper_limit, output)
                
        #set ramping speed. I don't know why self.set_ramping_speed_normal_ports(speed) does not work...
        self._do_set_ramping_speed_normal_ports(speed)
            
        #set all outputs to 0 Volts
        for output in range(1, 3+1):  #current sources
            self.set('output%d_output_current_voltage_in_V'% output, 0)
            
        for output in range(4, 8+1):  
            self.set('output%d_OUTvoltage'% output, 0)
                
            
            
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
        
        #new 1D coil
        #coil calibration parameters
        x_calib = 0.2448 #in Tesla/Amps
        y_calib = 10 #in Tesla/Amps
        z_calib = 10 #in Tesla/Amps
        
        x_max_current = 12.3 #maximal current in Amps through coil x before quench
        y_max_current = 0 #maximal current in Amps through coil y
        z_max_current = 0 #maximal current in Amps through coil z
        
        # #OLD 3D coils
        # #coil calibration parameters
        # x_calib = 0.180 #in Tesla/Amps
        # y_calib = 0.056 #in Tesla/Amps
        # z_calib = 0.060 #in Tesla/Amps
        
        # x_max_current = 8.34 #maximal current in Amps through coil x before quench
        # y_max_current = 5.0 #maximal current in Amps through coil y
        # z_max_current = 7.0 #maximal current in Amps through coil z
        
        #set  voltage 
        if direction == 1:
            voltage_x = amplitude / x_calib / translation_factor_x
            if abs(voltage_x) <=  10 and abs(voltage_x) <= abs(x_max_current / translation_factor_x):
                self.set_output1_output_current_voltage_in_V(voltage_x)
            else:
                logging.warning(__name__+': voltage in x-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 2:
            voltage_y = amplitude / y_calib / translation_factor_y
            if abs(voltage_y) <=  10 and abs(voltage_y) <= abs(y_max_current / translation_factor_y):
                self.set_output2_output_current_voltage_in_V(voltage_y)
            else:
                logging.warning(__name__+': voltage in y-direction out of limits.')
                input("Press Enter to continue.")
                sys.exit()
        
        if direction == 3:
            voltage_z = amplitude / z_calib / translation_factor_z
            if abs(voltage_z) <=  10 and abs(voltage_z) <= abs(z_max_current / translation_factor_z):
                self.set_output3_output_current_voltage_in_V(voltage_z)
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
        
        x_max_current = 12.3 #maximal current in Amps through coil x before quench
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
            self.set_output1_output_current_voltage_in_V(voltage_x) 
        else:
            logging.warning(__name__+': voltage in x-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set y voltage 
        voltage_y = amplitude_y / y_calib / translation_factor_y
        if abs(voltage_y) <=  10 and abs(voltage_y) <= abs(y_max_current / translation_factor_y):
            self.set_output2_output_current_voltage_in_V(voltage_y)
        else:
            logging.warning(__name__+': voltage in y-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
        #set z voltage 
        voltage_z = amplitude_z / z_calib / translation_factor_z
        if abs(voltage_z) <=  10 and abs(voltage_z) <= abs(z_max_current / translation_factor_z):
            self.set_output3_output_current_voltage_in_V(voltage_z)
        else:
            logging.warning(__name__+': voltage in z-direction out of limits.')
            input("Press Enter to continue.")
            sys.exit()
            
    def IV_curve(self, output=None, input_gate=None, V_min=0.0, V_max=0.001, V_div=1, samples=10, 
                 IV_gain=1e9, I_max=1e-9, averages=1000):
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
                self.set('output%d_OUTvoltage'% output, voltage)                
                current = self.get('input%d_INvoltage'% input_gate, averages)/IV_gain
                data_I.append(current) 
                if abs(current) > I_max:
                    break
            for voltage in V_values_positive:        
                data_V.append(voltage/V_div*1000) #voltage in mV
                self.set('output%d_OUTvoltage'% output, voltage)
                current = self.get('input%d_INvoltage'% input_gate, averages)/IV_gain
                data_I.append(current) 
                if abs(current) > I_max:
                    break
            self.set('output%d_OUTvoltage'% output, 0)
        else: 
            print("Input or output not defined!")
            
        return (data_V, data_I)    
        

    
   
   
if __name__ == "__main__":

    ##device test routine
    ##**************************************************************

    qkit.start()
    #1)create instance - implement global voltage limits when creating instance
    #bill with oversampling and parallel gate setting
    bill = qkit.instruments.create('bill', 'ADwin_Pro2_V2',processnumber=1, 
                                   processpath='C:/Users/nanospin/SEMICONDUCTOR/code/ADwin/ramp_input_V2.TC1', 
                                   devicenumber=1, 
                                   global_lower_limit_in_V=-2.5, 
                                   global_upper_limit_in_V=1.0,
                                   global_lower_limit_in_V_safe_port=-10,
                                   global_upper_limit_in_V_safe_port=10)
    
    gate_num = 24
    ohmics = np.arange(24, gate_num+1)
    
    bill.initialize_gates(gate_num,lower_limit=-2, upper_limit=0.8, speed=0.2)
    for ohmic in ohmics:
        bill.individual_voltage_limits_setter_in_V(-10e-3, 10e-3, ohmic)
    
    print(10*'*'+'Initialization complete'+10*'*')
    #bill.set_gate2_out(0.5)
    #bill.set_out(5, 0.5)
    #bill.get_ch1_input_voltage()
   
    #oversampling parameters
    bill.set_oversampling_divisions(10)
    gates_oversampled = [5]
    for gate in gates_oversampled:
        bill.set("gate%d_oversampling_state"%gate, 1)

    