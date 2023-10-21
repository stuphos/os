# Miscellaneous MUD Tools.
import types
import linecache
import re

try: import array # cx Freeze
except ModuleNotFoundError: pass

try: import dbm.ndbm, dbm.gnu
except ImportError as e:
    print(f'[dbm import error] {e}')


# Hmm, dependency.  But I don't want stuphlib to depend on this package.
# note: the dependent package is moved into framework/game/format
try: from stuphlib.directory import getUnderAssumedRoot, joinUnderAssumedRoot
except ImportError: pass


def atSetAttr(**kwd):
    def setAttrs(function):
        for (name, value) in kwd.items():
            setattr(function, name, value)

        return function
    return setAttrs


def columnize(items, nr_cols, fmt_width, max_width = None):
    from io import StringIO as new_buffer
    buf = new_buffer()

    if max_width:
        fmt = '%%-%d.%ds' % (fmt_width, max_width)
    else:
        fmt = '%%-%ds' % fmt_width

    col = 1
    nr_cols = int(nr_cols)

    for i in items:
        buf.write(fmt % i)
        if not (col % nr_cols):
            buf.write('\n')

        col += 1

    # XXX no newline added when uneven
    if col % nr_cols:
        buf.write('\n')

    return buf.getvalue()

FORBLANK_PATTERN = re.compile(r'^(\s*)')
def countIndent(line):
    # Match count of whitespace at the beginning of string.
    # Pretty simple, because tab-nontab indentation is incompatible.
    return len(FORBLANK_PATTERN.match(line).group(1))

    ##    i = 0
    ##    for c in line:
    ##        if c in (' ', '\t'):
    ##            i += 1
    ##        else:
    ##            break
    ##
    ##    return i

BLANK_PATTERN = re.compile(r'^(?:\s*)$')
def AllBlank(s):
    return BLANK_PATTERN.match(s) is not None

def ReadFileLines(filename):
    def getline(line):
        if line[-2:] in ['\r\n', '\n\r']:
            return line[:-2]
        if line[-1:] in '\r\n':
            return line[:-1]

        return line

    with open(filename) as fl:
        return list(map(getline, fl))

def functionLines(func, max = 0, trim_decorators = True, width = 60):
    if type(func) not in (types.FunctionType, types.MethodType): #, types.UnboundMethodType):
        raise TypeError(type(func))

    co = func.__code__
    return functionLines0(co.co_filename, co.co_firstlineno - 1,
                          max = max, trim_decorators = trim_decorators,
                          width = width)

def functionLines0(filename, startline, max, trim_decorators, width):
    # The basic source-parsing algorithm detached from function type.
    format = (lambda s, f = '%%.%ds' % width: f % s) if width else (lambda s:s)
    lines = ReadFileLines(filename)

    ln = startline
    end = min(startline + max, len(lines)) if max else len(lines) - 1

    line = lines[ln]
    n = countIndent(line)

    blanks = []
    headerState = 0

    yield format(line)

    while True:
        if ln >= end:
            break

        ln += 1
        line = lines[ln]

        if AllBlank(line):
            blanks.append(line)
            continue

        # The following algorithm only works with proper syntax:
        #   (but doesn't accept one-statement defs on same line) XXX
        i = countIndent(line)
        if i <= n:
            if headerState > 1:
                # Start of next definition.
                break

            if line.lstrip().startswith('@'):
                if trim_decorators:
                    continue

            else:
                # Met beginning of declaration and body.
                headerState = 1

        else:
            # In definition.
            headerState = 2

        if blanks:
            # Flush the blanks cache, but only after we know
            # that we're still within this definition.
            for b in blanks:
                yield format(b)

            blanks = []

        yield format(line)

def functionName(func):
    if type(func) is types.MethodType:
        return '%s.%s.%s' % (func.__module__, func.__self__.__class__.__name__, func.__name__)

    return '%s.%s' % (func.__module__, func.__name__)

def listSortInsert(listObj, item, key = None):
    # Insert an item into a list, with an order in mind.
    # (Maintain priority lists)
    if not listObj:
        # Because the algorithm below can't deal with empty list.
        listObj.append(item)
        return

    if callable(key):
        k = key(item)
        for i in range(len(listObj)):
            if key(listObj[i]) > k:
                break
        else:
            i += 1
    else:
        for i in range(len(listObj)):
            if 0 > cmp(item, listObj[i]):
                break
        else:
            i += 1

    listObj.insert(i, item)

