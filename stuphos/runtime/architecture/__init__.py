# MUD Runtime -- Object Entities.
#
from .. import Concretion, declareEventController, EventController

# from types import DictionaryType
DictionaryType = dict
# from new import classobj as newClassObject
from types import new_class

def populateNamespace(data):
    def doNamespacePopulate(ns):
        ns.update(data)
    return doNamespacePopulate

def newClassObject(name, bases, values):
    return new_class(name, bases, exec_body = populateNamespace(values))

# Overall identity constant.
class Undefined(object):
    def __repr__(self):
        return self.__class__.__name__
    __str__ = __unicode__ = __repr__

Undefined = Undefined()

# Design Pattern.
class Singleton(object):
    # This should be further specialized into 'Event' for runtime constructs.
    class Meta(type):
        def __new__(self, name, bases, values):
            cls = type.__new__(self, name, bases, values)
            if Singleton in bases:
                return cls

            ##    postvalues = {}
            ##    for name in values.keys():
            ##        if name in ['__module__', '__doc__']:
            ##            postvalues[name] = values[name]
            ##            del values[name]
            ##
            ##    inst = cls(name, **values)
            ##    inst.__dict__.update(postvalues)
            ##    return inst

            return cls(name, **values)

# Identity.
class Object: # (object):
    class _Meta:
        Attributes = []

        def __init__(self, *attributes, **kwd):
            self.Attributes = list(attributes) + list(kwd.items())

        @staticmethod
        def formatAttribute(instance, a, default = Undefined):
            def getAttribute(name):
                if callable(name):
                    return name(instance)

                if name.endswith('()'):
                    v = getattr(instance._Meta, name[:-2], default)
                    if callable(v):
                        return v(instance)
                else:
                    return getattr(instance, name, default)

                return Undefined

            if type(a) in (list, tuple):
                if len(a) == 2:
                    return '%s = %r' % (a[0], getAttribute(a[1]))
                if len(a) == 3:
                    return '%s = %r' % (a[0], getAttribute(a[1], a[2]))

            elif type(a) is str:
                return '%s = %r' % (a, getAttribute(a))

        @staticmethod
        def className(instance):
            return instance.__object_name__()

        @classmethod
        def instanceRepr(self, instance):
            meta = instance._Meta
            attribs = ', '.join(meta.formatAttribute(instance, a) for \
                                a in meta.Attributes)
            if attribs:
                return '<%s %s>' % (meta.className(instance), attribs)

            return '<%s>' % meta.className(instance)

    def __init__(self, name = Undefined):
        if name is not Undefined:
            self.__name = name

    def __repr__(self):
        return self._Meta.instanceRepr(self)
    def __str__(self):
        return self.__repr__()

    # This should go in the Meta.
    def __object_name__(self):
        try: return self.__name
        except AttributeError:
            return self.__class__.__name__

    @classmethod
    def _instanceOf(self, other):
        return isinstance(other, self)

        ##    try: return issubclass(other.__class__, self)
        ##    except AttributeError:
        ##        return False

from .lookup import LookupObject
LookupClassObject = LookupObject

class Synthetic(Object, dict): # todo: determine if adding dict base type is stable
    class _Meta(Object._Meta):
        Attributes = Object._Meta.Attributes + ['members()']

        @staticmethod
        def members(instance):
            return ', '.join(map(str, list(instance.__dict__.keys())))

    def __init__(self, dict = None, **values):
        if not isinstance(dict, DictionaryType):
            assert dict is None
            dict = values
        else:
            dict.update(values)

        self.__dict__ = dict

    # todo: FromStructure and ToStructure methods like in WRLC

class Namespace(Synthetic):
    # XXX :skip: namespace traditionally has a dict pointing to self.
    pass

namespace = Namespace


