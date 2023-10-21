# BOARD Communications Manifold.
'''
communication:
    categories:
        speech::
            say, say-to?, whisper?, emote
            shout, chat*, sing*, flame*, grat*
            tell?, clan-chat*..., quest-chat*..., group-chat...,
            echo!, zecho!, gecho!, wiznet!?, page!?, send!?

            legend::
                ? = target
                t! = gc
                x = level
                ... = select

        writing::
            boards (classic)
            mail

        other::
            bug/idea/typo

output-options::
    HTML/MIME generation?

specproc assignment:
    [Room:person.services.board.comm]
    xxxx: channel.last_room_say

    [Item:person.services.board.comm]
    xxxx: channel.conversational_item
'''

# from common.runtime import Object

from stuphos import getConfig
from stuphmud.server.player import ACMD
from stuphmud.server.zones.specials.standard import Special
from stuphos.runtime.facilities import Facility
from stuphos.runtime.architecture import Synthetic

from contextlib import contextmanager
from threading import Thread
from datetime import datetime
from time import time as now
from queue import Queue

def getCurrentTimestamp():
    return datetime.fromtimestamp(now())

boardComm = runtime.BOARD.COMM
boardCommStreaming = boardComm.Streaming

class BOARDCOMM(Facility):
    NAME = 'BOARD::COMM'

    @classmethod
    def BuildORM(self):
        @boardComm.ORM
        def ORM():
            from sqlobject import SQLObject, StringCol, BoolCol
            from sqlobject import ForeignKey, IntCol, DateTimeCol
            from sqlobject.dbconnection import ConnectionHub

            # Instantiate.
            hub = boardComm.SQLHUB(ConnectionHub)

            try:
                class Channel(SQLObject):
                    class sqlmeta:
                        #table = '"stuph:comm:channel"'
                        table = 'stuph_comm_channel'
                        # idName = 'name'

                    _connection = hub

                    name = StringCol(unique = True)
                    immortal = BoolCol(default = False)
                    level = IntCol(default = 0)
                    hasTarget = BoolCol(default = False)

                class Communicae(SQLObject):
                    class sqlmeta:
                        #table = '"stuph:comm:message"'
                        table = 'stuph_comm_message'

                    _connection = hub

                    channel = ForeignKey('Channel')
                    text = StringCol()
                    sourceIdnum = IntCol()
                    targetIdnum = IntCol(default = -1)
                    timestamp = DateTimeCol()
                    room = IntCol()
                    contentType = StringCol()

                class Tag(SQLObject):
                    class sqlmeta:
                        #table = '"stuph:comm:message:tag"'
                        table = 'stuph_comm_message_tag'

                    _connection = hub

                    channel = ForeignKey('Communicae')
                    tag = StringCol()

                ##    class Conversation(SQLObject):
                ##        class sqlmeta:
                ##            table = '"stuph:comm:conversation"'
                ##            idName = 'name'
                ##
                ##        _connection = hub
                ##        name = StringCol()

                class RoomConversation(SQLObject):
                    class sqlmeta:
                        #table = '"stuph:comm:conversation:room"'
                        table = 'stuph_comm_conversation_room'
                        #idName = 'room_vnum'

                    _connection = hub
                    room_vnum = IntCol(unique = True)
                    idnum = IntCol()

            except Exception as e:
                # already in registry..
                print('%s: %s' % (e.__class__.__name__, e))
                raise e
            else:
                return Synthetic(Channel = Channel,
                                 Communicae = Communicae,
                                 Tag = Tag,
                                 RoomConversation = RoomConversation)
        return ORM

    @classmethod
    def create(self):
        # Main Facility Bootstrap.
        database = getConfig('database', 'BOARDCOMM')
        assert database

        return self(_stuphChannels_builtin,
                    self.BuildORM(), database)

    def __init__(self, channels, orm, database):
        self.orm = orm
        self.database = database

        # This call initializes db tables as well.
        (self.channels,
         self.entities) = self.registerAllChannels(channels)

        self.roomConversations = self.hub.doInTransaction \
                                 (self.openRoomConversations)

        core = runtime[runtime.Agent.System]
        if core is not None:
            core.newToolConfig(path = 'components/services/boardcomm',
                               package = self.ToolInterface(self))

    def __registry_delete__(self):
        self.EndStream()

    class ToolInterface:
        # Native
        def __init__(self, comm):
            self._comm = comm
            self._channels = dict()

        def openChannel(self, frame, name):
            chan = AdhocChannel(name)
            self._channels[name] = chan
            chan.register(self._comm)

        def makeCommunicae(self, frame, name, player, message):
            self._channels[name].dispatchMessage(player, message)

    @property
    def dbURI(self):
        # XXX
        libdir = str(io.here)
        # libdir = abspath(normpath(getcwd()))

        libdir = libdir.replace('\\', '/')

        # Cleanup windows for sqlobject paths.
        ##    if libdir[1] == ':':
        ##        libdir = libdir[0] + libdir[2:]

        db = self.database.replace \
             ('$libdir$', libdir)

        return db

    ##    @property
    ##    def dbURI(self):
    ##        from os.path import split, sep
    ##        p = self.database.replace('/', sep).split(sep)
    ##        assert p
    ##
    ##        abs = not p[0]
    ##        p = filter(None, p)
    ##        p = sep.join(p)
    ##
    ##        if abs:
    ##            p = sep + p
    ##
    ##        return 'file://' + p

    @property
    def connection(self):
        if self.database and self.database.startswith('dbcore:'):
            from stuphos.db import dbCore
            return dbCore.getConnection(self.database[7:])

        # if self.database in ['pgcore', '(pgcore)']: # pgcore:classic
        #     return runtime['PG::Core'].connection

        from sqlobject import connectionForURI
        return connectionForURI(self.dbURI)

    @property
    def hub(self):
        hub = runtime[boardComm.SQLHUB]

        # Process connection works, but only while there are no other connections on the db held open.
        hub.threadConnection = self.connection
        #hub.processConnection = self.connection
        return hub

    def initializeDB(self, hub):
        # Create tables in order (to get around relational references).
        # for (name, table) in iteritems(dictOf(self.orm)):
        for name in ['Channel', 'Communicae', 'Tag', 'RoomConversation']:
            table = getattr(self.orm, name)

            #from pdb import set_trace; set_trace()

            # Note: each table creation must happen in its own transaction,
            # because if it fails, it will corrupt all following operations
            # in that transaction.  ifNotExists doesn't appear to be obeyed.
            try: hub.doInTransaction(table.createTable, ifNotExists = True)
            except Exception as e:
                # Todo: filter relation "xxx" already exists errors from other
                # real fatal errors.
                # Todo: syslog this.
                print('%s: %s' % (name, e))

    def registerAllChannels(self, channels):
        channelMap = dict()
        for ch in channels:
            ch.register(self)
            channelMap[ch.name] = ch

        entities = dict()

        hub = self.hub # resolve once.
        self.initializeDB(hub)

        @hub.doInTransaction
        def delegate_registration():
            for ch in channels:
                entities[ch.name] = self.registerChannel \
                                    (ch.configuration)

        return (channelMap, entities)

    def registerChannel(self, boardChannelConfiguration):
        name = boardChannelConfiguration['name']

        for ch in self.orm.Channel.selectBy(name = name): # limit = 1
            return ch

        conf = dict(name = name)

        try: conf['immortal'] = bool(boardChannelConfiguration['immortal'])
        except KeyError: pass

        try: conf['level'] = int(boardChannelConfiguration['level'])
        except (KeyError, TypeError): pass

        try: conf['hasTarget'] = bool(boardChannelConfiguration['hasTarget'])
        except KeyError: pass

        return self.orm.Channel(**conf)


    # Room Conversation Management.
    def openRoomConversations(self):
        return dict((c.room_vnum, c) for c in
                    self.orm.RoomConversation.select())

    def isConversationAt(self, vnum):
        return vnum in self.roomConversations

    def startConversationAt(self, player, avatar):
        print(self.startConversationAtVNum(avatar.location.vnum, avatar.idnum), file=player)

    def startConversationAtVNum(self, vnum, idnum):
        try: existing = self.roomConversations[vnum]
        except KeyError:
            e = self.hub.doInTransaction(self.orm.RoomConversation,
                                         room_vnum = vnum,
                                         idnum = idnum)

            self.roomConversations[vnum] = e
            return 'Conversation started at #%d.' % vnum
        else:
            return 'Conversation at #%d already opened by [#%d]' % \
                  (vnum, existing.idnum)

    def showRoomConversations(self, player):
        # todo: sort
        player.page_string('\r\n'.join('#%-20.20s : %10s' % (vnum, c.idnum)
                                       for (vnum, c)
                                       in iteritems(self.roomConversations)) + '\r\n')

    def stopConversationAt(self, player, vnum):
        try: existing = self.roomConversations[vnum]
        except KeyError:
            print('There is no conversation at #%d!' % vnum, file=player)
        else:
            @self.hub.doInTransaction
            def deleteConversation():
                existing.destroySelf()

            del self.roomConversations[vnum]
            print('Stopped conversation at #%d!' % vnum, file=player)


    # Message Production.
    @classmethod
    def MakeCommunicae(self, *args):
        comm = BOARDCOMM.get()
        if comm is not None:
            return comm.makeCommunicae(*args)

    @classmethod
    def EndStream(self):
        self.Streaming.End()

    def getCommunicaeArgs(self, configuration,
                          peerHost, player, argstr):

        try: room = player.location.vnum
        except AttributeError: room = -1

        return (configuration,
                (peerHost, player.idnum,
                 room, argstr,
                 datetime.now()))

    def makeCommunicae(self, event, configuration):
        try:
            name = configuration['name']
            channel = self.channels[name] # needed?
            entity = self.entities[name]

        except KeyError: pass # todo: log, but why

        # Note: using Dispatch method instead of Enqueue.
        # Todo: pass this instance (for room conversation dict)
        else: self.Streaming.Dispatch \
              (((channel, entity),
                self.getCommunicaeArgs \
                (configuration, *event)))

    def makeMessageCommunicae(self, channelName, player, message, configuration):
        try:
            name = configuration['name']
            channel = self.channels[name] # needed?
            entity = self.entities[name]

        except KeyError: pass # todo: log, but why

        else: self.Streaming.Enqueue(self.Streaming.CommMessage(channel, entity, player, message, configuration))

    class Streaming(Thread):
        @classmethod
        def Enqueue(self, message):
            queue = boardCommStreaming.Queue(Queue)
            queue.put(message)

            for x in range(10):
                thread = boardCommStreaming.Thread(self)

                if not thread.ended: # thread.isAlive():
                    try: thread.start()
                    except RuntimeError as e:
                        pass # print e # thread already started
                    else: break

                # Try again with new thread.
                del runtime[boardCommStreaming.Thread]

            else:
                raise RuntimeError('Tried 10 times to start thread')

        @classmethod
        def End(self, wait = False):
            try: thread = runtime[boardCommStreaming.Thread]
            except KeyError: pass
            else:
                if thread is not None:
                    del runtime[boardCommStreaming.Thread]
                    (thread.join if wait else
                     thread._Thread__stop)()

        ended = False
        def run(self):
            stream_q = runtime[boardCommStreaming.Queue]
            hub = runtime[boardComm.SQLHUB]
            orm = runtime[boardComm.ORM]

            try:
                while self.isAlive():
                    msg = stream_q.get()
                    hub.doInTransaction \
                        (self.dispatchCommMessage if isinstance(msg, self.CommMessage)
                         else self.dispatchComm,
                         *((orm,) + msg))
            finally:
                self.ended = True

        @classmethod
        def Dispatch(self, message):
            # Skip putting on the queue/starting thread.
            runtime[boardComm.SQLHUB].doInTransaction \
                (self.dispatchComm,
                 *((runtime[boardComm.ORM],) + message))

        class CommMessage:
            def __init__(self, channel, entity, player, message, configuration):
                self.channel = channel
                self.entity = entity
                self.player = player
                self.message = message
                self.configuration = configuration

            @property
            def idnum(self):
                return -1

        @classmethod
        def dispatchCommMessage(self, orm, msg):
            orm.Communicae(channel = msg.entity,
                           text = msg.message,
                           sourceIdnum = msg.idnum,
                           targetIdnum = -1, # xxx gr
                           room = -1,
                           timestamp = getCurrentTimestamp(), # XXX
                           contentType = 'text/plain').sync()

        @classmethod # for Dispatch form.
        def dispatchComm(self, orm, xxx_todo_changeme, xxx_todo_changeme1):

            # Currently, only record anything within conversational
            # rooms.  Otherwise, all communication is currently recorded,
            # and that's not what we exactly want.  What we want is a
            # framework for conditional conversation recording and
            # management.  This is one of the places to customize it.
            (channelObject,
                          channelEntity) = xxx_todo_changeme
            (configuration,
                          (peerHost, idnum,
                           room, argstr,
                           timestamp)) = xxx_todo_changeme1
            if not isConversationAt(room):
                return

            # Database Insert -- todo, conditionally on conversation.
            if 0 and configuration['name'] == 'say':
                # Todo: what about whisper, emote? shout?
                if not isConversationAt(room):
                    return

            orm.Communicae(channel = channelEntity,
                           text = argstr,
                           sourceIdnum = idnum,
                           targetIdnum = -1, # xxx gr
                           room = room,
                           timestamp = timestamp,
                           contentType = 'text/plain').sync()

            # now, tags


    @classmethod
    def GetChannel(self, name):
        instance = self.get()
        assert instance is not None

        for ch in self.orm.Channel.selectBy(name = name): # limit = 1
            return ch


