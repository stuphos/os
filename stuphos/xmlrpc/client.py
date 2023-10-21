# Client Provision.
from xmlrpc.client import ServerProxy
import socket

CLIENT_TIMEOUT = 20
CLIENT_URL_FORMAT = 'http://%(hostname)s:%(port)d/RPC2'

def getClientUrl(hostname, port):
    return CLIENT_URL_FORMAT % dict(hostname = hostname,
                                    port = port)

class ClientRpc:
    def __init__(self, config, timeout = CLIENT_TIMEOUT, verbose = False):
        # This should be configurable via client command-line.
        self.timeout = timeout
        self.proxy = ServerProxy(getClientUrl(config.hostname,
                                              config.port),

                                 verbose = verbose)

    def __call__(self, name, *args, **kwd):
        proc = getattr(self.proxy, name, None)

        try: return doSettingTimeout(self.timeout, proc, *args, **kwd)
        except socket.error as e:
            if e.args[0] != ECONNREFUSED:
                raise

def doSettingTimeout(timeout, function, *args, **kwd):
    # Dirty hack?  Presumably the rpc call is when the socket is made.
    if timeout is None:
        return function(*args, **kwd)

    previous = socket.getdefaulttimeout()
    socket.setdefaulttimeout(timeout)
    try: return function(*args, **kwd)
    finally: socket.setdefaulttimeout(previous)
