from .dblib import *

defaultContinent = 0
validCmds = 'MOEPDRG'

class ZoneReader(RecordReader):
    # A ZoneReader always produces one record, so the record-set only
    # ever has one zone in it.

    VirtualNRName = 'vnum'
    nameOfRecordSet = nameOfCurrentRecord = 'zone'

    def startOfZone(self, vnum):
        self.zone = {'vnum': vnum}

    newRecord = startOfRecords = startOfZone

    def endOfZone(self):
        # Todo: Ensure presence of all attributes.
        pass

    endOfRecords = endOfZone

    def zoneField(self, name, value):
        self.zone[name] = value

    recordField = zoneField

    def zoneCommand(self, type, ifFlag, args):
        cmd = (type, ifFlag, args)
        r = self.zone # self.getCurrentRecord()

        if 'commands' in r:
            r['commands'].append(cmd)
        else:
            r['commands'] = [cmd]

    def disabledZoneCommand(self, line):
        ## print 'Disabled: '+repr(line)
        pass

    def parseZone(self):
        line=self.readLine()
        if line[0] != '#':
            raise FormatError()
        self.startOfZone(int(line[1:]))

        self.zoneField('name', self.tildeString())

        parts=self.readLine().split()
        l=len(parts)
        if l is 5:
            top, flags, lifespan, resetMode, continent = parts
            continent=int(continent)
        elif l is 4:
            top, flags, lifespan, resetMode = parts
            continent=defaultContinent
        elif l is 3:
            top, lifespan, resetMode = parts
            flags=''
            continent=defaultContinent
        else:
            raise FormatError('Not right number of args in: '+repr(parts))

        self.zoneField('top', int(top))
        self.zoneField('flags', ASCIIFlagDecode(flags))
        self.zoneField('lifespan', int(lifespan))
        self.zoneField('reset-mode', int(resetMode))

        self.zoneField('continent', continent)

        self.parseCommands()
        return self # Method chaining.

    parseRecord = parseFile = parseZone

    def parseCommands(self):
        while 1:
            line=self.readLine()
            if line=='':
                return self.EOFNoDollar()

            c=line[0]
            d=line[1]

            if c=='*':
                self.disabledZoneCommand(line)
                continue

            if c=='$' or c=='S':
                if d!='\n':
                    raise FormatError('Expected newline immediately following %c. Got %c.'%(c,d))
                break

            if c in validCmds and d==' ':
                parts=line.split()

                l=len(parts)
                if c=='R' or c=='G':
                    if l<4:
                        raise FormatError('Expected 4 arguments to %c.  Got %d'%(c,l))
                elif l<5:
                    raise FormatError('Expected 5 arguments to %c.  Got %d'%(c,l))

                c=parts[0]
                ifFlag=int(parts[1])
                args=parts[2:] # this is kept as string arguments, though they should be integers
            else:
                raise FormatError('Expected %c in %s'%(c,validCmds))

            self.zoneCommand(c, ifFlag, args)

        self.endOfZone()

    def consumeZone(self):
        zone=self.zone

        del self.zone
        del self.file

        return zone

    consumeRecordSet = consumeZone


class SelectiveZoneReader(ZoneReader):
    def __init__(self, file, include):
        ZoneReader.__init__(self, file)

        self.include=include

    def zoneField(self, name, value):
        if name in self.include:
            self.zone[name]=value # ZoneReader.zoneField(self, name, value)

"""
#<Zone No>
<Name>~
<Top as Integer> <Flags as ASCII flags> <Lifespan> <Reset mode> [<Continent>]

    Commands are as follows:
*
MOEPD <If-flag> <arg1> <arg2> <arg3>
$ or S

"""

## SQLObject representation.
DEFAULT_ZONE_DBFL = 'lib/etc/zones.db'

def openZoneTables(dbpath):
    from .sql import openDatabaseTables
    return openDatabaseTables \
        (dbpath, 'StuphZoneRecord', 'StuphZoneCommand',
         schema_package = 'sql.zone')

def convert_zone_row(zone, columns):
    'Convert Zone Record into a mapping suitable for SQLObject row representation.'
    row = {}

    for n in columns:
        if n in zone:
            row[n] = zone[n]

        # Naming exception.
        elif n in ('resetMode'):
            row['resetMode'] = zone['reset-mode']

    return row

