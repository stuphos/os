# Utilizes libdata.
# Todo: Load into world.entities!


# Todo: this function name says nothing about what it does.  In this case 'new' means 'load' from index.
def newWorld(stuphlib, base, index = None, cascade = False, verbose = False):
    if verbose: from sys import stdout as logging
    else: logging = None

    base = stuphlib.dblib.LocalIndex(base)
    if index:
        w = stuphlib.wldlib.World(base, stuphlib.dblib.isAbsIndex(index), logStream = logging)
        w.loadFromZoneIndex(index, cascade = cascade)
    else:
        w = stuphlib.wldlib.World(base, logStream = logging)
        w.loadFromZoneIndex(cascade = cascade)

    return w

class Database:
    # World & Adjunct Records.
    def __init__(self, stuphlib, worldModule, world_dir, zone_index = None, cascade = False, verbose = False):
        self.stuphlib = stuphlib
        self.worldModule = worldModule

        self.world_dir = world_dir
        self.zone_index = zone_index
        self.cascade = cascade
        self.verbose = verbose

        self.world = None

        # from game.misc import profile
        # self.boot = profile(filename = 'db.boot.prof')(self.boot)

    def __repr__(self):
        return '[DB %r]' % self.world

    def boot(self):
        self.world = newWorld(self.stuphlib,
                              self.world_dir,
                              self.zone_index,
                              self.cascade,
                              self.verbose)

        # Load into world entities!
        from sys import stderr as logOutput

        if self.verbose:
            print('Internalizing World...', file = logOutput)

            from stuphos.etc.tools.timing import Elapsed
            e = Elapsed()

        for z in self.world.zones:
            if self.verbose:
                logOutput.write('\rLoading %r...' % z)
                logOutput.flush()

            # import pdb; pdb.set_trace()
            zone = self.worldModule.zone.create(record = z)

            # Patch up.
            z.resetReady = zone.resetReady
            z.reset = zone.reset

            for r in z.rooms:
                try: room = zone.createRoom(r.vnum, zone = zone, record = r)
                except ValueError:
                    print('ERROR: Room %r already exists!' % r, file = logOutput)

            for i in z.items:
                try: item = zone.createItem(i.vnum, zone = zone, record = i)
                except ValueError:
                    print('ERROR: Item %r already exists!' % i, file = logOutput)

            for m in z.mobiles:
                try: mob = zone.createMobile(m.vnum, zone = zone, record = m)
                except ValueError:
                    print('ERROR: Mobile %r already exists!' % m, file = logOutput)

        if self.verbose:
            print(file = logOutput) # the newline
            print('...', e, 'Resolving Exits...', file = logOutput)

            e = Elapsed()

        self.resolve_exits()

        if self.verbose:
            print('...', e, file = logOutput)

    def resolve_exits(self):
        def resolveRoomExits(room):
            for exit in room.exits:
                # Dereference real room.
                try: r = self.worldModule.room(exit.roomlink)
                except ValueError:
                    # Mini-mud?
                    r = None

                exit.room = exit.destination = r


        self.worldModule.iterate_entities(self.worldModule.room, resolveRoomExits)

    def zoneUpdate(self, sec, usec):
        def resetZone(zone):
            if zone.resetReady():
                self.resetZone(zone)

        self.worldModule.iterate_entities(self.worldModule.zone, resetZone)

    def resetZone(self, zone):
        # Emit lifecycle events.
        # Cycle through zone commands.
        print('Resetting', repr(zone))
        zone.reset()

    def printMaster(self):
        for zone in self.worldModule.zone.table.values():
            print(zone)


    def resetWorld(self, *args, **kwd):
        # Only run if stuphmud.server.zones.controller.ZoneReset is a service.
        zreset = runtime[runtime.StuphMUD.Zone.Controller]
        if zreset is not None:
            if self.verbose:
                print('[System Database] Resetting World...')

            return zreset.resetWorld(*args, **kwd)
