# This file contains user-specific settings for qtlab.
# It is run as a regular python script.

# Do not change the following line unless you know what you are doing
config.remove([
			'datadir',
			'startdir',
			'startscript',
			'user_ins_dir',
			])
            # YS: additionally in original userconfig (removed userconfig_old.py):
            # 'scriptdirs', 'startgui', 'gnuplot_terminal'. Not there: 'startscript'

# QTLab instance name and port for networked operation
config['instance_name'] = 'qtlab_main'
config['port'] = 12002

# A list of allowed IP ranges for remote connections
config['allowed_ips'] = (
	'172.22.197.*',
	'10.22.197.*',
)
  
# Start instrument server to share with instruments with remote QTLab?
config['instrument_server'] = True
  
## This sets a default location for data-storage
config['datadir'] = r'd:'

## This sets a default directory for qtlab to start in
#config['startdir'] = r'c:\\qtlab-15a460b_notebook'
config['startdir'] = r'C:\\qkit\qkit\core' # YS: qtlab ripoff now in qkit/core - should not be hardcoded

## This sets a default script to run after qtlab started
#config['startscript'] = 'c:\\qtlab_addons\\0_create_instruments_UFO.py' # AS: Removed overhauled imports

## A default script (or list of scripts) to run when qtlab closes
#config['exitscript'] = []       #e.g. ['closescript1.py', 'closescript2.py']

# Add directories containing scripts here. All scripts will be added to the
# global namespace as functions.
config['scriptdirs'] = [
		#r'c:\\qtlab_addons\\scripts', # AS: Removed overhauled imports
		r'c:\\qkit',
]

## This sets a user instrument directory
## Any instrument drivers placed here will take
## preference over the general instrument drivers
config['user_insdir'] = r'c:\\qkit\\qkit\\instruments'

## For adding additional folders to the 'systm path'
## so python can find your modules
import sys
#sys.path.append(r'c:\\qtlab_addons\\scripts') AS: Removed overhauled imports
sys.path.append(r'c:\\qkit') # AS: Is this still necessary? qkit path should be an environment variable anyways
#sys.path.append('d:/folder2')

# Whether to start the GUI automatically
config['startgui'] = False # YS: deactivated, gui is removed

# Default gnuplot terminal
#config['gnuplot_terminal'] = 'x11'
#config['gnuplot_terminal'] = 'wxt'
config['gnuplot_terminal'] = 'windows'

# Enter a filename here to log all IPython commands
config['ipython_logfile'] = ''      #e.g. 'command.log'

