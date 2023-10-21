# SQLite incorporation.
# from op.runtime import Object, Object as CommonObject, Wrapper
# from op.runtime.virtual.objects import mutateObject, mutateNamespace, ObjectDictionaryProxy
# from op.runtime.core import MemorizedProperty
# from op.runtime.layer.etc import apply

from contextlib import contextmanager
from urllib.parse import urlencode

__all__ = ['sqliteURIFromPath', 'SQLObject', 'connectToLocalURI', 'connectionForURI',
           'resetSQLObjectClasses', 'getRegisteredClass', 'SQLite']

try:
    import sqlobject as sqlobjectModule
    from sqlobject import SQLObject, sqlmeta # , StringCol, PickleCol
    from sqlobject import classregistry, connectionForURI
    from sqlobject.dberrors import DuplicateEntryError
    from sqlobject.sqlbuilder import sqlrepr

    from sqlobject import version, version_info as versionInfo

except ImportError:
    sqlobject = False

    ##    class EntryClass: # ():
    ##        # return failure
    ##        raise NotImplementedError

    def sqlrepr(*args, **kwd):
        raise NotImplementedError('sqlrepr')

    class sqlmeta:
        pass

    DuplicateEntryError = None

    SQLObject = None
    version = None
    versionInfo = None

    from op.runtime.core import notImplemented

    def sqliteURIFromPathXPlatform(*args, **kwd):
        return notImplemented('sqliteURIFromPathXPlatform') # , *args, **kwd)
    def sqliteURIFromPath(*args, **kwd):
        return notImplemented('sqliteURIFromPathXPlatform') # , *args, **kwd)
    def connectToLocalURI(*args, **kwd):
        return notImplemented('sqliteURIFromPathXPlatform') # , *args, **kwd)
    def resetSQLObjectClasses(*args, **kwd):
        return notImplemented('sqliteURIFromPathXPlatform') # , *args, **kwd)
    def getRegisteredClass(*args, **kwd):
        return notImplemented('sqliteURIFromPathXPlatform') # , *args, **kwd)

    def connectionForURI(*args, **kwd):
        return notImplemented('connectionForURI') # , *args, **kwd)

else:
    sqlobject = True

    # from .storage import sqliteURIFromPath as sqliteURIFromPathXPlatform
    import sys

    # def urlPathFromUrlString(string):
    #     string = string[5:]
    #     ##    if string[:2] == '//' and string[3:4] == ':':
    #     ##        return string[:3] + string[4:]

    #     return string

    # def toUrlPath(path):
    #     return urlPathFromUrlString(path.urlString)

    # def sqliteURIFromPath(path, toUrlPath = toUrlPath):
    #     return 'sqlite:/' + (':memory:' if path is None \
    #                          else toUrlPath(path))

    def sqliteURIFromPath(path):
        if sys.platform == 'win32':
            return 'sqlite:///' + str(path)

        elif sys.platform == 'cygwin' or sys.platform.startswith('linux'):
            return 'sqlite://' + str(path)

        raise NotImplementedError(sys.platform)
        ##    path = list(io.path(path).parts)
        ##
        ##    if system.core.platform == 'win32':
        ##        path[0] = path[0].letter
        ##    # what about other platforms?
        ##
        ##    return 'sqlite:///' + path[0] + '/' + '/'.join(path[1:])

    # sqliteURIFromPath = sqliteURIFromPathXPlatform

    def connectToLocalURI(path):
        return connectionForURI(sqliteURIFromPath(path))

    def resetSQLObjectClasses(*classNames):
        # SQLiteConnection(dbconnection.DBConnection).__init__ does:
        #     classregistry.registry(self.registry).addCallback(self.soClassAdded)
        # Which binds each newly created model (SQLObject) by its __name__ as a ConnWrapper
        #   to the DBConnection instance, (cached, presumably).
        # The connectionFromURI opener manager also registers each connection/builder type
        #   instance a la cache, so just reloading the dbconnection/.sqliteconnection modules
        #   won't kill the attributes from what's used..  Specifically, because the classregistry
        #   callbacks registered with these instance constructors are for 'genericCallbacks',
        #   which persist even when the individual entry from the registry is removed.
        #
        #   registerConnectionInstance(self)
        #
        # Otherwise, this would be sufficient:
        #   del classregistry.MasterRegistry.registries[None].classes['Entry']


        # The trick should be to clear the dbconnection instance cache registration first:
        #   reload(sqlobject.dbconnection)
        #   reload(sqlobject.sqlite.sqliteconnection)
        # Then:
        #   reload(sqlobject.classregistry)
        # to reset all registry callback cache.

        # Try to do this 'surgically'. This is actually more complicated, too, because
        # the registries have to correspond with each individual (SQLObject-derived).sqlmeta.registry
        # configuration.
        registryClasses = classregistry.MasterRegistry.registry(None).classes # .registries[None].classes

        for name in classNames:
            try: del registryClasses[name]
            except KeyError:
                pass

        # Fortunately, models shouldn't change in runtime much!  (So how much time should be
        # devoted to it... that we just restart whole interpreter session)

    def getRegisteredClass(name, registry = None): # default registry
        return classregistry.registry(registry).classes[name]


