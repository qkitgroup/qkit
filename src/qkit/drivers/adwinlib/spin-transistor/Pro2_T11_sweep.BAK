'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 2
' Initial_Processdelay           = 50000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = Low
' Priority_Low_Level             = 1
' Version                        = 1
' ADbasic_Version                = 6.4.0
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-0M2IFQQ  DESKTOP-0M2IFQQ\kaptn
'<Header End>
'Sweeps for spin transistor measurements written by Luca Kosche in April 2024
'This script is written sweep up to all outputs in the most efficient way on T11 and 16-bit output card.
'If the lockin process is active, the lockin channel is not set by this script, but the bias value is set,
'which is handled by the locking.
'At the end of each sweep the current outputs are saved to the sweep_start array which serve as new starting point
'for the next sweep, if nothing else is given by the PC. Problems can arise after repowering or rebooting the adwin,
'because the sweep_start array might not be filled with the ecpected values.

#Include ADwinPro2.Inc

#define refresh_rate        5000      'sampling frequency of sweep process. (MCU_frequency / sweep_processdelay)
#define MCU_frequency       300E6     'Processor frequency
#define sweep_processdelay  60000      'must be high enough to don't overload ADwin.
#define DAC_ZERO            32768
#define output_card         3
#define nb_outs             8         'number of outputs

#define out1              Par_1
#define out2              Par_2
#define out3              Par_3
#define out4              Par_4
#define out5              Par_5
#define out6              Par_6
#define out7              Par_7
#define out8              Par_8
#define sweep_active      Par_20
#define lockin_active     Par_21
#define measure_active    Par_22
#define duration          FPar_20  'duration of the sweep (s)
#define report_duration   FPar_21
#define target            Data_20   'sweep all outputs to these values (array of 8)

dim start1, start2, start3, start4, start5, start6, start7, start8, cycle, steps as long
dim inc1, inc2, inc3, inc4, inc5, inc6, inc7, inc8 as float
dim target[nb_outs] as long at dm_local 


init:
  processdelay = sweep_processdelay
  steps = Round(duration * refresh_rate)
  report_duration = steps / refresh_rate
  
  ' SET START VALUES OF THE SWEEP
  start1 = out1
  start2 = out2
  start3 = out3
  start4 = out4
  start5 = out5
  start6 = out6
  start7 = out7
  start8 = out8
  
  ' SET INCREMENT VALUES OF THE SWEEP
  inc1 = (target[1] - start1) / steps
  inc2 = (target[2] - start2) / steps
  inc3 = (target[3] - start3) / steps
  inc4 = (target[4] - start4) / steps
  inc5 = (target[5] - start5) / steps
  inc6 = (target[6] - start6) / steps
  inc7 = (target[7] - start7) / steps
  inc8 = (target[8] - start8) / steps
    
  cycle = 0
  sweep_active = 0
  
event:
  if (sweep_active = 0) then
    'Do nothing
  else
    ' SET MEASUREMENT FLAG TO START MEASUREMENT
    measure_active = 1  
  
    ' GO TO THE NEXT CYCLE OR END PROCESS
    if (cycle = steps) then
      measure_active = 0 'set measurement active flag as early as possible to prevent sending extra data to PC
      sweep_active = 0
      end
    else
      Inc cycle
    endif
    
    ' CALCULATE NEW OUTPUTS AND WRITE TO PAR_1 - Par_8
    out1 = start1 + inc1 * cycle
    out2 = start2 + inc2 * cycle
    out3 = start3 + inc3 * cycle
    out4 = start4 + inc4 * cycle
    out5 = start5 + inc5 * cycle
    out6 = start6 + inc6 * cycle
    out7 = start7 + inc7 * cycle
    out8 = start8 + inc8 * cycle
    
    ' SET ALL OUTPUTS EXCEPT LOCKIN CHANNEL (123 cycles)
    ' this is the fastest way i found for T11 and F8/18
    P2_DAC(output_card, 1, out1)
    P2_DAC(output_card, 2, out2)
    P2_DAC(output_card, 3, out3)
    P2_DAC(output_card, 4, out4)
    P2_DAC(output_card, 5, out5)
    P2_DAC(output_card, 6, out6)
    P2_DAC(output_card, 7, out7)
    
    'ONLY SET DAC OUTPUT IF LOCKIN IS INACTIVE
    if (lockin_active = 0) then
      P2_DAC(output_card, 8, out8)
    endif
    
  endif
  
finish:                               

