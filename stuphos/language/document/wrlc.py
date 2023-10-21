# The WRLC subsystem interoperates with native functionality, but because ph is
# higher level, many of these things exist for symbolic compatibility with the
# structural model ported from WRLC.  The structural module should be modified
# to use ph components.


from contextlib import contextmanager
# from types import DictionaryType, ClassType, DictProxyType, TypeType, InstanceType, ModuleType, CodeType
DictionaryType = dict
from types import new_class as ClassType
from types import ModuleType, CodeType

import re

def dictOf(o):
    return o.__dict__
def classOf(o):
    return o.__class__

def apply(function, *args, **kwd):
    return function(*args, **kwd)


# Currently unsupported:
# docstring

# Document.Section:
#     GenericSearch.Results.{points,selected}
#     search

# Core:
#     Objects:
#         encoded
#         url
#         format

#     Document:
#         extraction
#         processing


def getPathType():
    # The only real WRLC dependency.
    # The filesystem interface might be useful, but should
    # probably be put into the ph.components package if you
    # don't want this feature to fail.
    from common.platform.path import PathType
    return PathType


# Stubs.
class Object:
    class Format:
        def __init__(self, name):
            pass
        def __call__(self, object):
            return object

# class GenericContext:
#     def __enter__(self):
#         return self

#     def __exit__(self, etype = None, value = None, tb = None):
#         if etype is not None:
#             raise etype, value, tb


class Namespace(dict):
    @classmethod
    def ToStructure(self, object):
        # That is, to primitive type (not object.
        if isinstance(object, (dict, DictProxyType)):
            return dict((n, self.ToStructure(v)) \
                        for (n, v) in object.items())

        if isinstance(object, (ClassType, TypeType, InstanceType)):
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
            for pair in sequence:
                if isinstance(pair, (list, tuple)) and len(pair) == 2:
                    (name, value) = pair
                    self[name] = value

        self.update(kwd)
        self.__dict__ = self

class Synthetic(Object):
    # This should implement partials/mixins
    def __init__(self, dict = None, **values):
        if not isinstance(dict, DictionaryType):
            assert dict is None
            dict = values
        else:
            dict.update(values)

        self.__dict__ = dict

    def __getitem__(self, item):
        return self.__dict__.__getitem__(item)
    def __setitem__(self, item, value):
        self.__dict__.__setitem__(item, value)

    def getAttributeString(self):
        from reprlib import repr
        # XXX :skip: fail on recursively-referencing structures.
        return ', '.join('%s=%s' % (n, repr(v)) for (n, v) in \
                         self.__dict__.items())

    def __str__(self):
        return inspect(dictOf(self))

class GenericContext:
    def __enter__(self):
        return self
    def __exit__(self, etype = None, evalue = None, tb = None):
        if evalue is not None:
            raise etype(evalue).with_traceback(tb)


# class Namespace(dict):
#     def __init__(self, *args, **kwd):
#         dict.__init__(self, *args, **kwd)
#         self.__dict__ = self

# class Synthetic(Namespace):
#     pass


def ExecuteText(source, locals = None, globals = None,
                codeSource = '<interactive text input>'):

    if source is not None:
        if isinstance(source, str):
            code = compile(source, codeSource, 'exec')
        else:
            code = source
            assert isinstance(code, CodeType), ValueError(code)

        if locals is None:
            locals = dict()
        if globals is None:
            globals = locals

        exec(code, globals, locals)

    return (globals, locals)

exe = ExecuteText

class Executable:
    def executeIn(self, locals, globals, **kwd):
        ExecuteText(self.codeObject, locals = locals, globals = globals, **kwd)

    def newModule(self, name = None, values = None, **kwd):
        module = ModuleType(name or self.name)

        try: register = kwd.pop('registration')
        except KeyError:
            pass
        else:
            # Register newly-created instance BEFORE execution,
            # (putting it in system.modules, for instances), so
            # that the code can access itself.
            if callable(register):
                register(module)

        ns = module.__dict__
        if isinstance(values, dict):
            ns.update(values)

        self.executeIn(ns, ns, **kwd)
        return module

    def execute(self, **kwd):
        import __main__ as main; main = main.__dict__
        self.executeIn(self.space, main, **kwd)

    def executeWith(self, values, **kwd):
        self.space.update(values)
        return self.execute()

    # __call__ = execute

    @property # memorized?
    def module(self):
        return self.newModule()

    def evaluate(self, locals = None, globals = None):
        if locals is None:
            locals = dict()
        if globals is None:
            globals = dict() # self.space

        return eval(self.codeObject, globals, locals)

    ##    def evaluate(self, *args, **kwd):
    ##        return eval(self.Original(self), *args, **kwd)

    evaluated = property(evaluate)

    @classmethod
    def Evaluate(self, code, **env):
        return self(code, name = env.pop('name')) \
               .evaluate(locals = env.pop('locals'),
                         globals = env.pop('globals'))


