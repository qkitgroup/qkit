# object_sharer.py, TCP/IP client/server for sharing python objects
# Reinier Heeres <reinier@heeres.eu>, 2010
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
import pickle
import socket
from lib.network import tcpserver
import copy
import random
import inspect
import time
import gobject

PORT = 12002
BUFSIZE = 8192

class ObjectSharer():
    '''
    The object sharer containing both client and server functions.
    '''

    TIMEOUT = 3600
    server = None

    def __init__(self):
        self._functions = {}
        self._objects = {}
        self._clients = []
        self._object_cache = {}
        self._client_cache = {}

        self._last_hid = 0
        self._last_call_id = 0
        self._return_cbs = {}
        self._return_vals = {}

        self._client_timeout = 60

        # Store callback info indexed on hid and on signam__objname
        self._callbacks_hid = {}
        self._callbacks_name = {}
        self._event_callbacks = {}

        # Buffers to store partly received packets
        self._buffers = {}
        self._send_queue = {}

    def set_client_timeout(self, timeout):
        '''
        Set time to wait for client interaction after connection.
        '''
        self._client_timeout = timeout

    def add_client(self, conn, handler):
        '''
        Add a client through connection 'conn'.
        '''
        info = self.call(conn, 'root', 'get_object', 'root',
            timeout=self._client_timeout)
        if info is None:
            logging.warning('Unable to get client root object')
            return None
        client = ObjectProxy(conn, info)
        self._clients.append(client)
        name = client.get_instance_name()
        logging.info('Added client %r, name %s', client.get_id(), name)
        self._do_event_callbacks('connect', client)
        return client

    def register_event_callback(self, event, cb):
        '''
        Register callback cb for event. Event is one of:
        - connect: client connected
        - disconnect: client disconnected
        '''

        if event in self._event_callbacks:
            self._event_callbacks[event].append(cb)
        else:
            self._event_callbacks[event] = [cb]

    def _do_event_callbacks(self, event, *args):
        if event not in self._event_callbacks:
            return
        for func in self._event_callbacks[event]:
            func(*args)

    def remove_client(self, client):
        if client in self._clients:
            del self._clients[self._clients.index(client)]

        self._do_event_callbacks('disconnected', client)

    def _client_disconnected(self, conn):
        for client in self._clients:
            if client.get_connection() == conn:
                logging.warning('Client disconnected, removing')
                self.remove_client(client)
                break

        if conn in self._send_queue:
            del self._send_queue[conn]

    def get_clients(self):
        return self._clients

    def generate_objname(self):
        return 'obj_%d' % (random.randint(0, 1e6), )

    def get_objects(self):
        return self._objects

    def add_object(self, object, replace=False):
        if not isinstance(object, SharedObject):
            logging.error('Not a shareable object')
            return False

        objname = object.get_shared_name()
        if objname in self._objects:
            if not replace:
                logging.error('Object with name %s already exists', objname)
                return False
            else:
                logging.info('Object with name %s exists, replacing', objname)

        self._objects[objname] = object
        if objname is not 'root':
            self._objects['root'].emit('object-added', objname)

        return True

    def remove_object(self, objname):
        if objname in self._objects:
            del self._objects[objname]
            self._objects['root'].emit('object-removed', objname)

    def _get_full_object_name(self, client, objname):
        if ':' in objname:
            return objname
        else:
            return '%s:%s' % (client.get_instance_name(), objname)

    def _get_object_from(self, client, objname):
        info = client.get_object(objname)
        proxy = ObjectProxy(client.get_connection(), info)
        self._object_cache[objname] = proxy

        fullname = self._get_full_object_name(client, objname)
        if objname != fullname:
            self._object_cache[objname] = proxy

        return proxy

    def find_remote_object(self, objname):
        '''
        Locate a shared object. Search with connected clients.
        '''

        # Remote objects which have a local proxy
        if objname in self._object_cache:
            return self._object_cache[objname]

        hostname = None
        if ':' in objname:
            parts = objname.split(':')
            if len(parts) != 2:
                return None
            hostname = parts[0]
            objname = parts[1]

        # Cached names of objects on remote clients
        for client, object_names in self._client_cache.iteritems():

            # Request from any client or specific one
            if hostname is not None and hostname != client.get_instance_name():
                continue

            if objname in object_names:
                obj = self._get_object_from(client, objname)
                if obj is not None:
                    return obj

        # Full search
        for client in self._clients:

            # Request from any client or specific one
            if hostname is not None and hostname != client.get_instance_name():
                continue

            names = client.list_objects()
            if names is None:
                continue

            self._client_cache[client] = names
            if objname in names:
                obj = self._get_object_from(client, objname)
                if obj is not None:
                    return obj

        return None

    def find_object(self, objname):
        '''
        Locate a shared object. Search locally first and then with connected
        clients.
        '''

        logging.debug('Finding shared object %s', objname)

        parts = objname.split(':')
        if len(parts) > 2:
            return None

        elif len(parts) == 2:

            # Only look locally
            if parts[0] == root.get_instance_name():
                return self._objects.get(parts[1], None)

            # Find this anywhere
            if parts[0] == '':
                objname = parts[1]

        # Local objects
        if objname in self._objects:
            return self._objects[objname]

        return self.find_remote_object(objname)

    def _pickle_packet(self, info, data):
        try:
            retdata = pickle.dumps((info, data))
        except Exception, e:
            msg = 'Unable to encode object: %s' % str(e)
            retdata = pickle.dumps((info, msg))
        return retdata

    def _unpickle_packet(self, data):
        try:
            return pickle.loads(data)
        except Exception, e:
            logging.warning('Unable to decode object: %s [%r]', str(e), data)
            raise e

    def _send_return(self, conn, callid, retval):
        logging.debug('Returning for call %d: %r', callid, retval)
        retinfo = ('return', callid)
        retdata = self._pickle_packet(retinfo, retval)
        self.send_packet(conn, retdata)

    def handle_data(self, conn, data):
        '''
        Handle incoming data from a connection and produce packets in the
        packet queue. If a response is not expected, process the packet
        immediately.
        '''

        if conn not in self._buffers:
            self._buffers[conn] = ''

        self._buffers[conn] = self._buffers[conn] + data

        # Decode complete packets
        while len(self._buffers[conn]) >= 6:
            b = self._buffers[conn]

            if b[0] != 'Q' and b[1] != 'T':
                self._buffers[conn] = ''
                logging.warning('Packet magic missing, dumping data')
                return None

            datalen = (ord(b[2]) << 24) + (ord(b[3]) << 16) + (ord(b[4]) << 8)  + ord(b[5])
            if len(b) < datalen + 6:
                logging.debug('Incomplete packet received')
                return None

            packet = b[6:6+datalen]
            self._buffers[conn] = b[6+datalen:]

            try:
                packet = self._unpickle_packet(packet)
            except Exception, e:
                logging.warning('Unable to unpickle packet')
                return

            self.handle_packet(conn, packet)

    def handle_packet(self, conn, packet):
        '''
        Process an incoming packet
        '''

        info, callinfo = packet
        logging.debug('Handling packet %r', info)

        if info[0] == 'return':
            # (a)synchronous function reply
            callid = info[1]
            if callid not in self._return_cbs:
                logging.warning('Return received for unknown call %d', callid)
                return
            func = self._return_cbs[callid]
            del self._return_cbs[callid]
            func(callinfo)
            return

        elif info[0] not in ('call', 'signal'):
            logging.warning('Invalid request: %r, %r', info, callinfo)
            return False

        (objname, funcname, args, kwargs) = callinfo
        logging.debug('Handling: %s.%s(%r, %r)', objname, funcname, args, kwargs)
        if objname not in self._objects:
            msg = 'Object %s not available' % objname
            logging.warning(msg)
            if info[0] != 'signal':
                self._send_return(conn, info[1], ValueError(msg))
            return None

        obj = self._objects[objname]
        func = getattr(obj, funcname)
        try:
            ret = func(*args, **kwargs)
        except Exception, e:
            ret = e

        if info[0] == 'signal':
            # No need to send return
            return

        self._send_return(conn, info[1], ret)

    def _do_send_raw(self, conn, data):
        try:
            ret = conn.send(data)
        except socket.error, e:
            if e.errno not in (10035, ):
                logging.warning('Send exception (%s), assuming client disconnected', e)
                self._client_disconnected(conn)
                return -1
            ret = 0

        return ret

    def _process_send_queue(self):
        '''
        Process send queue on a per connection basis.
        '''

        for conn in self._send_queue.keys():
            datalist = self._send_queue[conn]
            while len(datalist) > 0:
                nsent = self._do_send_raw(conn, datalist[0])

                # Ok
                if nsent == len(datalist[0]):
                    del datalist[0]

                # Failed, signals disconnection so remove send queue
                elif nsent == -1:
                    if conn in self._send_queue:
                        del self._send_queue[conn]
                    break

                # Partially sent
                else:
                    datalist[0] = datalist[0][nsent:]
                    break

        return True

    def send_packet(self, conn, data):
        dlen = len(data)
        if dlen > 0xffffffffL:
            logging.error('Trying to send too long packet: %d', dlen)
            return -1

        tosend = 'QT%c%c%c%c' % ((dlen&0xff000000)>>24, \
            (dlen&0x00ff0000)>>16, (dlen&0x0000ff00)>>8, (dlen&0x000000ff))
        tosend += data

        if conn not in self._send_queue:
            self._send_queue[conn] = []
        self._send_queue[conn].append(tosend)
        self._process_send_queue()

    def _call_cb(self, callid, val):
        if callid in self._return_vals:
            logging.warning('Received late reply for call %d', callid)
            del self._return_vals[callid]
        else:
            self._return_vals[callid] = val

    def call(self, conn, objname, funcname, *args, **kwargs):
        '''
        Call a function through connection 'conn'
        '''

        is_signal = kwargs.pop('signal', False)
        timeout = kwargs.pop('timeout', self.TIMEOUT)
        blocking = ('callback' not in kwargs and not is_signal)

        if not is_signal:
            self._last_call_id += 1
            callid = self._last_call_id
            cb = kwargs.pop('callback', None)
            if cb is not None:
                self._return_cbs[callid] = cb
            else:
                self._return_cbs[callid] = lambda val: self._call_cb(callid, val)

            info = ('call', callid)
        else:
            cb = None
            info = ('signal', )

        logging.debug('Calling %s.%s(%r, %r), info=%r, blocking=%r', objname, funcname, args, kwargs, info, blocking)

        callinfo = (objname, funcname, args, kwargs)
        cmd = self._pickle_packet(info, callinfo)
        start_time = time.time()
        self.send_packet(conn, cmd)

        if not blocking:
            return

        # Wait for return
        while time.time() - start_time < timeout:
            if callid in self._return_vals:
                break

            # Don't depend on a main loop to receive data while blocking
            import select
            lists = select.select([conn], [], [], 0.1)
            if len(lists[0]) > 0:
                try:
                    data = conn.recv(BUFSIZE)
                except:
                    # Cope with strange windows errors?
                    time.sleep(0.002)
                    continue

                if len(data) == 0:
                    self._client_disconnected(conn)
                    return
                self.handle_data(conn, data)
            else:
                time.sleep(0.002)

        if callid in self._return_vals:
            ret = self._return_vals[callid]
            del self._return_vals[callid]
            if isinstance(ret, Exception):
                raise Exception('Remote error: %s' % str(ret))
            return ret
        else:
            logging.warning('Blocking call %d timed out', callid)
            self._return_vals[callid] = None    # Mark as timed out

        return None

    def connect(self, objname, signame, callback, *args, **kwargs):
        '''
        Called by ObjectProxy instances to register a callback request.
        '''
        self._last_hid += 1
        info = {
                'hid': self._last_hid,
                'object': objname,
                'signal': signame,
                'function': callback,
                'args': args,
                'kwargs': kwargs,
        }

        self._callbacks_hid[self._last_hid] = info
        name = '%s__%s' % (objname, signame)
        if name in self._callbacks_name:
            self._callbacks_name[name].append(info)
        else:
            self._callbacks_name[name] = [info]

        return self._last_hid

    def disconnect(self, hid):
        if hid in self._callbacks_hid:
            del self._callbacks_hid[hid]

        for name, info_list in self._callbacks_name.iteritems():
            for index, info in enumerate(info_list):
                if info['hid'] == hid:
                    del self._callbacks_name[name][index]
                    break

    def emit_signal(self, objname, signame, *args, **kwargs):
        logging.debug('Emitting %s(%r, %r) for %s to %d clients',
                signame, args, kwargs, objname, len(self._clients))

        kwargs['signal'] = True
        for client in self._clients:
            client.receive_signal(objname, signame, *args, **kwargs)

    def receive_signal(self, objname, signame, *args, **kwargs):
        logging.debug('Received signal %s(%r, %r) from %s',
                signame, args, kwargs, objname)

        ncalls = 0
        start = time.time()
        name = '%s__%s' % (objname, signame)
        if name in self._callbacks_name:
            info_list = self._callbacks_name[name]
            for info in info_list:
                try:
                    fargs = list(args)
                    fargs.extend(info['args'])
                    fkwargs = kwargs.copy()
                    fkwargs.update(info['kwargs'])
                    info['function'](*fargs, **fkwargs)
                    ncalls += 1
                except Exception, e:
                    logging.warning('Callback failed: %s', str(e))

        end = time.time()
        logging.debug('Did %d callbacks in %.03fms for sig %s',
                ncalls, (end - start) * 1000, signame)

    def close_sockets(self):
        logging.debug('Closing sockets')
        if SharedObject.server is None:
            SharedObject.server.close()
            SharedObject.server = None
        for client in self._clients:
            client.get_connection().close()

