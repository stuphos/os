# CB: Is open-sourcing a specific input format to the expert system actually a fail? ;)
# (and maybe it should go in another module, not __init__)
#

# todo: move into ph.lang.document

from xml.dom import minidom
import re

class FileSource(str):
    def parse(self):
        return minidom.parse(open(self))
    def getName(self):
        return self
class InternalSource(str):
    def parse(self):
        return minidom.parseString(self)
    def getName(self):
        try: return self.__name
        except AttributeError:
            from md5 import md5
            self.__name = name = 'internal$%s' % md5(self).hexdigest()

# Basic Parsing Tools.
def parseSoftInt(value):
    if value not in ('', None):
        return int(value)

def parseBoolean(value):
    if isinstance(value, str):
        value = value.lower()
        if value in ('true', 'on', 'yes', '1'):
            return True
        if value in ('false', 'off', 'no', '0'):
            return False
        if value.isdigit():
            return int(value)

    raise TypeError(type(value))

def parseSoftBoolean(value):
    return None if value == '' else parseBoolean(value)

DICE_PATTERN = re.compile(r'(?P<number>\\d+)d(?P<size>\\d+)(?:\\+(?P<addend>\\d+))?')
def parseDice(dice):
    match = DICE_PATTERN.match(dice)
    if match is None:
        raise SyntaxError(dice)

    match = match.groupdict()
    return (match['number'], match['size'], match['addend'])

def parseWeaponDice(dice):
    match = DICE_PATTERN.match(dice)
    if match is None:
        raise SyntaxError(dice)

    match = match.groupdict()
    return (match['number'], match['size'])

# todo: allow '-' in place of '_'
def transferAttributes(node, object, attributes):
    for (name, function) in attributes.items():
        value = node.getAttribute(name)
        if value:
            setattr(object, name, function(value))

def getVnum(node, name = 'vnum'):
    return int(node.getAttribute(name))
def getWholeText(node):
    data = []
    for child in node.childNodes:
        if child.nodeType == child.TEXT_NODE:
            data.append(child.data)

    return ''.join(data)

# Loading.
NAMESPACES = dict(stuph      = 'telnet://stuphmud.net/3',
                  olc        = 'telnet://stuphmud.net/world/3',
                  search     = 'telnet://stuphmud.net/world/zifnab/search',
                  genspecact = 'telnet://stuphmud.net/world/tarn/genspecact',
                  player     = 'telnet://stuphmud.net/player/3',
                  wizard     = 'telnet://stuphmud.net/wizard/3')

