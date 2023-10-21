
# The lib (data) directory in structure.
# todo: rewrite basic name patterns (define beyond \w.-/)
from os.path import join as joinpath, sep as PATHSEP
from glob import glob
import re
import yaml

class LibDataError:
    pass

class LibDataUriFormatError(LibDataError, ValueError):
    pass
class LibDataUnknownUriSection(LibDataError, NameError):
    pass
class LibDataUnknownUriName(LibDataError, NameError):
    pass

def getFullSection(section, subsection = None):
    if subsection:
        return '%s[%s]' % (section, subsection)

    return section

def getMiddleNameKey(name):
    c = name[:1].lower()
    if c in 'abcde': return 'A-E'
    if c in 'fghij': return 'F-J'
    if c in 'klmno': return 'K-O'
    if c in 'pqrst': return 'P-T'
    if c in 'uvwxyz': return 'U-Z'
    return 'ZZZ'

def merge(d, d2):
    d.update(d2)
    return d

def group(i):
    if isinstance(i, dict):
        i = iter(i.items())

    r = dict()
    for (n, v) in i:
        r.setdefault(n, []).append(v)

    return r

def getUnderAssumedRoot(*parts):
    parts = PATHSEP.join(parts).split(PATHSEP)
    path = []

    for p in parts:
        if p == '..':
            if path:
                path.pop()

        elif p != '.':
            path.append(p)

    return PATHSEP.join(path)

def joinUnderAssumedRoot(root, *parts):
    return joinpath(root, getUnderAssumedRoot(*parts))

class Section(dict):
    def __init__(self, section, subsection = None):
        self.section = section.upper()
        self.subsection = subsection.upper() if subsection else None

    def getFullSection(self):
        return getFullSection(self.section, self.subsection)
    def getLeafpoint(self, name):
        name = name.lower()
        try: return self[name]
        except KeyError:
            raise LibDataUnknownUriName(name)

    # leaf iteration?

    def enumerate(self):
        return iter(self.items())

    def toString(self):
        return yaml.dump(self.toStructure())
    def toStructure(self):
        return dict(section = self.getFullSection(), mapping = dict(self))

    __str__ = toString

# Section Types.
class PathMap(Section):
    def __init__(self, section, path, *components, **mapping):
        Section.__init__(self, section)
        self.path = path

        dict.__init__(self, mapping)

        for name in components:
            self[name] = name

    def getLeafpoint(self, name):
        return joinUnderAssumedRoot(self.path, Section.getLeafpoint(self, name))
    def toStructure(self):
        return dict(section = self.section, path = self.path, mapping = dict(self))

    def enumerate(self):
        from os.path import join
        path = self.path

        for (name, mapping) in self.items():
            yield (name, join(path, mapping))

    @classmethod
    def FromTree(self, section, tree):
        try: mapping = tree['mapping']
        except KeyError: mapping = {}

        components = tree.get('components', [])
        return self(section, tree['path'], *components, **mapping)

class RecordMap(Section):
    def __init__(self, section, varname, format, glob):
        Section.__init__(self, section)
        self.format = format # validate?
        self.varname = varname
        self.glob = glob

    def getLeafpoint(self, name):
        # Ugh, what about case?
        return self.format % {self.varname: getUnderAssumedRoot(name)}

    def enumerate(self):
        if self.glob is None:
            raise ValueError('Glob pattern not configured')

        for i in glob(self.glob):
            # todo: translate the glob into a regex pattern,
            # such that it can be used to match each entry 'i'
            # for the name that identifies the entry, and use
            # it as the 'name' item for this result.
            yield (None, i)

    def toStructure(self):
        return dict(section = self.section, format = self.format,
                    variable = self.varname)

    @classmethod
    def FromTree(self, section, tree):
        return self(section, tree.get('variable', 'name'),
                    tree['format'], tree.get('glob'))

class WorldRecord(RecordMap):
    def __init__(self, section, varname, format, index_format):
        RecordMap.__init__(self, section, varname, format, None)
        self.index_format = index_format

    def getLeafpoint(self, name):
        if name.isdigit():
            return RecordMap.getLeafpoint(self, name)

        name = name.lower()
        if name not in ['index', 'index.mini']:
            raise LibDataUnknownUriName(name)

        return self.index_format % dict(index = name)

    def enumerate(self, index = None):
        if index is None:
            index = 'index'

        indexEntry = self.getLeafpoint(index)
        yield (index, indexEntry)

        for n in open(indexEntry):
            # Yes, read the index file.
            n = n.strip()
            # xxx should be parsing *.suffix
            if n.isdigit():
                yield (n, self.getLeafpoint(n))

    @classmethod
    def FromTree(self, section, tree):
        return self(section, tree.get('variable', 'zone'),
                    tree['format'], tree['index-format'])

class PartitionMap(RecordMap):
    def __init__(self, *args, **kwd):
        RecordMap.__init__(self, *args, **kwd)
        self.section_varname = self.varname + '.section'

    def getLeafpoint(self, name):
        name = getUnderAssumedRoot(name)
        return self.format % {self.varname: name,
                              self.section_varname: getMiddleNameKey(name)}

    def toStructure(self):
        return dict(section = self.section, format = self.format,
                    variable = self.varname)

# Root.
class Directory(Section):
    def __init__(self, name, entries):
        Section.__init__(self, name)
        dict.__init__(self, ((e.getFullSection(), e) for e in entries))

    def toStructure(self):
        return dict((n, v.toStructure()) for (n, v) in self.items())

    SECTION_DEF_PATTERN = re.compile(r'([\w.]*)(?:\(([\w-]+)\))?')
    SECTION_TYPES = {'path-map': PathMap,
                     'record-map': RecordMap,
                     'partition-map': PartitionMap,
                     'world-record': WorldRecord}

    @classmethod
    def FromTree(self, name, tree):
        if isinstance(tree, str):
            tree = yaml.load(tree)

        def extractSections(subtree, parent = None):
            for (name, config) in subtree.items():
                m = self.SECTION_DEF_PATTERN.match(name)
                assert m is not None

                (name, type) = m.groups()
                if type is None:
                    # Define a parent section.
                    if name.endswith('[]'):
                        name = name[:-2]

                    for s in extractSections(config, parent = name):
                        yield s
                else:
                    typeClass = self.SECTION_TYPES[type]
                    section = name

                    if parent:
                        if not section:
                            # The default space for this section parent.
                            section = parent
                        else:
                            section = '%s[%s]' % (parent, section)

                    yield typeClass.FromTree(section, config)

        return self(name, extractSections(tree))

    # Todo: rewrite alot of this.
    # Accessors -- todo: get rid of whole notion of subtype in this parse: just keep it opaque.
    URI_SECTIONSUB_PATTERN = R'(?P<section>\w+)(?:\[(?P<subsection>[^]]+)\])?'
    URI_PATTERN = r'^(?:stuph\:)?%s\:(?P<name>[\w./]+)$' % URI_SECTIONSUB_PATTERN
    URI_SECTIONSUB_PATTERN = re.compile(URI_SECTIONSUB_PATTERN)
    URI_PATTERN = re.compile(URI_PATTERN)

    @classmethod
    def parse(self, uri):
        m = self.URI_PATTERN.match(uri)
        if m is None:
            raise LibDataUriFormatError(uri)

        m = m.groupdict()
        section = m['section'].upper()
        subsection = m['subsection']
        name = m['name']

        if subsection:
            section = '%s[%s]' % (section, subsection.upper())

        return (section, name)

    def lookup(self, name):
        try: section = dict.__getitem__(self, name)
        except KeyError:
            raise LibDataUnknownUriSection(name)

        return section

    def lookupFilename(self, uri):
        (section, name) = self.parse(uri)
        return self.lookup(section).getLeafpoint(name)

    __getitem__ = lookupFilename

    @property
    def contents(self):
        return Contents(self)


