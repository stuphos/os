#!/usr/local/bin/python -i
"""CircleMUD object database file interpreter.

Version: %(__version__)f

Class: ObjectReader
	constructor - first argument is either an open file handle,
		a string path name for a file to open, or a zone number
		for loading from a builtin library path

	parseFile() - initiate process to read entire file.  Calls
		startOfRecords(), newRecord(), recordField(), recordDescription(),
		recordAffection() and endOfRecords().
		Override these methods on subclass to implement your own
		records processing.

	result field - dictionary holding entire parsed-file database

"""
# Fraun Dec 24th 2005 - Converted to use RecordReader.

__version__ = 0.3
# __all__ = ['ObjectReader', 'ExtraDescription']

def usage():return __doc__%{'__version__':__version__}

from .dblib import *

class ExtraDescription:
	def __init__(self, keyword, text):
		self.keyword=keyword
		self.text=text

	#def __repr__(self):pass

class Affection:
	def __init__(self, location, modifier):
		self.location=location
		self.modifier=modifier

	#def __repr__(self):pass

class ObjectReader(RecordReader):
	def parseRecord(self):
		"""Load record area into logical Python object

		file argument is an open file handle

		Format of textually-defined object prototype:

		<Name String (keywords)>~<NL>
		<Short Description>~<NL>
		<Long Room Description (multiline)><NL>
		~<NL>
		<Action Description (multiline)><NL>
		~<NL>
		<Type as Integer Code> <ASCII-flag for Extra Bits> <ASCII-flag for Wear Bits>
			<ASCII-flag for Anti Bits><NL>
		<Integer Object Value 1> <Value 2> <Value 3> <Value 4><NL>
		<Integer Weight> <Cost> <Rent><NL>

			Extra Description/Affection/Special declarations Follow:
		E
		<Extra Description keywords>~<NL>
		<Extra description text (multiline)><NL>
		~<NL>
		A
		<Integer Affect Location Code> <Modifier Code><NL>
		S

			Singular Special (espec) Fields Follow:
		Timer: -1 to 100
		Trap: <Integer code>

		"""

		# Pass each field read to handler function
		self.recordField('name', self.tildeString('name'))
		self.recordField('shortdescr', self.tildeString('shortdescr'))
		self.recordField('longdescr', self.tildeString('longdescr'))
		self.recordField('actiondescr', self.tildeString('actiondescr'))

		type, extra, wear, anti = self.readLine().split()
		self.recordField('type', int(type))
		self.recordField('extraflags', ASCIIFlagDecode(extra))
		self.recordField('wearflags', ASCIIFlagDecode(wear))
		self.recordField('antiflags', ASCIIFlagDecode(anti))

		self.recordField('vals', [int(v) for v in self.readLine().split()])

		weight, cost, rent = self.readLine().split()
		self.recordField('weight', int(weight))
		self.recordField('cost', int(cost))
		self.recordField('minlevel', int(rent)) # Rent is minlevel..

##		timer=trap=0

##		extraDescr=[]
##		affections=[]

		line=self.readLine()

		while line!='':
			c=line[0]

			if c=='$': # detected end of records
				#print '} End Last Object'
				return

			if c=='#': # start of next record
				#print '} End Object, Next'
				try: return int(line[1:])
				except ValueError:
					raise FormatError('Expected #<vnum> of next record; got %r' % line[1:])

			if c=='E':
				self.objectDescription(
					self.tildeString('exdesc keywords'),
					self.tildeString('exdesc descr'))

			else:
				# This is done here because these blocks all uses additional lines
				line = self.readLine()

				assert line != '', FormatError("EOF expecting data for '%c'" % c)

				if c == 'A':
					location, modifier = line.split()

					self.objectAffection(location, modifier)

				elif c == 'S':
					while True:
						# Fraun Mar 1st 2006 - Note the necessary heading ' ' involved
						if line[:1] == '$':break # End of 'S' section.
						elif line[:1] == '#':
							# This isn't part of of parse_espec, but I wonder about old formats...
							# Todo: Warn.
							try: return int(line[1:])
							except ValueError:
								raise FormatError('Expected #<vnum> of next record; got %r' % line[1:])

						# Eww, but at least it's lowercase.
						elif line[:7] == 'Timer: ':self.recordField('timer', int(line[7:]))
						elif line[:6] == 'Trap: ':self.recordField('trap', int(line[6:]))
						elif line[:10] == 'SpecProc: ':self.recordField('specproc', line[10:])
						else:raise FormatError('Unknown S-type line "%r" (object #%d; line %d)' % (line, self.getVirtualNumber(), self.lineno))

						line = self.readLine()
						if line == '':
							return self.EOFNoDollar()

				else:
					raise FormatError("Unknown E/A/S-type '%r' (object #%d; line %d)" % (makePrintable(c), self.getVirtualNumber(), self.lineno))

			line=self.readLine()

		# No $ at terminating records at end of file
		#print '} End Object -- EOFNoDollar'
		return self.EOFNoDollar()

	# This is called for parsed EXTRA descriptions.  Other string descriptions
	# are parsed as recordFields
	def objectDescription(self, keyword, text):
		r = self.getCurrentRecord()

		if 'extradescr' in r:
			# ExtraDescription(keyword, text)
			r['extradescr'][keyword] = text
		else:
			# ExtraDescription(keyword, text)
			r['extradescr'] = {keyword:text}

	# Object affection data
	def objectAffection(self, location, modifier):
		aff = Affection(location, modifier)
		r = self.getCurrentRecord()

		if 'affections' in r:
			r['affections'].append(aff)
		else:
			r['affections'] = [aff]

## SQLObject representation.
DEFAULT_ITEM_DBFL = 'lib/etc/items.db'

def openItemTables(dbpath):
	from .sql import openDatabaseTables
	return openDatabaseTables \
		(dbpath, 'StuphItemRecord', schema_package = 'sql.item')

def convert_item_row(vnum, item, columns):
	'Convert Object Record into a mapping suitable for SQLObject row representation.'
	from .sql import getStuphZoneRecordIDByZoneVnum

	row = {'vnum' : vnum}
	for n in columns:
		if n in item:
			row[n] = item[n]

		# (S)pecial .obj file record section
		elif n in ('timer', 'trap'):
			row[n] = 0
		elif n in ('specproc',):
			row[n] = ''

	# Join with separate tables for extra-descriptions.  values? affections??
	row['vals']       = buffer(str(row.get('vals',  [0,0,0,0])))
	row['extradesc']  = buffer(str(row.get('extradescr',   [])))
	row['affections'] = buffer(str(row.get('affections',   [])))

	# Resolve this.
	row['stuphZoneRecordID'] = getStuphZoneRecordIDByZoneVnum(vnum / 100)

	return row

def loadStuphItemRecords(dbpath = DEFAULT_ITEM_DBFL, populate_with = None):
	StuphItemRecord = openItemTables(dbpath)[0]

	if populate_with:
		def iterate_population(p):
			if type(p) is list:
				for x in p:
					for y in iterate_population(x):
						yield y
			elif type(p) is str:
				for x in ObjectReader(p).parseFile().consumeRecordSet().items():
					yield x

		columns = list(StuphItemRecord.sqlmeta.columns.keys())

		for (vnum, item) in iterate_population(populate_with):
			StuphItemRecord(**convert_item_row(vnum, item, columns))

	return StuphItemRecord

def test():
	reader=ObjectReader('lib/0.obj')
	reader.parseFile()

	return reader.consumeRecordSet()

def main(opts = []):
	if '-test' in opts:
		print(test())
	else:
		n = len (opts)
		i = 0

		populate_with = []
		dbfile = DEFAULT_ITEM_DBFL

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

		return loadStuphItemRecords(dbfile, populate_with = populate_with)

if __name__ == '__main__':
	from sys import argv

	if '-debug' in argv:
		from pdb import runcall
		main_app = main

		def main(*args):
			return runcall(main_app, *args)

		argv.remove('-debug')

	I = main(argv[1:])
