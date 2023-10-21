# Runtime Error Handling.
__all__ = ['HandleException', 'ShowFrame',
           'getSystemException', 'getSystemExceptionString',
           'reraiseSystemException', 'reraise',
           'getModuleFileBasename']

from traceback import format_exc
from sys import exc_info as getSystemException

from . import getline, basename

# Utilities.
def getSystemExceptionString():
    return str(format_exc())
def reraiseSystemException():
    reraise(*getSystemException())
def reraise(type, value, tb):
    # I know this is the traditional pattern with python 3 traceback raising,
    # but usually value is already an instance of type.
    # raise type(value).with_traceback(tb)
    raise value.with_traceback(tb)

def getModuleFileBasename(filename):
    from sys import path as system_path
    for p in system_path:
        if p:
            if filename.startswith(p):
                return filename[len(p)+1:]

    return filename

# Game-Level Routines.
# Todo: rewrite this because obviously it's doing what .logs does.
def HandleException(exc = None):
    from .logs import log

    if exc is None:
        exc = getSystemException()

    (tp, val, tb) = exc

    # Find (second to?) last frame.
    while tb.tb_next:
        tb = tb.tb_next

    frame = tb.tb_frame
    code  = frame.f_code

    log('%s(%s): %s (%s:%d)' % (getattr(tp, '__name__', '<Unnamed>'),
                                code.co_name, str(val),
                                code.co_filename, frame.f_lineno))

def ShowFrame(frame, name, exc = None, use_basename = True):
    code = frame.f_code
    filename = code.co_filename

    line = getline(filename, frame.f_lineno).strip()

    if use_basename == 'relative':
        filename = system.relative(filename) # WRLC
    elif use_basename:
        filename = basename(filename)

    if exc:
        return '%s in %s: %s\n -> (%s:%d) %s' % \
               (name, code.co_name, exc[1], filename, frame.f_lineno, line)

    return '    (%s:%d:%s) %s' % (filename, frame.f_lineno, code.co_name, line)


class CodeSourceServer(dict):
    _lineClassCache = dict()

    @property
    def patterns(self):
        for (pattern, source) in self.items():
            if isinstance(pattern, str):
                pattern = re.compile(pattern)

            yield (pattern, source)

    def locate(self, code):
        filename = code.co_filename
        for (pattern, sourceClass) in self.patterns:
            m = pattern.match(filename)
            if m is not None:
                return sourceClass(self, code, *m.groups(),
                                   **m.groupdict())

    __getitem__ = __call__ = locate

    def sourceCodeServer(self, reader):
        return newClassObject('$', (self.CodeSource,), dict(read = reader))

    class CodeSource:
        def __init__(self, server, code, path):
            self.server = server
            self.code = code
            self.path = path

        @property
        def cacheId(self):
            cls = classOf(self)
            return '%s:%s' % (moduleOf(cls), nameOf(cls))

        @property
        def lineCache(self):
            id = self.cacheId
            try: return self.server._lineClassCache[id]
            except KeyError:
                cache = self.server._lineClassCache[id] = dict()
                return cache

        def __getitem__(self, index):
            cache = self.lineCache
            try: lines = cache[self.path]
            except KeyError:
                lines = cache[self.path] = self.read()

            return lines.__getitem__(index)

        def read(self):
            raise NotImplementedError

        @property
        def content(self):
            return self.read()
        source = content


class Traceback:
    def __init__(self, ptr):
        self.ptr = ptr

    @classmethod
    def StackFrom(self, tb):
        return self(tb).stack

    @classmethod
    def InstallCodeServer(self, pattern, server):
        self.Frame.CodeSource.server[pattern] = server.sourceCodeServer(server)

    @classmethod
    def Bind(self, pattern):
        def bind(server):
            self.InstallCodeServer(pattern, server)

        return bind

    @property
    def previous(self):
        return classOf(self)(self.ptr.tb_back)
    back = previous

    def __iter__(self):
        this = self
        while this is not None:
            yield this
            this = this.previous

    @property
    def frame(self):
        return self.Frame(self, self.ptr.tb_frame)

    @property
    def stack(self):
        return self.Stack(self)

    class Stack:
        def __init__(self, head):
            self.head = head

        def __iter__(self):
            return iter(reversed(list(self.head)))

        @property
        def rendering(self):
            return '\n'.join(f.frame.rendering for f in self)


    class Frame:
        def __init__(self, tb, ptr):
            self.tb = tb
            self.ptr = ptr

        @property
        def codeSource(self):
            return self.CodeSource(self, self.ptr.f_code)
        source = codeSource

        @property
        def lineNumber(self):
            return self.ptr.f_lineno

        @property
        def rendering(self):
            code = self.source
            lnr = self.lineNumber

            path = system.relative(code.path)
            r = '[%s:%s]\n' % (path, lnr)

            try: source = self.source[lnr]
            except: pass
            else:
                r += indent(source)

            return r

        def __str__(self):
            return self.rendering


        class CodeSource:
            server = CodeSourceServer()

            def __init__(self, f, code):
                self.f = f
                self.code = code

            @property
            def fileName(self):
                return self.code.co_filename

            path = fileName

            @property
            def sourceCode(self):
                server = self.server.locate(self.code)
                return server.source # .replace('\r', '')
            source = sourceCode

            @property
            def sourceSequence(self):
                return self.sourceCode.split('\n')

            def __iter__(self):
                return iter(self.sourceSequence)

traceback = Traceback.StackFrom
sourceClass = CodeSourceServer.CodeSource
codeServer = Traceback.InstallCodeServer
bindCodeServer = Traceback.Bind


# @bindCodeServer('^/virtual/(?P<path>.*)$')
# def virtualSource(code):
#     core = runtime.Agent.System(None)
#     node = core[code.path]

#     if isinstance(node, core.Node.Document):
#         return node.content
