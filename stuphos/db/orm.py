# Game Object Relational Model Schema.
from sqlobject import sqlhub, SQLObject, connectionForURI
from sqlobject import IntCol, StringCol
from sqlobject import DateTimeCol, FloatCol
from sqlobject import ForeignKey


SmallIntCol = IntCol
BitIntCol = IntCol

# todo: metaclass these for reloadable classregistry lookups
try:
    class Players(SQLObject):
        class sqlmeta:
            # table = 'players'
            ##    idName = 'id'
            ##    idType = int

            pass

        # -- administrative
        # id = IntCol() # -- formerly idnum
            # The column name "id" is reserved for SQLObject use (and is implicitly created).

        name = StringCol(length = 20)
        email = StringCol(length = 80)
        password = StringCol(length = 20)
        freeze_level = IntCol()
        bad_login_attempts = IntCol()
        host = StringCol(length = 80)

        # -- timestamps
        birth = IntCol()
        last_login = IntCol()
        last_logon = IntCol()

        # -- preferences
        wimp_level = SmallIntCol()
        page_length = SmallIntCol()
        save_room = IntCol()
        load_room = IntCol()
        pref_flags_1 = IntCol()
        pref_flags_2 = IntCol()
        display_flags = IntCol()
        invis_level = SmallIntCol()

        # -- characteristics
        weight = SmallIntCol()
        height = SmallIntCol()
        alignment = IntCol()
        act = IntCol()
        affected_by = IntCol()
        remort = IntCol()
        remort_points = IntCol()
        race = IntCol()
        clan = IntCol()
        clanrank = IntCol()
        sex = SmallIntCol() # StringCol(length = 80)
        chclass = SmallIntCol()
        level = SmallIntCol()
        hometown = SmallIntCol()
        drunk = IntCol()
        fullness = IntCol()
        thirst = IntCol()

        # -- abilities
        a_str = IntCol()
        a_str_add = IntCol()
        a_int = IntCol()
        a_wis = IntCol()
        a_dex = IntCol()
        a_con = IntCol()
        a_cha = IntCol()

        # -- points
        mana = SmallIntCol()
        max_mana = SmallIntCol()
        hit = SmallIntCol()
        max_hit = SmallIntCol()
        move = SmallIntCol()
        max_move = SmallIntCol()
        qpoints = IntCol()
        armor = SmallIntCol()
        gold = IntCol()
        bank_gold = IntCol()
        exp = IntCol()
        hitroll = SmallIntCol()
        damroll = SmallIntCol()

        # -- statistics
        deaths = IntCol()
        mkills = IntCol()
        pkills = IntCol()
        dts = IntCol()
        played = IntCol()

        spells_to_learn = IntCol()
        spouse = IntCol() # -- -> players
        num_marriages = IntCol()
        spell_attack_1 = IntCol()
        spell_attack_2 = IntCol()

        ##   -- misc
        ##   --   join on player_color_sets for color
        ##   --   join on player_affects for affects
        ##   --   join on player_skills for skills
        ##   --   languages? there are 3.
        ##   --   saving throws? there are 5.

    ##    create index player_name on players (name);
    ##    create index player_id on players (id);
except ValueError: # Already in registry.
    pass

try:
    # XXX has no primary key by design
    class PlayerSkills(SQLObject):
        player_id = IntCol()
        skill_id = IntCol()
        level = IntCol()

        FIELDS = ['player_id', 'skill_id', 'level']
        FieldsClass = dict

    ##    create index player_skills_index on player_skills (player_id);
except ValueError: # Already in registry.
    pass

try:
    class PlayerAliases(SQLObject):
        # id = IntCol() # Serial PK

        player = IntCol()
        type = SmallIntCol()
        alias = StringCol(length = 32)
        replacement = StringCol(length = 256)

    ##    create index player_aliases_index on player_aliases (player);
except ValueError: # Already in registry.
    pass

