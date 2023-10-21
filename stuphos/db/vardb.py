# VarDB

try: import op.data.sqlite # Requiring WRLC.
except ImportError:
	from . import sqlite
	from builtins import sqlite

from stuphos.runtime.architecture.api import writeprotected, representable
from stuphos.runtime.architecture import newClassObject
from stuphos.kernel import AutoMemoryMapping, AutoMemoryNamespace, baseStringClass, vmCurrentTask

from stuphos import getConfig
from . import orm, dbCore
from .orm import VariableDBNativeTool, createSQLObjectTable as createSqlTable

from contextlib import contextmanager
from datetime import datetime


class NoCoreDatabasePolicy(RuntimeError):
	def __init__(self, core):
		RuntimeError.__init__(self, f'No database policy for core: {core}')
		self.core = core


@contextmanager
def database():
	with dbCore.hubThread(configuration.VariableDB.namespace) as o:
		yield o

def buildSqlObject(tableName, registry, cfg):
	# def populateNS(ns):
	# 	ns.update(cfg)

	try: return newClassObject(tableName, (sqlite.Object,), cfg) # exec_body = populateNS)
	except ValueError:
		# XXX The registry will need to be flushed if the table definition
		# changes in the database schema.
		from sqlobject import classregistry # sqlite.module.
		return classregistry.registry(registry).getClass(tableName)

# def createSqlTable(table):
# 	from sqlobject.dberrors import OperationalError
# 	try: table.createTable()
# 	except OperationalError:
# 		pass

# Database Flags.
DBFLAG_NOACCOUNT = (1 << 0)


