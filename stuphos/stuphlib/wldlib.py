#!/usr/local/bin/python
'World-Aggregator'

# Core.
from .dblib import flagNames, INDEX_FILE, LocalIndex, Zonefix

from .zonelib import ZoneReader
from .roomlib import RoomReader
from .objlib import ObjectReader
from .moblib import MobileReader

from .dblib import directionName, directionIndicator, directionByName
from .dblib import doorState, wearPosition
from .dblib import zoneFlagNames, resetModeName
from .dblib import roomFlagNames, roomSectorName

class WorldBase:
    class Mixin:
        # For access to proper direct manipulation of the world instance.
        def lock(self):
            pass
        def unlock(self):
            pass

        def __getitem__(self, *args):
            return self.zones.__getitem__(*args)
        def __setitem__(self, *args):
            return self.zones.__setitem__(*args)

        def __repr__(self):
            return '<World %r (%d zones)>' % (self.fileBase, len(self.zones))

        def __iter__(self):
            return iter(self.zones.values())

# Foundation.

#
## Start generic.
# Note: this shares code with .runtime.architecture.Object, but there's still some
# reason to keep this package independent of the rest of stuphos.
class Object:
    class Meta:
        __attributes__ = ()

        @staticmethod
        def formatAttribute(instance, a):
            if type(a) in (list, tuple):
                if len(a) == 2:
                    return '%s = %r' % (a[0], getattr(instance, a[1]))
                if len(a) == 3:
                    return '%s = %r' % (a[0], getattr(instance, a[1], a[2]))
            elif type(a) is str:
                return '%s = %r' % (a, getattr(instance, a))

        @staticmethod
        def className(instance):
            return instance.__class__.__name__

        @classmethod
        def instanceRepr(self, instance):
            meta = instance.Meta
            attribs = ', '.join(meta.formatAttribute(instance, a) for \
                                a in meta.__attributes__)
            if attribs:
                return '<%s %s>' % (meta.className(instance), attribs)

            return '<%s>' % meta.className(instance)

    def __repr__(self):
        return self.Meta.instanceRepr(self)

    __str__ = __repr__

class Initializer(Object):
    class Meta(Object.Meta):
        __attributes__ = Object.Meta.__attributes__ + ('__dict__',)

    # Pattern encapsulates a dict within an attributable instance.
    def __init__(self, dict = None, **kwd):
        if dict is None:
            dict = {}

        dict.update(kwd)
        self.__dict__ = dict
    def update(self, **dict):
        self.__dict__.update(dict)
        return self # Method-chaining.

## End generic
#

class Record(Initializer):
    '''
    Pattern allows one of the world libdata reader classes
    to initialize this object, using lshift:

        class X(Record):
            def loadFrom(self, code):
                reader = RecordReader('x-%s.rec' % code)
                return self.genericLoadFromReader(reader)

        x = (X() << 'info')

    '''
    def __lshift__(self, *args, **kwd):
        self.loadFrom(*args, **kwd)

        # In-place operation; Method-chaining.
        return self

    def loadFromReader(self, reader):
        reader.parseFile()
        self.__dict__.update(reader.consumeRecordSet())

    # Default Behavior.
    loadFrom = loadFromReader

    ReaderClass = None
    def loadFromFile(self, file):
        return self.loadFromReader(self.ReaderClass(file))

