qkit.measure.transport package
==============================

Measurement class to take transport measurements such as current-voltage characteristics. The taken data are saved in an .h5-file. In addition, all instrument settings are saved in a .set-file and an optional measurement object is saved in a .measurement-file

Initialization:
---------------
* IV device: DC source-measure unit, e.g. Keithley 2636A, Yokogawa GS820, virtual tunnel electronic
    <IVD> = qkit.instruments.create('<IVD>', '<driver name>', address='<GBIP address>', reset=<bool>)
	tr = transport.transport(IV_Device=<IVD>)

Options:
--------
* usage of different bias modes possible:
  * current bias and voltage sense with one channel
	IVD.set_sweep_mode(1)
  * voltage bias and current sense with one channel
	IVD.set_sweep_mode(2)
  * voltage bias and voltage sense with two different channels to use external tunnel electronic
    initialize with
      <SMU> = qkit.instruments.create('<SMU>', 'Keithley', address='<GBIP address>', reset=<bool>)
      <IVD> = qkit.instruments.create('<IVD>', 'virtual_tunnel_electronic', SMU=<SMU>)
	  tr = transport.transport(IV_Device=<IVD>)
	IVD.set_sweep_mode(0)
    * external voltage biased current source and voltage amplifier (for effective current bias)
	    IVD.set_pseudo_bias_mode(0)
        IVD.set_dAdV(<val>)
        IVD.set_amp(<val>)
    * external voltage divider and current amplifier (for effective voltage bias)
        IVD.set_pseudo_bias_mode(1)
        IVD.set_dVdA(<val>)
        IVD.set_Vdiv(<val>)
* IV-curves: linear staircase sweeps where sweep subclass provides flexible trace handling
  * standard 4 quadrant sweep
	  tr.sweeps.reset_sweeps()
	  tr.add_sweep_4quadrants(start=<start>, stop=<stop>, step=<step>, offset=<offset>)
  * sequence of customized sweeps
	  tr.sweeps.add_sweep(start=<start>, stop=<stop>, step=<step>)
	  ...
  * calculates diffential resistance as numerical gradient
  	  tr.set_dVdI(<bool>)
  * averages enitre traces
      tr.set_average(<val>)
  * log function to record additional parameter (only in case of 2D and 3D scans)
	  tr.set_log_function([<func>], [<name>], [<unit>], [<dtype>])
  * landscape scan that limits the bias extrema by a envelope function to save measurement time (only in case of 2D and 3D scans)
      tr.set_landscape(<func>, <args>, <mirror>):
  * adds views to be plotted by qviewkit
* single point measurements
  * various quantities (e.g. voltage, current, resistance, ...) vs. x-parameter (e.g. time, temperature, ...)
      tr.set_xy_parameters(<x_name>, <x_func>, <x_vec>, <x_unit>, <y_name>, <y_func>, <y_unit>, <x_dt>)
  * adds customized views
      tr.set_view([<view>])

Measurement modes:
------------------
* 0D scan to take single data points
	tr.measure_xy()
* 1D scan to take single current-voltage characteristics
	tr.measure_1D()
* 2D scan to take the same current-voltage characteristics vs. x-parameter
	tr.set_x_parameters(x_vec=<x_vec>, x_coordname=<x_coordname>, x_set_obj=<x_set_obj>, x_unit=<x_unit>)
	tr.measure_2D()
* 3D scan to take the same current-voltage characteristics vs. x-parameter and y-parameter
	tr.set_x_parameters(x_vec=<x_vec>, x_coordname=<x_coordname>, x_set_obj=<x_set_obj>, x_unit=<x_unit>)
	tr.set_y_parameters(y_vec=<y_vec>, y_coordname=<y_coordname>, y_set_obj=<y_set_obj>, y_unit=<y_unit>)
	tr.measure_3D()



Submodules
----------

qkit.measure.transport.transport module
---------------------------------------

.. automodule:: qkit.measure.transport.transport
    :members:
    :undoc-members:
    :show-inheritance:


Module contents
---------------

.. automodule:: qkit.measure.transport
    :members:
    :undoc-members:
    :show-inheritance:
