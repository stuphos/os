'lib/etc/players'
__all__=['PLRFILE', 'PLRDBIntoSQL', 'DEFAULT_PLRFL', 'DEFAULT_STORE']

from struct import *
from os.path import exists

# C-Struct Format.
MAX_NAME_LENGTH=20
MAX_EMAIL_LENGTH=80
MAX_PWD_LENGTH=10
MAX_AFFECT=32
MAX_COLOR_SET=32
HOST_LENGTH=40
MAX_SKILLS=200
MAX_TONGUE=3

char_specials_fmt='i3l5h\n'
player_specials_fmt='%ds\n' % (calcsize('b') * MAX_SKILLS+1)
player_specials_fmt+='x\n'
player_specials_fmt+='%ds\n' % (calcsize('i') * MAX_TONGUE)
player_specials_fmt+='ibhI3lB3b3il3i\n'
abilities_fmt='7b\n'
points_fmt='12h3i2b\n'

affected_fmt='2h2bl\n'
affected_fmt+='%dx' % calcsize('P') # padd out next pointer

ending_padding='' # '1191x'

pfilel_fmt='%ds %ds 6i3bh2i2B %ds\n' % (MAX_NAME_LENGTH+1, MAX_EMAIL_LENGTH+1, MAX_PWD_LENGTH+1)
pfilel_fmt+=char_specials_fmt +player_specials_fmt +abilities_fmt +points_fmt
pfilel_fmt+='%ds' % (calcsize(affected_fmt) * MAX_AFFECT)
pfilel_fmt+='%ds' % (calcsize('i') * MAX_COLOR_SET)
pfilel_fmt+='2i'
pfilel_fmt+='%ds' % (HOST_LENGTH+1)
pfilel_fmt+=ending_padding

# Names.
saving_throw_names=('savingthrow1', 'savingthrow2', 'savingthrow3', 'savingthrow4', 'savingthrow5')

char_specials_names=('alignment', 'idnum', 'act', 'affectedby') +saving_throw_names
player_specials_names=('skills', 'talks', 'wimp', 'freeze', 'invis', 'loadroom',
                'pref', 'pref2', 'disp', 'badpws', 'drunk', 'hunger', 'thirst',
                'spells2learn', 'maritalstatus', 'num_marriages', 'spouse',
                'spellattack1', 'spellattack2', 'remortpoints')

abilities_names=('str', 'stradd', 'intel', 'wis', 'dex', 'con', 'cha')
points_names=('mana', 'maxmana', 'hit','maxhit', 'move', 'maxmove', 'deaths', 'mkills', 'pkills',
        'dts', 'qpoints', 'armor', 'gold', 'bank', 'exp', 'hitroll', 'damroll')

pfilel_names=('name', 'email', 'remort', 'race', 'clan', 'clanrank', 'pagelength', 'saveroom',
        'sex', 'chclass', 'level', 'hometown', 'birth', 'played', 'weight', 'height', 'pwd')\
        +char_specials_names +player_specials_names +abilities_names +points_names\
        +('affected', 'color', 'lastlogin', 'lastlogon', 'host')

pfilel_ncount=len(pfilel_names)
pfilel_types=['']*pfilel_ncount

# from structfmt import stfmti

#for n in 'pfilel_fmt', 'char_specials_fmt', 'player_specials_fmt', 'abilities_fmt', 'points_fmt', 'affected_fmt':
#   print n, `vars()[n]`, calcsize(vars()[n]), len(list(stfmti(vars()[n])))

#for n in 'pfilel_names', 'saving_throw_names', 'char_specials_names', 'player_specials_names', 'abilities_names', 'points_names':
#   print n, `vars()[n]`, len(vars()[n])

pfilel_size=calcsize(pfilel_fmt)
pfilel_sqldecl=', '.join([' '.join(p) for p in zip(pfilel_names, pfilel_types)])

# General Routines.
# ToDo: incorporate the original pfile-position

# Because of packing in the server code, the char_file_u struct
# does exactly match what we would expect to read with python
# struct.  This is a version-level hack to align properly.
ALIGNMENT_HACK_LEN = 1
ALIGNMENT_HACK_BUF = '\x00' * ALIGNMENT_HACK_LEN

