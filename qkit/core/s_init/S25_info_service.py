from __future__ import print_function
# start zmq based info_service
# on port and host defined in config/environment
# HR@KIT/2017
import qkit

if qkit.cfg.get('load_info_service',True):
    qkit.cfg['load_info_service']=True
    try: 
        import zmq
    except ImportError:
        print("Please install the zmq package")
        # we handle this exception again in the module
    
    from qkit.core.lib.com.info_service import info_service
    import qkit.core.qcorekit as qckit
    
    qkit.info = info_service()
    qckit.info = qkit.info
    #qckit.info.info("hallo welt")
else:
    # dummy info service
    def info_service(msg): pass
    qkit.info = info_service()
    qckit.info = qkit.info