def splitOne(s, c):
    i = s.find(c)
    if i >= 0:
        return (s[:i], s[i+1:])

    return (s, '')


class Indent:
    class Buffer:
        @classmethod
        def Get(self, buf = None):
            if buf is None:
                return StringIO()

            return buf

def camelize(*parts):
    return ''.join(parts[0] + (p.capitalize() for p in parts[1:]))

def merge(b, **kwd):
    return dict(b, **kwd)

    # b.update(kwd)
    # return kwd


class SourceCode:
    def GenerateFunction(self, *args, **kwd):
        raise NotImplementedError

    class Function:
        def __init__(self, *args, **kwd):
            raise NotImplementedError


class ContextStackScope(Object, list): # UserDict
    @contextmanager
    def __call__(self, **variables):
        self.append(dict())

        try: yield self.update(variables)
        finally:
            self.pop()

    def getAttributeString(self):
        return '%d levels' % len(self)
 
    # Accessors.
    @property
    def current(self):
        return list.__getitem__(self, -1)

    # data = current # for UserDict, making the following unnecessary:

    def update(self, dict = None, **kwd):
        if dict is not None:
            self.current.update(dict)

        self.current.update(kwd)
        return self

    def __getitem__(self, name):
        # return self.current[name]

        e = None
        for i in range(len(self)-1, -1, -1):
            try: return list.__getitem__(self, i)[name]
            except KeyError as e: pass

        if e is None:
            e = KeyError(name)

        raise e

    ##    def __getattr__(self, name):
    ##        # XXX :skip: Need to simulate base-access order upon attribute.
    ##
    ##        try: return list.__getitem__(self, -1)[name]
    ##        except KeyError:
    ##            return list.__getattribute__(self, name)

    @property
    def parent(self):
        return self.Parent(self, len(self) - 2)

    class Parent:
        @property
        def parent(self):
            assert self.__level > 0
            return classOf(self)(self.__scope, self.__level - 1)

        @property
        def scope(self):
            return list.__getitem__(self.__scope, self.__level)

        def __init__(self, scope, level):
            self.__scope = scope
            self.__level = level

        def __getitem__(self, name):
            return self.scope[name]
        def keys(self):
            return list(self.scope.keys())


# class ContextStackScope(list):
#     @contextmanager
#     def __call__(self, **kwd):
#         self.append(kwd)

#         try: yield
#         finally:
#             self.pop()


#     def __getattr__(self, name):
#         try: return object.__getattribute__(self, name)
#         except AttributeError:
#             for s in reversed(self):
#                 try: return s[name]
#                 except KeyError:
#                     continue

#             raise AttributeError(name)


@contextmanager
def mutateObject(object, **values):
    prev = dict()

    for (name, v) in values.items():
        try: prev[name] = getattr(object, name)
        except AttributeError: pass

        setattr(object, name, v)

    try: yield
    finally:
        for (name, v) in prev.items():
            setattr(object, name, v)


def registerSystemModule(name, module):
    from sys import modules
    modules[name] = module
    return module


def LookupObject(name):
    if ':' in name:
        (module, cls) = name.split(':')

        object = __import__(module, fromlist = [''])

        for n in cls.split('.'):
            object = getattr(object, n)

        return object

    return __import__(name, fromlist = [''])


WS = re.compile(r'^(\s*)').match
def indentOf(n):
    m = WS(n)
    return 0 if m is None else len(m.group(1))

def dedentBy(lines, i, lo = 0, hi = None):
    if hi is None:
        hi = len(lines)

    for x in range(lo, hi):
        n = lines[x]
        for c in n[:i]:
            if c not in ' \t':
                raise SyntaxError(repr(c))

        lines[x] = n[i:]

def dedent(string):
    lines = string.split('\n')

    # Delete any leading blank lines.
    for f in range(len(lines)):
        if lines[f]:
            break

    del lines[:f]

    if lines:
        i = indentOf(lines[0])
        dedentBy(lines, i)
        lines.append('')

    return '\n'.join(lines)