class SharedObject():
    '''
    Server side object that can be shared and emit signals.
    '''

    def __init__(self, name, replace=False):
        '''
        Create SharedObject, arguments:
        name:       shared name
        replace:    whether to replace object when it already exists
        '''

        self.__last_hid = 1
        self.__callbacks = {}
        self.__name = name
        helper.add_object(self, replace=replace)

    def get_shared_name(self):
        return self.__name

    def emit(self, signal, *args, **kwargs):
        helper.emit_signal(self.__name, signal, *args, **kwargs)

    def connect(self, signame, callback, *args):
        self.__last_hid += 1
        self.__callbacks[self.__last_hid] = {
                'signal': signame,
                'function': callback,
                'args': args,
                }
        return self.__last_hid

    def disconnect(self, hid):
        if hid in self.__callbacks:
            del self.__callbacks[hid]

class SharedGObject(gobject.GObject, SharedObject):

    def __init__(self, name, replace=False, idle_emit=False):
        logging.debug('Creating shared Gobject: %r', name)
        self.__hid_map = {}
        self._do_idle_emit = idle_emit
        gobject.GObject.__init__(self)
        SharedObject.__init__(self, name, replace=replace)

    def connect(self, signal, *args, **kwargs):
        hid = SharedObject.connect(self, signal, *args, **kwargs)
        ghid = gobject.GObject.connect(self, signal, *args, **kwargs)
        self.__hid_map[ghid] = hid
        return ghid

    def _idle_emit(self, signal, *args, **kwargs):
        try:
            gobject.GObject.emit(self, signal, *args, **kwargs)
        except Exception, e:
            print 'Error: %s' % e

    def emit(self, signal, *args, **kwargs):
        # The 'None' here is the 'sender'
        SharedObject.emit(self, signal, None, *args, **kwargs)
        if self._do_idle_emit:
            gobject.idle_add(self._idle_emit, signal, *args, **kwargs)
        else:
            return gobject.GObject.emit(self, signal, *args, **kwargs)

    def disconnect(self, ghid):
        if ghid not in self.__hid_map:
            return
        hid = self.__hid_map[ghid]
        SharedObject.disconnect(self, hid)
        del self.__hid_map[ghid]
        return gobject.GObject.disconnect(self, ghid)

