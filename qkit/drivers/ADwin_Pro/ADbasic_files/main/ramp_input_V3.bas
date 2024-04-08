'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 2000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = Low
' Priority_Low_Level             = 10
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LISTER-W  PHI-LISTER-W\nanospin
' Bookmarks                      = 41,154,417,418,426,430
'<Header End>
'Copy ramps_inputs.bas and ramps_inputs.TC1 into folder of your choice and initialize with QKit'
'ADPro: modules 1-14 are DACs, while module 15 should be an ADC. 

'ALL VOLTAGES ARE IN DIGITAL VALUES IN THIS SCRIPT!!!'
'ALL INDICES START FROM 1 TO RELATE TO NUMBER OF GATE. Generally Data_XXX[0] does not exist!

'Data_178-Data_184: INTERNAL array buffers for parallel setting of gates and oversampling. Do not change from outside!
'Data_185[i]: gates which are to be set in parallel. so Data_185=[15, 20, 1 ,10, 0, 0, 0,..] 
'Data_186[i]: voltage range of outputs. 10 means +-10V. This is only a storage for QKit calculations. Not used by ADwin directly.
'Data_187[i]: steps in one period of oversampling in which the lower bit is kept. The index corresponds to the gates in Data_188. So gate Data_188[i] is Data_187[i] steps in lower bit.
'Data_188[i]: gates which are oversampled continuously. so Data_188=[15, 20, 1 ,10, 0, 0, 0,..]  
'Data_190[i]: analog input gate i'
'Data_191[i]: output number variable => set output number on adwin module for each gate'
'Data_192[i]: limit error variable => 1 if voltage limit exceeded or limits not set'
'Data_193[i]: module numbers of gates'
'Data_194[i]: individual lower limit for output voltages, default=0V'
'Data_195[i]: individual upper limit for output voltages, default=0V'
'Data_197[i]: ramp start value, memory of last voltage set on output. INTERN USE ONLY!'
'Data_198[i]: ramp value at the moment which ist set to DAC. for single channel or parallel ramping 
'Data_199[i]: safe port bit => 1 if safe port, 0 if not (default)'
'Data_200[i]: ramp stop value'

'Par_68:      number of steps for one period for oversampling, usually between 10 to 100
'Par_69:      number of averages for input measurement ADC'
'Par_70:      number of gates ramped in parallel. Ramping process will decrease Par_70 until 0 and then finish.
'Par_71:      analog input module number'
'Par_75:      number of gates used, default=200 '
'Par_76:      run variable => 1 if device is run'
'FPar_77:     ramping speed in Volts/second normal ports'
'Par_78:      channel which is ramped. only it will be changed during an event'

'DEBUG variables:
'Par_1:       rampvalue at the moment
'Par_2:       stop value of the ramp 

'The speed adjustment is incrementing the output voltage by the minimal voltage step of 0.3mV and skipping ADwin cycles (1GHz) in between. The skipping parameter is skip.' 

#Include ADwinPro_All.Inc
Dim Data_200[200], Data_199[200], Data_198[200], Data_197[200], Data_196[200], Data_195[200], Data_194[200], Data_193[200], Data_192[200], Data_191[200], Data_190[8], Data_189[8], Data_188[200], Data_187[200] as Long
Dim Data_185[200], Data_183[200], Data_182[200], Data_181[200], Data_180[200], Data_178[200] as Long 'Data parameters in this line only for parallel gate setting
Dim Data_186[200] as Float
Dim ramp_down_busy, i, channel, increment_sign, output_number, module_number, skips, skips_total, eval, initialized, iterator_parallel, iterator_oversampled, step_oversampling as Long
Dim stopvalue, rampvalue, difference, speed as Float



#Define initialized_parallel_Data Data_178
#Define difference_parallel_Data Data_180
#Define skips_parallel_Data Data_181
#Define skips_total_parallel_Data Data_182
#Define increment_sign_parallel_Data Data_183
#Define ramped_channels_parallel_Data Data_185

#Define voltage_range_Data Data_186 
#Define oversampling_steps_lower_bit_Data Data_187
#Define oversampled_gates_Data Data_188
#Define input_gate_buffer_Data Data_189
#Define input_gate_Data Data_190
#Define output_number_Data Data_191
#Define limit_error_Data Data_192
#Define module_number_Data Data_193
#Define lower_limit_Data Data_194
#Define upper_limit_Data Data_195
#Define ramp_start_Data Data_197
#Define rampvalue_Data Data_198
#Define safe_bit_Data Data_199
#Define ramp_stop_Data Data_200

