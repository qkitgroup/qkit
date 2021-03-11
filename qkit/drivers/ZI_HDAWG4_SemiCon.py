import logging
import json
from datetime import datetime
from ZI_HDAWG4 import ZI_HDAWG4
import matplotlib.pyplot as plt
import numpy as np
import os
from pathlib import Path
import qkit
from qkit.core.instrument_base import Instrument
import shutil
import sys
import textwrap
import time
from time import sleep
import zhinst 
import zhinst.utils

class ZI_HDAWG4_SemiCon(ZI_HDAWG4):
    def __init__(self,name,device_id, **kwargs):
    #logging.info(__name__ + ' : Initializing instrument')
        super(ZI_HDAWG4_SemiCon,self).__init__(name = name, device_id = device_id, tags = ['physical','ZI_HDAWG4'])

        self.zshape_array = np.empty(0)#array containing the series of sequences

        self.add_function('zcreate_sequence_program')
        self.add_function('zconvert_time_in_s_to_samples')
        self.add_function('zconvert_samples_to_time_in_s')
        self.add_function('zrun_sequence')
        
    #calculate number of samples from a given time (input: time_value in s), considering the sample rate
    #the possibility to set round_return = 1 to round samples value to an integer multiple of 16 is possible in order to use return value directly for an awg output (see doc: granularity)
    def zconvert_time_in_s_to_samples(self, time_value, round_return = 0):
        sampling_rate = self.get_SamplingRate()
        samples = time_value * sampling_rate
        #check how much to add or substract to get integer multiple of 16
        if round_return:
            if samples%16<8:
                samples = samples-samples%16
            else:
                samples = samples+(16-samples%16)
        logging.info(__name__ +': %s s converted to %s samples.'%(f"{time_value:.5e}", f"{samples:.5e}"))
        return samples
        
    #calculate time from a number of given samples (input: samples_value)
    def zconvert_samples_to_time_in_s(self, samples_value):
        sampling_rate = self.get_SamplingRate()
        time = samples_value/sampling_rate
        logging.info(__name__ +': %s samples converted to %s s.'%(f"{samples_value:.5e}",f"{time:.5e}"))
        return time

    # define AWG program as string stored in the variable self.awg_program, equivalent to what
    # would be entered in the Sequence Editor window in the graphical UI.
    # before creating sequence, run load_config_file.
    # set int loop_or_single_or_repeat to 0 (loop mode), 1 (single mode, default) or other positive integer as the number of repetitions (example: 3 => repeating 3 times)

    def zcreate_sequence_program(self, loop_or_single_or_repeat = 0):

        #check input values

        if loop_or_single_or_repeat<0:
            logging.error(__name__ +': Expecting positive integer or 0 for loop_or_single_or_repeat.')

        #get a list of files in folder "waves/" and sort it

        fileslist = sorted(os.listdir(self.wave_dir))
        logging.debug(__name__+': Detected waveform files: '+str(os.listdir(self.wave_dir)))

        #make sequence program string in order to play all csv files in folder "waves/" (self.set_reg1_user_regs(1) to run playback)

        self.awg_program = str("while(getUserReg(0)==0);\n")

        #set up markers

        self.awg_program = self.awg_program+"wave marker1_wave = \"marker1_file\";\n"
        self.awg_program = self.awg_program+"wave marker2_wave = \"marker2_file\";\n"

        #put together csv wave w and marker_wave to wave wm...

        channel_identifiers = ['A','B','C','D']
        wms_array=np.array([])
        for j in range(0,len(fileslist)):
                if fileslist[j]!='.cache' and fileslist[j]!='marker1_wave.csv' and fileslist[j]!='marker2_wave.csv':#ommit .cache and marker waves when iterating through files
                    #check for files and also channel identifier A,B,C,D in filename, e.g. "custom0A..."
                    waveform_index=fileslist[j][6]
                    for i in range(0,len(self._channel_outputs)):

                        if self._channel_outputs[i]==1 and fileslist[j][7]==channel_identifiers[i]:
                            self.awg_program = self.awg_program+"wave w"+channel_identifiers[i]+waveform_index+" = \""+str(fileslist[j]).replace(".csv","")+"\";\n"
                            self.awg_program = self.awg_program+"wave wm"+channel_identifiers[i]+waveform_index+" = w"+channel_identifiers[i]+waveform_index+"+marker"+str(self._marker_outputs[i])+"_wave;\n"
                            wms_array=np.append(wms_array,"wm"+channel_identifiers[i]+waveform_index)

        #set up loop, single or repeat mode

        if loop_or_single_or_repeat==0:
            logging.info(__name__ +': Sequence run in loop mode')
            self.awg_program = self.awg_program+"while(true){\n"
        elif loop_or_single_or_repeat==1: 
            logging.info(__name__ +': Sequence run in single mode')
        else:
            logging.info(__name__ +': Repeating sequence %d times'%loop_or_single_or_repeat)
            self.awg_program = self.awg_program+"repeat(%d){\n"%loop_or_single_or_repeat

        #make playWaves

        #   internal counter to see how many channels are used
        counter = 0

        for j in range(0,len(wms_array)):

                for i in range(0,len(self._channel_outputs)): 
                    playwave_variable = wms_array[j] 

                    if counter==0 and i==0:
                        self.awg_program = self.awg_program+"playWave("

                    if self._channel_outputs[i]==1 and wms_array[j][2]==channel_identifiers[i]:
                        if counter!=0:
                            self.awg_program = self.awg_program+","
                        self.awg_program = self.awg_program+str(i+1)+","+playwave_variable
                        counter+=1

                #   check if brackets of playWave have to be closed
                if counter == np.sum(self._channel_outputs):
                    self.awg_program = self.awg_program+");\n"
                    counter = 0

        if loop_or_single_or_repeat!=1:
            self.awg_program = self.awg_program+"}"

        #print sequence program

        logging.info(__name__+' : sequence program : \n'+self.awg_program+'\n')

        #save sequence to file

        now = datetime.now()
        os.makedirs('sequences',exist_ok=True)
        sequence_code_file_name = "sequences/sequence_"+now.strftime("%Y-%m-%d_%Hh%Mmin%Ss")
        sequence_code_file = open(sequence_code_file_name, "w")
        n = sequence_code_file.write(self.awg_program)
        sequence_code_file.close()
        logging.info(__name__+' : saved sequence filename: %s'%sequence_code_file_name)

    def zrun_sequence(self, new):
        self.set_reg1_user_regs(new)