# Component Event Model.
# todo: rename to `Instrument'
# todo: make Singleton behavior part of new, AutoInstrument class.
class Component(Singleton, Concretion, metaclass=Singleton.Meta):
    # Todo: Rename to Instrument?
    '''
    class Me(Component):
        Events = EVENTS + ['movementXYZ']

        class Module:
            # Or,
            implements = ['presidingAction']

            '''

    Module = 'bridge'
    Events = None

    def __init__(self, name, Module = None, Events = None, **others):
        # Register this component class instance with bridge module.
        self.Target = others.get('Target', self)

        if Module is None:
            Module = self.Module
        if Events is None:
            Events = self.getEventNames(Module)

        self.bindToRuntime(Module, Events)

        try: init = self.__instance_init__
        except AttributeError: pass
        else: init() # others['__init_args__']

    def __call__(self, ctlr, *args, **kwd):
        method = self.getTriggerFunction(ctlr.event_name)
        if callable(method):
            return method(ctlr, *args, **kwd)

    def __eq__(self, other):
        if self.sameClass(other):
            try:
                return self.__class__.__module__ == \
                         other.__class__.__module__ and \
                       self.__class__.__name__ == \
                         other.__class__.__name__

            except AttributeError:
                return False

    def getTriggerFunction(self, event_name):
        return getattr(self.Target, self.getTriggerName(event_name), None)
    def getTriggerName(self, event_name):
        return getTriggerName(event_name)

    def getEventNames(self, module):
        if self.Events is None:
            from ..events import getEventNames
            return getEventNames(module)

        return self.Events


    DYNAMIC_TRIGGERS = False
    def bindToRuntime(self, Module = None, Events = None):
        # system-dependent
        # Module: ExtensionPoint

        from ..events import Binding

        if Module == 'bridge':
            from stuphos import getBridgeModule
            Module = getBridgeModule()

        binding = Binding(Module)
        self.boundControllers = []

        if Events:
            for event in Events:
                # What this is saying is that it won't bind to events that don't exist.
                if self.DYNAMIC_TRIGGERS or callable(self.getTriggerFunction(event)):
                    ctlr = binding.getController(event)
                    ctlr.registerHandler(self)
                    self.boundControllers.append(ctlr)

    def __repr__(self):
        return '%s.%s (Component)' % (self.__module__, self.__class__.__name__)

    def __registry_delete__(self):
        for ctlr in self.boundControllers:
            ctlr.unregisterHandler(self)


def getTriggerName(event_name):
    return 'on%s%s' % (event_name[0].upper(), event_name[1:])

def newComponent(cls, name = None, **values):
    if name is None:
        # Unfortunately, it ends up taking up the module name that calls newClassObject.
        name = '%s.%s' % (cls.__module__, cls.__name__)

    # values['__instance_init__'] = cls.__init__
    # values['__init_args__'] = (args, kwd)
    return newClassObject(name, (Component, cls), values)

# This should be in events, but it relies on Singleton.
class DeclareEvent(Singleton, metaclass=Singleton.Meta):
    def __new__(self, *args, **kwd):
        return declareEventController(*args, **kwd)


# Memory management.
class writable(object):
    # Base class for emulated object attribute sets.
    def _setAttribute(self, name, value):
        return object.__setattr__(self, name, value)

class representable:
    def __repr__(self):
        return '<%s>' % self.__class__.__name__

class writeprotected(writable, representable):
    # The preferred native object base class for constraining memory sets.
    # The reason is derives from representable is so that you don't have to
    # derive from both of them.

    def __setattr__(self, name, value):
        # Note: allowing all private sets (preceeding undescore) simplifies Pythonic
        # private variables becoming writable.  Now this becomes unsuitable for any-
        # thing other than expressing objects into the virtual environment (where private
        # members are already protected).

        # try: pub = getattr(self, "__public_members__", "nothing")
        # except Exception as e:
        #     pub = f'{e.__class__.__name__}: {e}'
        # else:
        #     if pub == 'nothing' and name == '_owner': # Our case.
        #         debugOn()

        # print(f'{name} in {pub}')

        # So in otherwords, to repeat, I'm allowing private sets HERE, but only
        # because store_member denies them.
        if name.startswith('_') or name in getattr(self, '__public_members__', []):
            return self._setAttribute(name, value)

        raise AttributeError('Unwritable: %s' % name)

blockSetAttr = writeprotected

def getMemberStored(object, name):
    try: return object.__dict__[name]
    except KeyError:
        raise AttributeError(name)

class baseInstance(writable):
    def __setattr__(self, name, object):
        # from world import heartbeat as vm
        # task = vm.contextObject.task
        from stuphos.kernel import vmCurrentTask
        task = vmCurrentTask()

        try: existing = getMemberStored(self, name)
        except AttributeError:
            task.addObject(name)
        else:
            task.removeObject(existing)

        task.addObject(object)
        return self._setAttribute(name, object)


class extension: # (image):
    def __init__(self, object):
        self._object = object

wrapper = extension # = image