# Entities.
class ZoneBase(Record):
    class ZCommand(Initializer):
        class Meta(Object.Meta):
            __attributes__ = ['type', 'conditional', 'arg1', 'arg2', 'arg3']

        class Arg:
            path = name = vnum = ''

        class EntityArg(Arg):
            @staticmethod
            def capfirst(s):
                return s[0].upper() + s[1:].lower()

            def __init__(self, world, vnum, type, **kwd):
                self.vnum = vnum
                self.path = '%s/%s' % (type.lower(), vnum)

                lookup = 'lookup' + self.capfirst(type)
                lookup = getattr(world, lookup)
                lookup = lookup(vnum)

                self.entity = lookup or ''
                self.name = getattr(lookup, 'name', '')

                self.__dict__.update(kwd)

        class MaxExistArg(Arg):
            def __init__(self, max):
                self.maximum = max
                self.name = '%s maximum' % max

        class WearPosArg(Arg):
            def __init__(self, world, pos):
                    self.position = pos
                    self.name = wearPosition(pos)

        class DirArg(Arg):
            def __init__(self, world, dir):
                    self.direction = dir
                    self.name = directionName(dir)

        class DoorArg(Arg):
            def __init__(self, world, state):
                    self.doorState = state
                    self.name = doorState(state)

        NullArg = Arg()

        def __init__(self, cmdtype, conditional, args, **kwd):
            arg1 = args[0]
            arg2 = args[1]
            arg3 = args[2] if len(args) > 2 else None

            Initializer.__init__(self,
                                 type = cmdtype,
                                 conditional = conditional,
                                 arg1 = arg1,
                                 arg2 = arg2,
                                 arg3 = arg3,
                                 **kwd)

        @property
        def name(self):
            return {'M': 'Load Mobile',
                    'O': 'Load Item',
                    'G': 'Give Item to Mobile',
                    'E': 'Equip Mobile',
                    'P': 'Put Item in Item',
                    'R': 'Remove Item from Room',
                    'D': 'Set Door State',
                    'U': 'Mount Mobile'} \
                    .get(self.type, "<Unknown '%c'>" % self.type)

        @property
        def args(self):
            'Return a resolved form of the arguments based on command type.'
            world = self.zone.world

            if self.type == 'M':
                    return [self.EntityArg(world, self.arg1, 'mobile'),
                            self.EntityArg(world, self.arg3, 'room'),
                            self.MaxExistArg(self.arg2)]

            if self.type == 'O':
                    return [self.EntityArg(world, self.arg1, 'item'),
                            self.EntityArg(world, self.arg3, 'room'),
                            self.MaxExistArg(self.arg2)]

            if self.type == 'G':
                    return [self.EntityArg(world, self.arg1, 'item'),
                            self.NullArg,
                            self.MaxExistArg(self.arg2)]

            if self.type == 'E':
                    return [self.EntityArg(world, self.arg1, 'item'),
                            self.WearPosArg(world, self.arg3),
                            self.MaxExistArg(self.arg2)]

            if self.type == 'P':
                    return [self.EntityArg(world, self.arg1, 'item'),
                            self.EntityArg(world, self.arg3, 'item'),
                            self.MaxExistArg(self.arg2)]

            if self.type == 'R':
                    return [self.EntityArg(world, self.arg2, 'item'),
                            self.EntityArg(world, self.arg1, 'room'),
                            self.NullArg]

            if self.type == 'D':
                    return [self.EntityArg(world, self.arg1, 'room'),
                            self.DirArg(world, self.arg2),
                            self.DoorArg(world, self.arg3)]

            if self.type == 'U':
                    return [self.EntityArg(world, self.arg1, 'mobile'),
                            self.EntityArg(world, self.arg3, 'mobile'),
                            self.MaxExistArg(self.arg2)]

            return [NullArg] * 3

    def __init__(self, world, vnum):
        """
        First argument is the base lib/world path.

        Second argument is the virtual no of this zone.  Note that zones can span
        multiple virtual numbers for room, object, and mobile sets.

        """
        Initializer.__init__(self)
        self.world = world

        # Load this record.
        (self) << (vnum)

        # Initialize further records.
        self.roomMap = {}
        self.mobileMap = {}
        self.itemMap = {}

    # Implementation of Record.
    ReaderClass = ZoneReader
    def loadFrom(self, vnum):
        return self.loadFromFile(self.world.fileBase.openZoneFile(vnum))

    # Properties.
    @property
    def resetModeName(self):
        return resetModeName(getattr(self, 'reset-mode'))

    @property
    def span(self):
        v = int(self.vnum)
        t = int(self.top)/100

        if v == t:
            return v

        return (v, t)

    @property
    def spanName(self):
        s = self.span
        return (type(s) is int and '#%d' or 'Spanning [%d-%d]') % s

    def spanZones(self):
        # Generator
        s = self.span

        if type(s) is int:
            yield s
        else:
            for z in range(s[0], s[1]+1):
                yield z

    @property
    def flagNames(self):
        return zoneFlagNames(self.flags)

    @property
    def continentName(self):
        return continentName(self.continent)

    @property
    def numZCmds(self):
        c = getattr(self, 'commands', None)
        return c and len(c) or 0

    def __repr__(self):
        return '<Zone %s (%s) %d/%d/%d/%d cmds/rooms/objs/mobs, %s every %d>' % \
            (self.spanName, self.name, self.numZCmds,
            len(self.roomMap), len(self.itemMap), len(self.mobileMap),
            self.resetModeName, self.lifespan)

    def createZCommand(self, *args, **kwd):
        # Factory.
        # Note this doesn't currently call into world.
        return self.ZCommand(*args, **kwd)

    def createRoom(self, vnum, record):
        # Factory.
        return self.world.createRoom(vnum, self, record)

    def createItem(self, vnum, record):
        # Factory.
        return self.world.createItem(vnum, self, record)

    def createMobile(self, vnum, record):
        # Factory.
        return self.world.createMobile(vnum, self, record)

    def loadRooms(self):
        # Consume, load and update entire room record set:
        reader = RoomReader(self.world.fileBase.openRoomFile(self.vnum))
        Record(self.roomMap) << (reader)

        # Reload room entities handles.
        for (vnum, room) in self.roomMap.items(): # XXX Dict change exception??
            self.roomMap[vnum] = self.createRoom(vnum, room)

        return self # Method-Chaining.

    def loadMobiles(self):
        # Consume, load and update entire mobile prototype record set:
        reader = MobileReader(self.world.fileBase.openMobileFile(self.vnum))
        Record(self.mobileMap) << (reader)

        # Reload mobile entities handles.
        for (vnum, mob) in self.mobileMap.items(): # XXX Dict change exception??
            self.mobileMap[vnum] = self.createMobile(vnum, mob)

        return self # Method-Chaining.

    def loadItems(self):
        # Consume, load and update entire object prototype record set:
        reader = ObjectReader(self.world.fileBase.openObjectFile(self.vnum))
        Record(self.itemMap) << (reader)

        # Reload item entities handles.
        for (vnum, item) in self.itemMap.items(): # Dict change exception??
            self.itemMap[vnum] = self.createItem(vnum, item)

        return self # Method-Chaining.

    @property
    def zcommands(self):
        return [self.createZCommand(*zcmd, **{'zone': self}) \
                for zcmd in getattr(self, 'commands', [])]

    @property
    def rooms(self):
        # Ascending sort by vnum.
        items = list(self.roomMap.items())
        items.sort()

        # Undecorate.
        return [i[1] for i in items]

    @property
    def items(self):
        # Ascending sort by vnum.
        items = list(self.itemMap.items())
        items.sort()

        # Undecorate.
        return [i[1] for i in items]

    @property
    def mobiles(self):
        # Ascending sort by vnum.
        items = list(self.mobileMap.items())
        items.sort()

        # Undecorate.
        return [i[1] for i in items]

    def resolveRooms(self):
        'Resolve room exits.'
        # XXX Is this needed?  Use lookupRoom on roomlink.
        raise NotImplementedError

    # def resolve(self):pass

