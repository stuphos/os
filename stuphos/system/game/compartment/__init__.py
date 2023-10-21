# Compartment Server.
# (C) 2021 runphase.com .  All rights reserved.
# --
# This comprises the standalone server provision that hosts the application,
# by building on stuphos.system, and also contains an implementation
# of the game module, such that the embedding aspects of the application
# software can perform where the extension protocol is expected.
#
#     So this means that embedding/extension aspects that are throughout
#     the application package need to be unified in some independent
#     package, but because they are still integrated, this compartment
#     is built from the synthesis of a game module for a non-embedding
#     provision that implements extension protocol.
#
#     The nominal 'game' module is provided parallel to this package,
#     adopts all of the functionality of this package for protocol
#     purposes, but this is the package that you run when not embedding.
#

import sys
import warnings

warnings.warn("module '%s' is not native" % __name__,
              ImportWarning, stacklevel = 1)

version = '1.0'

framework = True
embedded = False

import world
sys.modules['world'] = world

# Older versions of pickles might rely on this existing.
sys.modules['game.world'] = world

syslog_cr = True # Add CR to end of syslog lines.


def installWorldBridge():
    # Provide role of game bindings.
    world.installEventBridge()

def bridgeModule():
    # This is required by the mud runtime.
    return world

def syslog(*args):
    args = ' '.join(map(str, args))
    if syslog_cr:
        args += '\r'

    # debugOn()
    print(args, file = sys.stderr)

# Construct engine operations -- Do this after defining the above bit of game.
# XXX This should be done outside of the gamemodule (in the Extension Library) :skip:

# Yeah, because this is a gamemodule replacement.  So this doesn't have any
# purpose except where wrapping the dll..

# Currently causes segv (stackdump) crash on exit:
##    try: from mud.api import Main
##    except ImportError: pass
##    else: mainOps = Main()

def installBridge(bridge = None):
    # Install Event Bridge onto MUD-Package object.
    # This works sensibly because bootStart isn't on the bridge.
    if bridge is None:
        import builtins as builtin

        try: bridge = builtin.StuphMUD
        except AttributeError:
            from stuphos.runtime import EventBridge
            bridge = builtin.StuphMUD = EventBridge()

    for (api, event) in (('NewIncomingPeer'    , 'newConnection' ),
                         ('GreetPlayer'        , 'greetPlayer'   ),
                         ('FirstSpecialCommand', 'firstSpecial'  ),
                         ('LastSpecialCommand' , 'lastSpecial'   ),
                         ('StartWorldReset'    , 'resetStart'    ),
                         ('CompleteWorldReset' , 'resetComplete')):

        setattr(bridge, api, event)

    installWorldBridge()
