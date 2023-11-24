import zmq

from qkit.core.instrument_base import Instrument


class RT_MW_Switch(Instrument):
    """
    This is the remote switch client to connect to the room temperature switch.
    Initialize with:
    <name> = instruments.create('<name>', 'RT_MW_Switch', url = "tcp://rt-switch-pi.local:5000")
    """

    def __init__(self, name, url):
        Instrument.__init__(self, name, tags=['physical'])

        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(url)

        self.add_function('switch_to_position')

    def switch_to_position(self, position):
        """
        Switches to a position of the microwave switch.
        In this case, position may be either 1 or 2.
        """
        assert position in (1, 2), f"Invalid position {position}!"
        self.socket.send_string(f"S{position}")
        return self.socket.recv_string()
