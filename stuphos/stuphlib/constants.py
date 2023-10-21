# Scalar Constants.
LVL_IMPL = 115
LVL_ARCH_GOD = 114
LVL_ETERNAL_GOD = 113
LVL_GOD = 112
LVL_OVERSEER = 111
LVL_CREATOR = 110
LVL_DEMIGOD = 109
LVL_DEITY = 108
LVL_IMMORT = 107
LVL_AVATAR = 106

# debugOn()

# For CircleMUD adapters.
try: from world import LVL_IMMORT, LVL_IMPL # , LVL_GOD, LVL_GRGOD
except ImportError: pass

# Aliases.
LVL_SUPREME = LVL_IMPL
LVL_FREEZE = LVL_OVERSEER

# spells.h:
DEFAULT_STAFF_LVL   = 12
DEFAULT_WAND_LVL    = 12

CAST_UNDEFINED  = (-1)
CAST_SPELL  = 0
CAST_POTION = 1
CAST_WAND   = 2
CAST_STAFF  = 3
CAST_SCROLL = 4

MAG_DAMAGE      = (1 << 0)
MAG_AFFECTS     = (1 << 1)
MAG_UNAFFECTS   = (1 << 2)
MAG_POINTS      = (1 << 3)
MAG_ALTER_OBJS  = (1 << 4)
MAG_GROUPS      = (1 << 5)
MAG_MASSES      = (1 << 6)
MAG_AREAS       = (1 << 7)
MAG_SUMMONS     = (1 << 8)
MAG_CREATIONS   = (1 << 9)
MAG_MANUAL      = (1 << 10)


TYPE_UNDEFINED               = (-1)
SPELL_RESERVED_DBC             = 0  # SKILL NUMBER ZERO -- RESERVED

# PLAYER SPELLS -- Numbered from 1 to MAX_SPELLS

SPELL_ARMOR                   = 1 # Reserved Skill[] DO NOT CHANGE
SPELL_TELEPORT                = 2 # Reserved Skill[] DO NOT CHANGE
SPELL_BLESS                   = 3 # Reserved Skill[] DO NOT CHANGE
SPELL_BLINDNESS               = 4 # Reserved Skill[] DO NOT CHANGE
SPELL_BURNING_HANDS           = 5 # Reserved Skill[] DO NOT CHANGE
SPELL_CALL_LIGHTNING          = 6 # Reserved Skill[] DO NOT CHANGE
SPELL_CHARM                   = 7 # Reserved Skill[] DO NOT CHANGE
SPELL_CHILL_TOUCH             = 8 # Reserved Skill[] DO NOT CHANGE
SPELL_ENTANGLE                = 9 # Reserved Skill[] DO NOT CHANGE
SPELL_COLOR_SPRAY            = 10 # Reserved Skill[] DO NOT CHANGE
SPELL_CONTROL_WEATHER        = 11 # Reserved Skill[] DO NOT CHANGE
SPELL_CREATE_FOOD            = 12 # Reserved Skill[] DO NOT CHANGE
SPELL_CREATE_WATER           = 13 # Reserved Skill[] DO NOT CHANGE
SPELL_CURE_BLIND             = 14 # Reserved Skill[] DO NOT CHANGE
SPELL_CURE_CRITIC            = 15 # Reserved Skill[] DO NOT CHANGE
SPELL_CURSE                  = 17 # Reserved Skill[] DO NOT CHANGE
SPELL_DETECT_ALIGN           = 18 # Reserved Skill[] DO NOT CHANGE
SPELL_DETECT_INVIS           = 19 # Reserved Skill[] DO NOT CHANGE
SPELL_DETECT_MAGIC           = 20 # Reserved Skill[] DO NOT CHANGE
SPELL_DETECT_POISON          = 21 # Reserved Skill[] DO NOT CHANGE
SPELL_DISPEL_EVIL            = 22 # Reserved Skill[] DO NOT CHANGE
SPELL_EARTHQUAKE             = 23 # Reserved Skill[] DO NOT CHANGE
SPELL_ENCHANT_WEAPON         = 24 # Reserved Skill[] DO NOT CHANGE
SPELL_ENERGY_DRAIN           = 25 # Reserved Skill[] DO NOT CHANGE
SPELL_FIREBALL               = 26 # Reserved Skill[] DO NOT CHANGE
SPELL_HARM                   = 27 # Reserved Skill[] DO NOT CHANGE
SPELL_HEAL                   = 28 # Reserved Skill[] DO NOT CHANGE
SPELL_INVISIBLE              = 29 # Reserved Skill[] DO NOT CHANGE
SPELL_LIGHTNING_BOLT         = 30 # Reserved Skill[] DO NOT CHANGE
SPELL_LOCATE_OBJECT          = 31 # Reserved Skill[] DO NOT CHANGE
SPELL_MAGIC_MISSILE          = 32 # Reserved Skill[] DO NOT CHANGE
SPELL_POISON                 = 33 # Reserved Skill[] DO NOT CHANGE
SPELL_PROT_FROM_EVIL         = 34 # Reserved Skill[] DO NOT CHANGE
SPELL_REMOVE_CURSE           = 35 # Reserved Skill[] DO NOT CHANGE
SPELL_SANCTUARY              = 36 # Reserved Skill[] DO NOT CHANGE
SPELL_SHOCKING_GRASP         = 37 # Reserved Skill[] DO NOT CHANGE
SPELL_SLEEP                  = 38 # Reserved Skill[] DO NOT CHANGE
SPELL_STRENGTH               = 39 # Reserved Skill[] DO NOT CHANGE
SPELL_SUMMON                 = 40 # Reserved Skill[] DO NOT CHANGE
SPELL_VENTRILOQUATE          = 41 # Reserved Skill[] DO NOT CHANGE
SPELL_WORD_OF_RECALL         = 42 # Reserved Skill[] DO NOT CHANGE
SPELL_REMOVE_POISON          = 43 # Reserved Skill[] DO NOT CHANGE
SPELL_SENSE_LIFE             = 44 # Reserved Skill[] DO NOT CHANGE
SPELL_ANIMATE_CORPSE         = 45 # Reserved Skill[] DO NOT CHANGE
SPELL_DISPEL_GOOD            = 46 # Reserved Skill[] DO NOT CHANGE
SPELL_GROUP_ARMOR            = 47 # Reserved Skill[] DO NOT CHANGE
SPELL_GROUP_HEAL             = 48 # Reserved Skill[] DO NOT CHANGE
SPELL_GROUP_RECALL           = 49 # Reserved Skill[] DO NOT CHANGE
SPELL_INFRAVISION            = 50 # Reserved Skill[] DO NOT CHANGE
SPELL_WATERWALK              = 51 # Reserved Skill[] DO NOT CHANGE
SPELL_IDENTIFY               = 52
SPELL_FLY                    = 53
SPELL_FIRESHIELD             = 54
SPELL_WHUPASS                = 55
SPELL_PHASE_BLUR             = 56
SPELL_PASS_DOOR              = 57
SPELL_CREATE_SPRING          = 58
SPELL_CONTINUAL_LIGHT        = 59
SPELL_TELEPORT_OBJECT        = 60
SPELL_STONESKIN              = 61
SPELL_BARKSKIN               = 62
SPELL_ICE_STORM              = 63
SPELL_ENCHANT_ARMOR          = 64
SPELL_PORTAL                 = 65
SPELL_FORCESHIELD            = 66
SPELL_REFRESH                = 67
SPELL_ENDURANCE              = 68
SPELL_FIND_THE_PATH          = 69
SPELL_REGENERATION           = 70
SPELL_PROT_FROM_MAGIC        = 71
SPELL_EARTHMAW               = 72
SPELL_WATER_BREATHING        = 73
SPELL_FLAME_STRIKE           = 74
SPELL_CONJ_FIRE_ELEMENTAL    = 75
SPELL_CONJ_EARTH_ELEMENTAL   = 76
SPELL_CONJ_WATER_ELEMENTAL   = 77
SPELL_CONJ_AIR_ELEMENTAL     = 78
SPELL_ENERGY_BLAST           = 79
SPELL_ICE_BOLT               = 80
SPELL_RESTORATION            = 81
SPELL_IXSO_NIXSO             = 82
SPELL_REFLECT                = 83
SPELL_CHANNEL                = 84
SPELL_REGAIN_MANA            = 85
SPELL_ABSORB                 = 86
SPELL_MANA_STEAL             = 87
SPELL_GROUP_STRENGTH         = 88
SPELL_GROUP_WATER_BREATHING  = 89
SPELL_GROUP_SANCTUARY        = 90
SPELL_PEACE_SPHERE           = 91
SPELL_DIVINE_HAMMER          = 92
SPELL_POWER_LANCE            = 93
SPELL_TURN                   = 94
SPELL_CONFUSE                = 95

# Insert new spells here, up to MAX_SPELLS
MAX_SPELLS                   = 130

