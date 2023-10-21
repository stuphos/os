# MUD Tools.

# Tool Primitives.
def registerBuiltin(object, name = None):
    if name is None:
        name = object.__name__

    __builtins__[name] = object

def asBuiltin(function):
    registerBuiltin(function)
    return function

registerBuiltin(asBuiltin)


# System Tools.
import types

from os.path import basename, join as joinpath, dirname, normpath, abspath, splitext
from time import time as getCurrentSystemTime

import linecache
from linecache import getline as getLineFromCache, clearcache as clearLineCache, checkcache as checkLineCache
from linecache import getline

try: from json import load as fromJsonFile, loads as fromJsonString, dump as toJsonFile, dumps as toJsonString
except ImportError:
    try: from simplejson import load as fromJsonFile, loads as fromJsonString, dump as toJsonFile, dumps as toJsonString
    except ImportError:
        def jsonNotAvailable(*args, **kwd):
            raise NotImplementedError('Json methods not installed!')

        fromJsonFile = fromJsonString = toJsonFile = toJsonString = jsonNotAvailable

try: from collections import OrderedDict as ordereddict
except ImportError:
    # Provide our own implementation for < 2.7
    from .collections_hack import OrderedDict as ordereddict

from _thread import start_new_thread as _nth
def nth(function, *args, **kwd):
    return _nth(function, args, kwd)

# Also found in runtime.architecture.routines
def apply(function, *args, **kwd):
    return function(*args, **kwd)

asBuiltin(apply)


# Sub-tools.
from .debugging import breakOn, traceOn, remoteBreak, remoteTrace
from .debugging import enter_debugger, debugCall, debugCall as runcall
asBuiltin(breakOn)
asBuiltin(traceOn)
asBuiltin(remoteBreak)
asBuiltin(remoteTrace)
registerBuiltin(enter_debugger, 'debugOn')

from .errors import *
from .strings import *
from . import misc
from .misc import *
from .logs import *
from .cmdln import *

registerBuiltin(log, 'logOperation')

registerBuiltin(nling, 'nling')
registerBuiltin(indent, 'indent')


from . import timing

try:
    setupSubmodule(vars(), '.hashlib', 'hashlib',
                   ('new', 'md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512'))
except ImportError:
    pass # Not available.

# Pygments.
try: from .pyg_colorizer import stuphColorFormat
except (SyntaxError, ImportError) as e:
    # print e
    pyg_colorizer = False

    def stuphColorFormat(string):
        # Identity.
        return string


# supplementally:
def RegisterBuiltinAs(object, name):
    return builtin(**{name: object})
def RegisterDefaultBuiltin(object):
    return RegisterBuiltinAs(object, getObjectName(object))

class As:
    @classmethod
    def Builtin(self, function = None, alias = None):
        # As decorator.
        if function is None:
            assert alias
            def registerBuiltin(function):
                RegisterBuiltinAs(function, alias)
                return function

            return registerBuiltin

        elif alias:
            RegisterBuiltinAs(function, alias)
            return function
        else:
            RegisterDefaultBuiltin(function)
            return function

def _applyIndexAttributes(o):
    pass

class builtin(object):
    import builtins as builtinModule

    def __call__(self, *args, **kwd):
        ns = self.builtinModule.__dict__

        for o in args:
            try: name = o.__name__ # todo: getObjectName??
            except AttributeError: pass
            else:
                _applyIndexAttributes(o)
                ns[name] = o

        for (name, value) in kwd.items():
            _applyIndexAttributes(value)
            ns[name] = value # todo: AccessParts (deep) set, using synthetics...

        return self.builtinModule

    As = staticmethod(As.Builtin)
    # Overlay = Overlay

    module = name = variable = builtinModule
    default = staticmethod(RegisterDefaultBuiltin)

    @property
    def namespace(self):
        return self.module.__dict__

    ##    @applyWith(module)
    ##    class instance(Wrapper):
    ##        def anotherBuiltinMethod(self, *args, **kwd):
    ##            pass

builtin = builtin()
builtin(builtin = builtin)


def listing(function):
    def toListSequence(*args, **kwd):
        return list(function(*args, **kwd))

    return toListSequence

builtin(listing = listing)


# Todo: make this conditional/configurable
import stuphos.system.path
from stuphos.system.url import V3 # .Url

builtin(Url = V3.Url)


class Namespace(dict):
    @classmethod
    def ToStructure(self, object):
        # That is, to primitive type (not object.
        if isinstance(object, (dict,)):
            return dict((n, self.ToStructure(v)) \
                        for (n, v) in object.items())

        if isinstance(object, (TypeType, InstanceType)):
            return self.ToStructure(dictOf(object))

        if isinstance(object, list):
            return list(map(self.ToStructure, object))
        if isinstance(object, tuple):
            return tuple(self.ToStructure(o) for o in object)

        return object

    @classmethod
    def FromStructure(self, structure, strictTypes = True):
        if strictTypes:
            def typeCompare(i, *types):
                return type(i) in types
        else:
            def typeCompare(i, *types):
                return isinstance(i, types)

        def _(v):
            # Namespaces are already built?  This means that you should wrap
            # anything that might recurse like so.
            if not isinstance(v, Namespace):
                if typeCompare(v, dict):
                    return self.FromStructure(v)

                if typeCompare(v, tuple):
                    return tuple(_(i) for i in v)

                if typeCompare(v, list):
                    return list(map(_, v))

                # Todo: what about generator sequences?

            return v

        # Ostensibly the same as the (implicit) recursor,
        # except make sure to look at the...
        if typeCompare(structure, tuple):
            return tuple(self.FromStructure(v) for v in structure)
        if typeCompare(structure, list):
            return list(map(self.FromStructure, structure))

        if typeCompare(structure, dict):
            # ...dictionary-type reaction:
            kwd = dict((name, _(value)) for (name, value) \
                       in structure.items())
            return self(kwd) # **kwd)

        return structure

    # Todo: mutating deep-set

    def __init__(self, sequence = None, **kwd):
        # Q: Err, derive from dict? really?
        if isinstance(sequence, dict):
            sequence = iter(sequence.items())

        if sequence:
            for (name, value) in sequence:
                self[name] = value

        self.update(kwd)
        self.__dict__ = self

builtin(namespace = Namespace)
