# Game System Tools.
from time import time as getSystemTime
import code

class Examiner(code.InteractiveConsole):
    def __init__(self, locals = None, globals = None, *args, **kwd):
        code.InteractiveConsole.__init__(self, locals = locals, *args, **kwd)

        # Default these after they may be set by super-constructor.
        if globals is None:
            globals = self.locals

        self.globals = globals

    def runcode(self, paramCode):
        """Overridden to execute in split locals-globals context.

        Otherwise behaves exactly as InteractiveConsole.runcode.
        """
        try:
            exec(paramCode, self.globals, self.locals)
        except SystemExit:
            raise
        except:
            self.showtraceback()
        else:
            # python 2 remnant
            # if code.softspace(code.sys.stdout, 0):
            #     print()

            pass

def examine(*args, **kwd):
    try: import readline
    except ImportError: pass
    Examiner(*args, **kwd).interact(banner = '')

def examine_single(single, *args, **kwd):
    try: import readline
    except ImportError: pass
    code = compile(single, '<single>', 'single')
    Examiner(*args, **kwd).runcode(code)

NANOBIN = "'/bin/nano'"

def NanoText(text):
    from os import system, remove as delete_file
    tmpflname = getTempFileName()
    open(tmpflname, 'w').write(text)

    try:
        system('%s "%s"' % (NANOBIN, tmpflname))
        return open(tmpflname).read()
    finally:
        delete_file(tmpflname)

def NanoProgramme(filename, programmeName, managerId = None):
    manager = None
    if managerId is not None:
        from stuphmud.server.player.interfaces.code import LookupProgrammeManagerObject
        manager = LookupProgrammeManagerObject(managerId)

    from shelve import open
    db = open(filename)

    source = db.get(programmeName) or ''
    if manager is not None:
        source = getattr(source, 'sourceCode', '')

    source = NanoText(source)

    programme = source
    if manager is not None:
        programme = manager.buildProgramme(programmeName, programme)

    db[programme] = programme
    db.sync()

UPPER_A = ord('A')
UPPER_Z = ord('Z')
UPPER_RANGE = UPPER_Z - UPPER_A

NR_TMP_CHARS = 8

def getTempFileName(*leading):
    from os.path import join as joinpath
    parts = list(leading)
    parts.append('tmp%s' % getRandomLetters(UPPER_A, UPPER_Z, NR_TMP_CHARS))
    return joinpath(*parts)

try: from random import randint
except ImportError as e:
    print(f'[game.compartment.misc] {e}')

def getRandomLetters(lower, upper, nr):
    return ''.join(chr(randint(lower, upper)) for x in range(nr))

def getMainDict(**kwd):
    import __main__ as main
    import pdb

    try: from json import dumps
    except ImportError:
        from simplejson import dumps

    main.runcall = pdb.runcall
    main.tojson = dumps
    main.main = main

    main = main.__dict__
    main.update(kwd)
    return main

def columnize(items, nr_cols, fmt_width):
    from io import StringIO as new_buffer
    buf = new_buffer()

    fmt = '%%-%ds' % fmt_width
    col = 1
    nr_cols = int(nr_cols)

    for i in items:
        buf.write(fmt % i)
        if not (col % nr_cols):
            buf.write('\n')

        col += 1

    if col % nr_cols:
        buf.write('\n')

    return buf.getvalue()

def getRealPath(path):
    import os, os.path
    return os.path.normpath(os.path.join(os.getcwd(), path))

def registerRealPath(path):
    import sys
    path = getRealPath(path)

    if path not in sys.path:
        sys.path.append(path)
        return True

    return False

if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--shelf')
    parser.add_option('--programme')
    parser.add_option('--mud-package')

    (options, args) = parser.parse_args()
    if options.mud_package:
        registerRealPath(options.mud_package)

    if options.shelf:
        if options.programme:
            NanoProgramme(options.shelf, options.programme)

from profile import Profile
def profile(filename = None):
    assert filename
    def makeProfiledFunction(function):
        def profileCall(*args, **kwd):
            profiler = Profile()
            try: profiler.runcall(function, *args, **kwd)
            finally:
                profiler.dump_stats(filename)

        return profileCall
    return makeProfiledFunction
