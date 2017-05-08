# See also http://www.scipy.org/Cookbook/Reading_mat_files

import numpy as np
import scipy.io

# For old-style Matlab (up to 7.1) files you can use scipy.io

R = np.random.rand(100)
data = {
    'R': R,
    'test': 123,
}
scipy.io.savemat('test.mat', data)

data = scipy.io.loadmat('test.mat')
print 'Data: %r' % (data, )

# New-style Matlab files (HDF5 format) require use of the h5py module
import h5py
d = h5py.File('testhdf5.mat')
R = d['R'].value

