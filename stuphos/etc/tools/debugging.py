# MUD Debug Tools.
# Copyright 2021 runphase.com .  All rights reserved
#
from pdb import Pdb, set_trace as enter_debugger, runcall as debugCall

# Basic debugging implementation.
def breakOn(function):
    def debugWrapper(*args, **kwd):
        return debugCall(function, *args, **kwd)

    debugWrapper.__name__ = getattr(function, '__name__', '')
    debugWrapper.__doc__ = getattr(function, '__doc__', '')
    return debugWrapper

def traceOn(function):
    def traceWrapper(*args, **kwd):
        enter_debugger()
        return function(*args, **kwd)

    traceWrapper.__name__ = getattr(function, '__name__', '')
    traceWrapper.__doc__ = getattr(function, '__doc__', '')
    return traceWrapper

def remoteBreak(function):
    def remoteDebugWrapper(*args, **kwd):
        from rpdb import Rdb
        return Rdb().runcall(function, *args, **kwd)

    remoteDebugWrapper.__name__ = getattr(function, '__name__', '')
    remoteDebugWrapper.__doc__ = getattr(function, '__doc__', '')
    return remoteDebugWrapper

def remoteTrace(function):
    def remoteTraceWrapper(*args, **kwd):
        from rpdb import Rdb
        Rdb().set_trace()
        return function(*args, **kwd)

    remoteTraceWrapper.__name__ = getattr(function, '__name__', '')
    remoteTraceWrapper.__doc__ = getattr(function, '__doc__', '')
    return remoteTraceWrapper

# Hard-level Trace Tools.
def trace(*args, **kwd):
    from stuphos.system.api import mudlog
    scopeName = kwd.get('scopeName')

    args = ' '.join(map(str, args))
    if scopeName:
        mudlog('%s (%s)' % (args, scopeName))
    else:
        mudlog(args)

def traceInline(*args, **kwd):
    from ph import enqueueHeartbeatTask
    enqueueHeartbeatTask(trace, *args)

HARDLOG_FILENAME_FORMAT = '../log/hardlog.%s.txt'
def hardlog(*args, **kwd):
    topicName = kwd.get('topicName', 'main')

    try: open(HARDLOG_FILENAME_FORMAT % topicName, 'a').write(' '.join(map(str, args)))
    except IOError as e:
        from errno import ENOENT
        if e.args[0] != ENOENT:
            raise e

asBuiltin(trace)
asBuiltin(traceInline)
asBuiltin(hardlog)