# PLAYER SKILLS - Numbered from MAX_SPELLS+1 to MAX_SKILLS
SKILL_BACKSTAB              = 131 # Reserved Skill[] DO NOT CHANGE
SKILL_BASH                  = 132 # Reserved Skill[] DO NOT CHANGE
SKILL_HIDE                  = 133 # Reserved Skill[] DO NOT CHANGE
SKILL_KICK                  = 134 # Reserved Skill[] DO NOT CHANGE
SKILL_PICK_LOCK             = 135 # Reserved Skill[] DO NOT CHANGE
SKILL_PUNCH                 = 136 # Reserved Skill[] DO NOT CHANGE
SKILL_RESCUE                = 137 # Reserved Skill[] DO NOT CHANGE
SKILL_SNEAK                 = 138 # Reserved Skill[] DO NOT CHANGE
SKILL_STEAL                 = 139 # Reserved Skill[] DO NOT CHANGE
SKILL_TRACK                 = 140 # Reserved Skill[] DO NOT CHANGE
SKILL_SCOUT                 = 141
SKILL_CIRCLE_AROUND         = 142
SKILL_SECOND_ATTACK         = 143
SKILL_THIRD_ATTACK          = 144
SKILL_FOURTH_ATTACK         = 145
SKILL_DUAL_WIELD            = 146
SKILL_PEEK                  = 147
SKILL_HUNT                  = 148
SKILL_DODGE                 = 149
SKILL_TUMBLE                = 150
SKILL_CRITICAL_HIT          = 151
SKILL_DANGER_SENSE          = 152
SKILL_HAND_TO_HAND          = 153
SKILL_BERSERK               = 154
SKILL_DISARM                = 155
SKILL_ELBOW                 = 156
SKILL_CHIVALRY              = 157
SKILL_DIRT_KICK             = 158
SKILL_DUAL_BACKSTAB         = 159
SKILL_MARTIAL_ARTS          = 160
SKILL_MEDITATE              = 161
SKILL_SECOND_SPELL_ATTACK   = 162
SKILL_THIRD_SPELL_ATTACK    = 163
SKILL_KNEE                  = 164
SKILL_GROIN_KICK            = 165
SKILL_LUNGE_PUNCH           = 166
SKILL_NERVE_PUNCH           = 167
SKILL_CAPTURE               = 168
SKILL_COUNTER               = 169
SKILL_MOUNTAINEERING        = 170
SKILL_DESERT_SURVIVAL       = 171
SKILL_ARCTIC_SURVIVAL       = 172
SKILL_STUN                  = 173
SKILL_FISH                  = 174

# New skills may be added here up to MAX_SKILLS (200)


##  NON-PLAYER AND OBJECT SPELLS AND SKILLS
##  The practice levels for the spells and skills below are _not_ recorded
##  in the playerfile; therefore, the intended use is for spells and skills
##  associated with objects (such as SPELL_IDENTIFY used with scrolls of
##  identify) or non-players (such as NPC-only spells).

SPELL_FIRE_BREATH            = 202
SPELL_GAS_BREATH             = 203
SPELL_FROST_BREATH           = 204
SPELL_ACID_BREATH            = 205
SPELL_LIGHTNING_BREATH       = 206

TOP_SPELL_DEFINE             = 299
# NEW NPC/OBJECT SPELLS can be inserted here up to 299

# weapon attack types
TYPE_HIT                     = 300
TYPE_STING                   = 301
TYPE_WHIP                    = 302
TYPE_SLASH                   = 303
TYPE_BITE                    = 304
TYPE_BLUDGEON                = 305
TYPE_CRUSH                   = 306
TYPE_POUND                   = 307
TYPE_CLAW                    = 308
TYPE_MAUL                    = 309
TYPE_THRASH                  = 310
TYPE_PIERCE                  = 311
TYPE_BLAST                   = 312
TYPE_PUNCH                   = 313
TYPE_STAB                    = 314
TYPE_PECK                    = 315

# new attack types can be added here - up to TYPE_SUFFERING
TYPE_CHOKING                 = 398
TYPE_SUFFERING               = 399


# saving throws
SAVING_PARA   = 0
SAVING_ROD    = 1
SAVING_PETRI  = 2
SAVING_BREATH = 3
SAVING_SPELL  = 4


# spell object types
SPELL_TYPE_SPELL   = 0
SPELL_TYPE_POTION  = 1
SPELL_TYPE_WAND    = 2
SPELL_TYPE_STAFF   = 3
SPELL_TYPE_SCROLL  = 4

# zone::reset_mode
ZONE_RESET_NEVER  = 0 # Actually, reset once on boot.
ZONE_RESET_ALWAYS = 1
ZONE_RESET_EMPTY  = 2

# zone-command::door-state::arg3
DOOR_STATE_OPEN   = 0
DOOR_STATE_CLOSED = 1
DOOR_STATE_LOCKED = 2

# Sex
SEX_NEUTRAL                    = 0                   
SEX_MALE                       = 1                   
SEX_FEMALE                     = 2                   

# Positions
POS_DEAD                       = 0                   # dead
POS_MORTALLYW                  = 1                   # mortally wounded
POS_INCAP                      = 2                   # incapacitated
POS_STUNNED                    = 3                   # stunned
POS_SLEEPING                   = 4                   # sleeping
POS_MEDITATING                 = 5                   # meditating
POS_RESTING                    = 6                   # resting
POS_SITTING                    = 7                   # sitting
POS_FIGHTING                   = 8                   # fighting
POS_STANDING                   = 9                   # standing
POS_FLYING                     = 10                  # flying (will work on this later)

# Player Flags
PLR_KILLER                     = (1 << 0)            # Player is a player-killer
PLR_THIEF                      = (1 << 1)            # Player is a player-thief
PLR_FROZEN                     = (1 << 2)            # Player is frozen
PLR_DONTSET                    = (1 << 3)            # Don't EVER set (ISNPC bit)
PLR_WRITING                    = (1 << 4)            # Player writing (board/mail/olc)
PLR_MAILING                    = (1 << 5)            # Player is writing mail
PLR_CRASH                      = (1 << 6)            # Player needs to be crash-saved
PLR_SITEOK                     = (1 << 7)            # Player has been site-cleared
PLR_NOSHOUT                    = (1 << 8)            # Player not allowed to shout/goss
PLR_NOTITLE                    = (1 << 9)            # Player not allowed to set title
PLR_DELETED                    = (1 << 10)           # Player deleted - space reusable
PLR_LOADROOM                   = (1 << 11)           # Player uses nonstandard loadroom
PLR_NOWIZLIST                  = (1 << 12)           # Player shouldn't be on wizlist
PLR_NODELETE                   = (1 << 13)           # Player shouldn't be deleted
PLR_INVSTART                   = (1 << 14)           # Player should enter game wizinvis
PLR_CRYO                       = (1 << 15)           # Player is cryo-saved (purge prog)
PLR_IT                         = (1 << 16)           # Player is it (tag)
PLR_QUESTOR                    = (1 << 17)           # Player is a questor
PLR_CREATING                   = (1 << 18)           # player is using olc
PLR_NOCLANINFO                 = (1 << 19)           # Player shouldn't be on claninfo
PLR_FULL_OLC                   = (1 << 20)           # Player has full olc access
PLR_INWAR                      = (1 << 21)           # Player is in the Arena
PLR_NOIDLE                     = (1 << 22)           # Player never force-extracted
PLR_MOBKILL                    = (1 << 23)           # Immo can kill mobs
PLR_PKOK                       = (1 << 24)           # Player partakes in PK!
PLR_NO_INFO_MSG                = (1 << 25)           # Info message shutoff
PLR_SCARRED                    = (1 << 26)           # Player has been scarred fighting
PLR_NOTDEADYET                 = (1 << 27)           # (R) Player being extracted.
PLR_AUTOENTER                  = (1 << 28)           # Player autoenters game after auth

# Mobile Flags
MOB_SPEC                       = (1 << 0)            # Mob has a callable spec-proc
MOB_SENTINEL                   = (1 << 1)            # Mob should not move
MOB_SCAVENGER                  = (1 << 2)            # Mob picks up stuff on the ground
MOB_ISNPC                      = (1 << 3)            # (R) Automatically set on all Mobs
MOB_AWARE                      = (1 << 4)            # Mob can't be backstabbed
MOB_AGGRESSIVE                 = (1 << 5)            # Mob auto-attacks everybody nearby
MOB_STAY_ZONE                  = (1 << 6)            # Mob shouldn't wander out of zone
MOB_WIMPY                      = (1 << 7)            # Mob flees if severely injured
MOB_AGGR_EVIL                  = (1 << 8)            # Auto-attack any evil PC's
MOB_AGGR_GOOD                  = (1 << 9)            # Auto-attack any good PC's
MOB_AGGR_NEUTRAL               = (1 << 10)           # Auto-attack any neutral PC's
MOB_MEMORY                     = (1 << 11)           # remember attackers if attacked
MOB_HELPER                     = (1 << 12)           # attack PCs fighting other NPCs
MOB_NOCHARM                    = (1 << 13)           # Mob can't be charmed
MOB_NOSUMMON                   = (1 << 14)           # Mob can't be summoned
MOB_NOSLEEP                    = (1 << 15)           # Mob can't be slept
MOB_NOBASH                     = (1 << 16)           # Mob can't be bashed (e.g. trees)
MOB_NOBLIND                    = (1 << 17)           # Mob can't be blinded
MOB_HUNTER                     = (1 << 18)           # Mob hunts people
MOB_NO_KILL                    = (1 << 19)           # Mob can't be attacked
MOB_NOFIRE                     = (1 << 20)           # Mob can't be damaged by fire
MOB_NOSUBDUE                   = (1 << 21)           # Mob won't give in to subduing
MOB_ON_MOB                     = (1 << 22)           # A little Mob on Mob violence
MOB_MOUNT                      = (1 << 23)           # Player can ride mob
MOB_GEN_SPEC                   = (1 << 24)           # mob uses the gen_spec routine
MOB_SILENT                     = (1 << 25)           # Mob is silent
MOB_IGNSUM                     = (1 << 26)           # Mob ignores summoned mobs
MOB_NOCORPSE                   = (1 << 27)           # Mob is animated
MOB_NOUPDATE                   = (1 << 28)           # point_update doesn't touch mob
MOB_DELETED                    = (1 << 29)           # Mob won't be written next save
MOB_NOTDEADYET                 = (1 << 30)           # (R) Mob being extracted.

