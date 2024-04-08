'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 3000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.3.0
' Optimize                       = Yes
' Optimize_Level                 = 2
' Stacksize                      = 1000
' Info_Last_Save                 = PHI-LBERT  PHI-LBERT\phi-lbert
'<Header End>
'
' NanoQt: ADwin acquisition program
'
' On Linux compile with:
'   adbasic /M acquisition.bas /Aacquisition-gold2 /SGII /P11 /O2
'   adbasic /M acquisition.bas /Aacquisition-pro2 /SPII /P11 /O2
'
' Program interface:
'   data_1 (in, fifo):  commands
'   data_2 (out, fifo): measurement data
'   data_3 (out):       outputs
'   par_1 (out):        version (1 byte/field, ex: 01020ah -> 1.2.10)
'   par_2 (out):        sweep number
'   par_3 (out):        step number
'   par_4 (in):         address of AIN card
'   par_5 (in):         address of AOUT card
'   par_6 (in):         emergency stop
'   par_7 (out):        state
'   par_31 (in):        manual Hz correction
'   par_32 (out):       electromigration: done
'   par_33 (in):        electromigration: starting voltage
'   par_38 (in):        electromigration (slow): input channel
'   par_39 (in):        electromigration (slow): output channel
'   par_8 (in):         palier        microSQUID
'   par_9 (in):         pente         microSQUID
'   par_10 (in):        seuil         microSQUID
'   par_11 (in):        gain          microSQUID
'   fpar_12 (in):       proportional  microSQUID
'   par_13 (in):        setpoint      microSQUID
'   fpar_14 (in):       offset        microSQUID
'   fpar_15 (in):       ax            microSQUID
'   fpar_16 (in):       ay            microSQUID
'   par_17 (in):        regime        microSQUID
'   fpar_1 (in):        lock-in frequency
'   fpar_2 (in):        lock-in amplitude
'   fpar_3 (in):        lock-in kappa: 1-exp(-process_delay/timeconstant)
'   fpar_4 (in):        electromigration: conductance threshold
'   fpar_5 (in):        electromigration (slow): filter constant
'   fpar_6 (in):        electromigration (slow): maximum d(log(R))
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


#define VERSION             000509h
#define FIFO_SZ             1000000
#define DAC_ZERO            32768
#define PI                  3.1415927
#define TWO_PI              6.2831853
#define NB_IN               8
#define NB_OUT              8

' ADwin types.
' Keep in sync with adwincontrol.h:enum ADwin::ad_type
#define ADWIN_TYPE_UNKNOWN  0
#define ADWIN_TYPE_GOLD2    1
#define ADWIN_TYPE_PRO2     2
#define ADWIN_TYPE_VIRTUAL  3

' State machine.
#define ST_READING_HEADER   1
#define ST_READING_TARGET   2
#define ST_SWEEPING         3
#define ST_WAITING_TRIGGER  4

' Mode bits.
#define MODE_MEDIAN         0001h
#define MODE_LOW_PASS       0002h
#define MODE_QUADRATIC      0004h
#define MODE_RESET_FILTER   0008h
#define MODE_LOCK_IN        0010h
#define MODE_WAIT_TRIGGER   0020h
#define MODE_ELECTROMIG     0040h
#define MODE_SQUID          0080h
#define REGIME_ACTIF        0100h
#define REGIME_COLD         0200h
#define REGIME_PERIODIC     0400h
#define REGIME_APERIODIC    0800h
#define MODE_PLAN           1000h
#define MODE_FEEDBACK       2000h
#define MODE_RESET_FEEDBACK 4000h
#define MODE_COLD           8000h
#define MODE_NANOSQUID     10000h
#define MODE_EMS           20000h
#define RF_TRIGGER         40000h

' #define TICO_INACTIF        0
' #define TICO_COLD           1
' #define TICO_PERIODIC       2
' #define TICO_APERIODIC      3

' Par_* inputs
#define SWEEPNUMBER         par_2
#define STEPNUMBER          par_3
#define AIN_ADDRESS         par_4
#define AOUT_ADDRESS        par_5
#define EMERGENCY_STOP      par_6
#define STATE               par_7
#define SQUID_PALIER        par_8
#define SQUID_PENTE         par_9
#define SQUID_SEUIL         par_10
#define SQUID_GAIN          par_11
#define SQUID_SETPOINT      par_12
#define SQUID_F_MIN         par_13
#define SQUID_F_MAX         par_14
#define SQUID_REJECT_MIN    par_15
#define SQUID_REJECT_MAX    par_16
#define SQUID_REGIME        par_17
#define ADWIN_TYPE          par_18
#define coldtc              par_19
#define tc                  par_20
#define SQUID_BEGINPALIER   par_21
#define SQUID_TIMEPALIER    par_22
#define SQUID_TIMEOUT       par_23
#define SQUID_VOFFSET       par_24
#define PAUSE               par_30
#define MANUAL_DELTA_HZ     par_31
#define ELECTROMIG_DONE     par_32
#define ELECTROMIG_V_START  par_33
#define MODE                par_35
#define LOCK_IN_INPUT       par_36
#define LOCK_IN_OUTPUT      par_37
#define EMS_INPUT           par_38
#define EMS_OUTPUT          par_39

#define rf_trig             par_48

' FPar_* inputs
#define LOCK_IN_FREQUENCY   fpar_1
#define LOCK_IN_AMPLITUDE   fpar_2
#define LOCK_IN_KAPPA       fpar_3
#define ELECTROMIG_G_MIN    fpar_4
#define EMS_FILTER_CST      fpar_5
#define EMS_DR_MAX          fpar_6
#define SQUID_PROP          fpar_12
#define SQUID_OFFSET        fpar_14
#define SQUID_AX            fpar_15
#define SQUID_AY            fpar_16
#define Zplan               fpar_17
#define Zcorr               fpar_18


' Data_3 output
#define out                 data_3


dim data_1[FIFO_SZ] as long as fifo    ' command
dim data_2[FIFO_SZ] as long as fifo    ' data

' filter
dim data_10[8], data_11[8], data_12[8], data_13[8] as long at dm_local
dim data_17[8] as float at dm_local
dim b10, b11, a11, a12, b2, a21, a22, w10, w20 as float at dm_local
dim w11[8], w12[8], w21[8], w22[8] as float at dm_local
dim filter_inited as long

' outputs
dim out_init[NB_OUT], out_target[NB_OUT] as long at dm_local

' Sweep.
dim nb_steps, subsampling as long
dim input_mask, lock_in_mask, output_mask as long
dim trigger as long
dim nb_channels, i, j as long
dim out[NB_OUT] as long at dm_local
dim v[NB_OUT] as float at dm_local
dim phase as float

' Lock-in
dim lock_in_phase, lock_in_old_phase as float
dim c0, s0, c1, c2, c3, c4, s1, s2, s3, s4 as float

' Feedback
dim min_nb, min_reject, max_nb, max_reject as long
'dim den as float

' Cold
dim oldtc as long

' TiCo SQUID
dim tdrv[150] as long
dim NSQUIDpalier, NSQUIDpente, NSQUIDseuil, NSQUIDgain, NSQUIDregime as long
dim NSQUIDbeginpalier, NSQUIDtimepalier, NSQUIDtimeout as long

' Electromigration, normal (fast) mode.
dim G_sample as float

' Electromigration, slow mode.
dim ems_I, ems_filter_inited as long
dim ems_R, ems_x, ems_w, ems_w1, ems_dr as float

' Compute time-weighted relative resistance variation (ems_dr)
' by running a first order high pass on log(R)
sub ems_filter()
  ems_I = data_17[EMS_INPUT] - DAC_ZERO
  if (ems_I = 0) then
    ems_I = 1
  endif
  ems_R = absf((out[EMS_OUTPUT] - DAC_ZERO) / ems_I)
  ems_x = log(ems_R)
  if (ems_filter_inited = 0) then
    ' Make the filter believe it has always measured the current value
    ems_w1 = ems_x * EMS_FILTER_CST / (1 - EMS_FILTER_CST)
    ems_dr = 0
    ems_filter_inited = 1
  else
    ems_w = EMS_FILTER_CST * (ems_x + ems_w1)
    ems_dr = ems_w - ems_w1
    ems_w1 = ems_w
  endif
endsub

' Apply filters as needed
' input: data_10[1..8]
' output: data_17[1..8]
sub filter()

  if (filter_inited = 0) then
    b2 = 2 * subsampling / PI
    b11 = cos(2 * PI / subsampling)
    a21 = 2 * (1 - b2 * b2)
    a12 = 1 - b2 * (0.765367 - b2)
    b10 = 1 / (4 - a21 - a12)
    a11 = a21 * b10
    a12 = a12 * b10
    b10 = b10 * 2 / (1 - b11)
    b11 = -2 * b10 * b11
    a22 = 1 - b2 * (1.847759 - b2)
    b2 = 1 / (4 - a21 - a22)
    a21 = b2 * a21
    a22 = b2 * a22
    w10 = 1  / (1 + a11 + a12)  ' actually: steady state factor w10/x
    w20 = (2 * b10 + b11) / (1 + a21 + a22)  ' steady state w20/w10
    for i = 1 to 8
      if ((input_mask and (shift_left(1, i-1)) <> 0)) then
        data_11[i] = data_10[i]
        data_12[i] = data_10[i]
        data_13[i] = data_10[i]
        data_17[i] = data_10[i]
        w11[i] = w10 * data_10[i]
        w12[i] = w11[i]
        w21[i] = w20 * w11[i]
        w22[i] = w21[i]
      endif
    next i
    filter_inited = 1
  endif

  for i = 1 to NB_IN
    if ((input_mask and (shift_left(1, i-1)) <> 0)) then
      ' Median filter
      if ((mode and MODE_MEDIAN) <> 0) then
        if (data_10[i] < data_11[i]) then
          if (data_12[i] < data_10[i]) then
            data_13[i] = data_10[i]
          else
            if (data_12[i] < data_11[i]) then
              data_13[i] = data_12[i]
            else
              data_13[i] = data_11[i]
            endif
          endif
        else ' data_10[i] > data_11[i]
          if (data_12[i] < data_11[i]) then
            data_13[i] = data_11[i]
          else
            if (data_12[i] < data_10[i]) then
              data_13[i] = data_12[i]
            else
              data_13[i] = data_10[i]
            endif
          endif
        endif
        data_12[i] = data_11[i]
        data_11[i] = data_10[i]
      else ' !MODE_MEDIAN
        data_13[i] = data_10[i]
      endif ' MODE_MEDIAN

      ' Linear low-pass filter
      if ((mode and MODE_LOW_PASS) <> 0) then
        w10 = data_13[i] - a11 * w11[i] - a12 * w12[i]
        w20 = b10*w10 + b11*w11[i] + b10*w12[i] - a21*w21[i] - a22*w22[i]
        w12[i] = w11[i]
        w11[i] = w10
        data_17[i] = b2 * (w20 + 2 * w21[i] + w22[i])
        w22[i] = w21[i]
        w21[i] = w20
      else
        data_17[i] = data_13[i]
      endif

    endif ' channel i in input_mask
  next i
endsub

' input: data_10[LOCK_IN_INPUT]
' output: (c4, s4)
' Use the phase of the previous output
sub lock_in_filter()
  c0 = (data_10[LOCK_IN_INPUT] - DAC_ZERO) * 2 * cos(lock_in_old_phase)
  s0 = -(data_10[LOCK_IN_INPUT] - DAC_ZERO) * 2 * sin(lock_in_old_phase)
  c1 = c1 + LOCK_IN_KAPPA * (c0-c1)
  s1 = s1 + LOCK_IN_KAPPA * (s0-s1)
  c2 = c2 + LOCK_IN_KAPPA * (c1-c2)
  s2 = s2 + LOCK_IN_KAPPA * (s1-s2)
  c3 = c3 + LOCK_IN_KAPPA * (c2-c3)
  s3 = s3 + LOCK_IN_KAPPA * (s2-s3)
  c4 = c4 + LOCK_IN_KAPPA * (c3-c4)
  s4 = s4 + LOCK_IN_KAPPA * (s3-s4)
