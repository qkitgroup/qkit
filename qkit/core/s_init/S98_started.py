import qkit
from qkit.core.lib import temp

#qt.flow.register_exit_handler(qt.config._do_save)
#qt.flow.register_exit_handler(qt.flow.close_gui)

qkit.flow.register_exit_handler(temp.File.remove_all)

# Clear "starting" status
qkit.flow.finished_starting()