# Display Flags
DISP_HIT                       = (1 << 0)            # Display current hp
DISP_MANA                      = (1 << 1)            # Display current mana
DISP_MOVE                      = (1 << 2)            # Display current move
DISP_MAXHIT                    = (1 << 3)            # Display max hit
DISP_MAXMANA                   = (1 << 4)            # Display max mana
DISP_MAXMOVE                   = (1 << 5)            # Display max move
DISP_ALIGN                     = (1 << 6)            # Display alignment meter
DISP_COND                      = (1 << 7)            # Display condition of fighting(ch)
DISP_VTBAR                     = (1 << 8)            # Display the vtbar
DISP_EXP                       = (1 << 9)            # Display exp in prompt
DISP_MOUNT                     = (1 << 10)           # Display mount
DISP_TIME                      = (1 << 11)           # Display time

# Preference Flags
PRF_BRIEF                      = (1 << 0)            # Room descs won't normally be shown
PRF_COMPACT                    = (1 << 1)            # No extra CRLF pair before prompts
PRF_DEAF                       = (1 << 2)            # Can't hear shouts
PRF_NOTELL                     = (1 << 3)            # Can't receive tells
PRF_CLANLOG                    = (1 << 4)            # Player listening to clan log?
PRF_INTINVIS                   = (1 << 5)            # Invisible to interwho
PRF_NOINTERTELL                = (1 << 6)            # Deaf to intertells
PRF_AUTOEXIT                   = (1 << 7)            # Display exits in a room
PRF_NOHASSLE                   = (1 << 8)            # Aggr mobs won't attack
PRF_QUEST                      = (1 << 9)            # On quest
PRF_SUMMONABLE                 = (1 << 10)           # Can be summoned
PRF_NOREPEAT                   = (1 << 11)           # No repetition of comm commands
PRF_HOLYLIGHT                  = (1 << 12)           # Can see in dark
PRF_COLOR                      = (1 << 13)           # Color on/off
PRF_SPEEDWALK                  = (1 << 14)           # Player using speedwalk?
PRF_NOWIZ                      = (1 << 15)           # Can't hear wizline
PRF_LOG1                       = (1 << 16)           # On-line System Log (low bit)
PRF_LOG2                       = (1 << 17)           # On-line System Log (high bit)
PRF_NOAUCT                     = (1 << 18)           # Can't hear auction channel
PRF_NOFLAME                    = (1 << 19)           # Can't hear flame channel
PRF_NOGRATZ                    = (1 << 20)           # Can't hear grats channel
PRF_ROOMFLAGS                  = (1 << 21)           # Can see room flags (ROOM_x)
PRF_NOCHAT                     = (1 << 22)           # Can't hear chat channel
PRF_NOMUSIC                    = (1 << 23)           # Can't hear music channel
PRF_AUTOLOOT                   = (1 << 24)           # Automatic loot
PRF_NOWEATHER                  = (1 << 25)           # Weather info on or off?
PRF_NOCLANTELL                 = (1 << 26)           # Can't hear clan channel
PRF_ALL_CLANS                  = (1 << 27)           # Can hear all clan channels
PRF_GAG                        = (1 << 28)           # Missed fighting messages don't show
PRF_NOARENA                    = (1 << 29)           # Player is deaf to the arena channel
PRF_LOG3                       = (1 << 30)           # On-line System log, debuggory
PRF_STAYPAGE                   = (1 << 31)           # Do not auto-quit last string page

# Preferences Flags 2
PRF2_NOCLANTITLE               = (1 << 0)            # Player's clantitle will not show
PRF2_CLANRECALL                = (1 << 1)            # Player recalls to hometown or clan?
PRF2_AFK                       = (1 << 2)            # Player is afk
PRF2_NOPROMPT                  = (1 << 3)            # Prompt will not be redrawn
PRF2_MYTITLE                   = (1 << 4)            # Title doesn't changed through lvls
PRF2_AUTOASSIST                = (1 << 5)            # Automatically assist fighting chs
PRF2_SUBDUE                    = (1 << 6)            # Character subdues in fights
PRF2_AUTOSAC                   = (1 << 7)            # Character automatically sacrifices
PRF2_NOANNOUNCE                = (1 << 8)            # Character doesn't receive info
PRF2_COOPERATE                 = (1 << 9)            # Character cooperates with others
PRF2_NOMOBLSTTELL              = (1 << 10)           # Character has mob tells in last
PRF2_AUTOGOLD                  = (1 << 11)           # Character automatically loots gold
PRF2_NOBLINK                   = (1 << 12)           # Character ignores blinking text?
PRF2_SMALL_MENUS               = (1 << 13)           # Player receives small or large?
PRF2_TIME_CMDS                 = (1 << 14)           # Player receives duration message
PRF2_WIZDIAGNOSE               = (1 << 15)           # Wizard sees verbose fight messgs
PRF2_SNUFF                     = (1 << 16)           # Hehe, used in conjunction with gag
PRF2_HINTS                     = (1 << 17)           # See random hints given by mud

# Affect Bits
AFF_BLIND                      = (1 << 0)            # (R) Char is blind
AFF_INVISIBLE                  = (1 << 1)            # Char is invisible
AFF_DETECT_ALIGN               = (1 << 2)            # Char is sensitive to align
AFF_DETECT_INVIS               = (1 << 3)            # Char can see invis chars
AFF_DETECT_MAGIC               = (1 << 4)            # Char is sensitive to magic
AFF_SENSE_LIFE                 = (1 << 5)            # Char can sense hidden life
AFF_WATERWALK                  = (1 << 6)            # Char can walk on water
AFF_SANCTUARY                  = (1 << 7)            # Char protected by sanct.
AFF_GROUP                      = (1 << 8)            # (R) Char is grouped
AFF_CURSE                      = (1 << 9)            # Char is cursed
AFF_INFRAVISION                = (1 << 10)           # Char can see in dark
AFF_POISON                     = (1 << 11)           # (R) Char is poisoned
AFF_PROTECT_EVIL               = (1 << 12)           # Char protected from evil
AFF_PROTECT_GOOD               = (1 << 13)           # Char protected from good
AFF_SLEEP                      = (1 << 14)           # (R) Char magically asleep
AFF_NOTRACK                    = (1 << 15)           # Char can't be tracked
AFF_FLY                        = (1 << 16)           # Character is flying
AFF_FIRESHIELD                 = (1 << 17)           # Char aff'd by fireshield
AFF_SNEAK                      = (1 << 18)           # Char can move quietly
AFF_HIDE                       = (1 << 19)           # Char is hidden
AFF_PHASE                      = (1 << 20)           # Char is affected by phase
AFF_CHARM                      = (1 << 21)           # Char is charmed
AFF_TRANSLUCENT                = (1 << 22)           # Char walks through doors
AFF_SECOND_ATTACK              = (1 << 23)           # mobile has second attack
AFF_THIRD_ATTACK               = (1 << 24)           # mobile has third attack
AFF_FOURTH_ATTACK              = (1 << 25)           # mobile has fourth attack
AFF_MEDITATING                 = (1 << 26)           # mobile is meditating
AFF_HIT_BY_LIGHTNING           = (1 << 27)           # between standard wait
AFF_REFLECT                    = (1 << 28)           # reflects most spells
AFF_ABSORB                     = (1 << 29)           # absorb as move/mn/hit
AFF_ENTANGLE                   = (1 << 30)           # mobile cannot flee

