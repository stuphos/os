# Object-Oriented Path Tools
#  Copyright 2011-2014 Thetaplane.  All rights reserved.
#  
# (For interactive access)
# That, is symbolic file-system controller interface.
from os.path import join as joinpath0, basename, dirname, expanduser, expandvars
from os.path import exists as fileExists, splitext, splitdrive, isabs
from os import getcwd, listdir, sep as SEP, sep as ROOT, environ
from os import unlink, stat

from urllib.request import pathname2url
from hashlib import md5
import re, types, sys, os
import shlex
import subprocess

from json import load as loadJson
from marshal import load as loadBinary
from pickle import load as loadPickle

try: from yaml import load as loadYaml
except ImportError as e: loadYaml = e

from contextlib import contextmanager
from tempfile import mkstemp, mkdtemp

# from op.runtime import Object, Attributable, getObjectName, GenericContext
# from op.runtime.core import notImplemented
# from op.runtime.layer.strings import doubleQuote, callString

# from op.platform.url import V3 # 2 seconds debugging

# circular dependence
# from op.platform.filesystem import mapFileToString

# from op.data.storage import Storage, Directory_PrivateStoreMember_Name, DB # 6 seconds debugger


notImplemented = None
from .url import V3


# Unsupported Platforms.  Todo: notImplemented implementation that raises original ImportError!
try: from os import mkdir, chdir, makedirs
except ImportError: # GAE
    mkdir = chdir = makedirs = notImplemented

try: from os import mknod, S_IFIFO
except ImportError: # GAE
    mknod = notImplemented
    S_IFIFO = 0


try:
    from os import system as systemCommand
    from os import popen as pipeString
except ImportError: # GAE
    systemCommand = pipeString = notImplemented

# XXX not available for GAE (currently)
##    try: from os import getuid
##    except ImportError: # GAE
##        expanduser = notImplemented

try: from subprocess import CalledProcessError
except ImportError: # GAE
    class CalledProcessError(NotImplementedError):
        def __init__(self, returncode, cmd, output = None):
            pass


# This is important, because os.join implementation treats the 'rest of'
# positional args differently as first (in terms of doing string operations
# on it that will probably be foiled by path class object).
def joinpath(*parts):
    return joinpath0(*(str(p) for p in parts))

FileProtocol = V3.Protocol('file')

def asFileUrl(drive, *path):
    return FileProtocol(drive).request(*path)

# Cross-Platform Support:
# todo: utilize 'cygpath' (shell) utility
def toCygwinPath(drive, parts):
    if drive:
        parts = ('', 'cygdrive', drive) + tuple(parts)

    return '/'.join(parts)

def toWin32Path(drive, parts):
    return '\\'.join((drive + ':',) + tuple(parts))

PLATFORMS = dict(cygwin = toCygwinPath,
                 win32 = toWin32Path,
                 windows = toWin32Path)

def _convert2PlatformForString(parts, toPlatformPath):
    # Todo: return a path object?
    #
    # I don't see why, since converting to another platform
    # generally means it's not longer compatible with the
    # underlying filesystem.
    #
    #   So, this rationalization is relied on in the exec
    #   machinery.
    #
    drive = parts[0]

    if isinstance(drive, PathType.drive):
        drive = drive.letter

    return toPlatformPath(drive, parts[1:])

def Convert2Platform(path, platform):
    toPlatformPath = PLATFORMS[platform]

    if not isinstance(path, PathType):
        assert isinstance(path, str)
        path = PathType(path)

    # Todo: cross-platform .parts property (that is, converting from non-native path to here?)
    return _convert2PlatformForString(path.parts, toPlatformPath)

TARGET_PLATFORM_KEYWORD = 'platform' # 'target_platform'

_CONVERT_PATH_OPTIONS = [TARGET_PLATFORM_KEYWORD]

def ConvertPathList2PlatformForStrings(paths, kwd):
    # Convert paths in arguments to target platform if specified.
    try: platform = kwd[TARGET_PLATFORM_KEYWORD]
    except KeyError:
        def _(r):
            # Always convert to string because execute machinery will try to iterate over each.
            return (str(x) for x in r)
    else:
        toPlatformPath = PLATFORMS[platform]

        def _(r):
            for p in r:
                if isinstance(p, PathType):
                    # Only convert path types, returning string.
                    yield _convert2PlatformForString(p.parts, toPlatformPath)
                else:
                    yield p

    start = str(paths[0])
    args = paths[1:]

    args = tuple(_(args))
    return (start,) + args

def _parseConvertPathOptions(**kwd):
    options = dict()

    for name in _CONVERT_PATH_OPTIONS:
        try: options[name] = kwd[name]
        except KeyError: pass
        else: del kwd[name]

    return (options, kwd)

# Execute Machinery:
# (this should go into op.runtime!)

# Note: embedded-platform interoperation isn't just about getting paths right,
# it's also about the standard console streams.  This implementation of the
# subprocess module can't handle cygwin-only programs for such a case without
# going through the bash shell, which is hard to operate for arbitrary command
# programs without some kind of framework.
#
# From subprocess, to the Popen constructor:
#
##    On UNIX, with shell=True: If args is a string, it specifies the
##    command string to execute through the shell.  If args is a sequence,
##    the first item specifies the command string, and any additional items
##    will be treated as additional shell arguments.
#
# Which results in:
#     args = ["/bin/sh", "-c"] + args
#
# ..and this really isn't good enough because it amounts to throwing arguments
# to the bash shell -- this is because, apparently, the bash -c switch looks at
# only the "first" (next) argument for a full command... making it embedded;
# EVEN THOUGH (from man bash):
##    -c string If the -c option is present, then commands are read from string.
##              If there are arguments after the string, they are assigned to the
##                  positional parameters, starting with $0.
#
##    Security
##    --------
##    Unlike some other popen functions, this implementation will never call
##    /bin/sh implicitly.  This means that all characters, including shell
##    metacharacters, can safely be passed to child processes.
#
# Also, note universal_newlines, and the path.{shell,job} interfaces,
# env= keyword to Popen.
#

import subprocess
CalledProcessError0 = CalledProcessError

class CalledProcessError(CalledProcessError0):
    def __init__(self, returncode, cmd, stdoutput, stderrput):
        CalledProcessError0.__init__ \
            (self, returncode, cmd) # , output = stdoutput)
            # Wtf, why did I think 'output' was a keyword?

        self.stderrOutput = stderrput
        self.stdOutput = stdoutput

