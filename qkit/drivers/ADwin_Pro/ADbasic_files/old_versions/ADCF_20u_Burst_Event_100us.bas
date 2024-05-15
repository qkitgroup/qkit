'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 2
' Initial_Processdelay           = 100000
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
#Include ADwinPro_All.Inc




#Define module 15 'number given to the card 1-15, we use it as 15 always
#Define sample_lenght (8*10*4) 'should be divisible by 8 if one channel is read only, or divisible by 4 if more are read
#Define buffer_lenght (8*10*4)
#Define period 100 'time scale in which one event can be triggered in us. 100 would be used in a pulse train of 100us length



Dim Data_1[buffer_lenght], Data_2[buffer_lenght], Data_3[buffer_lenght], Data_4[buffer_lenght] As Long
Dim pattern As Long 'shows 
Dim segment As Long 'segment that is currently written
Dim rest As Long
Dim data_number_to_be_written As Long 'number of Data array that will be written
Dim flag_sample_loss As Long
Dim flag_Data_1 As Long
Dim flag_Data_2 As Long
Dim flag_Data_3 As Long
Dim flag_Data_4 As Long

LowInit:
  'variables for PC data transfer:
  data_number_to_be_written = 1
  flag_sample_loss = 0
  flag_Data_1 = 0 '0 means the Data_1 has been read by the PC, 1 means Data_1 
  'was written by the ADwin. The PC will set the value back to 0 after transfer.
  'The ADwin will set it to 1 if written.
  flag_Data_2 = 0
  flag_Data_3 = 0
  flag_Data_4 = 0
  
 
  pattern = Shift_Left(1,module-1) 'makes 100000000000000
  
  P2_Burst_Init (module,0001b,0,sample_lenght,25,0b)
  P2_Burst_Reset(pattern)
  
  'im Beispiel Timer gesteuert,  alle 100us,
  'dies bei >Options Process< auf EVENT setzen
  CPU_Event_Config(1,1,0) '50ns delay
  
  Processdelay=1000*period
  
  P2_set_average_filter(module, 0)
  
  Par_8 = 0
  Par_9 = 0
  Par_10 = 0
  Par_11 = 0
  Par_12 = 0
  Par_14 = 0
  
  
Event:
  inc Par_10 'debug
  Par_8 = data_number_to_be_written 'debug
  
  P2_Burst_Start(pattern)
  
  'do-until  ist sehr zeit-verschwenderisch, besser wäre es mit Wechselpuffern zu arbeiten, und nach dem Start den letzen Auszulesen,
  'allerdings würde im Zyklus N  die Werte von N-1 gelesen werden,  wenn das möglich ist, wäre das die effizientere Alternative
 
  Do
    rest = P2_Burst_Status(module)
    P2_Sleep(25*8) 'Sleep for 8/4MHz
  Until (rest=0) 'If (rest=0) Then 'data of burst aquired:

  Rem Alle Messwerte liegen vor:Von jedem Kanal 1000 Messwerte
  Rem (schnell) abholen und in Data_i ablegen
  SelectCase data_number_to_be_written
      
    Case 1 
      If (flag_Data_1=1) Then 'if data was not read by PC
        Inc flag_sample_loss
      EndIf
      P2_Burst_Read_Unpacked1(module,sample_lenght,0,Data_1,1,3)
      flag_Data_1 = 1
      
    Case 2 
      If (flag_Data_2=1) Then
        Inc flag_sample_loss
      EndIf
      P2_Burst_Read_Unpacked1(module,sample_lenght,0,Data_2,1,3)
      flag_Data_2 = 1
      
    Case 3 
      If (flag_Data_3=1) Then
        Inc flag_sample_loss
      EndIf
      P2_Burst_Read_Unpacked1(module,sample_lenght,0,Data_3,1,3)
      flag_Data_3 = 1
      
    Case 4 
      If (flag_Data_4=1) Then
        Inc flag_sample_loss
      EndIf
      P2_Burst_Read_Unpacked1(module,sample_lenght,0,Data_4,1,3)
      flag_Data_4 = 1
  EndSelect 
      
  Inc data_number_to_be_written
  If (data_number_to_be_written=5) Then
    data_number_to_be_written=1
  EndIf
  
  P2_Burst_Reset(pattern)
  
  Par_9 = flag_sample_loss 'debug
  inc Par_11 'debug
 


  