# NOTE: Don't confuse these constants with the ITEM_ bitvectors
#   which control the valid places you can wear a piece of equipment
WEAR_LIGHT              = 0
WEAR_FINGER_R           = 1
WEAR_FINGER_L           = 2
WEAR_NECK_1             = 3
WEAR_NECK_2             = 4
WEAR_BODY               = 5
WEAR_HEAD               = 6
WEAR_LEGS               = 7
WEAR_FEET               = 8
WEAR_HANDS              = 9
WEAR_ARMS               = 10
WEAR_SHIELD             = 11
WEAR_ABOUT              = 12
WEAR_WAIST              = 13
WEAR_WRIST_R            = 14
WEAR_WRIST_L            = 15
WEAR_WIELD_1            = 16
WEAR_HOLD               = 17
WEAR_EAR_R              = 18
WEAR_EAR_L              = 19
WEAR_FACE               = 20
WEAR_WIELD_2            = 21
WEAR_WIELD_BOTH         = 22
WEAR_RESTRAINT          = 23

NUM_WEARS               = 24       # This must be the # of eq positions!!

# room-related defines

# The cardinal directions: used as index to room_data.dir_option[]
NORTH                          = 0                   
EAST                           = 1                   
SOUTH                          = 2                   
WEST                           = 3                   
UP                             = 4                   
DOWN                           = 5                   


# Zone flags: used in zone_data.zone_flags
ZONE_OLC                       = (1 << 0)            # OLC zone
ZONE_GOD                       = (1 << 1)            # A God-only zone
ZONE_CLAN                      = (1 << 2)            # Clan zone
ZONE_REMORT                    = (1 << 3)            # RemortOnly zone

# Room flags: used in room_data.room_flags
# WARNING: In the world files, NEVER set the bits marked "R" ("Reserved")
ROOM_DARK                      = (1 << 0)            # Dark
ROOM_DEATH                     = (1 << 1)            # Death trap
ROOM_NOMOB                     = (1 << 2)            # MOBs not allowed
ROOM_INDOORS                   = (1 << 3)            # Indoors
ROOM_PEACEFUL                  = (1 << 4)            # Violence not allowed
ROOM_SOUNDPROOF                = (1 << 5)            # Shouts, gossip blocked
ROOM_NOTRACK                   = (1 << 6)            # Track won't go through
ROOM_NOMAGIC                   = (1 << 7)            # Magic not allowed
ROOM_TUNNEL                    = (1 << 8)            # room for only 1 pers
ROOM_PRIVATE                   = (1 << 9)            # Can't teleport in
ROOM_GODROOM                   = (1 << 10)           # LVL_GOD+ only allowed
ROOM_HOUSE                     = (1 << 11)           # (R) Room is a house
ROOM_HOUSE_CRASH               = (1 << 12)           # (R) House needs saving
ROOM_ATRIUM                    = (1 << 13)           # (R) The door to a house
ROOM_OLC                       = (1 << 14)           # (R) Modifyable/!compress
ROOM_BFS_MARK                  = (1 << 15)           # (R) breath-first srch mrk
ROOM_IMP_ROOM                  = (1 << 16)           # LVL_LSIMP+ only allowed
ROOM_ARENA                     = (1 << 17)           # Player killing allowed
ROOM_NO_TELEPORT               = (1 << 18)           # Can't teleport in
ROOM_NO_QUIT                   = (1 << 19)           # sent back to start room
ROOM_CLAN                      = (1 << 20)           # clan entrance
ROOM_REGEN                     = (1 << 21)           # Regen room
ROOM_NOMORT                    = (1 << 22)           # mortals can't enter
ROOM_NORECALL                  = (1 << 23)           # mortals can't recall from
ROOM_DELETED                   = (1 << 24)           # Room won't be saved


# Exit info: used in room_data.dir_option.exit_info
EX_ISDOOR                      = (1 << 0)            # Exit is a door
EX_CLOSED                      = (1 << 1)            # The door is closed
EX_LOCKED                      = (1 << 2)            # The door is locked
EX_PICKPROOF                   = (1 << 3)            # Lock can't be picked
EX_HIDDEN                      = (1 << 4)            # Secret door
EX_MAG_RESIST                  = (1 << 5)            # Magic resistant door


# Sector types: used in room_data.sector_type
SECT_INSIDE                    = 0                   # Indoors
SECT_CITY                      = 1                   # In a city
SECT_FIELD                     = 2                   # In a field
SECT_FOREST                    = 3                   # In a forest
SECT_HILLS                     = 4                   # In the hills
SECT_MOUNTAIN                  = 5                   # On a mountain
SECT_WATER_SWIM                = 6                   # Swimmable water
SECT_WATER_NOSWIM              = 7                   # Water - need a boat
SECT_UNDERWATER                = 8                   # Underwater
SECT_FLYING                    = 9                   # Mid Air
SECT_DESERT                    = 10                  # Desert
SECT_JUNGLE                    = 11                  # Jungle
SECT_SNOW                      = 12                  # Snow covered
SECT_SWAMP                     = 13                  # Swamp


# object-related defines

# Item types: used by obj_data.obj_flags.type_flag
ITEM_LIGHT                     = 1                   # Item is a light source
ITEM_SCROLL                    = 2                   # Item is a scroll
ITEM_WAND                      = 3                   # Item is a wand
ITEM_STAFF                     = 4                   # Item is a staff
ITEM_WEAPON                    = 5                   # Item is a weapon
ITEM_FIREWEAPON                = 6                   # Unimplemented
ITEM_MISSILE                   = 7                   # Unimplemented
ITEM_TREASURE                  = 8                   # Item is a treasure, not gold
ITEM_ARMOR                     = 9                   # Item is armor
ITEM_POTION                    = 10                  # Item is a potion
ITEM_WORN                      = 11                  # Unimplemented
ITEM_OTHER                     = 12                  # Misc object
ITEM_TRASH                     = 13                  # Trash - shopkeeps won't buy
ITEM_TRAP                      = 14                  # Unimplemented
ITEM_CONTAINER                 = 15                  # Item is a container
ITEM_NOTE                      = 16                  # Item is note
ITEM_DRINKCON                  = 17                  # Item is a drink container
ITEM_KEY                       = 18                  # Item is a key
ITEM_FOOD                      = 19                  # Item is food
ITEM_MONEY                     = 20                  # Item is money (gold)
ITEM_PEN                       = 21                  # Item is a pen
ITEM_BOAT                      = 22                  # Item is a boat
ITEM_FOUNTAIN                  = 23                  # Item is a fountain
ITEM_PORTAL                    = 24                  # Item is a portal
ITEM_PILL                      = 25                  # Item is a pill


# Take/Wear flags: used by obj_data.obj_flags.wear_flags
ITEM_WEAR_TAKE                 = (1 << 0)            # Item can be takes
ITEM_WEAR_FINGER               = (1 << 1)            # Can be worn on finger
ITEM_WEAR_NECK                 = (1 << 2)            # Can be worn around neck
ITEM_WEAR_BODY                 = (1 << 3)            # Can be worn on body
ITEM_WEAR_HEAD                 = (1 << 4)            # Can be worn on head
ITEM_WEAR_LEGS                 = (1 << 5)            # Can be worn on legs
ITEM_WEAR_FEET                 = (1 << 6)            # Can be worn on feet
ITEM_WEAR_HANDS                = (1 << 7)            # Can be worn on hands
ITEM_WEAR_ARMS                 = (1 << 8)            # Can be worn on arms
ITEM_WEAR_SHIELD               = (1 << 9)            # Can be used as a shield
ITEM_WEAR_ABOUT                = (1 << 10)           # Can be worn about body
ITEM_WEAR_WAIST                = (1 << 11)           # Can be worn around waist
ITEM_WEAR_WRIST                = (1 << 12)           # Can be worn on wrist
ITEM_WEAR_WIELD                = (1 << 13)           # Can be wielded
ITEM_WEAR_HOLD                 = (1 << 14)           # Can be held
ITEM_WEAR_EAR                  = (1 << 15)           # Can be worn in ear
ITEM_WEAR_FACE                 = (1 << 16)           # Can be worn on face
ITEM_WEAR_RESTRAINT            = (1 << 17)           # Restraint (captured chars)

# Anticlass object flags: used by obj_data.obj_flags.anti_flags
ANTI_WIZARD                    = (1 << 0)            # Wizards cannot use
ANTI_CLERIC                    = (1 << 1)            # Clerics cannot use
ANTI_ROGUE                     = (1 << 2)            # Rogues cannot use
ANTI_KNIGHT                    = (1 << 3)            # Knights cannot use
ANTI_RANGER                    = (1 << 4)            # Rangers cannot use
ANTI_PALADIN                   = (1 << 5)            # Paladins cannot use
ANTI_MONK                      = (1 << 6)            # Monks cannot use
ANTI_NINJA                     = (1 << 7)            # Ninjas cannot use


