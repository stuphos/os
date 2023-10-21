# Now a ph component that provides a runtime configuration.
#
# Separate from the framework/compartment core, used in an embedding context.
# Also separate from the (legacy) mud package that resides now in application.server.
#
# Copyright 2022 runphase.com .  All rights reserved.
# --

# MUD Runtime Core.
#    mud.runtime.core provides:
#       * access to the event bridge
#       * programming the virtual machine
#       * configuration access
#       * boot procedure
#
# This should probably be called 'bootstrap' (the runtime is the core)
from stuphos.runtime import BINDINGS, EVENT_NAMES, loadOnto, Binding
from stuphos.etc.tools.logs import *

from stuphos.management.config import PackageManager, getParentPath, joinpath
from stuphos.management.config import getStandardPath, loadConfig

from stuphos.runtime.registry import getObject as getRegistryObject
from stuphos.runtime.registry import delObject as deleteRegistryObject
from stuphos.runtime.registry import RegistryNotInstalled

from stuphos.runtime.plugins import installPlugins

from stuphos.etc.tools import isYesValue, isNoValue

__version__ = '0.9.1'


def getBridgeModule():
    ##    # First code to load the game module.
    ##    from pdb import run
    ##    run('from game import bridgeModule')

    try: from stuphos.system.api import game
    except ImportError:
        from stuphos.system import game

    return game.bridgeModule()

def callEventBridge(name, *args, **kwd):
    try: event = getattr(getBridgeModule(), name)
    except AttributeError: pass
    else:
        if callable(event):
            return event(*args, **kwd)

def getMudModule():
    from stuphmud import server as mud
    return mud

def getHeartbeat():
    return getBridgeModule().heartbeat

def enqueueHeartbeatTask(*args, **kwd):
    return getHeartbeat().enqueueHeartbeatTask(*args, **kwd)
def enqueueHeartbeatTaskDefault(*args, **kwd):
    return getHeartbeat().enqueueHeartbeatTaskDefault(*args, **kwd)
def deferredTask(*args, **kwd):
    # print(f'deferring task to heartbeat... {args}')
    return getHeartbeat().deferredTask(*args, **kwd)

enqueue = enqueueHeartbeatTask
executeInline = deferredTask

def inline(function):
    # Decorator
    def inlineWrapper(*args, **kwd):
        # print(f'inlining... {args}')
        return executeInline(function, *args, **kwd)

    try: inlineWrapper.__name__ = function.__name__
    except AttributeError: pass

    try: inlineWrapper.__doc__ = function.__doc__
    except AttributeError: pass

    return inlineWrapper

def invokeTimeoutForHeartbeat(timeout, function, *args, **kwd):
    return getHeartbeat().invokeTimeoutForHeartbeat(timeout, function, *args, **kwd)
def invokeTimeout(timeout, function, *args, **kwd):
    return getHeartbeat().invokeTimeout(timeout, function, *args, **kwd)

CONFIG_OBJECT_NAME = 'MUD::Configuration'
CONFIG_FILE = getStandardPath('etc', 'config.cfg')

def _createMUDConfig():
    from ...etc.tools import registerBuiltin
    o = loadConfig(CONFIG_FILE)
    registerBuiltin(o.addressor, 'configuration')
    registerBuiltin(o.addressorTruth, 'configurationTruth')
    registerBuiltin(runtime.MUD.Configuration, 'mudConfig')
    return o

def getConfigObject():
    # return mudConfig(loadConfig, CONFIG_FILE)
    return getRegistryObject(CONFIG_OBJECT_NAME,
                             create = _createMUDConfig)

def deleteConfig():
    # del runtime[mudConfig]
    return deleteRegistryObject(CONFIG_OBJECT_NAME)

def reloadConfigFile(filename, setOptions = False):
    global CONFIG_FILE
    CONFIG_FILE = filename
    deleteConfig()

    # debugOn()
    if setOptions is not False:
        # Load immediately and override with core cmdline opts.
        getConfigObject().loadSetOptionList(setOptions)


def getConfig(name, section = 'MUD'):
    try: return getConfigObject().get(name, section = section)
    except RegistryNotInstalled: pass
def getSection(section = 'MUD'):
    try: return getConfigObject().getSection(section)
    except RegistryNotInstalled: pass