class Contents: # Archival Operation
    # Kind of a heavy-weight class because it reconstructs alot of the work
    # done to tear down the directory structure..  But it's a directly
    # functional implementation.
    #
    # Access the iterator of toplevel sectional structures, and then
    # iterate through those by specifying an (world) index, enumerating
    # each entry mapping for a handle to the resource content.

    def __init__(self, directory):
        self.directory = directory

    MAIN_SECTION_ENUMERATION_ORDER = []

    def __iter__(self):
        def gathering():
            # Scan sections, parse structure and group.
            for (_, section) in self.directory.enumerate():
                (name, resource) = self.directory.parse \
                                  ('%s:NULL' % section.getFullSection())

                m = self.directory.URI_SECTIONSUB_PATTERN.match(name)
                if m is None:
                    print(name) # because it shouldn't fail
                    yield (name, (None, section))
                else:
                    (name, sub) = m.groups()
                    # if sub is None:
                    #     print name, repr(section)[:20]

                    yield (name, (sub, section))

        groups = iter(group(gathering()).items())

        ordering = self.MAIN_SECTION_ENUMERATION_ORDER.index
        def mainSectionOrderFor(xxx_todo_changeme):
            (name, item) = xxx_todo_changeme
            try: return ordering(name)
            except ValueError:
                return (0,) # last, ascending

        groups = sorted(groups, key = mainSectionOrderFor)

        # XXX PLAYER[MAIL(.{COUNT})]
        # This can be done with specific subs.
        # It could also be done by re-encapsulating the partition-map type.
        # XXX group
        return (self.Section.FromGroup(*group)
                for group in groups)

    class Section(list):
        # Structured internal representation of directory configuration.
        @classmethod
        def FromGroup(self, name, group):
            group = dict(group) # item pairs of sub/object
            main = group.pop(None, None)

            return self(self.MakeSub(None, name, main),
                        *(self.MakeSub(name, *v) for v in
                          group.items()))

        def __repr__(self):
            return '%s: %d subsections' % (self.main.name,
                                           len(self))

        @classmethod
        def MakeSub(self, root, name, object):
            root = '%s_%s' % (root, name.replace('.', '_')) \
                   if root else name

            subClass = self._subClasses.get(root, self.Sub)
            return subClass(name, object)

        def __init__(self, main, *subs):
            list.__init__(self, subs)
            self.main = main

        def __iter__(self):
            yield self.main

            for sub in self.subSections:
                yield sub

        @property
        def subSections(self):
            return list.__iter__(self)

        class Sub:
            # A sub-section (or, a section's main node).
            def __init__(self, name, object):
                self.name = name
                self.object = object

            def __repr__(self):
                return '%s: %r' % (self.name, self.object)

            @property
            def hasContents(self):
                return self.object is not None

            def __getitem__(self, index):
                if isinstance(self.object, WorldRecord):
                    return self.object.enumerate(index)

                return self.object.enumerate()

            def __iter__(self):
                # Prevent python from trying to access getitem sequentially.
                raise NotImplementedError


        ##    class WorldSub(Sub):
        ##        def __getitem__(self, index):
        ##            return self.object.enumerate(index)

        ##    _subClasses = dict(PLAYER = Player,
        ##                       PLAYER_MAIL = PlayerMail,
        ##                       PLAYER_MAIL_COUNT = PlayerMailCount)

        _subClasses = dict()

    def contents(self, index = None):
        # Generates a sequence of individual file components
        # paired with a qualified section key as well as a
        # unique value that may identify this particular
        # component resource within that directory section.
        #
        # Also references a particular index into each section,
        # which reflects the selection of library entities
        # that should be included in this content.

        def _(key, s):
            if s.hasContents:
                for c in s[index]:
                    yield (key, c)

        for section in self:
            main = section.main
            mainName = main.name

            for c in _((mainName, None), main):
                yield c

            for sub in section.subSections:
                key = (mainName, sub.name)

                for c in _(key, sub):
                    yield c

    __call__ = contents
    mainIndex = property(contents)

    def __str__(self):
        # XXX nls, mapi, group, iteritems
        return nls('%s:\n%s\n' % \
                   (n[0] if n[1] is None else '%s[%s]' % \
                    (n[0], n[1]), indent(nls(sorted(mapi(sliceOf[1], v)))))
                   for (n, v) in iteritems(group(self.mainIndex)))


