# Service/Daemon Management.

# todo: provide an application provider interface
from sys import platform

# if platform == 'cygwin':
from os import kill, spawnv, P_NOWAIT
from signal import SIGKILL as KILL_SIGNAL, SIGQUIT as QUIT_SIGNAL
from errno import ESRCH

from optparse import OptionParser, Option

from stuphos.runtime.facilities import Facility
from stuphos.runtime import Component
from .config import loadConfig
from ..etc import parseOptionsOverSystem, fromJsonFile, OpenFile, FileNotFoundException
from stuphos import getSection

import signal
_sigcodes = dict((getattr(signal, sig), sig) for sig in dir(signal) \
                 if sig.startswith('SIG'))

def parseCmdln(argv, *args):
    parser = OptionParser()

    for param in args:
        if type(param) in (list, tuple):
            parser.add_option(*param)
        elif isinstance(param, str):
            parser.add_option(param)
        elif isinstance(param, Option):
            parser.add_option(param)

    if argv in (list, tuple):
        argv = ' '.join(map(str, argv))

    return parseOptionsOverSystem(parser, argv)

def getStatusFile(folder, name):
    return joinpath(folder, name) + '-status.json'

def loadStatusFile(folder, name):
    def _():
        try: return fromJsonFile(OpenFile(getStatusFile(folder, name)))
        except FileNotFoundException: return dict()

    return SubDaemonManager.SubDaemon.Status(**_())

def saveStatusFile(folder, name, data):
    with open(getStatusFile(folder, name), 'w') as outfile:
        toJsonFile(data, outfile)