class Loader:
    def __init__(self, environment):
        self.environment = environment

    def loadDocument(self, source):
        doc = source.parse()
        stuph = doc.documentElement
        assert stuph.localName == 'stuph' and stuph.namespaceURI == NAMESPACES['stuph']

        doc.source = source
        self.environment.addDocument(doc)

        # todo: map namespace-prefixes on upfront element and check on those for faster recognition

        for node in stuph.childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                # detect node purpose and dispatch
                ns = node.namespaceURI
                name = node.localName

                if ns == NAMESPACES['olc']:
                    if name == 'zone':
                        zone = self.loadOlcZone(node)
                        self.environment.addOlcZone(zone)

                    elif name == 'houses':
                        pass

                elif ns == NAMESPACES['wizard']:
                    if name == 'command':
                        self.loadWizardCommand(node)
                    elif name == 'module':
                        self.loadWizardModule(node)

                elif ns == NAMESPACES['player']:
                    if name == 'trigger':
                        self.loadPlayerTrigger(node)
                    elif name == 'alias':
                        self.loadPlayerAlias(node)
                    elif name == 'profile':
                        self.loadPlayerProfile(node)
                    elif name == 'spell':
                        self.loadPlayerSpell(node)
                    elif name == 'mail':
                        self.loadPlayerMail(node)

                elif ns == NAMESPACES['stuph']:
                    if name == 'player':
                        self.loadStuphPlayer(node)

                    # Atypical and old-gen:
                    elif name == 'mobile':
                        self.loadStuphMobile(node)
                    elif name == 'item':
                        self.loadStuphItem(node)

        return doc

    parseContinentName = str
    zoneAttributes = dict(name = str, age = int, lifespan = int,
                          continent = parseContinentName)

    for flag in ('draft', 'immortal', 'clan', 'remort'):
        zoneAttributes[flag] = parseBoolean

    def loadOlcZone(self, node):
        # Commands and prototype data.
        zone = self.environment.ZoneData(vnum = getVnum(node))
        transferAttributes(node, zone, self.zoneAttributes)

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.localName
                if  name == 'commands':
                    self.loadOlcZoneCommands(zone, child)
                elif name == 'room':
                    self.loadOlcRoom(zone, child)
                elif name == 'mobile':
                    self.loadOlcMobile(zone, child)
                elif name == 'item':
                    self.loadOlcItem(zone, child)
                elif name == 'shop':
                    self.loadOlcShop(zone, child)

        return zone

    def loadOlcZoneCommands(self, zone, node):
        # Any and all zone commands.
        position = node.getAttribute('position')
        if position.isdigit():
            position = int(int)
        elif position == '':
            position = 'end'
        else:
            assert position in ('front', 'end', 'overwrite')

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                if child.tagName == 'room':
                    commands = list(self.loadOlcRoomCommands(zone, child))
                    zone.addCommands(position, commands)

    EXIT_NAMES = ['north', 'south', 'east', 'west', 'up', 'down']

    def loadOlcRoomCommands(self, zone, node):
        # Room commands container.
        room = zone.ZCmd.RoomCommand(zone = zone, vnum = getVnum(node))
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.tagName
                if name == 'item':
                    vnum = getVnum(child)
                    maximum = parseSoftInt(child.getAttribute('maximum'))

                    item = zone.ZCmd.ItemCommand(vnum = vnum, maximum = maximum)
                    self.loadOlcItemCommands(room, item, child)

                    yield item

                elif name == 'mobile':
                    yield self.loadOlcMobileCommands(room, child)
                elif name == 'remove':
                    yield zone.ZCmd.RemoveItem(room = room, vnum = getVnum(child, 'item'))

                elif name in self.EXIT_NAMES:
                    yield room.DoorState(room = room, direction = name,
                                         closed = parseSoftBoolean(child.getAttribute('closed')),
                                         locked = parseSoftBoolean(child.getAttribute('locked')))

    def loadOlcMobileCommands(self, room, node):
        # Mobiles loaded in room -- recursive on mount.
        mobile = room.zone.ZCmd.MobileCommand(vnum = getVnum(node),
                                              maximum = parseSoftInt(node.getAttribute('maximum')),
                                              room = room)

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.tagName
                if name == 'item':
                    position = child.getAttribute('position')

                    vnum = getVnum(child)
                    maximum = parseSoftInt(child.getAttribute('maximum'))

                    if position:
                        item = mobile.EquipmentCommand(vnum = vnum, maximum = maximum,
                                                    wearer = mobile, position = position)

                        self.loadOlcItemCommands(room, item, child)
                        mobile.addEquipment(item)
                    else:
                        item = room.zone.ZCmd.ItemCommand(vnum = vnum, maximum = maximum,
                                                          carrier = mobile)

                        self.loadOlcItemCommands(room, item, child)
                        mobile.addInventory(item)

                elif name == 'mount':
                    vnum = getVnum(child)
                    maximum = parseSoftInt(child.getAttribute('maximum'))

                    mount = room.zone.ZCmd.MobileCommand(vnum = vnum, maximum = maximum,
                                                         rider = mobile)

                    self.loadOlcMobileCommands(doc, room, child)
                    mobile.setMount(mount)

                # XXX this doesn't really exist.
                ##    elif name == 'unmount':
                ##        vnum = getVnum(child)
                ##        mobile.unmount(vnum)

        room.addMobile(mobile)
        return mobile

    def loadOlcItemCommands(self, room, item, node):
        # Items within containers -- meant for recursion.
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.tagName == 'item':
                vnum = getVnum(child)
                maximum = parseSoftInt(child.getAttribute('maximum'))

                subitem = room.zone.ZCmd.ItemCommand(vnum = vnum, maximum = maximum,
                                                     container = item)

                self.loadOlcItemCommands(room, subitem, child)
                item.addItem(subitem)

    parseRoomSector = str
    roomAttributes = dict(name = str, sector = parseRoomSector)

    # not house, housecrashsave, atrium, *, or clanhouseentrance
    for flag in ('dark', 'deathtrap', 'nomob', 'indoors', 'peaceful',
                 'soundproof', 'notrack', 'nomagic', 'tunnel', 'private',
                 'godroom', 'olc', 'implementorOnly', 'arena', 'noteleport',
                 'noquit', 'regeneration', 'nomortalpc', 'deleted'):
        roomAttributes[flag] = parseBoolean

    def loadOlcRoom(self, zone, node):
        room = zone.RoomData(vnum = getVnum(node), description = [],
                             extra_descriptions = {}, exits = {})

        transferAttributes(node, room, self.roomAttributes)

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.localName
                ns = child.namespaceURI

                if ns == NAMESPACES['search']:
                    # Q: Should this exist in room zone commands too?
                    self.loadOlcRoomSearches(room, child)

                elif name == 'description':
                    keywords = child.getAttribute('keywords')
                    if keywords:
                        room.extra_descriptions[keywords] = getWholeText(child)
                    else:
                        room.description.append(getWholeText(child))

                elif name in self.EXIT_NAMES:
                    self.loadOlcRoomExit(room, name, child)

        zone.addRoom(room)

    def loadOlcRoomSearches(self, room, node):
        if node.localName == 'on':
            search = room.SearchData()
            transferAttributes(node, search, dict(command = str, keywords = str,
                                                  match = str, reset = str))

            for child in node.childNodes:
                if child.nodeType == child.ELEMENT_NODE:
                    name = child.localName
                    if name == 'requires':
                        search.requires = Object(item = getVnum(child, 'item'))

                    elif name == 'act':
                        # todo: search object message api
                        messages = search('message', {})
                        messages[child.getAttribute('to')] = getWholeText(child)

                    elif name in ('open', 'close', 'toggle'):
                        self.loadOlcDoorSearch(search, child)
                    elif name == 'create':
                        self.loadOlcSpawnSearch(search, child)

                    elif name == 'teleport':
                        self.loadOlcTeleportSearch(search, child)

            room.addSearch(search)

    def loadOlcDoorSearch(self, search, node):
        door = Object()
        search('exits', {})[node.getAttribute('exit')] = door

        transferAttributes(node, door, dict(lock = parseBoolean))
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                # todo: search object message api
                messages = search('message', {})
                messages[child.getAttribute('to')] = getWholeText(child)

    def loadOlcSpawnSearch(self, search, node):
        item = Object(vnum = getVnum(node, 'item'))
        search['creation'].append(item)

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.localName
                if name == 'respawn':
                    item.respawn = True
                    self.loadOlcRespawnSearch(search('message', {}), child)

                elif name == 'act':
                    # todo: search object message api
                    message = search('message', {})
                    message[child.getAttribute('to')] = getWholeText(child)

    def loadOlcRespawnSearch(self, messages, node):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.localName == 'act':
                messages[child.getAttribute('to')] = getWholeText(child)

    def loadOlcTeleportSearch(self, search, node):
        teleport = Object(vnum = getVnum(node, 'room'))
        search.teleport = teleport

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                name = child.localName
                message = search('message', {})

                if name in ('departure', 'arrival'):
                    # todo: search object message api -- XXX breaking convention
                    self.loadOlcTeleportMessageSearch(message.setdefault(name, {}), child)

    def loadOlcTeleportMessageSearch(self, message, node):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.localName == 'act':
                message[child.getAttribute('to')] = getWholeText(child)

    exitAttributes = dict(room = int, key = int, keywords = str)

    for flag in ('isdoor', 'closed', 'locked', 'pickproof', 'hidden', 'nomagic'):
        exitAttributes[flag] = parseBoolean

    def loadOlcRoomExit(self, room, name, node):
        exit = room.ExitData(direction = name, description = [])
        transferAttributes(node, exit, self.exitAttributes)
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE:
                if child.localName == 'description':
                    exit.description.append(getWholeText(child))

        room.addExit(name, exit)

    mobileAttributes = dict(keywords = str, name = str, sex = str, level = int, alignment = int,
                            gold = int, position = str, movement = str, armorclass = int,
                            hitroll = int, barehand = parseDice, hitpoints = parseDice,
                            experience = int, attack = str, strength = str, intelligence = str,
                            wisdom = str, dexterity = str, constitution = str, charisma = str,
                            special = str)

    # todo: mobile flags
    for flag in ('sentinel', 'scavenger', 'nobackstab', 'stayinzone', 'wimpy', 'memory',
                 'helper', 'nocharm', 'nosummon', 'nosleep', 'nobash', 'noblind', 'hunter',
                 'invulnerable', 'nofire', 'nosubdue', 'mobviolence', 'mount', 'silent',
                 'ignoresummons', 'nocorpse', 'noupdate', 'deleted'):
        mobileAttributes[flag] = parseBoolean

    mobileAffectionAttributes = dict((name, parseBoolean) for name in \
                                     ('blind', 'invisible', 'detectalign', 'detectinvis',
                                      'detectmagic', 'senselife', 'waterwalk', 'sanctuary',
                                      'cursed', 'infravision', 'poisoned', 'protectionfromevil',
                                      'protectionfromgood', 'sleep', 'notrack', 'flying',
                                      'fireshield', 'sneaking', 'hiding', 'phaseblur', 'charmed',
                                      'etherealized', 'secondattack', 'thirdattack', 'fourthattack',
                                      'meditating', 'reflect', 'absorb', 'entangled'))

    def loadOlcMobile(self, zone, node):
        mobile = zone.MobileData(vnum = getVnum(node))
        transferAttributes(node, mobile, self.mobileAttributes)

        position = node.getAttribute('position')
        if position:
            position = position.split('/', 2)
            if len(position) == 2:
                (mobile.position, mobile.default_position) = position
            else:
                mobile.position = position

        aggressive = node.getAttribute('aggressive')
        if aggressive:
            mobile.aggressive = aggressive # all|(evil,neutral,good,npc)

        for child in node.nodeType == node.ELEMENT_NODE:
            ns = child.namespaceURI
            name = child.localName

            if ns == NAMESPACES['genspecact']:
                continue

            if name in ['room_description', 'detailed_description']:
                # todo: further format room_description
                setattr(mobile, name, getWholeText(child))

            elif name == 'affections':
                af = mobile.Affections()
                mobile.affections = af

                transferAttributes(child, af, self.mobileAffectionAttributes)

        zone.addMobile(zone, mobile)

    itemAttributes = dict(keywords = str, name = str, cost = int,
                          minlevel = int, weight = int, timer = int)

    for flag in ('glowing', 'humming', 'norent', 'nodonate', 'noinvis', 'invisible',
                 'magic', 'cursed', 'blessed', 'antigood', 'antievil', 'antineutral',
                 'twohanded', 'flaming', 'poison', 'nosell', 'nomobtake', 'quest',
                 'nodecay', 'nolocate', 'noauction', 'shining', 'hidden', 'nodisarm',
                 'transparent', 'biodegradable', 'deleted', 'noidentify', 'itemnodecay'):
        itemAttributes[flag] = parseBoolean

    itemAnticlassAttributes = dict((name, parseBoolean) for name in \
                                   ('wizard', 'cleric', 'assassin', 'knight', 'ranger',
                                    'paladin', 'monk', 'ninja', 'druid'))

    itemWearableAttributes = dict((name, parseBoolean) for name in \
                                  ('take', 'finger', 'neck', 'body', 'head', 'legs',
                                   'feet', 'hands', 'arms', 'shield', 'about', 'waist',
                                   'wrist', 'wield', 'hold', 'ear', 'face', 'restraint'))


    ScrollAttrs = dict(spell_level = int,
                       spell1 = str,
                       spell2 = str,
                       spell3 = str)

    WandAttrs = dict(spell_level = int,
                     capacity = int,
                     charges = int,
                     spell = str)

    LiqContAttrs = dict(capacity = int,
                        contains = int,
                        liquid = str,
                        poisoned = parseBoolean)

    ITEM_TYPE_ATTRIBUTES = dict(light = dict(hours = int),
                                scroll = ScrollAttrs,
                                potion = ScrollAttrs,
                                pill = ScrollAttrs,
                                wand = WandAttrs,
                                staff = WandAttrs,
                                weapon = dict(spell = str,
                                              damage = parseWeaponDice,
                                              weapon = str),

                                armor = dict(armorclass = int),
                                trap = dict(biodegradable = parseBoolean),
                                container = dict(capacity = int,
                                                 key = int,
                                                 closeable = parseBoolean,
                                                 pickproof = parseBoolean,
                                                 closed = parseBoolean,
                                                 locked = parseBoolean,
                                                 container_type = str),

                                fountain = LiqContAttrs,
                                food = dict(satiation = int,
                                            poisoned = parseBoolean),

                                money = dict(worth = int),
                                portal = dict(min_level = int,
                                              max_level = int,
                                              room = int))

    ITEM_TYPE_ATTRIBUTES['liquid-container'] = LiqContAttrs

    def loadOlcItem(self, zone, node):
        item = zone.ItemData(vnum = getVnum(node), extra_descriptions = [])
        transferAttributes(node, item, self.itemAttributes)

        for child in node.nodeType == node.ELEMENT_NODE:
            name = child.localName

            # merge all of these descriptiony things
            if name in ['room_description', 'detailed_description']:
                # todo: further format room_description
                setattr(item, name, getWholeText(child))

            elif name == 'description':
                keywords = child.getAttribute('keywords')
                if keywords:
                    item.extra_descriptions[keywords] = getWholeText(child)

            elif name == 'anticlass':
                af = item.Anticlass()
                item.affections = af

                transferAttributes(child, af, self.itemAnticlassAttributes)

            elif name == 'wearable':
                bitv = item.Wearable()
                item.wearable = bitv

                transferAttributes(child, bitv, self.itemWearableAttributes)

            elif name == 'affects':
                self.loadOlcItemAffects(item, child)

            elif name == 'trap':
                trapType = child.getAttribute('type')
                if trapType:
                    item.trapType = trapType

        itemType = node.getAttribute('type')
        if itemType:
            item.type = itemType
            attributes = self.ITEM_TYPE_ATTRIBUTES.get(itemType)

            if attributes is not None:
                transferAttributes(node, item, attributes)

        zone.addItem(zone, item)

    def loadOlcItemAffects(self, item, node):
        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.localName == 'apply':
                to = child.getAttribute('to')
                modifier = child.getAttribute('modifier')

                item.addAffect(to, modifier)

    def loadOlcShop(self, zone, node):
        pass

    def loadWizardCommand(self, node):
        # Todo: this node should go under a wizardly-module so that
        # it maybe compile-and-bind to the module's globals.
        action = node.getAttribute('action')
        verb = node.getAttribute('verb')
        level = node.getAttribute('level')

        for child in node.childNodes:
            if child.nodeType == child.ELEMENT_NODE and child.localName == 'code':
                source = child.getAttribute('source')
                codeType = child.getAttribute('type')
                code = getWholeText(child)

                cmd = self.environment.Wizard.Command((action, verb),
                                                      dict(level = level),
                                                      (source, codeType, code))
                self.environment.addModule(cmd)

                # Only process the first.
                break

    def loadWizardModule(self, node):
        pass

    def loadPlayerTrigger(self, node):
        pass
    def loadPlayerAlias(self, node):
        pass
    def loadPlayerProfile(self, node):
        pass
    def loadPlayerSpell(self, node):
        pass

    def loadStuphPlayer(self, node):
        pass
    def loadStuphMobile(self, node):
        pass
    def loadStuphItem(self, node):
        pass

