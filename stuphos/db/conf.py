# Database connection configuration service.
#
from contextlib import contextmanager
import json

class ConfigurationError(ValueError):
	pass

class DBCore(dict):
	'''
	[DBCore]
	primary.type = pg-auth
	primary.path = db.conf
	primary.host = 127.0.0.1
	primary.port = 5432
	secondary.type = sqlite
	secondary.path = sqlite:/etc/db.sqlite

	'''

	class PGAuthConfiguration:
		ENGINE = 'django.db.backends.postgresql_psycopg2'

		DEFAULT_PG_HOST = 'localhost' # '127.0.0.1'
		DEFAULT_PG_PORT = 5432

		def __init__(self, **kwd):
			self.path = kwd['path'] # assert exists
			self.host = kwd.get('host') #, self.DEFAULT_PG_HOST)
			self.port = kwd.get('port') #, self.DEFAULT_PG_PORT)

		@property
		def connectionString(self):
			if self.host or isinstance(self.port, int) or \
			    isinstance(self.port, str) and self.port.isdigit():
				return buildPGINetConnectionURIAuto \
                                    (authfile = self.path,
                                     port = self.port,
                                     host = self.host)

			return buildPGLocalConnectionURIAuto(authfile = self.path)

		@property
		def djangoDatabaseConfig(self):
			(dbName, username, password) = readPGAuthAuto(self.path)

			cfg = {'NAME': dbName,
			       'ENGINE': self.ENGINE,
			       'USER': username,
			       'PASSWORD': password}

			if self.host or isinstance(self.port, int) or \
			   isinstance(self.port, str) and self.port.isdigit():
			    cfg['HOST'] = self.host or self.DEFAULT_PG_HOST
			    cfg['PORT'] = int(self.port)

			return cfg

		@property
		def fields(self):
			return dict(path = self.path,
						host = self.host,
						port = self.port)

	class SqliteConfiguration:
		ENGINE = 'django.db.backends.sqlite3'

		def relative_path(self, path):
			if not self.rootpath:
				return path
				raise ValueError('Cannot get relative path because no root-path is configured!')

			return path.format(root = self.rootpath)

		def __init__(self, **fields):
			self.rootpath = fields.get('root-path')
			self.filepath = fields.get('file-path')

			try: self.path = fields['path']
			except KeyError:
				if self.filepath is None:
					raise ConfigurationError('Sqlite databases must define at least file-path')

				self.path = f'{fields.get("protocol", "sqlite:")}{self.filepath}'

		@property
		def connectionString(self):
			return self.relative_path(self.path)

		@property
		def djangoDatabaseConfig(self):
			return dict(NAME = self.filepath,
				        ENGINE = self.ENGINE,
				        USER = '',
				        PASSWORD = '')

		@property
		def fields(self):
			# Q How is this used and should we include self.rootpath?
			return dict(path = self.path,
						filepath = self.filepath)

	ConfigurationTypes = {'pg-auth': PGAuthConfiguration,
						  'pg': PGAuthConfiguration,
						  'postgres': PGAuthConfiguration,
						  'sqlite': SqliteConfiguration}

	def buildConfiguration(self, **fields):
		config = self.ConfigurationTypes[fields['type']]
		return config(**fields)

	def installConfiguration(self, name, **fields):
		cfg = self[name] = self.buildConfiguration(**fields)
		return cfg

	@classmethod
	def Load(self, section = 'DBCore'):
		# This is here for running web migrate --resync-db
		#import pdb; pdb.set_trace()

		from stuphos import getSection
		cfg = getSection(section)
		assert cfg is not None

		dbs = dict()

		for o in cfg.options():
			(name, field) = o.split('.', 1)
			d = dbs.setdefault(name, dict())
			d[field] = cfg.get(o)

		return self.LoadFromDBConfig(dbs)

	@classmethod
	def LoadFromDBConfig(self, dbs):
		# Validate while building.
		core = self()
		for (name, fields) in dbs.items():
			core.installConfiguration(name, **fields)

		return core

	def InitializeForThread(self, name = None):
	    self.hub.threadConnection = None if name is None else self.getConnection(name)
	def InitializeForProcess(self, name = None):
	    self.hub.processConnection = None if name is None else self.getConnection(name)

	@property
	def hub(self):
	    from sqlobject import sqlhub
	    return sqlhub


	class ConnectionDescriptor:
		def __init__(self, connectString):
			self.connectString = connectString

		def __call__(self):
			return self.connectString


	def getConnection(self, name):
		if isinstance(name, self.ConnectionDescriptor):
			connect = name()
		else:
			connect = self[name].connectionString

		from sqlobject import connectionForURI
		return connectionForURI(connect)

	def getDjangoDatabaseConfig(self, name):
	   	return self[name].djangoDatabaseConfig

	@contextmanager
	def hubThread(self, name):
		hub = self.hub
		try: prev = hub.threadConnection
		except AttributeError: prev = None

		conn = hub.threadConnection = self.getConnection(name)

		try: yield conn
		finally:
			hub.threadConnection = prev

	@contextmanager
	def hubProcess(self, name):
		hub = self.hub
		try: prev = hub.processConnection
		except AttributeError: prev = None

		conn = hub.processConnection = self.getConnection(name)

		try: yield conn
		finally:
			hub.processConnection = prev

class DynamicDBCore(DBCore):
	@classmethod
	def Load(self, master, masterNamespace = 'primary'):
		return self(master, masterNamespace)

	def __init__(self, master, masterNamespace):
		self.master = master
		self.masterNamespace = masterNamespace

	def loadConfig(self, name):
		from .orm import DBConf

		with master.hubThread(self.masterNamespace):
			for cfg in DBConf.selectBy(name = name):
				return self.buildConfiguration(**json.loads(cfg.fields))

	def saveConfig(self, name, cfg):
		from .orm import DBConf

		with master.hubThread(self.masterNamespace):
			DBConf(name = name, fields = json.dumps(cfg.fields)).save()


# PG
def readPGAuthAuto(authfile):
    # Get the configuration from file.
    with open(authfile) as dbConf:
        dbName = dbConf.readline().strip()
        username = dbConf.readline().strip()
        password = dbConf.readline().strip()

    return (dbName, username, password)

def buildPGLocalConnectionURIAuto(authfile):
    (dbName, username, password) = readPGAuthAuto(authfile)

    return 'postgres://{username}:{password}@/{database}'.format \
           (username = username, password = password, database = dbName)

def buildPGINetConnectionURIAuto(authfile, port = None, host = None):
    (dbName, username, password) = readPGAuthAuto(authfile)

    if port is None:
        port = DBCore.PGAuthConfiguration.DEFAULT_PG_PORT
    if host is None:
        host = DBCore.PGAuthConfiguration.DEFAULT_PG_HOST

    return 'postgres://{user}:{password}@{host}:{port}'.format \
           (user = username, password = password,
            host = host, port = port)

# XXX Get rid of this, if possible.  It should exist only in the runtime bootstrap.
from stuphos.runtime.registry import getRegistry
getRegistry(create = True)

# Instance.
dbCore = DBCore.Load()

def initDjangoDatabaseConfig(name):
    # A bootstrapped method for obtaining database config.
    # from stuphos.runtime.registry import getRegistry
    # getRegistry(create = True)

    return dbCore.getDjangoDatabaseConfig(name)

# dynamic_dbCore = DynamicDBCore.Load(dbCore)
