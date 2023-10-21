# MUD Runtime Object Registry.
# Copy 2021 runphase.com .  All rights reserved.
#
# Todo: get this from common tools.
_undefined = object()

class RegistryNotInstalled(RuntimeError):
    pass
class ObjectAlreadyRegistered(RuntimeError):
    pass
class DoesNotExistError(KeyError):
    pass

class Access(object): # todo: inherit from runtime.structure.Object? and builtin.object
    # VHLL object access interface and runtime base class.
    doesNotExist = DoesNotExistError

    class Node(object):
        def __init__(self, parent, name, call):
            self._parent = parent
            self._name = name
            self._call = call

        def _buildName(self):
            if self._parent:
                return '%s::%s' % (self._parent._buildName(), self._name)

            return self._name

        def __str__(self):
            return self._buildName()
        __repr__ = __str__

        def __getattr__(self, name):
            if not name.startswith('_'):
                # The basic goal here is to return a sub-node with priority
                # over attributes on the real, registered object, but support
                # dynamically access to those members secondarily.  This means
                # dynamic access to those members, except where eclipsed by
                # an inferior sub-node.
                #
                # This works effectively if the sub-objects are initialized
                # before the main object.  Otherwise, you'll have to use the
                # explicit get/registerObject toplevel routines if you know
                # for sure that it has a similarly named attribute.
                sub = Access.Node(self, name, self._call) # for reference.

                # Try to get the inferior object as named.
                if getObject(sub._buildName()) is None:
                    # Try to find an attribute on this named object.
                    o = getObject(self._buildName())
                    if o is not None:
                        # Only if there is an explicit attribute, and this isn't
                        # eclipsed by a registered sub-node object.
                        try: return object.__getattribute__(o, name)
                        except AttributeError:
                            pass # in this case, use unregistered sub-node:

                # Return the inferior node (not the object).
                # This means explicitly registered:
                #   Object::API
                #
                # will override the runtime['Object'].API real attribute,
                # that would be dereferenced above.
                #
                # By returning the node, instead of the object, sub-inferior
                # objects can still be referenced, even if there's an object
                # at Object, Object::API and Object::API:SubApi.
                #
                # This way, the real registered object is never returned by
                # this attribute lookup, only ever nodes.  Use explicit
                # getObject dereferencing to achieve this:
                #
                #   runtime['Object'].API
                #
                return sub

            return object.__getattribute__(self, name)

        def __call__(self, *args, **kwd):
            # runtime.Resource.Pool.Master(dict)
            # Q: Should this use registerObject? (to raise an error..)
            return self._call(self, *args, **kwd)

        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def __getattr__(self, name):
        # Create Top-level Accessor.
        # XXX :skip: Also, prevents top-level object names from being accessed
        # directly, this way (because Access is not an Access.Node).
        #
        return object.__getattribute__(self, name) \
               if name.startswith('_') \
                  else Access.Node(None, name, self._callCreate)

    def __getitem__(self, node):
        if isinstance(node, self.Node):
            node = node._buildName()

        if not isinstance(node, str):
            raise ValueError(node)

        return getObject(node)

    def __delitem__(self, node):
        if isinstance(node, self.Node):
            node = node._buildName()

        if not isinstance(node, str):
            raise ValueError(node)

        return delObject(node)

    def _callCreate(self, node, create = None, *args, **kwd):
        return getObject(node._buildName(),
                         create = lambda:create(*args, **kwd))

    def _doesNotExistError(self, name):
        raise DoesNotExistError(name)

    def _callNoCreate(self, node):
        return self._callCreate(node, self._doesNotExistError, node._buildName())

    def _callCall(self, node, *args, **kwd):
        # Call the registry object as a method with arguments.
        # Object must exist in registry or an error is raised.
        method = self._callNoCreate(node)
        return method(*args, **kwd)

    def _callCallIf(self, node, *args, **kwd):
        # Call the registry object as a method with arguments.
        # Nothing happens if object doesn't exist.
        try: method = self._callNoCreate(node)
        except DoesNotExistError: pass
        else: return method(*args, **kwd)

    def _callOn(self, node, client, *args, **kwd):
        # Wrap the client method with the callable registry object constructor.
        # Object must exist in registry or an error is raised.
        #
        # Note: this re-interprets the access node as the parent being an object
        # that has an attribute given by the terminal node name that is a Binding,
        # and then dereferences the binding's decorator (and calls it).

        parent = self._callNoCreate(node._parent)
        method = getattr(parent, node._name).on
        return method(client, *args, **kwd)

    def api(self, fon):
        return registerApi(fon)

    class _method(object):
        def __init__(self, access, method):
            self._access = access
            self._method = method

        def __getattr__(self, name):
            return self._access.Node(None, name, self._method)

    @property
    def call(self):
        return self._method(self, self._callCall)
    @property
    def callIf(self):
        return self._method(self, self._callCallIf)
    @property
    def on(self):
        return self._method(self, self._callOn)

    def __call__(self, node, *args, **kwd):
        def call(function):
            default = kwd.pop('default')
            object = self[node]
            if object is None:
                return default

            return function(object, *args, **kwd)

        return call

    def available(self, node, default = None):
        # todo: make this an accessor?
        def make(function):
            # XXX :skip: instance argument positioning.
            # todo: bind an availability decoration before object registration?
            def call(*args, **kwd):
                kwd = dict(default = default, **kwd)
                result = self(node, *args, **kwd)
                return result(function)
            return call
        return make


    def requireCall(self, node, *args, **kwd):
        def call(function):
            object = self[node]
            if object is None:
                raise AssertionError(f'Not available: {node}')

            return function(object, *args, **kwd)

        return call

    def require(self, node):
        def make(function):
            def call(*args, **kwd):
                result = self.requireCall(node, *args, **kwd)
                return result(function)
            return call
        return make


