import qt
import time

start = time.time()

def print_time():
    t = time.time() - start
    print 'DeltaT = %.03f' % t

    # Return True to continue executing this function
    return True

nsec = 20
qt.flow.register_callback(nsec * 1000, print_time, handle='timecb')

# To remove use:
# qt.flow.remove_callback('timecb')
