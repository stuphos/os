import world

from world.player import playerByID
from world.player.nanny import CON_GET_NAME

    # players = world.player.players
    # zone = world.zone
    # room = world.room
    # item = world.item
    # mobile = world.mobile
    # iterate_entities = world.iterate_entities

# from stuphos.runtime.facilities import Facility

try: import game
except ImportError:
    # Copy of framework/game.py
    from stuphos.system.game import *

    import world

    from world import peer, mobile_instance, player_character, getPlayerStoreByName, iteratePlayerIDs, findPlayerNameByID, SPECIAL
    from world.player import getMasterCommandList, interpretCommand, loadPlayer, EnableConsole
    from world.player import nanny, commands
    from world.player.commands import lookAtRoom

else:
    from .game import mudlog, syslog, iterateOLCAccessByName
