'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 9
' Initial_Processdelay           = 10000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = Low
' Priority_Low_Level             = 1
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LISTER-W  PHI-LISTER-W\nanospin
'<Header End>
#Include ADwinPro_All.Inc


Init:
  Par_10 = 80
  Par_11 = 10
  Par_12 = 3
  
  CPU_Dig_IO_Config(11b)
  
  CPU_Digout(0,1)
  
Event: 
  Processdelay = 200000

   
 
 
  
