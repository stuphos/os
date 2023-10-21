# Supposed to replace Circle board functionality, and provide a place to extend it.
# For now, it seeks to emulate Circle as closely as possible.
# classic

# expansion:
#   stylus-items for indexing deep into message thread-tree
#   for an hierarchical discussion board.
#
# Otherwise, the BOARD protocol should provide indirection
# layer between classical and this module models.

from time import time as now, asctime, localtime
from datetime import datetime

from stuphmud.server.tools import splitOne as chopOne, SORP
from stuphmud.server.runtime import Object

SECONDS_PER_DAY = 60 * 60 * 24

# System.
def getCurrentDateTime():
    return datetime.fromtimestamp(now())

def getTimeString(time):
    if type(time) is datetime:
        return time.ctime()
        time = time

    return asctime(localtime(time))

# Tools.
def delete_doubledollar(string):
    return string.replace('$$', '$')

def parseSpecialCommand(cmd, argstr):
    cmd = getattr(cmd, 'name', cmd)
    assert type(cmd) is str, TypeError(type(cmd).__name__)

    args = argstr and argstr.split() or ()
    return (cmd, args)

def isName(name, namelist):
    return name.lower() in namelist.lower().split()

# BOARD Model Implementation.
class Board(Object):
    _Meta = Object._Meta('name', 'vnum', 'filename')

    ACT_BEGIN_WRITING_TOCHAR = "Write your message.  End with '.' or '@' on a new line.\n"
    ACT_BEGIN_WRITING_TOROOM = "$n starts to write a message."

    MSG_NO_WRITE_TOCHAR = 'You are not holy enough to write on this board.'
    MSG_NO_READ_TOCHAR = 'You try but fail to understand the holy words.'

    MSG_NOTHOLY_ENOUGH = "You are not holy enough to remove other people's messages."
    MSG_NOTHOLIER_THAN = "You can't remove a message holier than yourself."

    class Message(Object):
        _Meta = Object._Meta('headline', 'author_name')

        def __init__(self, board, headline = '',
                     timestamp = None,
                     author_idnum = -1,
                     author_level = 0,
                     author_name = ''):

            self.board = board
            self.headline = headline
            self.timestamp = timestamp

            self.author_idnum = author_idnum
            self.author_level = author_level
            self.author_name = author_name

            self.body = ''

        # Creation.
        def startWriting(self, author):
            startWriting(author, self.finishWriting,
                         self.board.ACT_BEGIN_WRITING_TOCHAR,
                         self.board.ACT_BEGIN_WRITING_TOROOM)

        def finishWriting(self, author, string):
            self.body = string
            self.board.saveBoard()

        # Evaluation.
        def getAgeInDays(self):
            age = (getCurrentDateTime() - self.timestamp).days
            return ' (%s day%s old)' % (age, SORP(age))

        def getFullHeadline(self, withAge = False):
            return '&G%6.10s &C%-12s &N:: &b%s&N%s' % \
                   (getTimeString(self.timestamp),
                    '(%s)' % self.author_name, self.headline,
                    self.getAgeInDays() if withAge else '')

        def getFullDisplay(self, nr):
            return 'Message %d : %s\n\n%s\n' % (nr, self.getFullHeadline(), self.body)

        def isAuthor(self, author):
            return self.author_idnum == author.idnum and \
                   self.author_name == author.name

        def canRemove(self, actor, explain_why = False):
            return self.board.canRemove(actor, self, explain_why = explain_why)
        def remove(self, actor, nr):
            self.board.removeMessage(actor, self, nr)

    @classmethod
    def FromStuphLib(self):
        from stuphlib.boards import _builtin_boards as builtin
        return list(map(self.FromBuiltin, builtin))

    @classmethod
    def FromBuiltin(self, builtin):
        # Create a board object from a builtin record.
        return self(vnum = builtin.vnum,
                    name = builtin.name,
                    filename = builtin.name,
                    read_level = builtin.read_lvl,
                    write_level = builtin.write_lvl,
                    remove_level = builtin.remove_lvl,
                    auto_cleanup = builtin.auto_cleanup)

    def __init__(self, vnum = None, name = None, filename = None,
                 read_level = None, write_level = None, remove_level = None,
                 auto_cleanup = None):

        self.vnum = vnum
        self.name = name
        self.filename = filename
        self.read_level = read_level
        self.write_level = write_level
        self.remove_level = remove_level
        self.auto_cleanup = auto_cleanup

        self.messages = []

    def saveBoard(self):
        if self.filename:
            import json
            def ofMessage(msg):
                return dict(headline = msg.headline,
                            timestamp = msg.timestamp.ctime(),

                            author_idnum = msg.author_idnum,
                            author_level = msg.author_level,
                            author_name = msg.author_name,

                            body = msg.body)

            with open(self.filename, 'w') as o:
                json.dump(dict(vnum = self.vnum,
                               name = self.name,
                               read_level = self.read_level,
                               write_level = self.write_level,
                               remove_level = self.remove_level,
                               auto_cleanup = self.auto_cleanup,
                               messages = list(map(ofMessage, self.messages))),
                          o, indent = 1)

    def canWrite(self, author, explain_why = False):
        if author.level >= self.write_level:
            return True
        if explain_why and author.peer:
            print(self.MSG_NO_WRITE_TOCHAR, file=author.peer)

        return False

    def canRead(self, author, explain_why = False):
        if author.level >= self.read_level:
            return True
        if explain_why and author.peer:
            print(self.MSG_NO_READ_TOCHAR, file=author.peer)

        return False

    def canRemove(self, author, msg, explain_why = False):
        if author.level < self.remove_level and not msg.isAuthor(author):
            if explain_why and author.peer:
                print(self.MSG_NOTHOLY_ENOUGH, file=author.peer)

            return False

        if author.level < msg.author_level and not author.supreme:
            if explain_why and author.peer:
                print(self.MSG_NOTHOLIER_THAN, file=author.peer)
            return False

        return True

    def createMessage(self, author, headline):
        msg = self.Message(self, headline,
                           timestamp = getCurrentDateTime(),
                           author_idnum = author.idnum,
                           author_level = author.level,
                           author_name = author.name)

        self.messages.append(msg)
        return msg

    def removeMessage(self, author, message, nr):
        self.messages.remove(message)
        if author.peer:
            print('Message removed.', file=author.peer)

        # author.act('$n just removed message %d.' % nr)
        self.saveBoard()

    def registerItem(self, item):
        item.__board__ = self
        item.special = specialBoard