try:
    class PlayerStrings(SQLObject):
        class sqlmeta:
            # This may not be true, since it's not PK, but it functions
            # suitably.  Plus, SQLObject demands a PK in this case.
            idName = 'player'

        player = IntCol()
        title = StringCol(length = 256)
        prename = StringCol(length = 128)
        wizname = StringCol(length = 128)
        poofin = StringCol(length = 256)
        poofout = StringCol(length = 256)
        description = StringCol()
        plan = StringCol()

    ##    create index player_strings_index on player_strings (player);
except ValueError: # Already in registry.
    pass

try:
    class PlayerRent(SQLObject):
        class sqlmeta:
            idName = 'player'

        player = IntCol()
        time = IntCol()
        rentcode = SmallIntCol()
        net_cost_per_diem = IntCol()
        gold = IntCol()
        account = IntCol()
        nitems = IntCol()

    ##    create index player_rent_index on player_rent (player);
except ValueError: # Already in registry.
    pass

try:
    class Rooms(SQLObject):
        class sqlmeta:
            idName = 'number'

        number = IntCol()
        zone = IntCol()
        sector_type = IntCol()
        name = StringCol()
        description = StringCol()
        flags = IntCol()
        light = SmallIntCol()

        ##   -- join on extra_descriptions
        ##   -- join on room_direction_data
        ##   -- join on affected_type
        ##   -- also:
        ##   --   special
        ##   --   contents (items)
        ##   --   people
except ValueError: # Already in registry.
    pass

try:
    class Affects(SQLObject):
        rnum = IntCol()
        stored_object_id = IntCol()
        object_prototype_id = IntCol()
        player = IntCol()
        type = IntCol()
        duration = IntCol()
        modifier = IntCol()
        location = IntCol()
        bitvector = IntCol()

        FIELDS = ['rnum', 'stored_object_id', 'object_prototype_id', 'player',
                  'type', 'duration', 'modifier', 'location', 'bitvector']
        FieldsClass = dict

    ##    create	index object_affects_index		on affects (stored_object_id);
    ##    create	index player_affects_index		on affects (player);
    ##    create	index room_affects_index		on affects (rnum);
    ##    create	index object_prototype_affects_index	on affects (object_prototype_id);
except ValueError: # Already in registry.
    pass

try:
    class RoomDirections(SQLObject):
        rnum = IntCol()
        direction = IntCol()
        description = StringCol()
        keyword = StringCol()
        exit_flags = IntCol()
        exit_key = IntCol()
        exit_destination = IntCol()

        FIELDS = ['rnum', 'direction', 'description', 'keyword',
                  'exit_flags', 'exit_key', 'exit_destination']
        FieldsClass = dict

    ##    create index room_direction_index on room_directions (rnum);
except ValueError: # Already in registry.
    pass

try:
    class ExtraDescriptions(SQLObject):
        rnum = IntCol()
        onum = IntCol()
        obj_proto_id = IntCol()
        keyword = StringCol()
        description = StringCol()

    ##    -- create index op_extra_descriptions_index on extra_descriptions (obj_proto_id);
    ##    create index extra_descriptions_rnum_index on extra_descriptions (rnum);
    ##    create index extra_descriptions_onum_index on extra_descriptions (onum);
except ValueError: # Already in registry.
    pass

try:
    class Houses(SQLObject):
        class sqlmeta:
            idName = 'rnum'

        rnum = IntCol()
        atrium = IntCol()
        exit = IntCol()
        built_on = IntCol()
        mode = IntCol()
        owner = IntCol()
        guest_count = IntCol()
        last_payment = IntCol()
        max_item_save = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class HouseGuests(SQLObject):
        rnum = IntCol()
        guest = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class StoredObjects(SQLObject):
        # id = IntCol() # Serial PK
        house = IntCol()
        player = IntCol()
        onum = IntCol()
        name = StringCol(length = 128)
        description = StringCol(length = 256)
        short_description = StringCol(length = 128)
        locate = SmallIntCol()
        value1 = IntCol()
        value2 = IntCol()
        value3 = IntCol()
        value4 = IntCol()
        item_type = IntCol()
        extra_flags = IntCol()
        anti_flags = IntCol()
        wear_flags = IntCol()
        weight = IntCol()
        timer = IntCol()
        bitvector = IntCol()

        FIELDS = ['house', 'player', 'onum', 'name', 'description', 'short_description',
                  'locate', 'value1', 'value2', 'value3', 'value4', 'item_type', 'extra_flags',
                  'anti_flags', 'wear_flags', 'weight', 'timer', 'bitvector']
        FieldsClass = dict

    ##    create index stored_objects_house_index on stored_objects (house);
    ##    create index stored_objects_player_index on stored_objects (player);