def _read_player_buffer(playerfl):
    'Read one buffer capable of being unpacked a la pfilel_fmt.'

    b = playerfl.read(pfilel_size - ALIGNMENT_HACK_LEN)
    if b:
        return b + ALIGNMENT_HACK_BUF

    raise EOFError

def goto_pfilepos(fl, pfilepos):
    return fl.seek(pfilepos*pfilel_size)

def read_player(playerfl, pfilepos = None):
    if pfilepos is not None:
        goto_pfilepos(playerfl, pfilepos)

    return unpack(pfilel_fmt, _read_player_buffer(playerfl))

def write_player(plrrecord, playerfl, pfilepos = None):
    if pfilepos is not None:
        goto_pfilepos(playerfl, pfilepos)

    return playerfile.write(pack(pfilel_fmt, plrrecord))

class PlayerFileReader(object):
    "Iterate over load_source(filename)"

    def __init__(self, source):
        self.source = source

    def __repr__(self):
        return 'players: '+repr(self.source)
    def __iter__(self):
        return self.read_player_entries()

    def openPlayerFileSource(self, source):
        if type(source) is file:
            return file

        return open(source)

    def read_player_entries(self):
        'Generator -- Streams player records'
        plrfile = self.openPlayerFileSource(self.source)

        try:
            while True:
                yield unpack(pfilel_fmt, _read_player_buffer(plrfile))

        except EOFError:
            pass

## Aliases:
PLRFILEReader=PLRFILE=PlayerFileReader

def plr2dict(player):
    return dict((pfilel_names[i], player[i]) for i in range(len(pfilel_names)))
def dict2plr(dict):
    return tuple(dict[n] for n in pfilel_names)

def cstring(string):
    i = string.find('\x00')
    if i >= 0:
        return string[:i]

    return string

pfilel_conv = dict(name  = cstring,
                   host  = cstring,
                   email = cstring,
                   pwd   = cstring)

class Player:
    def __init__(self, record):
        # Generate tuple.
        if type(record) is file:
            record = read_player(record)
        elif type(record) is str:
            record = unpack(pfilel_fmt, record)

        # Generate dict.
        if type(record) is dict:
            record = record.copy()
        elif type(record) in (list, tuple):
            record = plr2dict(record)
        else:
            raise TypeError(type(record).__name__)

        # Convert.
        for (name, conv) in pfilel_conv.items():
            record[name] = conv(record[name])

        self.__dict__ = record

    def __iter__(self):
        gi = self.__dict__.__getitem__
        return (gi(n) for n in pfilel_names)

    def __repr__(self):
        return '<%s: %r [#%d]>' % (self.__class__.__name__,
                                   self.name, self.idnum)

DEFAULT_PFILE = 'lib/etc/players'

class PlayerIndex:
    def __init__(self, source, FileReaderClass = PlayerFileReader,
                 PlayerClass = Player):

        self.byName = dict()
        self.byIdnum = dict()

        for record in FileReaderClass(source):
            player = PlayerClass(record)
            self.byName[player.name] = player
            self.byIdnum[player.idnum] = player

    def __repr__(self):
        return '<%s (%d players)>' % (self.__class__.__name__, len(self))

    def __getitem__(self, item):
        if type(item) is int:
            return self.byIdnum[item]

        return self.byName[item]

    def __len__(self):
        return len(self.byName)
    def __iter__(self):
        return iter(self.byName.values())

    def idnums(self):
        return list(self.byIdnum.keys())
    def names(self):
        return list(self.byName.keys())

# Strings & Aliases.
def ReadStringsFile(file):
    from .dblib import FileReader
    reader = FileReader(file)

    return dict(title = reader.tildeString('title'),
                prename = reader.tildeString('prename'),
                wizname = reader.tildeString('wizname'),
                poofin = reader.tildeString('poofin'),
                poofout = reader.tildeString('poofout'),
                description = reader.tildeString('description'),
                plan = reader.tildeString('plan'))

