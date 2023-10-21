# This is actually specific to the embedded provision.
# --
# Contains objects used across the application:
#     .network.server.zones
#     .network.server.player.shell
#

from stuphmud.server.player.interfaces.dictcmd import CmdDict

from stuphos.kernel import Girl, Script, GirlSystemModule
from stuphos.system.api import mudlog
from stuphos.runtime.architecture.api import writeprotected, wrapper
from stuphos.etc.tools import isYesValue
from stuphos.etc.tools.logs import tracebackString

#girlSystemModule = runtime.Girl.System.Module

# todo: This module contains the base object EntityWrapper but it should probably
# go into runtime.architecture.
class EntityAdapter(wrapper, writeprotected):
    # Wraps layer zero.
    _readonly_properties = []

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError as e:
            if name in self._readonly_properties:
                return self._getWrappedAttribute(name)

            raise e

    def _getWrappedAttribute(self, name):
        return getattr(self._object, name)

    def __repr__(self):
        # This must be defined manually because it's already defined on EntityWrapper :)
        return repr(self._object)

class TriggerAdapter(EntityAdapter):
    pass


# Implementation of VM.Task.
class TriggerScript(Script):
    def __init__(self, *args, **kwd):
        tracing = kwd.pop('tracing', False)
        Script.__init__(self, *args, **kwd)
        self.uncaughtError = self.handleError
        if tracing == 'profile':
            self.tracing = self.profile
        elif tracing:
            # Use operator/programmer for output.
            self.tracing = self.auditInstruction # traceToLog

    def handleError(self, task, frame, exc, traceback):
        # name = "?" if frame is None else getattr(frame.procedure, "name", "?")
        # logOperation(f'[trigger$error] {name}:' + \
        #              f' {exc[0].__name__}: {exc[1]}')


        if not self.handleOperatorError(task, frame, exc, traceback):
            (exc_class, exc_value, exc_tb) = exc
    
            # XXX :skip: mudlog doesn't log to file (console stderr)
            def mudlog(s):
                logOperation('[trigger$error] ' + s)

            mudlog('(%s: %s) %s: %s\n%s' % \
                (task.name, '?' if frame is None else \
                 getattr(frame.procedure, 'name', '?'),
                 exc_class.__name__, exc_value,
                 tracebackString(exc_tb, indent = 4)))

        raise self.Done

    def frameOne(self, *args, **kwd):
        try: return Script.frameOne(self, *args, **kwd)
        except Script.Done as e:
            # Todo: task.onComplete/frame.onComplete
            # (Right now, we're just popping the stack, which doesn't need to be done)
            try: result = self.stack.pop()[0]
            except IndexError: pass
            else:
                if result is not None:
                    pass # todo: evaluate with result

            raise e

    def traceToLog(self, frame, pos, instr, args):
        # todo: logstream to database
        mudlog('%04d %s(%s)' % (pos, getattr(instr, '__name__', '?'),
                                ', '.join(map(str, args))))

    # Invocation Methods:
    @classmethod
    def invokeTrigger(self, program, context, tracing = False,
                      programmer = None, name = None):

        # from stuphos.kernel import startTask # XXX :skip: This is somehow named wrongly in the interior import.  Where is global startTask??
        from stuphos.kernel import executeGirl
        # context.setdefault('system', GirlSystemModule.Get())

        program = program.replace('\r', '')
        program = Girl(Girl.Module, program)

        if programmer is None:
            user = None
        else:
            from stuphos.kernel import findUserByName
            user = findUserByName(programmer.principal)

        task = self.Load(tracing = tracing, environ = context, user = user) # , programmer = programmer)
        task.name = name
        task.operator = None if programmer is None else programmer.principal
        program.setEnvironment(task.environ)
        program.name = name
        # programmer.invoke(task, program)
        # startTask(task, program, programmer = programmer)

        task.addFrameCall(program, programmer = programmer)
        executeGirl(task)
        # return task

    @classmethod
    def invokeVerbCommand(self, player, target, object):
        pass

class MobileScript(TriggerScript):
    pass