# Program the Main Directory -- todo: build with yaml.
MAIN = Directory.FromTree('MAIN',
        '''
        GAME:
            (path-map):
                path: etc
                components: ['bank', 'dns.cache', 'hcontrol', 'olczones',
                             'players', 'shopgold', 'time', 'trust',
                             'trust.python']

                mapping:
                    network.sessions: network-sessions.bin
                    process.id: process_id
                    syslog.patterns: syslog-patterns.cfg
                    shell.commands: shell-commands.cfg
                    admin.script: admin_scripts/
                    plugins: plugins/
                    deployment: deployment/
                    config: config.cfg
                    zones: zone-modules.cfg
                    subdaemons: subdaemons.cfg

            TEXT(path-map):
                path: text
                components: ['background', 'clanhelp', 'credits', 'handbook', 'immlist',
                             'imotd', 'info', 'motd', 'news', 'policies', 'wizlist']

            MISC(path-map):
                path: misc
                components: ['bugs', 'ideas', 'messages', 'socials', 'typos', 'xnames']

        CLAN:
            (path-map):
                path: clan
                components: ['bank', 'index']

            BAN(record-map):
                variable: clan
                format: clan/ban/%(clan)s.ban
                glob: clan/ban/*.ban
            DATA(record-map):
                variable: clan
                format: clan/data/%(clan)s.dat
                glob: clan/data/*.dat
            INFO(record-map):
                variable: clan
                format: clan/info/%(clan)s.inf
                glob: clan/info/*.inf

        BOARD(record-map):
            variable: name
            format: boards/board.%(name)s
            glob: boards/board.*

        HELP:
            (path-map):
                path: text/help
                components: ['screen']

            TOPIC(record-map):
                variable: topic
                format: text/help/%(topic)s

                # XXX Should be what's in the index!
                glob: text/help/{index,general,skills,wizhelp,programmer}

        WORLD:
            ZONE(world-record):
                format: world/zon/%(zone)s.zon
                index-format: world/zon/%(index)s
            ROOM(world-record):
                format: world/wld/%(zone)s.wld
                index-format: world/wld/%(index)s
            ITEM(world-record):
                format: world/obj/%(zone)s.obj
                index-format: world/obj/%(index)s
            MOBILE(world-record):
                format: world/mob/%(zone)s.mob
                index-format: world/mob/%(index)s

            SHOP(world-record):
                format: world/shp/%(zone)s.shp
                index-format: world/shp/%(index)s
            SEARCH(world-record):
                format: world/sch/%(zone)s.sch
                index-format: world/sch/%(index)s

            SPECIALS(partition-map):
                format: world/specials/%(name)s.spc
                glob: world/specials/*.spc

            HOUSE(partition-map):
                variable: house
                format: house/%(house)s.house
                glob: house/*.house

        PLAYER:
            RENT(partition-map):
                format: plrobjs/%(name.section)s/%(name)s.objs
                glob: plrobjs/{A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.objs
            STRINGS(partition-map):
                format: plrstrings/%(name.section)s/%(name)s.strings
                glob: plrstrings/{A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.strings
            ALIAS(partition-map):
                format: plralias/%(name.section)s/%(name)s.alias
                glob: plralias/{A-E,F-J,K-O,P-T,U-Z,ZZZ}.alias

            MAIL(partition-map):
                format: plrmail/%(name.section)s/%(name)s.mail
                glob: plrmail/{A-E,F-J,K-O,P-T,U-Z,ZZZ}.mail
            MAIL.COUNT(partition-map):
                format: plrmail/%(name.section)s/%(name)s.count
                glob: plrmail/{A-E,F-J,K-O,P-T,U-Z,ZZZ}.count
        ''')

StuphLIB = MAIN


# Directory Accessors.
getLibraryFile = MAIN.lookupFilename

def openLibraryFile(uri, interfaceRequest):
    # Try to open it for editing (with interface).
    pass

def pathNormalize(path):
    r = []
    b = ''

    for c in path:
        if c in '/\\':
            if b:
                r.append(b)
                b = ''

        else:
            b += c

    if b:
        r.append(b)

    return r

