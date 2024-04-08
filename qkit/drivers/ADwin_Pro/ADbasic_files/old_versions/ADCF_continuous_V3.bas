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
'Process writes 10kHz ADC input 1 values each event (100Hz) to memory of ADwin. 
'One buffer cycle takes 1 seconds

#Include ADwinPro_All.inc
#Define module 15                                            'module no.
#Define data Data_2                                           'receives values of channel 1
#Define segment Par_7                                       'segment that is currently written
#Define max_val 4*8*3000 '1e5                                'must be devisible by 32 (=4*8) no. of values
#Define seg1 max_val / 8                                    'seg1 MUST BE DIVISIBLE BY 4 ; end of segment 1
#Define seg2 max_val / 8 * 2                                'end of segment 2
#Define seg3 max_val / 8 * 3                                'end of segment 3
#Define blk max_val / 4                                     'read block size

Dim data[max_val] as long                                   'destination array
Dim pattern as long                                         'bit pattern to address one module                                         
Dim mem_idx as long                                         'mem position of last written value

LowInit:
  Processdelay = 20000
  P2_Set_LED(module, 1)
  Rem 1 channel continuous, mem for max_val values, 25 MHz
  pattern = Shift_Left(1, module - 1)                      'address this module only
  P2_Set_Average_Filter(pattern, 4)                        '2**4 averages
  P2_Burst_Init(module, 1, 0, max_val, 1000, 010b)        '100 000ns per sample, 10 kHz
  P2_Burst_Reset(pattern)
  P2_Burst_Start(pattern)
 
  segment = 1                                               'start with memory segment 1
  
  Par_40 = 0
  Par_41 = 0
  Par_42 = 0
  Par_43 = 0

Event:
  Processdelay = 3e6 '1e6
  mem_idx = P2_Burst_Read_Index(module)                     'get current mem index, number of samples is double of it! 
  If (segment = 1) Then                                     'read 1. segment
    If ((mem_idx > seg1) And (mem_idx < seg3)) Then
      Rem memory index is in segments 2 or 3: read segment 1
      P2_Burst_Read_Unpacked1(module, blk, 0, data, 1, 3)
      Inc Par_40
      segment = 2
    EndIf
  EndIf

  If (segment = 2) Then                                     'read 2. segment
    If (mem_idx > seg2) Then
      Rem memory index is in segments 3 or 4: read segment 2
      P2_Burst_Read_Unpacked1(module, blk, seg1, data, blk + 1, 3)
      segment = 3
      Inc Par_41
    EndIf
  EndIf

  If (segment = 3) Then                                     'read 3. segment
    If ((mem_idx > seg3) Or (mem_idx < seg1)) Then
      Rem memory index is in segments 4 or 1: read segment 3
      P2_Burst_Read_Unpacked1(module, blk, seg2, data, blk * 2 + 1, 3)
      segment = 4
      Inc Par_42
    EndIf
  EndIf

  If (segment = 4) Then                                     'read 4. segment
    If (mem_idx < seg2) Then
      Rem memory index is in segments 1 or 2: read segment 4
      P2_Burst_Read_Unpacked1(module, blk, seg3, data, blk * 3 + 1, 3)
      segment = 1
      Inc Par_43
    EndIf
  EndIf
  
   
Finish:
  P2_Set_LED(module, 0)
