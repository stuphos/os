'This package stores SQLObject schema in separately-imported modules.'
from os.path import abspath

IN_MEMORY = ':memory:'
DEFAULT_PROTOCOL = 'sqlite'

def _importMember(module):
	parts  = module.split('.')
	module = __import__('.'.join(parts[:-1]))

	for m in parts[1:]:
		module = getattr(module, m)

	# Or member
	return module

def openProcessConnection(path, protocol = DEFAULT_PROTOCOL):
	if path == IN_MEMORY:
		path = '/' + IN_MEMORY
	else:
		path = abspath(path)

	c = sqlobject.connectionForURI('%s:%s' % (protocol, path))
	sqlobject.sqlhub.processConnection = c
	return c

connect = openProcessConnection

def openDatabaseTables(path, *tables, **kwd):
	protocol       = kwd.get('protocol', 'sqlite')
	schema_package = kwd.get('schema_package')

	openProcessConnection(path, protocol)

	def open_table(t):
		if schema_package:
			t = schema_package + '.' + t

		# import sqlobject.classregistry
		# reload(sqlobject.classregistry)

		t = _importMember(t)
		t.createTable(ifNotExists = True)
		return t

	return list(map(open_table, tables))

tables = openDatabaseTables

def getStuphZoneRecordIDByZoneVnum(vnum, cache = {}):
	# Patches up cross-module foreign-key joins.
	if vnum in cache:
		return cache[vnum]

	from .zone import StuphZoneRecord as Z

	r = list(Z.selectBy(vnum = vnum)[:1])

	if len(r) > 0:
		r = r[0].id
		cache[vnum] = r
		return r

	# XXX return -1 ??

# def new_database_file(format = 'stuph-world-%d.db', root_path = 'lib/etc'):
#	# regex = r'stuph-world-(\d+)\.db'
#	from itertools import count
#	from os.path import exists, join
#
#	for dbno in count(1):
#		dbpath = join(root_path, format % dbno)
#		if not exists(dbpath):
#			return dbpath
#
#		assert dbno < 9999

try: import sqlobject
except ImportError:
        class sqlobject:
                pass

        class DisabledException(Exception):
                pass

        def disabled(*args, **kwd):
                raise DisabledException

        connect = openProcessConnection = disabled
        tables = openDatabaseTables = disabled
        
        getStuphZoneRecordIDByZoneVnum = disabled