# Extra object flags: used by obj_data.obj_flags.extra_flags
ITEM_GLOW                      = (1 << 0)            # Item is glowing
ITEM_HUM                       = (1 << 1)            # Item is humming
ITEM_NORENT                    = (1 << 2)            # Item cannot be rented
ITEM_NODONATE                  = (1 << 3)            # Item cannot be donated
ITEM_NOINVIS                   = (1 << 4)            # Item cannot be made invis
ITEM_INVISIBLE                 = (1 << 5)            # Item is invisible
ITEM_MAGIC                     = (1 << 6)            # Item is magical
ITEM_NODROP                    = (1 << 7)            # Item is cursed: can't drop
ITEM_BLESS                     = (1 << 8)            # Item is blessed
ITEM_ANTI_GOOD                 = (1 << 9)            # Not usable by good people
ITEM_ANTI_EVIL                 = (1 << 10)           # Not usable by evil people
ITEM_ANTI_NEUTRAL              = (1 << 11)           # Not usable by neutral people
ITEM_TWO_HANDED                = (1 << 12)           # Weapon requires both hands
ITEM_MAG_CREATED               = (1 << 13)           # Created from magic
ITEM_FLAMING                   = (1 << 14)           # Weapon is flaming
ITEM_POISONED                  = (1 << 15)           # Weapon is poisoned
ITEM_NOSELL                    = (1 << 16)           # Shopkeepers won't touch it
ITEM_NO_MOB_TAKE               = (1 << 17)           # Scavenger mobs won't touch
ITEM_QUEST_EQ                  = (1 << 18)           # Item is quest equipment
ITEM_NODECAY                   = (1 << 19)           # Item Will Never Decay
ITEM_NO_LOCATE                 = (1 << 20)           # Can't be located by spells
ITEM_DONATED                   = (1 << 21)           # Object was donated
ITEM_NOAUCTION                 = (1 << 22)           # Object cannot be auctioned
ITEM_SHINE                     = (1 << 23)           # Object glows as light source
ITEM_UNAPPROVED                = (1 << 24)           # Objects from OLC zones that have not been approved yet
ITEM_HIDDEN                    = (1 << 25)           # Can't see it in room
ITEM_NO_DISARM                 = (1 << 26)           # Item cannot be disarms
ITEM_TRANSPARENT               = (1 << 27)           # Item can be seen through
ITEM_BIODEGRADABLE             = (1 << 28)           # Item won't biodegrade
ITEM_DELETED                   = (1 << 29)           # Item won't be written
ITEM_NOIDENTIFY                = (1 << 30)           # Item can't be identified
ITEM_DECAYING                  = (1 << 31)           # Item Is Decaying


# Defines for restraining objects
RESTRAIN_COMM                  = 1                   
RESTRAIN_POS                   = 2                   
RESTRAIN_MOVE                  = 3                   
RESTRAIN_FIGHT                 = 4                   
RESTRAIN_SKILL                 = 5                   

R_COMM_BIT                     = (1 << 0)            
R_POS_BIT                      = (1 << 1)            
R_MOVE_BIT                     = (1 << 2)            
R_FIGHT_BIT                    = (1 << 3)            
R_SKILL_BIT                    = (1 << 4)            


# Modifier constants used with obj affects ('A' fields)
APPLY_NONE                     = 0                   # No effect
APPLY_STR                      = 1                   # Apply to strength
APPLY_DEX                      = 2                   # Apply to dexterity
APPLY_INT                      = 3                   # Apply to intelligence
APPLY_WIS                      = 4                   # Apply to wisdom
APPLY_CON                      = 5                   # Apply to constitution
APPLY_CHA                      = 6                   # Apply to charisma
APPLY_CLASS                    = 7                   # Reserved
APPLY_LEVEL                    = 8                   # Reserved
APPLY_AGE                      = 9                   # Apply to age
APPLY_CHAR_WEIGHT              = 10                  # Apply to weight
APPLY_CHAR_HEIGHT              = 11                  # Apply to height
APPLY_MANA                     = 12                  # Apply to max mana
APPLY_HIT                      = 13                  # Apply to max hit points
APPLY_MOVE                     = 14                  # Apply to max move points
APPLY_GOLD                     = 15                  # Reserved
APPLY_EXP                      = 16                  # Reserved
APPLY_AC                       = 17                  # Apply to Armor Class
APPLY_HITROLL                  = 18                  # Apply to hitroll
APPLY_DAMROLL                  = 19                  # Apply to damage roll
APPLY_SAVING_PARA              = 20                  # Apply to save throw: paralz
APPLY_SAVING_ROD               = 21                  # Apply to save throw: rods
APPLY_SAVING_PETRI             = 22                  # Apply to save throw: petrif
APPLY_SAVING_BREATH            = 23                  # Apply to save throw: breath
APPLY_SAVING_SPELL             = 24                  # Apply to save throw: spells

# Modifier constants used for rooms
ROOM_APPLY_NONE                = 0                   # No efefct

# Container flags - value[1]
CONT_CLOSEABLE                 = (1 << 0)            # Container can be closed
CONT_PICKPROOF                 = (1 << 1)            # Container is pickproof
CONT_CLOSED                    = (1 << 2)            # Container is closed
CONT_LOCKED                    = (1 << 3)            # Container is locked

# Special container value[3]
CONT_NORMAL                    = 0                   # Not a special container
CONT_CORPSE                    = 1                   # Container is a corpse
CONT_PILE                      = 2                   # Container is a pile
CONT_VOMIT                     = 3                   # Container is vomit

# Some different kind of liquids for use in values of drink containers
LIQ_WATER                      = 0                   
LIQ_BEER                       = 1                   
LIQ_WINE                       = 2                   
LIQ_ALE                        = 3                   
LIQ_DARKALE                    = 4                   
LIQ_WHISKY                     = 5                   
LIQ_LEMONADE                   = 6                   
LIQ_FIREBRT                    = 7                   
LIQ_LOCALSPC                   = 8                   
LIQ_SLIME                      = 9                   
LIQ_MILK                       = 10                  
LIQ_TEA                        = 11                  
LIQ_COFFE                      = 12                  
LIQ_BLOOD                      = 13                  
LIQ_SALTWATER                  = 14                  
LIQ_CLEARWATER                 = 15                  
LIQ_CHAMPAGNE                  = 16                  


# other miscellaneous defines


# Player conditions
DRUNK                          = 0                   
FULL                           = 1                   
THIRST                         = 2                   


# Sun state for weather_data
SUN_DARK                       = 0                   
SUN_RISE                       = 1                   
SUN_LIGHT                      = 2                   
SUN_SET                        = 3                   


# Sky conditions for weather_data
SKY_CLOUDLESS                  = 0                   
SKY_CLOUDY                     = 1                   
SKY_RAINING                    = 2                   
SKY_LIGHTNING                  = 3                   


# Rent codes
RENT_UNDEF                     = 0                   
RENT_CRASH                     = 1                   
RENT_RENTED                    = 2                   
RENT_CRYO                      = 3                   
RENT_FORCED                    = 4                   
RENT_TIMEDOUT                  = 5                   

# Special vnums
MOB_ANIMATED_CORPSE            = 7                   


# Maps, Tables & Vectors.

# imm_levels
_level_names = {LVL_IMPL        : 'Implementor',
                LVL_ARCH_GOD    : 'Arch God'   ,
                LVL_ETERNAL_GOD : 'Eternal God',
                LVL_GOD         : 'God'        ,
                LVL_OVERSEER    : 'Overseer'   ,
                LVL_CREATOR     : 'Creator'    ,
                LVL_DEMIGOD     : 'Demi-God'   ,
                LVL_DEITY       : 'Deity'      ,
                LVL_IMMORT      : 'Immortal'   ,
                LVL_AVATAR      : 'Avatar'}

# attack_hit_type = {singular, plural}
_attack_hit_text = [('hit'      , 'hits'     ),
                    ('sting'    , 'stings'   ),
                    ('whip'     , 'whips'    ),
                    ('slash'    , 'slashes'  ),
                    ('bite'     , 'bites'    ),
                    ('bludgeon' , 'bludgeons'),
                    ('crush'    , 'crushes'  ),
                    ('pound'    , 'pounds'   ),
                    ('claw'     , 'claws'    ),
                    ('maul'     , 'mauls'    ),
                    ('thrash'   , 'thrashes' ),
                    ('pierce'   , 'pierces'  ),
                    ('blast'    , 'blasts'   ),
                    ('punch'    , 'punches'  ),
                    ('stab'     , 'stabs'    ),
                    ('peck'     , 'pecks'    )]

_dam_weapons = [dict(to_room   = '',
                     to_char   = '',
                     to_victim = '')]