class SubDaemonManager(Facility):
    # This should probably use the subprocess module to handle child exits.
    NAME = 'SubDaemon::Manager'

    class Manager(Facility.Manager):
        VERB_NAME = 'subdaemon-*manage'
        MANAGE_LEVEL = Facility.Manager.IMPLEMENTOR

        USAGE = 'Usage: subdaemon-manage { load | unload | show [--long] | start | quit [--abort] | reload }'

        def doCommand(self, peer, cmd, args):
            if peer.avatar and peer.avatar.level >= self.MINIMUM_LEVEL:
                largs = args and args.strip().lower() or ''
                args = args and args.split() or ()

                try:
                    # Re-mapping facility-management sub-commands:
                    if not largs:
                        print(self.facility.get() or 'Not installed.', file=peer)
                    elif largs == 'load':
                        print(self.facility.get(create = True), file=peer)
                    elif largs == 'unload':
                        print(self.facility.destroy() and \
                              'Destroyed.' or 'Unknown facility.', file=peer)

                    # Use these ones for the subdaemon control.
                    else:
                        this = self.facility.get()
                        if this is None:
                            print('Facility is not loaded.', file=peer)
                        elif not self.doSubCommand(this, peer, args):
                            print(self.USAGE, file=peer)

                except RuntimeError as e:
                    print(e, file=peer)
                except SystemExit:
                    pass

                return True

        def doSubCommand(self, mgr, peer, args):
            # Q: Hasn't this been factored into the Manager base class?
            name = 'do_%s' % (args[0],)
            subcmd = getattr(self, name, None)

            if callable(subcmd):
                subcmd(mgr, peer, args[1:])
                return True

        def getDaemon(self, mgr, args):
            try: name = args[0]
            except KeyError:
                raise RuntimeError('Must specify <subdaemon-name>!')

            try: return mgr.getDaemon(name)
            except NameError:
                raise RuntimeError('Unknown daemon: %r' % name)

        def do_start(self, mgr, peer, args):
            daemon = self.getDaemon(mgr, args)
            if not daemon.isRunning():
                daemon.startProcess(args, manager = self)
                print(daemon, file=peer)
            else:
                print('Already running: %r' % daemon, file=peer)

        def do_quit(self, mgr, peer, args):
            (options, args) = parseCmdln(args, Option('--abort', action = 'store_true'))
            daemon = self.getDaemon(mgr, args)
            if daemon.isRunning():
                if options.abort:
                    daemon.abortProcess(manager = self)
                else:
                    daemon.quitProcess(manager = self)

                print(daemon, file=peer)
            else:
                print('Not running: %r' % daemon, file=peer)

        def do_show(self, mgr, peer, args):
            (options, args) = parseCmdln(args, Option('--long', action = 'store_true'))

            if args:
                daemons = []
                for name in args:
                    try: selected.append((name, mgr.getDaemon(name)))
                    except NameError:
                        raise RuntimeError('Unknown daemon: %r' % name)
            else:
                daemons = iter(mgr.daemons.items())

            if options.long:
                daemons = ('%s\r\n%s\r\n%s\r\n' % \
                           (name, '-' * len(name),
                            daemon.getLongDescription()) \
                           for (name, daemon) in daemons)
            else:
                daemons = ('%s: %r' % nd for nd in daemons)

            peer.page_string('\r\n'.join(daemons) + '\r\n')

        def do_reload(self, mgr, peer, args):
            mgr.reloadAllConfigs()
            print(mgr, file=peer)

        # detach, pause, resume

    class SubDaemon:
        # Todo: provide a subprocess architecture for piping i/o.
        RAW = ['arguments']

        class Status:
            def __init__(self, pid = -1, state = None, exepath = None):
                self.pid = pid
                self.state = state
                self.exepath = exepath

            def getSavedData(self):
                return dict(pid = self.pid,
                            state = self.state,
                            exepath = self.exepath)

            def synchronize(self, daemon):
                # Todo: Introspect the process at pid and validate that
                # it matches the exepath/start-time to confirm state.

                # daemon.pid = self.pid
                # daemon.state = self.state

                # Todo: if the daemon is found to not be started, attempt
                # to start it now?  XXX How to do this without manager?
                #
                #     Have this function return an outcome code to signal
                #     this post-condition to the loading manager.

                pass

        @classmethod
        def parseConfig(self, section):
            for opt in section.options():
                if opt in self.RAW:
                    get = section.config.config.get
                    yield (opt, get(section.section, opt, raw = True))
                else:
                    yield (opt, section.get(opt))

        def __init__(self, name, config):
            self.name = name
            self.config = config
            self.pid = -1
            self.state = 'unstarted'

        def getPid(self):
            return self.pid
        def getState(self):
            return self.state
        def isRunning(self):
            return self.getState() in ['running', 'started']
        def isPersistant(self):
            return self.config.get('persistant', False)

        try:
            DEFAULT_QUIT_SIGNAL = QUIT_SIGNAL
            DEFAULT_ABORT_SIGNAL = KILL_SIGNAL
        except NameError:
            # no platform....
            pass

        @classmethod
        def parseSignal(self, signame):
            if isinstance(signame, int):
                assert signame in _sigcodes
                return signame

            if isinstance(signame, str):
                signame = signame.upper()
                if signame.startswith('SIG'):
                    return getattr(self.signal, signame)

            raise ValueError(signame)

        def getExePath(self):
            return self.config['exepath']
        def getQuitSignal(self):
            return self.parseSignal(self.config.get('quit-signal', self.DEFAULT_QUIT_SIGNAL))
        def getAbortSignal(self):
            return self.parseSignal(self.config.get('abort-signal', self.DEFAULT_ABORT_SIGNAL))
        def getCommandLine(self, args):
            # todo: be able to inject args into command-line:
            #    detect command-line interpolatable values
            #    generate option parser from these values
            #    parser args with these options
            #    plug values into evaluation

            cmdln = [self.getExePath()]
            template = self.config.get('arguments', '')
            argv = template % self.config
            cmdln.extend(argv.split())

            return cmdln

        def saveStatus(self, manager):
            if manager is not None:
                manager.saveStatusFile(self.name,
                                       self.Status(pid = self.pid,
                                                   status = self.state,
                                                   exepath = exepath))

        def synchronize(self, loadStatus):
            status = self.loadStatus(self.name)
            status.synchronize(self)

        # Process life-cycle.
        def startProcess(self, args, manager = None):
            exepath = self.getExePath()
            args = self.getCommandLine(args)

            self.cmdln_instance = args
            self.pid = spawnv(P_NOWAIT, exepath, args)
            self.state = 'started'

            self.saveStatus(manager)

        def killProcess(self, abort = False, manager = None):
            killSignal = self.getAbortSignal() if abort else self.getQuitSignal()
            pid = self.getPid()

            if pid >= 0:
                try: kill(pid, killSignal)
                except OSError as e:
                    if e[0] == ESRCH:
                        from stuphos.system.api import mudlog
                        mudlog('No such process: %d' % pid)

            self.state = 'killed'
            self.saveStatus(manager)

        def quitProcess(self, manager = None):
            return self.killProcess(manager = manager)
        def abortProcess(self, manager = None):
            return self.killProcess(abort = True, manager = manager)

        def restartProcess(self, args = (), abort_ok = False, manager = None):
            if abort_ok:
                self.abortProcess(manager = manager)
            else:
                self.quitProcess(manager = manager)

            self.startProcess(args, manager = manager)

        def getLongDescription(self):
            return '\n'.join(['Pid: %d' % self.getPid(),
                              'State: %s' % self.getState()] + \
                             ['%s: %s' % nv for nv in self.config.items()])
        def __str__(self):
            return 'exepath=%s pid=%d state=%s' % \
                   (self.getExePath(), self.getPid(), self.getState())
        __repr__ = __str__

    @classmethod
    def getAllConfigs(self):
        section = getSection('SubDaemonManager')
        if section:
            for opt in section.options():
                if opt == 'path' or opt.startswith('path.'):
                    cfg = loadConfig(section.get(opt))
                    for name in cfg.sections():
                        section = cfg.getSection(name)
                        subdaemoncfg = self.SubDaemon.parseConfig(section)
                        subdaemoncfg = dict(subdaemoncfg)
                        yield (name, self.SubDaemon(name, subdaemoncfg))

    @classmethod
    def getStatusFileDir(self):
        section = getSection('SubDaemonManager')
        if section:
            return section.get('statusfile-dir')

    @classmethod
    def create(self):
        statusfiledir = self.getStatusFileDir()
        assert statusfiledir # isdir(statusfiledir)

        return self(dict(self.getAllConfigs()),
                    statusfiledir)

    def __init__(self, daemons, statusfiledir):
        self.statusfiledir = statusfiledir
        self.installDaemons(daemons)
        Component(self.NAME, Target = self)

    def __registry_delete__(self):
        self.abortAllProcesses()

    def installDaemons(self, daemons):
        self.daemons = daemons

        # Scan the pidfiles for persistant daemons to load running state.
        for daemon in self.daemons.values():
            if daemon.isPersistant():
                daemon.synchronize(self.loadStatusFile)

    def loadStatusFile(self, name):
        return loadStatusFile(self.statusfiledir, name)
    def saveStatusFile(self, name, status):
        return saveStatusFile(self.statusfiledir, name,
                              status.getSavedData())

    def reloadAllConfigs(self):
        # Hard
        self.abortAllProcesses()
        self.installDaemons(dict(self.getAllConfigs()))

    def abortAllProcesses(self):
        for daemon in self.daemons.values():
            if not daemon.isPersistant():
                daemon.abortProcess()

    def getDaemon(self, name):
        try: return self.daemons[name]
        except KeyError:
            raise NameError(name)

    # This should be necessary -- the registry should delete.
    def onShutdownGame(self, ctlr, xxx_todo_changeme):
        (circle_shutdown, circle_reboot,
                                    shutdown_mode, shutdown_timer, shutdown_by) = xxx_todo_changeme
        self.abortAllProcesses()

    def __str__(self):
        return '%s (%d daemons)' % (self.__class__.__name__,
                                    len(self.daemons))
    __repr__ = __str__