except ValueError: # Already in registry.
    pass

try:
    class LargeStrings(SQLObject):
        name = StringCol(length = 256)
        description = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class Zones(SQLObject):
        name = StringCol(length = 256)
        lifespan = IntCol()
        age = IntCol()
        bottom = IntCol()
        top = IntCol()
        flags = IntCol()
        reset_mode = IntCol()
        # id = IntCol()
        continent = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class ZoneCommands(SQLObject):
        # id = IntCol()
        # zone = ForeignKey(Zones, 'commands')

        znum = IntCol()
        command = StringCol(length = 1)
        if_flag = SmallIntCol()
        arg1 = IntCol()
        arg2 = IntCol()
        arg3 = IntCol()
        line = IntCol()

        FIELDS = ['znum', 'command', 'if_flag', 'arg1', 'arg2', 'arg3', 'line']
        FieldsClass = dict

    ##    create index zone_commands_index on zone_commands (znum);
except ValueError: # Already in registry.
    pass

try:
    class MobPrototypes(SQLObject):
        # id = IntCol()
        name = StringCol(length = 256)
        short_desc = StringCol()
        long_desc = StringCol()
        description = StringCol()
        flags = IntCol()
        affected_by = IntCol()
        alignment = IntCol()

        # -- abilities
        a_str = IntCol()
        a_str_add = IntCol()
        a_int = IntCol()
        a_wis = IntCol()
        a_dex = IntCol()
        a_con = IntCol()
        a_cha = IntCol()

        level = IntCol()
        hitroll = IntCol()
        armor = IntCol()
        max_hit = IntCol()
        hit = IntCol()
        max_move = IntCol()
        move = IntCol()
        max_mana = IntCol()
        mana = IntCol()
        damage_dice = IntCol()
        damage_dice_faces = IntCol()
        damroll = IntCol()
        gold = IntCol()
        exp = IntCol()
        position = IntCol()
        default_position = IntCol()
        sex = SmallIntCol()
        chclass = SmallIntCol(dbName = 'class')
        weight = SmallIntCol()
        height = SmallIntCol()

        # -- saving throws
        walk_type = IntCol()
        attack_type = IntCol()

        # -- generic spec proc
        spec_proc = StringCol(length = 64)

except ValueError: # Already in registry.
    pass

try:
    class Shops(SQLObject):
        zone = IntCol()
        # id = IntCol() # PK

        # Todo:
        ##    `DecimalCol`:
        ##        Base-10, precise number.  Uses the keyword arguments `size` for
        ##        number of digits stored, and `precision` for the number of digits
        ##        after the decimal point.

        profit_buy = FloatCol() # decimal(7, 4)
        profit_sell = FloatCol() # decimal(7, 4)

        no_such_item1 = StringCol(length = 256)
        no_such_item2 = StringCol(length = 256)
        missing_cash1 = StringCol(length = 256)
        missing_cash2 = StringCol(length = 256)
        do_not_buy = StringCol(length = 256)
        message_buy = StringCol(length = 256)
        message_sell = StringCol(length = 256)
        temper = IntCol()
        bitvector = IntCol()
        keeper = IntCol()
        with_who = IntCol()
        # -- in_room
        open1 = IntCol()
        open2 = IntCol()
        close1 = IntCol()
        close2 = IntCol()
        bankAccount = IntCol(dbName = 'bankAccount')
        goldOnHand = IntCol(dbName = 'goldOnHand')
        lastsort = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class ShopBuyTypes(SQLObject):
        class sqlmeta:
            idName = 'shop'

        shop = IntCol()
        type = IntCol()
        keywords = StringCol(length = 256)

    ##    create index shop_buy_types_index on shop_buy_types (shop);