#Define oversampling_number_of_steps_Par Par_68
#Define averages_Par Par_69
#Define ramped_gates_parallel_Par Par_70
#Define input_module_Par Par_71
#Define gate_number_Par Par_75
#Define run_Par Par_76
#Define ramping_speed_FPar FPar_77
#Define channel_Par Par_78


Init:  
  '2us process delay for T12 processor, Analog outs are 500kHz so 2000 makes sense
  Processdelay = 5000
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
    rampvalue_Data[channel]=32768
    
    'all ports are no safe ports per default'
    safe_bit_Data[channel]=0
    
    'reset limits to 0V'
    lower_limit_Data[channel]=32768
    upper_limit_Data[channel]=32768
    
    'reset limit error variable, error as long as limits are not set'
    limit_error_Data[channel]=1
    
    'reset output numbers of gates, default: 0'
    output_number_Data[channel]=0
       
    'reset voltage range data for outputs
    voltage_range_Data[channel]=0

    oversampled_gates_Data[channel]=0
    oversampling_steps_lower_bit_Data[channel]=0
      
    '----parallel:
    'reset variablse for ramping gates in parallel
    initialized_parallel_Data[channel]=0
    skips_parallel_Data[channel]=0
    difference_parallel_Data[channel]=0
    skips_parallel_Data[channel]=0
    skips_total_parallel_Data[channel]=0
    increment_sign_parallel_Data[channel]=0
    ramped_channels_parallel_Data[channel]=0
       
    IF (channel<=8) Then
      input_gate_Data[channel]=32768
    EndIf
  Next channel
   
  averages_Par = 1   'number of averages'
  gate_number_Par = 200 'number of gates'
  run_Par = 0   'run variable'
  ramping_speed_FPar = 0.1  'ramping speed'
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
  
  'reset number of gates which are to be set in parallel
  ramped_gates_parallel_Par = 0
  
  'reset the iterator for the oversampling that counts one period
  step_oversampling = 0
    
  'reset  number of oversampling steps
  oversampling_number_of_steps_Par = 1
  
  
  