##    {
##      "$n tries to #w $N, but misses.",
##      "You try to #w $N, but miss.",
##      "$n tries to #w you, but misses."
##    },
##
##    {
##      "$n barely #W $N.",
##      "You barely #w $N.",
##      "$n barely #W you."
##    },
##
##    {
##      "$n scratches $N with $s #w.",
##      "You scratch $N as you #w $M.",
##      "$n scratches you as $e #W you."
##    },
##
##    {
##      "$n #W $N.",
##      "You #w $N.",
##      "$n #W you."
##    },
##
##    {
##      "$n #W $N hard.",
##      "You #w $N hard.",
##      "$n #W you hard."
##    },
##
##    {
##      "$n #W $N very hard.",
##      "You #w $N very hard.",
##      "$n #W you very hard."
##    },
##
##    {
##      "$n #W $N extremely hard.",
##      "You #w $N extremely hard.",
##      "$n #W you extremely hard."
##    },
##
##    {
##      "$n massacres $N to small fragments with $s #w.",
##      "You massacre $N to small fragments with your #w.",
##      "$n massacres you to small fragments with $s #w."
##    },
##
##    {
##      "$n maims $N with $s #w!",
##      "You maim $N with your #w!",
##      "$n maims you with $s #w!"
##    },
##
##    {
##      "$n MUTILATES $N with $s harsh #w!",
##      "You MUTILATE $N with your harsh #w!",
##      "$n MUTILATES you with $s harsh #w!"
##    },
##
##    {
##      "$n OBLITERATES $N with $s deadly #w!",
##      "You OBLITERATE $N with your deadly #w!",
##      "$n OBLITERATES you with $s deadly #w!"
##    },
##
##    {
##      "$n ANNIHILATES $N with $s wicked #w!",
##      "You ANNIHILATE $N with your wicked #w!",
##      "$n ANNIHILATES you with $s wicked #w!"
##    },
##
##    {
##      "$n VAPORIZES $N with $s DEVASTATING #w!!",
##      "You VAPORIZE $N with your DEVASTATING #w!!",
##      "$n VAPORIZES you with $s DEVASTATING #w!!"
##    }

_move_list = [('walk'   ,'walks'   ),
              ('ooze'   ,'oozes'   ),
              ('stomp'  ,'stomps'  ),
              ('hop'    ,'hops'    ),
              ('slide'  ,'slides'  ),
              ('stroll' ,'strolls' ),
              ('wander' ,'wanders' ),
              ('crawl'  ,'crawls'  ),
              ('slither','slithers'),
              ('float'  ,'floats'  ),
              ('bounce' ,'bounces' ),
              ('run'    ,'run'     ),
              ('roll'   ,'rolls'   ),
              ('slink'  ,'slinks'  ),
              ('scurry' ,'scurries'),
              ('waddle' ,'waddles' ),
              ('glide'  ,'glides'  ),
              ('fly'    ,'flies'   ),
              ('swim'   ,'swims'   ),
              ('gallop' ,'gallops' )]

_movement_loss = {0  : 1,               # Inside
                  1  : 1,               # City
                  2  : 2,               # Field
                  3  : 3,               # Forest
                  4  : 4,               # Hills
                  5  : 6,               # Mountains
                  6  : 4,               # Swimming
                  6  : 1,               # Unswimable
                  7  : 2,               # Underwater
                  8  : 0,               # Flying
                  9  : 4,               # Desert
                  10 : 5,               # Jungle
                  11 : 5,               # Snow
                  12 : 5}               # Swamp

zoneFlagNamesDict = {
    1:"Olc",
    2:"Immortal",
    4:"Clan",
    8:"RemortOnly"
}

    # XXX These are in the wrong order, actually, but they're more familiar.
    ##    resetModes = {
    ##        0:"Never Reset",
    ##        1:"Reset When Empty",
    ##        2:"Always Reset"
    ##    }

_reset_mode_names = {ZONE_RESET_NEVER  : 'Once on boot',
                     ZONE_RESET_ALWAYS : 'Always'      ,
                     ZONE_RESET_EMPTY  : 'When Empty'}

_continents = {0: 'Marklar',
               1: 'Landrea'}

_directions = 'neswud'

_exit_bits = {0: "Door"     ,
              1: "Closed"   ,
              2: "Locked"   ,
              3: "PickProof",
              4: "Hidden"   ,
              5: "NoMagic"  }

_room_sectors = {
        0:"Inside",
        1:"City",
        2:"Field",
        3:"Forest",
        4:"Hills",
        5:"Mountains",
        6:"Water (Swim)",
        7:"Water (No Swim)",
        8:"Underwater",
        9:"Mid Air",
        10:"Desert",
        11:"Jungle",
        12:"Snow",
        13:"Swamp"
        }

roomFlagNamesDict = {
    1:"Dark",
    2:"DeathTrap",
    4:"NoMob",
    8:"Indoors",
    16:"Peaceful",
    32:"Soundproof",
    64:"NoTrack",
    128:"NoMagic",
    512:"Tunnel",
    1024:"Private",
    2048:"GodRoom",
    4096:"House",
    8192:"HouseCrashSave",
    16384:"Atrium",
    32768:"Olc",
    65536:"*", # BFS MARK
    131072:"ImplementorRoom",
    262144:"Arena",
    524288:"NoTeleport",
    1048576:"NoQuit",
    2097152:"ClanHouseEntrance",
    4195304:"Regeneration",
    8388608:"NoMortalPC",
    16777216:"Deleted"
    }

_door_states = {DOOR_STATE_OPEN   : 'Open'  ,
                DOOR_STATE_CLOSED : 'Closed',
                DOOR_STATE_LOCKED : 'Locked'}

_wear_positions = {WEAR_LIGHT       : 'Held as light'   ,
                   WEAR_FINGER_R    : 'On Right Finger' ,
                   WEAR_FINGER_L    : 'On Left Finger'  ,
                   WEAR_NECK_1      : 'Around Neck'     ,
                   WEAR_NECK_2      : 'Around Breast'   ,
                   WEAR_BODY        : 'On Body'         ,
                   WEAR_HEAD        : 'On Head'         ,
                   WEAR_LEGS        : 'On Legs'         ,
                   WEAR_FEET        : 'On Feet'         ,
                   WEAR_HANDS       : 'On Hands'        ,
                   WEAR_ARMS        : 'On Arms'         ,
                   WEAR_SHIELD      : 'Used as Shield'  ,
                   WEAR_ABOUT       : 'About Body'      ,
                   WEAR_WAIST       : 'About Waist'     ,
                   WEAR_WRIST_R     : 'On Right Wrist'  ,
                   WEAR_WRIST_L     : 'On Left Wrist'   ,
                   WEAR_WIELD_1     : 'Primary Wield'   ,
                   WEAR_HOLD        : 'Held'            ,
                   WEAR_EAR_R       : 'Right Ear'       ,
                   WEAR_EAR_L       : 'Left Ear'        ,
                   WEAR_FACE        : 'On Face'         ,
                   WEAR_WIELD_2     : 'Secondary Wield' ,
                   WEAR_WIELD_BOTH  : 'Two-Handed Wield',
                   WEAR_RESTRAINT   : 'Restraint'       }

_wear_bits = {0 : 'Take'  ,
              1 : 'Finger',
              2 : 'Neck'  ,
              3 : 'Body'  ,
              4 : 'Head'  ,
              5 : 'Legs'  ,
              6 : 'Feet'  ,
              7 : 'Hands' ,
              8 : 'Arms'  ,
              9 : 'Shield',
              10: 'About' ,
              11: 'Waist' ,
              12: 'Wrist' ,
              13: 'Wield' ,
              14: 'Hold'  ,
              15: 'Ear'   ,
              16: 'Face'  ,
              17: 'Restraint'}

_positions = {0 : "Dead"             ,
              1 : "Mortally wounded" ,
              2 : "Incapacitated"    ,
              3 : "Stunned"          ,
              4 : "Sleeping"         ,
              5 : "Meditating"       ,
              6 : "Resting"          ,
              7 : "Sitting"          ,
              8 : "Fighting"         ,
              9 : "Standing"         }

_display_bits = {0 : "HitPoints"    ,
                 1 : "Mana"         ,
                 2 : "Movement"     ,
                 3 : "MaxHitPoints" ,
                 4 : "MaxMana"      ,
                 5 : "MaxMovement"  ,
                 6 : "Alignment"    ,
                 7 : "AutoDiagnose" ,
                 8 : "VTBar"        ,
                 9 : "Experience"   ,
                 10: "Mount"        ,
                 11: "Time"         }

_player_bits = {0 : 'Killer'    ,
                1 : 'Thief'     ,
                2 : 'Frozen'    ,
                3 : 'DONTSET'   ,
                4 : 'Writing'   ,
                5 : 'Mailing'   ,
                6 : 'CrashSave' ,
                7 : 'SiteOk'    ,
                8 : 'Muted'     ,
                9 : 'NoTitle'   ,
                10: 'Deleted'   ,
                11: 'Loadroom'  ,
                12: 'NoWizlist' ,
                13: 'NoDelete'  ,
                14: 'InvisStart',
                15: "Cryo'd"    ,
                16: 'It'        ,
                17: 'Questor'   ,
                18: 'Creating'  ,
                19: 'NoClanInfo',
                20: 'FullOlcPerm',
                21: 'InWar'     ,
                22: 'NoIdle'    ,
                23: 'MobKill'   ,
                24: 'PKOK'      ,
                25: 'NoInfo'    ,
                26: 'Scarred'   ,
                27: 'MortalWounds',
                28: 'AutoEnter' }

