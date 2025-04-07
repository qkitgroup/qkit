'<ADbasic Header, Headerversion 001.001>
' Process_Number                 = 1
' Initial_Processdelay           = 3000
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
' ADwin lockin driver written by Luca Kosche in April 2024
' Idea:
'   * measure input at input_channel with 18-bit resolution
'   * lockin signal output on lockin_channel 
'   * lockin demodulation by reference signal + low pass filtering
'   * write (subsampled) lockin results and raw input to FIFOs (if measurement flag is set)

' Background of implementation:
'   * Delay between input and output leads to shifts and jitter
'   * -> set output first, then fetch the already measured input
'   * The lockin process is seperate from the sweep process to optimize for fast lockin out/input.
'   * The lockin signal is calculated in the init and saved to an array to minimize calculation times
'   * -> for the phase shifted references the same array is used, but the index is shifted by a quarter period. 
'   * length of the lockin_sig/lockin_ref arrays are limited by local memory and limit the frequency to min 62.5Hz.
'   * -> This can easily be changed by increasing 'lockin_len' and removing 'at dm_local' at the expense of processing time.
'   * Output and input cards and lockin channels are hard coded because this saves calculation time in event.
'   * The lockin signal is always added to the bias value set by the sweep process. Only when the lockin is inctive,
'   * the sweep process can write a value to the lockin output channel.

'SPECIALITIES ABOUT T11 AND 18-BIT INPUT CARD:
'With T11 processor, it is crucial to optimize every command to archive the processdelay of 600, 
'which which is the maximum sample rate of the 18-bit input card (500kHz | 2us)
'only the 18-bit card can work in timer mode enabled by "P2_ADCF_Mode(2, 1)". Thereby the card is 
' automatically triggered to give a new measurement at the beginning of each event cycle.

'WHAT COULD BE DONE WITH T12, 16-BIT INPUT CARD, FIFO OUTPUT CARD?
'Faster lockin cycle enabling higher lockin frequencies
'moving average in the 16-bit card.
'with output card with fifo, the lockin output could be handled by the fifo.

#Include ADwinPro2.Inc

'hard coded settings
#define input_card        2                                                                     
#define input_channel     8
#define lockin_card       3
#define lockin_channel    8         'this cannot simply changed here, but also needs to implemented fo2 adding lockin to channel
#define process_delay     600       'process time needs to be updated as well!!!
#define process_time      2E-6      'time of one event cycle
#define DAC_ZERO          32768
#define DAC_ZERO_18       131072    
#define PI                3.1415927
#define fifo_len          1000003
#define lockin_len        8003      '8003 gives a minimum lockin frequency of 62.48Hz @ 2us cycle time.

'communication PC ADwin
#define lockin_bias         Par_8     'lock-in bias voltage (bits)
#define lockin_active       Par_21    'lockin active flag
#define measure_active      Par_22
#define amplitude           Par_24    'lock-in amplitude (bits)
#define frequency           FPar_22    'lock_in frequency (Hz)
#define tao                 FPar_23    'lock_in tau: test purposes later only kappa will be given to program
#define report_frequency    FPar_24
#define sample_rate         FPar_25    'sample rate
#define report_samplerate   FPar_26
#define fifo_inphase        Data_1
#define fifo_quadrature     Data_2
#define fifo_input          Data_3
'ADwin only
#define lockin_sig          Data_10
#define lockin_ref          Data_11

'EVENT VARIABLES
dim lockin_sig[lockin_len] as long at dm_local    'lockin output signal in bit steps for output card
dim lockin_ref[lockin_len] as float at dm_local   'lockin reference normalized to 1 and shifted by one step because measurement happens one cycle after setting the output value
dim lockin_cycles, inph_cycle, quad_cycle, lockin_in, lockin_out, subs_cycle, subs_cycles as long
dim kappa, c0, c1, c2, c3, c4, s0, s1, s2, s3, s4 as float 'lockin demodulation and filter variables

dim fifo_inphase[fifo_len], fifo_quadrature[fifo_len] as float as fifo   'output fifo for data transmittion
dim fifo_input[fifo_len] as long as fifo

sub create_lockin_signal()
  dim sig_phase, ref_phase as float
  dim i as long
  'FIND HOW MANY lockin_cycles ARE NEEDED FOR ONE FULL SINE WAVE AT GIVEN FREQUENCY
  lockin_cycles = Round(1 / (frequency * process_time))
  subs_cycles = Round(1 / (sample_rate * process_time))
  'INCREASE TILL IT IS DEVIDABLY BY 4. (EASIER REFERENCE HANDLING, BUT ONLY CERTAIN FREQUENCIES POSSIBLE
  if (lockin_cycles and 11b <> 0) then
    do 
      Inc lockin_cycles
    until (lockin_cycles and 11b = 0)
  endif
  'REPORT ACTUAL FREQUENCY
  report_frequency = 1 / (lockin_cycles * process_time)
  report_samplerate = 1 / (subs_cycles * process_time)
  'CREATE LOCKIN SIN ARRAY  
  for i = 1 to lockin_len
    if (i <= lockin_cycles) then
      sig_phase = (i / lockin_cycles) * 2 * PI       'phase of lockin output signal
      ref_phase = ((i-1.0) / lockin_cycles) * 2 * PI 'phase of reference has to lack one cycle behind output
      lockin_sig[i] = Round(amplitude *  sin(sig_phase)) ' BEFORE: sin(phase)
      lockin_ref[i] = sin(ref_phase)
    else
      lockin_sig[i] = 0 'theoretically not necessary, just safety
      lockin_ref[i] = 0 'theoretically not necessary, just safety
    endif
  next i
