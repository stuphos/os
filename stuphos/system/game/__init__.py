# Synthetic Game Module
# --
# (C) 2021 runphase.com .  All rights reserved.
#

from .compartment import *

# These things need to be explicitly imported because of their usage through the application.
# To rely on game module for a particular implementation means that your application should
# upgrade to be using compartment.  In otherword, relying on game module except in a limited
# embedded context, is being obseleted.

# from compartment.world import new_peer

from .compartment.system import mudlog, boot_time, Heartbeat, Heartbeat as Engine
from .compartment.system import getCmdln, parseCmdln, Core, Game, mudlog as log
#from compartment.system.access import hasOLCAccessByName, iterateOLCAccessByName, shutdownMother
# from compartment.system.circle import mini_mud

# from compartment.misc import NanoText, registerRealPath, columnize
from .compartment.misc import *

# from compartment.world import peer, mobile_instance, player_character, getPlayerStoreByName, iteratePlayerIDs, findPlayerNameByID, SPECIAL
# from compartment.world.player import getMasterCommandList, interpretCommand, loadPlayer, EnableConsole
# from compartment.world.player import nanny, commands
# from compartment.world.player.commands import lookAtRoom

# from compartment.cli import Console


# The problem is that, if you're using this game module, we assume that you're using all of
# the intended functionality in the parallel package.  We do that individually here.

from .compartment import system
# from .compartment import world
# from .compartment import engine
from .compartment import format
from .compartment import misc
# from compartment import emulation


def iterateOLCAccessByName(name):
	return []