class Alias:
    def __init__(self, name, replacement, complex = False):
        self.name = name
        self.replacement = replacement
        self.complex = bool(complex)

    def __repr__(self):
        return '<%s%s %s = %r>' % ('(complex)' if self.complex else '',
                                   self.name, self.replacement)

def ReadAliasFile(file, map = False):
    from .dblib import FileReader
    reader = FileReader(file)

    def _():
        # Generate alias structures.
        try:
            while True:
                yield Alias(reader.tildeString('alias name'),
                            reader.tildeString('alias replacement'),
                            (reader.readLine() == '1'))

        except EOFError:
            pass

    # Return an associative mapping keyed on alias name, or just the iterator.
    return dict((a.name, a) for a in _()) if map else _()

class PlrFileSupplemental:
    def __init__(self, name):
        self.name = name
        self.load()

    def __repr__(self):
        return '<%s for %s>' % (self.__class__.__name__, self.name)

    @property
    def filename(self):
        from stuphlib import directory as stuphdir
        return stuphdir.StuphLIB['PLAYER[%s]:%s' % (self.TOPIC, self.name)]

    def load(self):
        raise NotImplementedError
    def save(self):
        raise NotImplementedError

class Strings(PlrFileSupplemental):
    TOPIC = 'STRINGS'

    def load(self):
        self.strings = ReadStringsFile(self.filename)
        self.__getitem__ = self.strings.__getitem__
        self.__setitem__ = self.strings.__setitem__
        self.keys = self.strings.keys

class Aliases(PlrFileSupplemental):
    TOPIC = 'ALIAS'

    def load(self):
        self.aliases = ReadAliasFile(self.filename, map = True)
        self.__getitem__ = self.aliases.__getitem__
        self.keys = self.aliases.keys


# SQLITE
NEW_PLAYERS_TABLE='CREATE TABLE players(%s)' % ', '.join(pfilel_names)
NEW_PLAYER='INSERT OR REPLACE INTO players('+pfilel_sqldecl+') VALUES('+', '.join(['?']*pfilel_ncount)+')'

#pfilel_types=('varchar(%d)'%MAX_NAME_LENGTH+1, 'varchar(%d)'%MAX_EMAIL_LENGTH+1)+('integer',)*6

class PLRDBIntoSQL(PlayerFileReader):
    "Plugs a PLRFILE into an SQLite database"

    def __init__(self, store=None, loadsource=None):
        # PlayerFileReader.__init__(self)
        self.open_store(type(store) is str and (store,) or store)
        if loadsource:
            self.save_players(self.read_player_entries(loadsource))

    def write_player(self, player, pfilepos = 0):
        'Install player into cursory connection'
        # from pprint import pprint as pp
        # pp(player)
        # raw_input()
        # print 'len(player[1])', len(player[1])

        self.x(NEW_PLAYER, player)
        # self.x('UPDATE players SET pfilepos=%d WHERE name=%r' % (pfilepos, player[1][0]))

    def save_players(self, players = None):
        "Stream all players given by the `players' iterable through write_player -- Also creates self.stmts and self.players."
        plrs=self.players=[]
        append=plrs.append

        stmts=self.stmts=[]
        append2=stmts.append

        pfilepos=0
        for p in players:
            append2(p[0])
            append(p[1])

            self.write_player(p, pfilepos)
            pfilepos+=1

        print('Saved', len(plrs), 'Players ...')

    def open_store(self, store):
        e=not exists(store[0])

        from pysqlite2 import dbapi2 as sqlite
        c=self.connection=sqlite.connect(*store)
        u=self.u=c.cursor()
        x=self.x=u.execute

        if e:
            x(NEW_PLAYERS_TABLE)
            x('ALTER TABLE players ADD (pfilepos)')

    def commit(self):
        self.connection.commit()

DEFAULT_PLRFL='lib/etc/players'
DEFAULT_STORE='lib/etc/players.db' # ':memory:'

def loadSql():
    from psyco import full;full()

    plrdb=PLRDBIntoSQL(DEFAULT_STORE)
    plrdb.save_players(plrdb.read_player_entries(DEFAULT_PLRFL))
    plrdb.commit()

    u=plrdb.u
    x=plrdb.x
    a=lambda:x('select * from players')