class _FunctionCall():

    def __init__(self, conn, objname, funcname, share_options):
        self._conn = conn
        self._objname = objname
        self._funcname = funcname

        if share_options is None:
            self._share_options = {}
        else:
            self._share_options = share_options

        self._cached_result = None

    def __call__(self, *args, **kwargs):
        cache = self._share_options.get('cache_result', False) 
        if cache and self._cached_result is not None:
            return self._cached_result

        ret = helper.call(self._conn, self._objname, self._funcname, *args, **kwargs)
        if cache:
            self._cached_result = ret
        return ret

class ObjectProxy():
    '''
    Client side object proxy.
    '''

    def __init__(self, conn, info):
        self.__conn = conn
        self.__name = info['name']
        self.__new_hid = 1
        self.__callbacks = {}

        for funcname, share_options in info['functions']:
            setattr(self, funcname, _FunctionCall(self.__conn, self.__name, funcname, share_options))

        for propname in info['properties']:
            setattr(self, propname, 'blaat')

    def get_connection(self):
        return self.__conn

    def connect(self, signame, func):
        return helper.connect(self.__name, signame, func)

    def disconnect(self, hid):
        return helper.disconnect(hid)

def cache_result(f):
    f._share_options = {'cache_result': True}
    return f

class RootObject(SharedObject):

    def __init__(self, name):
        SharedObject.__init__(self, name)
        self._objects = helper.get_objects()
        self._id = random.randint(0, 1e6)
        self._instance_name = ''

    def set_instance_name(self, name):
        self._instance_name = name

    @cache_result
    def get_instance_name(self):
        return self._instance_name

    def get_object(self, objname):
        if objname not in self._objects:
            raise Exception('Object not found')

        obj = self._objects[objname]
        props = []
        funcs = []
        for key, val in inspect.getmembers(obj):
            if key.startswith('_') or key in ObjectProxy.__dict__:
                continue
            elif callable(val):
                if hasattr(val, '_share_options'):
                    opts = val._share_options
                else:
                    opts = None
                funcs.append((key, opts))
            else:
                props.append(key)

        info = {
            'name': objname,
            'properties': props,
            'functions': funcs
        }
        return info

    def receive_signal(self, objname, signame, *args, **kwargs):
        helper.receive_signal(objname, signame, *args, **kwargs)

    def list_objects(self):
        return self._objects.keys()

    @cache_result
    def get_id(self):
        return self._id

    def hello_world(self, *args, **kwargs):
        return 'Hello world!'

    def hello_exception(self):
        1 / 0

