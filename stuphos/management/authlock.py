from twisted.internet import protocol, reactor
from twisted.application import internet, service
from twisted.protocols import amp

class MsgServer2Portal(amp.Command):
    """
    Message Server -> Portal

    """

    key = "MsgServer2Portal"
    arguments = [(b"packed_data", Compressed())]
    errors = {Exception: b"EXCEPTION"}
    response = []

class AMPMultiConnectionProtocol(amp.AMP):
    """
    AMP protocol that safely handle multiple connections to the same
    server without dropping old ones - new clients will receive
    all server returns (broadcast). Will also correctly handle
    erroneous HTTP requests on the port and return a HTTP error response.

    """

    def __init__(self, *args, **kwargs):
        """
        Initialize protocol with some things that need to be in place
        already before connecting both on portal and server.

        """
        super(AMPMultiConnectionProtocol, self).__init__(*args, **kwargs)

    def _commandReceived(self, box):
        """
        This overrides the default Twisted AMP error handling which is not
        passing enough of the traceback through to the other side. Instead we
        add a specific log of the problem on the erroring side.

        """

    def dataReceived(self, data):
        """
        Handle non-AMP messages, such as HTTP communication.
        """

    def makeConnection(self, transport):
        """
        Swallow connection log message here. Copied from original
        in the amp protocol.

        """

    def connectionMade(self):
        """
        This is called when an AMP connection is (re-)established. AMP calls it on both sides.

        """

    def connectionLost(self, reason):
        """
        We swallow connection errors here. The reason is that during a
        normal reload/shutdown there will almost always be cases where
        either the portal or server shuts down before a message has
        returned its (empty) return, triggering a connectionLost error
        that is irrelevant. If a true connection error happens, the
        portal will continuously try to reconnect, showing the problem
        that way.
        """

    def errback(self, e, info):
        """
        Error callback.
        Handles errors to avoid dropping connections on server tracebacks.

        Args:
            e (Failure): Deferred error instance.
            info (str): Error string.

        """

    def data_in(self, packed_data):
        """
        Process incoming packed data.

        Args:
            packed_data (bytes): Pickled data.
        Returns:
            unpaced_data (any): Unpickled package

        """

    def broadcast(self, command, sessid, **kwargs):
        """
        Send data across the wire to all connections.

        Args:
            command (AMP Command): A protocol send command.
            sessid (int): A unique Session id.

        Returns:
            deferred (deferred or None): A deferred with an errback.

        Notes:
            Data will be sent across the wire pickled as a tuple
            (sessid, kwargs).

        """

    def send_FunctionCall(self, modulepath, functionname, *args, **kwargs):
        """
        Access method called by either process. This will call an arbitrary
        function on the other process (On Portal if calling from Server and
        vice versa).

        Inputs:
            modulepath (str) - python path to module holding function to call
            functionname (str) - name of function in given module
            *args, **kwargs will be used as arguments/keyword args for the
                            remote function call
        Returns:
            A deferred that fires with the return value of the remote
            function call

        """

    @FunctionCall.responder
    @catch_traceback
    def receive_functioncall(self, module, function, func_args, func_kwargs):
        """
        This allows Portal- and Server-process to call an arbitrary
        function in the other process. It is intended for use by
        plugin modules.

        Args:
            module (str or module): The module containing the
                `function` to call.
            function (str): The name of the function to call in
                `module`.
            func_args (str): Pickled args tuple for use in `function` call.
            func_kwargs (str): Pickled kwargs dict for use in `function` call.

        """

class AMPServerClientProtocol(amp.AMPMultiConnectionProtocol):
    """
    This protocol describes the Server service (acting as an AMP-client)'s communication with the
    Portal (which acts as the AMP-server)

    """

    # sending AMP data

    def connectionMade(self):
        """
        Called when a new connection is established.

        """

    def send_MsgServer2Portal(self, session, **kwargs):
        """
        Access method - executed on the Server for sending data
            to Portal.

        Args:
            session (Session): Unique Session.
            kwargs (any, optiona): Extra data.

        """
        return self.data_to_portal(MsgServer2Portal, session.sessid, **kwargs)

    # @amp.MsgStatus.responder
    # def server_receive_status(self, question):
    #     return {"status": "OK"}

    # @MsgPortal2Server.responder
    # # @amp.catch_traceback
    # def server_receive_msgportal2server(self, packed_data):
    #     """
    #     Receives message arriving to server. This method is executed
    #     on the Server.

    #     Args:
    #         packed_data (str): Data to receive (a pickled tuple (sessid,kwargs))

    #     """
    #     return {}

    # @amp.AdminPortal2Server.responder
    # @amp.catch_traceback
    # def server_receive_adminportal2server(self, packed_data):
    #     """
    #     Receives admin data from the Portal (allows the portal to
    #     perform admin operations on the server). This is executed on
    #     the Server.

    #     Args:
    #         packed_data (str): Incoming, pickled data.

    #     """
    #     return {}

class AMPClientFactory(protocol.ReconnectingClientFactory):
    """
    This factory creates an instance of an AMP client connection. This handles communication from
    the be the Evennia 'Server' service to the 'Portal'. The client will try to auto-reconnect on a
    connection error.

    """

    protocol = AMPServerClientProtocol
    # Initial reconnect delay in seconds.
    initialDelay = 1
    factor = 1.5
    maxDelay = 1
    noisy = False

    def __init__(self, server):
        """
        Initializes the client factory.

        Args:
            server (server): server instance.

        """

    def startedConnecting(self, connector):
        """
        Called when starting to try to connect to the Portal AMP server.

        Args:
            connector (Connector): Twisted Connector instance representing
                this connection.

        """

    def buildProtocol(self, addr):
        """
        Creates an AMPProtocol instance when connecting to the AMP server.

        Args:
            addr (str): Connection address. Not used.

        """
        # self.resetDelay()
        self.amp_protocol = AMPServerClientProtocol()
        self.amp_protocol.factory = self
        return self.amp_protocol

    def clientConnectionLost(self, connector, reason):
        """
        Called when the AMP connection to the MUD server is lost.

        Args:
            connector (Connector): Twisted Connector instance representing
                this connection.
            reason (str): Eventual text describing why connection was lost.

        """

    def clientConnectionFailed(self, connector, reason):
        """
        Called when an AMP connection attempt to the MUD server fails.

        Args:
            connector (Connector): Twisted Connector instance representing
                this connection.
            reason (str): Eventual text describing why connection failed.

        """

factory = AMPClientFactory(None)

amp_service = internet.TCPClient(AMP_HOST, AMP_PORT, factory)
amp_service.setName("ServerAMPClient")

application = service.Application("phApp")

services = service.MultiService()
services.setServiceParent(application)

services.addService(amp_service)

def sendCommand(protocol, command, data):
    return protocol.callRemote(command, packed_data=amp.dumps(data)).addErrback(
        protocol.errback, command.key
    )

def sendAppCommand(command, data):
    return sendCommand(factory.amp_protocol, command, data)

def send_MsgServer2Portal(data):
    return sendAppCommand(MsgServer2Portal, data)


def userCreated(user, email):
    '''
    [Network]
    user-replication: stuphos.management.authlock.userCreated

    '''

    send_MsgServer2Portal(('user-created', user.username, email))
