from .dblib import *

class RoomReader(RecordReader):
	def parseRecord(self):
		self.recordField('name',  self.tildeString())
		self.recordField('descr', self.tildeString())

		zoneNo, flags, sector = self.readLine().split()
		self.recordField('flags', ASCIIFlagDecode(flags))
		self.recordField('sector', int(sector))

		while 1:
			line = self.readLineNoEOF(self.EOFNoDollar).strip()
			c = line[0]

			if c is 'S':
				break

			if c is '$':    # detected end of records
				return  # return None-value to terminate caller

			if c is 'D':
				dir      = int(line[1:].strip())
				descr    = self.tildeString()
				keyword  = self.tildeString()

				line = self.readLineNoEOF('Expected Exit Info')

				flags, key, roomLinkNo = line.split()

				self.roomExit(dir, int(roomLinkNo), keyword, descr, int(key), ASCIIFlagDecode(flags))

			elif c is 'E':
				self.roomDescription(self.tildeString(), self.tildeString())
			elif c is '#':
				# Raise warning accordingly??
				return int(line[1:])
			else:   # Not expecting a hash mark before 'S' terminator.
				raise FormatError('Expected D/E/S: %r' % line)

		# Parse and return next hashed vnum.
		line = self.readLineNoEOF(self.EOFNoDollar)
		c = line[0]

		if c == '$':    # detected end of records
			return  # return None-value to terminate caller

		if c == '#':    # start of next record
			return int(line[1:])

		raise FormatError("Trailing room record: '%s' (%s:%d)" % (makePrintable(c), self.filename, self.lineno))

	def roomDescription(self, keyword, text):
		r = self.getCurrentRecord()
		if 'text' in r:
			r['text'][keyword] = text
		else:
			r['text'] = {keyword:text}

	def roomExit(self, dir, roomLinkNo, keyword, descr, key, flagstr):
		ex = {'room-link':roomLinkNo,'keyword':keyword,'descr':descr,'key':key,'flags':flagstr}
		r = self.getCurrentRecord()

		if 'exits' in r:
			r['exits'][dir] = ex
		else:
			r['exits'] = {dir:ex}


## SQLObject representation.
DEFAULT_ROOM_DBFL = 'lib/etc/rooms.db'

def openRoomTables(dbpath):
	from .sql import openDatabaseTables
	return openDatabaseTables \
		(dbpath, 'StuphRoomRecord', schema_package = 'sql.room')

def convert_room_row(vnum, room, columns):
	'Convert Room Record into a mapping suitable for SQLObject row representation.'
	from .sql import getStuphZoneRecordIDByZoneVnum

	row = {'vnum' : vnum}
	for n in columns:
		if n in room:
			row[n] = room[n]

	# Join with these in a separate table.
	row['extradesc']    = buffer(str(row.get('extradesc', {})))
	row['exits']        = buffer(str(row.get('exits',     {})))

	# Resolve this.
	row['stuphZoneRecordID'] = getStuphZoneRecordIDByZoneVnum(vnum / 100)

	return row

def loadStuphRoomRecords(dbpath = DEFAULT_ROOM_DBFL, populate_with = None):
	StuphRoomRecord = openRoomTables(dbpath)[0]

	if populate_with:
		def iterate_population(p):
			if type(p) is list:
				for x in p:
					for y in iterate_population(x):
						yield y
			elif type(p) is str:
				for x in RoomReader(p).parseFile().consumeRecordSet().items():
					yield x

		columns = list(StuphRoomRecord.sqlmeta.columns.keys())

		for (vnum, room) in iterate_population(populate_with):
			StuphRoomRecord(**convert_room_row(vnum, room, columns))

	return StuphRoomRecord

def test(*args):
	room_mapping = {}
	for filename in args:
		room_mapping.update(RoomReader(filename).parseFile().consumeRecordSet())
	return room_mapping

def main(opts = []):
	if '-test' in opts:
		opts.remove('-test')

		global room_mapping
		room_mapping = test(*opts)
	else:
		n = len (opts)
		i = 0

		populate_with = []
		dbfile = DEFAULT_ROOM_DBFL

		while i < n:
			a = opts[i]

			if a in ('-new', '-new-db', '-newdb'):
				dbfile = new_database_file()
			elif a in ('-db', '-dbfile', '-dbpath'):
				i += 1
				dbfile = opts[i]
			else:
				populate_with.append(a)

			i += 1

		return loadStuphRoomRecords(dbfile, populate_with = populate_with)

if __name__ == '__main__':
	from sys import argv

	if '-debug' in argv:
		from pdb import runcall
		main_app = main

		def main(*args):
			return runcall(main_app, *args)

		argv.remove('-debug')

	R = main(argv[1:])
