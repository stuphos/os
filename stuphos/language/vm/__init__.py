from op.compute.emulation.application import VM as _VM

def enter(frame, procedure, *args, **kwd):
	'''
	components/language/application::
		def init$(source):
			a = $.components.language.cpp(source)
			i = $.components.language.x86.load(a)
			m = i.main.emulationCompiled.function()
			t = $.components.language.vm.enter(m)

			def execute():
				while true:
					t.run()

			.task = task(execute)
			.library = i

			'''

	task = _VM.Task()
	task.frameCall(procedure, *args, **kwd)
	vm += task

	return task
