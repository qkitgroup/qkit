'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 1000
' Eventsource                    = Timer
' Control_long_Delays_for_Stop   = No
' Priority                       = High
' Version                        = 1
' ADbasic_Version                = 6.4.0
' Optimize                       = Yes
' Optimize_Level                 = 1
' Stacksize                      = 1000
' Info_Last_Save                 = DESKTOP-0M2IFQQ  DESKTOP-0M2IFQQ\kaptn
'<Header End>
' Lockin for spin-transistor measurements by Luca
' Idea: controls lockin sin output + adc input + lockin cal + filtering + (subsampling)
' ADwin lockin driver written by Luca Kosche in April 2024
' The lockin process is seperate from the sweep process to optimize for fast lockin out/input.
' The lockin signal is calculated in the init and saved to an array to minimize calculation times
' during the event loop. With current length of the lockin array, only frequencies > 10Hz are possible.
' This can easily be changed by increasing "lockin_len".
' Output and input cards and lockin channels are hard coded because this saves calculation time in event.
' The lockin signal is always added to the bias value set by the sweep process. Only when the lockin is inctive,
' the sweep process can write a value to the lockin output channel.
' The lockin measurement data after filtering is send toPC subsampled to the lockin frequency.

'SPECIALITIES ABOUT T11 AND 18-BIT INPUT CARD:
'With T11 processor, it is crucial to optimize every command to archive the processdelay of 600, 
'which which is the maximum sample rate of the 18-bit input card (500kHz | 2us)
'only the 18-bit card can work in timer mode enabled by "P2_ADCF_Mode(2, 1)". Thereby the card is 
' automatically triggered to give a new measurement at the beginning of each event cycle.

'WHAT COULD MAYBE BE DONE WITH THIS HARDWARE?
'two output samples for each input??
'More subsampling?

'WHAT COULD BE DONE WITH T12, 16-BIT INPUT CARD, FIFO OUTPUT CARD?
'Faster lockin cycle enabling higher lockin frequencies
'moving average in the 16-bit card.
'with output card with fifo, the lockin output could be handled by the fifo.

#Include ADwinPro2.Inc

'hard coded settings
#define input_card        2                                                                     
#define input_channel     2
#define lockin_card       3
#define lockin_channel    8         'this cannot simply changed here, but also needs to implemented for adding lockin to channel
#define process_delay     600
#define cycle_time        1/300E6
#define DAC_ZERO          32768
#define DAC_ZERO_18       131072
#define DAC_RANGE         65536    
#define PI                3.1415927
#define fifo_len          1000003
#define lockin_len        25003     '25E3 gives a minimum lockin frequency of 20Hz @ 2us cycle time.

'communication PC ADwin
#define lockin_bias       Par_8     'lock-in bias voltage (bits)
#define lockin_active     Par_10
#define amplitude         Par_11    'lock-in amplitude (bits)
#define frequency         FPar_2    'lock_in frequency (Hz)
#define report_frequency  FPar_4
#define fifo_dc_readout   Data_1

'ADwin only
#define lockin_sin        Data_10
#define lockin_cos        Data_11

'program variables
dim lockin_sin[lockin_len], lockin_cos[lockin_len] as long at dm_local  'arrays holding the lockin sin/cos values.
dim nb_lockin_cycles, lockin_cycle, lockin_in as long

dim fifo_dc_readout[fifo_len] as long as fifo   'send data to PC

'only during init for creating lockin sin/cos arrays
dim process_time, theoretical_steps, phase as float
dim i as long

sub create_sin_cos_references()
  'Preperations
  process_time = process_delay * cycle_time                   'find closest applicable frequency with respect to the cycle time
  theoretical_steps = 1 / (frequency * process_time)          'calculate the theoretical number of nb_lockin_cycles
  nb_lockin_cycles = Round(theoretical_steps)                 'round nb_lockin_cycles to the closest even number -> this leads to a slightly different frequency
  if (nb_lockin_cycles and 1b = 1) then Inc nb_lockin_cycles  'add 1 if nb_lockin_cycles is not even
  report_frequency = 1 / (nb_lockin_cycles * process_time)    'report actual frequency  
  'create lockin reference arrays
  for i = 1 to lockin_len
    if (i <= nb_lockin_cycles) then
      phase = (i / nb_lockin_cycles) * 2 * PI - PI                                                                      '???? works without casting float explicitl?
      lockin_sin[i] = Round((sin(phase) * amplitude))
      lockin_cos[i] = Round((cos(phase) * amplitude))
    else
      lockin_sin[i] = 0
      lockin_cos[i] = 0
    endif
  next i
endsub
init:
  Processdelay = process_delay
  
  'CLEAR TRANSMITTION FIFOS
  fifo_clear(1)
  
  'CREATE THE ARRAYS HOLDING THE LOCKIN REFERENCE SIGNAL
  create_sin_cos_references()
  
  'INITIALIZE EVENT VARIABLES
  lockin_cycle = 1
  lockin_active = 1
  
  'ACTIVTATE TIMER MODE FOR 18-BIT INPUT CARD (MUST BE AT THE END OF INIT)
  P2_ADCF_Mode(2, 1)
 
event:
  if (lockin_active = 1) then
    'READ LOCK-IN INPUT (80 CYCLES)
    lockin_in = P2_Read_ADCF24(input_card, input_channel)   'read input with 18-bit resolution  ????? Check if nanoqt really handles 18-bit data correctly
    fifo_dc_readout = Shift_Right(lockin_in, 6)
    
    'WRITE LOCKIN OUTPUT (ASAP AFTER READING INPUT)
    P2_DAC(lockin_card, lockin_channel, lockin_bias + lockin_sin[lockin_cycle])
  

    'TRANSMIT DATA + HANDLE LOCKIN CYCLES
    if (lockin_cycle = nb_lockin_cycles) then
      lockin_cycle = 1
    else
      Inc lockin_cycle
    endif
  endif
  
finish:
  P2_DAC(lockin_card, lockin_channel, lockin_bias)
  lockin_active = 0