def doIncrementFilename(filename):
    # Essentially, create only if not exists,
    # reserving by way of this algorithm (but not locking).
    # XXX O_CREATONLY
    touch(filename)
    return filename

def getIncrementedFilename(filename):
    i = filename.find('.')
    if i < 0:
        root = filename
        ext = ''
    else:
        root = filename[:i]
        ext = filename[i:]

    while True:
        if not exists(filename):
            return doIncrementFilename(filename)

        parts = root.split('/')
        last = parts[-1] # assert

        if last.isdigit():
            last = int(last)
            parts = parts[:-1]
            parts.append(str(last + 1))
        else:
            parts.append('2')

        filename = '-'.join(parts) + ext


def defaultDateFormatter0(timestamp):
    pass

class DateFormatter:
    def __init__(self, format):
        self.format = format
    def __call__(self, timestamp):
        pass # return timestamp.strptime(self.format)

def compileDateFormat(format):
    if format == DEFAULT_DATE_FORMAT0:
        return defaultDateFormatter0

    return DateFormatter(format)

def getEntriesFromArchivalOptions(options):
    root = options.archive_root
    root = pathNormalize(root) if root else []

    index = options.world_index
    sectionize = options.archive_sections

    for ((section, sub), (key, entry)) \
        in MAIN.contents(index):

        # MAIN['SECTION[SUB]:KEY'] -> open(entry)
        localpath = entry

        entry = pathNormalize(entry)
        path = list(root)

        if sectionize:
            path.append(section.lower())
            if sub:
                path.append(sub.lower())

        path.extend(entry)
        path = '/'.join(path)

        yield (localpath, path)

archivalOptions = getEntriesFromArchivalOptions

def doZipArchive(filename, options, entries):
    # XXX memory hog:
    # todo: utilize shell utilities and disk space
    from zipfile import ZipFile
    zf = ZipFile(filename, 'w')

    for (localpath, path) in entries:
        # todo: a map-file-to-string
        try: o = open(localpath)
        except IOError as e:
            print(e)
            continue

        contents = o.read()
        zf.writestr(path, contents)

    zf.close()
    return zf

def doBZip2TarArchive(filename, options, entries):
    raise NotImplementedError
def doGZipTarArchive(filename, options, entries):
    raise NotImplementedError
def doDirectoryStructure(filename, options, entries):
    raise NotImplementedError
def doRDBMS(filename, options, entries):
    raise NotImplementedError

##    class doZipArchive(object):
##        __new__ = staticmethod(doZipArchive0)
##
##        @classmethod
##        def InitializeCmdlnOptions(self, parser):
##            parser.add_option('--use-shell', action = 'store_true')


def getConfigOptions(resource, section = None):
    # Read the configuration file specified in the directory.
    # return io.path(MAIN[CONFIG_RESOURCE_FORMAT % \
    #                dict(resource = resource)]) \
    #           .loading.ini

    return dict()


DEFAULT_OUTPUT_TARGET = 'zip-archive'

DEFAULT_DATE_FORMAT0 = 'mmmddthyyyy'
DEFAULT_DATE_FORMAT = DEFAULT_DATE_FORMAT0

OUTPUT_TARGET_ALIASES = dict(zip = 'zip-archive',
                             bz = 'bzip-tar',
                             bz2 = 'bzip-tar',
                             bzip = 'bzip-tar',
                             bzip2 = 'bzip-tar',
                             gz = 'gzip-tar',
                             gzip = 'gzip-tar',
                             folder = 'directory-structure')

OUTPUT_TARGETS = {'zip-archive': doZipArchive,
                  'bzip-tar': doBZip2TarArchive,
                  'gzip-tar': doGZipTarArchive,
                  'directory-structure': doDirectoryStructure,
                  'rdbms': doRDBMS}

CONFIG_RESOURCE_FORMAT = 'GAME:%(resource)s' # 'GAME[CONFIG]:%(resource)s'
DEFAULT_CONFIG_RESOURCE = 'config'
DEFAULT_CONFIG_SECTION = ''