def lookup(accessor):
    '''
    @lookup(runtime)
    def dereference(node, *args, **kwd)
        return lambda *secondArgs, **secondKwd: \
            runtime[node](*args, **kwd)

    '''

    def bindToMethod(method):
        return accessor._method(accessor, method)

    return bindToMethod


# Construction:
def _createRegistry():
    return dict()

# The registry must be created initially.
# ---
# The registry storage object is a part of the runtime object,
# which is a component of the system module:
#    (systemModule->)runtime->(registryAccess)
#
# Both of these objects are composed with the following routines.

RUNTIME_OBJECT_NAME = 'runtime'
def getRuntimeObject():
    import sys as systemModule

    # Try to get from container module cache.
    try: return getattr(systemModule, RUNTIME_OBJECT_NAME)
    except AttributeError:
        pass

    # The Runtime class implementation is in a superior module,
    # (which derives from registry.Access)
    from . import MudRuntime
    runtime = MudRuntime()
    runtime.system = runtime.System #: Cache this node.

    # Put into runtime container module.
    setattr(systemModule, RUNTIME_OBJECT_NAME, runtime)

    from stuphos.etc.tools import registerBuiltin
    registerBuiltin(runtime, RUNTIME_OBJECT_NAME)
    registerBuiltin(runtime, 'components')

    return runtime

# XXX :skip: Want to set 'registry' on runtime, but the attribute lookup dynamically
# builds an Access.Node for anything that doesn't start with '_'
RUNTIME_REGISTRY_NAME = '_registry'
def getRegistry(create = False):
    runtimeObject = getRuntimeObject()

    try: registry = getattr(runtimeObject, RUNTIME_REGISTRY_NAME)
    except AttributeError:
        if create not in (None, False, 0):
            registry = _createRegistry()
            setattr(runtimeObject, RUNTIME_REGISTRY_NAME, registry)
            # runtimeObject.registry = registry

            # Hook shutdown game event with registry-cleanup function:
            #   This expects a certain kind of object (Binding) to
            #   be passed as 'create' parameter.  Otherwise, ignores.
            #
            #   (Admittedly, a weird convention).
            #
            try: create.shutdownGame(deleteAllObjects)
            except AttributeError:
                pass
        else:
            registry = None

    return registry