class TriggerTemplate:
    # Adapter (wrapper).
    typeName = 'Trigger'
    typeCode = '--'

    class Argument:
        def __init__(self, number, name, value):
            self.number = number
            self.name = name
            self.value = value

        def setValue(self, trigger, value):
            pass

    def __init__(self, trigger):
        self.trigger = trigger

    def arguments(self):
        return iter(())
    def argumentsMapping(self):
        r = dict((arg.number, arg) for arg in self.arguments())
        return r

    def setCode(self, code):
        self.trigger.program = code


# Triggers.
class TriggerBase:
    def actTriggered(self, string):
        return False
    def departureTriggered(self):
        return False
    def arrivalTriggered(self):
        return False
    def deathTriggered(self):
        return False
    def mobileCreated(self):
        return False
    def portalOutTriggered(self):
        return False
    def portalInTriggered(self):
        return False

class MobileTrigger(TriggerBase):
    def __init__(self, program, programmer = None, tracing = None):
        self.program = program
        self.programmer = programmer
        self.tracing = tracing
    def invoke(self, *args):
        raise NotImplementedError

    FLAG_AUDIT = (1 << 0)

    @property
    def flags(self):
        yield dict(name = 'Audit', set = bool(self.tracing))

    @property
    def bitvector(self):
        return self.FLAG_AUDIT if self.tracing else 0

def prototypeTriggering(ch, callback):
    # Try triggers for this mobile instance.
    try: triggers = ch.triggers
    except AttributeError: pass
    else:
        for (i, trig) in enumerate(triggers):
            if callback(ch, trig, i):
                return True

    # Try triggers registered for the prototype.
    # Note: check identity of triggers object because
    # entity_instance (mobile_instance) overrides
    # __getattr__.
    try: ptriggers = ch.prototype.triggers
    except AttributeError: pass
    else:
        if ptriggers is not triggers:
            for (i, trig) in enumerate(triggers):
                if callback(ch, trig, i):
                    return True

def getTriggerName(object, nr, trig):
    return '%s:%d:%s' % (object, nr, getMobileTriggerType(trig).typeCode)

from random import randint
class RandomizedMobileTrigger(MobileTrigger):
    def __init__(self, chance, program):
        MobileTrigger.__init__(self, program)
        self.chance = int(chance)

    @property
    def triggerChance(self):
        return randint(0, 100) < self.chance

def getCallString(first, *args):
    return '%s(%s)' % (first, ', '.join(map(repr, args)))

class ActMobileTrigger(MobileTrigger):
    # ActMobileTrigger('*', "...")
    def __init__(self, matching, program):
        MobileTrigger.__init__(self, program)
        self.matching = matching
    def actTriggered(self, string):
        if self.matching == '*':
            return True

        import re
        return re.match(self.matching, string) is not None
        return self.matching in string

    def invoke(self, string, target, actor, item,
               indirect_actor, indirect_item,
               name):
        return MobileScript.invokeTrigger \
               (self.program,
                dict(string = string,
                     target = target,
                     actor = actor, # mud.zones.World.ZoneAccess.MobileInstance(actor),
                     item = item,
                     indirectActor = indirect_actor,
                     indirectItem = indirect_item),
                programmer = self.programmer,
                tracing = self.tracing,
                name = name)

    @classmethod
    def Event(self, original, string, target, actor, item, indirect_actor, indirect_item):
        ##    mudlog(getCallString('act', original, string, target, actor,
        ##                         item, indirect_actor, indirect_item))

        # For each call to act, as sent to a player (one with a descriptor),
        # loop over each mobile in the same room as the player, and search
        # for an act trigger.

        # Unfortunately, this doesn't do what you might expect it to: make
        # a mobile react to an act string sent to it.  This is because, most
        # of the time, no act strings are sent to mobiles because they don't
        # have playing descriptors.

        # So, this has mobiles reacting to all act strings sent to players,
        # even if it doesn't make sense that the mobile wouldn't be receiving
        # any of those strings.  Of course, it also means mobiles reacting
        # to multiple perform_act invocations per act call.

        # This is to mimic DG scripts as closely as possible (although admittedly,
        # not at all).

        def action(object, trig, nr):
            if trig.actTriggered(string):
                trig.invoke(string, target, actor, item,
                            indirect_actor, indirect_item,
                            getTriggerName(object, nr, trig))

                return True

        for ch in target.room.people:
            if ch is target:
                continue
            if ch.isPlayer:
                continue

            if prototypeTriggering(ch, action):
                return

