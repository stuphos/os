# Socket Programming & Timing.
from stuphos.system import Heartbeat
from stuphos.system.core import getSystemTime

import socket
import asyncore
import asynchat
import queue

from errno import EINPROGRESS, EALREADY, EWOULDBLOCK, EISCONN

class MotherSocket(Heartbeat.Task, asyncore.dispatcher):
    BIND_ADDRESS = '0.0.0.0'
    PULSE_FREQUENCY = 0.1

    class Connection(asynchat.async_chat):
        def __init__(self, *args, **kwd):
            asynchat.async_chat.__init__(self, *args, **kwd)

        def handle_close(self):
            self.network.closeConnection(self)
            self.close()

    class IncomingConnection(Connection):
        def __init__(self, network, socket, addr):
            MotherSocket.Connection.__init__(self, sock = socket,
                                             map = network.socketMap)

            self.client_address = addr
            self.network = network

            from stuphos.system.api import game
            self.peer = game.new_peer(self) # XXX

            # This should be done in new_peer:
            self.peer.host = addr[0]
            self.peer.remote_port = addr[1]

            # Devel compatibility:
            self.peer.engine = network.engine

            # Configure chat.
            self.set_terminator('\n')
            self.buffer = ''

            # Internal Greetings/State Initialization.
            from stuphos import log as mudlog # not the same as game.mudlog..?
            mudlog('NEW CONNECTION: %r' % self)

            from stuphos.system.api import world
            self.peer.state = world.player.nanny.CON_GET_NAME

            # World Bridge.
            StuphMUD.NewIncomingPeer(self.peer)
            StuphMUD.GreetPlayer(self.peer)

        # Chat I/O.
        def collect_incoming_data(self, data):
            self.buffer += data
        def found_terminator(self):
            input = self.buffer.replace('\r', '')
            self.buffer = ""

            # todo: telnet processing -- XXX this doesn't work with terminator-based input.
            self.network.handlePlayerInput(self.peer, input)

    def __init__(self, port, address = None, frequency = None):
        self.socketMap = {}
        asyncore.dispatcher.__init__(self, map = self.socketMap)

        self.port = port
        self.address = address is None and self.BIND_ADDRESS or address

        self.frequency = frequency or self.PULSE_FREQUENCY
        self.last_pulse = None
        self.connections = []
        self.connect_q = queue.Queue()

    def activate(self, engine):
        if self.socket is None:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((self.address, self.port))
            self.listen(5)

            print('Activated %r' % self)

        engine.network = self
        self.engine = engine

    def deactivate(self, engine):
        if self.socket is not None:
            self.close()

        try:
            if engine.network is self:
                del engine.network
            if self.engine is engine:
                del self.engine
        except AttributeError:
            pass

    def perform(self, engine):
        # Todo: catch .nextTimeout => SystemError: Time moving backwards.
        # This seems to happen when the dev computer comes out of hibernation.
        try: timeout = self.nextTimeout
        except SystemError as e:
            print(f'{self.__class__.__name__}.perform: {e}')
        else:
            asyncore.loop(timeout = timeout,
                          map = self.socketMap,
                          count = 1)

            try:
                while True:
                    conn = self.connect_q.get_nowait()
                    conn.handle_connect()

            except queue.Empty:
                pass

    def getNextTimeout(self):
        now = getSystemTime()
        timeout = self.frequency
        if self.last_pulse is not None:
            # Calculate time remaining within pulse from last call.
            elapsed = now - self.last_pulse
            if elapsed < 0:
                raise SystemError('Time moving backwards! (%s)' % elapsed)

            # print 'elapsed network time:', elapsed
            self.last_pulse = now
            timeout = elapsed % self.frequency
            if not timeout:
                timeout = self.frequency

        self.last_pulse = now
        # print 'next timeout:', timeout
        return timeout

    # Override for different timeout mode.
    nextTimeout = property(getNextTimeout)

    ##    def __getattr__(self, name):
    ##        try: return self.__dict__[name]
    ##        except KeyError:
    ##            return asyncore.dispatcher.__getattr__(self, name)

    # Mother Socket Dispatcher.
    def handle_accept(self):
        (socket, addr) = self.accept()
        self.newConnection(socket, addr)

    def newConnection(self, socket, address = None):
        conn = self.IncomingConnection(self, socket, address)
        self.connections.append(conn)

    def closeConnection(self, peer):
        if peer in self.connections:
            # Error occurred before newConnection was called.
            # XXX This doesn't really make sense.. newConnection
            # should always be called (synchronously) before close...
            self.connections.remove(peer)
            StuphMUD.Disconnection(peer)

    class OutgoingConnection(Connection):
        def __init__(self, network, sock, address):
            MotherSocket.Connection.__init__(self, sock = sock,
                                             map = network.socketMap)

            if sock is None:
                self.create_socket(socket.AF_INET, socket.SOCK_STREAM)

            self.remote_address = address
            self.network = network

            # Configure chat.
            self.set_terminator('\n')
            self.buffer = ''

            from _thread import start_new_thread as nth
            nth(self.connectOpen, ())

        def connectOpen(self):
            self.connected = False
            err = self.socket.connect_ex(self.remote_address)
            # XXX Should interpret Winsock return values
            if err in (EINPROGRESS, EALREADY, EWOULDBLOCK):
                # CB: For instance EINPROGRESS on cygwin is common for
                # a successful connection (0, EISCONN), meaning that the full
                # dispatcher cycle is never completed.  If this isn't done,
                # normal asyncore.dispatcher.handle_read_event will handle the
                # connect, but it will bypass our synchronization mechanism.
                err = 0 # return
            if err in (0, EISCONN):
                self.addr = self.remote_address
                self.connected = True
                self.network.handleOutgoingConnect(self)
            else:
                raise socket.error(err, errorcode[err])

        def handle_close(self):
            self.network.closeConnection(self)
            self.close()

        def handle_connect(self):
            print('Outgoing Connection Established [%s:%s]' % self.remote_address)

        # Chat I/O.
        def collect_incoming_data(self, data):
            self.buffer += data
        def found_terminator(self):
            self.network.handleIncomingData(self, self.buffer)
            self.buffer = ""

    def openConnection(self, address = None, socket = None):
        conn = self.OutgoingConnection(self, socket, address)
        self.connections.append(conn) # Do this aft-thread?
        return conn

    def handleOutgoingConnect(self, conn):
        self.connect_q.put(conn)
    def handlePlayerInput(self, peer, input):
        peer.forceInput(input)
        if self.engine.event:
            self.engine.event += peer.handleNextInput
    def handleIncomingData(self, conn, data):
        if self.engine.event:
            self.engine.event.call(handleIncomingData, conn, data)

    def emergeInternalPeer(self, stateName = None, avatar = None):
        ##    from game.cli import Console
        ##    return Console()

        from world import peer
        from world.player.nanny import CON_GET_NAME as DEFAULT_STATE

        new = peer.create()
        new.state = stateName or DEFAULT_STATE
        if avatar:
            new.avatar = avatar

        new.engine = self.engine

        return new

def handleIncomingData(conn, data):
    # Game Inline Event.
    print('%%', data)

class FreeNetwork(MotherSocket):
    class Engine:
        pass

    nextTimeout = None
    engine = Engine()

    def run(self):
        while self.is_running():
            self.perform(self.engine)

    def is_running(self):
        try: return self.__running
        except AttributeError:
            return False

    def set_running(self, state = True):
        self.__running = state

    def start(self):
        if not self.is_running():
            self.set_running(True)
            from _thread import start_new_thread as nth
            nth(self.run, ())

        return self

    def stop(self):
        self.set_running(False)
        return self

# Event Bridge Bindings.
StuphMUD.NewIncomingPeer = 'newConnection'
StuphMUD.Disconnection = 'disconnection'
StuphMUD.GreetPlayer = 'greetPlayer'
