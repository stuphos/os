# Also found in etc.tools.__init__
def apply(function, *args, **kwd):
	return function(*args, **kwd)


def importAllMembers(o):
	try: return o.__all__
	except AttributeError:
		return (n for n in dir(o) if not n.startswith('_'))

def importAll(module, scope):
	from .lookup import LookupObject
	module = LookupObject(module)
	for n in importAllMembers(module):
		scope[n] = getattr(module, n)

def importAllInit(name, msg, scope):
	if name:
		try: importAll(name, scope)
		except ImportError as e:
			print(f'{msg} {e}')
