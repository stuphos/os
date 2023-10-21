# MUD Runtime -- Event Objects.
# Todo: from the component library/support module.
from stuphos.etc import getLetters, listSortInsert, logException

from sys import exc_info as getExceptionInfo
from traceback import print_exception as printException

# Event Handler Model.
class EventResult(Exception):
    def __init__(self, result):
        self.result = result
        # raise self

def eventResult(result):
    raise EventResult(result)

class MutableInstanceMethodObject:
    # Hack to be able to snap other members onto it.
    def __init__(self, method):
        self.__method = method
        self.__repr__ = method.__repr__
        self.__name__ = method.__name__
        self.__doc_ = method.__doc__

    def __call__(self, *args, **kwd):
        return self.__method(*args, **kwd)

class EventController:
    # Prismatic.
    def __init__(self, event_name):
        self.event_name = event_name
        self.handlers = []

        # Because: See Binding.__getattr__
        self.decorator = MutableInstanceMethodObject(self.decorator)
        self.decorator.last = self.last
        self.decorator.first = self.first

        self.on = self.decorator

    def __call__(self, *args, **kwd):
        for h in self.handlers:
            try: self.callHandler(h, *args, **kwd)
            except EventResult as e:
                return e.result

    def callHandler(self, handler, *args, **kwd):
        try: return handler(self, *args, **kwd)
        except EventResult:
            raise
        except:
            self.handleException(*getExceptionInfo())

    def handleException(self, cls, value, tb):
        # printException
        logException(cls, value, tb, traceback = True)

    def registerHandler(self, handler):
        # Facilitate module reloading by removing all equivilant handlers.
        removal = []
        for h in self.handlers:
            if h == handler:
                removal.append(h)

        for h in removal:
            self.handlers.remove(h)

        # Now insert via priority.
        listSortInsert(self.handlers, handler,
                       key = lambda h: h.priority)

    def __iadd__(self, handler):
        self.registerHandler(handler)
        return self

    def decorator(self, function):
        self.registerHandler(Concretion(function))
        return function

    def last(self, function):
        self.registerHandler(Concretion(function, priority = HandlerBase.PRIORITY_LAST))
        return function

    def first(self, function):
        self.registerHandler(Concretion(function, priority = HandlerBase.PRIORITY_FIRST))
        return function

    def __repr__(self):
        return '%s(%s): %d handlers' % (self.__class__.__name__, self.event_name, len(self.handlers))

class Binding(object):
    def __init__(self, module):
        self.module = module

    def getController(self, name):
        try: ctlr = getattr(self.module, name)
        except AttributeError:
            ctlr = EventController(name)
            setattr(self.module, name, ctlr)
        else:
            assert issubclass(ctlr.__class__, EventController)

        return ctlr

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError as e:
            if not name.startswith('_'):
                # See EventController.__init__
                return self.getController(name).decorator

            raise e


    # def __getattr__(self, name):
    #     # XXX won't this recurse on self.getController? :skip:
    #     # todo: first try to do an object.__getattribute__, catching AttributeError and then do the controller decorator
    #     if not name.startswith('_'):
    #         # See EventController.__init__
    #         return self.getController(name).decorator

    #     # XXX object.__getattribute__ :skip:
    #     return object.__getattr__(self, name)

def declareEventController(name, **others):
    controllerClass = others.get('Controller', EventController)
    Module = others.get('Module')

    ctlr = controllerClass(name)
    if type(Module) is str:
        try: Module = __import__(Module)
        except ImportError:
            Module = None

    if Module is not None:
        setattr(Module, name, ctlr)

    return ctlr

def declare(module, events):
    for name in events:
        if not hasattr(module, name):
            ctlr = EventController(name)
            setattr(module, name, ctlr)

class EventBridge:
    # this is not used but a similar symbol is defined in system/__init__.
    class Calling:
        def __init__(self, name):
            self.name = name
        def __call__(self, *args, **kwd):
            try: from stuphos.system.api import game
            except ImportError:
                from stuphos.system import game

            bridgeModule = game.bridgeModule()
            if bridgeModule:
                function = getattr(bridgeModule, self.name, None)
                if callable(function):
                    return function(*args, **kwd)

        def __repr__(self):
            print('Calling: %r' % self.name)
        __str__ = __repr__

    def __setattr__(self, name, value):
        self.__dict__[name] = self.Calling(value)