performAct = ActMobileTrigger.Event

class MovementTrigger(RandomizedMobileTrigger):
    def invoke(self, object, mobile, origin, destination,
               direction, verb, movementNeeded, name):
        return MobileScript.invokeTrigger \
               (self.program,
                dict(object = object,
                     mobile = mobile,
                     origin = origin,
                     destination = destination,
                     direction = direction,
                     verb = verb,
                     movementNeeded = movementNeeded,
                     points = movementNeeded),
                programmer = self.programmer,
                tracing = self.tracing,
                name = name)

    def invokePortal(self, object, mobile, origin, destination, portal):
        return MobileScript.invokeTrigger \
               (self.program,
                dict(object = object,
                     mobile = mobile,
                     origin = origin,
                     destination = destination,
                     portal = portal),
                programmer = self.programmer,
                tracing = self.tracing)

class DepartureMobileTrigger(MovementTrigger):
    def departureTriggered(self):
        return self.triggerChance

    @classmethod
    def Event(self, mobile, origin, destination, direction, verb, movementNeeded):
        # mobile is what's moving -- including players, but the trigger is found on neighbors.
        # todo: invoke with triggered mobile instance handle parameter.
        def action(object, trig, nr):
            if trig.departureTriggered():
                trig.invoke(object, mobile, origin, destination,
                            direction, verb, movementNeeded,
                            getTriggerName(object, nr, trig))
                return True

        # Trigger for all NPCs that aren't currently doing the roaming.
        for ch in origin.people:
            if ch is mobile:
                continue
            if ch.isPlayer:
                continue

            if prototypeTriggering(ch, action):
                return

class PortalOutTrigger(MovementTrigger):
    def portalOutTriggered(self):
        return self.triggerChance

    @classmethod
    def Event(self, mobile, origin, destination, portal):
        def action(object, trig, nr):
            if trig.portalOutTriggered():
                trig.invokePortal(object, mobile, origin, destination, portal)
                return True

departure = DepartureMobileTrigger.Event
portalOut = PortalOutTrigger.Event

class ArrivalMobileTrigger(MovementTrigger):
    def arrivalTriggered(self):
        return self.triggerChance

    @classmethod
    def Event(self, mobile, origin, destination, direction, verb, movementNeeded):
        def action(object, trig, nr):
            if trig.arrivalTriggered():
                # import game
                # game.syslog('arrival: %r [%r]' % (object, mobile))

                trig.invoke(object, mobile, origin, destination,
                            direction, verb, movementNeeded,
                            getTriggerName(object, nr, trig))
                return True

        for ch in destination.people:
            if ch is mobile:
                continue
            if ch.isPlayer:
                continue

            if prototypeTriggering(ch, action):
                return

class PortalInTrigger(MovementTrigger):
    def portalInTriggered(self):
        return self.triggerChance

    @classmethod
    def Event(self, mobile, origin, destination, portal):
        def action(object, trig, nr):
            if trig.portalInTriggered():
                trig.invokePortal(object, mobile, origin, destination, portal)
                return True

arrival = ArrivalMobileTrigger.Event
portalIn = PortalInTrigger.Event

class DeathMobileTrigger(MobileTrigger):
    def deathTriggered(self):
        return True

    def invoke(self, victim, killer):
        return MobileScript.invokeTrigger \
               (self.program,
                dict(victim = victim,
                     killer = killer),
                programmer = self.programmer,
                tracing = self.tracing)

    @classmethod
    def Event(self, victim, killer):
        if victim.npc:
            def action(object, trig, nr):
                if trig.deathTriggered():
                    trig.invoke(victim, killer)
                    return True

            prototypeTriggering(victim, action)

slayMobile = DeathMobileTrigger.Event

class CreateMobileTrigger(MobileTrigger):
    def mobileCreated(self):
        return True

    def invoke(self, mobile, source, cause, name):
        # print(f'[create.mobile$trigger] {self.programmer}')

        return MobileScript.invokeTrigger \
               (self.program,
                dict(mobile = mobile,
                     source = source,
                     cause = cause),
                programmer = self.programmer,
                tracing = self.tracing,
                name = name)

    @classmethod
    def Event(self, mobile, source, cause):
        def action(object, trig, nr):
            if trig.mobileCreated():
                # logOperation(f'[create.mobile$trigger] #{nr}: {mobile} -- {trig.program}')
                # debugOn()

                trig.invoke(mobile, source, cause,
                            getTriggerName(object, nr, trig))

                return False # Allow pipelining of triggers.

        prototypeTriggering(mobile, action)

