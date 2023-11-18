# Note: this is not an an interface to the operating system, this is a system in itself
# that represents a hosting compartment for the application.  (It is used by framework).

# An example a pure python command-line bootstrap:
# --
# def runCore(argv = None):
#     from stuphos.system.core import Core
#     from stuphos.system.cli import getCmdln

#     # These need to be provided...
#     # from stuphos import stuphlib
#     # from game import world

#     # But only for world-booting purposes which don't exist without a directory:
#     # def bootWorld(self, options, stuphlib, worldModule):
#     #     if options.world_dir:

#     stuphlib = world = None

#     # Run application -- might want to provide at least the headless option.
#     Core(getCmdln(argv),
#          stuphlib, world,
#          globalize = True)


# Aspects -- this is game-support, not the actual mud package heartbeat.
__all__ = ['Heartbeat', 'Game', 'mudlog', 'core']

class Heartbeat:
    class Task:
        def perform(self, engine):
            pass

        # Task-Specific.
        def activate(self, engine):
            pass
        def deactivate(self, engine):
            pass

        # Engine-Specific.
        def engine_started(self, engine):
            pass
        def engine_stopped(self, engine):
            pass

    def __init__(self):
        self.tasks = []

    def run(self, optimisticTermination = False):
        # Game-loop.
        # time (echo|./mc -dn --network=false --no-init -f --)
        try:
            self.start()
            self.perform_start()

            while self.is_running():
                # debugOn()
                if optimisticTermination and not self.alive():
                    # performance decision -- END
                    # self.blockingQueue = 0
                    self.stop()

                self.perform_cycle()

        finally:
            self.perform_stop()

    def perform_cycle(self):
        self.dispatch_operation('perform')

    # Task Interface
    def dispatch_operation(self, name):
        for task in self.tasks:
            op = getattr(task, name, None)
            if callable(op):
                # print("Dispatching '%s' on %r" % (name, task))
                op(self)

    def is_running(self):
        return getattr(self, '_running_state', False)
    def set_running(self, state = True):
        # debugOn()
        previous_state = self.is_running()
        state = bool(state)
        setattr(self, '_running_state', state)

    def perform_start(self):
        self.dispatch_operation('engine_started')
    def perform_stop(self):
        self.dispatch_operation('engine_stopped')

    def start(self):
        self.set_running(True)
    def stop(self):
        self.set_running(False)

    # Just never exits...
    _forceAlive = True

    def alive(self):
        if bool(self.tasks):
            # XXX -f doesn't put osCommand in vm.tasks before this happens...
            if getattr(self, '_forceAlive', False):
                return True

            from world import heartbeat as vm
            for x in vm.tasks:
                return True

        return False

    def activate(self, task):
        if task not in self.tasks:
            self.tasks.append(task)
            task.activate(self)
        return self
    def deactivate(self, task):
        if task in self.tasks:
            self.tasks.remove(task)
            task.deactivate(self)
        return self

    __iadd__ = activate
    __isub__ = deactivate

class Game(Heartbeat.Task):
    # Internal.
    import queue
    import traceback

    # System Task -- Event Queue
    def __init__(self, timeout):
        self.event_q = self.queue.Queue()
        self.timeout = timeout

    def activate(self, engine):
        engine.event = self

    def call(self, event, *params, **kwd):
        self.event_q.put((event, params, kwd))

    def __iadd__(self, event):
        self.call(event)
        return self

    class _exitClass(SystemExit):
        pass

    _exitClasses = (_exitClass,)

    def perform(self, engine):
        timeout = self.timeout

        while True:
            if timeout is not False:
                (event, params, kwd) = self.event_q.get(timeout)
            else:
                try: (event, params, kwd) = self.event_q.get_nowait()
                except self.queue.Empty:
                    timeout = self.getDefaultTimeout()
                    if not timeout:
                        break

                    continue

            try: event(*params, **kwd)
            except self._exitClasses as e:
                raise e

            except SystemExit:
                break

            except: # Exception as e:
                # Soft Fail.
                self.traceback.print_exc()

    def getDefaultTimeout(self):
        return False # 0.1

class Interpreter(Heartbeat.Task):
    # Command Dispatch.
    pass

class ManualDelay(Heartbeat.Task):
	def __init__(self, core):
		self.ev = Event()
		core += self
		core.switch = self

	def perform(self, engine):
		print('Waiting on', self.ev, '...')
		self.ev.wait()
		print('Done waiting on ', self.ev, '.')

	def signal(self):
		print('Sending signal to', self.en, '...')
		self.ev.set()

	__call__ = signal

class EventBridge:
    # A similar, unused symbol is defined in runtime/events.
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
            return 'Calling: %r' % self.name
        __str__ = __repr__

    def __setattr__(self, name, value):
        self.__dict__[name] = self.Calling(value)

# The default bridge.  Application may override this.
import builtins as builtin
if not hasattr(builtin, 'StuphMUD'):
    builtin.StuphMUD = EventBridge()

# Todo: Export this constant.
LVL_IMMORT = 106

def mudlog(message, level = LVL_IMMORT, typeName = "Normal"):
    from world.player import players

    message = str(message)
    level = int(level)
    typeName = typeName and str(typeName) or "Normal"

    # Todo: Colorization.
    msg = '[ %s ]' % message
    for peer in players():
        # Todo: If not writing/mailing/creating and is playing.
        # Todo: Type-level check.
        if peer.avatar is not None and level <= peer.avatar.level:
            print(msg, file=peer)

def boot_time():
    from builtins import core
    return core.bootStartTime