endsub

sub init_lockin_filter()
  c0 = 0
  c1 = 0
  c2 = 0
  c3 = 0
  c4 = 0
  s0 = 0
  s1 = 0
  s2 = 0
  s3 = 0
  s4 = 0
endsub

init:
  'DEBUG
  'lockin_bias = DAC_ZERO
  'amplitude = DAC_ZERO / 10
  'frequency = 9100.31
  'tao = 0.0033
  'sample_rate = 500000
  Processdelay = process_delay
  
  'CLEAR TRANSMITTION FIFOS
  fifo_clear(1)
  fifo_clear(2)
  
  'CREATE LOCKIN SIGNAL AND REFERENCE
  create_lockin_signal()
  
  'INITIALITE FILTER
  init_lockin_filter()
  'INIT IN-PHASE CYCLE FOR INPHASE DEMODULATION AND LOCKIN OUTPUT
  inph_cycle = 1
  'INIT IN-QUADRATURE CYCLE FOR IN_QUADRATURE DEMODULATION BY SHIFTING LOCKIN PHASE BY 90DEG AND CORRECT FOR NEGATIVE VALUE
  quad_cycle = inph_cycle - Shift_Right(lockin_cycles, 2) + lockin_cycles 
  'INIT subs_cycles CYCLE 
  subs_cycle = 1
  'SET FILTER KONSTANT
  kappa = 1 - exp(-process_time / tao)
  
  'SET LOCKIN ACTIVE FLAG
  lockin_active = 1
  
  'CALC FIRST LOCKIN OUTPUT
  lockin_out = lockin_bias + lockin_sig[inph_cycle]
  
  'ACTIVTATE TIMER MODE FOR 18-BIT INPUT CARD (MUST BE AT THE END OF INIT)
  P2_ADCF_Mode(input_card, 1)
  
event:
  'WRITE LOCKIN OUTPUT [3 lockin_cycles (+2 jitter, comm)] 
  P2_DAC(lockin_card, lockin_channel, lockin_out)
  
  'READ LOCK-IN INPUT [88-93 lockin_cycles (+43 jitter, comm.)]
  lockin_in = P2_Read_ADCF24(input_card, input_channel) '18-bit resolution  
  
  '24 -> 18 BIT AND -OFFSET [5 lockin_cycles] 
  lockin_in = Shift_Right(lockin_in, 6) - DAC_ZERO_18
  
  'instead of idx_corr as function it could be done as sub and save some time!
  s0 = lockin_in * 2 * lockin_ref[inph_cycle]
  c0 = lockin_in * 2 * lockin_ref[quad_cycle]   'phase inph_cycle - 1 and shift by 90deg of the previous output
  
  '4 x 1st ORDER LOW PASS IN SERIES [91 lockin_cycles]
  c1 = c1 + kappa * (c0-c1)
  s1 = s1 + kappa * (s0-s1)
  c2 = c2 + kappa * (c1-c2)
  s2 = s2 + kappa * (s1-s2)
  c3 = c3 + kappa * (c2-c3)
  s3 = s3 + kappa * (s2-s3)
  c4 = c4 + kappa * (c3-c4) ' output quadrature: c4
  s4 = s4 + kappa * (s3-s4) ' output in_phase: s4
  
  'TRANSMIT DATA TO PC [max 103 during cycles measurement, 11 cycles no measurement]
  if (measure_active = 0) then
    'don't save data (faster this way, because else is processed faster than if)
  else
    'SUBSAMPLE
    if (subs_cycle < subs_cycles) then
      Inc subs_cycle
    else
      subs_cycle = 1
      'SEND DATAPOINT TO FIFO (27cycles per FIFO with no sweep)
      fifo_inphase = s4
      fifo_quadrature = c4
      fifo_input = lockin_in
    endif
  endif

  'HANDLE LOCKIN AND REFERENCE PHASE
  if (inph_cycle = lockin_cycles) then
    inph_cycle = 1
  else
    Inc inph_cycle
  endif
  if (quad_cycle = lockin_cycles) then 
    quad_cycle = 1
  else
    Inc quad_cycle
  endif

  'CALCULATE NEXT LOCKIN OUTPUT [13 lockin_cycles]
  lockin_out = lockin_bias + lockin_sig[inph_cycle]
  
finish:
  ' SET OUTPUT TO LOCKIN_BIAS
  P2_DAC(lockin_card, lockin_channel, lockin_bias)
  ' DISABLE LOCKIN ACTIVE FLAG
  lockin_active = 0