def isConversationAt(vnum):
    #return vnum in _conversations
    return BOARDCOMM.get().isConversationAt(vnum)


class BOARDChannel:
    def __init__(self, xxx_todo_changeme2, name,
                 immortal = False, target = False,
                 level = None, select = False):

        (verb, command) = xxx_todo_changeme2
        self.verb = verb
        self.commandName = command
        # what about subcmds? like tell/reply are the same channel
        # actually, the cmd-object is passed to the (dispatchCommand) handler,
        # so this could be used, just need to make sure to register, and handle
        # specially..

        self.name = name
        self.immortal = immortal
        self.target = target
        self.level = level
        self.select = select

    def register(self, comm):
        verb = self.verb
        if isinstance(verb, str):
            verb = [verb]

        for verb in verb:
            register = ACMD(verb)
            register(self.dispatchCommand)

        from world import command as BuiltinCommand
        self.commandObject = BuiltinCommand(self.commandName)

    @property # memorized
    def configuration(self):
        config = dict(name = self.name)

        if self.immortal is not None:
            config['immortal'] = self.immortal
        if self.level is not None:
            config['level'] = self.level

        return config

    def dispatchCommand(self, player, cmd, argstr):
        # Main Player Interface.
        if player.avatar.isPlayer:
            BOARDCOMM.MakeCommunicae((player.host,
                                      player.avatar,
                                      argstr),
                                     self.configuration)

        # return False # Let perform_command do it because
        # it will check for level, etc.

        return False

        # XXX isn't callable in game/support.
        return self.commandObject(player, argstr)


    # Special Procedures.
    class BOARDComm_RoomSayBuffer(Special):
        # RoomConversation_LastSay
        # Could probably be used as non-room specproc, too.
        COMMANDS = dict(last = 'doLastComm')

        def doLastComm(self, player, this, parsed):
            if not player.peer: # or not player.supreme:
                return False

            # todo: other privileges

            (all, few, specified) = range(3)
            last = few

            args = parsed.argstr.split()
            if not args:
                return False
            if not args[0] == 'say':
                return False

            del args[0]
            # todo: last "here"?
            if args:
                assert len(args) == 1
                a = args[0]
                if a == 'all':
                    last = all
                elif a == 'few':
                    last = few
                elif a.isdigit():
                    limit = int(a)
                    last = specified
                else:
                    raise ValueError(a)

            if last == all:
                limit = None
            elif last == few:
                limit = 15

            vnum = player.location.vnum

            # Instance of BOARDCOMM
            instance = BOARDCOMM.get()
            assert instance is not None

            for ch in instance.orm.Channel.selectBy(name = 'say'): # limit = 1
                break
            else:
                raise NameError(name)

            def makeQuery():
                for c in instance.orm.Communicae.selectBy \
                    (channel = ch, room = vnum).limit(limit) \
                    .orderBy('-timestamp'):
                    #(channel = ch, room = vnum).limit(limit):
                    # todo: order by so that 'last' has any meaning...
                    # .orderBy('timestamp'):
                    yield c

            def reportQuery(g):
                from world.player import playerByID

                for (i, c) in enumerate(reversed(list(g))): # XXX reversing here
                    # channel, text, sourceIdnum, targetIdnum, room, timestamp
                    idnum = c.sourceIdnum

                    # todo: cache these lookups.
                    try: name = playerByID(idnum)
                    except ValueError: name = '#%d' % idnum

                    yield '[%s] (%-20s) %s' % (c.timestamp, name, c.text)

                yield ''

            player.peer.page_string('\r\n'.join(reportQuery(makeQuery())))


    class BOARDComm_SpecialInterface_Buffer(Special):
        # Not sure what to do with this:
        ##    def StuphOS_BOARD_Pack(self, item):
        ##        pass

        TARGET_SELF = True
        COMMANDS = dict(read = 'doReadComm',
                        look = 'doReadComm')

        def __init__(self, **values):
            self.name = values['channel-name']
            self.query = values['query']

        def doReadComm(self, player, this, parsed):
            args = parsed.argstr.split()
            if args:
                #@Threading
                def performQuery():
                    # Create a report object, put it in player's inventory,
                    # or associate it with the buffer as a BOARD message,
                    # and then notify.
                    with BOARDCOMM.GetChannel(self.name) as channel:
                        return channel.entity.select(**self.query)

                builtin(pq = performQuery)
                return True

    class BOARDComm_SpecialInterface_ConversationManagement:
        class Base(Special):
            # Manage conversational contexts, in generic.
            COMMANDS = {':': 'doManageConversations'}

            def doManageConversations(self, player, this, parsed):
                #:conversation start here

                if not player.peer or not player.supreme:
                    return False

                args = self.prepareArgs(this, player, parsed)

                if args[0] == 'start':
                    del args[0]
                    assert args and args[0] == 'here'

                    BOARDCOMM.get().startConversationAt(player.peer, player)

                elif args[0] in ['show', 'list']:
                    del args[0]
                    assert not args

                    BOARDCOMM.get().showRoomConversations(player.peer)

                elif args[0] in ['stop']:
                    del args[0]
                    assert len(args) == 1

                    if args[0] == 'here':
                        location = player.location.vnum
                    else:
                        assert args[0].isdigit()
                        location = int(args[0])

                    BOARDCOMM.get().stopConversationAt(player.peer, location)

                else:
                    # Unknown
                    return False

                return True


        # Specific interfaces:
        class Room(Base):
            def prepareArgs(self, this, player, parsed):
                args = parsed.argstr.split()
                assert args
                assert args[0] == 'conversations'
                del args[0]

                return args

            ##    AttributeError: 'room' object has no attribute 'page_string'
            ##                                 [ixion\stuph\lib\python\mud\zones\specials\standard.py:184] __call__
            ##                                   this, parsed) is False:
            ##                                 [ixion\stuph\lib\python\mud\zones\specials\standard.py:197] dispatchCommand
            ##                                   return action(*args, **kwd)
            ##                                 [ixion\stuph\lib\python\packages\implementors\person\services\board\comm.py:557] doManageConversations
            ##                                   BOARDCOMM.get().showRoomConversations(player)
            ##                                 [ixion\stuph\lib\python\packages\implementors\person\services\board\comm.py:257] showRoomConversations
            ##                                   player.page_string('\r\n'.join('#%-20.20s : %10s' % (vnum, c.idnum)
            ##    Unknown command: ':conversations list'

        class Item(Base):
            TARGET_SELF = True

            def prepareArgs(self, this, player, parsed):
                args = parsed.argstr.split()
                del args[0] # name of object
                assert args

                return args

