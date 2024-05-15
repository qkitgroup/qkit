'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 3000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 5.0.2
' Optimize                       = Yes
' Optimize_Level                 = 1
' Info_Last_Save                 = TION-LU-DI  TION-LU-DI\TionLuDi
'<Header End>
'
' NanoQt: ADwin acquisition program
'
' On Linux compile with:
'   adbasic -sp -p11 -o2 -g3000 acquisition.bas
'
' Program interface:
'   data_1 (in, fifo):  commands
'   data_2 (out, fifo): measurement data
'   par_1 (out):        version (1 byte/field, ex: 01020ah -> 1.2.10)
'   par_2 (out):        sweep number
'   par_3 (out):        step number
'   par_4 (in):         address of AIN card
'   par_5 (in):         address of AOUT card
'   par_6 (in):         emergency stop
'   par_7 (out):        state
'   par_10 (in):        rlimite
'
' Ouput channels:
'   1 - analog out 1
'   :   :
'   4 - analog out 4
'   5 - analog out 5 = Hx (slope correction applied)
'   6 - analog out 6 = Hy (slope correction applied)
'   7 - analog out 7 = Hz (feedback applied)
'   8 - analog out 8 = lock-in output
'
' Input channels:
'    1 -  analog in 1
'    :    :
'    8 -  analog in 8
'    9 -  transition time (SQUID ramp mode)
'   10 -  transition time (SQUID cold mode)
'   11 -  feddback correction to Hz
' unnumbered inputs (implied by MODE_LOCK_IN):
'   Re LockIn (lock-in mode)
'   Im LockIn (lock-in mode)


#include adwinpro_all.inc

#define VERSION             000800h
#define FIFO_SZ             1000000
#define DAC_ZERO            32768
#define PI                  3.14159265358979
#define TWO_PI              6.28318530717958
#define NB_IN               8
#define NB_OUT              8

' State machine.
#define ST_READING_HEADER   1
#define ST_READING_TARGET   2
#define ST_SWEEPING         3

' Par_* inputs
#define SWEEPNUMBER         par_2
#define STEPNUMBER          par_3
#define AIN_ADDRESS         par_4
#define AOUT_ADDRESS        par_5
#define EMERGENCY_STOP      par_6
#define STATE               par_7

#define cin                 par_17
#define cout                par_18
#define MAX_R               fpar_18



dim data_1[FIFO_SZ] as long as fifo    ' command
dim data_2[FIFO_SZ] as long as fifo    ' data

' inputs
dim in[NB_IN] as long at dm_local
dim dzin as long

' outputs
dim out_init[NB_OUT], out_target[NB_OUT], clac[NB_OUT] as long at dm_local
dim dzout as long

' Sweep.
dim mode, input_mask, output_mask, nb_steps, subsampling as long
dim nb_channels, i, j as long
dim out[NB_OUT] as long at dm_local
dim v[NB_OUT] as float at dm_local
dim phase as float

lowinit:
  par_1 = VERSION
  AIN_ADDRESS = 2
  AOUT_ADDRESS = 3
  EMERGENCY_STOP = 0
  dzin = DAC_ZERO
  dzout = DAC_ZERO
  fifo_clear(1)
  fifo_clear(2)
  for i = 1 to NB_OUT
    out[i] = dzout
    out_init[i] = dzout
    v[i] = 0
    clac[i] = 1
  next i
  STATE = ST_READING_HEADER
  p2_dac8(AOUT_ADDRESS, out_init, 1)
  p2_start_convf(AIN_ADDRESS, 0FFh)   '*** Start conversion on inputs


event:
  ' *** EMERGENCY_STOP ***
  if (EMERGENCY_STOP <> 0) then
    fifo_clear(1)
    fifo_clear(2)
    STATE = ST_READING_HEADER
    for i = 1 to NB_OUT
      out_init[i] = dzout + clac[i]*(-dzout + out[i])
      data_2 = out_init[i]      ' disclose current output values
    next i
    EMERGENCY_STOP = 0
  endif

  ' *** ST_READING_HEADER ***
  if (STATE = ST_READING_HEADER) then ' Read a command header
    if (fifo_full(1) >= 5) then
      nb_channels = 0
      mode = data_1
      input_mask = data_1
      output_mask = data_1
      nb_steps = data_1
      subsampling = data_1
      for i = 1 to NB_OUT
        if ((output_mask and shift_left(1, i-1)) <> 0) then
          inc(nb_channels)
        endif
      next i
      dzin = 2^(cin-1)
      dzout = 2^(cout-1)
      ' Next state
      STATE = ST_READING_TARGET ' prepare read targets state
    endif ' fifo_full(1) >= 5
  endif ' ST_READING_HEADER

  ' *** ST_READING_TARGET ***
  if (STATE = ST_READING_TARGET) then ' Read output targets
    if (fifo_full(1) >= nb_channels) then
      for i = 1 to NB_OUT
        clac[i] = 1
        if ((output_mask and shift_left(1, i-1)) <> 0) then
          out_target[i] = data_1
        else
          out_target[i] = out_init[i]
        endif
      next i
      ' --- Next state ---
      STATE = ST_SWEEPING 'prepare sweep state
      inc SWEEPNUMBER
      STEPNUMBER = 0
    endif ' fifo_full(1) >= nb_channels
  endif ' ST_READING_TARGET

  ' *** ST_SWEEPING ***
  if (STATE = ST_SWEEPING) then
    inc(STEPNUMBER) ' Sweep one step
    phase = STEPNUMBER/nb_steps
    ' --- Output ---
    for i = 1 to NB_OUT
      out[i] = dzout + clac[i] * (-dzout + out_init[i]+phase*(out_target[i]-out_init[i]))
    next i
    p2_dac8(AOUT_ADDRESS, out, 1)

    ' --- Input ---
    if (input_mask <> 0) then
      p2_wait_eocf(AIN_ADDRESS, input_mask and 0FFh)
      p2_read_adcf8(AIN_ADDRESS, in, 1)
      for i = 1 to 8
        if (((out[i] - dzout) / (in[i] - dzin)) > MAX_R) then
          clac[i] = 0
        endif
      next i
        
      if ((STEPNUMBER/subsampling)*subsampling = STEPNUMBER) then   'i.e. par_3 mod subsampling = 0
        for i = 1 to 8
          if ((input_mask and (shift_left(1, i-1)) <> 0)) then
            data_2 = in[i] * 256
          endif
        next i
      endif ' par_3 mod subsampling = 0
    endif ' input_mask <> 0

    ' --- Next state? ---
    if (STEPNUMBER = nb_steps) then
      for i = 1 to NB_OUT
        v[i] = (out_target[i] - out_init[i]) / nb_steps
        out_init[i] = dzout + clac[i]*(-dzout + out_target[i])
      next i
      STATE = ST_READING_HEADER
    endif ' par_3 = nb_steps
  endif ' ST_SWEEPING

  p2_start_convf(AIN_ADDRESS, 0FFh) '*** Start conversion on inputs

  ' vim: set sw=2 ts=2 et:
