'<TiCoBasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 1000
' Eventsource                    = Timer
' Priority                       = High
' Version                        = 1
' TiCoBasic_Version              = 1.6.2
' Optimize                       = Yes
' Optimize_Level                 = 1
' Info_Last_Save                 = PC-TESTER  NEEL\nanospin
'<Header End>
'
' This program drives the micro-SQUID electronics through the DIO-32
' port of the TiCo processor.
'
' *** Pinout ***
'
' The ADwin Pro II can read back its outputs as if they were inputs.
' The Gold II cannot, then the `rearme' signal is fed back into the
' DIO10 input.
'
'                   ,----------------- rearme feed back on Gold II
'                   |,---------------- !stop
'                   ||,--------------- stop
'                   |||
'                   |||     ,--------- !rearme
'                   |||     | ,------- rearme
'                   |||     | |,------ clk
'                   |||     | ||,----- cmd
'                   |||     | |||,---- dat
'                   |||     | ||||
' DIO: x...x  xxxx xxxx  xxxx xxxx
'     31  16 15       8  7       0
'             --inputs-  -outputs-
'
' *** System states ***
'
' The input word is right shifted by 3, then masked to keep only:
'  - `rearme': bit 7 (80h) on Gold II or bit 0 (01h) on Pro II
'  - `stop':   bit 5 (20h) on both
' These two bits determine the system state:
'
'   stop (20h)
'     ^
'     |  COOL   RESET
'     |
'     |  RAMP   PLATEAU
'     +------------------> rearme (80h or 01h)

#if ADwin_SYSTEM = ADWIN_GOLDII THEN

#include GoldIITiCo.Inc
#define RAMP             000h
#define PLATEAU          080h  ' rearme
#define COOL             020h  ' stop
#define RESET            0a0h  ' rearme or stop
#define STATE_MASK       0a0h  ' rearme or stop
#define FIFO_MASK        500h  ' shift_left(STATE_MASK, 3)

#else  ' assume ADWIN_PROII

#include dio32tico.inc
#define RAMP             000h
#define PLATEAU          001h  ' rearme
#define COOL             020h  ' stop
#define RESET            021h  ' rearme or stop
#define STATE_MASK       021h  ' rearme or stop
#define FIFO_MASK        108h  ' shift_left(STATE_MASK, 3)

#endif

#define REGIME_COLD       0200h
#define REGIME_PERIODIC   0400h
#define REGIME_APERIODIC  0800h

#define SET_PALIERHI      8
#define SET_PALIERLO      9
#define SET_PENTE         10
#define SET_SEUIL         11
#define SET_GAIN          12
#define MEASURE           13
#define READING           14

#define palier            par_1
#define pente             par_2
#define seuil             par_3
#define gain              par_4
#define start             par_5
#define beginplateau      par_6
#define beginramp         par_7
#define period            par_8
#define Npalier           par_9
#define Npente            par_10
#define Nseuil            par_11
#define Ngain             par_14
#define Nregime           par_15

#define tc                par_12
#define coldtc            par_13

#define w_beginplateau    par_17
#define w_beginramp       par_18
#define w_period          par_19
#define REGIME            par_20

#define RACE_SEEN         par_21  ' We have seen a race condition

#define rf_trig           par_22  ' RF Trigger

dim index, dat, mode, counter, pulse, bitindex as long
dim stop, oldstop, num, clock, pattern, oldpattern, oldtimestamp, timestamp, word as long

init:
  processdelay = 200 'x 20ns
  ' 1 cycle <=> 4micros
  
  set_led(1)
#if ADwin_SYSTEM = ADWIN_GOLDII THEN
  conf_dio(0101b)
#else  ' assume ADWIN_PROII
  digprog(0101b)
#endif
  digin_fifo_enable(FIFO_MASK)
  digin_fifo_clear()

  mode = READING
  clock = 0
  pattern = 0
  word = 0

  palier = 5000
  pente = 200
  seuil = 20
  gain = 3
  beginplateau = 5 ' wait after transition
  beginramp = 10 ' after transition, before level.
  period = 75
  
  w_beginplateau = beginplateau
  w_beginramp = beginramp
  w_period = period
  
  Npalier = 0
  Npente = 0
  Nseuil = 0
  Ngain = 0
  Nregime = 0
  RACE_SEEN = 0
  
  rf_trig = 1
  
event:
  digout_long(word)

  if (Nregime <> REGIME) then
    clock = 0
    Nregime = REGIME
    word = 010h
  endif

  if (REGIME > 0) then
        
    if (REGIME = REGIME_COLD) then
      w_beginplateau = 3000
      w_beginramp = -1
      w_period = -1
    else
      w_beginplateau = beginplateau
      w_beginramp = beginramp
      w_period = period      
    endif
    
    inc clock
    if (clock >= w_period) then
      clock = 0
      rf_trig = 1
    endif

    num = digin_fifo_full()
    if (num > 0) then
      for index = 1 to num
        digin_fifo_read(pattern, timestamp)
        pattern = shift_right(pattern, 3)  ' For case can only use 8 bit ints
        pattern = pattern and STATE_MASK
        stop = pattern and COOL
      
        if ((stop = COOL) and (oldstop <> COOL)) then 'stop moves up <=> period or transition
          coldtc = timestamp
          tc = timestamp - oldtimestamp          
          if (REGIME <> REGIME_PERIODIC) then
            clock = 0
          endif
        endif

        oldstop = stop

        if (pattern = RESET) then  ' was if (pattern = RESET)
          oldtimestamp = timestamp
        endif
      next
    endif

    selectcase pattern
      case RAMP
        if (clock = 0) then
          word = 008h ' go to RESET through PLATEAU
        else
          word = 010h
        endif
      case PLATEAU
        if (clock < w_beginplateau) then
          inc RACE_SEEN
        endif
        if (clock = w_beginramp) then
          word = 010h ' go to RAMP
        else
          word = 008h
        endif
      case COOL
        if (clock = w_beginplateau) then
          word = 008h ' go to PLATEAU through RESET
        else
          word = 010h
        endif
      case RESET
        word = 010h ' go to COOL
        if (REGIME = REGIME_COLD) then
          clock = 0
        endif
    endselect

  endif
  
  selectcase mode
    case READING
      mode = READING '********************************************************************************
      bitindex = 255
      if (Npalier <> palier) then
        mode = SET_PALIERHI
        Npalier = palier
      else
        if (Npente <> pente) then
          mode = SET_PENTE
          Npente = pente
        else
          if (Nseuil <> seuil) then
            mode = SET_SEUIL
            Nseuil = seuil
          else
            if (Ngain <> gain) then
              mode = SET_GAIN
              Ngain = gain
            endif
          endif
        endif
      endif
    case SET_PALIERHI, SET_PALIERLO '********************************************************************************
      selectcase bitindex
        case 255
          if (mode = SET_PALIERHI) then
            dat = shift_right(Npalier, 8) 'load high weight bits
          else
            dat = Npalier 'load low weight bits
          endif
          bitindex = 0
          counter = 0
        case 0, 1, 2, 3, 4, 5, 6
          if (counter = 0) then
            word = word or (shift_right(dat, 7 - bitindex) and 1)
            counter = 1
          else
            word = word or 100b
            word = word or (shift_right(dat, 7 - bitindex) and 1)
            inc bitindex
            counter = 0
          endif
        case 7, 8
          if (counter = 0) then
            if (mode = SET_PALIERHI) then
              word = word or (shift_right(10b, 8 - bitindex) and 1)
            else
              word = word or (shift_right(01b, 8 - bitindex) and 1)
            endif
            counter = 1
          else
            word = word or 010b
            if (mode = SET_PALIERHI) then
              word = word or (shift_right(10b, 8 - bitindex) and 1)
            else
              word = word or (shift_right(01b, 8 - bitindex) and 1)
            endif
            inc bitindex
            counter = 0
          endif
        case 9
          if (counter = 0) then
            word = word or 010b
            word = word or (dat and 1)
            counter = 1
          else
            word = word or 110b
            word = word or (dat and 1)
            inc bitindex
            counter = 0
          endif
        case 10, 11
          if (counter = 0) then
            counter = 1
          else
            inc bitindex
            counter = 0
          endif
        case 12
          if (mode = SET_PALIERHI) then
            mode = SET_PALIERLO
          else
            mode = READING
          endif
          bitindex = 255
      endselect
    case SET_PENTE, SET_SEUIL '********************************************************************************
      selectcase bitindex
        case 255
          if (mode = SET_PENTE) then
            dat = Npente 'it seems coded on 16 bits
          else
            dat = shift_left(Nseuil, 3) '3 low bit are needed for an offset
          endif
          bitindex = 0
        case 0, 1, 2, 3
          if (counter = 0) then
            if (mode = SET_PENTE) then
              word = word or (shift_right(0101b, 3 - bitindex) and 1)
            else
              word = word or (shift_right(1001b, 3 - bitindex) and 1)
            endif
            counter = 1
          else
            word = word or 100b
            if (mode = SET_PENTE) then
              word = word or (shift_right(0101b, 3 - bitindex) and 1)
            else
              word = word or (shift_right(1001b, 3 - bitindex) and 1)
            endif
            inc bitindex
            counter = 0
          endif
        case 4, 5
          if (counter = 0) then
            counter = 1
          else
            word = word or 010b
            inc bitindex
            counter = 0
          endif
        case 6
          if (counter = 0) then
            word = word or 010b
            counter = 1
          else
            word = word or 110b
            inc bitindex
            counter = 0
          endif
        case 7, 8
          if (counter = 0) then
            word = word or 001b
            counter = 1
          else
            word = word or 011b
            inc bitindex
            counter = 0
          endif
        case 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24
          if (counter = 0) then
            word = word or 010b
            word = word or (shift_right(dat, 24 - bitindex) and 1)
            counter = 1
          else
            word = word or 110b
            word = word or (shift_right(dat, 24 - bitindex) and 1)
            inc bitindex
            counter = 0
          endif
        case 25, 26, 27, 28
          if (counter = 0) then
            word = word or (shift_right(1101, 28 - bitindex) and 1)
            counter = 1
          else
            word = word or 100b
            word = word or (shift_right(1101, 28 - bitindex) and 1)
            inc bitindex
            counter = 0
          endif
        case 29, 30
          if (counter = 0) then
            counter = 1
          else
            word = word or 010b
            inc bitindex
            counter = 0
          endif
        case 31
          if (counter = 0) then
            word = word or 010b
            counter = 1
          else
            word = word or 110b
            inc bitindex
            counter = 0
          endif
        case 32
          mode = READING
      endselect
    case SET_GAIN '********************************************************************************
      selectcase bitindex
        case 255
          dat = Ngain
          bitindex = 0
        case 0, 1
          if (counter = 0) then
            word = word or 001b
            counter = 1
          else
            word = word or 101b
            inc bitindex
            counter = 0
          endif
        case 2, 3
          if (counter = 0) then
            word = word or (shift_right(dat, 3 - bitindex) and 1)
            counter = 1
          else
            word = word or 100b
            word = word or (shift_right(dat, 3 - bitindex) and 1)
            inc bitindex
            counter = 0
          endif          
        case 4, 5
          if (counter = 0) then
            counter = 1
          else
            word = word or 010b
            inc bitindex
            counter = 0
          endif
        case 6
          if (counter = 0) then
            word = word or 010b
            counter = 1
          else
            word = word or 110b
            inc bitindex
            counter = 0
          endif
        case 7
          mode = READING
      endselect
  endselect
  
finish:
  digout_long(0)
  set_led(0)
