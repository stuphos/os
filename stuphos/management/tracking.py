# Player Event Tracking
from stuphos.runtime.facilities import Facility
from stuphos.runtime import newComponent
from stuphos import getConfig

# XXX dependency
from stuphos.system.api import mudlog

from xdrlib import Packer
from time import time as now

def timestamp():
    # Return time in milliseconds
    # XXX Just return 32bit time
    # return now() * 1000
    return int(now())

class BinaryLog(Packer):
    class Record(object):
        def pack(self, db):
            # Pack binary form into db.
            pass

    @classmethod
    def OpenFile(self, filename):
        return open(filename, 'w')

    # Much of the higher-level relational data will need to be kicked up into appl.
    def __init__(self, stream):
        self._Packer__buf = stream

    def flush(self):
        self._Packer__buf.flush()

    SHORT_MAX = (2 ** 16)
    INT_MAX = (2 ** 32)

    def convertFlags(self, these):
        bitv = 0
        if these is not None:
            for f in these:
                bitv |= self.FLAG_MAP[f.lower()]

        return bitv

    ##    TIMEFRAME_SIZE = 0
    ##
    ##    def convertTimestamp(self, timestamp):
    ##        return timestamp - (self.TIMEFRAME_SIZE, self._timeframe)
    ##
    ##    def activelyConvertTimestamp(Self, timestamp):
    ##        while True:
    ##            timestamp = self.convertTimestamp(record.timestamp)
    ##            timestamp *= 1000 # micros
    ##
    ##            if timestamp <= self.INT_MAX:
    ##                return timestamp
    ##
    ##            # push timeframe forward, reconvert.
    ##            self._timeframe += 1
    ##            self.pack_timeframe(self, self._timeframe)
    ##
    ##    def getPlayerIdnum(self, name):
    ##        try: return self._idnum_map[name]
    ##        except KeyError:
    ##            def newId():
    ##                s = len(self._idnum_map)
    ##                while s in self._idnum_map:
    ##                    s += 1
    ##
    ##                return s
    ##
    ##            i = self._idnum_map[name] = newId()
    ##            return i

    def buildPktHdr(self, type, flags, size):
        if isinstance(type, int):
            assert type >= 0 and type <= 255
        else:
            type = self.TYPE_MAP[type.lower()]

        if flags is None:
            flags = 0
        elif isinstance(flags, int):
            assert flags >= 0 and flags <= 255
        else:
            type = self.convertFlags(flags)

        self.pack_uint((type << 24) | (flags << 16) | size)

    def pack_packet(self, type, flags, data):
        n = len(data)
        pkthdr = self.buildPktHdr(type, flags, n)
        self.pack_fopaque(n, data)
        self.flush()

class RecordKeeping(BinaryLog):
    # Log game events, to listeners and/or to binary file.
    TYPE_EPOCH       = 10
    TYPE_TIMEFRAME   = 11
    TYPE_HOSTRECORD  = 12
    TYPE_NAMERECORD  = 13
    TYPE_PLAYERINPUT = 14
    TYPE_PEERINPUT   = 15

    BIT_LONG = (1 << 2)

    TYPE_MAP = dict(epoch         = TYPE_EPOCH,
                    time_frame    = TYPE_TIMEFRAME,
                    host_record   = TYPE_HOSTRECORD,
                    # player_record = TYPE_PLAYERRECORDS,

                    input         = TYPE_PLAYERINPUT,
                    peer_input    = TYPE_PEERINPUT)

    FLAG_MAP = dict(int = BIT_LONG)

    class Record(BinaryLog.Record):
        def present(self, peer):
            # Show this record to a player.
            pass

    def __init__(self, dbpath):
        BinaryLog.__init__(self, BinaryLog.OpenFile(dbpath))
        self.listeners = []

    # Todo: adapt log-form to message listener (pentacle)
    def addListener(self, o):
        if o not in self.listeners:
            self.listeners.append(o)
            return True

    def removeListener(self, o):
        if o in self.listeners:
            self.listeners.remove(o)
            return True

    def broadcast(self, record):
        for o in self.listeners:
            record.present(o)

    def handle(self, record):
        record.pack(self)
        self.broadcast(record)

    def __lshift__(self, record):
        self.handle(record)
        return self

class ComponentRecord(RecordKeeping.Record):
    @classmethod
    def Bind(self, component):
        for name in dir(component):
            try: obj = getattr(component, name)
            except AttributeError: pass
            else:
                try:
                    if issubclass(obj, ComponentRecord):
                        # Dynamically connect record type to instrument composing with it.
                        obj.Component = component

                except TypeError:
                    pass

        return component

    def __new__(self, ctlr, *args, **kwd):
        inst = RecordKeeping.Record.__new__(self)
        inst.__init__(*args, **kwd)

        self.Component << inst

