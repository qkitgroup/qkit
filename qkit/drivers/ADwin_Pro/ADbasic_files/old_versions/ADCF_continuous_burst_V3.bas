'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 4
' Initial_Processdelay           = 2000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 4
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LISTER-W  PHI-LISTER-W\nanospin
'<Header End>
'Process writes ADC valuse each 13.33us to memory of ADwin. 

#Include ADwinPro_All.Inc

#Define module 15                                             'number given to the card 1-15, we use it as 15 always                            
#Define data Data_2                                                                             
#Define sample_length Par_8                                   'number of data points
#Define memory_size 1e8                                       'size of Memory block for full measurement (about 10 events), multiple of 4

Dim data[memory_size] as Long   
Dim pattern as Long  
Dim rest as Long                                       

Init:
  Processdelay = 2000
  P2_SET_LED(module, 1)
  
  Par_8 = 8*1e2
  
  
   
  pattern = Shift_Left(1,module-1) 'makes 100000000000000
  
  P2_Burst_Init(module,0001b,0,sample_length,1333,000b) 'data point every 13.33us about 75kHz
  P2_set_average_filter(module, 5)
  P2_Burst_Reset(pattern)
  P2_Burst_Start(pattern)
    

Event: 
  Processdelay = 1e7
  
  Inc Par_1
  rest = (P2_Burst_Status(module))
  Par_3 = rest
  
  If (rest=0) Then
    Inc Par_2
    End
  EndIf
  

Finish:
  P2_Burst_Read_Unpacked1(module, sample_length, 0, data, 1, 1)
  
  P2_SET_LED(module, 0)