except ValueError: # Already in registry.
    pass

try:
    class ShopProducts(SQLObject):
        class sqlmeta:
            idName = 'shop'

        shop = IntCol()
        product = IntCol()

    ##    create index shop_products_index on shop_products (shop);
except ValueError: # Already in registry.
    pass

try:
    class ShopRooms(SQLObject):
        class sqlmeta:
            idName = 'shop'

        shop = IntCol()
        room = IntCol()

    ##    create index shop_rooms_index on shop_rooms (shop);
except ValueError: # Already in registry.
    pass

try:
    class Messages(SQLObject):
        # id = IntCol() # Serial PK
        name = StringCol(length = 32)
        type = StringCol(length = 32)
        room = IntCol()
        date_created = DateTimeCol()
        date_updated = DateTimeCol()
        status = StringCol(length = 64)
        message = StringCol()

    ##    create index message_type_index on messages (type);
    ##    create index message_status_index on messages (type);
except ValueError: # Already in registry.
    pass

try:
    class Boards(SQLObject):
        class sqlmeta:
            idName = 'obj'

        # id = IntCol()
        obj = IntCol()
        read_lvl = IntCol()
        write_lvl = IntCol()
        remove_lvl = IntCol()
        cleanup = SmallIntCol()

    ##    create index board_index on boards (obj);
except ValueError: # Already in registry.
    pass

try:
    class BoardMessages(SQLObject):
        # id = IntCol() # Serial PK
        board = IntCol()
        heading = StringCol(length = 256)
        message = StringCol()
        level = IntCol()
        poster = StringCol(length = 32)
        date_created = IntCol()

        FIELDS = ['board', 'heading', 'message', 'level', 'poster', 'date_created']
        FieldsClass = dict

    ##    create index board_message_index on board_messages (board);
except ValueError: # Already in registry.
    pass

try:
    class GlobalVariables(SQLObject):
        class sqlmeta:
            idName = 'name'
            idType = str

        name = StringCol(length = 32)
        value = StringCol()
except ValueError: # Already in registry.
    pass

try:
    class ObjectPrototypes(SQLObject):
        class sqlmeta:
            idName = 'number'

        number = IntCol()
        flags = IntCol()
        name = StringCol(length = 128)
        description = StringCol()
        short_description = StringCol(length = 128)
        action_description = StringCol(length = 256)

        value1 = IntCol()
        value2 = IntCol()
        value3 = IntCol()
        value4 = IntCol()
        type = SmallIntCol()
        wear_flags = IntCol()
        extra_flags = IntCol()
        anti_flags = IntCol()
        weight = IntCol()
        cost = IntCol()
        cost_per_day = IntCol()
        timer = IntCol()
        trap = IntCol()
        bitvector = BitIntCol()
        spec_proc = StringCol(length = 64)

except ValueError: # Already in registry.
    pass

try:
    class MailExchange(SQLObject):
        mail_id = IntCol()
        to_player = IntCol()
        read = IntCol()

except ValueError: # Already in registry.
    pass

# Mail:
# m.id, m.from_name, x.from_player, m.subject, m.body, m.date_created