def dropAll(connection, *tables):
    for t in tables:
        t.dropTable(connection = connection)

if 0:
    # uh, op.runtime.virtual.objects?
    @contextmanager
    def _mutation(object, **changes):
        old = dict()

        for name in iterkeys(changes):
            try: old[name] = getattr(object, name)
            except AttributeError:
                pass

        try:
            for (name, value) in iteritems(changes):
                setattr(object, name, value)

            yield

        finally:
            for (name, value) in iteritems(old):
                setattr(object, name, value)

    _mutation = mutateObject

else:
    @contextmanager
    def _mutateNamespace(ns, **changes):
        previous = dict()
        deletes = []

        for n in changes.keys():
            # This algorithm is specific, because we know we're
            # operating with the thread-local-enabled sqlhub, that
            # relies on properties to operate its namespace: in
            # this case, even with the obj-dict-proxy, we still
            # need to cater.
            #
            # Todo: rewrite this entirely.

            try: previous[n] = ns[n]
            except (KeyError, AttributeError):
                deletes.append(n)

        ns.update(changes)

        try: yield ns
        finally:
            ns.update(previous)
            for n in deletes:
                try: del ns[n]
                except KeyError: # AttributeError??
                    pass

    def _mutation(object, **changes):
        return _mutateNamespace(ObjectDictionaryProxy \
                                (object), **changes)

@contextmanager
def transactionalContext(connection, hub = False):
    t = connection.transaction()
    # t.begin()

    if hub:
        with _mutation(hub, threadConnection = connection):
            try: yield t
            except:
                #(etype, value, tb) = system.lastException.system()
                t.rollback()

                raise #etype, value, tb
            else:
                t.commit(close = True)
    else:
        try: yield t
        except:
            #(etype, value, tb) = system.lastException.system()
            t.rollback()

            raise #etype, value, tb
        else:
            t.commit(close = True)

    # initOf(col.SOCol):
    ##    name,
    ##    soClass,
    ##    creationOrder,
    ##    dbName=None,
    ##    default=NoDefault,
    ##    defaultSQL=None,
    ##    foreignKey=None,
    ##    alternateID=False,
    ##    alternateMethodName=None,
    ##    constraints=None,
    ##    notNull=NoDefault,
    ##    notNone=NoDefault,
    ##    unique=NoDefault,
    ##    sqlType=None,
    ##    columnDef=None,
    ##    validator=None,
    ##    validator2=None,
    ##    immutable=False,
    ##    cascade=None,
    ##    lazy=False,
    ##    noCache=False,
    ##    forceDBName=False,
    ##    title=None,
    ##    tags=[],
    ##    origName=None,
    ##    extra_vars=None


# From June 26th 2014
# from op.runtime import Object

# todo:
class Object:
    pass
CommonObject = Object

