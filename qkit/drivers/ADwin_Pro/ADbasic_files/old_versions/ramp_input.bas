'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 1000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-5K5Q7S9  DESKTOP-5K5Q7S9\nanospin
'<Header End>
'Copy ramps_inputs.bas and ramps_inputs.TC1 into folder of your choice and initialize with QKit'

'ALL VOLTAGES ARE IN DIGITAL VALUES IN THIS SCRIPT!!!'
'Data_190[i]: analog input gate i'
'Data_191[i]: output number variable => set output number on adwin module for each gate'
'Data_192[i]: limit error variable => 1 if voltage limit exceeded or limits not set'
'Data_193[i]: module numbers of gates'
'Data_194[i]: individual lower limit for output voltages, default=0V'
'Data_195[i]: individual upper limit for output voltages, default=0V'
'Data_197[i]: ramp start value, memory of last voltage set on output'
'Data_199[i]: safe port bit => 1 if safe port, 0 if not (default)'
'Data_200[i]: ramp stop value'

'Par_69:      number of averages for input measurement'
'Par_71:      analog input module number'
'Par_75:      number of gates used, default=200 '
'Par_76:      run variable => 1 if device is run'
'FPar_77:     ramping speed in Volts/second normal ports'
'Par_78:      channel which is ramped. only it will be changed during an event'

'The speed adjustment is incrementing the output voltage by the minimal voltage step of 0.3mV and skipping ADwin cycles (1GHz) in between. The skipping parameter is skip.' 

#Include ADwinPro_All.Inc
Dim Data_200[200], Data_199[200], Data_197[200], Data_196[200], Data_195[200], Data_194[200], Data_193[200], Data_192[200], Data_191[200], Data_190[8], Data_189[8] as Long
Dim ramp_down_busy, i, channel, increment_sign, output_number, module_number, skips, skips_total, eval, initialized as Long
Dim stopvalue, difference, rampvalue, speed as Float

#Define input_gate_buffer_Data Data_189
#Define input_gate_Data Data_190
#Define output_number_Data Data_191
#Define limit_error_Data Data_192
#Define module_number_Data Data_193
#Define lower_limit_Data Data_194
#Define upper_limit_Data Data_195
#Define ramp_start_Data Data_197
#Define safe_bit_Data Data_199
#Define ramp_stop_Data Data_200

#Define averages_Par Par_69
#Define input_module_Par Par_71
#Define gate_number_Par Par_75
#Define run_Par Par_76
#Define ramping_speed_Par FPar_77
#Define channel_Par Par_78



LowInit:  
  '1us process delay for T12 processor'
  Processdelay = 1000 
  'analog input module number'
  input_module_Par = 15
  
  'initialize 200 gates: change if more are needed!'
  For channel=1 to 200
    'set outputs and inputs to OV. initialized to -0.0003V so that reseting'
    'to 0V will actually set them to 0V instead of not doing anything''
    ramp_stop_Data[channel]=32767
    'set last voltage of ramp. initialized to -0.0003V so that reseting'
    'to 0V will actually set them to 0V instead of not doing anything'
    ramp_start_Data[channel]=32767
    'all ports are no safe ports per default'
    safe_bit_Data[channel]=0
    'reset limits to 0V'
    lower_limit_Data[channel]=32768
    upper_limit_Data[channel]=32768
    'reset limit error variable, error as long as limits are not set'
    limit_error_Data[channel]=1
    'reset output numbers of gates, default: 0'
    output_number_Data[channel]=0
  Next channel
  
  For channel=1 to 8
    input_gate_Data[channel]=32768
  Next channel
   
  averages_Par = 1   'number of averages'
  gate_number_Par = 200 'number of gates'
  run_Par = 0   'run variable'
  ramping_speed_Par = 0.1  'ramping speed'
  channel_Par = 0   'channel which is ramped'
   
  'number of skips between minimal increments'
  skips = 0
  
  'number of evaluations of inputs'
  eval = 0
  
  'initialisation state of ramp parameters'
  initialized = 0

  'Start AD conversion on channels 1-8'
  P2_Start_ConvF(input_module_Par, 0FFh)
  
  'Finish: ramping down busy variable'
  ramp_down_busy = 0
  