# Handler Types.
class HandlerBase:
    PRIORITY_FIRST = 0
    PRIORITY_LAST = 10000
    PRIORITY_NORMAL = (PRIORITY_LAST - PRIORITY_FIRST) / 2

    def __init__(self, priority = None):
        self.priority = priority

    def __call__(self, ctlr, *args, **kwd):
        pass

    def sameClass(self, other):
        try:
            thisClass = self.__class__
            otherClass = other.__class__

            return thisClass.__module__ == otherClass.__module__ and \
                   thisClass.__name__   == otherClass.__name__

        except AttributeError:
            return False

    def __eq__(self, other):
        return self.sameClass(other)
    def __cmp__(self, other):
        return cmp(self.priority, other.priority)

    @property
    def priority(self):
        return getattr(self, '_priority', self.PRIORITY_NORMAL)

    @priority.setter
    def priority(self, value):
        self._priority = self.PRIORITY_NORMAL \
                         if value is None \
                            else int(value)

class MemberResolutionHandler(HandlerBase):
    def __init__(self, method_name):
        method_name = method_name.split()[0].split('.')

        self.module = '.'.join(method_name[:-1])
        self.method = method_name[-1]

    def __call__(self, ctlr, *args, **kwd):
        try: module = self._import_module(self.module)
        except ImportError: pass
        else:
            if module:
                method = getattr(module, self.method, None)
                if callable(method):
                    return method(*args, **kwd)

    def _import_module(self, name):
        # Todo: import parts of name, in case the trailing items
        # are not submodules, but members.
        # (see mud/__init__: world.heartbeat.pulse)
        module = __import__(name)
        for m in name.split('.')[1:]:
            module = getattr(module, m)

        return module

    def __eq__(self, other):
        return self.sameClass(other) and \
               self.module == other.module and \
               self.method == other.method

    def __repr__(self):
        return 'resolve %s.%s' % (self.module, self.method)

class LoggingHandler(HandlerBase):
    def logEvent(self, ctlr, *args, **kwd):
        tab = '\n\t\t\t\t'

        msg = tab.join(map(repr, args))
        msg = '%s:%s%s' % (ctlr.event_name, tab, msg)

        if kwd:
            from pprint import pformat
            msg += tab
            msg += pformat(kwd)

        from stuphos import log
        log(msg)

    def __call__(self, ctlr, *args, **kwd):
        self.logEvent(ctlr, *args, **kwd)

class Concretion(HandlerBase):
    def __init__(self, function, *args, **kwd):
        HandlerBase.__init__(self, *args, **kwd)
        self.function = function

    def __call__(self, ctlr, *args, **kwd):
        # XXX todo: curry ctlr?? :skip:
        return self.function(*args, **kwd)

    def __eq__(self, other):
        if self.sameClass(other):
            return self.function.__module__ == other.function.__module__ and \
                   self.function.__name__ == other.function.__name__

    def __repr__(self):
        return repr(self.function)

# Parsing.
COMMENT_CHAR  = '#'
SECTION_LEFT  = '['
SECTION_RIGHT = ']'

def parseEvents(events, handler = None):
    for line in events.split('\n'):
        line = line.strip()
        if not line or line[0] == COMMENT_CHAR:
            continue

        if line[0] == SECTION_LEFT and line[-1] == SECTION_RIGHT:
            handler = line[1:-1]
        else:
            ws = line.find(' ')
            if ws < 0:
                yield line, handler, ''
            else:
                yield line[:ws], handler, line[ws + 1:].lstrip()

# A Configuration Layer.
_builtin_handlers = {'MemberResolution': MemberResolutionHandler,
                     'Logging'         : LoggingHandler}

def loadOnto(events, module):
    # Algorithm.
    for (name, handler, method) in parseEvents(events):
        ctlr = getattr(module, name, None)
        if ctlr is None:
            ctlr = EventController(name)
            setattr(module, name, ctlr)

        handlerClass = getHandlerClass(handler)
        if issubclass(handlerClass, HandlerBase):
            if method:
                ctlr += handlerClass(method)
            else:
                ctlr += handlerClass()

def getHandlerClass(name):
    return _builtin_handlers.get(getLetters(name))

def getEventNames(module):
    try: return module.implements
    except AttributeError: pass

    # Broad-spectrum:
    from . import EVENT_NAMES
    # import pdb; pdb.set_trace()
    return EVENT_NAMES
