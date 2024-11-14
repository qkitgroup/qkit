# environment
qkit.config.environment -- setting up the config dict for the qkit measurement suite

### Features:
  * upon import a config dictionary, called via "qkit.cfg" will be created with all
  needed entry keys filled with standard / dummy entries
  * this config allows access to all computer-specific settings
  
### Operation:
  * all scripts should have an "import qkit" command to ensure the accessibility to this config
  dict
  * all local entries specifically for each computer are stored in the local.py-config dict. It
  gets loaded during startup and will not be shared over the git (see "local.py_template" as expampe)