class weakExtension(extension):
    def __init__(self, object = None, weakref = None):
        if weakref is None:
            weakref = ref.weakref(object)

        self._weakref = weakref

    @property
    def _object(self):
        return self._weakref()


def reprWrapper(self):
    return '<%s: type %s>' % (self.__class__.__name__,
                              self._object.__class__.__name__)


class extensionObject(writeprotected, Object, wrapper):
    # More opaque than a transparent object.
    __init__ = extension.__init__
    __repr__ = reprWrapper

    def _getExtensionOrObjectAttr(self, name):
        '''
        class remoteLibraryNativeExtension(extensionObject):
            """
            tool.remote-library:
                path: com/runphase/library-extension
                methods:
                    - object: stuphos.runtime.architecture.remoteLibraryNativeExtension._Install
                      name: remote

            interface:
                commands:
                    remoteInstall($method)::
                        def call(routine, args):
                            'com/runphase/library-extension/remote'()
                            return act(routine, args)

                        task = task$(call, $.components.object, args$())
                        return task.result()

                        """

            # Optionally:
            __getattr__ = extensionObject._getExtensionOrObjectAttr

            @classmethod
            def _Install(self, frame):
                # Do this once.
                task = frame.task
                task.native = self(task.native)

            def create(self, frame, path, *args):
                return log.library.create(path, *args) # *map(convertValue, args)

                '''

        try: return object.__getattribute__(self, name)
        except AttributeError:
            return getattr(self._object, name)


def recastObject(wrapper, value):
    # isinstance is unacceptable because wrapped objects might very well inherit from them:
    # Todo: omit list and dict?
    if type(value) in (str, bytes, list, tuple, dict, int, float):
        return value

    return wrapper._recast(value)