# Environmental Model.
class Object:
    def __init__(self, **kwd):
        self.__dict__.update(kwd)
    def __call__(self, name, value):
        return self.__dict__.setdefault(name, value)
    def __getitem__(self, name):
        return self(name, [])

    Absent = object()
    def __repr__(self):
        def getValue(name):
            if callable(name):
                return name(self)

            value = self
            parts = name.split('.')
            first = parts[0]

            for name in parts:
                call = False
                if name.endswith('()'):
                    name = name[:-2]
                    call = True

                value = getattr(value, name, self.Absent)
                if value is self.Absent:
                    break

                if call:
                    value = value()

            return (first, value)

        def formatValue(v):
            # ???
            if isinstance(v, str):
                return str(v)
            return v

        attrs = getattr(self, '__attributes__', [])
        attrs = (getValue(n) for n in attrs)
        attrs = ' '.join('%s=%r' % (n, formatValue(v)) for (n, v) \
                         in attrs if v is not self.Absent)

        return '<%s%s%s>' % (self.__class__.__name__,
                             attrs and ' ' or '', attrs)

class Environment(Object):
    class ZoneData(Object):
        __module__ = __name__ + '.Environment'
        __attributes__ = ['vnum', 'name']

        class ZCmd:
            class RoomCommand(Object):
                __module__ = __name__ + '.Environment.ZoneData.ZCmd'
                __attributes__ = ['vnum']

                class DoorState(Object):
                    __module__ = __name__ + '.Environment.ZoneData.ZCmd.RoomCommand'
                    __attributes__ = ['direction', 'room']

                def addMobile(self, mobile):
                    self['mobiles'].append(mobile)
                def addItem(self, item):
                    self['items'].append(item)

            class MobileCommand(Object):
                __module__ = __name__ + '.Environment.ZoneData.ZCmd'
                __attributes__ = ['vnum']

                class EquipmentCommand(Object):
                    __module__ = __name__ + '.Environment.ZoneData.ZCmd.MobileCommand'
                    __attributes__ = ['vnum', 'position']

                    def addItem(self, item):
                        self['contents'].append(item)

                def addEquipment(self, item):
                    self['equipment'].append(item)
                def addInventory(self, item):
                    self['inventory'].append(item)

                def setMount(self, mount):
                    self.mount = mount

                ##    def unmount(self, vnum):
                ##        assert not hasattr(self, 'mount')
                ##        del self.mount

            class ItemCommand(Object):
                __module__ = __name__ + '.Environment.ZoneData.ZCmd'
                __attributes__ = ['vnum']

                def addItem(self, item):
                    self['contents'].append(item)

            class Position(Object):
                __module__ = __name__ + '.Environment.ZoneData.ZCmd'
                __attributes__ = ['position', lambda p: ('nr(commands)', len(p.commands))]

            class RemoveItem(Object):
                __module__ = __name__ + '.Environment.ZoneData.ZCmd'
                __attributes__ = ['vnum']

        class RoomData(Object):
            __module__ = __name__ + '.Environment.ZoneData'
            __attributes__ = ['vnum']

            class ExitData(Object):
                __module__ = __name__ + '.Environment.ZoneData.RoomData'
                __attributes__ = ['direction', 'room', 'key']

            class SearchData(Object):
                __module__ = __name__ + '.Environment.ZoneData.RoomData'
                __attributes__ = ['keywords', 'reset', 'command']

            def addExit(self, name, exit):
                self('exits', {})[name] = exit
            def addSearch(self, search):
                self['searches'].append(search)

        class MobileData(Object):
            __module__ = __name__ + '.Environment.ZoneData'

            class Affections(Object):
                __module__ = __name__ + '.Environment.MobileData'

        class ItemData(Object):
            __module__ = __name__ + '.Environment.ZoneData'

            class Anticlass(Object):
                __module__ = __name__ + '.Environment.ZoneData.ItemData'
            class Wearable(Object):
                __module__ = __name__ + '.Environment.ZoneData.ItemData'
            class Affection(Object):
                __module__ = __name__ + '.Environment.ZoneData.ItemData'

            def addAffect(self, to, modifier):
                self['affects'].append(self.Affection(to = to, modifier = modifier))

        def addCommands(self, position, commands):
            self['commands'].append(self.ZCmd.Position(position = position,
                                                       commands = commands))
        def addRoom(self, room):
            self['rooms'].append(room)
        def addMobile(self, mobile):
            self['mobiles'].append(mobile)
        def addItem(self, item):
            self['items'].append(item)

    def addDocument(self, doc):
        self('documents', {})[doc.source.getName()] = doc
        doc.environment = self

    def addOlcZone(self, zone):
        self('olc', Object(__attributes__ = ['zones'])) \
                        ('zones', {})[zone.vnum] = zone

    class Wizard:
        __module__ = __name__ + '.Environment'

        class Command(Object):
            __module__ = __name__ + '.Environment.Wizard'
            __attributes__ = ['verb', 'codeType', 'action']

            class Verb(Object):
                __module__ = __name__ + '.Environment.Wizard.Command'
                __attributes__ = ['verb']
            class Code(Object):
                __module__ = __name__ + '.Environment.Wizard.Command'
                __attributes__ = ['type', 'source']

            def __init__(self, xxx_todo_changeme, requirements, xxx_todo_changeme1):
                (action, verb) = xxx_todo_changeme
                (source, codeType, code) = xxx_todo_changeme1
                Object.__init__(self, verb = self.Verb(action = action, verb = verb),
                                requirements = Object(**requirements),
                                code = self.Code(type = codeType, source = source, code = code))

    def addModule(self, module):
        self['modules'].append(module)