createMobileInstance = CreateMobileTrigger.Event


# Alteration Interface.
# This is here because it is relied on by both mud.zones and web.stuph.embedded.olc.triggers
class ActMobileTriggerTemplate(TriggerTemplate):
    typeName = 'Perform Act'
    typeCode = 'perform-act'

    methodology = \
'''
<h2>Methodology: Perform-Act</h2>

<p>
For each call to act, as sent to a player (one with a descriptor),
loop over each mobile in the same room as the player, and search
for an act trigger.
</p>

<p>
Unfortunately, this doesn't do what you might expect it to: make
a mobile react to an act string sent to it.  This is because, most
of the time, no act strings are sent to mobiles because they don't
have playing descriptors.
</p>

<p>
So, this has mobiles reacting to all act strings sent to players,
even if it doesn't make sense that the mobile wouldn't be receiving
any of those strings.  Of course, it also means mobiles reacting
to multiple perform_act invocations per act call.
</p>

<p>
This is to mimic DG scripts as closely as possible (although admittedly,
not at all).
</p>

<pre>
    def performAct(original, string, target, actor, item, indirect_actor, indirect_item):
        def action(object, trig):
            if trig.actTriggered(string):
                trig.invoke(string, target, actor, item,
                            indirect_actor, indirect_item)
                return True

        for ch in target.room.people:
            if ch is target:
                continue
            if ch.isPlayer:
                continue

            # Iterate all triggers on instance and prototype, calling action with
            # ch as object, and the individual trigger object test as trig.
            if prototypeTriggering(ch, action):
                return
</pre>
'''

    parameters = ['string', 'target', 'actor', 'item', 'indirectActor', 'indirectItem']

    class MatchingArgument(TriggerTemplate.Argument):
        number = 0
        name = 'Pattern'

        def __init__(self, trigger):
            self.value = trigger.trigger.matching
        def setValue(self, trigger, value):
            trigger.matching = value

    def arguments(self):
        yield self.MatchingArgument(self)

    @classmethod
    def CreateEmpty(self):
        return ActMobileTrigger('', '')

class ChanceTemplate(TriggerTemplate):
    class ChanceArgument(TriggerTemplate.Argument):
        number = 0
        name = 'Chance'

        def __init__(self, trigger):
            self.value = trigger.trigger.chance
        def setValue(self, trigger, value):
            trigger.chance = int(value)

    def arguments(self):
        yield self.ChanceArgument(self)

class DepartureMobileTriggerTemplate(ChanceTemplate):
    typeName = 'Departure'
    typeCode = 'departure'

    methodology = \
    '''
    Reacts probabilistically to movement of other NPCs, departing this room.
    '''

    parameters = ['object', 'mobile', 'origin', 'destination',
                  'direction', 'verb', 'points']

    @classmethod
    def CreateEmpty(self):
        return DepartureMobileTrigger(0, '')

class ArrivalMobileTriggerTemplate(ChanceTemplate):
    typeName = 'Arrival'
    typeCode = 'arrival'

    methodology = \
    '''
    Reacts probabilistically to movement of other NPCs, entering this room.
    '''

    parameters = ['object', 'mobile', 'origin', 'destination',
                  'direction', 'verb', 'points']

    @classmethod
    def CreateEmpty(self):
        return ArrivalMobileTrigger(0, '')

class PortalOutTriggerTemplate(ChanceTemplate):
    typeName = 'Portal Out'
    typeCode = 'portal-out'

    @classmethod
    def CreateEmpty(self):
        return PortalOutTrigger(0, '')

class PortalInTriggerTemplate(ChanceTemplate):
    typeName = 'Portal In'
    typeCode = 'portal-in'

    @classmethod
    def CreateEmpty(self):
        return PortalInTrigger(0, '')

