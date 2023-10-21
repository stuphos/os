# XMLRPC Host-Client Provision.
# todo: move this into ph.web/networking package?
from . import config, host, client

from .config import buildConfig
from .host import HostRpc, installMarshaller
from .client import ClientRpc

from stuphos.runtime.facilities import Facility
from stuphos import log as mudlog

class HostRpcManager(Facility, HostRpc):
    NAME = 'XMLRPC::Host'

    @classmethod
    def create(self):
        config = buildConfig(None)

        mudlog('Creating XMLRPC Endpoint (port %s)' % config.port)
        installMarshaller()

        methods = self.RpcMethods.get(create = True).methods
        return self(config, methods = methods)

    def __registry_delete__(self):
        self.stop()
        # Also, signal network . . .

    def __init__(self, *args, **kwd):
        HostRpc.__init__(self, *args, **kwd)
    def __str__(self):
        return '{XmlRpc Host}\n%s' % (self.RpcMethods.get(),)

    class Manager(Facility.Manager):
        VERB_NAME = 'xmlrpc-*host-manage'
        MINIMUM_LEVEL = Facility.Manager.IMPLEMENTOR

    class RpcMethods(Facility):
        NAME = 'XMLRPC::Methods'

        def __init__(self):
            self.methods = dict()
        def __str__(self):
            return '    ' + '\n    '.join(list(self.methods.keys()))

        ##    def _listMethods(self):
        ##        return []
        ##    def _methodHelp(self, method):
        ##        return []

HostRpcManager.manage()

# Classic interface.
def getHost(create = False):
    return HostRpcManager.get(create = create)
def delHost():
    return HostRpcManager.destroy()

def getClientProxy(config = None, **kwd):
    return ClientRpc(buildConfig(config), **kwd)

def HOSTCALL(name, heartbeat = False, result = None):
    # XXX Registered methods will not survive host reload!
    # XXX This is a very non-standard interface.
    def registerRpcMethod(function):
        hot = getHost()
        if heartbeat:
            host.register_heartbeat_function(function, result, name = name)
        else:
            host.register_function(function, name = name)
        return function
    return registerRpcMethod
