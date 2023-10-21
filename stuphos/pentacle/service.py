# class LibraryDispatch(SubcommandMode):
# 	def __init__(self, path, previous = None):
# 		BaseMode.__init__(self, previous = previous)
# 		self.path = path

#     def defaultCommand(self, engine, peer, name, *args, **kwd):
#     	# get programmer setting from authenticated peer association.
#     	# run in a separate thread, and wait for the task completion to post result for return.
#     	pass

# # Craft an application that pushes LibraryDispatch modes based on configuration.
# # One way to do this is to override Application.LoggedInMode.

# from receptacle.architecture import ServiceBase
# class Girl(ServiceBase):
#     NAME = 'Agent'

#     def doRunModule(self, engine, peer, source, *args, **kwd):
#         from stuphos.kernel import newModuleTask
#         from Queue import Queue

#         q = Queue()

#         @newModuleTask(source, arguments = args, **kwd)
#         def response(result):
#         	q.put(result)

#         return q.get()

#     def doEvaluate(self, engine, peer, source, *args, **locals):
#         from stuphos.kernel import Girl, Script, executeGirl
#         from Queue import Queue

#         q = Queue()

#         procedure = Girl(Girl.Expression, source)
#         locals['arguments'] = args

#         task = Script.Load()
#         task.addFrameCall(procedure, locals = locals)

#         @executeGirl(task)
#         def response(task):
#             # tag:task-completion
#             q.put(task.stack[0])

#         return q.get()

#     def doRunAssembly(self, engine, peer, source, *args, **locals):
#         from stuphos.kernel import Girl, Script, executeGirl

#         procedure = Girl(Girl.Asm, source)
#         locals['arguments'] = args

#         task = Script.Load()
#         task.addFrameCall(procedure, locals = locals)

#         executeGirl(task)

#     def doRunMachineCode(self, engine, peer, code, *parameters, **locals):
#         from stuphos.kernel import Girl, Assembly, Script, executeGirl

#         # Compile and run.
#         procedure = Girl(Assembly, code)
#         locals['arguments'] = args

#         task = Script.Load()
#         task.addFrameCall(procedure, locals = locals)

#         executeGirl(task)

#     def doOpenServerChannel(self, engine, peer, name, *args, **kwd):
#         from stuphos.kernel import serverChannel

#         core = runtime[runtime.Agent.System]
#         assert core is not None

#         return serverChannel(core, name)


# class Federation(ServiceBase):
#     NAME = 'Federation'

#     def doRouteCall(self, engine, peer, routeAddress, method, *args, **kwd):
#     	pass
