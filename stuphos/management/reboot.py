"""
Please note that processes compiled with -pg profiling may not use the exec*
family of system calls (which this program does to initiate the reboot).

Invoking execve will cause the process to abort and print this message to stderr:
Profiling timer expired

"""
__all__=['Copyover']
# bootIntoMiniMUD=True # On reboot, give the new process the -m cmdln switch

import stuphos
import stuphmud.server.player

# XXX dependencies:
from stuphos.system.api import game, world, syslog

from os import execl, close, getenv, unlink, environ, rename # putenv as setenv
from os import chdir, getcwd
from os.path import join as joinpath, dirname
from marshal import dump, load
from traceback import print_exc
from time import time as now
from pprint import pformat

try : from fcntl import fcntl, F_SETFD, F_GETFD, FD_CLOEXEC
except ImportError:pass

def setenv(n, x):
    'This puts the string value of object into the environment for given key.'
    # environ is an instance of the _Environ class, which wraps getenv/putenv
    # in index or slice methods.  So this calls putenv.  Why doesn't putenv
    # work when invoked directly!?
    environ[n]=str(x)

COPYOVERKEY = 'STUPH_COPYOVER_KEY'
STUPHBIN    = 'bin/stuph' # sys.argv[0]
EXENAME     = STUPHBIN # 'stuph'
DFLTKEY     = 'default'

def persistSocket(fd):
    'This is broken because ~1 returns -2!  Fortunately, sockets seem to be !FD_CLOEXEC initially.'
    oldbits=fcntl(fd, F_GETFD)
    newbits=oldbits & ~FD_CLOEXEC

    #print oldbits, '&', '~%d' % FD_CLOEXEC, '(%d)' % ~FD_CLOEXEC, '=', newbits

    ##fcntl(fd, F_SETFD, newbits)
    return fd

class Copyover:
    """
    Implementation of Network Session Persistance.

    Do a clean reboot (or copyover):
       Save file descriptors, (unset close on exec), write to file (etc/network-sessions.pkl)
       Say goodbye to everyone??
       Re-execute the mud in this process-space.

       Possibly make the copyover process part of the serialization/deserialization of this class.

    The instance of a Copyover class is constructed with unique identifier of the netsessions store,
    and the methods implemented can be used for either initiating a copyover reboot, or recovering
    from a copyover, and the sharing of the netsessions key across the process (the environment).
    """

    # If path does not exist, disable Copyover?
    NETSESSION_PATH='etc/network-sessions'
    DefaultKey=DFLTKEY

    def __init__(self, exepath, key=DefaultKey, *args):
        self.exepath = exepath
        self.exename = exepath
        self.key     = key
        self.store   = self.findStore(key)

        # Todo: From mud.config:
        # Force server:
        self.args    = ('-server', ) + args

        # Optional setting:
        if self.isMiniMUD():
            self.args += ('-m',)

        # Specifying the mudlib dir will cause changing into it on post.
        # self.args += ('-l', getcwd())

    def isMiniMUD(self):
        setting = globals().get('bootIntoMiniMUD')
        if setting is not None:
            return bool(setting)

        setting = stuphos.getConfig('mini-mud', 'Copyover')
        if setting is not None:
            setting = setting.lower()
            if setting in ('true', 'on', 'yes', '1'):
                return True
            if setting in ('false', 'off', 'no', '0'):
                return False

        # Is currently in minimud
        try: from stuphos.system.api import game
        except ImportError: mini_mud = game.mini_mud
        else:
            if mini_mud():
                return True

        return False

    ## Store management:
    def findStore(self, key):
        'Give a file or system name to the netsession key.'
        if key=='default': # or key.upper()=='DEFAULT'
            return self.NETSESSION_PATH+'.bin'

        return joinpath(self.NETSESSION_PATH, str(key)) # + '.bin'

    def dumpToStore(self, data):
        # dump(data, open(self.store, 'wt'))
        from stuphmud.server.zones.freeze import dumpFile
        dumpFile(data, self.store)

    def loadStore(self):
        # return load(open(self.store))
        from stuphmud.server.zones.freeze import loadFile
        return loadFile(self.store)

    def destroyStore(self):
        # unlink(self.store)
        rename(self.store, '%s.trash' % self.store)

    def getStore(self):
        try: return self._loaded_store
        except AttributeError:
            st = self._loaded_store = self.loadStore()
            return st

    ## Persistant data:
    def avatarData(self, a):
        if not a: # or a.peer.state!='Playing'
            return {}

        return {
            'name'   : a.name,
            'room'   : a.room is not None and a.room.vnum or -1,
        }

    def playerData(self, p):
        'Do a selection of data from the player for persisting.'
        if p.state!='Playing':
            return None

        data={
            'socket' : persistSocket(p.descriptor),
            'host'   : p.host,
            'state'  : p.state,
            'input'  : p.input_queue,
        }

        data.update(self.avatarData(p.avatar))

        return data

    def mudData(self, options):
        data = {
            # 'mother'  : -1, # world.getMother(),
            'players' : [_f for _f in map(self.playerData, world.player.users()) if _f],
            'time'    : now(),
        }

        if options.world or options.complete:
            from stuphmud.server.zones.freeze import dumpWorldData
            data['world'] = dumpWorldData(options)

        return data

    ## Reboot process:
    def initiate(self, options):
        'Save player data and invoke the reboot procedure (doReboot).'
        syslog('Initiating Copyover Reboot...')

        # Write persistant data to store
        data = self.mudData(options)
        #game.syslog('\n'+pformat(data))
        self.dumpToStore(data)

        # Save everyone to playerfile, giving it that special key.
        # This will eventually be separated with some kind of database interface.
        game.library.save_all_players('Closing Player File')

        # Do this step so that the mother-socket regenerates itself rather than being saved.
        # If it did persist across exec, would that mean the backlog of awaiting acceptees
        # would remain?  (who cares)
        #
        # What about platforms where the child connections require that the mother socket
        # stay open?  Is this a case on any system?
        #
        # It is important to code this correctly, because all of the players are already
        # closed (meaning that the descriptor_data don't exist anymore).
        game.shutdownMother()

        # save_mud_time

        # Initiate reboot process.  Perhaps notify log that we're really doing it now..
        # If we want to tell everyone we're initiating a copyover, we'll have to have
        # done that during the previous heartbeat pulse, because we're going down NOW!

        # Step out of this directory and into parent directory, because we'll want
        # to chdir right back into it.
        # The real reason
        chdir(dirname(getcwd()))
        # ...Or, since the chdir facility exists with -l option, just rely on that.
        # Seems more formal.

        setenv(COPYOVERKEY, self.key)
        execl(self.exepath, self.exename, *self.args)

    __call__ = initiate

    ## Recovery process:
    def recoverPlayer(self, p):
        # Instantiating a peer descriptor from this stratum requires an avatar to connect to:
        avatar = world.player.loadPlayer(p['name'], p['room'])
        peer   = world.player.emergePlayer(p['socket'], p['state'], avatar)

        # Check for deleted character??
        # The CON_GET_NAME login state also removes:
        #    PLR_WRITING | PLR_MAILING | PLR_CRYO | PLR_CREATING | PLR_INWAR
        #    AFF_GROUP
        # in case they were saved in the file.

        # unrent is Crash_load.  Additionally, the following steps pick up
        # where the enter-game code from nanny() leaves off.
        avatar.unrent()
        avatar.save()

        # Set peer.last_host to pc_store.host
        # Set peer.login to pc_store.last_logon

        # world.newConnection(peer)
        peer.host = p['host']
        mud.player.interpret(peer)

        for input in p.get('input') or []:
            peer.input = input

        # Notify log of each individual recovery..?  unrent/Crash_load notifies the log..
        print('&r*&yWelcome Back From Copyover&r*&N', file=peer)

        # XXX I think there's a problem with just calling this now...
        # Why doesn't enter game seem to install the programs??
        #
        # This is why I introduced playerActivation, which is removed from
        # any newConnection/enterGame nonsense, because these things won't
        # happen after copyover (yet the extension runtime still needs to
        # be awakened).
        if avatar.room:
            mud.player.enterGame(peer, avatar)

    def recoverMother(self, socket):
        """
        Instead of copying over the mother socket, it could be set Close-On-Exec.
        Since the stuphMUDGame (and hence FixupMother) isn't instantiated when the
        mud package module imports tools.reboot (hence initiating copyover recovery),
        we can't use fixupMother at this point.

        """
        # world.fixupMother(socket)

    def recover(self):
        # Load persistance data store (netsession)
        mudData = self.getStore()

        #game.syslog('\n'+pformat(mudData))
        syslog('Recovering from Copyover...')

        # Calculate time from mudData['time']

        # Fixup the mother socket
        # self.recoverMother(mudData['mother'])

        # Connect those players back into the mud, logging them in.
        # Bump off or re-authenticate those that don't jive.
        for p in mudData['players']:
            try    : self.recoverPlayer(p)
            except : print_exc()

        worldData = mudData.get('world')
        if worldData:
            from stuphmud.server.zones.freeze import loadWorldData
            loadWorldData(worldData)

        self.destroyStore()
        # gc.collect()