endsub

' Code for the nanoSQUID

dim plateau_time, squid_time, squid_waiting as long

sub squid_init()
  squid_time = 0
  squid_waiting = 0
endsub

sub squid_process()

  ' Check transition
  if (data_17[8] > SQUID_SEUIL + SQUID_VOFFSET) then
    coldtc = digin_fifo_read_timer()
    tc = coldtc - plateau_time
    if ((SQUID_REGIME and REGIME_PERIODIC) <> 0) then
      squid_waiting = 1
    else
      squid_time = 0
    endif
  endif

  ' Drive the SQUID current
  if ((squid_time = 0) or (squid_waiting = 1)) then
    out[8] = DAC_ZERO    ' Set SQUID current to zero
  else
    if (squid_time = SQUID_BEGINPALIER) then
      SQUID_VOFFSET = data_17[8]
      out[8] = SQUID_PALIER
      plateau_time = digin_fifo_read_timer()
    else
      if ((((SQUID_REGIME and REGIME_PERIODIC) <> 0) or ((SQUID_REGIME and REGIME_APERIODIC) <> 0)) and (squid_time > SQUID_TIMEPALIER)) then
        out[8] = SQUID_PALIER + (squid_time - SQUID_TIMEPALIER) * SQUID_PENTE
      endif
    endif
  endif

  ' Increment time
  inc squid_time
  if (squid_time = SQUID_TIMEOUT) then
    squid_time = 0
    squid_waiting = 0
  endif

endsub

' Hardware access is system dependent.
' The wrapper routines below are defined for both ADwin Gold II
' and ADwin Pro II.
' WARNING: parentheses are needed when using formal parameters,
' just like with a #define in C.

#if ADwin_SYSTEM = ADWIN_GOLDII THEN

#include ADwinGoldII.inc

function tico_get_par(par_no) as long
  tico_get_par = get_par(1, (par_no))
endfunction

sub tico_set_par(par_no, value):
  set_par(1, (par_no), (value))
endsub

function read_trigger() as long
  read_trigger = (digin_edge(0) and 8000h)
endfunction

sub dac_output(values[])
  dim i as long
  for i = 1 to 8
    write_dac(i, values[i])
  next i
  start_dac()
endsub

sub adc_set_mux(input_mask)
  dim mux_pattern as long
  if (((input_mask) and 05555h) <> 0) then
    mux_pattern =                shift_right((input_mask) and 04h, 2)
    mux_pattern = mux_pattern or shift_right((input_mask) and 10h, 3)
    mux_pattern = mux_pattern or (shift_right((input_mask) and 40h, 6) * 3)
    set_mux1(mux_pattern)
  endif
  if (((input_mask) and 0aaaah) <> 0) then
    mux_pattern =                shift_right((input_mask) and 08h, 3)
    mux_pattern = mux_pattern or shift_right((input_mask) and 20h, 4)
    mux_pattern = mux_pattern or (shift_right((input_mask) and 80h, 7) * 3)
    set_mux2(mux_pattern)
  endif
endsub

sub adc_start_conv()
  start_conv(11b)
endsub

sub adc_wait_eoc(input_mask)
  wait_eoc(11b)
endsub

sub adc_read(input_mask, result[])
  dim i as long
  for i = 1 to 8
    if (((input_mask) and (shift_left(1, i-1)) <> 0)) then
      if ((i/2)*2 = i) then
        result[i] = read_adc(2)
      else
        result[i] = read_adc(1)
      endif
    endif
  next i
endsub

#else  ' assume ADWIN_PROII

#include ADwinpro_all.inc

