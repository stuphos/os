# PyUtiLib Runtime Architecture
# Note: this isn't in use yet.
from pyutilib.component.core import *

PluginGlobals.clear()
PluginGlobals.interface_registry.clear()

def getTriggerName(name):
    return 'on' + name[0].upper() + name[1:].lower()

class Bridge:
    class Event:
        # XXX All shared across instances of Bridge for single subclass.
        def __init__(self, triggerName = None, behavior = None):
            self.triggerName = triggerName
            self.behavior = behavior

        def install(self, bridge, module, name):
            # Configure this instance.
            self.bridge = bridge
            self.name = name

            if self.triggerName is None:
                self.triggerName = getTriggerName(name)

            # And put into bridge module space.
            setattr(module, name, self)

        def __call__(self, *args, **kwd):
            return self.bridge.callEvent(self, *args, **kwd)
        def __repr__(self):
            return '<%s: %s>' % (self.__class__.__name__, self.name)

    def __init__(self, module):
        self.listeners = ExtensionPoint(self.Interface)

        for (name, event) in self.__class__.__dict__.items():
            if isinstance(event, self.Event):
                event.install(self, module, name)

    def callEvent(self, event, *args, **kwd):
        for o in self.listeners:
            trigger = getattr(o, event.triggerName, None)
            if callable(trigger):
                # Todo: implement calling conventions (like EventController) via event.behavior.
                #
                # This probably means putting most of this code back into Event,
                # but exposing what it needs (listeners), too.
                #
                # Note: this doesn't pass a event controller object as first argument.
                trigger(*args, **kwd)


# MUD World-Bridge Runtime Implementation.
# Todo: eliminate some redundancy in declaration of the methods & their bindings.
# Todo: get rid of trigger-based naming convention.
class IWorldEvents(Interface):
    # Trigger-based naming conventions.
    # todo: finish programming in all of these?
    def onHeartbeat(secs, usecs):
        'Called whenever possible.'
    def onMovement(ch, direction, cost):
        'Called when mobiles move.'

class WorldComponent(Plugin):
    # Q: Not sure if this is proper because it should be 'abstract'?
    # Hmm, this gets registered in the PluginEnvironment's registry,
    # as do all subclasses of this (under the class name, so they can
    # not be the same!!)  Research this.
    implements(IWorldEvents)

class WorldBridge(Bridge):
    Interface = IWorldEvents

    # Names as called via extension bridge.
    heartbeat = Bridge.Event()
    movement = Bridge.Event()

def bootStart():
    # Install the world events onto the module for dispatch.
    from stuphos.system.api import game
    WorldBridge(game.bridgeModule())


# Example.
class Facility:
    @classmethod
    def create(self):
        # hmm, PluginEnvironment.registry makes this design unrealistic?
        self.Instrument()

class X(Facility):
    # Whereby Facility will automatically instance this as plugin.
    class Instrument(WorldComponent):
        def onHeartbeat(self, secs, usecs):
            print('heartbeat:', secs, usecs)
            #raise NotImplementedError
        def onMovement(self, ch, direction, cost):
            print('movement:', ch, direction, cost)
            #raise NotImplementedError

import __main__ as main
WorldBridge(main)

X.create()