try:
    class ZoneResetProgram(SQLObject):
        class sqlmeta:
            table = 'zone_reset_programs'

        zone = IntCol(unique = True)
        source = StringCol()
        programmer = StringCol()
        flags = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class PlayerRent(SQLObject):
        player = IntCol() # unique = True)
        time = IntCol()
        rentcode = SmallIntCol()
        net_cost_per_diem = IntCol()
        gold = IntCol()
        account = IntCol()
        nitems = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class VerbCommand(SQLObject):
        room = IntCol()
        mobile = IntCol()
        item = IntCol()
        verb = StringCol()
        method = StringCol()
        preposition = StringCol()
        programmer = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class Triggers(SQLObject):
        room = IntCol()
        mobile = IntCol()
        item = IntCol()

        number = IntCol()

        type = StringCol()
        arguments = StringCol()
        program = StringCol()

        programmer = StringCol()
        flags = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class Continents(SQLObject):
        vnum = IntCol()
        name = StringCol()
        planet = IntCol()
        object = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class Planets(SQLObject):
        vnum = IntCol()
        name = StringCol()
        object = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class GirlLibrary(SQLObject):
        parent = IntCol() # todo: SelfReference
        name = StringCol()
        type = StringCol()
        text = StringCol()
        programmer = StringCol() # node: also used as documument content-type
        meta = StringCol() # for storing activity superclass, etc.

    GirlNode = GirlLibrary
    ProgramLibrary = GirlLibrary

except ValueError: # Already in registry.
    pass

try:
    class GirlLibraryCore(SQLObject):
        position = IntCol()
        path = StringCol()

    GirlBootOrderNode = GirlLibraryCore

except ValueError: # Already in registry.
    pass

try:
    class GirlLibraryPerm(SQLObject):
        owner = StringCol()
        principal = StringCol()
        resource = StringCol()
        access = StringCol()

    GirlPermission = GirlLibraryPerm

except ValueError: # Already in registry.
    pass

try:
    class GirlPrincipalGroup(SQLObject):
        principal = StringCol()
        groups = StringCol()

        # Qualify Group Organization
        #   Provide streams of group settings.
        # name = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class GirlCompiledModule(SQLObject):
        node = ForeignKey('GirlLibrary')
        signature = StringCol() # checksum
        payload = StringCol()

except ValueError: # Already in registry.
    pass

try:
    # Girl System Library replacements.
    class Books(SQLObject): pass
    class BookLaunch(SQLObject): pass
    class BookAccess(SQLObject): pass
    class PrincipalGroup(SQLObject): pass

except ValueError: # Already in registry.
    pass

try:
    class PlayerNotebook(SQLObject):
        player = StringCol()
        folder = StringCol()
        name = StringCol()
        content = StringCol()
        flags = IntCol()

except ValueError: # Already in registry.
    pass

try:
    class UserKeyfile(SQLObject):
        username = StringCol()
        purpose = StringCol()
        content = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class Log(SQLObject):
        source = StringCol()
        type = StringCol()
        content = StringCol()
        timestamp = DateTimeCol()

except ValueError: # Already in registry.
    pass

try:
    class DBConf(SQLObject):
        name = StringCol()
        fields = StringCol()

except ValueError: # Already in registry.
    pass

try:
    class DatabaseConfiguration(SQLObject):
        name = StringCol()
        path = StringCol()
        hard = IntCol()
        flags = IntCol()

except ValueError: # Already in registry.
    pass


try:
    class BillableAccount(SQLObject):
        programmer = StringCol()
        # todo: CompositeKey with django.User and server.Player

except ValueError: # Already in registry.
    pass

try:
    class Job(SQLObject):
        link = StringCol()
        title = StringCol()
        company = StringCol()

except ValueError: # Already in registry.
    pass


try:
    # See phsite.network.models.site.UserRelation
    class PrincipalRelation(SQLObject):
        superior = StringCol()
        inferior = StringCol()

except ValueError: # Already in registry.
    pass


try:
    class InvoiceAccount(SQLObject):
        name = StringCol()
        type = StringCol()
        debitCompute = FloatCol(default = 0.0)
        debitContent = FloatCol(default = 0.0)

except ValueError: # Already in registry.
    pass

try:
    class InvoiceChargePath(SQLObject):
        # External girl_library activity node storing accounted name.
        pathIdExternal = IntCol()

except ValueError: # Already in registry.
    pass