# Compatability Mode (flatten for strict pickle):
##    Environment:
##        ZoneData:
##            ZCmd:
##                RoomCommand:
##                    DoorState
##                MobileCommand:
##                    EquipmentCommand
##                ItemCommand
##                Position
##                RemoveItem
##            RoomData:
##                ExitData
##                SearchData
##            MobileData:
##                Affections
##            ItemData:
##                Anticlass
##                Wearable
##                Affection
##
##        Wizard:
##            Command:
##                Verb
##                Code

ZoneData = Environment.ZoneData
ZCmd = ZoneData.ZCmd
RoomCommand = ZCmd.RoomCommand
DoorState = RoomCommand.DoorState
MobileCommand = ZCmd.MobileCommand
EquipmentCommand = MobileCommand.EquipmentCommand
ItemCommand = ZCmd.ItemCommand
Position = ZCmd.Position
RemoveItem = ZCmd.RemoveItem
RoomData = ZoneData.RoomData
ExitData = RoomData.ExitData
SearchData = RoomData.SearchData
MobileData = ZoneData.MobileData
Affections = MobileData.Affections
ItemData = ZoneData.ItemData
Anticlass = ItemData.Anticlass
Wearable = ItemData.Wearable
Affection = ItemData.Affection
Wizard = Environment.Wizard
Command = Wizard.Command
Verb = Command.Verb
Code = Command.Code

