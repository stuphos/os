# Debug/Devel Tools.
from _thread import start_new_thread as nth
from pdb import runcall
from stuphos.emulation.heartbeat import Heartbeat as CoreHeartbeat
from stuphmud import server as mud


class ControlledHeartbeat(CoreHeartbeat):
    import ph
    import builtins as control

    def __init__(self, core, *args, **kwd):
        Heartbeat.__init__(self, *args, **kwd)
        self.core = core

    @classmethod
    def install(self, *args, **kwd):
        if not self.isInstalled():
            ph.getBridgeModule().heartbeat = self(ph.getHeartbeat(), *args, **kwd)
            self._heartbeat_running = True
            nth(self.runHeartbeat, ())

    def uninstall(self):
        ph.getBridgeModule().heartbeat = self.core

    @classmethod
    def isInstalled(self):
        return issubclass(ph.getHeartbeat().__class__, self)

    _heartbeat_delay = 1.5
    def runHeartbeat(self):
        while self._heartbeat_running:
            self.pulse(0, 100) # !
            sleep(self._heartbeat_delay)

        print('heartbeat stopped')
        self.uninstall()

    # Control Points.
    def dispatchTask(self, *args, **kwd):
        if self.is_debugging:
            return pdb.runcall(self.core.dispatchTask, *args, **kwd)
        else:
            return self.core.dispatchTask(*args, **kwd)

    def stopControl(self):
        self._heartbeat_running = False

from game import Heartbeat as Engine, Game
from time import sleep
import ph

class Timeslice(Engine.Task):
    def __init__(self, delay):
        self.delay = delay
    def perform(self, engine):
        sleep(self.delay)

class Tool(Timeslice):
    DELAY = 0.5

    def __init__(self):
        Timeslice.__init__(self, self.DELAY)
        self.engine = Engine()
        self.engine += self
        self.engine += Game()

        from game import Console
        self.console = Console()
        self.console.avatar.level = 115
        mud.player.interpret(self.console)

        import __main__ as main
        main.go = self

        nth(self.engine.run, ())

    def perform(self, engine):
        ph.getHeartbeat().pulse(0, 100)
        Timeslice.perform(self, engine)

    def activate(self, engine):
        print('activating')
    def deactivate(self, engine):
        print('deactivating')
    def engine_start(self, engine):
        print('engine starting')
    def engine_stopped(self, engine):
        print('engine stopped')

    def doOneLine(self):
        self.engine.event += self.console.handleConsoleInput
