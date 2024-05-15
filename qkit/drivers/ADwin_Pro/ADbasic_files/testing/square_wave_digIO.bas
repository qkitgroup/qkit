'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 10
' Initial_Processdelay           = 10000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = Low
' Priority_Low_Level             = 0
' Version                        = 1
' ADbasic_Version                = 6.3.1
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LISTER-W  PHI-LISTER-W\nanospin
'<Header End>
#Include ADwinPro_All.inc


Init:
  processdelay = 2000  
  CPU_Dig_IO_Config(01b)
  CPU_Digout(0,0)
  
  
Event:
  processdelay = 1e6
  
  'For counter=1 to 10
  CPU_Digout(0,0) 
  CPU_Sleep(100*100)
  CPU_Digout(0, 1)
  P2_Sleep(100*100)
  CPU_Digout(0,0)
  
  
  