# Install Management.
SubDaemonManager.manage()

# API -- Q: Is this necessary if it's all tucked into SubDaemonManager object??
try: from stuphos.runtime.registry import registerObject
except ImportError: pass
else:
    #@runtime.api(runtime.Node(SubDaemonManager.NAME).API)
    class API:
        def getManager(self, start_ok = False):
            return SubDaemonManager.get(create = bool(start_ok))
        def startManager(self):
            return self.getManager(start_ok = True)

        def reloadManager(self):
            return self.getManager().reloadAllConfigs()

        def getDaemon(self, name):
            return self.getManager().getDaemon(name)

        def startDaemon(self, name):
            daemon = self.getDaemon(name)
            if not daemon.isRunning():
                daemon.startProcess(args, manager = self.getManager())

        def quitDaemon(self, name, abort_ok = False):
            daemon = self.getDaemon(name)
            if daemon.isRunning():
                if abort_ok:
                    daemon.abortProcess(manager = self.getManager())
                else:
                    daemon.quitProcess(manager = self.getManager())

        def restartDaemon(self, name, args = (), abort_ok = False):
            daemon = self.getDaemon(name)
            if daemon.isRunning():
                daemon.restartProcess(args = (), abort_ok = abort_ok,
                                      manager = self.getManager())

    # Singleton.
    API = API()

    SUBDAEMON_API_OBJECT_NAME = SubDaemonManager.NAME + '::API'
    registerObject(SUBDAEMON_API_OBJECT_NAME, API)
