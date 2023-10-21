# Use this when you want to extend the core with third party modules and you need an api
# package to include to use all of the package functions.

#
# This represents the underlying language architecture with which we build the application
# package out of.  In otherwords, all of the basic, system and utilitarian functions and
# objects are brought in by this module to unify their particular platform-specific imple-
# mentations with the object definitions of the package model.

# It probably makes sense to import these things specifically into the different features
# of the package, but we're trading off detailed provisioning with a more broad platform
# compatibilty design.  The only thing a detail provisioning does for us at this point is
# decouple the features from the application instead of preloading everything at boot.
#
# Also, to pre-import might mean committing to a certain implementation in terms of what
# components this module represents for the larger application product.

# Just import all of the platform objects here, and then import what you need in modules.

from stuphos import getConfig, getConfigObject, getSection, enqueueHeartbeatTask
from stuphos import logException, log as mudlog, inline

from stuphos import db
from stuphos.db import dbCore

from stuphos.runtime import Synthetic, Object, Undefined, LookupObject
from stuphos.runtime.facilities import Facility
from stuphos.runtime.registry import getObject

from stuphos.runtime.architecture import Procedure, Computer, Source, Yield, Continuation
from stuphos.runtime.architecture import OuterFrame, BypassReturn, Generator, YieldFrame
from stuphos.runtime.architecture import NoAccessException, InterpreterState, Uncompleted
from stuphos.runtime.architecture import newComponent, writable, writeprotected, blockSetAttr
from stuphos.runtime.architecture import wrapper, representable, Transparent, Translucent
from stuphos.runtime.architecture import ExceptionType, baseExceptionValue
from stuphos.runtime.architecture import extension, extensionObject, baseExceptionValue
from stuphos.runtime.architecture import baseInstance, safeNativeClass, _safe_native, _safe
from stuphos.runtime.architecture import safeNativeClass as _safe_native_class
from stuphos.runtime.architecture import safeNativeObject, _safe_native_object
from stuphos.runtime.architecture import _safe_iterator, ScheduledProcedureMixin
from stuphos.runtime.architecture import safeNativeNoKeyword, isSpecialPrincipal

from stuphos.runtime.architecture.routines import apply

from stuphos.etc import isYesValue, isNoValue, nth
from stuphos.etc import reraise, reraiseSystemException
from stuphos.etc import getSystemException, getSystemExceptionString

from stuphos.etc.tools import ordereddict, getSystemException, isYesValue
from stuphos.etc.tools.timing import date as now, Elapsed
from stuphos.etc.tools.misc import pickleSafe

from stuphos.db.orm import (GirlNode, GirlBootOrderNode, GirlPermission,
							GirlPrincipalGroup, PrincipalRelation)

from stuphmud import server as mud
from phsite.network import renderTemplate


# Dynamically-linked symbols.  Because of complex imports, and now the separation of
# these packages, some symbols need to be loaded dynamically.  This means a certain
# re-architecting of depending code in some cases where it is previously done at the
# beginning of its module initialization.

def getWebProgrammer():
	from phsite.network.embedded.olc import WebProgrammer
	return WebProgrammer

def getIsSuperuser():
	from phsite.network import is_superuser
	return is_superuser

def getNoAccessTemplate():
	from phsite.network.embedded.olc.base import NOACCESS_TEMPLATE
	return NOACCESS_TEMPLATE

def getMobileWrapper():
	from phsite.network.embedded.olc.triggers import MobileWrapper
	return MobileWrapper

def getFindClaimedPlayers():
	from phsite.network.embedded.olc import findClaimedPlayers
	return findClaimedPlayers

def getOn():
	from stuphmud.server import on
	return on # mud.on

def getPlayerModel():
	from phsite.network.models.realm import Player
	return Player

def getDefaultPlayerModel():
	from phsite.network.models.realm import DefaultPlayer
	return DefaultPlayer

def getUsageModel():
	from phsite.network.models.realm import Usage
	return Usage

def getFindUserByName():
	from phsite.network.accounts import findUserByName
	return findUserByName

def getFindUser():
	from phsite.network.accounts import findUser
	return findUser

def getFindCurrentUser():
	from phsite.network.accounts import findCurrentUser
	return findCurrentUser


# Some particular things cannot be imported at boot time, like the task processor
# base class that is actually depending on some derivative functionality.. which
# is wrong, but I will let that feature's development determine how to resolve
# itself because for now, the only solution is to just leave it unchanged and out
# of this architectural module.

# from ph.language.interpreter import native, objects as girlObjects, Girl, Script
# from ph.language.interpreter.objects import GirlSystemModule


# These things can't exactly be imported into an architecture pretty much because of
# dependencies, which primarily means that those functions must specifically import
# their components from other parts of THIS package.  As you can see, they're all
# relative, so I pretty leave them unchanged.

# from . import Object, Procedure, Heartbeat, Scheduling, tasklog, billing
# from .heartbeat import Heartbeat

# from .vtpool import VTPool as RealtimeAPI
# from ..virtual import Machine as VM, Native, Pure


# Some modules in this package shouldn't actually be here.  They rely on these things:

# from ph.network.server.player.interfaces.dictcmd import CmdDict

# from ph.emulation import startTask