class AdhocChannel(BOARDChannel):
    def __init__(self, name, instance = None):
        self.name = name
        self.instance = instance

    @property # memorized
    def configuration(self):
        return dict()

    def register(self, comm):
        pass

    def dispatchMessage(self, player, message):
        comm = BOARDCOMM.get()
        if comm is not None:
            comm.makeMessageCommunicae(self.name, player, message, configuration)

_stuphChannels_builtin = [BOARDChannel((['say*', "'"      ], 'say'), 'say'      ),
                          BOARDChannel((['to*', '>'       ], 'to'), 'sayTo',
                                       target = True),

                          BOARDChannel((['whisper*'       ], 'whisper'), 'whisper'  ),
                          BOARDChannel((['emote*', ':'    ], 'emote'), 'emote',
                                       target = True),

                          BOARDChannel((['chat*', '.'     ], 'chat'), 'chat'     ),
                          BOARDChannel((['shout*'         ], 'shout'), 'shout'    ),
                          BOARDChannel((['sing*'          ], 'sing'), 'sing'     ),
                          BOARDChannel((['flame*'         ], 'flame'), 'flame'    ),
                          BOARDChannel((['grat*'          ], 'grats'), 'congrats'   ),

                          BOARDChannel((['tell*'          ], 'tell'), 'tell',
                                       target = True),
                          # reply?

                          BOARDChannel((['csay*', 'ctell*'], 'csay'), 'clanChat',
                                       select = True),

                          BOARDChannel((['qsay*'          ], 'qsay'), 'questChat',
                                       select = True),

                          BOARDChannel((['gsay*'          ], 'gsay'), 'groupChat',
                                       select = True),

                          BOARDChannel((['echo*'          ], 'echo'), 'echo',
                                       target = False, immortal = True),

                          BOARDChannel((['zecho*'         ], 'zecho'), 'zecho',
                                       target = False, immortal = True),

                          BOARDChannel((['gecho*'         ], 'gecho'), 'gecho',
                                       target = False, immortal = True),

                          # Todo: remove '-' from channeling for sake of wizcontrol??
                          BOARDChannel((['wiznet*', '-'   ], 'wiznet'), 'wiznet',
                                       target = False, immortal = True),

                          BOARDChannel((['send*'          ], 'send'), 'send',
                                       target = True, immortal = True),

                          BOARDChannel((['page*'          ], 'page'), 'page',
                                       target = True, immortal = True)]