# Access API:
def getObject(name, create = None, **kwd):
    reg = getRegistry()
    if reg is None:
        raise RegistryNotInstalled('Registry not installed.')

    obj = reg.get(name, _undefined)
    if obj is _undefined:
        if callable(create):
            obj = reg[name] = create(**kwd)
        else:
            obj = None

    return obj

def setObject(name, value):
    reg = getRegistry()
    if reg is not None:
        if isinstance(name, Access.Node):
            name = name._buildName()

        reg[name] = value
    else:
        raise RegistryNotInstalled('Registry not installed.')

def registerObject(name, value):
    reg = getRegistry()
    if reg is not None:
        if isinstance(name, Access.Node):
            name = name._buildName()

        if name in reg:
            raise ObjectAlreadyRegistered(name)

        reg[name] = value
    else:
        raise RegistryNotInstalled('Registry not installed.')

def registerApi(fon, apiObject = None): # function-or-name
    if isinstance(fon, Access.Node):
        fon = fon._buildName()

    if isinstance(fon, str):
        if apiObject is not None:
            # Just directly register the object as an api.
            registerObject(fon, apiObject)
            return

        def makeNamedApiRegistry(object):
            registerObject(fon, object)
            return object

        return makeNamedApiRegistry

    # Expect a decorator style.
    assert apiObject is None

    def makeDefaultApiRegistry(object):
        # This style looks for a pre-programmed name.
        registerObject(object.NAME, object)
        return object

    return makeDefaultApiRegistry

def callObject(name, *args, **kwd):
    object = getObject(name)
    if callable(object):
        return object(*args, **kwd)

def callObjectMethod(name, methodName, *args, **kwd):
    object = getObject(name)
    if object is not None:
        try: method = getattr(object, methodName)
        except AttributeError: pass
        else: return method(*args, **kwd)

def _doDelete(object):
    # Todo: Maybe call this __unregister__?
    try: delete = getattr(object, '__registry_delete__', None)
    except ValueError:
        # This occurs if the object is a builtin entity handle
        # that has become invalid (through game-play).
        delete = None

    if not callable(delete):
        return True

    result = delete()
    if result is None:
        return True

    return bool(result)

def delObject(name, registry = None):
    if registry is None: # Err, why am I doing this?  Don't do this...
        registry = getRegistry()

    if registry is not None and name in registry:
        if _doDelete(registry[name]):
            del registry[name]
            return True

    return False

deleteObject = delObject

def deleteAllObjects():
    from traceback import print_exc as traceback

    reg = getRegistry()
    for obj in list(reg.values()):
        try: _doDelete(obj)
        except:
            traceback()

    reg.clear()

# Runtime-Access Usage:
##    # Creation:
##    r_pool = runtime.System.Resource.Pool(dict)
##
##    # Deletion:
##    del runtime['System::API']
##    del runtime[runtime.System.API]
##
##    # Method-decorator-based registration.
##    @registerApi('System::API')
##    class SystemAPI:
##        pass
##
##    @registerApi(runtime.System.API)
##    class SystemAPI:
##        pass
##
##    @registerApi
##    class SystemAPI:
##        NAME = 'System::API'
##
##    # Runtime-access-decorator-based registration.
##    @runtime.api('System::API')
##    class SystemAPI:
##        pass
##
##    @runtime.api(runtime.System.API)
##    class SystemAPI:
##        pass
##
##    @runtime.api
##    class SystemAPI:
##        NAME = 'System::API'
##
##    # Exact object lookup:
##    runtime[runtime.System.API]
##    runtime['System::API']

# Application example:
##    # Cache this lazy accessor for immediate invocation:
##    cmApi = runtime.system.CommandMessaging.API
##    def HandlePayload(self, payload):
##        cmApi.ExecuteTrustedCommandMessage(self.getUrlBase(), payload)

# Todo: Allow another kind of access:
# '@penobscotrobotics.us/modules/fraun/conf;1'
