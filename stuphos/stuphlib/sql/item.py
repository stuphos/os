from sqlobject import *

class StuphItemRecord(SQLObject):
	vnum            = IntCol(unique = True)

	name            = StringCol()
	shortdescr      = StringCol()
	longdescr       = StringCol()
	actiondescr     = StringCol()

	# itemtype? kind?
	type            = IntCol() # Convert into string/text type name (formencode.validators?)

	extraflags      = IntCol()
	wearflags       = IntCol()
	antiflags       = IntCol()
	weight          = IntCol()
	cost            = IntCol()
	minlevel        = IntCol()
	timer           = IntCol()
	trap            = IntCol()

	vals            = BLOBCol() # convert with validator
	extradesc       = BLOBCol() # convert with validator
	affections      = BLOBCol() # convert with validator

	specproc        = StringCol()

	stuphZoneRecord = ForeignKey('StuphZoneRecord')
