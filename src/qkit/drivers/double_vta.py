# import instrument


# 

class DoubleVTA(Instrument):
  def __init__(self):
    # setter matrix & getter matrix for sweeping voltage difference at const. total voltage across a sample and measuring current:
    # (delV) = (1   -1) . (V1) 
    # (avgV)   (.5  .5)   (V2)
    # (Ieff) = (.5 -.5) . (I1)
    # (Ioff)   (1    1)   (I2)
    #
    self.setter_1 = None
    self.setter_2 = None
    self.setter_matrix = np.array([[1, 0], [0, 1]])
    self.getter_1 = None
    self.getter_2 = None
    self.getter_matrix = np.array([[1, 0], [0, 1]])