class Room(Initializer):
    "['sector', 'name', 'exits', 'text', 'flags', 'descr', 'vnum']"

    class Meta(Object.Meta):
        __attributes__ = ['vnum', 'name', 'sector', 'flags']

    NOWHERE = -1

    class Exit(Initializer):
        "['room-link', 'keyword', 'descr', 'key', 'flags']"

        class Meta(Object.Meta):
            __attributes__ = ['room-link', 'key', 'flags', 'keyword']

        @property
        def roomlink(self):
            return getattr(self, 'room-link')

        @property
        def name(self):
            return directionName(self.dir)

        @property
        def isPurged(self):
            return (self.roomlink == Room.NOWHERE)

    @property
    def flagNames(self):
        return roomFlagNames(self.flags)

    @property
    def sectorName(self):
        return roomSectorName(self.sector)

    def createExit(self, *args, **kwd):
        # Factory.
        # Note this doesn't currently call into world.
        return self.Exit(*args, **kwd)

    @property
    def exitdirs(self):
        try: exits = self.exits
        except AttributeError: pass
        else:
            for (dir, info) in exits.items():
                yield self.createExit(info, dir = dir)

    def __repr__(self):
        return '<Room #%5d:%.50s (%s)>' % (self.vnum, self.name,
                                           ', '.join(self.flagNames))