class PythonInterpreter(SharedObject):

    def __init__(self, name, namespace={}):
        SharedObject.__init__(self, name)
        self._namespace = namespace

    def cmd(self, cmd):
        retval = eval(cmd, self._namespace, self._namespace)
        return retval

class _DummyHandler(tcpserver.GlibTCPHandler):

    def __init__(self, sock, client_address, server):
        tcpserver.GlibTCPHandler.__init__(self, sock, client_address, server,
                packet_len=True)
        helper.add_client(self.socket, self)

    def handle(self, data):
        if len(data) > 0:
            data = helper.handle_data(self.socket, data)
        return True

_flush_queue_hid = None

def setup_glib_flush_queue():
    global _flush_queue_hid
    if _flush_queue_hid is not None:
        return
    _flush_queue_hid = gobject.timeout_add(2000, helper._process_send_queue)

def start_glibtcp_server(port=PORT):
    try:
        server = tcpserver.GlibTCPServer(('', port), _DummyHandler, '127.0.0.1')
        SharedObject.server = server
        setup_glib_flush_queue()
        return True
    except Exception, e:
        logging.warning('Failed to start sharing server: %s', str(e))
        return False

def start_glibtcp_client(host, port=PORT, nretry=1):
    while nretry > 0:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            handler = _DummyHandler(sock, 'client', 'server')
            setup_glib_flush_queue()
            return True
        except Exception, e:
            logging.warning('Failed to start sharing client: %s', str(e))
            if nretry > 0:
                logging.info('Retrying in 2 seconds...')
                time.sleep(2)
    return False

helper = ObjectSharer()
root = RootObject('root')

