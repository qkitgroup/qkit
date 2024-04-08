'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 2
' Initial_Processdelay           = 2000
' Eventsource                    = External
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 4
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LISTER-W  PHI-LISTER-W\nanospin
'<Header End>
'Process needs to use an external event source and starts burst measurements of amount sample_length.
'the memory address is shifted for every pulse in the pulse train. 
'then another process reads out the whole burst data 

#Include ADwinPro_All.Inc

#Define module 15                                          'number given to the card 1-15, we use it as 15 always
#Define sample_length Par_10                               'SHARED WITH OTHER PROCESS! MUST BE DIVISIBLE BY 8 if one channel is read only, or divisible by 4 if more are read
#Define measurements_done Par_13                           'SHARED WITH OTHER PROCESS! tells how many measurments (triggers for one pulse train) are already measured
#Define flag_error Par_17                                  'SHARED WITH OTHER PROCESS! 'is 1 if things go wrong
#Define index_to_write Par_15                              'SHARED WITH OTHER PROCESS!'index in Card memory where to write to
#Define trigger_on Par_20                                  'If Par_20=1 then trigger is send to awg by other process

Dim pattern as Long                                        'bit pattern to address one module


Init:
  Processdelay = 1000
  pattern = Shift_Left(1,module-1) 'makes 100000000000000
  
  index_to_write = 0 'changed back to 0 in Event_Stopp process as this process is run once after starting.
  
  CPU_Event_Config(1,1,1) '50ns delay of Event In
 
  P2_set_average_filter(module, 0)
  
  'Par_5 = 0 'debug
 
  
Event: 
  'starting this process will run the init and event once! so index_to_write is set to 0 in other process.
  Processdelay = 1000 'doesnt matter
  
  'setting trigger to AWG off 
  trigger_on = 0 'no triggers are send to AWG anymore by ADwin
  
  'Inc Par_5 'debug
  
  'If (P2_Burst_Status(module)<>0) Then 'debug: Last burst not finished yet! happens in the first one
  '  Inc Par_51 'debug
  'EndIf
  
  P2_Burst_Init(module,0001b,index_to_write,sample_length,25,000b)
  P2_Burst_Reset(pattern)
  P2_Burst_Start(pattern)
  
  index_to_write = index_to_write + (0.5*sample_length) 'two samples per memory unit, reset in second process
  
  'Par_50 = index_to_write 'debug
  
  measurements_done = measurements_done + 1
 
