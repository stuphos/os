# Should this be in mud.tasks.parallel?
from _thread import start_new_thread
def nth(function, *args, **kwd):
	return start_new_thread(function, args, kwd)

def nthWith(*args, **kwd):
	# Decorator
	def runWith(function):
		return nth(function, *args, **kwd)

	return runWith
