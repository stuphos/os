'Base classes and utility functions for reading StuphMUD (Circle) world files.'

# Written by Fraun
# Todo: Rename RecordReader to RecordSetReader, derived from RecordReader which
#    only defines access of a single record.  Override parseFile as appropriate.

MINDEX_FILE  = 'index.mini'
INDEX_FILE   = 'index'
RINDEX_FILE  = 'index.reduced'

Zonefix = 'zon'
Roomfix = 'wld'
Objfix  = 'obj'
Mobfix  = 'mob'

class FormatError(Exception):
    def __init__(self, reason, cause = None, lineno = None):
        Exception.__init__(self, reason)
        self.cause = cause
        self.lineo = lineno

def ASCIIFlagDecode(flagstr):
    """Return packed integer bitvector representation of flag string as used in Circle MUD.

    bitvector_t asciiflag_conv(char *flag)
    {
          bitvector_t flags = 0;
          int is_num = TRUE;
          char *p;

          for (p = flag; *p; p++) {
            if (islower(*p))
              flags |= 1 << (*p - 'a');
            else if (isupper(*p))
              flags |= 1 << (26 + (*p - 'A'));

            if (!isdigit(*p))
              is_num = FALSE;
          }

          if (is_num)
            flags = atol(flag);

          return (flags);
    }
    """

    # Start bitvector value buffer at 0
    # For each character, set the nth bit, where n is:
    #    For lowercase characters, n is the offset into the alphabet (zero-based)
    #    For the uppercase, n is is the offset into the alphabet (zero-based), plus 26
    # (This makes valid bit-chars: a-zA-F)
    # Ignore all other characters
    # If all characters are digits, convert to long and that's the result
    # Otherwise, char-to-bit conversion is done, the value buffer is the result

    lowndx='abcdefghijklmnopqrstuvwxyz'.find # Find is faster: skips 1 instruction
    highndx='ABCDEF'.find

    bits=0
    numval=None # Need three values here

    for c in flagstr:
        if c.islower():
            bits|=1<<lowndx(c) # Guaranteed
        elif c.isupper():
            i=highndx(c)
            if i>-1:
                bits|=1<<(i+26) # Use long to suppress signage warning

        if not c.isdigit():
            numval=False
        elif numval is None:
            numval=True # Only occurs when there is at least a single digit

    if bool(numval): # False if None (no characters)
        return int(flagstr)

    return bits

def ASCIIFlagEncode(bits):
    flagstr=''
    for i in range(25):
        b=1<<i
        if bits&b==b:
            flagstr+='abcdefghijklmnopqrstuvwxyz'[i]

    for i in range(6):
        b=1<<(i+26)
        if bits&b==b:
            flagstr+='ABCDEF'[i]

    return flagstr

def flagNames(g, v):
    'sprintbit equivilant.'
    n = []
    a = n.append

    for x in list(g.keys()):
        b = (1 << x)
        if (v & b) == b:
            a(g[x])

    return n

# from string import printable
printable='~`!1@2#3$4%5^6&7*8(9)0_-+=QqWwEeRrTtYyUuIiOoPp{[}]AaSsDdFfGgHhJjKkLl:;"\'ZzXxCcVvBbNnMm,,>.?/|\\'

# Make this puppy printable!
def makePrintable(c):
    'An invalid file might contain binary data so this prevents a spam.'
    return (c in printable) and c or ('\\x%02x' % c)

import re
DICE_PATTERN = re.compile('([0-9\-]+)d([0-9\-]+)\+([0-9\-]+)')

def parseDice(dice):
    match = DICE_PATTERN.match(dice)
    assert match is not None, FormatError('Expected dice format (XdX+X) got: %r' % dice)
    return match.groups()

def isFileLike(file):
    for attr in ['read', 'readline']:
        if hasattr(file, attr):
            return True

    return False

