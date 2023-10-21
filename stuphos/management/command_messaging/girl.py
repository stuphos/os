from . import CommandMessage, RegisterCommandClass

class GirlScriptCommandMessage(CommandMessage):
    def Execute(self):
        sourceCode = self.payload.replace('\r', '')

        from stuphos.kernel import Script, Girl, executeGirl
        # from world import heartbeat as vm
        module = Girl(Girl.Module, sourceCode)

        task = Script.Load()
        task.addFrameCall(module)
        return executeGirl(task)

RegisterCommandClass('application/x-stuph-agent-script', GirlScriptCommandMessage)