class DeathMobileTriggerTemplate(TriggerTemplate):
    typeName = 'Slay Mobile'
    typeCode = 'death'

    methodology = \
    '''
    Reacts to killing of one NPC by another mobile.
    '''

    parameters = ['killer', 'victim']

    @classmethod
    def CreateEmpty(self):
        return DeathMobileTrigger('')

class CreateMobileTriggerTemplate(TriggerTemplate):
    typeName = 'Create Mobile'
    typeCode = 'create'

    parameters = ['mobile', 'source', 'cause']

    @classmethod
    def CreateEmpty(self):
        return CreateMobileTrigger('')

MOBILE_TRIGGER_TEMPLATES = \
    dict(ActMobileTrigger = ActMobileTriggerTemplate,
         DepartureMobileTrigger = DepartureMobileTriggerTemplate,
         ArrivalMobileTrigger = ArrivalMobileTriggerTemplate,
         DeathMobileTrigger = DeathMobileTriggerTemplate,
         CreateMobileTrigger = CreateMobileTriggerTemplate,
         PortalOutTrigger = PortalOutTriggerTemplate,
         PortalInTrigger = PortalInTriggerTemplate)


# For create-new-trigger select.  Ordered for recognizability.
MOBILE_TRIGGER_TYPES = [('create', CreateMobileTriggerTemplate),
                        ('death', DeathMobileTriggerTemplate),
                        ('arrival', ArrivalMobileTriggerTemplate),
                        ('departure', DepartureMobileTriggerTemplate),
                        ('portal-in', PortalInTriggerTemplate),
                        ('portal-out', PortalOutTriggerTemplate),
                        ('perform-act', ActMobileTriggerTemplate)]

def getMobileTriggerType(trigger):
    triggerType = MOBILE_TRIGGER_TEMPLATES[trigger.__class__.__name__]
    triggerType = triggerType(trigger)
    return triggerType

def getMobileTriggerTemplate(byName):
    return dict(MOBILE_TRIGGER_TYPES)[byName]

def getMobileTriggerSheet(mobile):
    try: triggers = mobile.triggers
    except AttributeError:
        triggers = []

    return MobileTriggerSheet(triggers)

class MobileTriggerSheet(dict):
    ORDER = [('create', 'create', 'Create Mobile -- Run mobile lifecycle'),
             ('death', 'death', 'Slay Mobile -- Killed by opponent'),
             ('arrival', 'arrival', 'Arriving in Room'),
             ('departure', 'departure', 'Departing from Room'),
             ('portal-in', 'portalIn', 'Portal Exit Point'),
             ('portal-out', 'portalOut', 'Portal Entrance Point'),
             ('perform-act', 'performAct', 'Act() Messaging')]

    def __init__(self, triggers):
        for (type, name, title) in self.ORDER:
            self.install(triggers, type, name)

    def install(self, triggers, type, name = None):
        if name is None:
            name = type

        for t in self.search(triggers, type):
            self.setdefault(name, []).append(t)
            break
        else:
            t = getMobileTriggerTemplate(type)
            self[name] = [t.CreateEmpty()]

    def search(self, triggers, type):
        for t in triggers:
            if getMobileTriggerType(t).typeCode == type:
                yield t

    @property
    def iterator(self):
        for (type, name, title) in self.ORDER:
            yield dict(list = self[name],
                       title = title)


# Entity Verb Commands.
class VerbGroup(CmdDict):
    def match(self, command):
        try: reg = self[command]
        except KeyError:
            return

        return reg

def verbCommand(player, command, argstr):
    ch = player.avatar
    if ch is not None:
        # if hasattr(ch.room, 'verbs'):
        #     verb = ch.room.verbs.match(command)
        #     if verb is not None:
        #         program = "call(%r, %r, %r)" % (verb.method, command, argstr)


        # A verb is a command-based action in the interactive world.
        # Todo: how to integrate with evaluateCommand?
        if isYesValue(configuration.Interpreter.evaluate_verbs):
            from stuphmud.server.player.interfaces.code.girl import PlayerScript

            try: kwd = dict(program = player.session.adapter.handleCommand)
            except AttributeError:
                kwd = dict()

            return PlayerScript.evaluateVerb(player, ch, command, argstr, **kwd)


        # try: spatial = ch.spatial
        # except AttributeError: pass
        # else:
        #     spatial.interpretCommandArgs(player, command, argstr)

