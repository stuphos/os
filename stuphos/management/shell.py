# Execute routine system commands and redirect to peer.
from stuphos.runtime.facilities import Facility
from .config import loadConfig
from ..etc import parseOptionsOverSystem
from stuphos import getSection, enqueueHeartbeatTask

import os
from _thread import start_new_thread as nth

class SystemShell(Facility):
    NAME = 'System::Shell'

    class Manager(Facility.Manager):
        VERB_NAME = 'system-sh*ell'
        MANAGE_LEVEL = Facility.Manager.IMPLEMENTOR

        USAGE = 'Usage: system-shell { load | unload | show [--long] | <command> }'

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
            name = args[0]
            args = args[1:]

            methname = 'do_%s' % (name,)
            subcmd = getattr(self, methname, None)

            if callable(subcmd):
                subcmd(mgr, peer, args)
                return True

            try: sh = mgr.getShellCommand(name)
            except NameError:
                print('Unknown subcommand or shell command: %r' % name, file=peer)
            else:
                if sh:
                    sh.invoke(mgr, peer, args)
                    return True

        def do_show(self, mgr, peer, args):
            peer.page_string('\r\n'.join('%s: %s' % (name, sh.getSystemCommand()) \
                                         for (name, sh) in mgr.commands.items()) + '\r\n')

        def do_reload(self, mgr, peer, args):
            mgr.reloadAllConfigs()
            print(mgr, file=peer)

    class ShellCommand:
        @classmethod
        def parseConfig(self, section):
            for opt in section.options():
                yield (opt, section.get(opt))

        def __init__(self, name, config):
            self.name = name
            self.config = config

        def getSystemCommand(self):
            try: return self.config['command']
            except KeyError:
                raise ValueError

        def invoke(self, mgr, peer, args):
            ##    if not peer.avatar or peer.avatar.level < self.config.get('level', mgr.Manager.MINIMUM_LEVEL):
            ##        return

            try: systemCommand = self.getSystemCommand()
            except ValueError:
                mgr.syslog('Command not configured: %r' % self.name)
            else:
                mgr.syslog('Executing: %r' % self.name)
                mgr.syslog('...%s' % systemCommand)

                pipe = os.popen(systemCommand)
                def processOutput():
                    enqueueHeartbeatTask(peer.page_string, pipe.read())

                nth(processOutput, ())

        def invokeHeadless(self, mgr, args):
            systemCommand = self.getSystemCommand()
            mgr.syslog('Executing: %r' % self.name)
            mgr.syslog('...%s' % systemCommand)

            return os.popen(systemCommand)

    @classmethod
    def getAllConfigs(self):
        section = getSection('SystemShell')
        if section:
            for opt in section.options():
                if opt == 'path' or opt.startswith('path.'):
                    cfg = loadConfig(section.get(opt))
                    for name in cfg.sections():
                        section = cfg.getSection(name)
                        shellcmdcfg = self.ShellCommand.parseConfig(section)
                        shellcmdcfg = dict(shellcmdcfg)
                        yield (name, self.ShellCommand(name, shellcmdcfg))

    @classmethod
    def create(self):
        return self(dict(self.getAllConfigs()))
    def __init__(self, commands):
        self.commands = commands

    def getShellCommand(self, name):
        try: return self.commands[name]
        except KeyError:
            raise NameError(name)

    def reloadAllConfigs(self):
        # Hard
        self.commands = dict(self.getAllConfigs())

    def syslog(self, message):
        from stuphos.system.api import syslog
        syslog('[%s]: %s' % (self.__class__.__name__, message))

    def __str__(self):
        return '%s (%d commands)' % (self.__class__.__name__,
                                     len(self.commands))
    __repr__ = __str__

# Install Management.
SystemShell.manage()

##    @ACMD('shell-pstree*')
##    def doShellPSTree(peer, cmd, argstr):
##        if peer.avatar and peer.avatar.level >= 115:
##            peer.page_string(os.popen('ps ux').read())
##            return True

# API
try: from stuphos.runtime.registry import registerObject, ObjectAlreadyRegistered
except ImportError: pass
else:
    class API:
        def getSystemShell(self):
            return SystemShell.get()
        def reloadCommands(self):
            return self.getSystemShell().reloadAllConfigs()

        def doCommand(self, name, peer, *args):
            mgr = self.getSystemShell()
            sh = mgr.getShellCommand(name)
            if sh:
                sh.invoke(mgr, peer, args)

        def doCommandHeadless(self, name, *args):
            mgr = self.getSystemShell()
            sh = mgr.getShellCommand(name)
            if sh:
                return sh.invokeHeadless(mgr, args)

    # Singleton.
    API = API()

    SYSTEMSHELL_API_OBJECT_NAME = SystemShell.NAME + '::API'
    try: registerObject(SYSTEMSHELL_API_OBJECT_NAME, API)
    except ObjectAlreadyRegistered:
        pass
