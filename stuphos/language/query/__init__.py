# Query Language.
try:
    from world import zone as ZoneTable
    from world import room as RoomTable
    from world import mobile as MobileInstanceTable
    from world import item as ItemInstanceTable
    from world import house as HouseTable
    from world import iterate_entities as IterateNativeEntities
    from world import command as CommandType

    NATIVE_TABLE_TYPES = [ZoneTable, RoomTable, MobileInstanceTable, ItemInstanceTable, HouseTable, CommandType]
    world = True

except (ImportError, NameError):
    NATIVE_TABLE_TYPES = []
    world = False

# Object Model.
class base(object):
    # Could be like, a runtime.Object
    @classmethod
    def isSubtype(self, type):
        try: return issubclass(type, self)
        except TypeError:
            return False

    @classmethod
    def isInstanceOf(self, instance):
        try: return self.isSubtype(instance.__class__)
        except AttributeError:
            return False

# Todo: fold native types into object model.
class TableType(base):
    pass

class MobilePrototypeTable(TableType):
    @classmethod
    def iterateRecords(self, callback):
        def iterateZoneMobilePrototypes(zone):
            for mobile in zone.mobiles:
                callback(mobile)

        IterateNativeEntities(ZoneTable, iterateZoneMobilePrototypes)

class ItemPrototypeTable(TableType):
    @classmethod
    def iterateRecords(self, callback):
        def iterateZoneItemPrototypes(zone):
            for item in zone.items:
                callback(item)

        IterateNativeEntities(ZoneTable, iterateZoneItemPrototypes)

class PlayerTable(TableType):
    @classmethod
    def iterateRecords(self, callback):
        pass

# Registered Table Types.
KNOWN_TABLE_TYPES = NATIVE_TABLE_TYPES
if world is not False:
    KNOWN_TABLE_TYPES += [MobilePrototypeTable, ItemPrototypeTable, PlayerTable]

    tableAliases = dict(zones = ZoneTable,
                        rooms = RoomTable,
                        mobiles = MobileInstanceTable,
                        items = ItemInstanceTable,
                        houses = HouseTable,

                        mobile_prototypes = MobilePrototypeTable,
                        item_prototypes = ItemPrototypeTable,
                        players = PlayerTable,

                        command = CommandType)

    tableAliases['prototypes.mobile'] = MobilePrototypeTable
    tableAliases['prototypes.item'] = ItemPrototypeTable
    tableAliases['instances.mobile'] = MobileInstanceTable
    tableAliases['instance.item'] = ItemInstanceTable

def getTable(object):
    if isinstance(object, str):
        return tableAliases.get(object.lower())
    if object in KNOWN_TABLE_TYPES:
        return object

    object = type(object)
    if object in KNOWN_TABLE_TYPES:
        return object

    raise TypeError(object)

def IterateRecords(table, callback):
    if table in NATIVE_TABLE_TYPES:
        return IterateNativeEntities(table, callback)
    if TableType.isSubtype(table):
        return table.iterateRecords(callback)

class Criteria(base, list):
    def __init__(self, *args, **kwd):
        self.extend(args)
        self.extend(iter(kwd.items()))
    def __add__(self, other):
        return Criteria(*(self + other))
    def __getitem__(self, item):
        for (name, value) in list(self.items()):
            if name == name:
                return value

    def __str__(self):
        return '\n'.join('%s: %r' % nv for nv in self)
    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__,
                           ' '.join('%s=%r' % nv for nv in self))

    @classmethod
    def Build(self, **kwd):
        return self(**kwd)

class NullType(object):
    def __repr__(self):
        return 'Null'
    def __str__(self):
        return ''

Null = NullType()

class Query(base):
    def __init__(self, *args, **criteria):
        self.criteria = Criteria(*args, **criteria)
        self.results = []

    def clear(self):
        del self.results[:]
        return self

    # Results:
    def __iter__(self):
        return iter(self.results)

    def __str__(self):
        return str(self.criteria)
    def __repr__(self):
        return '%s: %r' % (self.__class__.__name__, self.criteria)

class TableQuery(Query):
    def _queryTable(self, entity):
        # Todo: and/or
        for (field, clause) in self.criteria:
            try: value = getattr(entity, field)
            except (AttributeError, TypeError, ValueError):
                value = Null # Undefined

            try:
                if clause == value:
                    self.results.append(Result(self, entity, field, value))

            except TypeError:
                pass

    def select(self, *objects):
        # Joins?
        for table in objects:
            if Query.isInstanceOf(table):
                # Subquery.
                assert table is not self
                for result in table:
                    self._queryTable(result.entity)

            else:
                try: table = getTable(table)
                except TypeError: pass
                else: IterateRecords(table, self._queryTable)

        return self

    def fields(self):
        return set(r.field for r in self.results)
    def entities(self):
        return set(r.entity for r in self.results)
    def entityTypes(self):
        return set(type(r.entity) for r in self.results)
    def entitiesByType(self, search_type):
        return [r for r in self.results if type(r.entity) is search_type]
    def fieldsByType(self, search_type):
        return set(r.field for r in self.results if type(r.entity) is search_type)

class Result(base):
    def __init__(self, query, entity, field, value):
        self.query = query
        self.entity = entity
        self.field = field
        self.value = value

    def __repr__(self):
        # Q: should entity repr be r?
        return '%s: %r [%r on %s]' % (self.__class__.__name__,
                                      self.value, self.field,
                                      self.entity)

class Clause(base):
    def __init__(self, this):
        self.this = this
    def __repr__(self):
        return '%s: %r' % (self.__class__.__name__, self.this)

class Equals(Clause):
    def __eq__(self, value):
        return self.this == value

class NotEquals(Equals):
    def __eq__(self, value):
        return self.this != value

class Contains(Clause):
    def __eq__(self, value):
        return self.this in value

class ContainedBy(Clause):
    def __eq__(self, value):
        return value in self.this

class Like(Clause):
    import re
    def __init__(self, pattern):
        self.pattern = self.re.compile(pattern)
    def __eq__(self, value):
        return self.pattern.match(value) is not None
    def __repr__(self):
        return '%s: %s' % (self.__class__.__name__, self.pattern.pattern)

class GreaterThan(Clause):
    def __init__(self, this, OrEqual = False):
        Clause.__init__(self, this)
        self.OrEqual = OrEqual
    def __eq__(self, value):
        if self.OrEqual:
            return self.this >= value
        return self.this > value

class LessThan(Clause):
    def __init__(self, this, OrEqual = False):
        Clause.__init__(self, this)
        self.OrEqual = OrEqual
    def __eq__(self, value):
        if self.OrEqual:
            return self.this <= value
        return self.this < value

class IsTrue(Clause):
    def __eq__(self, value):
        return bool(value)
class IsFalse(Clause):
    def __eq__(self, value):
        return not value

class IsNullType(Clause):
    def __init__(self):
        pass
    def __eq__(self, value):
        return value is Null
class IsNotNullType(Clause):
    def __init__(self):
        pass
    def __eq__(self, value):
        return value is not Null

IsNull = IsNullType()
IsNotNull = IsNotNullType()

class Matches(Clause):
    def __eq__(self, other):
        return self.this(other)

# Aliases.
Q = Query
EQ = Equals
NEQ = NotEquals
Not = NotEquals
NOT = NotEquals
IN = ContainedBy
HAS = Contains
Has = Contains
GT = GreaterThan
LT = LessThan
NULL = IsNull
NOTNULL = IsNotNull
NotNull = IsNotNull

def parseSQL(sql):
    syntax = pysqldap.simpleSQL.parseString(sql)
    if len(syntax) >= 4:
        if syntax[0].lower() != 'select':
            raise SyntaxError('Unknown statement: %r' % syntax[0])
        if syntax[2].lower() != 'from':
            raise SyntaxError('Unknown preposition: %r' % syntax[2])

        columns = syntax[1][0]
        tables = syntax[3]

        if len(syntax) >= 6:
            if syntax[4].lower() != 'where':
                raise SyntaxError('Unknown clause specifier: %r' % syntax[4])

            clause_type = 'and'
            criteria = Criteria()

            for clause in syntax[4]:
                if isinstance(clause, str):
                    if clause.lower() not in ['and', 'or']:
                        raise SyntaxError('Unknown grouping operation: %r' % clause)

                    clause_type = clause

                elif len(clause) is 3:
                    (lh, op, rh) = clause

                    try: clause_handler = CLAUSE_HANDLERS[op]
                    except KeyError:
                        raise SyntaxError('Unknown clause operator: %r' % op)

                    criteria += Criteria(lh = clause_handler(rh))
                    clause_type = None

            if clause_type is not None:
                raise SyntaxError('Expecting clause operator after: %r' % clause_type)

        else:
            # Generate Criteria simply including names that exist.
            criteria = Criteria(*[(field, IsNotNull) for field in columns])

        return (criteria, tables)

    raise SyntaxError('Unknown syntax: %r' % sql)

def showResults(q):
    for entity_type in q.entityTypes():
        yield '%s:' % entity_type

        ten = ' ' * 10
        fields = [(f, len(f) + 10) for f in q.fieldsByType(entity_type)]
        fields = [(f[0], f[1], '%%-%d.%ds' % (f[1], f[1])) for f in fields]
        field_map = dict((fields[nr][0], nr) for nr in range(len(fields)))

        yield ' '.join(f[0] + ten for f in fields)
        yield ' '.join('-' * f[1] for f in fields)

        yield ''

        entity_results = {}
        for result in q.results:
            entity = result.entity
            if type(entity) is entity_type:
                entity_results.setdefault(entity, []).append(result)

        for (entity, results) in entity_results.items():
            # yield '  %s:' % entity

            results = [(field_map[r.field], r) for r in results]
            results.sort()
            results = [r[1] for r in results]

            yield ' '.join(fields[nr][2] % results[nr].value \
                           for nr in range(len(fields)))

        yield ''

# Player Command.
MINIMUM_LEVEL = 115
CLAUSE_HANDLERS = {}

WorldQuery = TableQuery
def doQueryWorld(peer, cmd, argstr):
    # todo: manage queries, views, and reports
    if peer.avatar and peer.avatar.level >= MINIMUM_LEVEL:
        if argstr:
            try: (criteria, tables) = parseSQL(argstr)
            except SyntaxError as e:
                print(e, file=peer)
            else:
                # Perform query.
                q = WorldQuery(*criteria).select(*tables)
                peer.page_string('\r\n'.join(showResults(q)))

        return True

try:
    from stuphmud.server.player import ACMD
    import pysqldap

except ImportError: pass
else: ACMD('mql*')(doQueryWorld)
