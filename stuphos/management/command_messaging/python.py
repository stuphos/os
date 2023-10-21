from . import CommandMessage, RegisterCommandClass

class PythonScriptCommandMessage(CommandMessage):
    # Lame.
    _globals = {}
    _locals = {}

    class System:
        # Access.
        def __getitem__(self, name):
            return MaterializeResourceCommandMessage.getResource(name)
        def __iter__(self):
            return iter(MaterializeResourceCommandMessage.Pool.getMaster().items())

    def getGlobals(self):
        return self._globals
    def getLocals(self):
        return self._locals

    DEFAULT_CODE_SOURCE = 'automatic' # '<uptime-checkpoint command message>'

    def getCodeSource(self):
        return self.get('X-Code-Source', self.DEFAULT_CODE_SOURCE)
    def getScriptName(self):
        return self.get('X-Script-Name', '__main__')

    def Execute(self):
        # todo: add options to do threading/next heartbeat, remote/local debugging

        sourceCode = self.payload.replace('\r', '')
        codeSource = self.getCodeSource()

        if codeSource == 'automatic':
            from stuphmud.server.player.interfaces.code import TemporaryCodeFile
            codefile = TemporaryCodeFile(self.fakePeer, sourceCode,
                                         shellName = self.fakePeer.avatar.shellName)
            with codefile:
                return self._executeCode(codefile.filename, sourceCode)
        else:
            return self._executeCode(codeSource, sourceCode)

    class fakePeer: # For use with TemporaryCodeFile
        recordCompiler = True
        class avatar:
            name = 'stuphMud'
            shellName = 'SystemCheckpoint'
            isPlayer = True # to use the name

    def _executeCode(self, codeSource, sourceCode):
        code = compile(sourceCode, codeSource, 'exec')

        ns_globals = self.getGlobals()

        # This is necessary for an 'exec' scope??
        ns_locals = ns_globals # self.getLocals()

        ns_globals['system'] = self.System()
        ns_globals['__name__'] = self.getScriptName()

        if self.headers.get('X-Script-Debug') == 'on':
            # XXX Should be remote debugging at the very best!!
            import pdb; pdb.set_trace()

        exec(code, ns_globals, ns_locals)

RegisterCommandClass('application/x-stuph-python-script', PythonScriptCommandMessage)