Event: 
  Processdelay = 6000    'this was changed in August 2022 from the original value of 2000. All timings have been adjusted accordingly 
  
  SelectCase run_Par 'run variable'
        
    Case 1 'voltage ramps'
      SelectCase initialized 'initialization state of ramp parameters'
        Case 0 'initialize rampvalue and ramping sign'
          'channel which is going to be changed'
          channel = channel_Par
          skips = 0
          rampvalue_Data[channel] = ramp_start_Data[channel] 
          stopvalue = ramp_stop_Data[channel]
            
          'debug variable:'
          'Par_2 = stopvalue
      
          module_number = module_number_Data[channel]
          output_number = output_number_Data[channel]
      
          'check if voltage limits are not exceeded:'
          If ((stopvalue <= upper_limit_Data[channel]) And (stopvalue >= lower_limit_Data[channel])) Then
            
            'check if channel is a save port'
            If (safe_bit_Data[channel]=1) Then 
              'channel is a safe port so 0.5V/s. so 20V/(2^16)/(6*10^-6s)/0.5V/s=102 skips between minimal voltage increments'
              'The ramping speed is not increased for safe ports of the voltage range is lowered by voltage dividers.
              SelectCase channel
                Case 1 
                  skips_total = 102 'x-coil speed 
                Case 2
                  skips_total = 102 'y-coil speed 
                Case 3
                  skips_total = 102 'z-coil speed 
                CaseElse
                  skips_total = 102
              EndSelect
           
            Else
              'channel is a normal port. The ramping speed (so amount of skips is adjusted also with the maximum voltage range of the outputs.'
              'If skips = 10 then every 10th clock cycle the voltage will be increased by the minimum value. 2*10V/(2^16)/(6*10^-6s)= 51V/s'
              skips_total = Round(51 / ramping_speed_FPar * (voltage_range_Data[channel] / 10)) 'FPar_77 is speed in Volts/s'
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
        
            stopvalue = rampvalue_Data[channel]
                    
            'ADwin is not busy anymore'
            run_Par = 0
          EndIf   
            
        
        Case 1 'ramping voltage'
          If (rampvalue_Data[channel] <> stopvalue) Then 
            'adjust ramping speed by skipping incrementation:'    
            If (skips=skips_total) Then
              'change value of ramp by one bit'
              rampvalue_Data[channel] = rampvalue_Data[channel] + increment_sign
                        
              'ramp up voltage by minimum step with skipped cycles to reach the right speed'
              P2_Write_DAC(module_number,output_number, rampvalue_Data[channel])
              'P2_Start_DAC(module_number) taken out since DACs are started at the end of an event 
              skips = 0
                
              'debug variable'
              'Par_1 = rampvalue_Data[channel]
            Else
              skips = skips + 1
            EndIf
          
          Else
            'ramp done'
            'save this voltage in Data_197 for the next ramp'
            ramp_start_Data[channel] = rampvalue_Data[channel]
             
            'ADwin to be initialized again'
            initialized = 0
                    
            'ADwin is not busy anymore'
            run_Par = 0
          EndIf
      EndSelect
         
    
        
    
        
    Case 2 'read inputs
      'eval counts number of evaluations of inputs'
      If (eval=0) Then  
        'analog input, Par_71 is module number'
        P2_Wait_EOCF(input_module_Par, 1111b)
        P2_Read_ADCF4(input_module_Par, input_gate_Data, 1)
        P2_Start_ConvF(input_module_Par, 1111b) 
        eval = eval + 1 
      Else
        If (eval<averages_Par+1) Then 'evaluations < averages + 1'
          'P2_Wait_EOCF(input_module_Par, 1111b) not necessary if Process Delay long enough. Not relying on EOC makes sure oversampling is still working properly. 
          P2_Read_ADCF4(input_module_Par, input_gate_buffer_Data, 1)
          P2_Start_ConvF(input_module_Par, 1111b)
          For i=1 to 4
            input_gate_Data[i]=input_gate_Data[i] + input_gate_buffer_Data[i]
          Next i
          eval = eval + 1
        Else
          For i=1 to 4
            input_gate_Data[i]= Round(input_gate_Data[i] / eval)
          Next i
          eval = 0
            
          'ADwin is not busy anymore'
          run_Par = 0
        EndIf 
      EndIf
  
        
        
        
    Case 3 'voltage ramps in parallel'
      For iterator_parallel=1 To 12    'iterate over 12 gates
        IF (ramped_channels_parallel_Data[iterator_parallel]<>0) Then  
          'ramped_channels_parallel_Data[i] is the gate which uses parameters skips_parallel_Data[i] 
          'check if gate needs to be ramped  
   
          SelectCase initialized_parallel_Data[iterator_parallel] 'initialization state of ramp parameters'
            Case 0 'initialize rampvalue and ramping sign'
              'channel which is going to be changed is ramped_channels_Data[iterator_parallel]=1'
              skips_parallel_Data[iterator_parallel] = 0
              rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]] = ramp_start_Data[ramped_channels_parallel_Data[iterator_parallel]] 
    
              'debug variable:'
              'Par_2 = ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]]
                
              'check if voltage limits are not exceeded:'
              If ((ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]] <= upper_limit_Data[ramped_channels_parallel_Data[iterator_parallel]]) And (ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]] >= lower_limit_Data[ramped_channels_parallel_Data[iterator_parallel]])) Then
                
                'check if channel is a save port'
                If (safe_bit_Data[ramped_channels_parallel_Data[iterator_parallel]]=1) Then 
                  'channel is a safe port so 0.5V/s. so 2*10V/(2^16)/(6*10^-6s)/0.5V/s=102 skips between minimal voltage increments'
                  'The ramping speed is not increased for safe ports of the voltage range is lowered by voltage dividers.
                  SelectCase ramped_channels_parallel_Data[iterator_parallel]
                    Case 1 
                      skips_total_parallel_Data[iterator_parallel] = 102 'x-coil speed 
                    Case 2
                      skips_total_parallel_Data[iterator_parallel] = 102 'y-coil speed 
                    Case 3
                      skips_total_parallel_Data[iterator_parallel] = 102 'z-coil speed 
                    CaseElse
                      skips_total_parallel_Data[iterator_parallel] = 102
                  EndSelect
                  
                Else
                  'channel is a normal port. The ramping speed (so amount of skips is adjusted also with the maximum voltage range of the outputs.'
                  'If skips = 10 then every 10th clock cycle the voltage will be increased by the minimum value. 2*10V/(2^16)/(6*10^-6s)= 51V/s'
                  skips_total_parallel_Data[iterator_parallel] = Round(51 / ramping_speed_FPar * (voltage_range_Data[ramped_channels_parallel_Data[iterator_parallel]] / 10)) 'FPar_77 is speed in Volts/s'
                EndIf
        
                'difference from start to stop voltage'
                difference_parallel_Data[iterator_parallel] = ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]] - ramp_start_Data[ramped_channels_parallel_Data[iterator_parallel]]
          
                If (Abs(difference_parallel_Data[iterator_parallel])<>difference_parallel_Data[iterator_parallel]) Then 
                  'voltage step is negative'
                  increment_sign_parallel_Data[iterator_parallel] = -1
                Else
                  'voltage step is positive'
                  increment_sign_parallel_Data[iterator_parallel] = 1
                EndIf               
                            
                'ADwin initialized successfully'
                initialized_parallel_Data[iterator_parallel] = 1
              Else 
                'voltage limits exceeded'
                limit_error_Data[ramped_channels_parallel_Data[iterator_parallel]] = 1
        
                ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]] = rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]]
                  
                'ADwin is not busy anymore on this gate so gate must not be ramped anymore.
                ramped_channels_parallel_Data[iterator_parallel]=0 
                
                'One gate less to ramp:
                ramped_gates_parallel_Par = ramped_gates_parallel_Par - 1
              EndIf   
            
        
            Case 1 'ramping voltage'
              If (rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]] <> ramp_stop_Data[ramped_channels_parallel_Data[iterator_parallel]]) Then 
                'adjust ramping speed by skipping incrementation:'
                If (skips_parallel_Data[iterator_parallel]=skips_total_parallel_Data[iterator_parallel]) Then
                  'change value of ramp by one bit'
                  rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]] = rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]] + increment_sign_parallel_Data[iterator_parallel]
                        
                  'ramp up voltage by minimum step with skipped cycles to reach the right speed'
                  P2_Write_DAC(module_number_Data[ramped_channels_parallel_Data[iterator_parallel]],output_number_Data[ramped_channels_parallel_Data[iterator_parallel]], rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]])
                  'P2_Start_DAC(module_number) taken out since DACs are started at the end of an event 
                  skips_parallel_Data[iterator_parallel] = 0
                
                  'debug variable'
                  'Par_1 = rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]]

                Else
                  'skip
                  skips_parallel_Data[iterator_parallel] = skips_parallel_Data[iterator_parallel] + 1
                EndIf

              Else
                'ramp done'
                'save this voltage in ramp_start_Data for the next ramp'
                ramp_start_Data[ramped_channels_parallel_Data[iterator_parallel]] = rampvalue_Data[ramped_channels_parallel_Data[iterator_parallel]]
             
                'ADwin to be initialized again'
                initialized_parallel_Data[iterator_parallel] = 0
                   
                'ADwin is not busy anymore on this gate so gate must not be ramped anymore. 
                ramped_channels_parallel_Data[iterator_parallel]=0
                
                'One gate less to ramp:
                ramped_gates_parallel_Par = ramped_gates_parallel_Par - 1 
              EndIf
          EndSelect
          
        EndIf
        'Do it for the next gate  
      Next iterator_parallel
      
      'If no gates are to be ramped anymore: finish   
      If (ramped_gates_parallel_Par=0) Then
        'ADwin is not busy anymore'
        run_Par = 0
      EndIf    
  EndSelect
   
    
  
  '--------------------------------------------------------------------------------
  'Oversmapling continuously of a couple of gates every event at 167kHz
  'Jumping between two bits for a period of "oversampling_number_of_steps" with the amount of steps "oversampling_steps_lower_bit" in the the lower bit
  'oversampled_gates_Data[i] is the gate which is oversampled using the steps oversampling_steps_lower_bit[i]
  'oversampling ist NOT stopped for channels which are ramped at the moment! So the current value of the DAC rampvalue_Data is used for oversampling instead of ramp_stop_Data.
  
  
  IF (step_oversampling>oversampling_number_of_steps_Par) Then
    step_oversampling=1 'one period finished
  Else
    Inc(step_oversampling) 'increments the time step for ONE amount of processdelay
  EndIF

  For iterator_oversampled=1 to 20: 'loop over 20 possible gates
    'check which gate is oversampled:
    IF (oversampled_gates_Data[iterator_oversampled]<>0) Then   
      IF (step_oversampling=1) Then
        'Always go to lower bit in the beginning of a period.
        P2_Write_DAC(module_number_Data[oversampled_gates_Data[iterator_oversampled]], output_number_Data[oversampled_gates_Data[iterator_oversampled]], rampvalue_Data[oversampled_gates_Data[iterator_oversampled]])
      Else
        IF (step_oversampling=(1+oversampling_steps_lower_bit_Data[oversampled_gates_Data[iterator_oversampled]])) Then
          'If its time to move up to the higher bit then 
          'This step is never reached when oversampling_steps_lower_bit_Data[i]=0
          'PROBLEM: oversampling highest bit does not work!
          P2_Write_DAC(module_number_Data[oversampled_gates_Data[iterator_oversampled]], output_number_Data[oversampled_gates_Data[iterator_oversampled]], (rampvalue_Data[oversampled_gates_Data[iterator_oversampled]]+1))  
        EndIF     
      EndIF
    EndIF
  Next iterator_oversampled
  
   
  '-----------------------------------------------------------------------------------
    
   

  'In each event all DACs are Started. ADD NEW DAC MODULES BELOW!
  P2_Start_DAC(1)
  P2_Start_DAC(2)
  P2_Start_DAC(3)
  P2_Start_DAC(4)
  P2_Start_DAC(5)
  P2_Start_DAC(6)
  P2_Start_DAC(7)
  P2_Start_DAC(8)
  P2_Start_DAC(9)
  
  
  
  
