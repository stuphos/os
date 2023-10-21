"CircleMUD shop database file interpreter."
from .dblib import RecordReader

class ShopReader(RecordReader):
	VERSION3_TAG="v3.0"

	# Read all records in file
	def parseFile(self):
		'Override'
		line = self.readLineNoEOF("Shop Version Line (First)")

		if self.VERSION3_TAG in line:
			self.v3format = True

		self.startOfRecords()

		while 1:
			line = self.readLineNoEOF("Record VNR")

			c = line[0]
			if c == '$':
				break

			assert c == '#', ('Line %d: ' % self.lineno) + repr("[%s != '#'] %s" % (c, line[1:]))

			# This hack simply ignores all non-digits and goes from there.
			vno = int (''.join([n for n in line if n.isdigit()]))

			self.newRecord(vno)
			self.parseRecord()

		self.endOfRecords()

	def readBuyType(self):
		"Returns None on malformat; empty-string on end-of-list indicator (-1); otherwise a 2-tuple."
		try:
			line=self.readLine().strip()

			i=line.find(';')
			line=(i>=0) and line[:i] or line[:-1]

			parts=line.split(' ')
			num=int(parts[0])

			return (num==-1) and '' or (num, parts[1])

		except:
			return None

	def readBuyTypeList(self):
		if not getattr(self, 'v3format'):
			return self.readNumberList()

		buyTypes=[];append=buyTypes.append

		while True:
			bt=self.readBuyType()
			if not bt:
				break

			append(bt)

		return buyTypes

	# read_shop_message validates %-formatters: we'll skip this.
	readShopMessage = RecordReader.tildeString

	def parseRecord(self):
		"Load record area into logical Python object."

		# boot_the_shops sets the 'zone' member: we'll skip this.

		self.recordField('producing',     self.readNumberList())

		self.recordField('buy-profit',    self.readFloat())
		self.recordField('sell-profit',   self.readFloat())

		self.recordField('buy-type',      self.readBuyTypeList())

		self.recordField('no-such-item1', self.readShopMessage())
		self.recordField('no-such-item2', self.readShopMessage())
		self.recordField('do-not-buy',    self.readShopMessage())
		self.recordField('missing-cash1', self.readShopMessage())
		self.recordField('missing-cash2', self.readShopMessage())
		self.recordField('message-buy',   self.readShopMessage())
		self.recordField('message-sell',  self.readShopMessage())

		self.recordField('temper',        self.readInteger())
		self.recordField('bitvector',     self.readInteger())

		self.recordField('shopkeeper',    self.readInteger())
		self.recordField('trade-with',    self.readInteger())

		self.recordField('rooms',         self.readNumberList())

		self.recordField('open-1',        self.readInteger())
		self.recordField('open-2',        self.readInteger())
		self.recordField('close-1',       self.readInteger())
		self.recordField('close-2',       self.readInteger())


if __name__=='__main__':
	from glob import glob
	from sys import argv
	from os.path import join

	argv = argv[1:]
	if argv:
		x = [ShopReader(n)._() for n in glob(join(argv[0], '*.shp'))]