# Query and report from within main module during testing:
# for (_, _, msg, _, _, time, _) in sqlite.Connection(c.connection).sqlite3Connection.execute('select * from "stuph:comm:message"'): print msg

##    if 0:
##        stuphMud.testing.module.BOARDChannel.BOARDComm_SpecialInterface_Buffer \
##            (**{'query': '', 'channel-name': ''}) \
##            (core.console, None, synthetic(name = 'read'), 'query')
##
##        o = stuphMud.testing.module.BOARDChannel.BOARDComm_RoomSayBuffer()
##        o(None, core.console.avatar, synthetic(name = 'last'), '')
##
##        RoomConversation_LastSay = BOARDComm_RoomSayBuffer

# Specproc Assignment Interface.
class channel:
    last_room_say = BOARDChannel.BOARDComm_RoomSayBuffer
    last_say = last_room_say
    conversational_room = BOARDChannel.BOARDComm_SpecialInterface_ConversationManagement.Room
    conversational_item = BOARDChannel.BOARDComm_SpecialInterface_ConversationManagement.Item

# selectBy(room = room).limit(10)


# _conversations = dict()

# runtime[boardComm.RoomConversations]

##    @ACMD('boardcomm-*admin')
##    def doAdminBOARDCOMM(player, cmd, argstr):
##        avatar = player.avatar
##        if avatar and avatar.supreme:
##            args = argstr.split()
##            if args:
##                if args[0] == 'conversation':
##                    del args[0]
##                    assert args
##
##                    if args[0] == 'start':
##                        del args[0]
##                        assert args and args[0] == 'here'
##
##                        BOARDCOMM.get().startConversationAt(player, avatar)
##                        ##    vnum = avatar.location.vnum
##                        ##
##                        ##    try: existing = _conversations[vnum]
##                        ##    except KeyError:
##                        ##        _conversations[vnum] = dict(idnum = avatar.idnum)
##                        ##        print >> player, 'Conversation started at #%d.' % vnum
##                        ##    else:
##                        ##        print >> player, 'Conversation at #%d already opened by [#%d]' % \
##                        ##              (vnum, existing['idnum'])
##
##                    elif args[0] in ['show', 'list']:
##                        del args[0]
##                        assert not args
##
##                        BOARDCOMM.get().showRoomConversations(player)
##                        ##    player.page_string('\r\n'.join('#%-20.20s : %10s' % nv for nv
##                        ##                                   in iteritems(_conversations)))
##
##                    elif args[0] in ['stop']:
##                        assert not args # for now
##
##                    else:
##                        return False
##
##                    return True


