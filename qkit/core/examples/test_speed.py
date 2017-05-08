# Script to test overhead of QTLab framework

import qt
import time

ins = qt.instruments['dsgen']
N = 1e6

start = time.time()
i = 0
while i < N:
    v = ins._ins.do_get_wave()
    i += 1
stop = time.time()
print 'do_get_wave: %s sec' % (stop - start, )

start = time.time()
i = 0
while i < N:
    v = ins.get_wave(fast=True)
    i += 1
stop = time.time()
print 'get_wave(fast=True): %s sec' % (stop - start, )

start = time.time()
i = 0
while i < N:
    v = ins.get_wave()
    i += 1
stop = time.time()
print 'get_wave: %s sec' % (stop - start, )

