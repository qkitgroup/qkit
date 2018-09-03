qkit.measure.transport package
==============================

Measurement class to take transport measurements such as current-voltage characteristics. The taken data are saved in an .h5-file. In addition, all instrument settings are saved in a .set-file and an optional measurement object is saved in a .measurement-file

Initialization:
---------------
* IV device: DC source-measure unit, e.g. Keithley 2636A, Yokogawa GS820
    <IVD> = qkit.instruments.create('<IVD>', 'Keithley', address='<GBIP address>', reset=<bool>)
	tr = transport.transport(IV_Device=<IVD>)

Options:
--------
* usage of different bias modes possible:
  * current bias and voltage sense with one channel
	IVD.set_sweep_mode(1)
  * voltage bias and current sense with one channel
	IVD.set_sweep_mode(2)
  * voltage bias and voltage sense with two different channels
	IVD.set_sweep_mode(0)
    * external voltage biased current source and voltage amplifier (for effective current bias)
	IVD.set_pseudo_bias_mode(0)
    * external voltage divider and current amplifier (for effective voltage bias)
	IVD.set_pseudo_bias_mode(1)
* sweep subclass provides flexible trace handling
  * standard 4 quadrant sweep
	tr.sweep.reset_sweeps()
	tr.add_sweep_4quadrants(start=<start>, stop=<stop>, step=<step>, offset=<offset>)
  * sequence of customized sweeps
	tr.sweep.add_sweep(start=<start>, stop=<stop>, step=<step>)
	...
* calculates diffential resistance as numerical gradient
	tr.set_dVdI(<bool>)
* log function to record additional parameter (in case of 2D and 3D scans)
	tr.set_log_function([get_T], ['temp'], ['K'], ['f'])
* adds views to be plotted by qviewkit

Measurement modes:
------------------
* 1D scan to take single current-voltage characteristics
	tr.measure_1D()
* 2D scan to take the same current-voltage characteristics for different x-parameters
	tr.set_x_parameters(x_vec=<x_vec>, x_coordname=<x_coordname>, x_set_obj=<x_set_obj>, x_unit=<x_unit>)
* 3D scan to take the same current-voltage characteristics for different x-parameters and different y-parameters
	tr.set_x_parameters(x_vec=<x_vec>, x_coordname=<x_coordname>, x_set_obj=<x_set_obj>, x_unit=<x_unit>)
	tr.set_y_parameters(y_vec=<y_vec>, y_coordname=<y_coordname>, y_set_obj=<y_set_obj>, y_unit=<y_unit>)



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
