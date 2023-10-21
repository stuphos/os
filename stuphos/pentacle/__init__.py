# Pentacle - The out-of-band binary telnet protocol interface.
# Note: this should probably go in mud.management, because it qualifies as a high-
# level service, but it's also trying to be low-level.
# Todo: move into mud.management.
from stuphos.runtime.facilities import Facility

# Protocol:
#   Challenge/Handshake for hashing password but only sending the hash for auth.

class Pentacle(Facility):
    NAME = 'Network::Telnet::Pentacle'

    @classmethod
    def create(self):
        return newComponent(self)

    # Component Architecture.
    def onTelnetCommand(self, ctlr, peer, tc):
        pass
