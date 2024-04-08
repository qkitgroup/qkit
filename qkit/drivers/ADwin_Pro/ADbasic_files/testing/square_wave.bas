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
'Creats a 50% duty cycle square wave with t_period and number of periods when Par_20 is set to 1

#Include ADwinPro_All.inc
#Define module 2
#Define number_DAC 1
#Define voltage_high 50000
#Define voltage_low 32768

Dim cycle as Long
Dim counter as Long
Dim periods as Long
Dim t_period as Long

Init:
  cycle = 0  'can be either high=0 or low=1
  processdelay = 2000  
  counter = 0  'counts the number of periods
  
  periods = 1e9
  t_period = 10000 'in us
  
  
Event:
  processdelay = t_period*500
  
  If (counter<2*periods) Then
    counter = counter+1
      
    SelectCase cycle
      Case 0
        P2_Write_Dac(module, number_DAC, voltage_high)
        Inc Par_60
      Case 1
        P2_Write_Dac(module, number_DAC, voltage_low)
        Inc Par_61
    EndSelect
  
    P2_Start_DAC(module)
  
    Inc cycle
    IF (cycle=2) Then
      cycle=0
    EndIF
  EndIf
    
  IF (counter>=2*periods) Then
    counter = 0
  EndIF

 