class Mobile(Initializer):
    class Meta(Object.Meta):
        __attributes__ = ['vnum', 'shortdescr']

class Item(Initializer):
    """
    ['extraflags', 'actiondescr', 'longdescr', 'name',      'weight', 'antiflags', 'affections',
     'shortdescr', 'minlevel',    'cost',      'wearflags', 'vals',   'vnum',      'type',
     'extradescr', 'timer',       'trap',      'specproc']
    """

    class Meta(Object.Meta):
        __attributes__ = ['vnum', 'shortdescr', 'typeName']

    item_types = [] # Todo

    @property
    def typeName(self):
        if type(self.type) is int:
            if self.type >= 0 and self.type < len(self.item_types):
                return self.item_types[self.type]
        return 'Type%s' % self.type

    extraFlagNamesDict = {} # Todo
    wearFlagNamesDict = {} # Todo
    antiFlagNamesDict = {} # Todo

    @property
    def extraFlagNames(self):
        return flagNames(self.extraFlagNamesDict, self.extraflags)
    @property
    def wearFlagNames(self):
        return flagNames(self.wearFlagNamesDict, self.wearflags)
    @property
    def antiFlagNames(self):
        return flagNames(self.antiFlagNamesDict, self.antiflags)

    @property
    def value1(self):
        return self.vals[0]
    @property
    def value2(self):
        return self.vals[1]
    @property
    def value3(self):
        return self.vals[2]
    @property
    def value4(self):
        return self.vals[3]

# Utility.
class WorldLoader(WorldBase, WorldBase.Mixin):
    'Encapsulate all zon/wld/obj/mob/shp/sch data into accessible object.'

    def __init__(self, fileBase, absindex = None, logStream = False):
        self.fileBase = fileBase
        self.absindex = absindex
        self.logStream = logStream

        self.zoneMap = {}

    def logMessage(self, msg):
        if self.logStream:
            self.logStream.write(msg)
            self.logStream.flush()

    # Sequential DB load.
    def readZoneIndex(self, index = INDEX_FILE):
        # Generates zone vnums from zone index file parameters.
        for (vnum, fix) in self.fileBase.iterindex(self.fileBase.superindex(index, fix = Zonefix)):
            yield vnum

    def createZone(self, vnum):
        # Factory.
        return ZoneBase(self, vnum)

    def createRoom(self, vnum, zone, record):
        # Factory.
        return Room(record, vnum = vnum, zone = zone)

    def createItem(self, vnum, zone, record):
        # Factory.
        return Item(record, vnum = vnum, zone = zone)

    def createMobile(self, vnum, zone, record):
        # Factory.
        return Mobile(record, vnum = vnum, zone = zone)

    def loadWorld(self, index = INDEX_FILE, cascade = False):
        '''
        Cascading Circle-like database load from zone index.
        Loads all zones from specified index absolute path or
        base.  If cascade is True, load all other elements
        that are kept under zone (which is pretty much everything).
        '''

        self.logMessage('Loading index %r from %r:\n' % (index, self.fileBase))
        for vnum in self.readZoneIndex(index = index):
            self.loadZone(vnum, cascade = cascade)

    loadFromZoneIndex = loadWorld

    def loadZone(self, vnum, cascade = True):
        self.logMessage('    Info on Zone #%3d...' % vnum)
        zone = self.zoneMap[vnum] = self.createZone(vnum)

        if cascade:
            self.logMessage('Rooms...')
            zone.loadRooms()

            self.logMessage('Items...')
            zone.loadItems()

            self.logMessage('Mobiles...')
            zone.loadMobiles()

        self.logMessage('\n')
        return zone

    @property
    def zones(self):
        # Ascending sort by vnum.
        items = list(self.zoneMap.items())
        items.sort()

        # Undecorate.
        return [i[1] for i in items]

    def lookupZone(self, vnum):
        return self.zoneMap.get(int(vnum))

    def lookupRoom(self, vnum):
        # This should be done sooner, too.
        vnum = int(vnum)
        try: return self.zoneMap[vnum / 100].roomMap[vnum]
        except KeyError:
            return None

    def lookupMobile(self, vnum):
        vnum = int(vnum)
        try: return self.zoneMap[vnum / 100].mobileMap[vnum]
        except KeyError:
            return None

    def lookupItem(self, vnum):
        vnum = int(vnum)
        try: return self.zoneMap[vnum / 100].itemMap[vnum]
        except KeyError:
            return None

