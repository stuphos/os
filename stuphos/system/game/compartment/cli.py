#!/usr/bin/python
# Copyright 2021 runphase.com .  All rights reserved.
#
import os
import sys
import pdb
import queue

from os.path import realpath, normpath, dirname

# from .system import *


# Front-End.
def buildCli(consoleBaseClass = None):
    # Do this dynamically -- import the core stuff only during core compartmentalize.
    global Console, Heartbeat, peer, mobile_instance, NanoText
    from game import Heartbeat, peer, mobile_instance, NanoText # XXX remove reliance on game

    import sys
    sys.__peer_shell_stdout = sys.stdout

    if consoleBaseClass is None:
        from stuphos.system.game.compartment.system import ConsoleBusiness as consoleBaseClass

    class Console(consoleBaseClass, peer, Heartbeat.Task):
        def __init_entity__(self, *args, **kwd):
            peer.__init_entity__(self) # conn = something containing network ref
            consoleBaseClass.__init_entity__(self, *args, **kwd)
            self.avatar = mobile_instance.create()

        def editString(self, string):
            string = NanoText(string)
            return consoleBaseClass.editString(self, string)

        class Nonconnection:
            def __init__(self, peer, network):
                self.peer = peer
                self.network = network

        def attachNetwork(self, network):
            self.conn = self.Nonconnection(self, network)

# Executable Script.
# ['mushclient_game_cli', '-m', 'H:\\StuphMUD\\lib\\python', '-C', '.mud-config.cfg', '-w', 'H:\\StuphMUD\\lib\\world', '--cascade', '-z', 'index.mini', '--libdata=H:\\StuphMUD\\lib\\python\\supplemental\\iibdata', '-p', '9876', '--headless', '-vsa']

def runCore(options, args, globalize = True,
            consoleBaseClass = None,
            initForCore = None):

    if options.mud_package and isinstance(options.mud_package, str):
        from game import registerRealPath
        registerRealPath(options.mud_package)

    # I don't like this here, but it can't be a part of Core because
    # of the complication of the world module being separate from the
    # mud package.  So even though the event bridge could be initialized
    # as part of the mud package domain, the framework implementation
    # requires that it be part of the game module domain.
    from game import installBridge
    installBridge()

    # Todo: Stitch these two calls together within the compartment.
    buildCli(consoleBaseClass)

    from stuphos.stuphlib import wldlib, dblib
    from stuphos import stuphlib

    from game import world, Core

    return Core((options, args),
                stuphlib, world,
                globalize = globalize,
                initForCore = initForCore,
                consoleClass = Console)


