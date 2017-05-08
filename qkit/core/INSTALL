################
INSTALLING QTLAB
################

QTlab does not have an installer. It just needs to be copied to the local hard drive. It does have numerous dependencies on 3rd party software. For more information on the dependencies see below.

#############
RUNNING QTLAB
#############

win32:
qtlab.bat
(assumes python installed in c:\python2X, change if needed)

linux:
./qtlab

############
DEPENDENCIES
############

The dependencies are split into two groups:

A) python and python libraries.
    These always need to be installed separately by the user on the computer where QTlab will be running.

B) other programs.
    These programs generally do not need to be installed, but just have to 'be there'. Adding their locations to the PATH will make sure that QTLab can find the necessary files. This you can do any way you like, below we will describe one way as an example.

=group A=

1) python (2.6.x or 2.7.x)

    NOTE: python is in transition to an new and incompatible version 3.x. Python 2.7 is the last of the 2.x series and will likely be supported for a very long time. It contains many features that should make the transition smooth (if we will ever make it). We will stick with 2.7.x until all the dependencies have switched to 3.x.
    URL: python.org

2a) numpy (>=1.4.0)
2b) scipy (>=0.7.1) (optional)

    numpy gives numerical-math functionality (similar to matlab)
    scipy has many math routines (like fitting), based on numpy.
    URL: scipy.org (for both numpy and scipy)

3a) ipython (>=0.10)
3b) pyreadline (>=1.5)

    enhanced interactive shell for python
    pyreadline is needed by ipython for 'tab'-completion
    URL: ipython.scipy.org (pyreadline in download dir)

    NOTE: it is highly recommended to use ipython >0.11 as it
    contains a much more robust interactive gui implementation.

4)  pygtk-all-in-one (>=2.24.0)

    containing pygtk, pygobject, pycairo and gtk-runtime.

    libraries used for creating graphical interfaces.
    URL: pygtk.org

5) pyvisa (1.3)

    library for communication with GPIB/USB/SERIAL instruments
    URL: pyvisa.sourceforge.net/

=Group B=

1) gnuplot (>=4.3)

    plotting in QTlab is done using the gnuplot program.
    URL: gnuplot.info

2) Console2 (>=2.00)

    an enhanced interface for the windows 'cmd'-terminal
    URL: sourceforge.net/projects/console

    NOTE: Don't get the _src version, but just the
    regular binary version from the files list.

To 'install' the programs of group B, we recommend the following.

a) Make a folder '3rd_party' inside the QTLab folder.

b) Both gnuplot and Console2 don't have an installer. They are just copied to the 3rd_party folder.

c) Make sure that QTlab can find the executables. In stead of changing the PATH permanently (in system => advanced => system_variables), we prefer to add them on the commandline. Adjust the qtlab.bat file to correspond to the location of your '3rd_party' folder. If you did it exactly as recommended here, you can just uncomment the four 'SET' lines. This will add the following variables to the PATH:

<path_to_gnuplot_folder>\bin
<path_to_console2_folder>\

It is important to add them to the beginning of the list (of the PATH variable), so if any other versions exist, ours will be found before.

This is it, your done. Happy measuring.