# Test Bed.
def read_player_analysis(playerfl):
    try:
        b=playerfl.read(pfilel_size - 1)
        if b == '':
            raise EOFError

        return unpack(pfilel_fmt, b + '\x00')

    except error as e:
        print('read/record: %d / %d' % (len(b), pfilel_size))
        raise e

def analyze_player_file(plrfile):
    nr_records = 0

    import os
    plrfile.seek(0, os.SEEK_END)
    bytes = plrfile.tell()
    print('size of player file:', bytes)
    print('number of entries:', float(bytes) / pfilel_size)
    plrfile.seek(0)

    try:
        while True:
            plr = read_player_analysis(plrfile)
            nr_records += 1

    except EOFError:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        print('number of records:', nr_records)

def readWholeFile(filename):
    from io import StringIO
    buf = StringIO()

    import os
    goal = os.stat(filename).st_size

    file = open(filename)
    size = 0
    while size < goal:
        b = file.read(512)
        if b == '':
            print('null read!')

        buf.write(b)
        size += len(b)

    buf.seek(0)
    print('read into buffer:', file.tell())
    return buf

# XML Generation.
def getTab(kwd):
    return kwd.pop('_tab', '  ') * kwd.pop('_indent', 0)

def getAttr(nv):
    return '%s="%s"' % nv

def xmlOpen(tag, **kwd):
    tab = getTab(kwd)
    close = kwd.pop('_close', False)
    attrs = ' '.join(getAttr(nv) for nv in kwd.items())
    return '%s<%s%s%s%s>' % (tab, tag, ' ' if attrs else '', attrs,
                             ' /' if close else '')

def xmlClose(tag, **kwd):
    return '%s</%s>' % (getTab(kwd), tag)

import base64
def base64_encode(value, **kwd):
    value = base64.encodestring(value)
    tab = getTab(kwd)
    if tab:
        value = tab + ('\n' + tab).join(value.split('\n'))

    return value

XML_SKIP = ['name', 'idnum']
XML_LONG_FORM = ['color', 'affected', 'skills', 'talks']
XML_ENCODING = dict(color    = ('base64', base64_encode),
                    affected = ('base64', base64_encode),
                    skills   = ('base64', base64_encode),
                    talks    = ('base64', base64_encode))

def generatePlayerFileXML(plrfile):
    index = PlayerIndex(plrfile)

    yield '<?xml version="1.0">'
    yield xmlOpen('playerIndex')
    for plr in index:
        yield xmlOpen('player', name = plr.name, idnum = plr.idnum, _indent = 1)
        for attr in pfilel_names:
            if attr in XML_SKIP:
                continue

            value = getattr(plr, attr)
            encoding = XML_ENCODING.get(attr)
            if encoding is not None:
                (encoding, encode) = encoding
                value = encode(value, _indent = 3)

            if attr in XML_LONG_FORM:
                if encoding:
                    opening = xmlOpen(attr, encoding = encoding, _indent = 2)
                else:
                    opening = xmlOpen(attr, _indent = 2)

                if type(value) in (str, str):
                    newline = value.rfind('\n')
                    if newline < 0:
                        yield '%s%s%s' % (opening, value, xmlClose(attr))
                    else:
                        yield '%s\n%s%s%s' % (opening, value,
                                              '\n' if newline != (len(value) - 1)
                                                else '',
                                              xmlClose(attr, _indent = 2))

            else:
                yield xmlOpen(attr, value = value, _indent = 2, _close = True)

        yield xmlClose('player', _indent = 1)

    yield xmlClose('playerIndex')

def reportPlayerFileXML(plrfile):
    for line in generatePlayerFileXML(plrfile):
        print(line)

