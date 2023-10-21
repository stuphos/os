# Command-Line Interface Routines
# (Used for subsystems.)
# Todo: merge in special command stuff.  Also, this should probably be migrated to mud.player.commands
#
import sys
import shlex

from contextlib import contextmanager

NoArgv = object()

@contextmanager
def settingCmdln(args):
    # Must temporarily shift the given argv into system module so that optparse functions right.
    previous_argv = getattr(sys, 'argv', NoArgv)

    if isinstance(args, str):
        args = args.split()
    elif args is None:
        args = []
    else:
        args = list(args)

    sys.argv = [''] + args
    try: yield # should yield args..? sys.argv?
    finally:
        if previous_argv is NoArgv:
            del sys.argv
        else:
            sys.argv = previous_argv

def parseOptionsOverSystem(parser, args):
    with settingCmdln(args):
        return parser.parse_args(list(args))


def printOptionsWithPrognameOverSystem(parser, progname, fileObj = None):
    previous_argv = getattr(sys, 'argv', NoArgv)

    progname = str(progname)
    assert progname
    sys.argv = [progname]

    try: return parser.print_help(file = fileObj)
    finally:
        if previous_argv is NoArgv:
            del sys.argv
        else:
            sys.argv = previous_argv

# Why isn't this in tools?
def maxWidth(sequence, width):
    for n in sequence:
        n = len(n)
        if n > width:
            width = n

    return width

def getKeyword(kwd, name, default = None):
    try: value = kwd[name]
    except KeyError: return default
    else: del kwd[name]

    return value

def Option(*args, **kwd):
    # Returns a pair of argument aggregates suitable for passing as the
    # positional and keyword arguments to a function (add_option).
    return (args, kwd)

def createCmdlnParser(*options):
    from optparse import OptionParser
    parser = OptionParser()
    for (args, kwd) in options:
        parser.add_option(*args, **kwd)

    return parser

class Cmdln:
    def __init__(self, progName, *options, **kwd):
        self.progName = progName
        self.options = options
        self.parser = createCmdlnParser(*options)
        self.shlex = bool(kwd.get('shlex', False))

    class HelpExit(Exception):
        pass

    class Parsed:
        def __init__(self, cmdln, command, argstr, options, args):
            self.cmdln = cmdln
            self.command = command
            self.options = options
            self.args = args
            self.argstr = argstr

            self.nextArg = iter(self).__next__

        def __repr__(self):
            return 'Parsed-Command: %s [%s] %r' % \
                   (self.command, self.argstr, self.options)

        def help(self):
            return self.cmdln.help()

        @property
        def argstr_stripped(self):
            return self.argstr.strip() if self.argstr else ''

        def __iter__(self):
            for arg in self.args:
                yield arg

            while True:
                yield ''

        def __len__(self):
            return len(self.args)

        def halfChop(self, string = None):
            if string is None:
                string = self.argstr

            a = string.strip()
            i = a.find(' ')
            if i < 0:
                return (a, '')

            return (a[:i], a[i:].lstrip())

        def oneArg(self, string = None):
            return self.halfChop(self.argstr if string is None else string)[0]

    def parseCommand(self, cmd, argstr):
        if argstr:
            if self.shlex:
                argv = shlex.split(argstr)
            else:
                argv = argstr.split()
        else:
            argv = []

        return self.Parsed(self, cmd, argstr, *self.parseArgv(argv))

    def parseArgv(self, argv):
        try: return parseOptionsOverSystem(self.parser, argv)
        except SystemExit:
            raise self.HelpExit

    __call__ = parseArgv

    def help(self):
        from io import StringIO
        buf = StringIO()

        printOptionsWithPrognameOverSystem(self.parser, self.progName, buf)
        return buf.getvalue()
