@runtime.api.Agent.System.Action
def libraryChange(core, node):
	libraryInvocation.systemAsynchronous \
		(core, 'system/workflow/libraryChange',
		 node.path)
