import gobject
import qt

def measure_mon():
    print 'Measuring...'

    # Return True to continue calling this function
    return True

nsec = 10
mon_hid = gobject.timeout_add(nsec * 1000, measure_mon)

# To remove:
#gobject.source_remove(mon_hid)
