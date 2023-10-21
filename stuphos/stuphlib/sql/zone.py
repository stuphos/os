from sqlobject import *

class StuphZoneCommand(SQLObject):
	type            = StringCol(length = 1)
	ifFlag          = IntCol()

	arg1            = IntCol()
	arg2            = IntCol()
	arg3            = IntCol()

	stuphZoneRecord = ForeignKey('StuphZoneRecord')

class StuphZoneRecord(SQLObject):
	# StuphZoneRecord.byVnum(12)
	vnum      = IntCol(alternateID = True)

	name      = StringCol()

	top       = IntCol()
	flags     = IntCol()
	lifespan  = IntCol()
	resetMode = IntCol()
	continent = IntCol()

	# zone = StuphZoneRecord(**Record)
	# StuphZoneCommand(stuphZoneRecord = zone, **Command)

	commands  = MultipleJoin('StuphZoneCommand')

	# RelatedJoin??
	rooms     = MultipleJoin('StuphRoomRecord')
	items     = MultipleJoin('StuphItemRecord')