class JSONPlayerFileReader(PlayerFileReader):
    # Attempts to verify that the player record is jsonifiable.
    # It does this by encoding the following fields:
    ENCODE_FIELDS = ['color', 'affected', 'skills', 'talks']
    CSTRIP_FIELDS = ['name', 'email', 'pwd', 'host']

    # If it finds that it cannot jsonify the result, it skips
    # the record (because it is malformed anyway).
    def read_player_entries(self):
        from sys import stderr
        nr = 0
        for record in super(self.__class__, self).read_player_entries():
            # Make mutable:
            record = list(record)
            nr += 1

            for field in self.ENCODE_FIELDS:
                i = pfilel_names.index(field)
                record[i] = base64_encode(record[i])

            # what about pfilel_conv?
            for field in self.CSTRIP_FIELDS:
                i = pfilel_names.index(field)
                record[i] = cstring(record[i])

            invalid = self.json_invalid(record)
            if invalid:
                print('record #%d:' % nr, file=stderr)
                for i in range(len(pfilel_names)):
                    invalid = self.json_invalid(record[i])
                    if invalid:
                        print('  %s: %s' % (pfilel_names[i], invalid), file=stderr)
            else:
                # Make immutable, again:
                yield tuple(record)

    try: from django.utils.simplejson import dumps as _json_dumps
    except ImportError:
        try: from json import dumps as _json_dumps
        except ImportError:
            from simplejson import dumps as _json_dumps

    _json_dumps = staticmethod(_json_dumps)

    def json_invalid(self, object):
        try: self._json_dumps(object)
        except Exception as e: return str(e)
        else: return False

def reportPlayerFileJSON(plrfile, stream = False):
    # from simplejson import dump
    from json import dump
    from sys import stdout

    # One big record:
    players = PlayerIndex(plrfile, FileReaderClass = JSONPlayerFileReader)

    if stream:
        for plr in players:
            dump(list(plr), stdout)
    else:
        # players = tuple(tuple(plr) for plr in players)
        players = list(map(list, players))

        dump(players, stdout)

def report_player_file(plrfile, options):
    index = PlayerIndex(plrfile)
    print(index)
    for plr in index:
        print('%-15s [%s]' % (plr.name, plr.email))

def parse_cmdln(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-r', '--report', action = 'store_true')
    parser.add_option('-x', '--xml', action = 'store_true')
    parser.add_option('-j', '--json', action = 'store_true')
    parser.add_option('-s', '--stream', action = 'store_true')

    parser.add_option('-f', '--filename')

    parser.add_option('-g', '--debug', action = 'store_true')
    parser.add_option('-b', '--buffer', action = 'store_true')
    return parser.parse_args()

def main(argv = None):
    from pdb import runcall
    (options, args) = parse_cmdln(argv)

    plrfile = options.filename
    if not plrfile:
        plrfile = args[0] if args else r'H:\StuphMUD\lib\etc\players'

    # Just report what we can.
    if options.report:
        if options.xml:
            reportPlayerFileXML(plrfile)
        elif options.json:
            if options.debug:
                runcall(reportPlayerFileJSON, plrfile, options.stream)
            else:
                reportPlayerFileJSON(plrfile, options.stream)
        else:
            report_player_file(plrfile)
    else:
        # Read entire file into buffer before analysis. (Pythonwin)
        if options.buffer:
            plrfile = readWholeFile(plrfile)
        else:
            plrfile = open(plrfile)

        # Perform analysis read. (careful)
        if options.debug:
            runcall(analyze_player_file, plrfile)
        else:
            analyze_player_file(plrfile)

if __name__=='__main__':
    main()

'''
AppEngine:                 AE           Ormus        Difference
21s 81s 6i3bh2i2B 11s    : 157          157
i3l5h                    : 42           26           > 16
201s                     : 201          201
x                        : 1            1
12s                      : 12           12
ibhI3lB3b3il3i           : 76           56           > 20
7b                       : 7            7
12h3i2b                  : 38           38
768s128s2i41s            : 945          689          > 256

                                                     > 292 bytes

Ormus:
21s 81s 6i3bh2i2B 11s    : 157
i3l5h                    : 26
201s                     : 201
x                        : 1
12s                      : 12
ibhI3lB3b3il3i           : 56
7b                       : 7
12h3i2b                  : 38
512s128s2i41s            : 689
'''
