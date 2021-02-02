#
# This file handles external requests to the radiall switch pi
# S1@KIT2020
# Based on TIP 2.0 by HR@KIT 2019
#
import logging
import zmq
import zmq.auth
from switch import Switch


def _isfloat(argument):
    try:
        float(argument)
        return True
    except ValueError:
        return False


def parse_request(request, switch):
    """
    The following commands are available. They are not case sensitive and can be abbreviated up to the first letter. Sub-commands and parameters are
    separated by a slash.
    All switch and port numbering starts with 1, i.e. switches 1,2 ports 1-6
    
    SET/switch/port: e.g. SET/1/3 switches switch No 1 to Port 3 (and resets the other ports, if needed)
    
    ENABLE/switch/port: activate the specific port. This does not check wether you have multiple ports enabled simultaneously.
    DISABLE/switch/port: disables (resets) the specific port.
    
    GET/switch: returns a list of currently activated ports.
    GET/switch/port: returns True if the specific port is activated.
    
    RESET/switch: Perform a full reset of all ports (sequentially) for the given switch
    
    SET/LENGTH/length: e.g. SET/LENGTH/0.5 sets the current pulse time to 0.5s
    SET/LENGTH/length/switch: SET/LENGTH/0.2/1 sets pulse time to 0.2s for switch 1
    GET/LENGTH: returns the current pulse times
    
    """
    logging.info(request)
    
    cmds = request.strip('/').split("/")
    cmds = [cmd.strip().lower() for cmd in cmds]
    try:
        if "set".find(cmds[0]) == 0:
            if _isfloat(cmds[1]) and _isfloat(cmds[2]):
                if int(cmds[1]) in [1, 2] and int(cmds[2]) in [1, 2, 3, 4, 5, 6]:
                    switch.switch_to(int(cmds[1])-1, int(cmds[2])-1)
                    return True
                else:
                    return "Error: Argument 1 needs to be [1|2], argument 2 in [1,6]"
            elif "length".find(cmds[1]) == 0 and _isfloat(cmds[2]):
                if len(cmds) == 4 and _isfloat(cmds[3]) and int(cmds[3]) in [1,2]:
                    switch.set_pulse_length(length=float(cmds[2]),switch=int(cmds[3]))
                else:
                    switch.set_pulse_length(float(cmds[2]))
                return True
        elif "enable".find(cmds[0]) == 0 and _isfloat(cmds[1]) and _isfloat(cmds[2]):
            if int(cmds[1]) in [1, 2] and int(cmds[2]) in [1, 2, 3, 4, 5, 6]:
                switch.enable(int(cmds[1])-1, int(cmds[2])-1)
                return True
            else:
                return "Error: Argument 1 needs to be [1|2], argument 2 in [1,6]"
        elif "disable".find(cmds[0]) == 0 and _isfloat(cmds[1]) and _isfloat(cmds[2]):
            if int(cmds[1]) in [1, 2] and int(cmds[2]) in [1, 2, 3, 4, 5, 6]:
                switch.disable(int(cmds[1])-1, int(cmds[2])-1)
                return True
            else:
                return "Error: Argument 1 needs to be [1|2], argument 2 in [1,6]"
        elif "reset".find(cmds[0]) == 0:
            if len(cmds) == 1:
                switch.reset_all(None)
                return True
            elif int(cmds[1]) in [1, 2]:
                switch.reset_all(int(cmds[1])-1)
                return True
            else:
                return "Error: Argument 1 needs to be [1|2]"
        elif "get".find(cmds[0]) == 0:
            if _isfloat(cmds[1]):
                if len(cmds) == 2 and int(cmds[1]) in [1, 2]:
                    return [s+1 for s in switch.get_switch_position(int(cmds[1])-1)]
                elif int(cmds[1]) in [1, 2] and _isfloat(cmds[2]) and int(cmds[2]) in [1, 2, 3, 4, 5, 6]:
                    return int(cmds[2])-1 in switch.get_switch_position(int(cmds[1])-1)
                else:
                    return "Error: Argument 1 needs to be [1|2], argument 2 in [1,6] or not present"
            elif "length".find(cmds[1]) == 0:
                return switch.get_pulse_length()
        else:
            return "invalid syntax : " + request
        return "Request not processed: " + request
    except Exception as e:
        return "Command error. Your command '" + request + "'. Error: '" + str(e) + "'."


def serve_requests():
    context = zmq.Context()
    
    # # FIXME: authentication is not working in the moment
    # auth = ThreadAuthenticator(context, log=logging.getLogger())
    # auth.start()
    # auth.allow('127.0.0.1')
    # auth.allow('localhost')
    # set_allowed_IPs(auth)
    
    socket = context.socket(zmq.REP)
    socket.zap_domain = b'global'
    socket.bind("tcp://*:5000")
    
    switch = Switch()
    
    while True:
        #  Wait for next request from client
        message = socket.recv_string()
        logging.debug("Received request: %s" % message)
        socket.send_string(str(parse_request(message, switch)))

# def set_allowed_IPs(auth):
#     for IP in str(config['system'].get('allowed_ips', "")).split(" "):
#         logging.info("Add " + IP + " to allowed IP list.")
#         auth.allow(IP)

if __name__ == "__main__":
    print("Switch server starting")
    serve_requests()
