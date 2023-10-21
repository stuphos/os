##    MIME-Version: 1.0
##    Content-Type: text/plain
##    X-Checkpoint-Command-Type: application/x-stuph-python-script

#X-Code-Source: http://www.penobscotrobotics.us/team/admin
#X-Code-Source: automatic
#X-Script-Name: penro.team.admin
#X-Script-Debug: on

# Incorporate a new componentized facility into the core.
from stuphos.runtime.facilities import Facility
from stuphos.runtime import Synthetic

class TeamCore(Facility):
    NAME = 'PenobscotRobotics::Team::Core'
    COMPONENT = True

    class Manager(Facility.Manager):
        VERB_NAME = 'penro-*team-core'
        # todo: commands that add/remove members!

    ##    def __init__(self):
    ##        self.members = # load from file/database

    # Watch the world:
    def onEnterGame(self, ctlr, peer, player):
        # todo: add this property only if it's a team member!!
        # player.properties.team = Synthetic(name = 'penro')

        player.team = Synthetic(name = 'penro',
                                core = self)

    def __str__(self):
        return '{Team Members: 0}'

if TeamCore.CreateNew(andManage = True):
    from stuphos.system.api import syslog, mudlog

    message = '%s Created: %s' % (TeamCore.NAME, TeamCore.get())
    mudlog(message)
    syslog(message)