## Check for copyover when this module is loaded such that this module
## must be loaded after a copyover to ensure complete recovery.
#
## Issues of recovering from here:
##    Since this would occur during the mud/__init__.py script, the game hasn't
##    even been initialized yet: stuphMUDGame hasn't been instantiated, so the
##    mother socket isn't open, nothing's initialized, including the player file.
##
##    Perhaps recovery should go in world-load.
#
# This is implemented in the boot procedures found in the mud module code.

def StartRecovery():
    'Call this basically once per boot (from world load).'

    key = getenv(COPYOVERKEY)
    if key:
        global _active_copyover
        _active_copyover = Copyover(STUPHBIN, key)

        if _active_copyover.getStore().get('world'):
            # As last component:
            from stuphos.runtime import Component, eventResult
            class Recovery(Component):
                def onResetStart(self, ctlr):
                    # todo: uninstall this component:
                    return eventResult(True)

def CompleteRecovery():
    active = globals().get('_active_copyover')
    if active is not None:
        def recover():
            try: active.recover()
            except:
                syslog('Reboot Recovery N/A')
                from traceback import print_exc; print_exc()
            finally:
                del globals()['_active_copyover']

        from stuphos import enqueueHeartbeatTask
        enqueueHeartbeatTask(recover)

def Reboot(options):
    Copyover(STUPHBIN, DFLTKEY).initiate(options)


## -- Misc. --

def doReboot(*args):
    execl(STUPHBIN, EXENAME, '-server', *args)

## Spawn a new process that waits for its parent (this process) to die,
## whereby it executes another instance of stuph, possibly after a delay.
#
# This isn't necessary with supervisory program + auto-cycle.

# Command Overlay.
MINIMUM_COPYOVER_LEVEL = 115
def doCopyover(peer, cmd, argstr):
    args = argstr.split() if argstr else []
    if not args or args[0].lower() not in ('copy-over', 'copyover'):
        return False

    if peer.avatar and peer.avatar.level >= MINIMUM_COPYOVER_LEVEL:
        del args[0] # Not needed in freeze subsystem.

        from stuphmud.server.zones.freeze import getValidCmdlnOptions
        try: options = getValidCmdlnOptions(args)
        except SystemExit:
            return True

        from world.player import players
        for player in players():
            print('&r*&yInitiating Copyover, %s Saved&r*&N' % \
                  (player.avatar and player.avatar.name or 'Character'), file=player)

            print('Standby...', file=player)

        # XXX Not timed or confirmed!  (todo: modify act.wizard.cpp shutdown apparatus)
        from stuphos import enqueueHeartbeatTask
        enqueueHeartbeatTask(Reboot, options)
        return True

try: from stuphmud.server.player import ACMD
except ImportError: pass
else: ACMD('shutdown*')(doCopyover)
