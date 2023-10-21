from .conf import *

def installVariableDatabaseNativeTool(*args, **kwd):
	from .vardb import installVariableDatabaseNativeTool
	return installVariableDatabaseNativeTool(*args, **kwd)


# Among other modules, SQLObject relies on datetime, which relies on thread-
# sensitive module imports that can fail because of race conditions.  The
# logging system uses datetime entities through sqlobject in another thread,
# and because sqlobject (as a third party library) relies on datetime, I'm
# performing the pre-import here.  It may need to be moved into the parent
# package initialization code.  The reason a pre-import should work is because
# the dynamic load won't race if the module is already in the system mapping.

try: import _strptime
except Exception as e:
	print('[_strptime pre-import] %s: %s' % (e.__class__.__name__, e))