from . import getLineFromCache, clearLineCache, checkLineCache

class lineCache:
    get = staticmethod(getLineFromCache)
    clear = staticmethod(clearLineCache)
    check = staticmethod(checkLineCache)

lineCache = lineCache()

def setupSubmodule(ns, name, base, attrs = ()):
    fqName = name
    if name[0] == '.':
        fqName = ns['__name__'] + name
        name = name[1:]

    import sys
    submod = types.ModuleType(fqName)
    ns[name] = submod
    sys.modules[fqName] = submod

    if isinstance(base, str):
        base = __import__(base, fromlist = [''])

    try: attrs = base.__all__
    except AttributeError: pass

    for n in attrs:
        if isinstance(n, (list, tuple)):
            (n, a) = n
        else:
            a = n

        try: setattr(submod, a, getattr(base, n))
        except AttributeError: pass

    return submod


def xorString(s, k):
    if not k:
        return s

    def forever():
        o = list(map(ord, k))
        while True:
            for c in o:
                yield c

    i = forever().__next__
    return ''.join(chr(ord(c) ^ i()) for c in s)

xor = xorString

def capitalize(string):
    return string[0].upper() + string[1:]

class Attributes(object):
    ##    class Attributes(Object):
    ##        Meta = Object.Meta('function', 'object')

    @classmethod
    def Dynamic(self, function):
        # Decorator.
        def buildGetter(object, *args, **kwd):
            return self(function, object, *args, **kwd)

        return buildGetter

    def __init__(self, function, object, *args, **kwd):
        self.function = function
        self.object = object
        self.args = args
        self.kwd = kwd

    def __getattr__(self, name):
        # Todo: define this policy a bit better.  Also, when to raise AttributeError?
        if name.startswith('__'):
            return object.__getattribute__(self, name)

        return self.function(self.object, name, *self.args, **self.kwd)

def listing(function):
    def listWrapper(*args, **kwd):
        return list(function(*args, **kwd))

    from functools import update_wrapper
    return update_wrapper(listWrapper, function)

def stylizedHeader(caption, nl = '\r\n', blank = True):
    # Display a stuph-styled caption.
    def h():
        yield '&y%s&N' % caption
        yield '&r%s&N' % ('=' * len(caption))

        if blank:
            yield ''

    return nl.join(h())

def expend(sequence):
    # Use up a generator (return nothing)
    for x in sequence:
        pass


class FileNotFoundException(IOError):
    pass

def OpenFile(filename, *args, **kwd):
    # A subroutine for opening a file and raising a separate exception if it doesn't exist.
    # This saves extra code for introspecting the error.
    try: return open(filename, *args, **kwd)
    except IOError:
        from sys import exc_info
        from errno import ENOENT

        (etype, value, tb) = exc_info()

        if value.errno == ENOENT:
            raise FileNotFoundException

        raise etype(value).with_traceback(tb)


# Used..?
def Code(source, name, filename):
    # Compile code.
    tab = '\n' + ' ' * 4

    argspec = '*args, **kwd'
    code = 'def %s(%s):%s%s' % (name, argspec, tab, tab.join(source.split('\n')))

    return compile(code, filename or '<Function Code>', 'exec')

def Function(code, name = None, filename = None, globals = None):
    name = name or 'function'
    if type(code) is str:
        code = Code(code, name, filename)

        # Extract code from function (pre)definition.
        ns = dict()
        exec(code, ns)
        code = ns[name].__code__

    from dis import disassemble as dis
    dis(code)

    name = name or code.co_name

    def mainGlobals():
        import __main__ as main
        return main.__dict__

    import new
    return new.function(code, globals or mainGlobals(), name)

def accessItems(object, names):
    for n in names:
        object = object[n]

    return object


from pickle import dumps
def pickleSafe(object):
    try: return dumps(object)
    except Exception as e:
        return e

# def pickleSafe(object):
#     return object


