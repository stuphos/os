# MUD Runtime -- Computing API
# --
# A centralized application platform core that objectifies its implementing
# components in relation to the interface layers.
#
# It also contains the instruction execution processing modules.

from .events import *
from .architecture import *

from . import registry

# Todo: Perform object registration later during boot cycle.
#@runtime.MUD.Runtime.API
class Runtime(registry.Access):
    # System classification.

    # This could be documented much better:
    # ---
    # Represents the main access object for mud runtime layer.
    # Utilizes registry access base class for addressing the
    #    named object directory.
    #
    # The actual instance is created by registry subroutines.
    # Should probably be a Singleton.

    pass

MudRuntime = Runtime


# Event Names.
EVENT_NAMES = ['bootStart'                  ,'bootComplete'               ,
               'resetStart'                 ,'resetComplete'              ,
               'greetPlayer'                ,'welcomePlayer'              ,
               'makePrompt'                 ,'loadPlayerStore'            ,
               'playerSavePoint'            ,'startRentSave'              ,
               'completeRentSave'           ,'startRentLoad'              ,
               'completeRentLoad'           ,'deleteRentFile'             ,
               'idleToVoid'                 ,'timedOut'                   ,
               'helpQueryNotFound'          ,'helpQueryUnfinished'        ,
               'helpQueryComplete'          ,'doPython'                   ,
               'createItemPrototype'        ,'createItemInstance'         ,
               'extractItemInstance'        ,'createMobilePrototype'      ,
               'createMobileInstance'       ,'extractMobileInstance'      ,
               'movement'                   ,'dealDamage'                 ,
               'slayMobile'                 ,'purgeMobile'                ,
               'deathTrap'                  ,'createRoom'                 ,
               'startZoneReset'             ,'endZoneReset'               ,
               'itemToRoom'                 ,'itemFromRoom'               ,
               'itemToContainer'            ,'itemFromContainer'          ,
               'itemToCarrier'              ,'itemFromCarrier'            ,
               'mobileToRoom'               ,'mobileFromRoom'             ,
               'lookAtRoom'                 ,'firstSpecial'               ,
               'lastSpecial'                ,'mudlog'                     ,
               'telnetCommand'              ,'writeItemPrototypeStart'    ,
               'writeItemPrototypeComplete' ,'startSpellAssign'           ,
               'startSkillAssign'           ,'newConnection'              ,
               'disconnection'              ,'enterGame'                  ,
               'quitGame'                   ,'newPlayer'                  ,
               'loadZone'                   ,'createZone'                 ,
               'castSpellSuperior'          ,'startSpellCast'             ,
               'completeSpellCast'          ,'callMagic'                  ,
               'saySpell'                   ,'lookupSkill'                ,
               'setSpellLevel'              ,'sendMail'                   ,
               'switchCutBy'                ,'unswitchForcedBy'           ,
               'usurpedBy'                  ,'duplicateKilledBy'          ,
               'reconnection'               ,'usurped'                    ,
               'passwordChange'             ,'shutdownGame'               ,
               'playerInput'                ,'playerActivation'           ,
               'performAct'                 ,'startZoneReset'             ,
               'completeZoneReset'          ,'portalOut'                  ,
               'portalIn'                   ,'manualSpell'                ,
               'libraryNode'                ,'loggedIn']

BINDINGS = \
    """
    [MemberResolution]
     # The heartbeat object is implemented directly, not as a binding.
     #  (see mud.installBridge)
     # heartbeat                   world.heartbeat.pulse # (Bridge Module)

     shutdownGame                stuphmud.server.shutdownGame

     doPython                    stuphmud.server.player.doPython
     newConnection               stuphmud.server.player.interpret

     # login                       stuphmud.server.player.login
     loggedIn                    stuphmud.server.player.loggedIn
     enterGame                   stuphmud.server.player.enterGame

     newPlayer                   stuphmud.server.player.newPlayer

     greetPlayer                 stuphmud.server.player.greetPlayer
     welcomePlayer               stuphmud.server.player.welcomePlayer

     lookAtRoom                  stuphmud.server.player.lookAtRoom

     makePrompt                  stuphmud.server.player.shell.makePrompt

     telnetCommand               stuphmud.server.player.telnet.process_command

     performAct                  stuphos.triggers.performAct
     slayMobile                  stuphos.triggers.slayMobile
     createMobileInstance        stuphos.triggers.createMobileInstance

     departure                   stuphos.triggers.departure
     arrival                     stuphos.triggers.arrival

     portalOut                   stuphos.triggers.portalOut
     portalIn                    stuphos.triggers.portalIn

     lookupSkill                 stuphmud.server.lang.magic.lookupSkill
     manualSpell                 stuphmud.server.lang.magic.manualSpell

     # writeItemPrototypeStart     stuphmud.server.zones.olc.writeItemPrototypeStart
     # writeItemPrototypeComplete  stuphmud.server.zones.olc.writeItemPrototypeComplete

    ## playerSavePoint           stuphmud.server.player.db.playerSavePoint
    ## loadPlayerStore           stuphmud.server.player.db.loadPlayerStore

    ## deleteRentFile            stuphmud.server.deleteRentFile

    ## createMobileInstance      zones.MobileCreation
    ## createItemInstance        zones.ItemCreation

    [Logging]
    ##     quitGame                
    ##     disconnection           
    ##     idleToVoid              
    ##     timedOut                
    ##
    ##     helpQueryNotFound       
    ##     helpQueryUnfinished     
    ##     helpQueryComplete       
    ##
    ##     startRentSave           
    ##     completeRentSave        
    ##     startRentLoad
    ##     completeRentLoad
    ##
    ##    ## extractMobileInstance   
    ##    ## extractItemInstance     
    ##
    ##    ## startZoneReset          
    ##    ## endZoneReset            
    ##
    ##     createMobilePrototype   
    ##     createItemPrototype     
    ##     createZone              
    ##     createRoom              
    ##
    ##    ## movement                
    ##    ## dealDamage              
    ##
    ##     slayMobile              
    ##     purgeMobile             
    ##     deathTrap               
    ##
    ##     startSpellAssign
    ##     telnetCommand
    """