class wrappedObject(extensionObject):
    # Fully-wrapped.
    def __init__(self, defn, object):
        self._defn = defn
        extensionObject.__init__(self, object)

    @classmethod
    def _deny(self, typeClass, *names, **kwd):
        defn = kwd.get('defn', None)
        if defn is None:
            defn = dict()

        perClass = defn.setdefault(f'{typeClass.__module__}.{typeClass.__name__}', dict())
        for n in names:
            perClass[n] = False

        return defn

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError:
            if name == '_defn': # Unpickled? XXX Todo: figure out why.
                raise AttributeError(name)

            if not self._checkAccess(name):
                from stuphos.kernel import vmCurrentTask
                progr = vmCurrentTask().findProgrammer()
                raise NoAccessException('' if progr is None else progr.principal,
                                        resource = self._objectName().split('.') + [name])

            o = getattr(self._object, name)
            if callable(o):
                return self._wrappedFunction(self, o)

            return o

    def _objectName(self):
        t = type(self._object)
        return f'{t.__module__}.{t.__name__}'

    def _checkAccess(self, name):
        # print(f'{name}')
        try: access = self._defn[self._objectName()][name]
        except KeyError:
            return True

        return bool(access)

    def _recast(self, *args, **kwd):
        # Todo: return wrappingObject derivative based on value type
        # mapped to wrapper (self) property.
        return self.__class__(self._defn, *args, **kwd)


    class _wrappedFunction(writeprotected):
        def __init__(self, wrapper, object):
            self._wrapper = wrapper
            self._object = object

        def __call__(self, *args, **kwd):
            r = self._object(*list(self._unwrapArgs(args)),
                             **dict(self._unwrapKwd(kwd)))

            return recastObject(self._wrapper, r)

        def _unwrapArgs(self, args):
            for a in args:
                if isinstance(a, wrappedObject):
                    yield a._object
                else:
                    yield a

        def _unwrapKwd(self, kwd):
            for (name, value) in kwd.items():
                if isinstance(value, wrappedObject):
                    yield (name, value._object)
                else:
                    yield (name, value)


    def _call(self, proc, *args, **kwd):
        return self._recast(proc(*args, **kwd))


    def __call__(self, *args, **kwd):
        # Translate arguments.
        return self._wrappedFunction(self, self._object) \
            (*args, **kwd)

    def __dir__(self):
        # Todo: return self._call(dir, self._object)
        return dir(self._object)

    # __new__(cls[, ...])
    # __init__(self[, ...])
    # __del__(self)

    # __repr__(self)
    # __str__(self)

    # __bytes__(self)
    # __format__(self, format_spec)

    def __lt__(self, *args, **kwd):
        return self._object.__lt__(*args, **kwd)
    def __le__(self, *args, **kwd):
        return self._object.__le__(*args, **kwd)
    def __eq__(self, *args, **kwd):
        return self._object.__eq__(*args, **kwd)
    def __ne__(self, *args, **kwd):
        return self._object.__ne__(*args, **kwd)
    def __gt__(self, *args, **kwd):
        return self._object.__gt__(*args, **kwd)
    def __ge__(self, *args, **kwd):
        return self._object.__ge__(*args, **kwd)
    def __hash__(self):
        return self._object.__hash__()
    def __bool__(self):
        return self._object.__bool__()

    # __getattr__(self, name)
    # __getattribute__(self, name)
    # __setattr__(self, name, value)
    # __delattr__(self, name)
    # __dir__(self)
    # __get__(self, instance, owner=None)
    # __set__(self, instance, value)
    # __delete__(self, instance)
    # __slots__
    # __set_name__(self, owner, name)
    # __call__(self[, args...])
    def __len__(self):
        return self._object.__len__()
    def __length_hint__(self):
        return self._object.__length_hint__()
    def __getitem__(self, *args, **kwd): # key):
        return self._object.__getitem__(*args, **kwd)
    def __setitem__(self, *args, **kwd): # key, value):
        return self._object.__setitem__(*args, **kwd)
    def __delitem__(self, *args, **kwd): # key):
        return self._object.__delitem__(*args, **kwd)
    # __missing__(self, key)
    def __iter__(self):
        return self._object.__iter__()
    # __reversed__(self)
    def __contains__(self, *args, **kwd):
        return self._object.__contains__(*args, **kwd)
    def __add__(self, *args, **kwd):
        return self._object.__add__(*args, **kwd)
    def __sub__(self, *args, **kwd):
        return self._object.__sub__(*args, **kwd)
    def __mul__(self, *args, **kwd):
        return self._object.__mul__(*args, **kwd)
    def __matmul__(self, *args, **kwd):
        return self._object.__matmul__(*args, **kwd)
    def __truediv__(self, *args, **kwd):
        return self._object.__truediv__(*args, **kwd)
    def __floordiv__(self, *args, **kwd):
        return self._object.__floordiv__(*args, **kwd)
    def __mod__(self, *args, **kwd):
        return self._object.__mod__(*args, **kwd)
    def __divmod__(self, *args, **kwd):
        return self._object.__divmod__(*args, **kwd)
    # def __pow__(self, other[, modulo])
    def __lshift__(self, *args, **kwd):
        return self._object.__lshift__(*args, **kwd)
    def __rshift__(self, *args, **kwd):
        return self._object.__rshift__(*args, **kwd)
    def __and__(self, *args, **kwd):
        return self._object.__and__(*args, **kwd)
    def __xor__(self, *args, **kwd):
        return self._object.__xor__(*args, **kwd)
    def __or__(self, *args, **kwd):
        return self._object.__or__(*args, **kwd)
    def __radd__(self, *args, **kwd):
        return self._object.__radd__(*args, **kwd)
    def __rsub__(self, *args, **kwd):
        return self._object.__rsub__(*args, **kwd)
    def __rmul__(self, *args, **kwd):
        return self._object.__rmul__(*args, **kwd)
    def __rmatmul__(self, *args, **kwd):
        return self._object.__rmatmul__(*args, **kwd)
    def __rtruediv__(self, *args, **kwd):
        return self._object.__rtruediv__(*args, **kwd)
    def __rfloordiv__(self, *args, **kwd):
        return self._object.__rfloordiv__(*args, **kwd)
    def __rmod__(self, *args, **kwd):
        return self._object.__rmod__(*args, **kwd)
    def __rdivmod__(self, *args, **kwd):
        return self._object.__rdivmod__(*args, **kwd)
    # __rpow__(self, other[, modulo])
    def __rlshift__(self, *args, **kwd):
        return self._object.__rlshift__(*args, **kwd)
    def __rrshift__(self, *args, **kwd):
        return self._object.__rrshift__(*args, **kwd)
    def __rand__(self, *args, **kwd):
        return self._object.__rand__(*args, **kwd)
    def __rxor__(self, *args, **kwd):
        return self._object.__rxor__(*args, **kwd)
    def __ror__(self, *args, **kwd):
        return self._object.__or__(*args, **kwd)
    def __iadd__(self, *args, **kwd):
        return self._object.__iadd__(*args, **kwd)
    def __isub__(self, *args, **kwd):
        return self._object.__isub__(*args, **kwd)
    def __imul__(self, *args, **kwd):
        return self._object.__imul__(*args, **kwd)
    def __imatmul__(self, *args, **kwd):
        return self._object.__imatmul__(*args, **kwd)
    def __itruediv__(self, *args, **kwd):
        return self._object.__itruediv__(*args, **kwd)
    def __ifloordiv__(self, *args, **kwd):
        return self._object.__ifloordiv__(*args, **kwd)
    def __imod__(self, *args, **kwd):
        return self._object.__imod__(*args, **kwd)
    # __ipow__(self, other[, modulo])
    def __ilshift__(self, *args, **kwd):
        return self._object.__ilshift__(*args, **kwd)
    def __irshift__(self, *args, **kwd):
        return self._object.__irshift__(*args, **kwd)
    def __iand__(self, *args, **kwd):
        return self._object.__iand__(*args, **kwd)
    def __ixor__(self, *args, **kwd):
        return self._object.__ixor__(*args, **kwd)
    def __ior__(self, *args, **kwd):
        return self._object.__ior__(*args, **kwd)
    def __neg__(self):
        return self._object.__neg__()
    def __pos__(self):
        return self._object.__pos__()
    def __abs__(self):
        return self._object.__abs__()
    def __invert__(self):
        return self._object.__invert__()
    def __complex__(self):
        return self._object.__complex__()
    def __int__(self):
        return self._object.__int__()
    def __float__(self):
        return self._object.__float__()
    def __index__(self):
        return self._object.__index__()
    # __round__(self[, ndigits]):
    def __trunc__(self):
        return self._object.__trunc__()
    def __floor__(self):
        return self._object.__floor__()
    def __ceil__(self):
        return self._object.__ceil__()
    def __enter__(self):
        return self._object.__enter__()
    def __exit__(self, *args, **kwd): # exc_type, exc_value, traceback):
        return self._object.__exit__(*args, **kwd)
    # __match_args__
    def __await__(self):
        return self._object.__await__()
    def __aiter__(self):
        return self._object.__aiter__()
    def __anext__(self):
        return self._object.__anext__()
    def __aenter__(self):
        return self._object.__aenter__()
    def __aexit__(self, *args, **kwd): # exc_type, exc_value, traceback):
        return self._object.__aexit__(*args, **kwd)