sub tico_start()
  p2_tico_start(1)  ' was p2_tico_start(0)
endsub

sub tdrv_init(tico_no, tdrv_datatable[])
  p2_tdrv_init(1, tico_no, tdrv_datatable)
endsub

sub tico_start_process(tdrv_datatable[], process_no)
  p2_tico_start_process(tdrv_datatable, process_no)
endsub

function tico_get_par(par_no) as long
  tico_get_par = p2_get_par(1, 1, (par_no))
endfunction

sub tico_set_par(par_no, value):
  p2_set_par(1, 1, (par_no), (value))
endsub

function read_trigger() as long
  read_trigger = cpu_digin(0)  ' falling edge at DIG I/O 0
endfunction

function digin_fifo_read_timer() as long
  digin_fifo_read_timer = p2_digin_fifo_read_timer(1)
endfunction

sub dac_output(values[])
  p2_dac8(AOUT_ADDRESS, values, 1)
endsub

sub adc_set_mux(input_mask)
  ' No multiplexers: do nothing
endsub

sub adc_start_conv()
  p2_start_convf(AIN_ADDRESS, 0FFh)
endsub

sub adc_wait_eoc(input_mask)
  p2_wait_eocf(AIN_ADDRESS, (input_mask) and 0FFh)
endsub

sub adc_read(input_mask, result[])
  p2_read_adcf8(AIN_ADDRESS, result, 1)
endsub

#endif


lowinit:
  par_1 = VERSION
#if ADwin_SYSTEM = ADWIN_GOLDII THEN
  ADWIN_TYPE = ADWIN_TYPE_GOLD2
#else
  ADWIN_TYPE = ADWIN_TYPE_PRO2
#endif
  AIN_ADDRESS = 2
  AOUT_ADDRESS = 3

  ' Since the TiCo is now started by the bootloader, we do not need to
  ' call tico_start() or tico_start_process() anymore. We still need to
  ' initialize the communication with tdrv_init().
  tdrv_init(1, tdrv)

  EMERGENCY_STOP = 0
  fifo_clear(1)
  fifo_clear(2)
  for i = 1 to NB_OUT
    out[i] = DAC_ZERO
    out_init[i] = DAC_ZERO
    v[i] = 0
  next i
  SQUID_PALIER = 0
  SQUID_PENTE = 0
  SQUID_SEUIL = 120
  SQUID_GAIN = 1
  SQUID_PROP = 0
  SQUID_OFFSET = 0
  SQUID_AX = 0
  SQUID_AY = 0
  SQUID_SETPOINT = 0
  STATE = ST_READING_HEADER
  SQUID_F_MIN = 5000
  SQUID_F_MAX = 35000
  SQUID_REJECT_MIN = 3
  SQUID_REJECT_MAX = 3
  SQUID_REGIME = 0
  SQUID_BEGINPALIER = 5
  SQUID_TIMEPALIER = 10
  SQUID_TIMEOUT = 80
  SQUID_VOFFSET = 0
  
  NSQUIDpalier = 0
  NSQUIDpente = 0
  NSQUIDseuil = 0
  NSQUIDgain = 0
  NSQUIDregime = 0
  NSQUIDbeginpalier = 0
  NSQUIDtimepalier = 0
  NSQUIDtimeout = 0
  
  c1 = 0: s1 = 0
  c2 = 0: s2 = 0
  c3 = 0: s3 = 0
  c4 = 0: s4 = 0
  lock_in_phase = -PI/2
  lock_in_old_phase = lock_in_phase
  LOCK_IN_INPUT = 8
  LOCK_IN_OUTPUT = 8
  PAUSE = 0
  tc = 0
  coldtc = 0
  Zplan = 0
  Zcorr = 0
  min_nb = 0
  max_nb = 0
  MANUAL_DELTA_HZ = 0
  ELECTROMIG_DONE = 0
  filter_inited = 0
  ems_filter_inited = 0
  dac_output(out_init)
  adc_start_conv()
  
  rf_trig = 0