if __name__ == "__main__":
    qkit.start()

    #example of a sequence
    device_identification = 'dev8268'
    hartwig = qkit.instruments.create('hartwig','ZI_HDAWG4_SemiCon',device_id = device_identification )
    logging.info(__name__ + ' : ZI_HDAWG4_SemiCon initialized')
    print('Starting testing routine.')
    print(100*'x')

    hartwig.load_config_file('example_config_ZI_HDAWG4_Semicon.json')
    print(hartwig._marker_outputs)
    print(hartwig._channel_outputs)

    ##----------------------------------
    ##demo: SamplingRate
    #hartwig.get_SamplingRate()
    #hartwig.set_SamplingRate(0,user_input = 1)
    #hartwig.get_SamplingRate()
    #input()

    ##----------------------------------

    ##demo: convert samples/time

    #a = hartwig.zconvert_time_in_s_to_samples(5.232e-6,round_return = 0)
    #b = hartwig.zconvert_time_in_s_to_samples(5.232e-6,round_return = 1)
    #hartwig.zconvert_samples_to_time_in_s(a)
    #hartwig.zconvert_samples_to_time_in_s(b)

    #input()

    ##----------------------------------

    #if new sequence arrays
    #hartwig.zrefresh_folder()
    #create sequence array 
    ##for i in range(0,3):
    ##    #make sequence array
    ##    hartwig.zshape()

    ##    #channelA = hartwig.zshape_array
    ##    channelB = hartwig.zshape_array
    ##    #channelC = hartwig.zshape_array
    ##    #channelD = hartwig.zshape_array

    ##    testarray = np.array([channelB],dtype = 'object')
    ##    #testarray = np.array([],dtype = 'object')
    ##    hartwig.zwrite(testarray,stamp = i,preview = 'no')

    hartwig.zcreate_sequence_program()

    #upload and play
    hartwig.zupload_to_device()

    #run sequence
    hartwig.zrun_sequence(1)

    #stop sequence
    hartwig.zrun_sequence(0)

    #disable everything
    zhinst.utils.disable_everything(hartwig.daq, hartwig.device)
    #----------------------------------

