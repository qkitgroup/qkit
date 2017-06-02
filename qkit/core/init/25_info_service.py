# start zmq based info_service
# on port and host defined in config/environment
# HR@KIT/2017
try: 
    import zmq
except ImportError:
    print "please install the zmq package"
    # we handle this exception again in the module
from qkit.core.lib.comm.info_service import info_service
import qkit.core.qkit as qkit

qkit.info = info_service()
#qkit.info.info("hallo welt")
