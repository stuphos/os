# Game Core Replacement
# (C) 2021 runphase.com .  All rights reserved.
#
from stuphos.etc.tools import isYesValue, isNoValue

from . import Heartbeat, Game
from .db import Database

from time import time as getSystemTime
from pdb import runcall, set_trace as enter_debugger
from os import getpid, getenv, environ as os_environ
from queue import Empty
import sys

# System Database.
class Local(Database):
    sys = sys

    def __init__(self, *args, **kwd):
        # Obselete, just configure packages.
        # try: libdata = kwd['libdata']
        # except KeyError: pass
        # else:
        #     del kwd['libdata']
        #     if libdata not in self.sys.path:
        #         self.sys.path.append(libdata)

        Database.__init__(self, *args, **kwd)

    def activate(self, engine):
        engine.db = self
        self.boot()

# Application.
def freeClient(network, port):
    print('Opening Loopback Connection:', port)
    network.openConnection(('localhost', port))

def parseArgvToKwd(args):
    kwd = dict()
    for a in args:
        (name, value) = a.split('=', 1)
        kwd[name] = value

    return kwd

class Core(Heartbeat):
    class Pulse(Heartbeat.Task):
        # This could go in system.heartbeat
        from time import time as getTimeInSeconds, sleep
        getTimeInSeconds = staticmethod(getTimeInSeconds)
        sleep = staticmethod(sleep)

        OPT_MSEC = 100 # Milliseconds per timeslice.

        def getRemainingTimeslice(self, duration):
            return duration % self.OPT_MSEC # XXX what if duration > OPT_MSEC??
        def sleepForMilliseconds(self, duration):
            duration /= 1000
            # duration /= 10 # seems more accurate, but wtf?
            # print duration
            self.sleep(duration) # / 1000) # XXX :skip: don't divide by 1000!?
        def getTimeInMilliseconds(self):
            return self.getTimeInSeconds() * 1000

        def __init__(self, heartbeat):
            self.heartbeat = heartbeat

        def perform(self, engine):
            start = self.getTimeInMilliseconds()

            # import pdb; pdb.set_trace()
            # pdb.runcall(self.heartbeat.pulse, 0, 100)

            # import time, datetime
            # print datetime.datetime.fromtimestamp(time.time())

            try:
                self.heartbeat.pulse(0, 100, blocking = engine.blockingQueue)

                duration = self.getTimeInMilliseconds() - start
                remaining = self.getRemainingTimeslice(duration)
                if remaining:
                    self.sleepForMilliseconds(remaining)

            except Empty:
                # What are we catching if not an errant exception coming from
                # pulse.  This is able to clear the error which seems to not
                # be happening in the emulated machine.  It is unclear if this
                # catch will work if not for the sleep call that might raise
                # the pending Empty exception.
                pass

            except KeyboardInterrupt:
                @engine.event.call
                def done():
                    # debugOn()
                    engine.stop()
                    StuphMUD.ShutdownGame()
                    # gc.collect(); os.kill(signal.SIGTERM, os.getpid())

            except:
                from traceback import print_exc
                print_exc()

    def __init__(self, optArgs,
                 stuphlib, worldModule,
                 globalize = False,
                 initForCore = None,
                 consoleClass = None):

        (options, args) = optArgs

        if globalize:
            # Hmm, done before superclass constructor.
            global instance
            import builtins as builtin
            instance = builtin.core = self

        # print(os_environ.get('here'))
        os_environ.setdefault('here', '.')

        # Configure for continuous metal.
        if options.fast_vm:
            timeout = None
        else:
            # Or blocking game queue.
            timeout = options.timeout
            if not timeout: # If not timeout is specified: burnout!
                timeout = False


        Heartbeat.__init__(self)
        self.cmdln = dict(options = options, args = args)

        # Configure against options.
        try: import readline
        except ImportError: pass

        if options.debug > 3:
            enter_debugger()

        if options.runpid:
            with open(getenv('RUNPID_FILENAME', 'runpid'), 'w+b') as o:
                o.write(str(getpid()))


        if options.local:
            # Bespoke configuration.
            # debugOn()
            options.agent_system = options.local
            options.services.insert(0, 'facility.agentsystem=ph.interpreter.mental.library.model.service_localAgentSystem')


        self.consoleClass = consoleClass

        # Combine conditionally.
        self.headless = options.headless
        self.headed = options.headed

        if options.headed or not options.headless:
            self._forceAlive = False

            if consoleClass is not None:
                console = consoleClass.create(debug = options.debug) # interactive = options.interactive
                self += console

                if options.supreme:
                    console.avatar.level = console.avatar.LVL_SUPREME

                    # Enable 'examine' command.
                    from world.player import EnableEMHW
                    EnableEMHW() # Emergency Mode Holographic Wizard

                if options.admin_name:
                    console.avatar.name = options.admin_name
                # if options.enter_game:
                #     from stuphos.system.api import world
                #     console.avatar.room = world.room(3001)

            else:
                console = None

        self += Game(timeout = timeout)

        if options.port:
            from stuphos.system.network import MotherSocket
            network = MotherSocket(options.port)
            self += network
            # self.event.call(freeClient, self.network, options.port)

            from world import player
            player.emergeInternalPeer = network.emergeInternalPeer

            if options.headed or not options.headless:
                console.attachNetwork(network)


        # Before this there is no configuration.
        if options.debug > 2:
            runcall(self.bootMudStart, options, stuphlib, worldModule)
        else:
            self.bootMudStart(options, stuphlib, worldModule)


        # Now 'configuration' builtin is available.


        # worldModule.player.EnableEMHW
        from world.player import EnableEMHW

        if isYesValue(configuration.Interpreter.emhw): # or options.emhw:
            EnableEMHW()

        if options.headed or not options.headless:
            def ehwm(console):
                # Console might be None. (?)
                if console is not None:
                    console.state = 'Playing' # 'Shell'

                    if options.admin_command:
                        # todo: do this after enter game?
                        console.input = options.admin_command
                        # if options.single_command_exit:
                        #     console.input = 'exit'

                    StuphMUD.GreetPlayer(console)
                    StuphMUD.NewIncomingPeer(console)

                    try: enterGameInRoom(console, console.avatar)
                    except ValueError as e:
                        print(f'[EHWM] Enter Game: {e}')

            self.event.call(ehwm, console)

        if options.data_dir:
            from os import chdir
            print('Changing to data directory: %s' % options.data_dir)
            chdir(options.data_dir)

        if callable(initForCore):
            # Let calling context initialize, now that most of the
            # core is booted, before the main process is run.
            initForCore(self)


        if options.file:
            # XXX :skip: The file argument should be accessible with natives
            # as well as the runModuleScript/open file routines such
            # that the AgentSystem:initialization script can decide
            # when to run test console code (not very useful in a server).

            from ph.interpreter.mental import runModuleScript
            if options.file == '--':
                script = sys.stdin.read()
            else:
                with open(options.file) as o:
                    script = o.read()

            def boot_runModuleScript():
                runModuleScript(script, programmer = options.admin_name,
                                tracing = options.admin_trace,
                                tokenize = options.parser_tokenize,
                                args = args[1:])

                # print('running')

            self._boot_runModuleScript = boot_runModuleScript

        if options.admin_script:
            from stuphos.runtime.architecture.lookup import LookupObject
            adminScript = LookupObject(options.admin_script)
            adminScript(**parseArgvToKwd(options.admin_script_args))


        # How to run 'quick' command mode:
        # --network=false --no-init -dn --blocking=0
        #
        # -dn --no-init \
        #   -S Management:embedded-webserver=false \
        #   -S Management:session-adapter=false \
        #   -S XMLRPC:off=on \
        #   --blocking=0 \
        #   -f test-inline-2.ela


        self.optimisticTermination = not options.asynchronous and \
            (bool(options.file) or bool(options.admin_command))

        # self._forceAlive = not self.optimisticTermination


        # The engine will be run another way.  Just return Core.
        if not options.no_run_engine:
            self.blockingQueue = self.cmdln['options'].blocking

            if options.debug > 1:
                runcall(self.run) # Todo: ShutdownGame
            elif options.asynchronous:
                from _thread import start_new_thread as nth
                nth(self.run, ()) # Todo: ShutdownGame
            else:
                # print('running')

                try: self.run(optimisticTermination = self.optimisticTermination)
                except KeyboardInterrupt:
                    print()

                # print('done')

                StuphMUD.ShutdownGame()
                # system.core.unreachable = True

    # @property
    # def blockingQueue(self):
    #     # Todo: if console is enabled, do not block!
    #     return self.cmdln['options'].blocking

    def isNetworkEnabled(self):
        # debugOn()
        network = self.cmdln['options'].network
        return network is None or not isNoValue(network)

    def resetWorldOption(self, options):
        if isYesValue(configuration.World.reset_on_boot):
            return True

        return options.reset_world

    def bootMudStart(self, options, stuphlib, worldModule):
        # Initialize MUD Package.
        import stuphos

        stuphos.bootStart(options.config_file,
            options.set_option, core = self) # runtime.

        # Complete MUD Boot Cycle.
        self.bootStartTime = getSystemTime()

        if not self.cmdln['options'].fast_vm:
            # Install timing driver.
            import stuphos

            try: self += self.Pulse(stuphos.getHeartbeat())
            except AttributeError as e:
                self.pulseInstallFailure('bootMudComplete', e)


        def _bootMudStart_loadWorld():
            return self.loadWorld(options, stuphlib, worldModule)

        self._bootMudStart_loadWorld = _bootMudStart_loadWorld

    # _bootMudStart_loadWorld = None

    def loadWorld(self, options, stuphlib, worldModule):
        if not options.no_world:
            self.event.call(self.bootWorld, options, stuphlib, worldModule)

        self.event += self.worldResetStart

        if not options.no_world and self.resetWorldOption(options):
            self.event.call(self.resetWorld)

        self.event += self.worldResetComplete

        self.event += self.bootMudComplete

    def bootMudComplete(self):
        import stuphos
        elapsed = getSystemTime() - self.bootStartTime
        stuphos.bootComplete((elapsed / 1000, elapsed % 1000))

        if self.cmdln['options'].fast_vm:
            from ..metal import vm
            self.fastVM = vm()
            nth(self.fastVM)

        # else:

            # If components.system.core.Core construction fails
            #     to bootStart because the components.runtime.core
            #     fails, then it doesn't not fail the system core
            #     construction, it just causes the runtime.bootStart
            #     to return None (so no bridge...) 

            #     This means that later functionality may fail to
            #     load, for example, the compartmental framework
            #     heartbeat driver activated at the end of the
            #     boot protocol.

            #     Really what this means is that the boot start
            #     shouldn't fail where the boot complete continues,
            #     except that as a discrete and specific failure,
            #     a non-existence bridge should indicate no heartbeat
            #     module, and thus an alternative pulse activation.

            #         But to do this means that the core logics need
            #         to recognize and apply state.


    def pulseInstallFailure(self, where, e):
        what = configuration.MUD.on_pulse_install_failure or 'shutdown'
        print(f'{where}: {e} (resolving as {what})') # No need to print the traceback.

        if what == 'debug':
            debugOn()
            self.stop()

        elif what == 'debug-continue':
            debugOn()

        elif what == 'shutdown':
            self.stop()

        elif what == 'ignore':
            return

        else:
            print(f'Not sure what to do with configuration[MUD:on_pulse_install_failure]: {what}')

        print('Timing driver failed to install: engine may over-consume processing resource.')


    # def initConsole(self, console):
    #     from stuphmud.server.player import interpret
    #     interpret(console)

    def bootWorld(self, options, stuphlib, worldModule):
        if options.world_dir:
            index = 'index' if options.full_world else options.zone_index

            self += Local(stuphlib, worldModule,
                          options.world_dir, index,
                          cascade = options.cascade,
                          verbose = options.verbose)
                          # libdata = options.libdata)

    def resetWorld(self):
        return self.db.resetWorld(self, forceAll = True)

    def worldResetStart(self):
        StuphMUD.StartWorldReset()
    def worldResetComplete(self):
        # debugOn()
        StuphMUD.CompleteWorldReset()


def loadIntoRoom(peer, actor, room):
    if room is not None:
        actor.room = room
        from stuphos.system.game.namespace import lookAtRoom # import shelter
        lookAtRoom(actor, peer, room)

def enterGameInRoom(peer, actor):
    from stuphmud.server.player import getFirstValidRoom, getPlayerLoadRooms
    loadIntoRoom(peer, actor, getFirstValidRoom(getPlayerLoadRooms(actor)))
    StuphMUD.EnterGame(peer, actor)

    # from stuphmud.server.player import enterGame
    # enterGame(peer, actor)


# System Core Bridged Events.
StuphMUD.ShutdownGame = 'shutdownGame'

StuphMUD.StartWorldReset = 'resetStart'
StuphMUD.CompleteWorldReset = 'resetComplete'

StuphMUD.StartZoneReset = 'startZoneReset'
StuphMUD.CompleteZoneReset = 'completeZoneReset'

StuphMUD.MobileFromRoom = 'removeMobileFromRoom'
StuphMUD.MobileToRoom = 'putMobileInRoom'