for _obj in (ZoneData, ZCmd, RoomCommand, DoorState, MobileCommand,
             EquipmentCommand, ItemCommand, Position, RemoveItem,
             RoomData, ExitData, SearchData, MobileData, Affections,
             ItemData, Anticlass, Wearable, Affection, Wizard, Command,
             Verb, Code):
    _obj.__module__ = __name__
    _obj.__name__ = _obj.__name__.split('.')[-1]

# Testing Front End.
from pickle import Unpickler, Pickler
import sys

class ClassfulUnpickler(Unpickler):
    def find_class(self, module, name):
        # This handles nested classes.
        module = module.split('.')
        __import__(module[0])
        mod = sys.modules[module[0]]

        for n in module[1:]:
            mod = getattr(mod, n)

        klass = getattr(mod, name)
        return klass

def main(argv = None):
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-p', '--pickle')
    parser.add_option('-u', '--unpickle')

    (options, args) = parser.parse_args(argv)

    global env
    if options.unpickle:
        env = ClassfulUnpickler(open(options.unpickle)).load()
    else:
        env = Environment()
        loader = Loader(env)

        for name in args:
            loader.loadDocument(FileSource(name))

        if options.pickle:
            Pickler(open(options.pickle, 'w')).dump(env)

if __name__ == '__main__':
    main()