wrappingObject = wrappedObject

class zonedObject(wrappedObject):
    def __init__(self, defn, object, taskId):
        self._taskId = taskId
        wrappedObject.__init__(self, defn, object)

    def _recast(self, object):
        return self.__class__(self._defn, object, self._taskId)

    def _checkAccess(self, name):
        if wrappedObject._checkAccess(self, name):
            from stuphos.kernel import vmCurrentTask
            return vmCurrentTask().id == self._taskId


# class NamespaceRedirect(extensionObject):
#     def __getattr__(self, name):
#         try: return object.__getattribute__(self, name)
#         except AttributeError:
#             try: return self._object[name]
#             except KeyError:
#                 if name == 'items':
#                     def items():
#                         o = self._object
#                         for name in dir(o):
#                             if not name.startswith('_'):
#                                 yield (name, getattr(o, name))

#                     return items # XXX :skip: Todo: safe_native

#                 raise AttributeError(name)


class Transparent(extensionObject):
    # Mainly, pass wrapped object value in resolveSymbol.
    pass

class Translucent(extensionObject):
    # Do not dereference ._object when passing/returning.
    pass

_transparent = Transparent
_translucent = Translucent


class ExceptionType(Translucent):
    '''
    def exceptionClass(name, code):
        return act('kernel/callObject$', \
            ['stuphos.runtime.architecture.ExceptionType', \
             run$python(code, valueName = name)] + args$(), \
             keywords$())

        usage:
            return exceptionClass('exceptionClass', code) <- code:
                class exceptionClass(Exception):
                    pass

    '''

    # @classmethod
    def _fromMessage(self, message, *args, **kwd):
        return self._object(message, *args, **kwd)

    def _checkActionCall(self, *args, **kwd):
        return self._checkAction \
            (*args, **kwd) \
                ()

    def _checkAction(self, etype, exc, **kwd):
        def exceptionCheck():
            yield issubclass(etype, self._object)
            yield self
            yield exc

            # yield exceptionCheckHandle

        return exceptionCheck


