from .constants import *
from .binary import Record, BuildRecordClass
from .binary import ReadFile, ReadOneFromFile, ReadBytes

NUM_OF_BOARDS = 32
BOARD_FILE = (lambda n: 'boards/board.%s' % n)


class BoardInfo:
    def __init__(self, vnum, read_lvl, write_lvl, remove_lvl,
                 name, auto_cleanup):

        self.vnum = vnum
        self.read_lvl = read_lvl
        self.write_lvl = write_lvl
        self.remove_lvl = remove_lvl
        self.name = name
        self.filename = BOARD_FILE(name)
        self.auto_cleanup = auto_cleanup

    def __str__(self):
        return 'Board #%d (%s)' % (self.vnum, self.filename)
    __repr__ = __str__


_builtin_boards = [BoardInfo(1216, 0, 0, LVL_OVERSEER,
                             ('remort'), False),
                   BoardInfo(1221, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('buildergroup'), False),
                   BoardInfo(1223, 0, 0, LVL_OVERSEER,
                             ('newbie'), False),
                   BoardInfo(1224, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('area'), False),
                   BoardInfo(1225, 0, 0, LVL_OVERSEER,
                             ('quest'), False),
                   BoardInfo(1226, 0, 0, LVL_OVERSEER,
                             ('clan'), False),
                   BoardInfo(1227, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('todo'), False),
                   BoardInfo(1228, 0, 0, LVL_OVERSEER,
                             ('idea'), False),
                   BoardInfo(1229, LVL_OVERSEER, LVL_OVERSEER, LVL_IMPL,
                             ('admin'), False),
                   BoardInfo(1230, 0, 0, LVL_OVERSEER,
                             ('skills'), True),
                   BoardInfo(1231, 0, 0, LVL_OVERSEER,
                             ('social'), False),
                   BoardInfo(1233, 0, 0, LVL_OVERSEER,
                             ('player_relations'), False),
                   BoardInfo(1234, 0, LVL_AVATAR, LVL_IMPL,
                             ('zifnab'), True),
                   BoardInfo(1245, 0, LVL_AVATAR, LVL_IMPL,
                             ('coder'), False),
                   BoardInfo(1260, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('clangroup'), False),
                   BoardInfo(1261, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('questgroup'), False),
                   BoardInfo(1263, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('continent'), False),
                   BoardInfo(3097, LVL_AVATAR, LVL_DEITY, LVL_IMPL,
                             ('freeze'), True),
                   BoardInfo(3098, LVL_AVATAR, LVL_AVATAR, LVL_ARCH_GOD,
                             ('immort'), True),
                   BoardInfo(3099, 0, 0, LVL_OVERSEER,
                             ('mort'), True),
                   BoardInfo(8299, LVL_AVATAR, LVL_AVATAR, LVL_OVERSEER,
                             ('roleplay'), False),
                   BoardInfo(40700, 0, 0, LVL_GOD,
                             ('forsaken'), False),
                   BoardInfo(40767, 0, 0, LVL_DEMIGOD,
                             ('avalon'), False),
                   BoardInfo(40792, 0, 0, LVL_OVERSEER,
                             ('clan_council'), False),
                   BoardInfo(40797, 0, 0, LVL_OVERSEER,
                             ('mort_council'), False),
                   BoardInfo(40801, 0, 0, LVL_IMMORT,
                             ('gwar'), False),
                   BoardInfo(40832, 0, 0, LVL_IMMORT,
                             ('imperial_knights'), False),
                   BoardInfo(40902, 0, 0, LVL_IMMORT,
                             ('evil_empire'), False),
                   BoardInfo(41004, 0, 0, LVL_ETERNAL_GOD,
                             ('widowmaker'), False),
                   BoardInfo(41106, 0, 0, LVL_DEMIGOD,
                             ('valheru'), False),
                   BoardInfo(41131, 0, 0, LVL_IMMORT,
                             ('magic_roundabout'), False),
                   BoardInfo(41171, 0, 0, LVL_IMMORT,
                             ('ahroun'), False)]

class NumberOfMessages(Record, metaclass=BuildRecordClass):
    Fields = [('number', Record.Int)]

class BoardMessageInfo(Record, metaclass=BuildRecordClass):
    Fields = [('slot_num'   , Record.Int     ),
              # XXX This should be hacked ito a four-byte type
              ('heading'    , Record.Pointer ), # Unused
              ('level'      , Record.Int     ),
              ('heading_len', Record.Int     ),
              ('message_len', Record.Int     ),
              # XXX This should be hacked into a four-byte type
              ('birth'      , Record.TimeT   )]

class BoardMessageInfo_Compat(Record, metaclass=BuildRecordClass):
    # All of these fields assume files created on a 32-bit machine.
    Fields = [('slot_num'   , Record.Int     ),
              ('heading'    , Record.Int     ), # Unused
              ('level'      , Record.Int     ),
              ('heading_len', Record.Int     ),
              ('message_len', Record.Int     ),
              ('birth'      , Record.Int     )]

class BoardMessage:
    def __init__(self, info, header, message):
        self.info = info
        self.header = header
        self.message = message

    def __str__(self):
        return '%s\n%s' % (self.header, self.message)

def ReadBoardFile(fp, compat = False):
    nr = ReadOneFromFile(fp, NumberOfMessages)
    recordClass = BoardMessageInfo_Compat if compat else BoardMessageInfo
    for x in range(nr.number):
        msginfo = ReadOneFromFile(fp, recordClass)
        yield BoardMessage(msginfo,
                           header = ReadBytes(fp, msginfo.heading_len),
                           message = ReadBytes(fp, msginfo.message_len))

def LoadBuiltinBoards(base, compat = False):
    from os.path import join as joinpath
    for board in _builtin_boards:
        fp = open(joinpath(base, board.filename))
        messages = list(ReadBoardFile(fp, compat = compat))
        yield (board, messages)

BOARD_INFO_TEMPLATE = '''vnum: %d
read-level: %d
write-level: %d
remove-level: %d
auto-cleanup: %s
'''

def getBoardInfoString(board):
    return BOARD_INFO_TEMPLATE % \
           (board.vnum, board.read_lvl, board.write_lvl,
            board.remove_lvl, board.auto_cleanup)

from datetime import datetime
def getBoardMessageBoxString(messages):
    # return one string with all messages in multipart format.
    from io import StringIO
    buf = StringIO()

    for msg in messages:
        body = msg.message + '\n\n'

        print('Content-Length  : %d' % len(body), file=buf)
        print('X-Heading       : %s' % msg.header, file=buf)
        print('X-Level         : %d' % msg.info.level, file=buf)
        print('Date            : %s' % datetime.fromtimestamp(msg.info.birth).ctime(), file=buf)
        print('X-tra           : slot_num = %d' % msg.info.slot_num, file=buf)
        print(file=buf)
        buf.write(body)

    return buf.getvalue()

def main(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-z', '--zip-file')
    parser.add_option('--compat', action = 'store_true')
    (options, args) = parser.parse_args(argv)

    if len(args) > 0:
        base = args[0]

        if options.zip_file:
            from zipfile import ZipFile
            zf = ZipFile(open(options.zip_file, 'w'), 'w')

        # import pdb; pdb.set_trace()

        for (board, messages) in LoadBuiltinBoards(base, compat = options.compat):
            if options.zip_file:
                zf.writestr('%s/INFO' % board.name, getBoardInfoString(board))
                zf.writestr('%s/MESSAGES' % board.name, getBoardMessageBoxString(messages))
            else:
                print(board)
                for msg in messages:
                    print(msg)

if __name__ == '__main__':
    main()
