# Initialize Management Services for Bootstrap.
from stuphos.etc.tools import isYesValue
from .services import AutoServices

class ManagementServices(AutoServices):
    CONFIG_OBJECT_NAME = 'MUD::Configuration'
    CONFIG_SECTION_NAME = 'Management'

    def loadPentacleServices(self, conf):
        from stuphos.pentacle import partner
        partner.bootPartnerAspect()

    def loadSessionAdapter(self, conf):
        from phsite.network.adapter.sessions import SessionManager
        try: SessionManager.get(create = True) # CreateFacility(SessionManager)
        except RuntimeError as e:
            logOperation(f'[sessions] {e}')

    def loadEmbeddedWebserver(self, conf):
        from stuphos.runtime.architecture.api import LookupObject
        webServiceClass = LookupObject(self.section.get('webserver-object', 'stuphos.webserver.DjangoService'))

        try: webServiceClass.get(create = True) # CreateFacility(webServiceClass)
        except OSError as e:
            logOperation(f'[webserver] {e.__class__.__name__}: {e}')

            from stuphos import logException
            logException(traceback = True)

        # todo: catch error: [Errno 112] Address already in use
        # OSError: [Errno 98] Address already in use


    # Some lesser features.
    def loadSystemShell(self, conf):
        from . import shell
        shell.SystemShell.get(create = True)
        # CreateFacility(shell.SystemShell)

    def loadSubdaemonManager(self, conf):
        from . import subdaemon
        subdaemon.SubDaemonManager.get(create = True)
        # CreateFacility(subdaemon.SubDaemonManager)

    def loadSyslogScanner(self, conf):
        from . import syslog

    def loadCrashHandler(self, conf):
        import sys, signal
        from os import kill, getpid

        def bailOut(signr, frame):
            # Running after a segv does not guarentee success,
            # but if we have enough facility, then we want this data.
            print(system.CallingFrame.Snapshot(), file=sys.stderr)

            # Resend signal with default processor -- force crash.
            signal.signal(signal.SIGSEGV, signal.SIG_DFL)
            kill(getpid(), signal.SIGSEGV)

        signal.signal(signal.SIGSEGV, bailOut)

    def postOn(self, cfg):
        if not isYesValue(cfg.get('embedded-webserver')):
            from stuphos.webserver import djangoConfig
            djangoConfig()


initForCore = ManagementServices(setup_deferred = True)

# def traceToSyslog(frame, pos, instr, args):
#     msg = '%04d %s(%s)' % (pos, getattr(instr, '__name__', '?'),
#                            ', '.join(map(str, args)))

#     import game
#     game.syslog('%s:\n%s' % (msg, '\n'.join(map(repr, frame.task.stack))))

#     # import pdb; pdb.set_trace()
#     # return True # enter (girl) debugger

def runSessionCore(peer, path, activationName, **environ):
    # Structural combination of girl and web.adapter.sessions
    # from stuphos.system.api import game
    from stuphos.kernel import constrainStructureMemory

    try: session = peer.session_ref()
    except AttributeError:
        pass
    else:
        core = runtime[runtime.Agent.System]
        vm = runtime[runtime.System.Engine]

        if session is None or core is None or vm is None:
            def run(function):
                raise RuntimeError('Invalid runtime')
        else:
            try: playerName = peer.avatar.name.lower()
            except AttributeError: progr = None
            else:
                from stuphos.runtime.architecture.api import getWebProgrammer
                progr = getWebProgrammer()(playerName)

            def run(function):
                try:
                    struct = core[path].structure
                    trigger = getattr(struct, activationName) # trigger

                except (AttributeError, KeyError): pass
                except ImportError as e: # no WMF
                    pass # todo: log
                else:
                    try: name = environ.pop('task_name')
                    except KeyError: name = None

                    def initContainer(task):
                        # Whoops: should be using 'environment', set by Trigger.
                        with vm.threadContext(task = task):
                            task.frame.locals['container'] = constrainStructureMemory(task, struct)

                    # debugOn()
                    debug = configuration.Interpreter.debug_session
                    if isYesValue(debug):
                        debug = True

                    # Pass a trigger by naming it via activationName in the struct.
                    if callable(getattr(trigger, '_activate', None)):
                        task = trigger._activate(trigger._module, locals = environ,
                                                 initialize = initContainer,
                                                 programmer = progr,
                                                 audit = debug)

                        task._task.name = name # mud.management.structure.Trigger.Task

                        # game.syslog('operator: %r, audit: %r' % (task._task.operator, task._task.tracing))

                        @task._onComplete
                        def complete(_, exception = None):
                            # p = task._task.frames[-1].procedure
                            # game.syslog('%s\n%s\n%s' % (p.position()-1, p.instructions, task._task.stack))
                            # game.syslog('\n%s' % '\n'.join(map(repr, task._task.stack)))

                            try: result = task._result
                            except IndexError as e:
                                pass # game.syslog('%s' % e)
                            else:
                                try: function(session, result)
                                except:
                                    from stuphos import logException
                                    logException(traceback = True)

        return run