# Eventually:
# from .behavior import Instrumentation
# from . import ComponentRecord

class Instrumentation:
    def __init__(self):
        self._hostname_map = dict()

    def newHostId(self, host):
        hostId = crc32(host)
        p = Packer()
        p.pack_int(hostId)
        p.pack_string(host)
        self.pack_packet('host_record', None, p.get_buffer())
        return hostId

    def pack_host(self, host):
        try: return self._hostname_map[host]
        except KeyError:
            hostId = self.newHostId(host)
            self._hostname_map[host] = hostId
            return hostId

    class onNewConnection(ComponentRecord):
        def __init__(self, peer):
            self.peer = peer
            self.host = peer.host

        def pack(self, db):
            db.pack_host(self.host)

        def present(self, peer):
            print('&B[&WConnect: &w%s&B]&N' % self.peer)

    class onPlayerInput(ComponentRecord):
        def __init__(self, peer, input):
            if peer.avatar is None:
                self.host = peer.host
                self.idnum = None
            else:
                self.host = None
                self.idnum = peer.avatar.idnum

            self.input = input
            self.peer = peer

        def pack(self, db):
            if self.idnum is None:
                # This must be done before any new record.
                hostId = db.pack_host(self.host)

                p = Packer()
                p.pack_uint(hostId)
                p.pack_uint(timestamp())
                p.pack_string(self.input)
                db.pack_packet('peer_input', None, p.get_buffer())
            else:
                p = Packer()
                p.pack_uint(timestamp())
                p.pack_uint(self.idnum)
                p.pack_string(self.input)
                db.pack_packet('input', None, p.get_buffer())

        def present(self, peer):
            print('&B[&w%s&B] &N%s&N' % (self.peer, self.input), file=peer)

    ##    class onMovement(ComponentRecord):
    ##        def __init__(self, mobile, origin, destination, direction, move_type, move_cost):
    ##            self.mobile = mobile
    ##
    ##        def pack(self, db):
    ##            if not self.mobile.npc:
    ##                db.pack()

    ##    class onSlaying(ComponentRecord):
    ##        def __init__(self, victim, killer):
    ##            # And also, for instance, experience earned (approx), level at the time
    ##            pass

class PlayerTracking(Facility, Instrumentation, RecordKeeping):
    '''
    [Facilities]
    facility.tracking: mud.management.tracking.PlayerTracking

    [PlayerTracking]
    db-path: etc/player-tracking.db
    '''

    NAME = 'Player::Tracking'
    AUTOMANAGE = True

    class Manager(Facility.Manager):
        MINIMUM_LEVEL = Facility.Manager.IMPLEMENTOR
        VERB_NAME = 'player-tracking*'

        def do_listen(self, peer, cmd, args):
            t = PlayerTracking.get()
            if t is not None:
                if t.addListener(peer):
                    print('You will now be informed of player events.', file=peer)
                else:
                    print('You are already listening to player events.', file=peer)

        def do_unlisten(self, peer, cmd, args):
            t = PlayerTracking.get()
            if t is not None:
                if t.removeListener(peer):
                    print('You will no longer be informed of player events.', file=peer)
                else:
                    print('You are not currently listening to player events.', file=peer)

        def do_last(self, peer, cmd, args):
            # Show all records from log since time.
            pass

    @classmethod
    def create(self):
        dbpath = getConfig('db-path', section = 'PlayerTracking')
        if not dbpath:
            raise ValueError('PlayerTracking:db-path is not configured')

        return ComponentRecord.Bind(newComponent(self, dbpath = dbpath))

    def __instance_init__(self):
        Instrumentation.__init__(self)
        RecordKeeping.__init__(self, self.dbpath)

    # Er, do this onShutdownGame instead??
    ##    def __registry_delete__(self):
    ##        rotated = '%s.%s' % (self.dbpath, now())
    ##        rename(self.dbpath, rotated)
    ##        system('gzip -9 %r' % rotated)


PlayerTracking.get(create = True)
PlayerTracking.manage()

class NSA(Instrumentation.onPlayerInput):
    # Called as a special procedure.
    def __new__(self, player, *args, **kwd):
        if not player.npc:
            t = PlayerTracking.get()
            if t is not None:
                inst = RecordKeeping.Record.__new__(self)
                inst.__init__(player, *args, **kwd)

                t << inst

    def __init__(self, player, this, cmd, argstr):
        self.idnum = player.idnum
        self.host = '' if player.peer is None else player.peer.host
        self.input = ' '.join([_f for _f in (cmd.name, argstr) if _f])
        self.peer = player.peer