class BoardManager:
    def __init__(self):
        self.table = {}
    def __getitem__(self, item):
        try: return self.table.get(item.vnum)
        except ValueError:
            # Atypical.
            raise KeyError

_builtin_board_manager = BoardManager()

_builtin_boards = Board.FromStuphLib()

_builtinBoardsByName = dict((b.name, b) for b in _builtin_boards)
_builtinBoardsByVnum = dict((b.vnum, b) for b in _builtin_boards)


# Worldly Actualization.
def findBoardByItem(item):
    try: return item.__board__
    except AttributeError:
        pass

    try: return item.prototype.__board__
    except AttributeError:
        pass

    try: return _builtin_board_manager[item]
    except KeyError:
        pass

def findNamedBoard(actor, name, this):
    # From boards.cpp:find_board(ch, arg)

    # "If there's an argument we look by keyword first"
    name = name.strip()
    if name:
        # "First check inventory by name"
        item = actor.find(name, inventory = True)
        if item is not None:
            board = findBoardByItem(item)
            if board is not None:
                return (item, board)

        # "Didn't find that lets try the room"
        item = actor.find(name, item_in_room = True)
        if item is not None:
            board = findBoardByItem(item)
            if board is not None:
                return (item, board)

    # "Ok we'll resort to this..."
    for item in actor.room.contents:
        board = findBoardByItem(item)
        if board is not None:
            return (item, board)

    for item in actor.inventory:
        board = findBoardByItem(item)
        if board is not None:
            return (item, board)

    # Default result (this object).
    board = findBoardByItem(this)
    if board is not None:
        return (this, board)

    return (None, None)

def startWriting(author, finish, to_char, to_room):
    peer = author.peer
    if peer:
        def messageTerminator(peer, string):
            author.playerflags.writing = False
            finish(author, string)

        peer.messenger = messageTerminator

        if not author.npc:
            author.playerflags.writing = True

        print(to_char, file=peer)
        peer.editString('')

        # XXX
        # author.act(to_room, hide_if_invisible = True, to_room = True)

# Player Interface.
# Todo: what about NEWEST_AT_TOP emulation?  Newest is always at bottom..
def doReadBoard(actor, this, argstr, *args):
    # Peer is required for message output.
    if not actor.peer:
        return False

    # Not supporting "read board" currently..

    (name, argstr) = chopOne(argstr, ' ')
    (item, board) = findNamedBoard(actor, name, this)
    if board is not None and argstr.isdigit(): # read 2.mail, look 2.sword
        if board.canRead(actor, explain_why = True):
            msgNr = int(argstr)

            if not board.messages:
                print('The board is empty!', file=actor.peer)
            elif msgNr < 1 or msgNr > len(board.messages):
                print('That message exists only in your imagination!', file=actor.peer)
            else:
                msg = board.messages[msgNr - 1]
                if not msg.body:
                    print('That message seems to be empty.', file=actor.peer)
                else:
                    actor.peer.page(msg.getFullDisplay(msgNr))

        return True

