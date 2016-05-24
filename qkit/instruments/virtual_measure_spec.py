from instrument import Instrument
import numpy
from plot_engines.qtgnuplot import get_gnuplot
import qt
import types
import time


class virtual_measure_spec(Instrument):
    '''
    perform time-resolved and averaged measurement with the spectrum card
    '''
    _offsets = None
    
    def __init__(self, name, card, samples, segments = 1, averages = 1, blocks = 1, channels = 3, multimode = True, gate_func = None, trigger_rate = 1e5, offsets = None):
        '''
            perform time-resolved averaged measurements with the spectrum card

            parameters:
                card - spectrum card to use
                samples - number of samples per trigger
                segments - number of different measurements in a row
                averages - number of acquisitions per block
                blocks - number of blocks to aquire
                channels - bit map of channels to use (B"01" = ch0, B"10" = ch1, B"11" = ch0 and ch1
                multimode - use multiple recording mode?
                gate_func - called at the start/end of each block with parameter True/False
                trigger_rate - expected rate of triggers for calculation of proper timeouts
                offsets - offset added to the channel values
        '''
        Instrument.__init__(self, name, tags=['virtual'])

        # parameters
        self.add_parameter('samples', type = types.IntType)
        self.add_parameter('samplerate', type = types.IntType)
        self.add_parameter('segments', type = types.IntType)
        self.add_parameter('averages', type = types.IntType)
        self.add_parameter('blocks', type = types.IntType)
        self.add_parameter('offsets', type = types.ListType)
        self.add_parameter('channels', type = types.IntType)
        self.add_parameter('multimode', type = types.BooleanType)
        self.add_parameter('trigger_rate', type = types.FloatType)
        self.add_parameter('spec_trigger_delay', flags=Instrument.FLAG_GETSET, type=types.IntType)
        # measurement functions
        self.add_function('get_clock')
        self.add_function('set_gate_func')
        self.add_function('acquire')
        self.add_function('measure_1d_avg')
        self.add_function('measure_1d')
        self.add_function('spec_start')
        self.add_function('spec_stop')
        
        self._initializing = True
        # fixed parameters
        self._dacq = card
        
        # changeable parameters
        self._samples = 32
        self._segments = 1
        self._averages = 1
        self.set_samples(samples)
        self.set_segments(segments)
        self.set_averages(averages)
        self.set_blocks(blocks)
        
        self.set_channels(channels)
        self.set_multimode(multimode)
        self.set_offsets(offsets)
        self.set_trigger_rate(trigger_rate)
        self.set_gate_func(gate_func)
        self.get_all()
        
        # initialize card
        self._initializing = False
        self.init_card()
        self._dacq.set_trigger_ORmask_tmask_ext0()
        self._dacq.trigger_mode_pos()

    def get_all(self):
        self.get_samples()
        self.get_segments()
        self.get_averages()
        self.get_blocks()
        self.get_offsets()
        self.get_channels()
        self.get_multimode()
        self.get_trigger_rate()   #JB

    def init_card(self):
        # abort if still starting up
        if(self._initializing): return True
        
    	self._dacq.stop()
        # acquisition mode
        if(self._multimode):
            self.init_card_multi()
        else:
            self.init_card_single()

    def init_card_single(self):
        self._dacq.set_single_mode()
        self._dacq.set_timeout(1000) #todo: replace by sensible default
        self._dacq.set_memsize(self._samples)
        self._dacq.set_post_trigger(self._samples - 16)

    def init_card_multi(self):
        self._dacq.set_multi_mode()
        acq_time = self._segments*self._averages/self._trigger_rate
        self._dacq.set_timeout(int(1000*(5+acq_time)))
        if(self._samples * self._segments * self._averages > self._dacq.get_ramsize()/self._numchannels):
            raise ValueError('meas_spec: card memory is not sufficient to store _segments and _averages requested')
        self._dacq.set_segmentsize(self._samples)
        self._dacq.set_memsize(self._samples * self._segments * self._averages)
        self._dacq.set_post_trigger(self._samples - 16)


    def spec_start(self):
        self._dacq.start()
		
    def spec_stop(self):
        self._dacq.stop()

    #make spec.timeout settable by mspec via remote
    def do_set_spec_timeout(self, timeout):
        self._dacq.set_timeout(timeout)
    def do_get_spec_timeout(self):
        return self._dacq.get_timeout()
    ###

    def do_set_spec_trigger_delay(self,delay):
        self._dacq.set_trigger_delay(delay)
		
    def do_get_spec_trigger_delay(self):
        return self._dacq.get_trigger_delay()
	

    def do_set_samples(self, samples):
        if(samples < 32): raise ValueError('meas_spec: minimum number of samples per trace is 32.')
        if(samples % 16 != 0): raise ValueError('meas_spec: number of samples per trace must be divisible by 16.')
        self._samples = samples
        self.init_card()
        
    def do_get_samples(self):
        return self._samples
        
    def do_get_samplerate(self):
        return self._dacq.get_spc_samplerate()
        
    def do_set_samplerate(self,rate):
        return self._dacq.set_spc_samplerate(rate)
        
    def do_set_channels(self, channels):
        if((channels < 1) | (channels > 3)): raise ValueError('meas_spec: channels must be B"01", B"10" or B"11"')
        self._channels = channels
        if((channels == 1) | (channels == 2)):
            self._numchannels = 1
        else:
            self._numchannels = 2
        
        # channel setup
        self._dacq.stop()
        if(self._channels == 1):
            self._dacq.select_channel0()
        elif(self._channels == 2):
            self._dacq.select_channel1()
        elif(self._channels == 3):
            self._dacq.select_channel01()
        self.init_card()

    def do_get_channels(self):
        return self._channels

    def do_set_segments(self, segments):
        self._segments = segments
        self.init_card()
        
    def do_get_segments(self):
        return self._segments
        
    def do_set_averages(self, averages):
        self._averages = int(averages)
        self.init_card()
    
    def do_get_averages(self):
        return self._averages

    def do_set_blocks(self, blocks):
        self._blocks = blocks
    
    def do_get_blocks(self):
        return self._blocks
        
    def do_set_trigger_rate(self, trigger_rate):
        ''' set expected trigger rate. used to calculate timeouts. '''
        self._trigger_rate = trigger_rate
        self.init_card()
        
    def do_get_trigger_rate(self):
        return self._trigger_rate
        
    def do_set_offsets(self, offsets):
        if(offsets == None):
            offsets = numpy.zeros((self._numchanels,))
        if(len(offsets) != self._numchannels):
            raise ValueError(__name__ + 'one offset per channel is required')
        self._offsets = offsets
        
    def do_get_offsets(self):
        return self._offsets
        
    def set_gate_func(self, gate_func):
        ''' function called at start of new block '''
        if isinstance(gate_func,str):
            global mm
            import multimeasure as mm
            print gate_func
            self._gate_func = eval(gate_func)
        else:
            self._gate_func = gate_func
        
    def do_set_multimode(self, multimode):
        self._multimode = multimode
        self.init_card()

    def do_get_multimode(self):
        return self._multimode

    def get_clock(self):
        return self._dacq.get_spc_samplerate()



    def acquire(self):
        '''
        wrapper to the acquire function corresponding to the current mode setting
        '''
        # acquire data
        if(self._multimode):
            result = self._acquire_multimode()
        else:
            result = self._acquire_singlemode()
        # apply offsets
        if(self._offsets != None):
            for idx in range(len(self._offsets)):
                if(self._segments == 1):
                    # shape of result is (samples, channels)
                    result[:, idx] += offsets[idx]
                else:
                    # shape of result is (samples, channels, segments)
                    result[:, idx, :] += offsets[idx]
        return result

    def _acquire_multimode(self):
        '''
        acquire the number of traces specified by the _averages and _blocks parameters
        and return the averaged trace. measurement is done in multiple recording mode.
        '''
        dat = []
        # measure first block
        self._acquire_multimode_prepare()
        for i in range(self._blocks):
            # retrieve current block
            dat_block = self._acquire_multimode_extract(blocking = True, averaged = False)
            # background-measure next block
            if(i < self._blocks-1): self._acquire_multimode_prepare()
            # process current block
            #dat_block = numpy.asfarray(dat_block, numpy.float32)
            #dat_block = numpy.mean(dat_block, axis = 1)
            if self._segments > 1:
                # fast averaging
                sum = numpy.zeros((self._samples, self._numchannels, self._segments), numpy.int32)
                for j in range(self._numchannels):
                    for i in range(self._averages):
                        sum[:, j, :] += dat_block[:, i, j, :]
                dat_block = numpy.asfarray(sum) / self._averages
            else:
                # fast averaging
                sum = numpy.zeros((self._samples, self._numchannels), numpy.int32)
                for j in range(self._numchannels):
                    for i in range(self._averages):
                        sum[:, j] += dat_block[:, i, j]
                dat_block = numpy.asfarray(sum) / self._averages

                # faster averaging over 2d structure
                #dat_block.shape = (self._averages, self._samples*self._numchannels)
                #sum = numpy.zeros((self._samples*self._numchannels), numpy.int32)
                #for i in range(self._averages):
                #    sum += dat_block[i, :]
                #dat_block = numpy.asfarray(sum.reshape((self._samples, self._numchannels))) / self._averages
            dat.append(dat_block)
        # average over blocks
        return numpy.mean(numpy.array(dat), axis = 0)

    def _acquire_multimode_prepare(self):
        '''
        prepare and start a measurement in multipe recording mode.
        return control to the main program while the card is measuring.
        '''
        if(self._gate_func): self._gate_func(False)
        self._dacq.stop()
        self._dacq.invalidate_buffer()
        self._dacq.start_with_trigger()
        #self._dacq.start_with_trigger_and_waitready()
        if(self._gate_func): self._gate_func(True)

    def _acquire_multimode_extract(self, blocking = True, averaged = True):
        '''
        return averaged traces acquired in multiple recording mode.

        blocking - if False, return to the main program if acquisition is not complete yet
        '''
        if(blocking):
            err = self._dacq.waitready()
            if(err == 263):
                print 'measure_spec: Timeout during data acquisition.'
                return None;
        else:
            status = self._dacq.get_card_status()
            # 'ready' or 'waitdma' flag, see p138 of the manual
            if(~(status & 0x4) | ~(status & 0x200)): return None
            # todo: assumes that no error occured when status&4 occurs

        # time is on axis 0
        if(self._numchannels == 2):
            dat = self._dacq.readout_doublechannel_multimode_bin() # channel, segment, sample
        else:
            dat = self._dacq.readout_singlechannel_multimode_bin() # channel, segment, sample
        dat = numpy.swapaxes(dat, 0, 2) # sample, segment, channel
        # add segments axis at the end
        if self._segments > 1:
            dat = numpy.reshape(dat, (self._samples, self._averages, self._segments, self._numchannels))
            dat = numpy.swapaxes(dat, 2, 3)
            if(averaged):
                dat = numpy.asfarray(dat, numpy.float32)
                dat = numpy.mean(dat, axis=1) # sample, channel
        else:
            if(averaged):
                # two times faster than numpy.mean
        	    dat = self._multimode_average(dat)
        return dat

    def _multimode_average1(self, dat):
    	''' faster-than-numpy averaging '''
    	shp = dat.shape
    	res = numpy.zeros((shp[0], shp[2]))
    	for i in range(shp[0]):
    		for j in range(shp[2]):
    			res[i, j] = numpy.mean(numpy.asfarray(dat[i, :, j], numpy.float32))
    	return res

    def _multimode_average(self, dat):
    	''' faster-than-numpy averaging '''
    	shp = dat.shape
    	sum = numpy.zeros((shp[0], shp[2]), np.int)
    	for i in range(shp[1]):
            sum += dat[:, i, :]
    	return np.array(res, np.float32)/shp[1]


    def _acquire_singlemode(self):
        '''
        acquire the number of traces specified by the _averages parameter
        and return the averaged trace. measurement is done in single mode.
        '''

        averaged = numpy.zeros(shape=(self._samples, 2), dtype = numpy.float32)
        for idx in range(1, 1+self._averages):
            err = self._dacq.start_with_trigger_and_waitready()
            if(err == 263):
                print 'measure_spec: Timeout during data acquisition.'
                return None;
            data = self._dacq.readout_doublechannel_singlemode_bin()
            averaged.__iadd__(data) #numpy.array(data, numpy.float32)
        return averaged/self._averages



    def measure_1d_avg(self, x_vec, coordname, set_param_func, iterations = 1, comment = None, dirname = None, plotLive = True):
        '''
            acquire _averages traces per value in x_vec and store the time-averaged result

            x_vec - vector of values to pass to set_param_func at the start of each iteration
            coordname - friendly name of the parameter contained in x_vec
            set_param_func - parameter values are passed to this function at the start of each iteration
            comment - comment line in the data file
            dirname - data is saved in directories named <time>_spec_<dirname>
            plotLive - plot data during measurement
        '''
        qt.mstart()

        if(dirname == None): dirname = coordname
        data = qt.Data(name='spec_lp_%s'%dirname)
        if comment: data.add_comment(comment)
        data.add_coordinate(coordname)
        data.add_value('ch0')
        if(self._numchannels == 2):
            data.add_value('ch1')
        if iterations > 1: data.add_coordinate('iteration')
        data.create_file()

        plot_ch0 = qt.Plot2D(data, name='waveform_ch0', coorddim=0, valdim=1, maxtraces=2)
        if(self._numchannels == 2):
            plot_ch1 = qt.Plot2D(data, name='waveform_ch1', coorddim=0, valdim=2, maxtraces=2)

        set_param_func(x_vec[0])

        # measurement loop
        for i in range(iterations):
            data.new_block()
            for x in x_vec:
                set_param_func(x)
                # sleep(td)
                qt.msleep() # better done during measurement (waiting for trigger)

                dat_x = [x]
                dat_mean = numpy.mean(self.acquire(), axis = 0)
                dat = numpy.append(dat_x, dat_mean, axis = 0)
                if(iterations > 1): dat = numpy.append(dat, [i], axis = 0)
                data.add_data_point(*dat)

                plot_ch0.update()
                if(self._numchannels == 2):
                    plot_ch1.update()

            plot_ch0.update()
            plot_ch0.save_png()
            plot_ch0.save_gp()
            if(self._numchannels == 2):
                plot_ch1.update()
                plot_ch1.save_png()
                plot_ch1.save_gp()




    def measure_1d(self, x_vec, coordname, set_param_func, comment = None, dirname = None, plotLive = True, plot3d = False):
        qt.mstart()

        if(dirname == None): dirname = coordname
        data = qt.Data(name='spec_%s'%dirname)
        if comment: data.add_comment(comment)
        data.add_coordinate(coordname)
        data.add_coordinate('time')
        self._rate = self._dacq.get_spc_samplerate()
        dat_time = numpy.arange(0, 1.*self._samples/self._rate, 1./self._rate)
        dat_time = dat_time.reshape((dat_time.shape[0], 1))
        data.add_value('ch0')
        data.add_value('ch1')
        data.create_file()

        if plotLive:
            if plot3d:
                plot_ch0 = qt.Plot3D(data, name='waveform_ch0_3d', coorddims=(0,1), valdim=2)
                plot_ch0.set_palette('bluewhitered')
                plot_ch1 = qt.Plot3D(data, name='waveform_ch1_3d', coorddims=(0,1), valdim=3)
                plot_ch1.set_palette('bluewhitered')
            else:
                plot_ch0 = qt.Plot2D(data, name='waveform_ch0', coorddim=1, valdim=2, maxtraces=2)
                plot_ch1 = qt.Plot2D(data, name='waveform_ch1', coorddim=1, valdim=3, maxtraces=2)

        set_param_func(x_vec[0])

        # save plot even when aborted
        try:
            # measurement loop
            for x in x_vec:
                set_param_func(x)
                # sleep(td)
                qt.msleep() # better done during measurement (waiting for trigger)

                data.new_block()
                dat_x = x*numpy.ones(shape=(self._samples, 1))
                dat = numpy.append(dat_x, dat_time, axis = 1)
                dat_wave = self.acquire()
                dat = numpy.append(dat, dat_wave, axis = 1)
                data.add_data_point(dat)

                if plotLive & ~plot3d:
                    plot_ch0.update()
                    plot_ch0.save_png()
                    plot_ch0.save_gp()
                    plot_ch1.update()
                    plot_ch1.save_png()
                    plot_ch1.save_gp()
            return; # execute finally statement
        finally:
            if(~plotLive | plot3d):
                plot_ch0.update()
                plot_ch0.save_png()
                plot_ch0.save_gp()
                plot_ch1.update()
                plot_ch1.save_png()
                plot_ch1.save_gp()
            data.close_file()
            qt.mend()