# Boot Procedure.
SITE_PATH = getParentPath(__file__, 5) # XXX ??? (besides its configurable)
COMPONENTS_FILE = 'components.pth'

# EASY_SITE_PATH = joinpath(SITE_PATH, 'packages/third-party')
# EASY_INSTALL_FILE = 'easy-install.pth'

def getDefaultComponentsPath():
    return SITE_PATH, COMPONENTS_FILE

def installSite():
    # Manually search non-standard paths for .pth files.
    path = getConfig('components')
    if path is None:
        (path, file) = getDefaultComponentsPath()
    else:
        from os import sep
        i = path.rfind(sep)
        if i < 0:
            file = path
            path = '' # '.'
        else:
            file = path[i+1:]
            path = path[:i]

    PackageManager(path, file).install()
    # PackageManager(EASY_SITE_PATH, EASY_INSTALL_FILE).install()

def installBridge():
    bridgeModule = getBridgeModule()
    thisModule = getMudModule()

    # from mud.runtime import declare, DeclareEvent
    # declare(bridgeModule, EVENTS)
    loadOnto(BINDINGS, bridgeModule)

    thisModule.on = Binding(bridgeModule)
    thisModule.core = Binding(thisModule)

    ##    class bootStart(DeclareEvent):
    ##        Module = thisModule
    ##    class bootComplete(DeclareEvent):
    ##        Module = thisModule

    return bridgeModule

def installHost():
    from socket import error
    from errno import EADDRINUSE

    disabling = [EADDRINUSE]

    # error: [Errno 10013] An attempt was made to access a socket in a way forbidden by its access permissions
    try: from errno import WSAEACCES
    except ImportError: pass
    else: disabling.append(WSAEACCES)

    try:
        from stuphos.kernel import getHost
        from stuphos.kernel import NotConfigured
        try: getHost(create = True).start()
        except NotConfigured:
            logWarning('XMLRPC disabled.')

    except error as e:
        if e.args[0] not in disabling:
            from stuphos.etc.tools import reraiseSystemException
            reraiseSystemException()

        logWarning('Host port is in use -- XMLRPC disabled.  Please reconfigure!')

    except Exception:
        logException(traceback = True)


def installEnviron():
    # Configure the system/shell environment.
    from os import environ
    # debugOn()
    envCfg = getSection('Environment')
    for name in envCfg.options():
        (name, value) = envCfg.get(name).split('=', 1)
        environ[name] = value


def installSystemComponents():
    # Install system path components.
    systemComp = getSection('SystemComponents')
    systemPaths = []

    if systemComp is not None:
        for option in systemComp.options():
            if option == 'system-path' or \
               option.startswith('system-path.'):
                systemPaths.append(systemComp.get(option))

    from sys import path as syspathCore
    for path in systemPaths:
        if path not in syspathCore:
            syspathCore.append(path)

def installSystemPackages():
    systemPkgs = getSection('SystemPackages')
    packages = []

    if systemPkgs is not None:
        for option in systemPkgs.options():
            if option == 'package' or \
               option.startswith('package.'):
                pkg = systemPkgs.get(option)
                # todo: filter for duplicate packages?
                packages.append((option, pkg))

    for (n, pkg) in sorted(packages, key = lambda a_b: a_b[0]):
        # logOperation(f'importing {n}: {pkg}')

        try: __import__(pkg)
        except SyntaxError as e:
            print(f'[syntax error] {pkg}: {e}')

        except: logException(traceback = True)


def installJournal():
    try:
        from stuphos.management import syslog
        # debugOn()
        syslog.Journal.get(create = True)
    except:
        logException(traceback = True)