Finish:
  'Ramp down all outputs to 0 Volts with a sleep delay instad of using the processdelay which doesn't exist in Finish'
  'ADwin is busy now'
  'run_Par = -1
  '
  'For channel=1 to gate_number_Par
  '  ramp_down_busy = 1   'Parameter that is 1 if a gate is ramped to 0'
  '  Do 
  '    SelectCase initialized 'initialization state of ramp parameters'
  '      Case 0 'initialize rampvalue and ramping sign'
  '        'channel which is going to be changed'
  '      
  '        rampvalue = ramp_start_Data[channel] 
  '        stopvalue = 32768  '0 Volts'
  '        
  '        'debug variable:'
  '        'Par_2 = stopvalue
  '  
  '        module_number = module_number_Data[channel]
  '        output_number = output_number_Data[channel]
  '    
  '        'difference from start to stop voltage'
  '        difference = stopvalue - ramp_start_Data[channel]
  '      
  '        If (Abs(difference)<>difference) Then 
  '          'voltage step is negative'
  '          increment_sign = -1
  '        Else
  '          'voltage step is positive'
  '          increment_sign = 1
  '        EndIf
  '        'ADwin initialized successfully'
  '        initialized = 1  
  '        P2_Set_LED(module_number, 1)
  '      
  '        
  '    
  '      Case 1 'ramping voltage'
  '        If (rampvalue <> stopvalue) Then  
  '          'change value of ramp by one bit'
  '          rampvalue = rampvalue + increment_sign
  '                  
  '          P2_Write_DAC(module_number,output_number, rampvalue)
  '          P2_Start_DAC(module_number)
  '          
  '          P2_Sleep(6*(10^4))  '=60k*10ns= 0.6ms waiting for a voltage increment of 0.3mV to achieve 0.5V/s ramping speed'
  '            
  '          'debug variable'
  '          'Par_1 = rampvalue
  '        Else
  '          'ramp done'
  '          'save this voltage in Data_197 for the next ramp'
  '          ramp_start_Data[channel] = rampvalue
  '         
  '          'ADwin to be initialized again'
  '          initialized = 0
  '          P2_Set_LED(module_number, 0)
  '        
  '          'ADwin is not busy anymore'
  '          ramp_down_busy = 0
  '        EndIf
  '    EndSelect
  '  Until (ramp_down_busy=0)
  'Next channel
  '
  'ADwin is not busy anymore'
  'run_Par = 0
