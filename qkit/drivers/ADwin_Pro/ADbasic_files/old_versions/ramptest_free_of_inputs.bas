'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 10000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-5K5Q7S9  DESKTOP-5K5Q7S9\Sven
'<Header End>
'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 10000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-5K5Q7S9  DESKTOP-5K5Q7S9\Sven
' Bookmarks                      = 8,22,23,46,79,91
'<Header End>

'Changes by Daniel: Line 121-126 and line 157 changed.'

'ramptest.bas - copy into folder of your choice'

'Data_190[i]: analog input gate i'
'Data_191[i]: output number variable => set output number on adwin module for each gate'
'Data_192[i]: limit error variable => 1 if voltage limit exceeded or limits not set'
'Data_193[i]: module numbers of gates'
'Data_194[i]: individual lower limit for output voltages, default=0V'
'Data_195[i]: individual upper limit for output voltages, default=0V'
'Data_196[i]: time to ramp (in µs) default=1µs, '
'Data_197[i]: ramp start value=> if no input, last set voltage is taken to be start voltage'
'Data_198[i]: write status variable => 1 while setting voltage to gate i'
'Data_199[i]: safe port bit => 1 if safe port, 0 if not (default)'
'Data_200[i]: ramp stop value'
'Par_71:      analog input module number'
'Par_72:      test variable to read out input'
'Par_73:      module number test variable to read out input'
'Par_74:      output number test variable to read out input'
'Par_75:      number of gates used, default=200 '
'Par_76:      run variable => 1 if device is run'

#Include ADwinPro_All.Inc
Dim Data_200[200], Data_199[200], Data_198[200], Data_197[200], Data_196[200], Data_195[200], Data_194[200], Data_193[200], Data_192[200], Data_191[200], Data_190[200], Data_189[200] as Long
Dim channel, ramp_iterator, loop_iterator, safe_port_bit, output_number, range, startvalue, stopvalue, time, voltage_limit_individual_lower, voltage_limit_individual_upper, module_number, write, run, input_iterator, input_value, input_module as Long
Dim voltagestep as Float

Init:
  'default settings'
  '********************************************************************'
  '1 s process delay (T12 processor)'
  Processdelay=1000
  'set number of gates used'
  Par_75=200
  'analog input module number'
  Par_71= 15
  For channel=1 to 200
    'set outputs and inputs to OV'
    Data_200[channel]=32768
    Data_190[channel]=32768
    'set outputs as safe ports'
    Data_197[channel]=32768
    'default time to ramp: 1µs'
    Data_196[channel]=1
    'all ports are no safe ports per default'
    Data_199[channel]=0
    'reset status variables'
    Data_198[channel]=0
    'reset limits to 0V'
    Data_194[channel]=32768
    Data_195[channel]=32768
    'reset limit error variable, error as long as limits are not set'
    Data_192[channel]=1
    'reset output numbers of gates, default: 0'
    Data_191[channel]=0
    'reset input module numbers to 1'
    Data_189[channel]=1
  Next channel

  '********************************************************************'
  'for test routine -  delete when in usage'
  ''Par_75=8
  '********************************************************************'

  'channel iterator channel, goes from 1 to Par_75'
  channel=1
  'ramp iterator ramp_iterator, goes from 1 to time/1ms'
  ramp_iterator=1

Event:

'''analog input, always active'
  'input_module=Par_71
  'Data_190[1]=P2_ADCF(input_module,1)
  'Data_190[2]=P2_ADCF(input_module,2)
  'Data_190[3]=P2_ADCF(input_module,3)
  'Data_190[4]=P2_ADCF(input_module,4)
  'Data_190[5]=P2_ADCF(input_module,5)
  'Data_190[6]=P2_ADCF(input_module,6)
  'Data_190[7]=P2_ADCF(input_module,7)
  'Data_190[8]=P2_ADCF(input_module,8)

  'test variable to read out voltage on analog input'
  ''Par_72=P2_ADC(Par_73, Par_74)
  'do nothing until Par_76=1'

  run=Par_76
  If (run=1) Then

    'pass values at beginning of ramp'
    If (ramp_iterator=1) Then
      voltage_limit_individual_lower=Data_194[channel]
      voltage_limit_individual_upper=Data_195[channel]
      'write input (stop voltage) to buffer and check if voltage limit exceeded'
      stopvalue=Data_200[channel]

      'write start value to buffers'
      startvalue=Data_197[channel]
      write=Data_197[channel]
      'write time to ramp to buffer'
      time=Data_196[channel]

      'check if the voltage limits are exceeded, the ports will remain unchanged if yes'
      If ((stopvalue > voltage_limit_individual_upper) Or (stopvalue < voltage_limit_individual_lower)) Then
        stopvalue=startvalue
        Data_192[channel]=1
      EndIf

      'set range to ramp over'
      range=stopvalue-startvalue
      'voltage step=range/(time to ramp) or fixed maximum value for safe port'
      voltagestep=range/time
      'safe ports: maximum voltage step => change voltage by one digit every 625 rounds = 0.5 V / s'
      'smaller voltage steps are possible'
      'using loop_iterator and safe_port_bit to adjust voltage increment in each step'
      loop_iterator=625
      If ((Data_199[channel]=1) And (Abs(voltagestep)>0.0016)) Then
        voltagestep=voltagestep/Abs(voltagestep)
        loop_iterator=625
        safe_port_bit=1
      Else
        loop_iterator=625
        safe_port_bit=0
      EndIf
      ''safe_port_bit=Data_199[channel]
      'write status variable set to 1'
      If ((range>0) Or (range<0)) Then
        Data_198[channel]=1
      EndIf
    EndIf

    module_number=Data_193[channel]
    output_number=Data_191[channel]

    'augment output voltage by voltagestep'
    'for safe ports: maximum voltage step => increment by one digit every 625 rounds = 0.5 V / s'
    If (loop_iterator=625) Then
      'reset loop_iterator to 625, 0 for ports, safe ports, respectively'
      If (safe_port_bit=1) Then
        loop_iterator=0     'will be incremented by 1'
      Else
        loop_iterator=625   'wont be incremented at all'
      EndIf
      
      If ((stopvalue<write) Or (stopvalue>write)) Then
        'increase or decrease voltage by voltagestep'
        write=Round(startvalue+voltagestep*ramp_iterator)
        'pass write buffer to Data_200 and to DAC module'
        'by doing this, the applied voltage can be read out via Data_200[channel] during ramping'
        'If applied voltage > voltage limit:'
        Data_200[channel]=write
        P2_Write_DAC(module_number,output_number,write)
        P2_Start_DAC(module_number)
        ramp_iterator=ramp_iterator+1
      Else
        Data_200[channel]=write
        P2_Write_DAC(module_number,output_number,write)
        P2_Start_DAC(module_number)
        'overwrite start voltage to ramp the next time and move to next gate'
        Data_197[channel]=write
        'reset write status variable'
        Data_198[channel]=0
        'reset ramp iterator'
        ramp_iterator=1
        'augment channel by 1'
        channel=channel+1
      EndIf
    EndIf

    'augment loop_iterator by 0, 1 for ports, safe ports, respectively'
    loop_iterator=loop_iterator+safe_port_bit

    'restart iteration over channels'
    If ((channel=Par_75+1) Or (Par_75=1)) Then
      channel=1
    EndIf
  EndIf