def CallSubprocessForOutErr(*args, **kwd):
    'Like check_output, but buffers stderr in the exception.'

    p = subprocess.Popen(stdout = subprocess.PIPE,
                         stderr = subprocess.PIPE,
                         *args, **kwd)

    (stdout, stderr) = p.communicate()
    retCode = p.poll()

    if retCode:
        # This means the process/function call is actually 'converted'
        # into an exception, but the stdout and stderr streams are still
        # accessible (just not directly as return values).
        #
        # Unfortunately, use the icky way of catching the CalledProcessError
        # and extracting the result for custom shell commands.
        #
        # For instance, for process that you know will "fail" (non-zero
        # status), do assume the error, like so:
        #
        #   print catch(my.pybin.pipe, my.devAppCfg, '-h', platform = 'cygwin').output
        #
        raise CalledProcessError(retCode, kwd.get('args', args[0]),
                                 stdout, stderr)

    return (stdout, stderr)

def CallSubprocessForOut(*args, **kwd):
    return CallSubprocessForOutErr(*args, **kwd)[0]
def CallSubprocessForErr(*args, **kwd):
    return CallSubprocessForOutErr(*args, **kwd)[1]

CallSubprocess = CallSubprocessForOut

def startNewProcess(*args, **kwd):
    (options, kwd) = _parseConvertPathOptions(**kwd)
    return subprocess.Popen(ConvertPathList2PlatformForStrings(args, options),
                            stdout = subprocess.PIPE,
                            stderr = subprocess.PIPE,
                            **kwd)

def splitShellTokens(cmdln):
    return shlex.split(cmdln, posix = True)

# Hmm, this should be moved into platform, so that target-platform
# translation is only being called if through that class's methods.
# (skipping need for kwd and conversion unless needed).
#
# But this means always executing via AutoPlatform and not using kwd.
def executeString(string, **kwd):
    # Todo:
    # paths = ConvertPathList2PlatformForStrings(paths, kwd)
    return systemCommand(string)

def execute(*paths, **kwd):
    (options, kwd) = _parseConvertPathOptions(**kwd)
    paths = ConvertPathList2PlatformForStrings(paths, options)
    # XXX Lame
    return executeString(' '.join(doubleQuote(str(p)) for p in paths))

def pipe(*paths, **kwd):
    (options, kwd) = _parseConvertPathOptions(**kwd)
    return CallSubprocess(ConvertPathList2PlatformForStrings(paths, options),
                          **kwd)

def pipeString(string, **kwd):
    (options, kwd) = _parseConvertPathOptions(**kwd)
    return pipe(*ConvertPathList2PlatformForStrings \
                (splitShellTokens(string), options),
                **kwd)

def spawn(*paths, **kwd):
    # XXX Note:
    # win32->cygwin for exe paths with spaces:
    # ConvertPathList2PlatformForStrings converts rest(paths) to platform,
    # only if they're PathType.  os.spawn* expects the exe name first, and
    # then the argv (which shall include the exe as index 0), but since
    # the conversion function just returns this as a string (it's skipped),
    # it's not properly converted.  Wait, how is this a problem?  It shouldn't
    # be, but some programs might use it incorrectly, expecting something
    # else?  So maybe the problem is with os.spawnv on a windows platform.
    # What are other examples using Program Files or similar paths?
    # A quick solution is to not use paths[0] at all for third argument, or,
    # replace it with something ('' or appropriate platform conversion) for
    # this implementation of spawnv.

    (options, kwd) = _parseConvertPathOptions(**kwd)
    paths = ConvertPathList2PlatformForStrings(paths, options)

    try: env = kwd.pop('env')
    except KeyError:
        # return os.spawnv(os.P_NOWAIT, paths[0], paths)
        return os.spawnv(os.P_NOWAIT, paths[0], paths[1:])
    else:
        # return os.spawnve(os.P_NOWAIT, paths[0], paths, env)
        return os.spawnve(os.P_NOWAIT, paths[0], paths[1:], env)

# @Object.Format('for {name}')
class AutoPlatform: # (Object):
    def __init__(self, name):
        self.name = name
        self.kwd = {TARGET_PLATFORM_KEYWORD: self.name}

    def execute(self, *paths):
        return execute(*paths, **self.kwd)
    def pipe(self, *paths):
        return pipe(*paths, **self.kwd)
    def spawn(self, *paths):
        return spawn(*paths, **self.kwd)

    def convert(self, path):
        return PathType.ToPlatform(path, self.name)
    def convertAll(self, *paths):
        return list(map(self.convert, self.paths))
    def convertExec(self, *paths):
        return ConvertPathList2PlatformForStrings(paths, self.kwd)

    __call__ = convert

# REGEX_TYPE = type(re.compile(''))

toString = str.__str__

def loadModule(path, moduleTypeClass = types.ModuleType, name = None,
               vars = dict(), getVars = lambda module:dict()):

    try: source = open(path).read()
    except IOError as e:
        # todo: anything other than ENOENT??
        source = '' # Just ignore..

    # X-platform compat:
    source = source.replace('\r', '')

    if name is None:
        (name, _) = splitext(basename(path))

    module = moduleTypeClass(name)
    co = compile(source, path, 'exec')
    module.__file__ = str(path)

    ns = module.__dict__
    ns.update(vars)
    ns.update(getVars(module))

    exec(co, module.__dict__)
    return module

class SelectorBase:
    @property # memorized
    def filtering(self):
        return attributable(self.filterExtension)

    def filterExtension(self, extension):
        return self.filter('*.' + extension)

    # hmm, walk what?
    #   just files?
    #   just dirs?
    #   both dirs and files?
    #
    #   also, a way to walk using extension filtering based on
    #   an attributable thingma.

    ##    def walk(self, function):
    ##        return function