def doWriteBoard(actor, this, argstr, *args):
    # Peer is required for message input.
    if not actor.peer:
        return False

    (name, argstr) = chopOne(argstr, ' ')
    (item, board) = findNamedBoard(actor, name, this)
    if board is not None:
        if board.canWrite(actor, explain_why = True):
            argstr = argstr.lstrip()
            argstr = delete_doubledollar(argstr)

            if len(argstr) > 80:
                argstr = argstr[:80]

            if not argstr:
                print('We must have a headline!', file=actor.peer)
            else:
                msg = board.createMessage(actor, argstr)
                msg.startWriting(actor)

        return True

def doShowBoard(actor, this, argstr, *args):
    # Peer is required for message display.
    if not actor.peer:
        return False
    if not args or not isName(args[0], this.keywords):
        return False

    (item, board) = findNamedBoard(actor, argstr, this)
    if board is not None:
        if board.canRead(actor, explain_why = True):
            # XXX
            # actor.act('$n studies %s.' % item.name,
            #           hide_if_invisible = True, to_room = True)

            # Display
            def _():
                n = len(board.messages)
                yield '&NThis is %s.  &NUsage: &cREAD/REMOVE&N <messg #>, &cWRITE&N <header>.' % item.name

                # This may not be true, but it may prompt other players to look at the board.
                yield 'You will need to look at the board to save your message.'

                if not n:
                    yield 'The board is empty.'
                else:
                    yield 'There are %d message%s on the board.' % (n, SORP(n))

                    for (i, m) in enumerate(board.messages):
                        yield '%-3d: %s' % (i + 1, m.getFullHeadline(withAge = True))

                yield ''

            actor.peer.page('\n'.join(_()))

        return True

def doRemoveFromBoard(actor, this, argstr, *args):
    def notify(msg):
        if actor.peer:
            print(msg, file=actor.peer)

    (name, argstr) = chopOne(argstr, ' ')
    (item, board) = findNamedBoard(actor, name, this)
    if board is not None and argstr.isdigit():
        from stuphmud.server.player import playerAlert, PlayerAlert
        try:
            n = len(board.messages)
            if not n:
                playerAlert('The board is empty!')
            else:
                msgNr = int(argstr)
                if msgNr < 1 or msgNr > n:
                    playerAlert('That message exists only in your imagination.')
                else:
                    msg = board.messages[msgNr - 1]
                    if msg.canRemove(actor, explain_why = True):
                        # Todo: 'At least wait until the author is finished before removing it!'
                        msg.remove(actor, msgNr)

        except PlayerAlert as e:
            if actor.peer:
                e.deliver(actor.peer)

        return True

#@ASSIGNOBJ('BOARD::Interface')
def specialBoard(actor, this, cmd, argstr):
    (cmd, args) = parseSpecialCommand(cmd, argstr)
    func = _board_functions.get(cmd)

    # Originally, the board_type is found before calling the command,
    # but this leaves that specific argument-matching up to that routine.
    if callable(func):
        return func(actor, this, argstr, *args)

_board_functions = dict(write   = doWriteBoard,
                        read    = doReadBoard,
                        look    = doShowBoard,
                        examine = doShowBoard,
                        remove  = doRemoveFromBoard)


# This is a departure from Circle, which would define boards internally.
_board_cache = {}

from stuphmud.server.player import ACMDLN, Option
@ACMDLN('new-board', Option('--board-name', '--name'),
                     Option('--item'),
                     Option('--vnum', type = int),
                     Option('--filename'),
                     Option('--read-level', type = int),
                     Option('--write-level', type = int),
                     Option('--remove-level', type = int),
                     Option('--auto-cleanup', action = 'store_true'))
def doNewBoard(peer, command):
    player = peer.avatar
    if player.supreme:
        boardName = command.options.board_name
        itemName = command.options.item

        if not (boardName and itemName):
            yield command.help()
        else:
            try: board = _board_cache[boardName]
            except KeyError:
                # Figure out what this item is.
                if itemName.isdigit():
                    import world
                    item = world.item(int(itemName))

                else:
                    item = player.find(itemName, inventory = True, equipment = True,
                                       item_in_room = True)

                if item is None:
                    yield 'Could not find any item named %r' % itemName
                else:
                    # Create new board, add it to cache, register item.
                    o = command.options
                    board = Board(name = boardName,
                                  vnum = o.vnum,
                                  filename = o.filename,
                                  read_level = o.read_level,
                                  write_level = o.write_level,
                                  remove_level = o.remove_level,
                                  auto_cleanup = o.auto_cleanup)

                    _board_cache[boardName] = board
                    board.registerItem(item)

                    yield 'New board created [%s], and attached it to %s.' % (boardName, item)
            else:
                yield 'Board already exists: %r' % board