class Wrapper(object):
    def __init__(self, wrapped):
        self.__original = wrapped
        self.__original__ = wrapped # hmm, this becomes not name-mangled.

    def __getattr__(self, name):
        # todo: special attribute, descriptor, class member emulate, etc.
        try: return object.__getattribute__(self, name)
        except AttributeError:
            return getattr(Wrapper.Original(self), name)

    @classmethod
    def Original(self, wrapping):
        return wrapping.__dict__['_Wrapper__original']


class baseSchema(Object, list):
    @classmethod
    def FromSyntax(self, type, name, columns, flags):
        return self(type, name, columns, flags)

    def __init__(self, type, name, columns, flags):
        list.__init__(self, columns)
        self.type = type
        self.name = name
        self.flags = flags

    def getAttributeString(self):
        return '%s %s (%d columns)' % (self.type, self.name,
                                       len(self))

    class Column(Object, list):
        def __init__(self, name, type, constraints):
            list.__init__(self, constraints)
            self.name = name
            self.type = type

        def getAttributeString(self):
            return '%s %s (%d constraints)' % \
                   (self.type, self.name, len(self))

        def __str__(self):
            c = [self.name]
            if self.type:
                c.append(self.type)

            return ' '.join(c + list(self))

    def columnObject(self, name, constraints = []):
        type = None
        if constraints:
            type = constraints[0]
            del constraints[0]

        return self.Column(name, type, constraints)

    @property
    def columnNames(self):
        return (n for (n, constraints) in
                list.__iter__(self))

    def __getitem__(self, name):
        if isinstance(name, int):
            return self.columnObject(*list.__getitem__(self, name))

        for (n, constraints) in list.__iter__(self):
            if n == name:
                return self.columnObject(n, constraints)

        raise KeyError(name)

    def __iter__(self):
        return (self.columnObject(*n) for n
                in list.__iter__(self))


@listing
def parseColumns(columns):
    for c in columns:
        c = c.split()
        yield (c[0], c[1:])

def parseSQL(source, schemaClass = baseSchema):
    i = source.find('(')
    if i >= 0:
        e = source.rfind(')')
        assert e > 0

        columns = source[i+1:e]
        # source = source[:i] + ' ' + source[e+1:]
    else:
        columns = ''

    # source = source.split()
    columns = parseColumns(columns.split(','))

    return schemaClass.FromSyntax(None, None, columns, None)

def explain(c, sql, w = 30):
    def shorten(x):
        x = str(x).replace('\n', '')
        return x[:w] if x > w else x

    for r in list(c.execute('explain %s' % sql)):
        yield list(map(shorten, r))

class baseSQLiteMaster(Object):
    @property
    def parsedSQL(self):
        if self.sql:
            return parseSQL(self.sql, schemaClass = self.Schema)
    schema = parsedSQL

    class Schema(baseSchema):
        pass

    @listing
    def explain(self, c, *args, **kwd):
        return explain(c, self.getCreationSQL(), *args, **kwd)

    class baseSQLiteMasterList(Object, list):
        def explain(self, c):
            for t in self:
                if t.type == 'table': # hack
                    yield (t, t.explain(c))

        @nling
        def fullExplanation(self, c):
            for (t, e) in self.explain(c):
                yield '%s:' % t.getObjectName()
                yield ''
                yield indent(string.table(e))
                yield ''


def objectUpdate(o, x):
    # Ass
    for (n, v) in iteritems(x):
        setattr(o, n, v)


