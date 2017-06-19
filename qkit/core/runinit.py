# Script to initialize the startup routine for the Qkit core
# (replacing qtlab_shell)
# YS@KIT/2017

import os
import sys
import qkit.core.qcorekit as qckit

#if __name__ == '__main__': # YS: with this statement, the code is only executed if file is run explicitely
qckit.coredir = os.path.dirname(qckit.__file__)

initdir = os.path.join(qckit.coredir,'init')
filelist = os.listdir(initdir)

print 'Starting the core of the Qkit framework...'

for i in filelist:
    if os.path.splitext(i)[1] == ".py":
        print 'Executing %s...' % (i)
        try:
            execfile(os.path.join(initdir,i))
        except SystemExit:
            break

try:
    del filelist, initdir
except:
    pass