class baseExceptionValue(Translucent):
    _type = None
    _python_traceback = None

    def __init__(self, value, type = None, python_traceback = None):
        Translucent.__init__(self, value)
        if type is not None:
            self._type = type
        if python_traceback is not None:
            self._python_traceback = python_traceback

    def __repr__(self):
        if isinstance(self._object, type):
            return f'<{self.__class__.__name__}: type {self._object.__name__}>'

        return f'<{self.__class__.__name__}: type {self._object.__class__.__name__}: {self._object}>'
    vars()['repr$'] = property(__repr__)

    def __str__(self):
        return str(self._object)

    @property
    def typeName(self):
        return str(self._object.__class__.__name__)
    @property
    def typeMessage(self):
        return f'{self._object.__class__.__name__}: {self._object}'

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError as e:
            t = self._type
            if t is not None:
                if name in getattr(t, '_methods', []):
                    m = getattr(t, name)
                    return lambda *args, **kwd: \
                        m(self._object, *args, **kwd)

            # print(f'[evalue$attr] {t}: {self}: {name}')
            # debugOn()

            raise e


class safeNative(writeprotected):
    # XXX Not pickle-friendly.
    _nokwd = False

    def __init__(self, callable, name = None, nokwd = None):
        # self.__call__ = callable
        self._callable = callable
        self._name = name

        if nokwd is not None:
            self._nokwd = nokwd

    def __call__(self, *args, **kwd):
        # Note: this is done in Native._run
        # if self._nokwd:
        #     return self.__dict__['_callable'](*args)

        return self.__dict__['_callable'](*args, **kwd)

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(f'Attribute {repr(name)} must not started with underscore!')

        return getattr(self.__dict__['_callable'], name)

        # try: return getattr(self.__dict__['_callable'], name)
        # except AttributeError:
        #     if name == 'extend':
        #         debugOn()

    # I don't know why I resort to this translation.  What am I hiding?
    # def __getattr__(self, name):
    #     # debugOn()
    #     try: return self.__dict__['_callable'][name] # translation
    #     except (TypeError, KeyError):
    #         raise AttributeError(name)

    def __getitem__(self, item):
        return self.__dict__['_callable'][item]

    def __repr__(self):
        return f'<native {self.__name__}>' # repr(self._callable)

    @property
    def __name__(self):
        # print(f"safe-native: {self.__dict__['_callable']}")
        if self._name is not None:
            return self._name

        return self.__dict__['_callable'].__name__

    @property
    def __doc__(self):
        # print(f"safe-native: {self.__dict__['_callable']}")
        return self.__dict__['_callable'].__doc__

_safe = _safe_native = safeNative


class safeNativeNoKeyword(safeNative):
    _nokwd = True

_safe_native_nokwd = safeNativeNoKeyword


class safeNativeClass(object):
    def __getattribute__(self, name):
        o = object.__getattribute__(self, name)
        if name.startswith('_'):
            return o

        if callable(o):
            return _safe_native(o)

        return o

_safe_native_class = safeNativeClass

class safeNativeObject:
    def __init__(self, object):
        self._object = object

    # getattribute is required, but it catches .__dict__ (and probably .__class__)
    def __getattribute__(self, name):
        # print(f'safe-native.getattr: {name}')
        # debugOn()

        if name in ['__dict__', '__class__', '_object']:
            return object.__getattribute__(self, name)

        o = getattr(object.__getattribute__(self, '__dict__')['_object'], name)
        if callable(o):
            return _safe_native(o)

        return o

    def __repr__(self):
        try: name = self._object.__name__
        except AttributeError:
            name = self._object.__class__.__name__

        return f'<native-object {name}>'

    def __iter__(self):
        return self._object.__iter__()
    def __next__(self):
        return self._object.__next__()

_safe_native_object = safeNativeObject


class safeIterator(writeprotected):
    __init__ = safeNativeObject.__init__
    __repr__ = safeNativeObject.__repr__

    def __iter__(self):
        return iter(self._object)

    def __next__(self, *args, **kwd):
        return self._object.__next__(*args, **kwd)

    @classmethod
    def decorator(self, function):
        def call(*args, **kwd):
            return self(function(*args, **kwd))
        return call

_safe_iterator = safeIterator


# Execution Primitives.
class InterpreterState(Exception):
    pass