def convert_command_row(command, columns):
    row = {}

    for n in columns:
        if n == 'type':
            row[n] = str(command[0])[0]
        elif n == 'ifFlag':
            row[n] = int(command[1])

        elif n == 'arg1':
            if len(command[2]) > 0:
                row[n] = int(command[2][0])
            else:
                row[n] = -1

        elif n == 'arg2':
            if len(command[2]) > 1:
                row[n] = int(command[2][1])
            else:
                row[n] = -1

        elif n == 'arg3':
            if len(command[2]) > 2:
                row[n] = int(command[2][2])
            else:
                row[n] = -1

    return row

def loadStuphZoneRecords(dbpath = DEFAULT_ZONE_DBFL, populate_with = None):
    'Open a database and return the relevent tables.  populate_with a file/name/sequence of .zon files.'
    from types import GeneratorType as generator

    StuphZoneRecord, StuphZoneCommand = openZoneTables(dbpath)

    if populate_with:
        def iterate_population(p):
            if type(p) in (list, tuple, generator):
                for x in p:
                    for y in iterate_population(x):
                        yield y
            elif type(p) in (str, file):
                # p is a filename
                yield ZoneReader(p).parseZone().consumeZone()

            elif isinstance(p, ZoneReader):
                # What if parseZone has already been performed? (track state)
                yield p.parseZone().consumeZone()

        zone_columns    =  list(StuphZoneRecord .sqlmeta.columns.keys())
        command_columns = list(StuphZoneCommand .sqlmeta.columns.keys())

        for zone in iterate_population(populate_with):
            zone_record = StuphZoneRecord(**convert_zone_row(zone, zone_columns))

            for c in zone.get('commands', ()):
                StuphZoneCommand \
                    (stuphZoneRecord = zone_record,
                     **convert_command_row \
                        (c, command_columns))

    return (StuphZoneRecord, StuphZoneCommand)

# FORMAT = '%(name)-35.30s #%(vnum)5d'
FORMAT   = '#[%(vnum)5d] %(name)-20.20s (%(top)5d:%(resetMode)02d:%(continent)02d) [%(flags)010d] %(commands)-68.68s'
PAGER    = 'less'

def zonelist(Z, fmt = None, selection = None, **kwd):
    fmt       = fmt or FORMAT
    selection = selection or Z.select(**kwd)
    columns   = list(Z.sqlmeta.columns.keys())

    def rowdict(row):
        d = {}

        for c in columns:
            d[c] = getattr(row, c)

        return d

    from os import popen
    popen(PAGER, 'w').write('\n'.join(fmt % rowdict(row) for row in selection))

def test(*args):
    keyByFilename = ('-key-by-filename' in args)

    if keyByFilename:
        args.remove('-key-by-filename')

    zone_mapping = {}

    for filename in args:
        zone = ZoneReader(filename).parseZone().consumeZone()

        if keyByFilename:
            # In case multiple different files define same zone vnum.
            zone_mapping[filename] = zone
        else:
            zone_mapping[zone['vnum']] = zone

    return zone_mapping

def main(opts = []):
    if '-test' in opts:
        opts.remove('-test')

        global zone_mapping
        zone_mapping = test(*opts)
    else:
        n = len (opts)
        i = 0

        populate_with = []
        dbfile = DEFAULT_ZONE_DBFL

        while i < n:
            a = opts[i]

            if a in ('-new', '-new-db', '-newdb'):
                dbfile = new_database_file()
            elif a in ('-db', '-dbfile', '-dbpath', '-db-file', '-db-path'):
                i += 1
                dbfile = opts[i]
            else:
                populate_with.append(a)

            i += 1

        return loadStuphZoneRecords(dbfile, populate_with = populate_with)

if __name__ == '__main__':
    from sys import argv

    if '-debug' in argv:
        from pdb import runcall
        main_app = main

        def main(*args):
            return runcall(main_app, *args)

        argv.remove('-debug')

    Z, Commands = main(argv[1:])

    import new
    Z.zonelist = new.instancemethod(zonelist, Z)
