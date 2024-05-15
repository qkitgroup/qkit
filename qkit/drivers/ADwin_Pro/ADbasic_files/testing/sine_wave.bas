'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 9
' Initial_Processdelay           = 4000
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
'<Header End>
#Include ADwinPro_All.inc                         ' Include-file For Pro II system 

#Define module 2
#Define dac_no 1
#Define PI 3.14159265 
#Define data Data_20
#Define samples 1e4

Dim Data_20[samples+1] As Float                        'waveform table
Dim count As Float
Dim i As Long



INIT:  
  Processdelay = 1e5          
  For i = 1 TO samples
    data[i] = (Sin(2 * PI * i / samples)*50000/2)+32768         ' generates a sine wave
  Next i
  data[samples+1] = data[1]                     ' one additional element is necessary!
 
  count = 1
  
EVENT:
  Processdelay = 1e6
  P2_write_dac(module, dac_no, data[count])
  'P2_start_dac(module)
  
  Inc count
  If (count > samples) Then 
    count = 1
  EndIf
  

 
  