@builtin.As(alias = 'sqliteMaster')
class relSQLiteMasterList(baseSQLiteMaster.baseSQLiteMasterList):
    @classmethod
    def FromConnection(self, c, dbName = None):
        return self.FromResults(c.execute \
            ('select * from %ssqlite_master' % \
             ((dbName + '.') if dbName else '')))

    @classmethod
    def FromResults(self, results):
        return self(mapi(self.relSQLiteMasterTable.FromRow, results))

    def getAttributeString(self):
        return '%d tables' % len(self)

    @property
    @nling
    def summary(self):
        for t in self:
            yield t.getAttributeString()
        yield ''

    @nling
    def __str__(self):
        return nls(mapi(str, self))

    # @Object.Format('{type} {name} (over {tbl_name}) [#{rootpage}]')
    class relSQLiteMasterTable(baseSQLiteMaster):
        @classmethod
        def FromRow(self, row):
            return self(*row)

        def __init__(self, type, name, tbl_name, rootpage, sql):
            self.type = type
            self.name = name
            self.tbl_name = tbl_name
            self.rootpage = rootpage
            self.sql = sql

        def getCreationSQL(self):
            return str(self)
        def getObjectName(self):
            return '%s (%s)' % (self.name, self.type)

        @nling
        def __str__(self):
            yield 'CREATE %s %s' % (self.type, self.name)

            if self.name != self.tbl_name:
                yield '  ON ' + self.tbl_name

            s = self.schema
            if s is None:
                yield indent('();')
            else:
                yield indent('(')

                s = list(self.schema)
                e = len(s) - 1

                for (i, c) in enumerate(s):
                    c = str(c)

                    # XXX
                    if '(' in c:
                        yield indent(indent('XXXXX'))
                        break

                    if i < e:
                        c += ','

                    yield indent(indent(c))

                yield indent(');')


def evaluateSingularResult(r):
    r = list(r)

    if len(r) == 1:
        return r[0]
    if len(r):
        return r

# print x.lower(x.hex(str(x.randomblob(16)[0]))[0])[0]
# how 'random' this is is questionable


def toClassName(c):
    for i in ':/.-+':
        c = c.replace(i, '_')

    return camelize(*having(c.split('_')))


# ORM Base Class:
# from op.runtime import Object

class ORM: # (Object):
    @classmethod
    def BuildORM(self):
        building = access(system.access, *self.REGISTRATION.split('::'))

        try: return building(self._initializeOrm)
        # except ValueError:
        except Exception:
            # Catch pre-built -- but no wait! we have no
            # local definition then to return -- so assert
            # that this object model be installed.
            raise

    def __init__(self, connection = None):
        if connection is None:
            connection = sqlite.newMemory

        self.orm = self.BuildORM()
        self.setupConnection(connection)

        self._createTables()

    def setupConnection(self, connection):
        self.connection = connection

    def _createTables(self):
        with self.connection.hub:
            for t in dictOf(self.orm).values():
                try: create = t.createTable
                except AttributeError: pass
                else: create(ifNotExists = True)

    def _dropAllTables(self):
        with self.connection.hub:
            for t in dictOf(self.orm).values():
                try: drop = t.dropTable
                except AttributeError: pass
                else: drop()

    def _recreateTables(self):
        self._dropAllTables()
        self._createTables()


