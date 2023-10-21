from . import CommandMessage, RegisterCommandClass

class ShellCommand:
    def parseCommandLine(self, cmdln):
        # XXX horrible parsing
        return cmdln.split()

class AdminScriptCommandMessage(CommandMessage, ShellCommand):
    def Execute(self):
        argv = self.parseCommandLine(self.payload)

        # Try to find argv[0] in etc/admin_scripts directory,
        # execute as a shell command with arguments.

class SystemShellCommandMessage(CommandMessage, ShellCommand):
    def Execute(self):
        from stuphos.runtime.registry import getObject
        argv = self.parseCommandLine(self.payload)
        shell = getObject('System::Shell::API')
        if shell:
            from stuphos import enqueueHeartbeatTask
            from stuphos.system.api import syslog

            pipe = shell.doCommandHeadless(argv[0], *argv[1:])
            def processOutput():
                result = pipe.read()
                enqueueHeartbeatTask(syslog, 'System Shell Result: %s' % result)

            enqueueHeartbeatTask(processOutput)

RegisterCommandClass('application/x-stuph-system-shell-command', SystemShellCommandMessage)
RegisterCommandClass('application/x-stuph-admin-script', AdminScriptCommandMessage)
