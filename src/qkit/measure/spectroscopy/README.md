# spectroscopy
qkit.measure.spectroscopy -- the qkit measurement module for VNA spectroscopy measurements

### Features:
  * multi-dimensional measurements with up to two external sweep parameters besides the
  VNA frequencies
  * measurement of VNA frequency over time
  * live-fitting of measured MW resonators using the qkit.analysis.resonator module, used
  via set_resonator_fit(...)
  * measurement time during a multi-dimensional sweep can be saved by designing a landscape
  and only measurin in this interesting paramter space
  * data is stored in HDF5 file using our own qkit.storage.store module
  
### Operation:
  * for a example see the spectroscopy_example.ipynb