try:
    # debugOn()
    class InvoiceCharge(SQLObject):
        account = ForeignKey('InvoiceAccount')
        creation = DateTimeCol()
        paid = StringCol(default = None) # XXX What I want is a NULLABLE DateTimeCol
        type = IntCol()
        charge = FloatCol()
        path = ForeignKey('InvoiceChargePath', default = None)
        memo = StringCol()
        runId = FloatCol()

except ValueError: # Already in registry.
    pass

try:
    class InvoiceBillpoint(SQLObject):
        account = ForeignKey('InvoiceAccount')
        charge = ForeignKey('InvoiceCharge')

        creation = DateTimeCol()
        name = StringCol()

        debitCompute = FloatCol()
        debitContent = FloatCol()

        debitComputeChargeUSD = FloatCol(default = -1.0)
        debitContentChargeUSD = FloatCol(default = -1.0)

        debitChargeTotalUSD = FloatCol(default = -1.0)
        feeMarkup = FloatCol(default = 1.0)
        perTxFee = FloatCol(default = 0.0)

except ValueError: # Already in registry.
    pass

try:
    class InvoiceQuotaObject(SQLObject):
        account = ForeignKey('InvoiceAccount')
        type = StringCol()
        hard = IntCol()
        exceeded = IntCol()

except ValueError: # Already in registry.
    pass


# from sqlobject import JSONCol
from sqlobject import BoolCol

class VariableDBNativeTool:
    # imported dynamically from conf because sqlite is broken.
    def __init__(self, core, vardb):
        self._core = core
        self._vardb = vardb

    # BLOBCol
    # BigIntCol
    # BoolCol
    # CurrencyCol
    # DateCol
    # DateTimeCol
    # DecimalCol
    # DecimalStringCol
    # EnumCol
    # FloatCol
    # IntCol
    # JSONCol
    # JsonbCol
    # KeyCol
    # MediumIntCol
    # PickleCol
    # SetCol
    # SmallIntCol
    # StringCol
    # TimeCol
    # TimedeltaCol
    # TimestampCol
    # TinyIntCol
    # UnicodeCol
    # UuidCol

    def db(self, frame, name, *args, **kwd):
        from stuphos.kernel import interpreter as girl # XXX Make this global!

        progr = frame.task.findProgrammer()
        name = str.__str__(name)
        resource = ['service/database'] + name.split('/')

        if progr is None or not self._core.principalHasAccess(progr.principal, resource, 'read+write'): # write
            raise girl.NoAccessException(progr, resource, 'read+write')

        tables = dict((t.name, t) for t in args if not t.name.endswith('acct_'))
        return self._vardb._Open(name, **tables)

    def table(self, frame, name, *cols):
        cols = [(c.name, c) for c in cols]
        return self._vardb.Table(name, cols)

    # DateTimeCol, IntCol, StringCol, JSONCol, BoolCol
    class _Column(object):
        def __new__(self, frame, name):
            return self._columnClass(name)
        # def __init__(self, *args, **kwd):
        #   # print string.call('column.init', *args, **kwd)
        #   pass

    class datetime(_Column):
        _columnClass = DateTimeCol # sqlite.module.DateTimeCol
    class integer(_Column):
        _columnClass = IntCol # sqlite.module.IntCol
    class string(_Column):
        _columnClass = StringCol # sqlite.module.StringCol
    # class json(_Column):
    #     _columnClass = JSONCol # sqlite.module.JSONCol
    class bool(_Column):
        _columnClass = BoolCol # sqlite.module.BoolCol

    date = time = timestamp = datetime
    boolean = bool

    _columns = dict(datetime = date, date = date, time = date,
                    timestamp = date, integer = integer,
                    string = string)

    _columns.update(dict(#json = json,
                         bool = bool,
                         boolean = bool))


def selectTableSql(cursor, table):
    cursor.execute('select %s from %s' % (', '.join(table.FIELDS), table.name))

    def toModel(row):
        return table.FieldsClass(**dict(list(zip(table.FIELDS, row))))

    return list(map(toModel, cursor))

def createSQLObjectTable(table):
    from sqlobject.dberrors import OperationalError
    try: table.createTable()
    except OperationalError:
        pass