Event:
  
  SelectCase run_Par 'run variable'
    Case 1 'voltage ramps'
      
      SelectCase initialized 'initialization state of ramp parameters'
        Case 0 'initialize rampvalue and ramping sign'
          'channel which is going to be changed'
          channel = channel_Par
          skips = 0
          rampvalue = ramp_start_Data[channel] 
          stopvalue = ramp_stop_Data[channel]
          
          'debug variable:'
          Par_2 = stopvalue
    
          module_number = module_number_Data[channel]
          output_number = output_number_Data[channel]
    
          'check if voltage limits are not exceeded:'
          If ((stopvalue <= upper_limit_Data[channel]) And (stopvalue >= lower_limit_Data[channel])) Then
            'check if channel is a save port'
            If (safe_bit_Data[channel]=1) Then 
              'channel is a safe port so 0.5V/s. so 20V/(2^16)/(10^-6s)0.5V/s=610 skips between minimal voltage increments'
              skips_total = 610
            Else
              'channel is a normal port'
              'If skips = 10 then every 10th clock cycle the voltage will be increased by the minimum value. 20V/(2^16)/(10^-6s)= 305V/s'
              skips_total = Round(305 / ramping_speed_Par) 'FPar_77 is speed in Volts/s'
            EndIf
      
            'difference from start to stop voltage'
            difference = stopvalue - ramp_start_Data[channel]
        
            If (Abs(difference)<>difference) Then 
              'voltage step is negative'
              increment_sign = -1
            Else
              'voltage step is positive'
              increment_sign = 1
            EndIf
            'ADwin initialized successfully'
            initialized = 1  
          Else 
            'voltage limits exceeded'
            limit_error_Data[channel] = 1
      
            stopvalue = rampvalue
                  
            'ADwin is not busy anymore'
            run_Par = 0
          EndIf   
          
      
        Case 1 'ramping voltage'
          If (rampvalue <> stopvalue) Then 
            'adjust ramping speed by skipping incrementation:'    
            If (skips=skips_total) Then
              'change value of ramp by one bit'
              rampvalue = rampvalue + increment_sign
                      
              'ramp up voltage by minimum step with skipped cycles to reach the right speed'
              P2_Write_DAC(module_number,output_number, rampvalue)
              P2_Start_DAC(module_number)
              skips = 0
              
              'debug variable'
              Par_1 = rampvalue
            Else
              skips = skips + 1
            EndIf
        
          Else
            'ramp done'
            'save this voltage in Data_197 for the next ramp'
            ramp_start_Data[channel] = rampvalue
           
            'ADwin to be initialized again'
            initialized = 0
      
            'ADwin is not busy anymore'
            run_Par = 0
          EndIf
      EndSelect
       
  
    Case 2 'read inputs every 10us'
      Processdelay = 3000
      'eval counts number of evaluations of inputs'
      If (eval=0) Then  
        'analog input, Par_71 is module number'
        P2_Wait_EOCF(input_module_Par, 0FFh)
        P2_Read_ADCF8(input_module_Par, input_gate_Data, 1)
        P2_Start_ConvF(input_module_Par, 0FFh) 
        eval = eval + 1 
      Else
        If (eval<averages_Par+1) Then 'evaluations < averages + 1'
          P2_Wait_EOCF(input_module_Par, 0FFh)
          P2_Read_ADCF8(input_module_Par, input_gate_buffer_Data, 1)
          P2_Start_ConvF(input_module_Par, 0FFh)
          For i=1 to 8
            input_gate_Data[i]=input_gate_Data[i] + input_gate_buffer_Data[i]
          Next i
          eval = eval + 1
        Else
          For i=1 to 8
            input_gate_Data[i]= Round(input_gate_Data[i] / eval)
          Next i
          eval = 0
          
          Processdelay = 1000
          'ADwin is not busy anymore'
          run_Par = 0
        EndIf 
      EndIf  
  EndSelect
 
  
  
Finish:
  'Ramp down all outputs to 0 Volts with a sleep delay instad of using the processdelay which doesn't exist in Finish'
  'ADwin is busy now'
  run_Par = -1
  
  For channel=1 to gate_number_Par
    ramp_down_busy = 1   'Parameter that is 1 if a gate is ramped to 0'
    Do 
      SelectCase initialized 'initialization state of ramp parameters'
        Case 0 'initialize rampvalue and ramping sign'
          'channel which is going to be changed'
        
          rampvalue = ramp_start_Data[channel] 
          stopvalue = 32768  '0 Volts'
          
          'debug variable:'
          Par_2 = stopvalue
    
          module_number = module_number_Data[channel]
          output_number = output_number_Data[channel]
      
          'difference from start to stop voltage'
          difference = stopvalue - ramp_start_Data[channel]
        
          If (Abs(difference)<>difference) Then 
            'voltage step is negative'
            increment_sign = -1
          Else
            'voltage step is positive'
            increment_sign = 1
          EndIf
          'ADwin initialized successfully'
          initialized = 1  
          P2_Set_LED(module_number, 1)
        
          
      
        Case 1 'ramping voltage'
          If (rampvalue <> stopvalue) Then  
            'change value of ramp by one bit'
            rampvalue = rampvalue + increment_sign
                    
            P2_Write_DAC(module_number,output_number, rampvalue)
            P2_Start_DAC(module_number)
            
            P2_Sleep(6*(10^4))  '=60k*10ns= 0.6ms waiting for a voltage increment of 0.3mV to achieve 0.5V/s ramping speed'
              
            'debug variable'
            Par_1 = rampvalue
          Else
            'ramp done'
            'save this voltage in Data_197 for the next ramp'
            ramp_start_Data[channel] = rampvalue
           
            'ADwin to be initialized again'
            initialized = 0
            P2_Set_LED(module_number, 0)
          
            'ADwin is not busy anymore'
            ramp_down_busy = 0
          EndIf
      EndSelect
    Until (ramp_down_busy=0)
  Next channel

  'ADwin is not busy anymore'
  run_Par = 0