class FileReader:
    libPath='lib'
    pathSep='/'

    def __init__(self, file):
        # from types import FileType
        from io import FileIO as FileType

        # Will likely be already opened by the wldlib.filesystem.
        fileType = type(file)

        # Want a file type
        if fileType is bytes:
            self.filename = file
            self.file = open(file)
        elif fileType is FileType:
            self.file = file
            self.filename = file.name
        elif fileType is int:
            # Shouldn't this be self.pathSep?
            self.filename = libPath + pathSep + str(file) + '.' + self.__class__.fileExtension
            self.file = open(self.filename)
        elif isFileLike(file):
            self.filename = file.name
            self.file = file
        else:
            raise TypeError(str(getattr(fileType, '__name__', '?')))

        self.lineno=0

    # Override this for other input methods
    def readLine(self):
        self.lineno+=1
        # todo: strip carriage returns.
        return self.file.readline() # .strip()

    def readLineNoEOF(self, errproc):
        self.lineno+=1

        n = self.file.readline() # .strip()
        if n != '':
            return n

        ##  if type(errproc) is str:
        ##      raise self.error(errproc)

        raise self.error(str(errproc))

    def error(self, msg):
        return FormatError('%s (%s:line %d)' % (msg, self.filename, self.lineno),
                           lineno = self.lineno)

    def tildeString(self, area='no particular'):
        'Read lines from file until terminated by "~\n", removing this sequence.'

        # Todo: utilize ReadTildeString from textlib.
        buffer=[]
        append=buffer.append

        while 1:
            line=self.readLine()
            assert line != '', self.error('Area: %s [EOF expecting ~string]' % area)

            # XXX should not strip every line (is this done in C source??)
            line=line.strip()
            tildeNdx=line.find('~')
            last=len(line)-1

            if tildeNdx > -1:
                if tildeNdx == last and tildeNdx != 0:
                    line=line[:-1]
                    append(line)

                break

            else:
                append(line)


        # There is a tilde: put it on, break on ~\n
        buffer='\n'.join(buffer)

        return buffer

    def readInteger(self):
        return int(self.readLine().strip())

    def readFloat(self):
        return float(self.readLine().strip())

    # Introduced by shops: (which use the v3format)
    def readNumberList(self):
        nItems=self.readInteger()

        numbers=[];append=numbers.append

        if getattr(self, 'v3format'):
            # This is Circle 3.0 shops.
            while True:
                # Fraun Jan 4th 2006 - Convert to readFloat (from readInteger)
                item=self.readFloat()
                if item<0.0:
                    break

                append(item)

        else:
            while nItems>0:
                nItems-=1
                append(self.readInteger())

        return numbers

# Multiple record reading.
class RecordProducer:
    'Interface.'

    VirtualNRName = 'vnum'
    nameOfRecordSet = 'recordSet'
    nameOfCurrentRecord = 'current'

    # Beginning of records (start of file)
    def startOfRecords(self):
        pass

    # End of records (end of file)
    def endOfRecords(self):
        pass

    # Start of new current record
    def newRecord(self, vnum):
        pass

    # Delete result reference from this record and return it to caller
    def consumeRecordSet(self):
        pass

    produce = consumeRecordSet

    # New parsed field name=value pair for current record
    def recordField(self, name, value):
        pass

    def getCurrentRecord(self):
        pass

    def getRecordSet(self):
        pass

class RecordProducerStore(RecordProducer):
    'Default response to record production: Store in dictionary backend.'

    def startOfRecords(self):
        setattr(self, self.nameOfRecordSet, {})

    def endOfRecords(self):
        if hasattr(self, self.nameOfCurrentRecord):
            delattr(self, self.nameOfCurrentRecord)

    def newRecord(self, vnum):
        r = {self.VirtualNRName:vnum}
        setattr(self, self.nameOfCurrentRecord, r)
        getattr(self, self.nameOfRecordSet)[vnum] = r

        # Usable?
        # return r

    def consumeRecordSet(self):
        r = getattr(self, self.nameOfRecordSet)
        delattr(self, self.nameOfRecordSet)

        return r

    def getCurrentRecord(self):
        return getattr(self, self.nameOfCurrentRecord)

    def getRecordSet(self):
        return getattr(self, self.nameOfRecordSet)

    def recordField(self, name, value):
        getattr(self, self.nameOfCurrentRecord)[str(name)] = value

    def getVirtualNumber(self):
        return getattr(self, self.nameOfCurrentRecord)[self.VirtualNRName]

