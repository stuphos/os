from . import CommandMessage, RegisterCommandClass

# Other command message implementations.
class SubDaemonCommandMessage(CommandMessage):
    def Execute(self):
        from stuphos.runtime.registry import getObject
        mgr = getObject('SubDaemon::Manager')
        if mgr is not None:
            daemon = mgr.getDaemon(self.SUBDAEMON_NAME)
            if daemon is not None:
                if not daemon.isRunning():
                    daemon.startProcess([])

                # Now, communicate the message contained in payload to the server.

class JythonCommandMessage(SubDaemonCommandMessage):
    SUBDAEMON_NAME = 'jyCommandApp'

RegisterCommandClass('application/x-jython', JythonCommandMessage)