_npc_bits = {0 : 'SpecProc'       ,
             1 : 'Sentinel'       ,
             2 : 'Scavenger'      ,
             3 : 'IsNPC'          ,
             4 : 'NoBackstab'     ,
             5 : 'Aggressive'     ,
             6 : 'StayInZone'     ,
             7 : 'Wimpy'          ,
             8 : 'AggressiveEvil' ,
             9 : 'AggressiveGood' ,
             10: 'AggressiveNeutral',
             11: 'Memory'         ,
             12: 'Helper'         ,
             13: 'NoCharm'        ,
             14: 'NoSummon'       ,
             15: 'NoSleep'        ,
             16: 'NoBash'         ,
             17: 'NoBlind'        ,
             18: 'Hunter'         ,
             19: 'Invulnerable'   ,
             20: 'NoFire'         ,
             21: 'NoSubdue'       ,
             22: 'MobViolence'    ,
             23: 'Mount'          ,
             24: 'GenSpec'        ,
             25: 'Silent'         ,
             26: 'IgnoreSummons'  ,
             27: 'NoCorpse'       ,
             28: 'NoUpdate'       ,
             29: 'Deleted'        }

_preference_bits = {0 : 'Brief'     ,
                    1 : 'Compact'   ,
                    2 : 'NoShout'   ,
                    3 : 'NoTell'    ,
                    4 : 'ClanLog'   ,
                    5 : 'Invisible' ,
                    6 : '!UNUSED!'  ,
                    7 : 'AutoExits' ,
                    8 : 'NoHassle'  ,
                    9 : 'Quest'     ,
                    10: 'Summon'    ,
                    11: 'NoRepeat'  ,
                    12: 'HolyLight' ,
                    13: 'AnsiColor' ,
                    14: 'Speedwalk' ,
                    15: 'NoWiznet'  ,
                    16: 'SyslogBit1',
                    17: 'SyslogBit2',
                    18: 'NoAuction' ,
                    19: 'NoFlame'   ,
                    20: 'NoGratz'   ,
                    21: 'RoomFlags' ,
                    22: 'NoChat'    ,
                    23: 'NoMusic'   ,
                    24: 'AutoLoot'  ,
                    25: 'NoWeather' ,
                    26: 'NoClanTell',
                    27: 'AllClanTells',
                    28: 'MessageGag',
                    29: 'NoArena'   ,
                    30: 'SyslogBit3',
                    31: 'StayPage'  }

_preference_bits2 = {0 : 'NoClanTitle'      ,
                     1 : 'ClanRecall'       ,
                     2 : 'AFK'              ,
                     3 : 'NoPrompt'         ,
                     4 : 'KeepMyTitle'      ,
                     5 : 'AutoAssist'       ,
                     6 : 'Subdues'          ,
                     7 : 'AutoSacrifice'    ,
                     8 : 'IgnoreAnnouncements',
                     9 : 'Cooperates'       ,
                     10: 'NoMobLastTell'    ,
                     11: 'AutoGold'         ,
                     12: 'NoBlink'          ,
                     13: 'SmallMenus'       ,
                     14: 'CommandTiming'    ,
                     15: 'MessageSnuff'     ,
                     16: 'GameHints'        }

_affected_bits = {0 : 'Blind'           ,
                  1 : 'Invisible'       ,
                  2 : 'DetectAlign'     ,
                  3 : 'DetectInvis'     ,
                  4 : 'DetectMagic'     ,
                  5 : 'SenseLife'       ,
                  6 : 'Waterwalk'       ,
                  7 : 'Sanctuary'       ,
                  8 : 'Grouped'         ,
                  9 : 'Cursed'          ,
                  10: 'Infravision'     ,
                  11: 'Poisoned'        ,
                  12: 'ProtectionFromEvil',
                  13: 'ProtectionFromGood',
                  14: 'Sleep'           ,
                  15: 'NoTrack'         ,
                  16: 'Flying'          ,
                  17: 'Fireshield'      ,
                  18: 'Sneaking'        ,
                  19: 'Hiding'          ,
                  20: 'PhaseBlur'       ,
                  21: 'Charmed'         ,
                  22: 'Etherealized'    ,
                  23: 'SecondAttack'    ,
                  24: 'ThirdAttack'     ,
                  25: 'FourthAttack'    ,
                  26: 'Meditating'      ,
                  27: 'HitByLightning'  ,
                  28: 'Reflect'         ,
                  29: 'Absorb'          ,
                  30: 'Entangled'       }

_class_names = {0: "wizard"  ,
                1: "cleric"  ,
                2: "assassin",
                3: "knight"  ,
                4: "ranger"  ,
                5: "paladin" ,
                6: "monk"    ,
                7: "ninja"   ,
                8: "druid"   }

_genders = {0: "Neutral",
            1: "Male"   ,
            2: "Female" }

_item_types = {0 : 'Undefined'    ,
               1 : 'Light'        ,
               2 : 'Scroll'       ,
               3 : 'Wand'         ,
               4 : 'Staff'        ,
               5 : 'Weapon'       ,
               6 : 'RangeWeapon'  ,
               7 : 'Missile'      ,
               8 : 'Treasure'     ,
               9 : 'Armor'        ,
               10: 'Potion'       ,
               11: 'Worn'         ,
               12: 'Other'        ,
               13: 'Trash'        ,
               14: 'Trap'         ,
               15: 'Container'    ,
               16: 'Note'         ,
               17: 'LiquidContainer',
               18: 'Key'          ,
               19: 'Food'         ,
               20: 'Money'        ,
               21: 'Pen'          ,
               22: 'Boat'         ,
               23: 'Fountain'     ,
               24: 'Portal'       ,
               25: 'Pill'         }

# Extra what? (item)
_extra_bits = {0 : 'Glowing'       ,
               1 : 'Humming'       ,
               2 : 'NoRent'        ,
               3 : 'NoDonate'      ,
               4 : 'NoInvis'       ,
               5 : 'Invisible'     ,
               6 : 'Magic'         ,
               7 : 'Cursed'        ,
               8 : 'Blessed'       ,
               9 : 'AntiGood'      ,
               10: 'AntiEvil'      ,
               11: 'AntiNeutral'   ,
               12: 'TwoHanded'     ,
               13: 'MagicallyCreated',
               14: 'Flaming'       ,
               15: 'Poison'        ,
               16: 'NoSell'        ,
               17: 'NoMobTake'     ,
               18: 'Quest'         ,
               19: 'NoDecay'       ,
               20: 'NoLocate'      ,
               21: 'Donated'       ,
               22: 'NoAuction'     ,
               23: 'Shining'       ,
               24: 'Unapproved'    ,
               25: 'Hidden'        ,
               26: 'NoDisarm'      ,
               27: 'Transparent'   ,
               28: 'Biodegradable' ,
               29: 'Deleted'       ,
               30: 'NoIdentify'    ,
               31: 'ItemDecaying'  }
               # There aren't 33 bits in a bitvector.
               # 32: 'ItemNoDecay'   }

_anticlass_bits = {0: 'wizard'  ,
                   1: 'cleric'  ,
                   2: 'assassin',
                   3: 'knight'  ,
                   4: 'ranger'  ,
                   5: 'paladin' ,
                   6: 'monk'    ,
                   7: 'ninja'   ,
                   8: 'druid'}

_apply_types = {0 : 'None'                   ,
                1 : 'Strength'               ,
                2 : 'Dexterity'              ,
                3 : 'Intelligence'           ,
                4 : 'Wisdom'                 ,
                5 : 'Constitution'           ,
                6 : 'Charisma'               ,
                7 : 'Class'                  ,
                8 : 'Level'                  ,
                9 : 'Age'                    ,
                10: 'Weight'                 ,
                11: 'Height'                 ,
                12: 'MaxMana'                ,
                13: 'MaxHit'                 ,
                14: 'MaxMove'                ,
                15: 'Gold'                   ,
                16: 'Experience'             ,
                17: 'Armour'                 ,
                18: 'Hitroll'                ,
                19: 'Damroll'                ,
                20: 'Saving vs. Paralysis'   ,
                21: 'Saving vs. Rod/Staff/Wand',
                22: 'Saving vs. Petrification',
                23: 'Saving vs. Breath Weapon',
                24: 'Saving vs. Spells'      }

_container_bits = {0: 'Closeable',
                   1: 'Pickproof',
                   2: 'Closed' ,
                   3: 'Locked' }

_container_types = {0: 'Normal',
                    1: 'Corpse',
                    2: 'Pile',
                    3: 'Vomit'}

_drinks = {0 : 'water'         ,
           1 : 'beer'          ,
           2 : 'wine'          ,
           3 : 'ale'           ,
           4 : 'dark ale'      ,
           5 : 'whisky'        ,
           6 : 'lemonade'      ,
           7 : 'firebreather'  ,
           8 : 'local speciality',
           9 : 'slime mold juice',
           10: 'milk'          ,
           11: 'tea'           ,
           12: 'coffee'        ,
           13: 'blood'         ,
           14: 'salt water'    ,
           15: 'clear water'   ,
           16: 'champagne'     ,
           17: 'eggnog'        ,
           18: 'fireoil'       ,
           19: 'embalming fluid'}