def doArchiveContents(filename, options):
    # PYTHONPATH="..\..\pythonlib\packages"
    # python -m stuphlib.directory
    #   --archive=stuphlib-aug18th2014.zip

    outputTarget = options.output_target
    outputTarget = OUTPUT_TARGET_ALIASES.get \
                   (outputTarget, outputTarget)

    try: outputTarget = OUTPUT_TARGETS[outputTarget]
    except KeyError:
        raise NameError('%s not in available %s' % \
                        (outputTarget, list(OUTPUT_TARGETS.keys())))


    dateFormatter = compileDateFormat(options.date_format)
    entries = archivalOptions(options)
    configOptions = getConfigOptions(options.config_resource)

    from datetime import datetime

    todaysDate = dateFormatter(datetime.now())

    filename = filename.format(dict(today = todaysDate,
                                    game = configOptions))

    if options.increment:
        filename = doIncrementFilename(filename)

    return outputTarget(filename, options, entries)


def main(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--dump')
    parser.add_option('--dump-full', action = 'store_true')

    parser.add_option('--archive-contents', '--archive')
    parser.add_option('--output-target', default = DEFAULT_OUTPUT_TARGET)
    parser.add_option('--increment', action = 'store_true')
    parser.add_option('--date-format', default = DEFAULT_DATE_FORMAT)

    parser.add_option('--config-resource', default = DEFAULT_CONFIG_RESOURCE)
    parser.add_option('--config-section', default = DEFAULT_CONFIG_SECTION)

    parser.add_option('--archive-root')
    parser.add_option('--archive-sections', action = 'store_true')

    parser.add_option('--world-index')

    (options, args) = parser.parse_args(argv)

    if options.archive_contents:
        doArchiveContents(options.archive_contents, options)
    else:
        if options.dump_full:
            print(MAIN.toString())
        if options.dump:
            print(MAIN.lookup(options.dump).toString())

        for a in args:
            print(MAIN[a])

if __name__ == '__main__':
    main()

# Reference.
'''
etc/
    bank|dns.cache|hcontrol|olczones|players|shopgold|time|trust

    config.cfg
    zone-modules.cfg
    trust.python
    shell-commands.cfg
    subdaemons.cfg
    syslog-patterns.cfg

    network-sessions.bin
    process_id

    admin_scripts/
    plugins/

clan/
    ban/
        number.ban
    data/
        number.dat
    inf/
        number.inf

boards/
    board.name

text/
    background|clanhelp|credits|handbook|immlist|imotd
    info|motd|news|policies|wizlist

text/help/
    screen
    general|general|wizhelp|skills|programmer

misc/
    bugs|ideas|messages|socials|typos|xnames

world/
    mob|obj|sch|shp|wld|zon
        number.section
        index
        index.mini

    specials/
        name.spc
        zone-modules.cfg

plrobjs/
    A-E|F-J|K-O|P-T|U-Z|ZZZ/
        name.objs

plrstrings/
    A-E|F-J|K-O|P-T|U-Z|ZZZ/
        name.strings

plralias/
    A-E|F-J|K-O|P-T|U-Z|ZZZ/
        name.alias

plrmail/
    A-E|F-J|K-O|P-T|U-Z|ZZZ/
        name.mail
        name.count

house/
    number.house
'''

'''
stuphlib::
    boards: board.*
    house: *.house

    text:
        background, credits, handbook, immlist, imotd, info, motd,
        news, policies, title, wizlist, clanhelp

        help:
            screen, general, skills, wizhelp, index, programmer

    misc:
        bugs, ideas, typos, socials, messages, xnames, treeMap

    clan:
        bank, index

        ban: *.ban
        data: *.dat
        info: *.inf

    etc:
        hcontrol, olczones, shopgold, bank, time, trust, players,
        dns.cache

    plrstrings:
        {A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.strings
    plrobjs:
        {A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.objs
    plrmail:
        {A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.{mail,count}
    plralias:
        {A-E,F-J,K-O,P-T,U-Z,ZZZ}/*.alias

    world:
        zon: *.zon, index
        wld: *.wld, index
        obj: *.obj, index
        mob: *.mob, index
        shp: *.shp, index
        sch: *.sch, index
        '''
