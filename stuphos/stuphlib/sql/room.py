from sqlobject import *

class StuphRoomRecord(SQLObject):
	vnum            = IntCol()

	name            = StringCol()
	descr           = StringCol()
	flags           = IntCol()
	sector          = IntCol()

	exits           = BLOBCol()
	extradesc       = BLOBCol()

	stuphZoneRecord = ForeignKey('StuphZoneRecord')