# Disabled:
##    # Programmed for Pdb Overseer.
##    from pdb import Pdb, set_trace as enter_debugger, runcall as debugCall
##    import sys
##
##    class DebugCompartment(Pdb):
##        # Handles
##        def __init__(self, breakpoints = None):
##            Pdb.__init__(self)
##            self.load_breakpoints(breakpoints)
##
##        def load_breakpoints(self, breakpoints):
##            if breakpoints:
##                for (filename, lineno) in parse_breakpoints(breakpoints):
##                    self.perform_set_break(filename, lineno)
##
##        def perform_set_break(self, filename, lineno):
##            # High-level breakset.
##            outcome = self.set_break(filename, lineno)
##            if outcome:
##                print outcome
##
##            bp = self.get_breaks(filename, lineno)
##            if bp:
##                bp = bp[-1]
##                print 'Breakpoint %d at %s:%d' % (bp.number, bp.file, bp.line)
##
##        def __repr__(self):
##            from pprint import pformat as pf
##            cname = self.__class__.__name__
##            return '<%s %r>' % (cname, ('\n%s' % (len(cname) + 2)).join(pf(self.breaks).split('\n')))
##
##    def stream_breakpoints(breakpoints):
##        if callable(getattr(breakpoints, 'readlines', None)):
##            def stream():
##                for bp in breakpoints.readlines():
##                    # Trim comments.
##                    pos = bp.find('#')
##                    if pos >= 0:
##                        bp = bp[:pos]
##
##                    # Cheap strchr?
##                    if any(c not in (' \t\b\n\r') for c in bp):
##                        yield bp.rstrip()
##
##            return stream()
##        return breakpoints
##
##    def parse_breakpoints(breakpoints):
##        # Generator.
##        for bp in stream_breakpoints(breakpoints):
##            (filename, lineno) = evaluate_target(bp)
##            if filename:
##                yield (filename, lineno)
##
##    from types import FunctionType as function
##    def evaluate_target(bp):
##        # Parsing and resolution phase.
##        if type(bp) is function:
##            return (bp.func_code.co_filename, bp.fun_code.co_firstlineno)
##        if type(bp) in (tuple, list) and len(bp) is 2 and \
##           type(bp[0]) is str and type(bp[1]) is int:
##            return bp
##
##        (filename, lineno) = ('', '')
##
##        colon = bp.find(':')
##        if colon >= 0:
##            filename = bp[:colon]
##            lineno = int(bp[colon+1:])
##        else:
##            # Search for qualified module/class/method filename/lineno.
##            parts = bp.split('.')
##            try:
##                if len(parts) == 1:
##                    target = eval(parts[0])
##                else:
##                    b = parts[0]
##
##                    target = __import__(b)
##                    z = False # Considered all imports requisited.
##                    for i in xrange(1, len(parts)):
##                        n = parts[i]
##                        if not z:
##                            b = '%s.%s' % (b, n)
##                            try: __import__(b)
##                            except ImportError:
##                                z = True
##
##                        target = getattr(target, n)
##
##                # Dereference target function.
##                code = target.func_code
##
##                # filename = self.canonic(code.co_filename)
##                filename = code.co_filename
##                lineno = code.co_firstlineno
##
##                return (filename, lineno)
##
##            except (ImportError, AttributeError), e:
##                print str(e)
##
##        return (filename, lineno)
##
##    def openNone(*args, **kwd):
##        try: return open(*args, **kwd)
##        except IOError, e:
##            from errno import ENOENT
##            if e.errno != ENOENT:
##                raise
##
##    class MainFrame(DebugCompartment):
##        BREAKPOINTS_FILE = 'python/.breakpoints'
##        MUDFRAME = 'runMUD'
##
##        def __init__(self):
##            DebugCompartment.__init__(self, openNone(self.BREAKPOINTS_FILE))
##            self.set_mud()
##
##        def set_mud(self, name = None):
##            # Start tracing the main frame, immediately, but only stopping for breakpoints.
##            name = name or self.MUDFRAME
##
##            import mud.tools.frames
##            frame = mud.tools.frames.find(name = name, ascending = True)
##
##            self.reset()
##            self.set_trace(frame)
##
##            self.set_continue()
##            # self.set_next()
##            # self.set_return()
##
##            sys.settrace(self.trace_dispatch)
##
##    # Another implementation.
##    DEFAULT_BREAKPOINT_STATE = True
##    _breakpoint_registry = {None: False}
##
##    @asBuiltin
##    def breakOn(point, onStart = DEFAULT_BREAKPOINT_STATE):
##        if type(point) is str:
##            def makeBreakpoint(function):
##                if point == 'this' or point == 'regardless':
##                    breakpoint = getFunctionIdentityBreakpoint(function)
##                else:
##                    breakpoint = point
##
##                function.breakpoint = breakpoint
##                if onStart or point == 'regardless':
##                    enableBreakpoint(breakpoint)
##
##                def debugCall(*args, **kwd):
##                    if not getBreakStatus(function):
##                        return function(*args, **kwd)
##
##                    return runcall(function, *args, **kwd)
##
##                debugCall.__name__ = function.__name__
##                debugCall.__doc__ = function.__doc__
##                debugCall.breakpoint = breakpoint
##
##                return debugCall
##            return makeBreakpoint
##
##        if not callable(point):
##            return point
##
##        def debugCall(*args, **kwd):
##            return runcall(point, *args, **kwd)
##
##        try: debugCall.__name__ = point.__name__
##        except AttributeError: pass
##        try: debugCall.__doc__ = point.__doc__
##        except AttributeError: pass
##
##        return debugCall
##
##    @asBuiltin
##    def enableBreakpoint(object):
##        _breakpoint_registry[getObjectBreakpoint(object)] = True
##
##    @asBuiltin
##    def disableBreakpoint(object):
##        _breakpoint_registry[getObjectBreakpoint(object)] = False
##
##    def getFunctionIdentityBreakpoint(function):
##        return (function.func_code.co_filename, function.func_code.co_firstlineno)
##
##    def getObjectBreakpoint(object):
##        # The breakpoint itself.
##        if type(object) in (str, tuple, list):
##            return object
##
##        try: return object.breakpoint
##        except AttributeError:
##            if type(object) is FunctionType:
##                return getFunctionIdentityBreakpoint(object)
##
##    def isBreakpointEnabled(name):
##        return bool(_breakpoint_registry.get(name, False))
##    def getBreakStatus(object):
##        return isBreakpointEnabled(getObjectBreakpoint(object))
##
##    ##    __builtins__.update(dict(breakOn = breakOn,
##    ##                             debug = enter_debugger,
##    ##                             enter_debugger = enter_debugger))
##
##    def dbgpClientBrk():
##        # Komodo/xdebug
##        from dbgp.client import brk
##        brk(port = 9000)
##
##    asBuiltin(dbgpClientBrk)
##
##    def test():
##        return test
##
##    if __name__ == '__main__':
##        from pdb import runcall
##        print runcall(mainFrame)