_drinknames = {0 : 'water'     ,
               1 : 'beer'      ,
               2 : 'wine'      ,
               3 : 'ale'       ,
               4 : 'ale'       ,
               5 : 'whisky'    ,
               6 : 'lemonade'  ,
               7 : 'firebreather',
               8 : 'local'     ,
               9 : 'juice'     ,
               10: 'milk'      ,
               11: 'tea'       ,
               12: 'coffee'    ,
               13: 'blood'     ,
               14: 'salt'      ,
               15: 'water'     ,
               16: 'champagne' ,
               17: 'nog'       ,
               18: 'oil'       ,
               19: 'fluid'     }

_color_liquid = {0 : 'clear'              ,
                 1 : 'brown'              ,
                 2 : 'clear'              ,
                 3 : 'brown'              ,
                 4 : 'dark'               ,
                 5 : 'golden'             ,
                 6 : 'red'                ,
                 7 : 'green'              ,
                 8 : 'clear'              ,
                 9 : 'light green'        ,
                 10: 'white'              ,
                 11: 'brown'              ,
                 12: 'black'              ,
                 13: 'red'                ,
                 14: 'clear'              ,
                 15: 'crystal clear'      ,
                 16: 'thick yellowish white'}

_spell_wear_off_msg = {0 : 'RESERVED DB.C'                                              ,
                       1 : 'You feel less protected.'                                   ,
                       2 : '!Teleport!'                                                 ,
                       3 : 'You feel less righteous.'                                   ,
                       4 : 'You feel a cloak of blindness disolve.'                     ,
                       5 : '!Burning Hands!'                                            ,
                       6 : '!Call Lightning'                                            ,
                       7 : 'You feel more self-confident.'                              ,
                       8 : 'You feel your strength return.'                             ,
                       9 : 'The magical vines constricting you suddenly disappear.'     ,
                       10: '!Color Spray!'                                              ,
                       11: '!Control Weather!'                                          ,
                       12: '!Create Food!'                                              ,
                       13: '!Create Water!'                                             ,
                       14: '!Cure Blind!'                                               ,
                       15: '!Cure Critic!'                                              ,
                       16: '!Cure Light!'                                               ,
                       17: 'You feel more optimistic.'                                  ,
                       18: 'You feel less aware.'                                       ,
                       19: 'Your eyes stop tingling.'                                   ,
                       20: 'The detect magic wears off.'                                ,
                       21: 'The detect poison wears off.'                               ,
                       22: '!Dispel Evil!'                                              ,
                       23: '!Earthquake!'                                               ,
                       24: '!Enchant Weapon!'                                           ,
                       25: '!Energy Drain!'                                             ,
                       26: '!Fireball!'                                                 ,
                       27: '!Harm!'                                                     ,
                       28: '!Heal!'                                                     ,
                       29: 'You feel yourself exposed.'                                 ,
                       30: '!Lightning Bolt!'                                           ,
                       31: '!Locate object!'                                            ,
                       32: '!Magic Missile!'                                            ,
                       33: 'You feel less sick.'                                        ,
                       34: 'You feel less protected.'                                   ,
                       35: '!Remove Curse!'                                             ,
                       36: 'The white aura around your body fades.'                     ,
                       37: '!Shocking Grasp!'                                           ,
                       38: 'You feel less tired.'                                       ,
                       39: 'You feel weaker.'                                           ,
                       40: '!Summon!'                                                   ,
                       41: '!Ventriloquate!'                                            ,
                       42: '!Word of Recall!'                                           ,
                       43: '!Remove Poison!'                                            ,
                       44: 'You feel less aware of your suroundings.'                   ,
                       45: '!Animate Corpse!'                                           ,
                       46: '!Dispel Good!'                                              ,
                       47: '!Group Armor!'                                              ,
                       48: '!Group Heal!'                                               ,
                       49: '!Group Recall!'                                             ,
                       50: 'Your night vision seems to fade.'                           ,
                       51: 'Your feet seem less boyant.'                                ,
                       52: '!Identify!'                                                 ,
                       53: 'You float back down to the ground.'                         ,
                       54: 'The shield of flame around your body disappears.'           ,
                       55: 'Your whupass seems to have worn off.'                       ,
                       56: 'Your image stops shifting and returns to normal.'           ,
                       57: 'You feel solid again.'                                      ,
                       58: '!Create Spring!'                                            ,
                       59: '!Continual Light!'                                          ,
                       60: '!Teleport Object!'                                          ,
                       61: 'Your skin softens and returns to normal.'                   ,
                       62: 'Your barkskin returns to normal.'                           ,
                       63: '!Ice Storm!'                                                ,
                       64: '!Enchant Armor!'                                            ,
                       65: '!Portal!'                                                   ,
                       66: 'The force shield around you shimmers and fades away.'       ,
                       67: '!Refresh!'                                                  ,
                       68: 'Your feel your less energetic.'                             ,
                       69: '!Find the Path!'                                            ,
                       70: 'You feel your metabolism begin to slow down.'               ,
                       71: 'You feel less protected from magic.'                        ,
                       72: '!Earthmaw!'                                                 ,
                       73: 'Your magical gills glow briefly and disappear.'             ,
                       74: '!Flame Strike!'                                             ,
                       75: '!Conjure Fire Elemental!'                                   ,
                       76: '!Conjure Earth Elemental!'                                  ,
                       77: '!Conjure Water Elemental!'                                  ,
                       78: '!Conjure Air Elemental!'                                    ,
                       79: '!Energy Blast!'                                             ,
                       80: '!Ice Bolt!'                                                 ,
                       81: '!Restoration!'                                              ,
                       82: 'The green aura around you fades.'                           ,
                       83: '!Channel!'                                                  ,
                       84: '!Regain Mana!'                                              ,
                       85: 'The green aura around you fades.'                           ,
                       86: '!Mana Steal!'                                               ,
                       87: 'The calm peacefulness around you slowly recedes.'           ,
                       88: '!Divine Hammer!'                                            ,
                       89: '!Power Lance!'                                              ,
                       90: '!Turn!'                                                     ,
                       91: 'Your befuddlement suddenly disappears.  You blush sheepishly.',
                       92: '!UNUSED!'                                                   }

_weekdays = {0: 'the Day of the Moon'    ,
             1: 'the Day of the Bull'    ,
             2: 'the Day of the Deception',
             3: 'the Day of Thunder'     ,
             4: 'the Day of Freedom'     ,
             5: 'the Day of the Great Gods',
             6: 'the Day of the Sun'     }

_month_name = {0 : 'Month of Winter'            ,
               1 : 'Month of the Winter Wolf'   ,
               2 : 'Month of the Frost Giant'   ,
               3 : 'Month of the Old Forces'    ,
               4 : 'Month of the Grand Struggle',
               5 : 'Month of the Spring'        ,
               6 : 'Month of Nature'            ,
               7 : 'Month of Futility'          ,
               8 : 'Month of the Dragon'        ,
               9 : 'Month of the Sun'           ,
               10: 'Month of the Heat'          ,
               11: 'Month of the Battle'        ,
               12: 'Month of the Dark Shades'   ,
               13: 'Month of the Shadows'       ,
               14: 'Month of the Long Shadows'  ,
               15: 'Month of the Ancient Darkness',
               16: 'Month of the Great Evil'    }

_sun_types = {0: '&BNight&N',
              1: '&YSunrise&N',
              2: '&yDaytime&N',
              3: '&YSunset&N'}

_sky_types = {0: '&wClear Skies&N',
              1: 'Cloudy'       ,
              2: '&bRaining&N'  ,
              3: '&yLightning&N'}

UNUSED    = '!UNUSED!'
UNDEFINED = '!UNDEFINED!'
RESERVED  = '!RESERVED!'

_tunnel_size = 2


# Conversion Utilities.
##    import re
##    PATTERN = re.compile(r'#define\s+(\w+)(?:\s+)(.*)')
##
##    def convert_defines(config):
##        config.replace('\t', '    ')
##        for line in config.split('\n'):
##            line = line.rstrip()
##            match = PATTERN.match(line)
##            if match is None:
##                print line
##            else:
##                (name, value) = match.groups()
##                pt = value.find('/*')
##                if pt >= 0:
##                    comment = value[pt+2:]
##                    value = value[:pt].rstrip()
##
##                    pt = comment.rfind('*/')
##                    if pt >= 0:
##                        comment = comment[:pt]
##
##                    comment = '# ' + comment.strip()
##                else:
##                    comment = ''
##
##                print '%-30s = %-20s%s' % (name, value, comment)
##
##    def convert_arrays(these):
##        from sys import stdout
##        for (name, array) in []:
##            longest = max(len(i) for i in array)
##            ln = len(array)
##
##            fmt = '%%-%dd: %%-%dr' % (len(str(ln)), longest)
##            header = '%s = {' % name
##            tab = ',\n' + len(header) * ' '
##
##            stdout.write(header)
##            for x in xrange(ln):
##                if x:
##                    stdout.write(tab)
##
##                stdout.write(fmt % (x, array[x]))
##
##            stdout.write('}\n\n')
##
##    if __name__ == '__main__':
##        convert_defines(CONFIG)