def installServices(thisModule):
    # Install VM
    # Install system paths
    # Install environ config
    # Install XMLRPC host service
    # Install journal
    # Import system modules (config)
    # Install Management modules
    # Install logging service

    # Create binding to bridge module.

    # Todo: actually make this a registered COM object!
    if not isYesValue(configuration.VM.disabled):
        try: from stuphos.kernel import Machine, Native
        except ImportError as e: # e.path
            logOperation(f'[services$install] {e}: {e.path}')
            logException(traceback = True)
        else:
            bridge = getBridgeModule()
            vm = bridge.heartbeat = Machine()

            runtime.System.Network.Core(lambda:thisModule)
            runtime.System.Bridge(lambda:bridge)
            runtime.System.Engine(lambda:bridge.heartbeat)

            thisModule.on.shutdownGame(vm.onShutdownGame)

            debug = configuration.AgentSystem.debug_natives

            if isYesValue(debug):
                Native._tracing = True
            elif debug is not None and isNoValue(debug):
                Native._tracing = False


    # runtime.components = registry.Access(runtime, 'registry')
    # runtime.builtin = builtin
    # builtin.runtime = runtime
    # runtime.system = builtin.system
    #     # runtime.system.core

    # runtime.core = runtime.system.module.stuphos ?
    #     runtime.core.mud = runtime.system.module.stuphos ?
    #     runtime.core.game = runtime.system.module.game
    #     runtime.core.world = runtime.system.module.world

    # from ph import psOpGameVsz
    # import builtins
    # builtins.psOpGameVsz = psOpGameVsz
    # import op
    # print(f'[vsz] pre-services {psOpGameVsz()}')

    # Pre-Management Set:
    installSystemComponents()
    installEnviron()
    installHost()

    # print(f'[vsz] post-host {psOpGameVsz()}') # +74Mb

    installJournal()

    # print(f'[vsz] post-journal {psOpGameVsz()}') # +74Mb

    # Note that this relies on core components working.
    # But the rest of the runtime should rely on system
    # packages, not the other way around.
    installSystemPackages()

    # print(f'[vsz] post-packages {psOpGameVsz()}')


    try:
        from stuphos.kernel import MachineCore
        MachineCore.systemCore()
    except:
        logException(traceback = True)


    from stuphos.etc.tools.logs import logger
    endpoint = getConfig('log-endpoint', 'MUD')
    receiver = logger._nullreceiver
    if endpoint:
        from xmlrpclib import ServerProxy
        receiver = ServerProxy(endpoint).logging.receive

    from ...etc.tools import registerBuiltin
    registerBuiltin(logger(receiver), 'log')


    try: from stuphmud.server.player.interfaces.code.girl import initCommands
    except ImportError: pass
    else: initCommands()


    try: from stuphos.management import initForCore
    except ImportError: pass
    else:
        # Hack -- fixup core plugins before managed components.
        try:
            import stuphmud.server.player.db.managedfs
            from stuphmud.server.player.commands.gc import wizard
        except:
            # XXX :skip: Why doesn't this print the exception causes?
            # import traceback
            # traceback.print_exc()

            logException(traceback = True)

        initForCore()


    # Todo: integrate this into management initForCore?
    # Note: AgentSystem (plugin) relies on webserver, which is
    # a management component.  Use Management:webserver-object.
    # debugOn()
    installPlugins()


def installWorld():
    try: from stuphmud.server.zones import initForCore
    except ImportError: pass
    else: initForCore()

    from stuphmud.server.player.commands import installCommands
    installCommands()


def installSystemConfig():
    from os import getenv
    config = getenv('STUPHOS_CONFIG_ENV')
    if config:
        # Load --set-option from command line for initial config.
        reloadConfigFile(config, setOptions = core.cmdln['options'].set_option)


# Event Bridge.
def bootStart(configFile, setOptions):
    # Note: this function must return the bridge, or
    # the rest of the extension is not installed.

    # todo: import more of management
    # import mud.tools.debug


    # Least configurable:
    # installSystemConfig()

    bridge = installBridge()


    from stuphos.runtime.registry import getRegistry
    thisModule = getMudModule()
    getRegistry(create = thisModule.on) # Binding passed for shutdown-game registration.

    if configFile:
        # Note: this is necessary in order to activate 'configuration' builtin.
        reloadConfigFile(configFile, setOptions = setOptions)


    installSite()


    import sys
    sys._ph_security_package = configuration.Security.ph_security_package


    # Start reliance on VM path packages and rest of site.
    try:
        installServices(thisModule)
        installWorld()

        from stuphos.management.reboot import StartRecovery
        StartRecovery()

    except:
        logException(traceback = True)
    finally:
        return bridge

def bootComplete(timing):
    (secs, usecs) = timing
    from stuphos.management.reboot import CompleteRecovery
    CompleteRecovery()