# class VariableDB(writeprotected, AutoMemoryMapping, representable):
class VariableDB(writeprotected, representable):
	# _preserve_memory_binding = True
	_memoryObjectManaged = True

	DBFLAG_NOACCOUNT = DBFLAG_NOACCOUNT


	@classmethod
	def _checkCore(self, core):
		# Security check: as an extension of the structure() native
		# initiatable by programs contained by a syntheticAgentSystem,
		# we want the VariableDB._Open method to only allow topmost
		# database paths (AgentSystem) because _Open opens the sqlite
		# db directly and without this policy a synthetic container
		# could merely shadow a topmost path.
		if core is None or core is not runtime[runtime.Agent.System]:
			raise NoCoreDatabasePolicy(core)


	@classmethod
	def _Select(self, name):
		with database():
			yield from orm.DatabaseConfiguration.selectBy(name = name)

	@classmethod
	def _Names(self):
		with database():
			for db in orm.DatabaseConfiguration.select():
				yield db.name

	@classmethod
	def _Open(self, core, name, **cfg):
		self._checkCore(core)

		for dbConf in self._Select(name):
			# Note: relies on wrlc
			# rootpath = configuration.VariableDB.root_path
			# if rootpath:
			# 	path = io.path(dbConf.path.format(rootpath = rootpath))
			# else:

			path = io.here(dbConf.path)
			handle = sqlite.pathOpen(path)

			return self._OpenConfHandle(name, dbConf, handle, **cfg)

		raise NameError(name)

	@classmethod
	def _OpenConfHandle(self, name, dbConf, handle, **cfg):
		return self(name, dbConf.hard, dbConf.flags, handle, **cfg)

	@classmethod
	def _Create(self, name, path, hard, flags = 0):
		for dbConf in self._Select(name):
			raise NameError(name)

		return orm.DatabaseConfiguration(name = name, path = path,
										 hard = hard, flags = flags)

	class _Namespace(writeprotected, representable):
		def __init__(self, object):
			self._object = object

		def __getattr__(self, name):
			try: return object.__getattribute__(self, name)
			except AttributeError:
				try: return self._object[name]
				except KeyError:
					raise AttributeError(name)


	# __public_members__ = ['name', 'tables']

	def __init__(self, name, hard, flags, db, **cfg):
		# AutoMemoryMapping.__init__(self)
		self._tables = dict()
		self._name = name
		self._hard = hard
		self._flags = flags or 0
		self._db = db

		self._setAttribute('tables', self._Namespace(self))
		for (name, t) in cfg.items():
			t._set_database(self)
			self._tables[name] = t

	@property
	def name(self):
		return self._name

	@property
	def path(self):
		r = ['system:vardb', 'path'] + self._name.split('/')
		vmCurrentTask().checkAccessSystem(r, 'read')

		for dbConf in self._Select(self._name):
			return dbConf.path

		raise NameError(self._name)

	@property
	def sqliteConnectURI(self):
		path = io.path(self.path)
		return sqlite.sqliteURIFromPath(str(path if path.absolute else io.here(path)))

	@property
	def noAccount(self):
		return self._flags & DBFLAG_NOACCOUNT


	def __setitem__(self, item, value):
		raise NotImplementedError('Operation not permitted')

	def __getitem__(self, name):
		return self._tables[name]

	def __getattr__(self, name):
		try: return object.__getattribute__(self, name)
		except AttributeError as e:
			try: return self[name]
			except KeyError:
				raise e

	def _calculateSize(self):
		return sum(table.size for table in self._tables.values())

	@property
	def size(self):
		try: return self._size
		except AttributeError:
			self._size = size = self._calculateSize()
			return size

	@size.deleter
	def size(self):
		try: del self._size
		except AttributeError:
			pass

	# def _memoryChange(self, table, entity, new, old):
	# 	pass


	def _createTables(self):
		# note: this isn't used because tables are created during class initialization.
		for table in self.values():
			if isinstance(table, self.Table):
				createSqlTable(table._tableClass)
				createSqlTable(table._accountingTable)


	# todo: make private?
	class Table(writeprotected):
		# __public_members__ = ['name']

		__name__ = 'table'

		def __init__(self, name, columns):
			self._name = name
			self._definition = columns

			self._checkColumnObjectNames()

		def __repr__(self):
			return f'<table {self._name}>'

		@classmethod
		def _accounting_definition(self, sqlmeta):
			# Load sqlobject and def at runtime.
			from sqlobject import IntCol
			return dict(object = IntCol(),
		                size = IntCol(),
		                sqlmeta = sqlmeta)

		@property
		def name(self):
			return self._name

		@property
		def database(self):
			return self._database

		def _set_database(self, db):
			# print string.call('newClassObject', name, (sqlite.Object,), **cfg)
			# from sqlite.module.classregistry import registry
			# registry(db.name)

			assert isinstance(db, VariableDB)
			self._database = db

			noAcct = db.noAccount

			class sqlmeta:
				registry = db.name
				lazyUpdate = True

			cfg = dict(self._definition, sqlmeta = sqlmeta)

			# XXX When calling from the native interface, the cfg will have objects
			# of class VariableDBNativeTool._Column which would make this code wrong.
			# But when built from the structural 'table' function defined below, it
			# builds the _columnClass for the type per column name, out of the Open
			# call connecting database, which is the right level for sqlobject.
			self._tableClass = buildSqlObject(self.name, db.name, cfg)

			if not noAcct:
				self._accountingTable = buildSqlObject \
					('%s_acct' % self.name, db.name,
					 self._accounting_definition(sqlmeta))

			self._tableClass._connection = db._db
			if not noAcct:
				self._accountingTable._connection = db._db

			createSqlTable(self._tableClass)
			if not noAcct:
				createSqlTable(self._accountingTable)

		def _calculateSize(self):
			return sum(row.size for row in self._accountingTable.select())

		@property
		def size(self):
			try: return self._size
			except AttributeError:
				self._size = size = self._calculateSize()
				return size

		@size.deleter
		def size(self):
			try: del self._size
			except AttributeError:
				pass

			del self._database.size

		@property
		def _columnNames(self):
			return (n for (n, c) in self._definition)

		def _checkColumnObjectNames(self):
			if any(n.startswith('_') for n in self._columnNames):
				raise AttributeError('Column names cannot start with undescore')

		@property
		def _writables(self):
			return list(self._columnNames)

		@property
		def columns(self):
			return vmCurrentTask().sequence(self._columnNames)

		def columnType(self, name):
			pass # return self._definition[name]

		def __call__(self, *args):
			# runtime.call.System.Engine.IO(args)
			# debugOn()
			return self._Entity(self, values = self._toKeywordColumns(args))

		def _toKeywordColumns(self, values):
			from sqlobject import DateTimeCol

			row = dict()

			d = self._definition
			for i in range(len(d)):
				(n, c) = d[i]
				v = values[i]

				if isinstance(v, baseStringClass):
					v = str(v)

				# Inline internal column value data type conversion(s).
				if isinstance(c, DateTimeCol):
					if not isinstance(v, float):
						raise TypeError('Column #%d %r value needs to be a float for datetime conversion' % \
									    (i, n))

					v = datetime.fromtimestamp(v)

				row[n] = v

			return row


		# Querying.
		# Todo: cursors
		def get(self, column, value):
			# Select individual entity wrapped row.
			column = baseStringClass._asString(column)
			if isinstance(value, str):
				value = baseStringClass._asString(value)

			return vmCurrentTask().sequence \
				(self._Entity(self, row = e)
				 for e in self._tableClass.selectBy \
					(**{column: value}))

		def get(self, column, value):
			return self.query({column: value})

		def all(self):
			# Return native object query set.
			return vmCurrentTask().sequence \
				(self._Entity(self, row = e)
				 for e in self._tableClass.select())

		def query(self, criteria):
			asString = baseStringClass._asString
			def asStringIf(v):
				if isinstance(v, str):
					return asString(v)

				return v

			criteria = dict((asString(name), asStringIf(value))
				            for (name, value) in criteria.items())

			return vmCurrentTask().sequence \
				(self._Entity(self, row = e)
				 for e in self._tableClass.selectBy(**criteria))


		# Migrations.
		# todo: emit underlying alter table sql commands to migrate the database.
		# todo: recreate the underlying sqlobject table class by deregistering
		# it with the class registry first.
		def addColumn(self, name, type):
			pass
		def removeColumn(self, name):
			pass

		def addColumns(self, *columns):
			# Add multiple columns, specified with 2-tuples (or sequences) of
			# name and type.
			pass
		def removeColumns(self, *columns):
			# Remove multiple columns by name.
			pass


		class _Entity(writeprotected):
			def __init__(self, table, row = None, values = None):
				self._table = table
				self._row = row
				self._values = values
				self.__public_members__ = table._writables

			# todo: do column set based on row information.
			# def __setattr__(self, name, value):
			# 	pass

			@property
			def id(self):
				return getattr(self._row, 'id', None)

			def __repr__(self):
				if self._row is None:
					return f'<{self._table._name} {self._values}>'

				return f'<{self._table._name} {self._row}>'

			def __getattr__(self, name):
				try: return object.__getattribute__(self, name)
				except AttributeError as e:
					try: return self.getValue(name)
					except KeyError:
						raise e

			@property
			def _columnNames(self):
				return (n for (n, c) in self._table._definition)

			@property
			def _dataItems(self):
				v = self._values
				if v is None:
					return ((n, getattr(self, n)) for n in self._columnNames)

				return ((n, v[n]) for n in self._columnNames)

			def getValue(self, name):
				if self._row is None:
					return self._values[name]

				if any(name == n for (n, c) in self._table._definition):
					return getattr(self._row, name)

				raise AttributeError(name)

			def _getColumnValues(self):
				return [v for (n, v) in self._dataItems]

			def _saveNoAccount(self):
				if self._row is None:
					self._row = self._table._tableClass(**self._values) # insert

				else:
					self._row.sync()

				return self


			def save(self):
				if self._table._database.noAccount:
					return self._saveNoAccount()

				def sizeOf(v):
					if isinstance(v, str):
						return len(v)

					return 4 # or 8?

				def insertAcct(size):
					acct = self._table._accountingTable(object = self._row.id,
						                                size = size)
					acct.sync()
					del self._table.size

					return acct

				def checkInsert(size, r):
					# Check for quota boundaries.
					m = self._table._database.size + size
					if m > r:
						raise IndexError('%s > %s' % (m, r))


				size = sum(sizeOf(v) for v in self._getColumnValues())

				if self._row is None:
					r = self._table._database._hard
					if r >= 0:
						checkInsert(size, r)

					self._row = self._table._tableClass(**self._values) # insert
					insertAcct(size)

				else:
					# Check for quota boundaries.
					r = self._table._database._hard
					if r >= 0:
						for acct in self._table._accountingTable.select(object = self._row.id):
							if acct.size != size:
								m = self._table._database.size + (size - acct.size)
								if m > r:
									raise IndexError('%s > %s' % (m, r))

								acct.size = size
								acct.sync()
								del self._table.size

							break
						else:
							# Catch not exist for upsert.
							checkInsert(size, r)
							insertAcct(size)

					self._row.sync()

				return self

	@classmethod
	def _InstallNative(self, core):
		path = configuration.AgentSystem.variable_database or 'components/services/database'
		core.newToolConfig(package = VariableDBNativeTool(core, self),
						   path = path)