# Fraun Dec 24th 2005 - Renamed from FileReader2 to RecordReader.
class RecordReader(FileReader, RecordProducerStore):
    'Implements commonalities between the parsers connoting structure.'

    MALFORMED_FIRST_RECORD_FMT = 'Malformed first record header %c%r (expected #<Virtual NR>)'

    def EOFNoDollar(self):
        raise self.error('Expected $ (dollar) to end records at EOF')

    def parseFile(self):
        'Initiates the parse of that file initialized in the constructor.'
        line = self.readLineNoEOF('Empty File')
        c = line[0]

        if c == '#':
            self.startOfRecords()

            vnum = int(line[1:])
            while vnum != None:
                self.newRecord(vnum)
                vnum = self.parseRecord()

            self.endOfRecords()

        elif c != '$':
            raise self.error(self.MALFORMED_FIRST_RECORD_FMT % (c, line))
        else:
            # Simulate empty record set.
            self.startOfRecords()
            self.endOfRecords()

        return self # Method chaining.

    def parseRecord(self):
        'Override this.'

    def readNextVnum(self):
        line = self.readLineNoEOF('Expected #<vnum> of next record').strip()
        if line[:1] == '$':
            return None

        assert line[:1] == '#', self.error('Expected #<vnum> of next record; got %r' % line[1:])

        try: return int(line[1:])
        except ValueError:
            raise self.error('Expected #<vnum> of next record; got %r' % line[1:])

class SingleRecordReader(RecordReader):
    # XXX how-the-fuck do I do this?
    pass

# Index File System.
def iterindex(index):
    for n in index:
        n = n.strip()
        if n == '$':
            break

        n = n.split('.')
        n[0] = int(n[0])
        yield n

def isAbsIndex(index):
    return (len(index) > 0 and (index[0] == '/')) or (len(index) > 1 and (index[1] == ':'))

class Index:
    'The general file-access routines, meant to abstract away from disk.'
    # FileBase: Merges FileSystem, Source/Store and Index.

    # Low-Level.
    def open(*args, **kwd):
        raise NotImplementedError
    def joinpath(*args, **kwd):
        raise NotImplementedError

    # Mid-Level.
    def fileName(self, vnum, fix):
        return self.joinpath(fix, '%d.%s' % (vnum, fix))

    # High-Level -- Index.
    def detectAbsIndex(self, index):
        return isAbsIndex(index)

    def superindex(self, index = INDEX_FILE,
                   absindex = False, fix = None):

        if absindex is None:
            absindex = self.detectAbsIndex(index)

        if not absindex:
            assert fix
            index = self.joinpath(fix, index)

        elif fix:
            index = self.joinpath(fix, index)

        return index

    def iterindex(self, index):
        return iterindex(self.open(index))

    def zonfile(self, vnum):
        return self.fileName(vnum, Zonefix)
    def roomfile(self, vnum):
        return self.fileName(vnum, Roomfix)
    def objfile(self, vnum):
        return self.fileName(vnum, Objfix)
    def mobfile(self, vnum):
        return self.fileName(vnum, Mobfix)

    def openZoneFile(self, vnum):
        return self.open(self.zonfile(vnum))
    def openRoomFile(self, vnum):
        return self.open(self.roomfile(vnum))
    def openObjectFile(self, vnum):
        return self.open(self.objfile(vnum))
    def openMobileFile(self, vnum):
        return self.open(self.mobfile(vnum))

class LocalIndex(Index):
    from os.path import join as joinpath
    joinpath = staticmethod(joinpath)

    def __init__(self, root):
        self.root = root

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.root)

    def open(self, path, *args, **kwd):
        # Open relative from root.
        # XXX this breaks notions of absindex
        # Todo: collapse/normpath this.
        return open(self.joinpath(self.root, path), *args, **kwd)

# Archive Index Systems.
from io import StringIO

class ArchiveIndex(Index):
    # Build routines:
    @classmethod
    def openBuffer(self, buffer, filename = None):
        buffer.filename = filename
        buffer.name = filename # For ZipFile

        return self(buffer)

    @classmethod
    def openFieldStorage(self, storage, filename = None):
        return self.openBuffer(StringIO(storage.value),
                               filename = filename)

# Archive Provisions.
import zipfile

class ZipArchiveIndex(ArchiveIndex):
    # XXX prefix might not be needed anymore.
    def __init__(self, base):
        self.zipfile = zipfile.ZipFile(base)
        self.prefix = self.zipfile.filename + '/'
        self.prefix_len = len(self.prefix)

    def open(self, name):
        if name.startswith(self.prefix):
            name = name[self.prefix_len:]

        buf = StringIO(self.zipfile.read(name))
        buf.name = '%s%s' % (self.prefix, name)
        return buf

    def joinpath(self, *parts):
        return '/'.join(parts)

class TarArchiveIndex(ArchiveIndex):
    # XXX Impl.
    pass

_archive_index_typemap = dict(zip   = ZipArchiveIndex,
                              tar   = TarArchiveIndex,
                              gz    = TarArchiveIndex,
                              gzip  = TarArchiveIndex,
                              bz2   = TarArchiveIndex,
                              bzip2 = TarArchiveIndex)