class PythonWinCompartment:
    class PyWinConsoleBusiness: # XXX :skip:: (ConsoleBusiness): so much for a base class.
        # Usage: console.startInteractiveHandler()
        def __init_entity__(self, *args, **kwd):
            ConsoleBusiness.__init_entity__(self, *args, **kwd)
            self.readQ = queue.Queue()
            self.leavingMode = False
            self.debugMode = False

            # Todo: formalize this definition, not here locally:
            #    sh = Interactive.Shell.New()
            #    sh.handleCommand = self.handlePyWinInteractiveShellCommand
            #
            #    def handlePyWinInteractiveShellCommand(self, line):
            #        self.readQ.put(line)
            #        return True

            from common.subsystem.pythonwin.ide import Interactive
            class PyWinInteractiveShell(Interactive.Shell):
                def handleCommand(this, line):
                    # How to escape..?
                    # Or, system.core.interactive.pythonInterpreter .runcode
                    #
                    # Implement a top-level command-interpreter here for
                    # escaping (self.leaveGameMode)
                    #
                    # Actually, just make this routine return False..!

                    self.readQ.put(line)
                    self.leavingMode = False

                    if self.debugMode:
                        from pywin.debugger import set_trace
                        set_trace()

                    if 1:
                        print()
                        self.handleConsoleInput()

                    return not self.leavingMode

            self.pyWinInteractiveShellClass = PyWinInteractiveShell

        def textout(self, text):
            # When used as withPeerHead entity.
            out = sys.stdout
            if out is self:
                out = sys.interactive.interpreter

            return out.write(text) # should this be returning value..?

        def page_string(self, string):
            # todo: open document template
            print(string)

        def editString(self, string):
            if callable(self.messenger):
                self.messenger(self, string)

        def startInteractiveHandler(self):
            self.pyWinInteractiveShellClass(system.core.interactive)
        enterGameMode = startInteractiveHandler

        def leaveGameMode(self):
            self.leavingMode = True

        def readConsoleInput(self):
            return self.readQ.get()

        def perform(self, engine):
            if 0:
                # The classic way is to do this within the event loop,
                # but that isn't inline with the GUI thread, so, make
                # the handleCommand method call the event.
                if not self.readQ.empty():
                    self.engine.event += self.handleConsoleInput

    def __init__(self, options_file):
        self.loadOptionsFile(options_file)
        self.recompartmentalize()

    def loadOptionsFile(self, options_file):
        (self.argv, self.paths, self.game_module) = self.parseOptionsFile(options_file)
    def loadRunCore(self, game_module):
        return __import__(game_module, globals(), locals(), ['']).runCore

    def parseOptionsFile(self, filename):
        # Prepare (options, args) output from file.
        game_module = None
        argv = []
        paths = []
        for line in open(filename):
            line = line.strip()
            if line and line[0] in '#;':
                continue # Comments.

            colon = line.find(':')
            if colon > 0:
                option = line[:colon]
                value = line[colon + 1:].lstrip()

                if option in ('switches', 'switch'):
                    argv.append('-' + value)
                elif option == 'toggle':
                    argv.append('--' + value)
                elif option == 'system-path':
                    if value not in paths:
                        paths.append(value)
                elif option == 'game-module':
                    game_module = value
                elif len(option) == 1:
                    argv.append('-' + option)
                    argv.append(value)
                else:
                    argv.append('--' + option)
                    argv.append(value)

        return (argv, paths, game_module)

    def recompartmentalize(self):
        # Remove this directory from the system path.
        this_path = realpath(normpath(dirname(__file__)))
        if this_path in sys.path:
            sys.path.remove(this_path)

        # Add in new directories.
        for path in self.paths:
            if path not in sys.path:
                sys.path.append(path)

        # Load the game module runCore routine.
        self.runCore = self.loadRunCore(self.game_module)

        # Reparse the assembled command line.
        from game import parseCmdln
        (options, args) = parseCmdln(self.argv)

        # Don't let Core do async -- we'll handle that.
        options.asynchronous = False
        self.options = options
        self.args = args

    def Setup(self, core):
        #: Compartmentalize within the mud core:

        # Override the default system debug decorator.
        ##    from mud.tools import registerBuiltin
        ##    self.installPywinDebugger(registerBuiltin)

        # Register onShutdown event -- to quit application last!
        from stuphos import on
        @on.shutdownGame.last
        def exitApp():
            self.thisApp.OnQuit()

        # Install Console Class.
        ##    @runtime.api('Game::Support::Console')
        ##    @apply
        ##    class ConsoleAPI:
        ##        @breakOn
        ##        def create(self, *args, **kwd):
        ##            from game.cli import Console
        ##            return Console.create(*args, **kwd)

    def installPywinDebugger(self, registerBuiltin):
        # Declare the pywin-debug decorator.
        def pywinBreakOn(function):
            from pywin.debugger import runcall
            def pywinDebugCall(*args, **kwd):
                return self.runInGUIFor(runcall, function, *args, **kwd)

            return pywinDebugCall

        registerBuiltin(pywinBreakOn, 'breakOn')

    def _getCoreBootstrap(self):
        def resumeCoreBootstrap():
            # Debugging bootstrap:
            # installDefaultDebugger(defaultRegisterBuiltin)
            # self.installPywinDebugger(defaultRegisterBuiltin)

            from _thread import start_new_thread as nth
            nth(self.runCore, (self.options, self.args),
                dict(consoleBaseClass = self.PyWinConsoleBusiness,
                     initForCore = self.Setup))

        return resumeCoreBootstrap

    def Run(self):
        sys.argv = ['/new']
        from pywin.framework import intpyapp

        thisApp = self.thisApp = intpyapp.thisApp

        thisApp.InitInstance()
        self.runInGUI(self._getCoreBootstrap())
        thisApp.Run()

    def runInGUI(self, function, *args, **kwd):
        def guiCompartment(handler, count):
            self.thisApp.DeleteIdleHandler(guiCompartment)
            function(*args, **kwd)

        self.thisApp.AddIdleHandler(guiCompartment)

    def runInGUIFor(self, function, *args, **kwd):
        waitQ = queue.Queue()
        def guiCompartment(handler, count):
            self.thisApp.DeleteIdleHandler(guiCompartment)
            waitQ.put(function(*args, **kwd))

        self.thisApp.AddIdleHandler(guiCompartment)
        return waitQ.get()

    # Embed in already-running PythonWin.
    @classmethod
    def EmbedFromOptions(self, xxx_todo_changeme, asynchronous = True):
        (options, args) = xxx_todo_changeme
        kwd = dict(consoleBaseClass = self.PyWinConsoleBusiness)

        if asynchronous:
            from _thread import start_new_thread as nth
            return nth(runCore, (options, args), kwd)

        return runCore((options, args), **kwd)

    @classmethod
    def EmbedFromCmdln(self, cmdln, *args, **kwd):
        if isinstance(cmdln, str): # boxing
            from shlex import split as splitShlex
            cmdln = splitShlex(cmdln)

        from game import parseCmdln
        return self.EmbedFromOptions(parseCmdln(cmdln), *args, **kwd)