class selection(list, SelectorBase):
    # A list of file paths.
    # Todo: reverse filter? (exclusion)
    # todo: implement as iterator?
    def containing(self):
        return self

    listing = property(containing)

    def matching(self, pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        return selection(f for f in self.containing() \
                         if pattern.match(f) is not None)

    def baseMatching(self, pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        return selection(f for f in self.containing() \
                         if pattern.match(f.basename) is not None)

    def filter(self, pattern):
        from fnmatch import filter
        return selection(list(filter(self.containing(), pattern)))

    def baseFilter(self, pattern):
        from fnmatch import filter
        return selection(list(filter(io.basenames(self.containing()), pattern)))

    @classmethod
    def application(self, function):
        def wrapSelection(*args, **kwd):
            return self(function(*args, **kwd))

        return wrapSelection

    def relative(self, using): # *using?
        return classOf(self)(mapi(system.RelativePath(using = using).reduce, self))

    @property
    def tree(self):
        return tree.FromParts(path(p).parts for p in self)

    def including(self, inclusion):
        return selection(p for p in self.containing() if inclusion(p))

    def sorting(self, key, **kwd):
        return selection(sorted(self.containing(), key = key, **kwd))


if sys.platform == 'win32':
    def platformMakeDir(self, soft):
        if soft:
            try: return mkdir(self)
            except WindowsError as e:
                if e.winerror != 183:
                    raise
        else:
            return mkdir(self)
else:
    def platformMakeDir(self, soft):
        return mkdir(self)


class path(str, SelectorBase):
    from os.path import isdir, isfile
    from shutil import copy, move as rename # todo: methods that return new (arg 1)

    selection = selection

    # todo: override __new__ so that multiple path parts can be passed in during construction?

    # Because these are builtin.
    # Todo: what about chaining??
    def mkdir(self, soft = False):
        platformMakeDir(self, soft)
        return self
    def unlink(self):
        return unlink(self)

    def mkpipe(self, mode = 0o600):
        mknod(self, mode|S_IFIFO)
        return self

    isdir = property(isdir)
    isfile = property(isfile)

    absolute = property(isabs)

    @classmethod
    def FromRelative(self, this, folder = None):
        return path(this) if isabs(this) \
               or folder is None \
               else folder(this)

    delete = unlink
    move = rename # todo: methods that return new (arg 1)

    ##    def move(self, other):
    ##        other = io.path(other) # todo: if not isinstance(other, PathType)
    ##        shutil.move(other)
    ##        return other
    ##    rename = move

    def ensure(self, folder_only = False):
        target = self.folder if folder_only else self
        if not target.exists:
            makedirs(target)

    @classmethod
    def New(self, *paths):
        # XXX platform??
        return self(joinpath(*paths))

    def subpath(self, *subpath):
        return self.New(self, *subpath)

    __div__ = __call__ = join = subpath
    # __add__ = subpath # XXX?

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError:
            if name[-2:] == 'Of' and len(name) > 2:
                # XXX this is no good if decimals are a part of the basename,
                # but we want to be able to give an extension regardless..
                return self.folder.subpath('%s.%s' % \
                        (self.rootName, name[:-2]))

            return self.subpath(name)

    __str__ = asString = toString = toString

    def doesExist(self):
        return fileExists(self)

    exists = property(doesExist)
    __nonzero__ = doesExist

    def open(self, mode = 'r'):
        return open(self, mode)

    @property
    def writable(self):
        return self.open('w')

    def folderOf(self):
        return self.New(dirname(self))
    def getInitOf(self):
        return self.New(self('__init__.py'))

    @property
    def pythonModuleOf(self):
        e = self.extension
        if e:
            assert e == 'py'

        return path(self + '.py')

    directoryOf = folderOf
    folder = directory = property(folderOf)

    initOf = property(getInitOf)
    moduleOf = pythonModuleOf

    def chdir(self):
        chdir(self)

    @property
    @contextmanager
    def working(self):
        cwd = self.cwd()
        self.chdir()
        try: yield self
        finally: cwd.chdir()

    @property
    def stat(self):
        return stat(self)

    @property
    def size(self):
        return self.stat.st_size

    @property
    def basename(self):
        # Hmm, why return as a new path object??
        # should basically be a string because we know it's not a complete path anywhere...
        return self.New(basename(self))

    @property
    def fileName(self):
        return splitext(self.basename)[0]

    @property
    def rootName(self):
        n = self.basename
        i = n.find('.')
        return n if i < 0 else n[:i]

    @property
    def folderAs(self):
        rn = self.rootName
        if rn == self.basename:
            return self

        return self.folder(rn)

    def __getitem__(self, item):
        if isinstance(item, (list, tuple)):
            # todo: enhance the sequencing/joining mechanism here.
            return self.New('-'.join([self] + list(map(str, item))))

        return str.__getitem__(self, item)

    def findNextEntry(self, *parts, **kwd):
        self.ensure()

        try: name = kwd['name']
        except KeyError:
            #if parts:
            name = first(parts)
            parts = rest(parts)
            parts = list(parts)

        try: extension = kwd['extension']
        except KeyError:
            extension = parts[-1]
            parts = parts[:-1]

        #folder = self

        parts = list(parts)
        nr = 0
        while True:
            p = self(name)
            # p = p(*parts)

            if nr:
                p = p[parts + [nr]]
            else:
                p = p[parts]

            p = io.path(p + '.' + extension)

            if not p.exists:
                return p

            # todo: iteration control?
            nr += 1

    @property
    def nextEntry(self):
        if not self.exists:
            return self

        assert self.isfile
        return self.folder.findNextEntry \
               (name = self.rootName, # todo: break down indexed parts? .split('-')
                extension = self.extension)

    @property
    def fileExtension(self):
        return splitext(self)[1][1:].lower()

    extension = fileExtension

    @property
    def extensionOf(self):
        @attributable
        def getExtensionOf(name):
            return self.subpath(self.folder.subpath \
                                ('%s.%s' % (self.basename,
                                            name)))

        return getExtensionOf

    @selection.application
    def containing(self):
        return mapi(self, listdir(self))

    listing = property(containing)

    #@selection.application
    def getListing(self, sort = None, *args, **kwd):
        return sorted(self.listing, key = sort, *args, **kwd) \
               if callable(sort) else self.listing

    def __iter__(self):
        return iter(self.listing)

    @property
    def subdirs(self):
        return [d for d in self if d.isdir]

    @property
    def number(self):
        return len(self.listing)

    def walk(self):
        # assert self.isdir
        from os import walk

        for (root, dirs, files) in walk(self):
            for d in dirs:
                yield self.New(root, d)
            for f in files:
                yield self.New(root, f)

    walkedi = property(walk)
    walked = property(selection.application(walk))

    def walkfiles(self):
        return (p for p in self.walk() if p.isfile)
    def walkdirs(self):
        return (p for p in self.walk() if p.isdir)

    @property # memorized
    def walkingExt(self):
        return attributable(self.walkForExtension)

    @selection.application
    def walkForExtension(self, extension):
        extension = '.' + extension
        return (f for f in self.walked if f.endswith(extension))


    class drive(str): # (Object, str):
        def getAttributeString(self):
            return self

        @property
        def letter(self):
            return self[:1].lower()

    def getParts(self, omit_drive = False):
        (drive, path) = splitdrive(self)
        def _():
            if drive and not omit_drive:
                yield self.drive(drive)

            for x in path.split(SEP):
                if x:
                    yield x

        return list(_())

    parts = property(getParts)

    def write(self, data, mode = 'w'):
        with self.open(mode) as o:
            o.write(data)

        return self

    def writeline(self, lines, mode = 'w'):
        with self.open(mode) as o:
            for n in lines:
                o.write(n)
                o.write('\n')

        return self

    @property
    def md5sum(self):
        return md5(self.read()).hexdigest()

    def touch(self):
        self.open('a').close()
        return self

    def __lshift__(self, data):
        return self.write(data, mode = 'a')

    def read(self, size = -1):
        r = self.open().read
        return r() if size < 0 else r(size)

    def compile(self, mode = 'exec'):
        return compile(self.read(), str(self), mode)

    def toUrl(self):
        (drive, path) = splitdrive(self)
        path = str(path) # pathname2url expects string iteration
        return asFileUrl(drive, pathname2url(path))

    def toUrlString(self):
        return self.toUrl().urlString

    url = property(toUrl)
    urlString = property(toUrlString)

    def load(self, format = None, schemaName = None, context = None):
        # Hmm, we also want to verify that the handler exists before opening file??
        # opener = lambda:self.open()

        # print 'loading %r...' % self

        if format is None:
            if self.isdir:
                return self.load('folder') # recurse..

            if context is None:
                return op_data.loadStreamByFileExtension('.' + self.fileExtension, self.open())

            with context(path = self):
                return op_data.loadStreamByFileExtension('.' + self.fileExtension, self.open())
            # format = 'json'

        # Hmm, parse out certain ones that don't conform to our open() result type,
        # and handle those specifically (they're mostly path-related):

        elif format == 'db':
            # Why not just storage.DB?  (Or maybe the question is, why not distinguish with 'path-database'?)
            return Repository() # (self)
        elif format == 'module':
            return loadModule(self)
        elif format == 'package':
            # no: put on path and import.. do so implicitly using loader/importer?
            return self('__init__.py').load('module')

        elif format == 'importer':
            from zipimport import zipimporter
            return zipimporter(self)

        elif format == 'zip':
            from zipfile import ZipFile
            return ZipFile(self)

        elif format == 'coverage':
            # Coverage, parseCoverage
            from op.subsystem.project.coverage import Analysis
            return Analysis(self)

        ##    @property
        ##    def moduleSyntax(self):
        ##        from op.subsystem.project.coverage import \
        ##            (moduleSyntax, moduleSoup, moduleHTML)
        ##        return (self)

        elif format == 'folder':
            return FolderClass.FromPath(self)
        elif format == 'code':
            return self.compile()
        elif format == 'eval':
            return eval(self.compile('eval'))

        elif format == 'sqlite':
            return SqliteSession(self, schemaName = schemaName)
        elif format == 'structure':
            if context is None:
                return op_data.loadStreamByName(format, self.open())

            with context(path = self):
                return op_data.loadStreamByName(format, self.open())
        else:
            return op_data.loadStreamByName(format, self.open())

            # raise NameError(format)

    def save(self, value, format = None, name = None, content_type = None):
        if name:
            assert not format
            assert not content_type
            format = name

        if content_type:
            assert not format
            op_data.saveToStreamByContentType \
                (content_type, value, self.writable)

        elif format:
            op_data.saveToStreamByName \
                (format, value, self.writable)
        else:
            op_data.saveToStreamByFileExtension \
                (self.extension, value, self.writable)

        return self

        raise NotImplementedError

    dump = save

    __lshift__ = write # = save

    @property # memorized
    def loading(self):
        return attributable(self.load)

    @property
    def loadValue(self):
        return self.load(format = None)

    value = loadValue

    ##    @property
    ##    def text(self):
    ##        return self.loading.text

    def __enter__(self):
        return self.open().__enter__()
    # XXX __exit__ unto open file?

    @property
    @contextmanager
    def this(self):
        yield self

    @selection.application
    def matching(self, pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        return (self(f) for f in self.containing() \
                if pattern.match(f) is not None)

    @selection.application
    def baseMatching(self, pattern):
        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        return (self(f) for f in self.containing() \
                if pattern.match(f.basename) is not None)

    @selection.application
    def filter(self, pattern):
        from fnmatch import filter
        return list(filter(self.containing(), pattern))

    @selection.application
    def baseFilter(self, pattern):
        from fnmatch import filter
        return (self(f) for f in filter \
                (io.basenames(self.containing()),
                 pattern))

        b = list(io.basenames(self.containing()))
        print(b[0])

        b = list(filter(b, pattern))
        print(b[0])

        print(self(b[0]))

        return b

        b = [self(f) for f in b]
        print(b[0])

        return b

    # Todo: temporary file/directory in this directory?
    @contextmanager
    def tempfile(self, suffix = '', prefix = 'tmp', text = False):
        assert self.isdir
        (fd, name) = mkstemp(suffix = suffix, prefix = prefix,
                             dir = self, text = text)

        yield self.New(name)

    def tempdir(self, suffix = '', prefix = 'tmp'):
        assert self.isdir
        return self.New(mkdtemp(suffix = suffix, prefix = prefix, dir = self))

    tmpfile = tempfile
    tmpdir = tempdir

    @property
    def temporary(self):
        with self.tempfile() as t:
            return t

    def temporaryName(self, prefix = 'tmp-', nr = 10, suffix = '', attempts = 100):
        assert self.isdir

        from random import choice # , randint
        alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890'

        for o in forever() if attempts is None else range(attempts):
            n = ''.join(choice(alphabet) for x in range(nr))
            p = self('%s%s%s' % (prefix, n, suffix))
            if not p.exists:
                return p

        raise RuntimeError('Could not generate unique name after %d tries in %s' % (attempts, self))

        ##    x = 10 ** (nr.bit_length() / 8.)
        ##    hex(randint(10 ** x, 10 * x))


    execute = execute
    ##    def execute(self, *args):
    ##        execute(self, *args)

    def execString(self, cmdln, **kwd):
        return executeString('%s %s' % (self, cmdln), **kwd)

    pipe = pipe
    ##    def pipe(self, *args):
    ##        return pipe(self, *args)

    def pipeString(self, cmdln, **kwd):
        # XXX Err, use splitShellTokens?
        # Shouldn't these things be a function at global level?
        return pipeString('%r %s' % (self, cmdln), **kwd)

    spawn = spawn
    def spawnString(self, cmdln, **kwd):
        cmdln = splitShellTokens(cmdln)
        return spawn(self, *cmdln, **kwd) # self.spawn(*cmdln)

    startNewProcess = startNewProcess

    def job(self, *args, **kwd):
        return self.Shell.Job(self, *args, **kwd)
    singular = property(job)
    def shell(self, *args, **kwd):
        return self.Shell(self.job(*args, **kwd))
    group = property(shell)

    # todo: move actual implementation out of path class, possibly
    # merging with platform.shell objects.
    class Shell(list): # (Object, list):
        "print my.netStat.shell('-ab') | my.grep.job('10080', '-A', '3')"

        '''
        print my.find.group | my.grep.job('pattern') | \
              io.path.Shell.Options.unifyOutput | \
              my.bin.pager.exeOf

        my.find.shell(my.grep.job('pattern'),
                      my.wcLineCount.singular) \
                      .evaluation
            '''

        def __init__(self, *jobs, **kwd):
            list.__init__(self, jobs)
            self.kwd = kwd

        class Options(list): # (Object, list):
            def __init__(self, *sequence, **kwd):
                list.__init__(self, sequence)
                self.keywords = kwd # namespace(kwd)

            @classmethod
            def GetKeywordOption(self, name, value, doubleQuote = False): # 'force'):
                if ' ' in value:
                    value = repr(value) # todo: force double-quotes?

                return '--%s=%s' % (name, value)

            @classmethod
            def GetKeywordOptions(self, **kwd):
                return [self.GetKeywordOption(n, v) for (n, v)
                        in iteritems(kwd)]

            @classmethod
            def GetCmdln(self, *cmdln, **kwd):
                for a in cmdln:
                    if isinstance(a, (list, tuple)):
                        for x in self.GetCmdln(a):
                            yield x

                    elif isinstance(a, dict):
                        for x in self.GetKeywordOptions(**a):
                            yield x

                    elif isinstance(a, path.Shell.Options):
                        for x in a:
                            yield x

                    else:
                        yield str(a)

                if kwd:
                    for x in self.GetCmdln(kwd):
                        yield x

            def __iter__(self):
                return self.GetCmdln(*self, **self.keywords)


        options = Options
        redirectStderr = options(stderr = 'redirect')
        unifyOutput = redirectStderr

        ##    nullStdout = options(stdout = NULL_PIPE)
        ##    nullStderr = options(stderr = NULL_PIPE)
        ##    nullOutput = options(stdout = NULL_PIPE,
        ##                         stderr = NULL_PIPE)

        def getAttributeString(self):
            return ', '.join(map(repr, self))

        def invoke(self, stdin = None):
            # todo: create new processes, connecting ends.
            stdout = stderr = None
            i = None

            options = dict(self.kwd) # copy

            # todo: stdin can be string..!
            # so, copy to buffer, but need this be a named pipe?

            for job in self:
                # todo: basically, write the string to the next
                # invoked process's stdin stream.
                #
                # so, figure out how to insert that into this procedure:

                if isinstance(job, self.Options):
                    options.update(job.keywords)

                elif isinstance(job, classOf(self)):
                    # Another shell group.
                    i = job.invoke(stdin = stdin)
                    # what about job.last?

                    stdin = i.process.stdout
                else:
                    i = job.pipe(stdin = stdin,
                                 stdout = stdout,
                                 **options)

                    stdin = i.process.stdout

            assert i is not None
            return i # what about self?

        invocation = property(invoke)
        __call__ = invoke

        def __str__(self):
            return self.invocation.output # read()


        @property
        def first(self):
            return self[0]
        @property
        def last(self):
            return self[-1]

        def evaluate(self):
            # evaluation of last job.
            return self.invocation.evaluation
        evaluation = property(evaluate)

        def chain(self, job):
            # implement job chaining.
            if isinstance(job, PathType.Shell):
                # XXX see Shell::invoke
                self.extend(job)
                return self

            if isinstance(job, self.Job):
                self.append(job)
                return self

            if isinstance(job, PathType):
                job = job.job() # shell() # *args, **kwd?
                self.append(job)
                return self # job

            # todo: scriptables?

            raise ValueError(job)

        __or__ = __div__ = __lshift__ = __sub__ = chain

        def __lshift__(self, job):
            self.insert(0, job)
            return job

        # A contained shell item.
        class Job: # (Object): # hmm, curried-bundle?
            # print (my.cygwinroot.bin.cat.exeOf.singular << 'hi\nthere\n').evaluation
            def __init__(self, path, *args, **kwd):
                self.path = path
                self.args = args

                self.environ = dict()

                self.formatClass = kwd.pop('formatClass', None)

                # Strip out path platform conversion options.
                (self.options, self.kwd) = _parseConvertPathOptions(**kwd)

                self.process = None # The invocation.

            def getAttributeString(self):
                return callString(self.path, *self.args, **self.kwd)

            @property
            def keywordOptions(self):
                return path.Shell.Options.GetKeywordOptions(**self.kwd)

            @property
            def argv(self):
                argv = [self.path]
                argv.extend(path.Shell.Options.GetCmdln(*self.args))
                argv.extend(self.keywordOptions) # why trailing?

                argv = ConvertPathList2PlatformForStrings(argv, self.options)

                return argv

            def setenv(self, name, value):
                self.environ[name] = value
                return self

            def execOptions(self, stdin = None, stdout = None, **kwd):
                if 'stdin' not in kwd:
                    kwd['stdin'] = subprocess.PIPE if stdin is None else stdin
                if 'stdout' not in kwd:
                    kwd['stdout'] = subprocess.PIPE if stdout is None else stdout

                # Set stderr explicitly to None if you want it nulled.
                try: stderr = kwd['stderr']
                except KeyError:
                    stderr = self.kwd.get('stderr', '')

                if isinstance(stderr, str):
                    stderr = stderr.lower()

                    if stderr in ['redirect', 'stdout']:
                        kwd['stderr'] = subprocess.STDOUT
                    elif stderr in ['pipe', '']:
                        kwd['stderr'] = subprocess.PIPE

                elif stderr is None:
                    # Make sure it's not there.
                    try: del kwd['stderr']
                    except KeyError: pass

                else:
                    # for the time being -- accept and pass to subprocess
                    # raise ValueError(stderr)
                    pass

                kwd['env'] = self.environ

                return kwd

            def pipe(self, stdin = None, stdout = None, **kwd):
                if self.process is None:
                    kwd = self.execOptions(stdin = stdin,
                                           stdout = stdout,
                                           **kwd)

                    # The invocation.
                    self.process = subprocess.Popen(self.argv, **kwd)

                return self

            __call__ = pipe
            invocating = property(pipe)

            def write(self, string):
                self.process.stdin.write(string)
                # what to return?? number of bytes?

            def read(self):
                return self.process.stdout.read()
            def readStderr(self):
                return self.process.stderr.read()

            output = property(read)
            errorOutput = property(readStderr)

            def __lshift__(self, string):
                self.invocating.write(string)
                return self

            def __rshift__(self, buffer):
                buffer.write(self.invocating.read())
                return buffer


            # I hesitate to allow this:
            def __str__(self):
                return str(self.evaluation)


            def evaluate(self, autoExecute = True):
                if self.process is None:
                    assert autoExecute
                    self.pipe()

                retCode = self.process.poll()

                # Utilizing communite instead of reading the stream objects
                # on the process objects ourselves...
                # (stderr, stdout) = self.process.communicate()

                stdout = self.process.stdout
                stderr = self.process.stderr

                return self.InvocationResult.Evaluate \
                       (self, retCode, stderr, stdout)
            evaluation = property(evaluate)

            def done(self):
                self.process = None
                return self
            finished = property(done)

            def fromFormat(self, result):
                return self.formatClass.FromInvocationResult(result)

            class InvocationResult: # (Object):
                @classmethod
                def Evaluate(self, job, retCode, stderr, stdout, cmd = None):
                    if retCode:
                        raise self.Error(retCode, cmd, stderr, stdout)

                    return self(self, retCode, stderr, stdout)

                class Error(CalledProcessError):
                    # Todo: actually make this inherit from InvResult as mixin.
                    pass

                def __init__(self, job, retCode, stderr, stdout):
                    self.job = job
                    self.retCode = retCode
                    self.stderr = stderr
                    self.stdout = stdout

                def read(self):
                    r = b''
                    if self.stdout:
                        r += self.stdout.read()
                    if self.stderr:
                        r += self.stderr.read()

                    return r

                def __iter__(self):
                    for x in self.stdout:
                        yield x
                    for x in self.stderr:
                        yield x

                def done(self):
                    return self.job.done()
                finished = property(done)

                __str__ = read

                def fromFormat(self):
                    return self.job.fromFormat(self)
                formattedObject = property(fromFormat)


    ##    def grep(self, pattern):
    ##        pass # todo: use sgrepmdi

    # Common
    @classmethod
    def here(self):
        return self.New(getcwd())

    cwd = here

    @classmethod
    def FromEnv(self, path):
        return self.New(expanduser(expandvars(path)))

    @classmethod
    def FromLocalURL(self, url):
        if not isinstance(url, str):
            url = url.urlString

        # Todo: make this less lame.
        parts = '/'.join(url.path).split('/')
        path = getattr(io.drives, first(parts)[0].lower())
        return path(*rest(parts))

    @classmethod
    def user(self):
        return self.New(expanduser('~'))

    @classmethod
    def root(self):
        return self.New(ROOT)

    @classmethod
    def ToPlatform(self, path, platform):
        return Convert2Platform(path, platform)

    def toPlatform(self, platform):
        return self.ToPlatform(self, platform)

    @property
    def platformMapped(self):
        try: from op.platform.filesystem import mapFileToString
        except ImportError as e:
            raise NotImplementedError('%s: %s' % (e, str(self)))

        return mapFileToString(str(self))


PathType = path

# @Object.Format('{format}')
class ScriptableVariable: # (Object):
    __name__ = 'Variable'

    def __init__(self, format):
        self.format = format

    def resolve(self, **kwd):
        return self.getFormat().format(**kwd)

    def getFormat(self):
        value = self.format
        return value if '{' in value \
               else '{%s}' % value

class Scriptable: # (Object):
    # Store, basically, curried arguments to a path, which can be assembled to call.
    def __init__(self, *parts):
        self.parts = parts

    def getAttributeString(self):
        return ', '.join(map(str, self.parts))

    @property
    def path(self):
        return self.parts[0]

    @property
    def rest(self):
        return self.parts[1:]

    def getEnvironment(self, **kwd):
        kwd['system'] = system
        return kwd

    def resolve(self, *args, **kwd):
        env = self.getEnvironment(**kwd)
        return (a.resolve(**env) \
                if isinstance(a, self.Variable) \
                   else a for a in args)

    var = Variable = ScriptableVariable
    # varOf = attributable(var)

    def assemble(self, function, *args, **kwd):
        args = (self.rest + args)
        args = self.resolve(*args, **kwd)
        return getattr(io.path(self.path), function)(*args, **kwd)

    def spawn(self, *args, **kwd):
        return self.assemble('spawn', *args, **kwd)
    def spawnString(self, *args, **kwd):
        return self.assemble('spawnString', *args, **kwd)

    def execute(self, *args, **kwd):
        return self.assemble('execute', *args, **kwd)
    def execString(self, *args, **kwd):
        return self.assemble('execString', *args, **kwd)

    def pipeString(self, *args, **kwd):
        return self.assemble('pipeString', *args, **kwd)
    def pipe(self, *args, **kwd):
        return self.assemble('pipe', *args, **kwd)

    class parseVariables(object):
        # from op.runtime.virtual.objects import isInstance
        # from op.runtime.layer.strings import TokenizeInterpolatedExpression as tokenize, Expression
        # from op.runtime.functional.sequencing import filtering, mapping

        # def __new__(self, sc, allSC = filtering(isInstance(ScriptableVariable)),
        #                       tokenize = mapping(lambda v, allExprs = filtering(isInstance(Expression)),
        #                                                    tokenize = tokenize:
        #                                                    allExprs(tokenize(v.format)))):
        #     return tokenize(allSC(sc.parts))

        def __new__(self, sc):
            return sc.parts

    variables = property(parseVariables)


class PathRepository: # (Storage):
    # Todo: this should automatically convert paths for platform
    # (for instance, with cygwin presence)
    def getItem(self, name):
        value = Storage.getItem(self, name)

        if isinstance(value, str):
            # Todo: validate??
            value = PathType(value)

        return value

    def setItem(self, name, value):
        if isinstance(value, str): # PathType
            # For path types.  Essentially, always decode it.
            # Q: This doesn't really need to be here, but keeping mind
            # on the encoding is a good idea.
            value = str(value)

        return Storage.setItem(self, name, value)

    __getitem__ = getItem
    __setitem__ = setItem

Repository = PathRepository


class binpath:
    def __init__(self, path):
        if not isinstance(path, PathType):
            assert isinstance(path, str)
            path = PathType(path)

        self.__path = path

    def __getattr__(self, name):
        bin = self.__dict__['_binpath__path'](name + '.exe')
        if bin.exists: # and executable?
            return bin

class ShellCommand:
    # Todo: allow piping, redirection, job control, etc.
    def __or__(self, other):
        pass

# Customization:
MYPATHS_ENV_VAR = 'MYPATHS'
MYPATHS_ENV_VAR2 = 'MYPATHSFULL'

# Or, just separate this via platform??
MYPATHS_DEFAULT_FILE ='.my-paths-{sys.platform}.db'

class identity(object):
    def __repr__(self):
        return self.__class__.__name__

_sampleFullContent = (lambda c:c)
_sampleFirst200 = (lambda c:c[:200])

_defaultSample = _sampleFirst200

SAMPLES = dict(full = _sampleFullContent,
               first200 = _sampleFirst200)

def fileSampling(filelist, sample = None):
    if sample is None:
        sample = _defaultSample
    if isinstance(sample, str):
        sample = SAMPLES[sample]

    fmt = '%r:\n    %s\n\n'
    content = lambda x:'\n    '.join(sample(x.read()).split('\n'))
    return joinlines(fmt % (x, content(x)) for x in filelist)

# from op.runtime.virtual.objects import forPrivateParentAccess

##    from op.runtime.virtual.objects import PrivateParentAccess
##    class StorageCode(PrivateParentAccessor):
##        def __call__(self, item):
##            return PrivateParentAccessor(self, item).dict

class io: # (Object):
    path = path

    here = property(lambda self:path.here())
    executable = path(sys.executable)

    from io import StringIO as buffer
    # from op import data

    def folder(self, path, initialize = False):
        object = path.load('folder')

        if initialize:
            try: init = object.initForSystem
            except AttributeError: pass
            else: init()

        return object

    def folderOf(self, path):
        return path('.folder.py')
    def initOf(self, path):
        return path.initOf
    def pythonModuleOf(self, path):
        return path.pythonModuleOf

    scriptable = Scriptable
    # varOf = scriptable.varOf

    # Todo: simplify these declarations:
    def pipe(self, object, *args, **kwd):
        return object.pipe(*args, **kwd)
    def pipeString(self, object, *args, **kwd):
        return object.pipeString(*args, **kwd)

    def spawn(self, object, *args, **kwd):
        return object.spawn(*args, **kwd)
    def spawnString(self, object, *args, **kwd):
        return object.spawnString(*args, **kwd)

    def execute(self, object, *args, **kwd):
        return object.execute(*args, **kwd)
    def execString(self, object, *args, **kwd):
        return object.execString(*args, **kwd)

    def ls(self, *args, **kwd):
        print(cygwin.pipe(fs.cygwinroot.bin('ls.exe'), *args, **kwd))

    shell = ShellCommand

    class drives(object): # (Object, object):
        if sys.platform == 'win32':
            def __scanDrives(self):
                for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                    p = path(letter + ':\\')
                    if p.exists:
                        yield (letter, p)

        elif sys.platform == 'cygwin':
            def __scanDrives(self):
                # Todo: get this from system configuration?
                return ((d.basename, d) for d in path('/cygdrive').listing)

        else:
            # This has no concept in linux.
            __scanDrives = staticmethod(lambda:())

        def __buildDrives(self):
            try: return self.__dict__['_drives__allDrives']
            except KeyError:
                # todo: log when this is happening, because it doesn't
                # happen during instantiation.
                d = self.__allDrives = dict((letter.lower(), p) for (letter, p) \
                                            in self.__scanDrives())
                return d

        def __getDrive(self, letter):
            return self.__buildDrives()[letter]
        def __iter__(self):
            return iter(self.__buildDrives().keys())

        def regenerate(self):
            try: del self.__allDrives
            except AttributeError: pass
            self.__buildDrives()
            return self

        def __getattr__(self, name):
            try: return self.__getDrive(name)
            except KeyError:
                return object.__getattribute__(self, name)

        def getAttributeString(self):
            return ', '.join(map(str, self))

    def __init__(self):
        # Since this is a singleton... (this very well should be on class except for GAE..)
        self.drives = self.drives()
        self.root = path.root()

        try: self.home = self.user = path.user()
        except AttributeError: # thrown by expanduser when accessing os.getuid on unsupporting platform.
            self.home = self.user = None
        else:
            # Get the repository path name -- this is for a specific format
            # (not shell/user dir escapes)
            default = MYPATHS_DEFAULT_FILE.format(sys = sys, os = os)
            r = path(environ.get(MYPATHS_ENV_VAR2) or \
                     self.user(environ.get(MYPATHS_ENV_VAR, default)))

            try: self.op = r.load('db')
            except:
                from traceback import print_exc
                print_exc()
            else:
                builtin(fs = self.op,
                        my = self.op)

            # print pickle.Disassemble(my.storageCode.directory)
            # self.op.storageCode = forPrivateParentAccess(self.op).store

        builtin(io = self)
        # system.io = self

    def pkgInstall(self, folder):
        setup = folder('setup.py')
        assert setup.exists

        # io.executable.spawn
        exe = self.op.winpythonexe # self.executable
        exe.spawn(setup, 'install')

    def basenames(self, paths):
        return (p.basename for p in paths)

    sample = staticmethod(fileSampling)

    def dirlist(self, paths, against = 100):
        return columnize.auto(self.basenames(paths), against)
    def showdir(self, *args, **kwd):
        print(self.dirlist(*args, **kwd), end=' ', file=edit)

    def dirtree(self, folder):
        folder = io.path(folder)
        return folder.walked.relative([folder]).tree

    def showtree(self, *args, **kwd):
        print(self.dirtree(*args, **kwd), end=' ', file=edit)

    def which(self, name, paths = None, first = False):
        if paths is None:
            paths = system.environment.PATH

        @apply
        def find():
            for p in paths.split(os.pathsep):
                p = io.path(p)

                if p(name).exists:
                    yield p

        if first:
            return next(find)

        return find

    def findexe(self, name, paths = None):
        return self.which(name, paths = paths, first = True)(name)

    def pathOf(self, module):
        # I think this is the same as system.module(module)
        return io.path(system.moduleFile(module))
    __getitem__ = pathOf


    def pathSelect(self, folder, extension = None):
                   # transform = builtin.module.identity):

        folder = io.path(folder)

        if extension:
            files = folder.filterExtension(extension)
            names = (p.rootName for p in files)
        else:
            files = folder.listing
            names = io.basenames(files)

        # names = list(map(transform, names))
        names = list(names)
        ref = dict(list(zip(names, files)))

        return (ref[n] for n in pythonWin.listSelect(names))


    class pathSerialization:
        def __init__(self, path):
            self.__path = path

        def __getstate__(self):
            return self.__path
        def __setstate__(self, path):
            self.__path = path

        @property
        def __path__(self):
            return self.__path


    class pathScript(pathSerialization, object):
        @property
        def value(self):
            try: return self.__value
            except AttributeError:
                v = self.__value = self.__path__.loading.structure
                return v

        @value.deleter
        def value(self):
            try: del self.__value
            except AttributeError:
                pass

        def __getattr__(self, name):
            try: return object.__getattribute__(self, name)
            except AttributeError as e:
                if name == '_pathScript__value':
                    raise e

                return getattr(self.value, name)

    pathSerialization.script = pathScript
    serialization = pathSerialization


try: io = io()
except (ImportError, NotImplementedError):
    from traceback import print_exc
    print_exc()

    pass # GAE


##    def pythonwin(path):
##        systemCommand('%r %r' % (io.drives.c('Python27', 'Lib', 'site-packages', 'pythonwin', 'Pythonwin.exe'), path))
##    def explore(path):
##        systemCommand('%r %r' % (io.drives.c('Windows', 'explorer.exe'), path))

# Todo: system.naming['System::MountPoint'] = io.op

# from op import data as op_data

# Todo: as WMC?s
# Or, as package (.folder/me/__init__.py?)
class FolderClass(types.ModuleType):
    @classmethod
    def FromPath(self, folder):
        folder = path(folder)
        script = folder('.folder.py')

        packages = folder('.folder')
        if packages.isdir:
            assert not script.exists
            return self.FromPackages(folder, packages)

        wmc = folder('.wmc')
        if wmc.isfile:
            assert not script.exists
            return self.FromWMC(folder, wmc)


        import op

        # Todo: revamp the variable namespace structure here.
        module = loadModule(script, moduleTypeClass = self,
                            name = basename(folder),
                            getVars = lambda module:dict(__this_module__ = module,
                                                         this = module),
                            vars = dict(op = op,
                                        __folder__ = folder,
                                        folderClass = self))

        module.__init_folder__(script, folder)
        return module


    @classmethod
    def FromWMC(self, folder, wmc):
        module = self(basename(folder))
        module.__init_structure__(folder, wmc)

        return module

    def __init_structure__(self, folder, wmc):
        # XXX So this doesn't work...
            # This is kind of a trashy way to create an application object,
            # but basically we're relying on two things:
            #   1) The module type behavior
            #   2) The fact that setting its dictionary to the dictionary
            #      of the loaded structure instance pretty much does what
            #      we want in terms of an install.

        '''
        packages$: [packages/external, packages/system]
        local$: true

        init$($module)::
            def folder(instance):
                getattr(instance, 'init$').folder # same thing

        init$($method):
            code: system.path += folder.__folder__
            parameters: [folder]

            '''


        # Load the structure and then figure out how to get it into this
        # instance.
        object = wmc.loading.structure
        if not isinstance(object, dict):
            object = dictOf(object)


        # XXX So this doesn't work:
            # Of course, this means that technically, the underlying
            # structural object has great determinacy in the state of
            # this folder module object.
            # self.__dict__ = object

        dictOf(self).update(object)


        # Now we do the normal initialization of the folder object.
        self.__init_folder__(wmc, folder)


        # Now do folder-specific, WMC-specific initialization:
        try: packages = getattr(self, 'packages$')
        except AttributeError: pass
        else:
            if isinstance(packages, list):
                for pkg in packages:
                    if isinstance(pkg, str):
                        pkg = pkg.split('/')
                        pkg = self.__folder__(*pkg)

                        system.path += pkg

        if getattr(self, 'local$', False):
            system.path += self.__folder__


        # Now the client operation:
        try: init = getattr(self, 'init$')
        except AttributeError: pass
        else:
            if callable(init):
                # The initializor happens to be a method.
                init(self)

            else:
                # The initializor is a module or object
                # of some sort that should have a folder
                # method.
                try: init = init.folder
                except AttributeError: pass
                else: init(self)


           # .itervalues().next()
           # wrap in structure-containing folder class?


    @classmethod
    def FromPackages(self, folder, packages):
        # Todo: try to load packages from this directory:
        #   this/__init__.py?
        #   this/me/__init__.py?
        #
        #   this/ on system.path
        #   load this/folder.py??

        raise NotImplementedError('%s for %s/%s' % (self.FromPackages.__name__,
                                                    packages.folder.basename,
                                                    packages.basename))

    def importSubmodules(self, *names):
        ns = self.__this_module__.__dict__
        for sub in names:
            mod = self.__folder__(sub).load('module')
            ns.update(mod.__dict__)

    # @Attributable
    def submodule(self, sub):
        return self.__folder__(sub).load('module')

    def __init_folder__(self, script, folder):
        self.__folder__ = folder
        self.__file__ = script

    # This way, you can overload loadObject and still use below conventions.
    def openObject(self, *args, **kwd):
        return self.loadObject(*args, **kwd)

    __call__ = openObject

    def __iter__(self):
        return self.enumerate()

    # Extensible.
    def getObjectName(self, name):
        # Return the object file name for the given name (not like core.getObjectName).
        return name

    def getFileExtension(self, object):
        # Map object to file extension (should be via content-type)
        return op_data.getFileExtension(object)

    def loadObject(self, name, format = None):
        # Get handler from name/type/extension
        # return handler built with content from name under this path.New
        name = self.getObjectName(name)
        object = self.__folder__(name)

        if object.isdir:
            # Of course, the logical thing to do here is do a FolderClass load...
            # But we'll leave that up to the implementation of the containing folder.
            instance = name
        else:
            if format is None:
                # Yeah, of course this belongs in path.load
                ext = self.getFileExtension(object)
                instance = op_data.loadStreamByFileExtension(ext, object.open())
            else:
                instance = object.load(format)

        # So, this actually gets overloaded by the folder script,
        # since the folder script serves as the class initialization
        # code that is derived from this - slash - the module type.
        #
        # (but probably inherits from the one here).
        return self.Instance(instance, object) # self

    # Also, a way to enumerate objects in this folder (naming index).

    class Instance(object): # Wrapper
        # An extensible wrapper base -- connects object (path) to instance.
        def __new__(self, instance, object):
            try: init = self.__init__
            except AttributeError: pass
            else:
                this = object.__new__(self)
                init(this, instance, object)
                return this

            return instance

        # Implementation of Wrapper.
        ##    def __getattr__(self, name):
        ##        try: getattr(dictOf(self)['object'], name)
        ##        except AttributeError:
        ##            return object.__getattribute__(self, name)

        # This may be handy in loading FolderClass.Instance objects
        # from paths routinely:
        #
        #    my.object.loading.folder:
        #       .folder.py:
        #           from op.platform.path import FolderClass
        #           Instance = FolderClass.PathWrapperInstance
        #
        #       .folder.structure:
        #           Westmetal Configuration:
        #               ...
        #           database(memorized-property)::
        #               return this('the-database.db').loading.db

class SqliteSession:
    def __init__(self, path, schemaName = None):
        self.path = path
        self.session = sqlite.pathOpen(path)

        # Technically, the schema is present within the sqlite session object.
        if schemaName is None:
            # module = path.rootName + '-schema.py'
            root = path[len(path.folder)+1:]
            module = root[:-(len(path.extension)+1)] + '-schema.py'
        else:
            module = schemaName

        module = path.folder(module)
        self.module = module.load('module')
        self.orm = self.module.orm(self.session.sqlobjectConnection)