## Unused:
class WorldScanner(WorldBase):
    # Alternative load methods -- Random Access.
    def scanStart(self):
        pass
    def scanComplete(self):
        pass

    def scanParts(self, **parts):
        'Adaptive load from indexed sources.  Serve parts back to caller.'

        # Generator
        from types import GeneratorType as generator
        g = self.scanStart()

        if type(g) is generator:
            for n in g:
                yield n

        # Index record sources individually: by entity-set file unit or zone list.
        if 'rooms' in parts:
            # Scan room parts
            r = parts['rooms']

            if type(r) is str:
                index = self.superindex(index = r, fix = Roomfix)
            elif bool(r):
                # On truth test load default index.
                index = self.superindex(fix = Roomfix)

            for roomfile in self.iterindex(index):
                for r in self.scanRoomfile(roomfile):
                    yield r

        # Todo: provide objects
        # Todo: provide mobiles

        if 'zcommands' in parts:
            # Scan zone commands.
            pass

        if 'zone_table' in parts:
            # Scan all loadable zone data.
            pass

        if 'text':
            # Text search all text-aware locations.
            pass

        # End of scan.  Try to call this before exiting this function.
        g = self.scanComplete()
        if type(g) is generator:
            for n in g:
                yield n

    # Transformer.
    roomResult = staticmethod(lambda rec:rec) # Room(rec)

    def scanRoomfile(self, filename, sorted = False):
        rooms = RoomReader(filename).parseFile().consumeRecordSet()
        order = list(rooms.keys())

        if sorted:
            order.sort()

        for rec in rooms:
            #
            # Return an instance wrapping the data, which has an accessible 'universalForm' method.
            #
            yield self.roomResult(rec)

World = WorldLoader

# Front End.
def parse_cmdln(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--cascade', action = 'store_true')
    parser.add_option('-i', '--inspect', action = 'store_true')
    parser.add_option('-z', '--zone-index', '--index')
    parser.add_option('-l', '--log-file')
    return parser.parse_args(argv)

def buildWorld(options, args):
    '''
    Originally took argv and optional cascadeOptionName arguments.

    Now call like so:
        argv = ['']
        argv.append('/StuphMUD/lib/world')
        argv.append('--zone-index=index.mini')
        argv.append('--cascade')

        (options, args) = parse_cmdln(argv)
        w = buildWorld(options, args)

    This is basically what main() does, except validates # of arguments and
    implements optional interactive inspection.
    '''

    # Operates directly on 
    base = LocalIndex(args[0])
    absindex = False
    loadOptions = {}

    if options.zone_index:
        loadOptions['index'] = options.zone_index
        # absindex = isAbsIndex(options.zone_index)
        absindex = None # fs detect

    if options.cascade:
        loadOptions['cascade'] = True

    if options.log_file == '--':
        from sys import stdout as logging
    elif options.log_file:
        logging = open(options.log_file, 'w')
    else:
        logging = None

    w = World(base, absindex = absindex, logStream = logging)
    w.loadFromZoneIndex(**loadOptions)

    return w

def main(argv = None):
    (options, args) = parse_cmdln(argv)

    if not args:
        parser.print_usage()
        return

    w = buildWorld(options, args)
    if options.inspect:
        inspect(world = w)

def inspect(**kwd):
    from code import InteractiveConsole as IC
    import readline

    global pf, pp, page
    from pprint import pprint as pp, pformat as pf

    vars = globals()
    vars.update(kwd)
    IC(locals = vars).interact(banner = '')

if __name__ == '__main__':
    main()