# todo: put into profiling gc:
##    from cProfile import Profile
##    from mud.runtime.facilities import Facility
##
##    class ProfiledHeartbeatManager(Facility):
##        NAME = 'Heartbeat::Profiler'
##
##        class ProfiledCallable(object):
##            def __init__(self, callable):
##                self.profiler = Profile()
##                self.callable = callable
##            def __call__(self, *args, **kwd):
##                return self.profiler.runcall(self.callable, *args, **kwd)
##            def dump_stats(self, filename):
##                self.profiler.dump_stats(filename)
##
##            def __getattr__(self, name):
##                return object.__getattribute__(self.callable, name)
##
##            @classmethod
##            def isInstance(self, this):
##                return issubclass(this.__class__, self)
##
##        from mud import getBridgeModule
##        getBridgeModule = staticmethod(getBridgeModule)
##
##        @classmethod
##        def create(self):
##            bridgeModule = self.getBridgeModule()
##            heartbeat = getattr(bridgeModule, 'heartbeat', None)
##
##            if not heartbeat:
##                raise Exception('No heartbeat installed!')
##            if self.ProfiledCallable.isInstance(heartbeat):
##                raise Exception('Already installed!')
##
##            bridgeModule.heartbeat = self.ProfiledCallable(heartbeat)
##            return self()
##
##        def __init__(self):
##            self.filename = None
##
##        def __registry_delete__(self):
##            bridgeModule = self.getBridgeModule()
##            heartbeat = getattr(bridgeModule, 'heartbeat', None)
##
##            if not heartbeat:
##                raise SystemError('Heartbeat was uninstalled!')
##            if not self.ProfiledCallable.isInstance(heartbeat):
##                raise SystemError('Expected a profiler installation.')
##
##            bridgeModule.heartbeat = heartbeat.callable
##
##        class Manager(Facility.Manager):
##            VERB_NAME = 'heartbeat-*profiler'
##            MINIMUM_LEVEL = Facility.Manager.IMPLEMENTOR
##
##            def do_filename(self, peer, cmd, args):
##                facility = self.facility.get()
##                if len(args) == 0:
##                    print >> peer, facility.filename
##                else:
##                    facility.filename = ' '.join(args)
##
##            def do_dump(self, peer, cmd, args):
##                facility = self.facility.get()
##                if not facility.filename:
##                    print >> peer, 'Filename not specified.'
##
##                heartbeat = getattr(facility.getBridgeModule(), 'heartbeat', None)
##                if not heartbeat:
##                    raise SystemError('Heartbeat was uninstalled!')
##                if not self.facility.ProfiledCallable.isInstance(heartbeat):
##                    raise SystemError('Expected a profiler installation.')
##
##                heartbeat.profiler.dump_stats(facility.filename)
##
##            def do_list(self, peer, cmd, args):
##                facility = self.facility.get()
##                if not facility.filename:
##                    print >> peer, 'Filename not specified.'
##
##                heartbeat = getattr(facility.getBridgeModule(), 'heartbeat', None)
##                if not heartbeat:
##                    raise SystemError('Heartbeat was uninstalled!')
##                if not self.facility.ProfiledCallable.isInstance(heartbeat):
##                    raise SystemError('Expected a profiler installation.')
##
##                from cStringIO import StringIO
##                from pstats import Stats
##
##                args = list(args)
##                args.insert(0, 'list')
##                (options, args) = self.parse_list_args(args)
##
##                if options.output_file:
##                    buf = open(options.output_file, 'w')
##                else:
##                    buf = StringIO()
##
##                stat = Stats(facility.filename, stream = buf)
##
##                stat.strip_dirs()
##                # stat.sort_stats(...)
##
##                for arg in args:
##                    if arg == 'callers':
##                        stat.print_callers()
##                    elif arg == 'callees':
##                        stat.print_callees()
##                    elif arg == 'stats':
##                        stat.print_stats()
##
##                if options.output_file:
##                    buf.flush()
##                    buf.close()
##                else:
##                    peer.page_string(buf.getvalue())
##
##            def parse_list_args(self, args):
##                from optparse import OptionParser
##                parser = OptionParser()
##                parser.add_option('--output-file')
##                return parser.parse_args(args)

# ProfiledHeartbeatManager.manage()