# def table(name, **cfg):
#     return newClass(name, (sqlite.Object,) **value)

# used?
vardb = VariableDB._Open
createdb = VariableDB._Create

# table = VariableDB.Table

# vardb('basic', house = table('house', id = table.integer, guests = table.list)) \
#     .objects.house(id = 0, guests = [0]).sync()

def db(self, name, value, **kwd):
	from stuphos.language.document.interface import getContextEnvironment

	try: core = getContextEnvironment('libraryCore')
	except KeyError: core = None


	if isinstance(value, dict):
		'''
		storage(db):
			memory:
				data(table):
					- field: string

		'''

		try: memory = value['memory']
		except KeyError: pass
		else:
			if isinstance(memory, dict): # XXX and not isinstance(table)
				vmCurrentTask().checkAccessSystem(['system:database'], 'memory')

				hard = -1
				flags = 0

				return VariableDB(name, hard, flags, sqlite.memoryOpen(), **memory)


	# debugOn()
	# Todo: the full object name in the yaml spec isn't used: just the last spec'd name.
	# This should be folded into another context environment variable.
	try: path = getContextEnvironment('document')
	except KeyError:
		# Do not rely on vardb
		raise RuntimeError('No document context to obtain configuration')

	else: name = '%s/%s' % ('/'.join(path), name)

	return vardb(core, name, **value)

def table(self, name, value, **kwd):
	def buildColumn(c):
		if len(c) != 1:
			raise ValueError('Column must have one key-value pair.')

		(name, type) = list(c.items())[0]
		c = VariableDBNativeTool._columns[type]._columnClass(name)
		return (c.name, c)

	name = name.replace('$', '_').replace('@', '_').replace('.', '_').replace('-', '_').replace('%', '_')
	# name = re.sub(r'(\$|\@|\.|\-|\%)', '_', name)

	assert not name.endswith('_acct'), NameError('Table name %r must not end in _acct' % name)
	assert isinstance(value, list)
	cols = [buildColumn(c) for c in value]
	return VariableDB.Table(name, cols)

installVariableDatabaseNativeTool = VariableDB._InstallNative
