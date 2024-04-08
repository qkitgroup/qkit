'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 3000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 5.0.6
' Optimize                       = Yes
' Optimize_Level                 = 1
' Info_Last_Save                 = PULSAR  PULSAR\edgar
'<Header End>
' Tell whether this is a Gold II or a Pro II system.
'
' This can be known by reading the version register of the Gold II,
' which should be zero on a Pro II. Run this right after boot to
' ensure par_1 is initialized to zero. Returns result in par_1 as:
'
'   0: the program did not start yet, retry later
'   1: Gold II
'   2: Pro II

init:
  if (peek(0c000240h) <> 0) then
    par_1 = 1  ' Gold II
  else
    par_1 = 2  ' Pro II
  endif