def getFileExtension(name):
    # os.path.splitext is platform-dependent.
    i = name.rfind('.')
    if i >= 0:
        if name.rfind('/') < i:
            # (within this basename)
            return name[i+1:]

    return ''

def detectArchiveIndexType(base):
    typeName = getFileExtension(base).lower()
    return _archive_index_typemap.get(typeName)

# Factories.
##    def buildArchiveIndex(base, filename = None):
##        fstype = detectArchiveIndexType(filename or base)
##        if fstype is not None:
##            return fstype(base, filename = filename)

# XXX Needs Compat:
#   Now, using detectArchiveIndexType, obtain indexClass
#   and then call appropriate build routines.


# Routines.
def IsBitSet(vector, bit):
    return bool(vector & bit)
def SetBit(vector, bit):
    return (vector | bit)
def RemoveBit(vector, bit):
    return (vector | ~(bit))

def getFlagBit(flags, name):
    # Eww..
    flags = list(flags.values())
    lname = name.lower()

    for bit in range(len(flags)):
        if flags[bit].lower() == lname:
            return bit

    raise NameError(name)

def getFlagVector(flags, name):
    return (1 << getFlagBit(flags, name))

def IsFlagSet(vector, flags, name):
    return IsBitSet(vector, getFlagVector(flags, name))
def SetFlag(vector, flags, name):
    return SetBit(vector, getFlagVector(flags, name))
def RemoveFlag(vector, flags, name):
    return RemoveBit(vector, getFlagVector(flags, name))

from .constants import _level_names, zoneFlagNamesDict, _reset_mode_names, _continents
from .constants import _directions, _room_sectors, _movement_loss, roomFlagNamesDict
from .constants import _door_states, _wear_positions

def GetLevelName(level):
    try: return _level_names[level]
    except KeyError:
        raise ValueError(level)

def GetSectorMoveCost(sector1, sector2):
    # move points needed is avg. move loss for src and destination sect type
    return (_movement_loss.get(sector1, 0) + \
            _movement_loss.get(sector2, 0)) / 2

def zoneFlagNames(flags):
    return flagNames(zoneFlagNamesDict, flags)

def resetModeName(reset_mode):
    return _reset_mode_names.get(reset_mode) or \
           ('Reset Mode #%s' % reset_mode)

def continentName(continent):
    return _continents.get(continent) or \
           'Continent #%s' % continent

def directionName(dir):
    return {0: 'north', 1: 'east', 2: 'south',
            3: 'west',  4: 'up',   5: 'down'} \
            .get(dir) or 'Unknown: %s' % dir

def directionIndicator(dir):
    try: return _directions[int(dir)]
    except (IndexError, ValueError):
        return ''

def directionByName(dir):
    return {'north': 0, 'east': 1, 'south': 2,
            'west' : 3, 'up'  : 4, 'down' : 5}.get(str(dir))

def numberOfDirections():
    return len(_directions)

def doorState(state):
    return _door_states.get(state) or 'Door State: %s' % state

def wearPosition(pos):
    return _wear_positions.get(pos) or 'Wear Position: %s' % pos

def roomFlagNames(flags):
    return flagNames(roomFlagNamesDict, flags)

def roomSectorName(sector):
    return _room_sectors.get(sector) or 'Sector #%s' % sector

from .constants import _preference_bits, _preference_bits2
def allPreferenceFlagNames(vector1, vector2):
    return flagNames(_preference_bits, vector1) + \
           flagNames(_preference_bits2, vector2)

def isPreferenceFlagSet(vector1, vector2, name):
    try: return isPreference1FlagSet(vector1, name)
    except NameError:
        return isPreference2FlagSet(vector2, name)

def isPreference1FlagSet(vector, name):
    return IsFlagSet(vector, _preference_bits, name)
def isPreference2FlagSet(vector, name):
    return IsFlagSet(vector, _preference_bits2, name)

def preference1FlagNames(vector):
    return flagNames(_preference_bits, vector)
def preference2FlagNames(vector):
    return flagNames(_preference_bits2, vector)

def setPreference1Flag(vector, name):
    return SetFlag(vector, _preference_bits, name)
def setPreference2Flag(vector, name):
    return SetFlag(vector, _preference_bits2, name)

def removePreference1Flag(vector, name):
    return RemoveFlag(vector, _preference_bits, name)
def removePreference2Flag(vector, name):
    return RemoveFlag(vector, _preference_bits2, name)
