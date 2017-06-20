# start zmq based info_service
# on port and host defined in config/environment
# HR@KIT/2017

try: 
    import zmq
except ImportError:
    print "please install the zmq package"
    # we handle this exception again in the module
from lib.com.info_service import info_service
import qkit.core.qcorekit as qckit

qckit.info = info_service()
#qckit.info.info("hallo welt")