def PyWinEmbeddedMain():
    cmdln = pythonWin.property['Startup StuphMUD Command Line']

    if cmdln:
        PythonWinCompartment.EmbedFromCmdln(cmdln)


try: from common.runtime.structural.document import Submapping
except ImportError: pass
else:
    from common.runtime import Object

    class wmc:
        class Factory(Submapping):
            class wmcStuphOSConfiguration(Object):
                '''
                Westmetal Configuration::
                    stuphos = game.cli.wmc

                stuphos:
                    cmdln(stuphos$configuration):
                        game-configuration: '{support}(".mud.config")'
                        data-folder: '{support}.folder.lib'

                        # no-world: true
                        world-folder: '{support}.folder.lib.world'
                        load-world-cascade: true
                        zone-index: 'index.mini'

                        port: 6112
                        mud-package: '{support}.folder.lib.python'

                        interactive: false
                        asynchronous: true
                        debug: false
                        # verbose: 2

                        implementor: true
                        headless: false

                    init(python$module)::
                        builtin(bootStuph = container.cmdln)

                '''

                def __init__(self, name, value, **kwd):
                    self.gameConfiguration = value.get('game-configuration')
                    self.dataFolder = value.get('data-folder')

                    self.noWorld = value.get('no-world')
                    self.worldFolder = value.get('world-folder')
                    self.loadWorldCascade = value.get('load-world-cascade')
                    self.zoneIndex = value.get('zone-index')

                    self.port = value.get('port')
                    self.mudPackage = value.get('mud-package')

                    self.interactive = value.get('interactive')
                    self.asynchronous = value.get('asynchronous')
                    self.debug = value.get('debug')
                    self.verbose = value.get('verbose')

                    self.implementor = value.get('implementor')
                    self.headless = value.get('headless')

                def prepareCmdln(self):
                    # Todo: translate contained structural configuration
                    # to expected cli-based options.

                    ##    ('-w', '--world-dir')
                    ##    ('-z', '--zone-index', '--index')
                    ##    ('-i', '--interactive', action = 'store_true')
                    ##    ('-a', '--async', action = 'store_true')
                    ##    ('-W', '--cascade', '--load-world', action = 'store_true')
                    ##    ('-C', '--config-file', '--config', '--game-config')
                    ##    ('-g', '--debug', action = 'count', default = 0)
                    ##    ('-n', '--no-world', action = 'store_true')
                    ##    ('-p', '--port', type = int)
                    ##    ('-m', '--mud-package', '--mud')
                    ##    ('-s', '--supreme', action = 'store_true')
                    ##    ('-L', '--data-dir', '--lib-dir')
                    ##    ('--libdata')
                    ##    ('-v', '--verbose', action = 'count', default = 0)
                    ##    ('--headless', '--no-console', action = 'store_true')

                    return (dict(),
                            ())

                def embed(self, *args, **kwd):
                    (cmdlnOptions, cmdlnArgs) = self.prepareCmdln()
                    return PythonWinCompartment.EmbedFromOptions \
                           ((cmdlnOptions, cmdlnArgs),
                            *args, **kwd)

                __call__ = boot = embed

            configuration = wmcStuphOSConfiguration


##    def defaultRegisterBuiltin(function, name):
##        setattr(__builtins__, name, function)
##    def installDefaultDebugger(registerFunction):
##        from pdb import set_trace
##        def breakOn(function):
##            def debugCall(*args, **kwd):
##                set_trace()
##                return function(*args, **kwd)
##
##            return debugCall
##        registerFunction(breakOn, 'breakOn')

# Todo: When run from the support (development) directory,
# path will be relative.  Can we do this kind of thing sanely?
##    def qualifyModulePath(module):
##        p = module.__path__
##        p[0] = abspath(p[0])
##
##    qualifyModulePath(__import__('game'))
# And is it really going to be effective?

def main(argv = None):
    # Application compartment.
    from game import getCmdln, parseCmdln

    argv = getCmdln(argv)
    if len(argv) == 3 and argv[1] == '/pywin':
        # Host the MUD server asynchronously while running pywin in main.
        pywin = PythonWinCompartment(argv[2])
        pywin.Run()
    else:
        return runCore(*parseCmdln(argv))

if __name__ == '__main__':
    main()
else:
    buildCli()
