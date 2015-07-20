from numpy import  arange, size, linspace

# set matplotlib figure label
plt.gca().set_xlabel("V [uV]")
plt.gca().set_ylabel("I [nA]")
#plt.gcf().clear()

from time import sleep, time
import qt


start_time = time()

# define my channels

Chan_Iout = DAQ._ins._get_output_channels()[0]
Chan_Vin = DAQ._ins._get_input_channels()[0]

class  IV(object):
    def  __init__(self,DAQ):
    self.DAQ =  DAQ
    self.current_bias = False
    self.voltage_bias = False
    
    self.data = qt.Data(name=name)
    
    def set_current_bias(self):
        self.current_bias = True
        self.voltage_bias = False
        # current bias
        self.A_per_V = 2e-5
        self.V_amp = 1e3
        self.I_div = 1
        self.V_divider  = 1
        
        # current bias range:
        Imin = 135.e-6
        Imax =  137.e-6
        
        
        data.add_coordinate('I [A]')
            if mw_scan:
                data.add_coordinate('f [Hz]')
            elif mag_scan:
                data.add_coordinate('I [mA]')
            else:
                data.add_coordinate('empty')
            data.add_value('V [V]')

    def set_voltage_bias(self):
        self.current_bias = False
        self.voltage_bias = True
        # voltage bias
        A_per_V = 1e8
        V_divider  = 1000
        V_amp = 1
        
        # voltage bias range
        Vmin = -00e-6
        Vmax =  100e-6
                    data.add_coordinate('V [V]')
            if mw_scan:
                data.add_coordinate('f [Hz]')
            elif mag_scan:
                data.add_coordinate('I [mA]')
            else:
                data.add_coordinate('empty')
            data.add_value('I [A]')
            data.add_coordinate('V [V]')
            if mw_scan:
                data.add_coordinate('f [Hz]')
            elif mag_scan:
                data.add_coordinate('I [mA]')
            else:
                data.add_coordinate('empty')
            data.add_value('I [A]')


        if self.voltage_bias:

        if self.current_bias:

        
    
    def set_IV_parameters(self, samples = 1000, rate = 1000):
        self.samples =  samples
        self.rate = rate
    def set_sweeps(self, sweeps = 1):
        self.sweeps =  sweeps
    
    expname = 'A0067_E2_P25_'
    name='IV_vs_f_'+expname

    name_settings = name+"_SETTINGS.txt"

    # second vector vec_2: either 
    # magnetic fild scan (mag_scan)
    # or
    # microwave scan (mw_scan)
    mag_scan = False
    mw_scan  = False


    if mag_scan:
        # magnetic field scan
        A_per_V_coil = 2e-2
    if mw_scan:
        MW=mw_src2





    fmin        = 1e9
    fmax        = 1e10
    f_step_size = .5e8


    IBmin = 136.e-3
    IBmax = 138.e-3
    IB_step_size = .1e-3

    Voffset = 50e-6


    Ioffmax =0.8e-6
    Ioffmin =0.0e-6
    Ioff_step =0.05e-6

    def _gen_triangle(self,min,max,samples=1000):
        tri_fw = linspace(min,max,samples)
        tri_bw = linspace(max,min,samples)
        return tri_fw,tri_bw

    def _take_IV(self,vec_fw,vec_bw,vec_2,out_conversion_factor,in_amplification,out_divider=1, in_offset=0):
        """ IV measurement with current or voltage (vec_fw, vec_bw) and a second parameter (vec_2) """
        mydata=DAQ.sync_output_input(Chan_Iout,Chan_Vin,vec_fw*out_divider/out_conversion_factor,rate=rate)
        data.add_data_point(vec_fw, vec_2, mydata/in_amplification)
        if current_bias:
            pl1 = plt.plot((mydata/in_amplification)*1e6,vec_fw*1e6,"o")
        if voltage_bias:
            pl1 = plt.plot(vec_fw*1e6, (mydata/in_amplification)*1e9,"-")
        qt.msleep(0.1)
        
        mydata=DAQ.sync_output_input(Chan_Iout,Chan_Vin,vec_bw*out_divider/out_conversion_factor,rate=rate)
        data.add_data_point(vec_bw, vec_2, mydata/in_amplification)
        #pl1 = plt.plot(vec_bw*1e6, (mydata/in_amplification)*1e6,"+")
        
        if current_bias:
            pl1 = plt.plot((mydata/in_amplification)*1e6,vec_bw*1e6,"+")
        if voltage_bias:
            
            pl1 = plt.plot(vec_bw*1e6, (mydata/in_amplification)*1e9,"-")
        qt.msleep(0.1)

    def _save_settings(self):
        name_settings = (data.get_filepath().split(data.get_filename())[0])+name+"_SETTINGS.txt"
        settings = open(name_settings, "w")

        settings.write("## Settings for measurement, "+name)
        settings.write("\nA per V = %f\nA per V (coil) = %f\nV_amp = %f\nI_div = %f\nsamples = %f\nrate = %f\nsweeps = %f\n" % (float(A_per_V), float(A_per_V_coil), float(V_amp), float(I_div), float(samples), float(rate), float(sweeps)))
        settings.write("\nImin = %f A\nImax = %f mA\n" % (Imin, Imax))
        settings.write("\nIBmin = %f A\nIBmax = %f A\nIB_step = %f A\n" % (IBmin, IBmax, IB_step))
        if len(IB_vec)==1: settings.write("Constant IB at %f mA\n" %(IB_vec[0]))
        settings.write("\nIoffmin = %f A\nIoffmax = %f A\nIoff_step = %f A\n" % (Ioffmin, Ioffmax, Ioff_step))
        if len(Ioff_vec)==1: settings.write("Constant Ioff at %f mA\n" %(Ioff_vec[0]))

        settings.close()
        
        
        
    def scan(self):
        "main scan function"
        # second vector vec_2
        if not mw_scan and not mag_scan:
            # reset vec_2
            vec_2=[0]

        #Frequency
        if mw_scan:
            vec_2 = arange(fmin, fmax, f_step_size)
            print "Frequency steps:", len(vec_2), "with size:", f_step_size

        #Magnetic field
        if mag_scan:
            vec_2 = arange(IBmin, IBmax, IB_step_size)
            print "Coil current steps:", len(vec_2), "with size:", IB_step_size

            
        if current_bias:
            I_vec_fw, I_vec_bw = gen_triangle(Imin,Imax,samples)
        elif voltage_bias:
            V_vec_fw, V_vec_bw = gen_triangle(Vmin,Vmax,samples)
        else:
            print "please specify current_bias or voltage_bias!"
            exit()

        qt.mstart()

  







        data.create_file()
        data.add_comment('Samples: '+str(samples))
        data.add_comment('Rate: '+str(rate))

        for vec_2_item in vec_2:

            # if current sweep
            if mag_scan:
                IB = vec_2_item
                #DAQ.set_ao1(IB/A_per_V_coil)
                yoko.ramp_ch1_current(IB, 100e-6, showvalue=False)
                print 'Coil Current [mA]:', IB/1e-3
            # if frequency
            if mw_scan:
                f = vec_2_item
                MW.set_frequency(f)
                print 'Frequency [GHz]:', f/1e9
            
            # let it settle
            qt.msleep(0.5)
            
            print "Elapsed time:", (time()-start_time)/60., "min"
            
            # this is a crude hack to save the data       
            vec_2_vec = []
            if current_bias:
                for nn in I_vec_fw:
                    vec_2_vec.append(vec_2_item)
                # take the IV
                for i in arange(sweeps):
                    take_IV(I_vec_fw, I_vec_bw,
                        vec_2_vec,
                        out_conversion_factor = A_per_V,
                        in_amplification = V_amp, 
                        out_divider=V_divider, 
                        in_offset=0)
                    data.new_block()

            if voltage_bias:
                for nn in V_vec_fw:
                    vec_2_vec.append(vec_2_item)

                # take the IV
                for i in arange(sweeps):
                    take_IV(V_vec_fw, V_vec_bw,
                            vec_2_vec,
                            out_conversion_factor = 1,
                            in_amplification = A_per_V, 
                            out_divider=V_divider, 
                            in_offset=0)
                    data.new_block()
                    
                    
                    
        #DAQ.set_ao0(0)
        DAQ.set_ao1(0)

        png_file = (data.get_filepath().split(data.get_filename())[0])+name+'.png'
        #print png_file
        #pl1.save_png(filepath=png_file)
        #pl1.save_gp()

        data.close_file()
        qt.mend()
