# Compartmental Command-line Bootstrap Interface.
from optparse import OptionParser
import sys, os

try: import pdb
except ImportError: pass

def parseCmdln(argv = None):
    parser = OptionParser()

    parser.add_option('-C', '--config-file', '--config', '--game-config')
    parser.add_option('-g', '--debug', action = 'count', default = 0)
    parser.add_option('-p', '--port', type = int)
    parser.add_option('-v', '--verbose', action = 'count', default = 0)
    parser.add_option('-d', '--headless', '--no-console', action = 'store_true')

    parser.add_option('-w', '--world-dir')
    parser.add_option('-z', '--zone-index', '--index')
    parser.add_option('--reset-world', action = 'store_true')
    parser.add_option('-Z', '--full-world', action = 'store_true')
    parser.add_option('-n', '--no-world', action = 'store_true')
    parser.add_option('-W', '--cascade', '--load-world', action = 'store_true')

    parser.add_option('-i', '--interactive', action = 'store_true')
    parser.add_option('-a', '--asynchronous', '--async', action = 'store_true')
    parser.add_option('-m', '--mud-package', '--mud')
    parser.add_option('-e', '--service', action = 'append', default = [], dest = 'services')
    parser.add_option('-S', '--set-option', action = 'append', default = [])

    parser.add_option('-s', '--supreme', action = 'store_true')
    parser.add_option('--enter-game', action = 'store_true')

    parser.add_option('--admin-name')

    # These are different than admin-name:
    parser.add_option('--admin-script')
    parser.add_option('-x', '--admin-script-args', default = [], action = 'append')

    parser.add_option('-f', '--file') # Like -c, but a whole file as module script.

    # And this is for injecting initial commands into a console-based session.
    parser.add_option('-c', '--admin-command')
    parser.add_option('--admin-trace', action = 'store_true')

    parser.add_option('--parser-tokenize', action = 'store_true')
    parser.add_option('--elemental-parser-debug', '--parser-debug')

    parser.add_option('-L', '--data-dir', '--lib-dir')
    # parser.add_option('--libdata')

    parser.add_option('--fast-vm', action = 'store_true')
    parser.add_option('--blocking', type = int, default = 0)
    parser.add_option('--timeout', type = int, default = 0)
    parser.add_option('--runpid', action = 'store_true')

    parser.add_option('--no-run-engine', action = 'store_true')
    parser.add_option('--no-init', action = 'store_true')

    parser.add_option('--tool-package', action = 'append', default = [])
    parser.add_option('--load-fixture', action = 'append', default = [], dest = 'fixture_load_set')
    parser.add_option('--agent-system')
    parser.add_option('--local', '--local-filesystem')

    return parser.parse_args(argv)


def getCmdln(argv = None):
    return sys.argv if argv is None else argv


    # can't specify a --mud-package to the game.cli because the game module
    # now fully imports the compartment system necessarily, which depends on
    # the stuphos.runtime package.

    #     The implications of this are that the compartment server cannot
    #     boot independently or independently load a particular application
    #     base package, but rather is must essentially statically link with
    #     the runtime.  The only real reason for this is because: the cli
    #     application bootstrap code originally loaded runtime components
    #     AT runtime (dynamically), but because it's doing so using the game
    #     module, and everything in the synthetic game module is now statically
    #     imported so that there's no relative package imports using it's name,
    #     it's because of the static nature of the synthetic game module that
    #     we can back everything with compartment concretely but update very
    #     little about the way we refer to game, as a container concept.


class ConsoleBusiness:
    # Heartbeat Task Implementation.
    def activate(self, engine):
        self.engine = engine
        engine.console = self
    def deactivate(self, engine):
        try:
            if self.engine is engine:
                del self.engine
        except AttributeError:
            pass

        try:
            if engine.console is self:
                del engine.console
        except AttributeError:
            pass

    def perform(self, engine):
        self.engine.event += self.handleConsoleInput

    # Game I/O Events.
    PROMPT = ' --+====> ' # ' +> '

    def readConsoleInput(self):
        # Todo: Do not perform.  Instead, enable an XMLRPC method for entering input.
        return input(self.prompt or self.PROMPT).rstrip()

    def handleConsoleInput(self):
        'Interpret player input as command for avatar.'

        try:
            self.forceInput(self.readConsoleInput())
            if self.debug:
                return pdb.runcall(self.handleNextInput)

            else:
                return self.handleNextInput()

        except EOFError as e:
            print()

            e = str(e)
            if e:
                print(f'{self.__class__.__name__}.handleConsoleInput: {e}')

            from stuphos.etc.tools.strings import isYesValue
            if isYesValue(configuration.Interpreter.console_eof_stubborn):
                # If not set, seek to terminate this console session.
                return

        except SystemExit:
            pass
        else:
            return

        # Full stop on errors.
        if self.engine.headless:
            self.engine -= self
        else:
            @self.engine.event.call
            def done():
                # debugOn()
                self.engine.stop()
                StuphMUD.ShutdownGame()
                # gc.collect(); os.kill(signal.SIGTERM, os.getpid())


    # Entity Handle -- Bastard player implementation.
    def __init_entity__(self, debug = False):
        self.host = 'localhost'
        self.debug = debug

    def textout(self, text):
        # Set by mud.player.shell.ShellI.withPeerHeadAndException
        getattr(sys, '__peer_shell_stdout').write(text)

    def sendln(self, line):
        print(line, file=sys.stdout)

    # Avoid the whole external pipe thing, especially for a windowed IDE.
    if os.name.startswith('nt'):
        def page_string(self, string):
            from stuphos.etc.tools.strings import parse_color
            string = ''.join(parse_color(string))
            print(string)

    elif os.name.startswith('posix'):
        nroff = True
        def page_string(self, string):
            from os import popen
            from stuphos.etc.tools.strings import parse_color
            string = ''.join(parse_color(string))
            popen('%s/bin/less' % ('/usr/bin/nroff|' if self.nroff else ''), 'w') \
                                .write(str(string))

    def editString(self, string):
        if callable(self.messenger):
            self.messenger(self, string)

    def messenger(self, peer, string):
        self.page_string(string)

