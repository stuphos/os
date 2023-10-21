# Installation of Computation Core.

from stuphos.xmlrpc import getHost
from stuphos.xmlrpc import host

from stuphos.xmlrpc.config import NotConfigured


from stuphos import getConfig
from stuphos.etc import isYesValue

if isYesValue(getConfig('metal', 'VM')):
	from ph.emulation.metal import Machine
	from ph.emulation.metal import MachineCore
	from ph.emulation.metal import Native
	from ph.emulation.metal import TaskControl

	from ph.emulation.metal import Heartbeat

	from ph.emulation.metal import Processor
	from ph.emulation.metal import Subroutine

else:
	from ph.emulation.machine.virtual import Machine
	from ph.emulation.machine.virtual import MachineCore
	from ph.emulation.machine.virtual import Native
	from ph.emulation.machine.virtual import Pure
	from ph.emulation.machine.virtual import TaskControl
	# from ph.emulation.machine.virtual import startTask

	from ph.emulation.machine.virtual import machine
	from ph.emulation.machine.virtual import checkActiveTasks
	from ph.emulation.machine.virtual import checkActiveTimers
	from ph.emulation.machine.virtual import BypassReturn
	from ph.emulation.machine.virtual import OuterFrame
	from ph.emulation.machine.virtual import Continuation
	from ph.emulation.machine.virtual import resolve_procedure
	from ph.emulation.machine.virtual import EmptyStackError

	from ph.emulation.machine import currentVMTask
	from ph.emulation.machine import vmCurrentTask
	from ph.emulation.machine import vmCheckAccess
	from ph.emulation.machine import vmNewMapping
	from ph.emulation.machine import vmNewSequence
	from ph.emulation.machine import nativeObject
	from ph.emulation.machine import nativeMemoryObject
	from ph.emulation.machine import deletable
	from ph.emulation.machine import baseStringClass
	from ph.emulation.machine import StringValue
	from ph.emulation.machine import InlineTextClass
	from ph.emulation.machine import TaskCreation

	from ph.emulation.machine.memory import AutoMemoryObject
	from ph.emulation.machine.memory import AutoMemoryMapping
	from ph.emulation.machine.memory import AutoMemorySequence
	from ph.emulation.machine.memory import AutoMemoryNamespace
	from ph.emulation.machine.memory import protectedMemoryCopy
	from ph.emulation.machine.memory import protectedMemoryLoad
	from ph.emulation.machine.memory import MemoryMapping
	from ph.emulation.machine.memory import MemorySequence


	from ph.emulation.machine.heartbeat import Heartbeat

	from ph.emulation.operation.application import Processor
	from ph.emulation.operation.application import Subroutine
	from ph.emulation.operation.application import Generator
	from ph.emulation.operation.application import FastLocals


	try: from ph.emulation.machine.parallel import pool
	except ImportError: pass


from ph.emulation.security import RelationNetwork


# debugOn()
try:
	from ph.interpreter import mental as interpreter

	# from stuphos.runtime import Undefined
	from ph.interpreter.mental import Undefined

	from ph.interpreter.mental import Assembly
	from ph.interpreter.mental import CallMethodError
	from ph.interpreter.mental import Girl
	from ph.interpreter.mental import Ella # New symbology.
	from ph.interpreter.mental import Agent
	from ph.interpreter.mental import ParallelTask
	from ph.interpreter.mental import Programmer
	from ph.interpreter.mental import Script
	from ph.interpreter.mental import Volume
	from ph.interpreter.mental import callGirlMethod
	from ph.interpreter.mental import executeGirl
	from ph.interpreter.mental import getLibraryCore
	from ph.interpreter.mental import grammar
	from ph.interpreter.mental import invokeLibraryMethod
	from ph.interpreter.mental import newModuleTask
	from ph.interpreter.mental import callStringValueMethod

	from ph.interpreter.mental import findUser
	from ph.interpreter.mental import findUserByName
	from ph.interpreter.mental import findCurrentUser

	from ph.interpreter.mental import native
	from ph.interpreter.mental import nullproc

	from ph.interpreter.mental.objects import Library
	from ph.interpreter.mental.objects import LibraryNode
	from ph.interpreter.mental.objects import Instance
	from ph.interpreter.mental.objects import GirlSystemModule
	from ph.interpreter.mental.objects import SyntheticClass
	from ph.interpreter.mental.objects import constrainStructureMemory
	from ph.interpreter.mental.objects import NoSymbolError

	from ph.interpreter.mental.grammar import GrammaticalError

	from ph.interpreter.mental.compiler import WMBasedCompiler

	from ph.interpreter.mental.native import sleep, create, call
	from ph.interpreter.mental.native import _securityContext as securityContext
	from ph.interpreter.mental.native import _accessItemsNative as accessItemsNative
	from ph.interpreter.mental.native import _setTimeout

	from ph.interpreter.mental.ipc import cleanupObject # , channel

	from ph.interpreter.mental.library.model import GirlCore
	from ph.interpreter.mental.library.model import LIB_ROOT
	from ph.interpreter.mental.library.extensions import serverChannel

	def getLibraryViews():
		# The views module relies on django settings which might not
		# be loaded when this kernel module is loaded.
		from ph.interpreter.mental.library import views
		return views

	def wm(*args, **kwd):
		global wm
		from ph.interpreter.mental.library.views import wm
		return wm(*args, **kwd)

	# from ph.interpreter.mental.library.views import LibraryView

# Disable interpreter.
except ImportError as e:
	# todo: print stack trace
	print(f'[stuphos.kernel:interpreter] {e}')

	# from stuphos import logException
	# logException(traceback = True)
	# debugOn()


##    XXX MOBILE_TRIGGER_TYPES :skip:
##    XXX getMobileTriggerSheet :skip:
##    XXX getMobileTriggerType :skip:
##    XXX libraryViews :skip:


from stuphos.runtime.architecture.routines import importAllInit
importAllInit(configuration.VM.kernel, '[VM:kernel]', globals())
