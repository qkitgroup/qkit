#coil.py
#script mediating IVVI and measurement script
#Started by Jochen Braumueller <jochen.braumueller@kit.edu> 08/11/2013
#last update: 05/02/2015


import os, sys, time, qt

IVVI = qt.instruments.get('IVVI')
DAC_ROUT = 5    #number of routed dac port

dac_val = {'20m':1,'10m':2,'1m':3,'100u':4,
           '10u':5,'1u':6,'100n':7,'10n':8,'1n':9}

#scl_out = {1:'mA',2:'mA',3:'mA',4:'muA',5:'muA',6:'muA',7:'nA',8:'nA',9:'nA'}


def set_current(current):     #current in units of c_range
    try:  
        val = (current * 1000)
        
        if val > 2000 or val < -2000:
            print 'Error: Value exceeds upper threshold!'
            raise ArithmeticError
        else:
            if val < 1 and val > -1 and val != 0 :
                print 'Warning: Bad current setting!'
            IVVI.set_dac(DAC_ROUT,val)    
           
    except IndexError as detail:
        print 'Error: Electronics might be disconnected. ',detail
    except ArithmeticError as detail:
        print 'Invalid current setting. ',detail


def get_current(c_range = '100u'):
    
    val = IVVI.get_dac(DAC_ROUT)/1000    #val = voltage in Volts
   
    try:
        if c_range == '20m':
            print round(val*20,3), 'mA'
        
        elif c_range == '10m':
            print round(val*10,3), 'mA'
            
        elif c_range == '1m':
            print round(val,3), 'mA' 
               
        elif c_range == '100u':
            print round(val*100,3), 'uA' 
            
        elif c_range == '10u':
            print round(val*10,3), 'uA'
            
        elif c_range == '1u':
            print round(val,3), 'uA' 
                   
        elif c_range =='100n':
            print round(val*100,3), 'nA'
            
        elif c_range == '10n':
            print round(val*10,3), 'nA'
            
        elif c_range == '1n':
            print round(val,3), 'nA'    
            
    except IndexError as detail:
        print 'Error: Electronics might be disconnected. ',detail
    except Exception as detail:
        print 'Error: ',detail
    

def init():
    IVVI.initialize()
    time.sleep(0.1)

    if IVVI.reset_dac() == None:
        print 'Error!'
    else:
        set_current(0)
        print 'Done.'

if __name__ == "__main__":

    time.sleep(0.1)
    print get_current()