class Yield(InterpreterState): # virtual.Machine.Task.Yield?
    pass

class Continuation(Yield):
    # Used to signal that processing should just continue.
    pass

class AwaitableContinuation(Continuation):
    pass

class OuterFrame(Continuation):
    def __init__(self, frame = None):
        self.frame = frame

    @property
    def returnValue(self):
        return self.frame.returnValue

    def onComplete(self, *args, **kwd):
        return self.frame.onComplete(*args, **kwd)

class BypassReturn(Continuation):
    pass

class YieldFrame(OuterFrame):
    pass


class Interrupt(InterpreterState):
    _uncatchable = True
class Timeout(Interrupt):
    _uncatchable = False
class TimeoutQuotaExceeded(Timeout):
    _uncatchable = True


class Uncompleted(RuntimeError):
    "A native or didn't complete because it resulted in an asynchronous operation that wasn't handled."


class Interface(writeprotected, Object):
    # Revealed to the GIRL object runtime, proxies the local subroutine def
    # through the vm invocation instruction.
    class _Meta(Object._Meta):
        Attributes = [('procedure', lambda i: repr(i._procedure))]

    def __init__(self, procedure):
        self._procedure = procedure

    def __str__(self):
        return self._procedure.pathString() or ''

    @property
    def _activation(self):
        # Return a copy of a PC-tracking invocation object.
        # Todo: Invocation(self._procedure)
        return self._procedure

class Done(InterpreterState, Object):
    pass

class ScheduledProcedureMixin:
    def _runSchedule(self, active, frame):
        return self._run(frame)

class Procedure(Object, ScheduledProcedureMixin):
    _Interface = Interface
    _Done = Done

    def __resolve__(self):
        return repr(self)


class Computer:
    # Instruction set.
    pass

class Source:
    pass


class Generator(writeprotected):
    _position = None

    def __init__(self, program, frame):
        self._setAttribute('_program', program)
        self._setAttribute('_frame', frame) # Old frame.
        self._setAttribute('_task', frame.task)
        self._setAttribute('_stack', dict())

    def __repr__(self):
        return f'<generator {repr(self._program)}>'

    def isGenerator(self):
        return True

    def __iter__(self):
        return self

    def __stopIteration__(self, pos):
        self._setAttribute('_position', pos)

    def _deleteStack(self, task):
        taskId = task.id
        stack = self._stack[taskId]
        del self._stack[taskId]

        ro = task.removeObject
        for i in stack:
            ro(i)

    def _restoreStack(self):
        stack = self._task.stack
        taskId = self._task.id

        try: saved = self._stack[taskId]
        except KeyError: pass
        else:
            list.extend(stack, saved)
            self._stack[taskId]

    def _saveStackRemove(self, frame):
        stack = self._task.stack
        n = len(stack) - frame.initialStackSize

        # Since this function is called by levelStack when the frame
        # is remove, yield will already have put a value on the stack,
        # which needs to not be saved (on this generator) or restored.
        x = self._stack[self._task.id] = stack[-n:-1]

        # print(f'[gen.stack.save] {x}')
        # debugOn()

        list.__delitem__(stack, slice(-n, -(n-1)))

    def __next__(self, genCycle = None, knowsYield = False):
        # Since for_next calls this function, we set up a new
        # frame call and then raise a Yield so that the runtime
        # can rely on frame-stack state to push the next iter.
        #
        # Also, memory.native.sequence calls this function
        # (setting genCycle).

        if not knowsYield:
            raise AssertionError('Must call Generator.__next__(knowsYield = True)!')

        self._restoreStack()

        # todo: do general frame copy, storing parameters on instance construction.
        new = self._task.addFrameCall \
            (self._program,
             locals = self._frame.locals,
             environ = self._frame.environ,
             programmer = self._frame.programmer,
             arguments = self._frame.arguments,
             keywords = self._frame.keywords,
             genContinue = self)

        # print(f'[gen.next] {new}')

        @new.onComplete
        def completion(it, etype = None, value = None, tb = None, traceback = None):
            # print(f'[gen.next.complete] {value}')

            it.genContinue = False # so that levelStack doesn't restore.

            if etype is StopIteration:
                if callable(genCycle):
                    # The call path for natives like sequence and kernel/map.
                    genCycle(self, stopIteration = True)
                else:
                    self._task.onStopIteration(it, self._position)

                return True

            # Note: don't pass/raise exceptions other than StopIteration.
            elif value is None and callable(genCycle):
                genCycle(self)

        raise new.yieldOuter