# @builtin.As(alias = 'sqlite')
#@apply
#@attributeOf.Initialize
class SQLite(Object):
    module = sqlobject and sqlobjectModule

    Object = SQLObject # Might be None
    version = version # Might be None
    versionInfo = versionInfo # Might be None

    # col, index, joins, main, styles
    # sqlbuilder, dbconnection, dberrors

    @classmethod
    def Initialize(self):
        if self.module is not False:
            for name in ['col', 'index', 'joins', 'main', 'styles']:
                __import__('%s.%s' % (self.module.__name__, name))

                # Merge all.
                try: m = getattr(self.module, name)
                except AttributeError:
                    pass # print name
                else:
                    for n in m.__all__:
                        setattr(self, n, getattr(m, n))

        return self()

    DuplicateEntryError = DuplicateEntryError

    sqliteURIFromPath = staticmethod(sqliteURIFromPath)
    connectToLocalURI = staticmethod(connectToLocalURI)
    connectionForURI = staticmethod(connectionForURI)
    resetSQLObjectClasses = staticmethod(resetSQLObjectClasses)
    getRegisteredClass = staticmethod(getRegisteredClass)

    repr = sqlrepr = staticmethod(sqlrepr)

    def getAttributeString(self):
        return '%s.%s.%s (%s r%s)' % self.versionInfo

    transactionalContext = staticmethod(transactionalContext)
    dropAll = staticmethod(dropAll)

    @property
    def hub(self):
        from sqlobject import sqlhub
        return sqlhub

    def threadHub(self, conn):
        return _mutation(self.hub, threadConnection = conn)

    def threadTransaction(self, conn):
        return transactionalContext(conn, self.hub)

    master = sqliteMaster
    ORM = ORM

    # @CommonObject.Format('{connection}')
    class SQLiteCall(CommonObject):
        @classmethod
        def Call(self, conn, name, *args):
            return evaluateSingularResult(conn.execute('SELECT %s' % string.call(name, *args)))

        def __init__(self, conn):
            self.connection = conn
        def __getattr__(self, name):
            return curry(self.Call, self.connection,
                         name)

    call = SQLiteCall.Call
    caller = SQLiteCall

    @classmethod
    def pragma(self, conn, name, evaluate = False):
        r = conn.execute('PRAGMA %s' % name)
        if evaluate:
            r = evaluateSingularResult # (r)?

        return r

    def pragmaOver(self, conn):
        return curry(self.pragma, conn)
    def pragmaOn(self, conn):
        return attributable(self.pragmaOver(conn))

    ##    pragma.over = pragmaOver
    ##    pragma.on = pragmaOn

    MEMORY_URI = 'sqlite::memory:'

    def memoryOpen(self, *args, **kwd):
        uri = self.MEMORY_URI
        if kwd:
            uri = '%s?%s' % (uri, urlencode(kwd))

        return self.Connection(self.connectionForURI(uri)) \
               .attachSequence(*args)

    newMemory = property(memoryOpen)

    def memoryAttach(self, *args, **kwd):
        return self.memoryOpen(*args).attachSequence(**kwd)

    def pathOpen(self, path):
        return self.Connection(self.connectToLocalURI \
                               (io.path(path)))

    @property
    def defined(self):
        @attributable
        def getDefined(name):
            return self.module.classregistry.registry(None).getClass(name)

        return getDefined

    class Connection(Wrapper):
        def getAttributeString(self):
            return self.filename

        #@property
        # @MemorizedProperty.Decorator # for user registrations
        #                              # of course, this is trash
        #                              # logic for multithreading
        def sqlite3Connection(self, ignore):
            # This relies on (sqlobject.sqlite.sqliteconnection)
            # .makeConnection, which nearly always calls a new
            # sqlite3.connect on the target, so user callback
            # registrations are not carried over.
            # todo: Refer to connection-object caching in pysqlite
            return self.getConnection()
        @property
        def sqlobjectConnection(self):
            return self.Original(self)

        def masterOver(self, *args, **kwd):
            return SQLite.master.FromConnection \
                   (self.sqlite3Connection,
                    *args, **kwd)

        master = property(masterOver)

        @property
        def masterOf(self):
            return attributable(self.masterOver)

        @property
        def pragma(self):
            return SQLite.pragmaOn(self.sqlite3Connection)

        def attach(self, path, name):
            path = str(path)
            path = path.replace('\\', '/')
            path = sqlrepr(path, 'sqlite')
            name = sqlrepr(name, 'sqlite')

            ##    self.sqlite3Connection.execute \
            ##        ('attach %s as %s' % (path, name))

            sql = 'attach %s as %s' % (path, name)
            # print sql

            eat(self.sqlite3Connection.execute(sql))

        def detach(self, name):
            # print(f'detaching db {name} ({sqlrepr(name, "sqlite")})')

            eat(self.sqlite3Connection.execute \
                ('detach %s' % sqlrepr(name, 'sqlite')))

        def detachAll(self):
            # debugOn()
            for at in self.attachments:
                if at.name != 'main':
                    self.detach(at.name)

        # XXX Exception TypeError: "'int' object is not iterable" in
        #   <bound method Connection.detachAll of <Connection :memory:>>
        #    ignored
        __del__ = detachAll

        def attachSequence(self, *args, **kwd):
            for (path, name) in args:
                self.attach(path, name)
            for (name, path) in iteritems(kwd):
                self.attach(path, name)

            return self

        def newTemporary(self, name):
            return self.attach('', name)

        @property
        def attachments(self):
            return [self.Attachment(self, at)
                    for at in SQLite.pragma \
                        (self.sqlite3Connection,
                         'database_list',
                         evaluate = False)]
            # return self.pragma.database_list

        # @Object.Format('[#{id}] {name} -> {path} / {conn}')
        class Attachment(Object):
            def __init__(self, conn, xxx_todo_changeme):
                (id, name, path) = xxx_todo_changeme
                self.conn = conn
                self.id = id
                self.name = name
                self.path = path

            @property
            def master(self):
                return self.conn.masterOver \
                       (self.name)

        def query(self, statement, *args, **kwd):
            return self.ResultSet(self.sqlite3Connection.execute \
                                  (statement, *args, **kwd))

        @property
        @contextmanager
        def queryable(self):
            def resultsQuery(*args, **kwd):
                return self.ResultSet(*args, **kwd)

            with self.transaction:
                yield resultsQuery

        class ResultSet(Object, list):
            def __str__(self):
                return string.table(self)

        class basicSqlMeta(sqlmeta):
            fromDatabase = True

        @property
        def transaction(self):
            return SQLite.threadTransaction(self.Original(self))
        @property
        def hub(self):
            return SQLite.threadHub(self.Original(self))

        def autoCreate(self, className, tableName = None, **kwd):
            o = self.Original(self)

            try: c = o._autoCreate_cache
            except AttributeError:
                c = o._autoCreate_cache = dict()

            try: return c[(className, tableName)]
            except KeyError:
                pass

            # todo: pass db name..
            with self.transaction:
                # XXX Obviously heavily problematic with more custom tables,
                # which is what **kwd is for.
                sqlmeta = create.type('sqlmeta', self.basicSqlMeta)

                # !!! What about auto 'oid'?
                # This should pretty much work for most tables!

                ##    sqlmeta.idName = 'oid'
                ##    args['oid'] = sqlite.IntCol(alternateID = True)

                metaOverride = kwd.pop('metaOverride', None)

                args = dict(kwd)

                if callable(metaOverride):
                    x = metaOverride(sqlmeta)
                    if x is not None:
                        sqlmeta = x

                elif isinstance(metaOverride, dict):
                    ##    from binascii import hexlify
                    ##
                    ##    def encodeID(n):
                    ##        return int(hexlify(n), 16)
                    ##
                    ##    overrideSqlMeta = dict(idName = 'name', idType = staticmethod(encodeID))

                    objectUpdate(sqlmeta, metaOverride)

                args['sqlmeta'] = sqlmeta

                if tableName:
                    sqlmeta.table = tableName

                t = create.type(className, SQLite.Object, **args)
                c[(className, tableName)] = t

                return t

        @property
        def autoTable(self):
            return attributable(self.autoCreate)

        def masterAutoTablesWith(self, master):
            def _():
                for r in master:
                    name = toClassName(r.name)
                    yield (name, catch(self.autoCreate, name,
                                       tableName = '"%s"' % \
                                       r.name))

            with self.transaction:
                return namespace(_())

        @property
        def masterAutoTables(self):
            return self.masterAutoTablesWith(self.master)

builtin(sqlite = SQLite.Initialize())


# @system.access.SQLite.Master.ORM
def SQLiteMasterORM():
    if sqlobject is False:
        SQLiteMaster = None
    else:
        try:
            class SQLiteMaster(SQLite.Object):
                class sqlmeta:
                    table = 'sqlite_master'

                # XXX need to reassign primary key, alternateID not enough?
                type = SQLite.StringCol()
                name = SQLite.StringCol(alternateID = True, unique = True)
                tbl_name = SQLite.StringCol()
                rootpage = SQLite.IntCol()
                sql = SQLite.StringCol()

        except ValueError: # Already in registry.
            pass

    return synthetic(locals())