event:
  rf_trig = tico_get_par(22)
  ' *** EMERGENCY_STOP ***
  if (EMERGENCY_STOP <> 0) then
    ZCorr = 0
    tc = 0
    mode = 0
    fifo_clear(1)
    STATE = ST_READING_HEADER
    for i = 1 to NB_OUT
      out_init[i] = out[i]
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

      ' Next state
      STATE = ST_READING_TARGET ' prepare read targets state

    endif ' fifo_full(1) >= 5
  endif ' ST_READING_HEADER

  ' *** ST_READING_TARGET ***
  if (STATE = ST_READING_TARGET) then ' Read output targets
    if (fifo_full(1) >= nb_channels) then
      for i = 1 to NB_OUT
        if ((output_mask and shift_left(1, i-1)) <> 0) then
          out_target[i] = data_1
        else
          out_target[i] = out_init[i]
        endif
      next i

      ' --- Next state ---
      inc SWEEPNUMBER
      STEPNUMBER = 0

      if ((mode and MODE_LOCK_IN) <> 0) then
        lock_in_mask = shift_left(1, LOCK_IN_INPUT-1)
      else
        lock_in_mask = 0
      endif
      adc_set_mux(input_mask or lock_in_mask)

      if ((mode and MODE_RESET_FILTER) <> 0) then
        filter_inited = 0
      endif

      if ((mode and MODE_EMS) <> 0) then
        ems_filter_inited = 0
      endif

      if ((mode and MODE_WAIT_TRIGGER) <> 0) then
        trigger = read_trigger()   ' reset trigger
        STATE = ST_WAITING_TRIGGER ' wait for trigger on DIG I/O 0
      else
        STATE = ST_SWEEPING 'prepare sweep state
      endif
      
      if ((mode and REGIME_ACTIF) <> 0) then  
        if ((mode and REGIME_COLD) <> 0) then
          tico_set_par(20, REGIME_COLD)
        else
          if ((mode and REGIME_PERIODIC) <> 0) then
            tico_set_par(20, REGIME_PERIODIC)
          else
            if ((mode and REGIME_APERIODIC) <> 0) then
              tico_set_par(20, REGIME_APERIODIC)
            else
              tico_set_par(20, 0)
            endif
          endif
        endif 
      else
        tico_set_par(20, 0)
      endif
      
      if ((mode and MODE_COLD) <> 0) then
        oldtc = digin_fifo_read_timer()
        ' If previous transition was detected more than 20 s ago, it is
        ' in the future mod(2^32). This resets the previous transition
        ' to now. For an unknown reason, this was at some point
        ' commented out.
        tico_set_par(13, oldtc)
      endif
      
      if ((mode and MODE_RESET_FEEDBACK) <> 0) then
        Zcorr = 0
        tc = 0
      endif

      if ((mode and MODE_NANOSQUID) <> 0) then
        squid_init()
      endif

    endif ' fifo_full(1) >= nb_channels
  endif ' ST_READING_TARGET

  ' *** ST_SWEEPING ***
  if (STATE = ST_SWEEPING) then
    if (PAUSE = 0) then
      inc(STEPNUMBER) ' Sweep one step
    endif
    phase = STEPNUMBER/nb_steps

    ' --- Prepare outputs ---
    for i = 1 to NB_OUT
      if ((mode and MODE_QUADRATIC) <> 0) then
        out[i] = out_init[i]+phase*((1-phase)*v[i]*nb_steps+phase*(out_target[i]-out_init[i]))
      else
        out[i] = out_init[i]+phase*(out_target[i]-out_init[i])
      endif
    next i

    ' Manual Hz correction
    out[7] = out[7] + MANUAL_DELTA_HZ
    
    ' Limit 5, 6 and 7 to [-5 V, +5V]
    if ((mode and MODE_SQUID) <> 0) then
      for j = 5 to 7 
        if (out[j] > 49151) then out[j] = 49151
        if (out[j] < 16383) then out[j] = 16383
      next j
    endif
    
    if ((mode and MODE_NANOSQUID) <> 0) then
      squid_process()
    endif

    ' Calculate feedback correction
    
    'if (((SQUID_REGIME and REGIME_PERIODIC) <> 0) or ((SQUID_REGIME and REGIME_APERIODIC) <> 0)) then
    if (((MODE and REGIME_PERIODIC) <> 0) or ((MODE and REGIME_APERIODIC) <> 0)) then
      if ((MODE and MODE_NANOSQUID) = 0) then
        tc = tico_get_par(12)
      endif
      if ((MODE and MODE_FEEDBACK) <> 0) then
        if (tc < SQUID_F_MIN) then
          inc min_nb
          if (min_nb > SQUID_REJECT_MIN) then
            tc = SQUID_F_MIN
          else
            tc = SQUID_SETPOINT
          endif
        else
          min_nb = 0
        endif
        if (tc > SQUID_F_MAX) then
          inc max_nb
          if (max_nb > SQUID_REJECT_MAX) then
            tc = SQUID_F_MAX
          else
            tc = SQUID_SETPOINT
          endif
        else
          max_nb = 0
        endif
        Zcorr = Zcorr + SQUID_PROP*(tc - SQUID_SETPOINT)
      else
        Zcorr = 0
      endif
    endif
        
    ' plan correction
    if ((mode and MODE_PLAN) <> 0) then
      Zplan = DAC_ZERO + SQUID_OFFSET * DAC_ZERO + SQUID_AX*(out[5] - DAC_ZERO) + SQUID_AY*(out[6] - DAC_ZERO)
    else
      Zplan = DAC_ZERO
    endif
    
    ' Limit Hz to [-5 V, +5V]
    if (((mode and MODE_PLAN) <> 0) or ((mode and MODE_FEEDBACK) <> 0))then
      out[7] = Zplan + Zcorr
      ' Limit Hz to [-5 V, +5V]