def progr_reveal(progr):
    hide = getattr(progr, '_principalHide', False)
    if hide:
        return f'<{"hidden" if hide is True else hide}>'

    try: p = progr.principal # WithCase?
    except AttributeError:
        p = progr

    p = str(p)

    if p.startswith('apikey:'):
        return '<API-Key>'

    return p

class NoAccessException(Exception):
    @classmethod
    def _fromMessage(self, args):
        (path, access) = args
        return self(None, resource = path, access = access)

    def __init__(self, programmer, resource = '?', access = '?', task = None):
        # todo: use task.id?
        # This format is compatible with 'agent grant' command.
        path = resource if isinstance(resource, str) else ' '.join(map(str, resource))
        Exception.__init__(self,
            f"[{task.taskName if task else ''}] {progr_reveal(programmer)} {access} {path}")
        # '[%s] %s for %s by %r' % (task.taskName if task else '', access, resource, programmer)

        self.programmer = programmer
        self.resource = resource
        self.access = access
        self._task = task

    # def pathNotFound(self):
    #     raise PathNotFound(self.resource)

    def node(self, *args):
        return AliasedView \
            ((self.resource if isinstance
                (self.resource, (list, tuple))
                else (self.resource,)) + args)


# Todo: because PathNotFound is part of ph, move this into that package.
def pathNotFound(noAccess):
    raise ValueError(noAccess.resource) # PathNotFound(noAccess.resource)

NoAccessException.pathNotFound = pathNotFound

def recastNoAccess(function):
    '''
    Catch NoAccessExceptions and reraise them as PathNotFound.
    This hides the fact that a missing permission can't be used
    to verify an existing node in the library.

    Use as a decorator.

    '''

    def call(*args, **kwd):
        try: return function(*args, **kwd)
        except NoAccessException as e:
            pathNotFound(e)

    call.__name__ = 'recastNoAccess:' + function.__name__
    return call


# Permissions.
SPECIAL_PRINCIPALS = ['group', 'agent', 'role', 'apikey']

def isSpecialPrincipal(principal):
    i = principal.find(':')
    if i > 0:
        return principal[:i].lower() in SPECIAL_PRINCIPALS


# Game-Level Objects.
class UnknownFlag(NameError):
    pass

class Bitvector(Object):
    # A pure implementation of the bitvector type in game module.
    class _Meta(Object._Meta):
        Attributes = Object._Meta.Attributes + ['set']

    def __init_subclass__(self, **kwd):
        pass

    def __init__(self, __bitv = 0, **bits):
        # This is an abstract base class.
        assert self.__class__ is not Bitvector

        self.__bitv = int(__bitv)
        for (name, value) in bits.items():
            setattr(self, name, bool(value))

        self.getUpperBitvNames()

    @classmethod
    def getUpperBitvNames(self):
        try: return self.__UPPER_BITVECTOR_NAMES
        except AttributeError:
            names = self.__UPPER_BITVECTOR_NAMES = \
                [n.upper() for n in self.BITVECTOR_NAMES]

        return names

    BITVECTOR_NAMES = []

    def isBitSet(self, bit):
        return bool(self.__bitv & bit)
    def getFlagBit(self, name):
        try: return (1 << self.getUpperBitvNames().index(name.upper()))
        except ValueError:
            raise UnknownFlag

    def isFlagSet(self, name):
        return self.isBitSet(self.getFlagBit(name))

    @property
    def names(self):
        return self.BITVECTOR_NAMES

    @property
    def set(self):
        return [name for name in self.names if self.isFlagSet(name)]

    @property
    def notset(self):
        return [name for name in self.names if not self.isFlagSet(name)]

    unset = nonset = notset

    def __getattr__(self, name):
        try: return self.isFlagSet(name)
        except UnknownFlag:
            return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        try: bit = self.getFlagBit(name)
        except UnknownFlag: return object.__setattr__(self, name, value)
        else: self.__bitv |= bit if value else ~bit

    def __int__(self):
        return int(self.__bitv)
    def __str__(self):
        return ', '.join(map(str, self.set))
    def __iter__(self):
        return iter(self.set)

class PromptPreferences(Bitvector):
    BITVECTOR_NAMES = ['Mail', 'DataRate']