# Generalized:
class ConversationManagement:
    def handleCommand(self, player, this, args, parsed):
        if args[0] == 'start':
            del args[0]
            assert args and args[0] == 'here'

            BOARDCOMM.get().startConversationAt(player, player.avatar)
            ##    vnum = avatar.location.vnum
            ##
            ##    try: existing = _conversations[vnum]
            ##    except KeyError:
            ##        _conversations[vnum] = dict(idnum = avatar.idnum)
            ##        print >> player, 'Conversation started at #%d.' % vnum
            ##    else:
            ##        print >> player, 'Conversation at #%d already opened by [#%d]' % \
            ##              (vnum, existing['idnum'])

        elif args[0] in ['show', 'list']:
            del args[0]
            assert not args

            BOARDCOMM.get().showRoomConversations(player)
            ##    player.page_string('\r\n'.join('#%-20.20s : %10s' % nv for nv
            ##                                   in iteritems(_conversations)))

        elif args[0] in ['stop']:
            assert not args # for now

        else:
            return False

        return True

##    @ACMD('boardcomm-*admin')
##    @apply
##    class WizardConversationMngr(ConversationManagement):
##        def __call__(self, player, cmd, argstr):
##            avatar = player.avatar
##            if avatar and avatar.supreme:
##                args = argstr and argstr.split() or []
##                if args:
##                    if args[0] == 'conversation':
##                        del args[0]
##                        assert args
##
##                        return self.handleCommand(player, None, args, None)