'       if (out[7] > 49151) then out[7] = 49151
'       if (out[7] < 16383) then out[7] = 16383
    endif
  
    ' Add lock-in signal
    if ((mode and MODE_LOCK_IN) <> 0) then
      lock_in_old_phase = lock_in_phase
      lock_in_phase = lock_in_phase + LOCK_IN_FREQUENCY
      if (lock_in_phase > TWO_PI) then
        lock_in_phase = lock_in_phase - TWO_PI
      endif
      out[LOCK_IN_OUTPUT] = out[LOCK_IN_OUTPUT] + LOCK_IN_AMPLITUDE * cos(lock_in_phase)
    endif

    ' Electromigration finished? Normal mode.
    if ((mode and MODE_ELECTROMIG) <> 0) then
      if (out[8] > ELECTROMIG_V_START) then
        G_sample = (data_17[8] - DAC_ZERO) / (out[8] - DAC_ZERO)
        if (absf(G_sample) < ELECTROMIG_G_MIN) then
          for i = 1 to 8
            out[i] = DAC_ZERO
          next i
          ELECTROMIG_DONE = 1
          EMERGENCY_STOP = 1
        endif
      endif
    endif

    ' Electromigration finished? Slow mode.
    if ((mode and MODE_EMS) <> 0) then
      if (out[8] > ELECTROMIG_V_START) then
        ems_filter()
        if (ems_dr >= EMS_DR_MAX) then
          for i = 1 to 8
            out[i] = DAC_ZERO
          next i
          ELECTROMIG_DONE = 1
          EMERGENCY_STOP = 1
        endif
      endif
    endif
    
    ' RF - trigger
    if ((MODE and RF_TRIGGER) <> 0) then
      rf_trig = tico_get_par(22)
      if (rf_trig <> 0) then
        out [4] = 40960
        tico_set_par(22, 0)
      endif
    endif
    ' Actual output
    dac_output(out)

    ' --- Input ---
    if ((input_mask or lock_in_mask) <> 0) then
      adc_wait_eoc(input_mask or lock_in_mask)
      adc_read(input_mask or lock_in_mask, data_10)
      
      if (input_mask <> 0) then
        filter()
      endif
      
      if ((mode and MODE_LOCK_IN) <> 0) then
        lock_in_filter()
      endif
      
      if (((STEPNUMBER/subsampling)*subsampling = STEPNUMBER) and (PAUSE = 0)) then   'i.e. par_3 mod subsampling = 0
        for i = 1 to 8
          if ((input_mask and (shift_left(1, i-1)) <> 0)) then
            data_2 = data_17[i] * 256 ' transmit filtered data
          endif
        next i
        
        if (input_mask and (shift_left(1,  9-1)) <> 0) then
          data_2 = tc
        endif
        
        if (input_mask and (shift_left(1, 10-1)) <> 0) then
          coldtc = tico_get_par(13) - oldtc
          if (coldtc < 0) then
            coldtc = 0
          endif
          data_2 = coldtc
        endif
        
        if (input_mask and (shift_left(1, 11-1)) <> 0) then
          data_2 = (Zcorr + 32768) * 256
        endif
        
        if ((mode and MODE_LOCK_IN) <> 0) then
          data_2 = (DAC_ZERO + c4) * 256
          data_2 = (DAC_ZERO + s4) * 256
        endif
      endif ' par_3 mod subsampling = 0
    endif ' input_mask <> 0

    ' --- Next state? ---
    if (STEPNUMBER = nb_steps) then
      for i = 1 to NB_OUT
        if ((mode and MODE_QUADRATIC) <> 0) then
          v[i] = 2 * (out_target[i] - out_init[i]) / nb_steps - v[i]
        else
          v[i] = (out_target[i] - out_init[i]) / nb_steps
        endif
        out_init[i] = out_target[i]
      next i
      STATE = ST_READING_HEADER
    endif ' par_3 = nb_steps
  endif ' ST_SWEEPING

  ' *** ST_WAITING_TRIGGER ***
  if (STATE = ST_WAITING_TRIGGER) then
    trigger = read_trigger()
    if (trigger <> 0) then
      STATE = ST_SWEEPING
    endif
  endif

  ' --- Send config of micro-SQUID ---
  if (NSQUIDpalier <> SQUID_PALIER) then
    tico_set_par(1, SQUID_PALIER)
    NSQUIDpalier = SQUID_PALIER
  endif
  if (NSQUIDpente <> SQUID_PENTE) then
    tico_set_par(2, SQUID_PENTE)
    NSQUIDpente = SQUID_PENTE
  endif
  if (NSQUIDseuil <> SQUID_SEUIL) then
    tico_set_par(3, SQUID_SEUIL)
    NSQUIDseuil = SQUID_SEUIL
  endif
  if (NSQUIDgain <> SQUID_GAIN) then
    tico_set_par(4, SQUID_GAIN)
    NSQUIDgain = SQUID_GAIN
  endif
  if (NSQUIDbeginpalier <> SQUID_BEGINPALIER) then
    tico_set_par(6, SQUID_BEGINPALIER)
    NSQUIDbeginpalier = SQUID_BEGINPALIER
  endif
  if (NSQUIDtimepalier <> SQUID_TIMEPALIER) then
    tico_set_par(7, SQUID_TIMEPALIER)
    NSQUIDtimepalier = SQUID_TIMEPALIER
  endif
  if (NSQUIDtimeout <> SQUID_TIMEOUT) then
    tico_set_par(8, SQUID_TIMEOUT)
    NSQUIDtimeout = SQUID_TIMEOUT
  endif
  if ((mode and REGIME_ACTIF) <> 0) then
    if ((NSQUIDregime <> SQUID_REGIME)) then
      NSQUIDregime = SQUID_REGIME
    endif
  else
    if ((NSQUIDregime <> SQUID_REGIME)) then
      tico_set_par(20, SQUID_REGIME)
      NSQUIDregime = SQUID_REGIME
    endif
  endif


  adc_start_conv() '*** Start conversion on inputs

  ' vim: set sw=2 ts=2 et:
