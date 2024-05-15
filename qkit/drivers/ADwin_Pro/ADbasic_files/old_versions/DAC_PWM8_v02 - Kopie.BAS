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
' Info_Last_Save                 = PC-I3770-4  pc-i3770-4\testuser
'<Header End>
#include adwinpro_all.inc
#include Z:\Heinz\ADbasic Examples\cal.inc

' Par_1 ist die Spannung in DIGITS   während PAR_2  die Substufen darstellt


dim data_1[8][10] as integer

dim ii, i, j, jj as long
dim x, xx as float32


lowinit:
  
  data_1[1][1] = 0
  data_1[1][2] = 0
  data_1[1][3] = 0
  data_1[1][4] = 0
  data_1[1][5] = 0
  data_1[1][6] = 0
  data_1[1][7] = 0
  data_1[1][8] = 0
  
  data_1[2][1] = 1
  data_1[2][2] = 0
  data_1[2][3] = 0
  data_1[2][4] = 0
  data_1[2][5] = 0
  data_1[2][6] = 0
  data_1[2][7] = 0
  data_1[2][8] = 0
  
  data_1[3][1] = 1
  data_1[3][2] = 0
  data_1[3][3] = 0
  data_1[3][4] = 0
  data_1[3][5] = 1
  data_1[3][6] = 0
  data_1[3][7] = 0
  data_1[3][8] = 0
  
  data_1[4][1] = 1
  data_1[4][2] = 0
  data_1[4][3] = 0
  data_1[4][4] = 1
  data_1[4][5] = 0
  data_1[4][6] = 1
  data_1[4][7] = 0
  data_1[4][8] = 0
  
  data_1[5][1] = 1
  data_1[5][2] = 0
  data_1[5][3] = 1
  data_1[5][4] = 0
  data_1[5][5] = 1
  data_1[5][6] = 0
  data_1[5][7] = 1
  data_1[5][8] = 0
 
  data_1[6][1] = 1
  data_1[6][2] = 1
  data_1[6][3] = 0
  data_1[6][4] = 1
  data_1[6][5] = 0
  data_1[6][6] = 1
  data_1[6][7] = 0
  data_1[6][8] = 1
  
  data_1[7][1] = 1
  data_1[7][2] = 1
  data_1[7][3] = 0
  data_1[7][4] = 1
  data_1[7][5] = 1
  data_1[7][6] = 1
  data_1[7][7] = 0
  data_1[7][8] = 1
  
  data_1[8][1] = 1
  data_1[8][2] = 1
  data_1[8][3] = 1
  data_1[8][4] = 1
  data_1[8][5] = 1
  data_1[8][6] = 1
  data_1[8][7] = 0
  data_1[8][8] = 1
 
  
  jj = 1
  
  processdelay = 2000
event:
  
  par_3 = par_1 + data_1[par_2][jj] + 32768
  p2_dac(2, 1, par_3)
  inc jj
  if (jj > 8) then jj = 1
  
