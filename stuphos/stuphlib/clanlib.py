from stuphlib.dblib import SingleRecordReader
from stuphlib.binary import Record, BuildRecordClass

from datetime import datetime

NUM_CLAN_RANKS = 10

class ClanReader(SingleRecordReader):
    def parseRecord(self):
        # Read one record per file -- #<vnum> already read.
        self.recordField('alias', self.tildeString())
        self.recordField('name', self.tildeString())
        self.recordField('colorized_name', self.tildeString())

        (donation_room, entrance_room, recall_room,
         range_low_room, range_high_room) = self.readLine().split()

        self.recordField('donation_room'  , donation_room   )
        self.recordField('entrance_room'  , entrance_room   )
        self.recordField('recall_room'    , recall_room     )
        self.recordField('range_low_room' , range_low_room  )
        self.recordField('range_high_room', range_high_room )

        # I believe these are currently unused.
        (store_object, last_updated, updated_by) = self.readLine().split()

        self.recordField('store_object', store_object )
        self.recordField('last_update' , last_updated )
        self.recordField('updated_by'  , updated_by   )

        # Read rank titles.
        ranks = []
        for x in range(NUM_CLAN_RANKS):
            male = self.tildeString()
            female = self.tildeString()

            rank = dict(male = male, female = female)

            self.recordField('rank%d' % (x + 1), rank)
            ranks.append(rank)

        self.recordField('ranks', ranks)

ClanPowers = [('apply'  , -1),
              ('ban'    ,  8),
              ('demote' ,  8),
              ('deposit',  2),
              ('donate' ,  0),
              ('enlist' ,  5),
              ('expel'  ,  8),
              ('help'   , -1),
              ('info'   , -1),
              ('log'    ,  0),
              ('promote',  6),
              ('ranks'  ,  0),
              ('recall' ,  0),
              ('resign' ,  6),
              ('roster' ,  8),
              ('set'    ,  9),
              ('title'  ,  0),
              ('unban'  ,  8),
              ('who'    ,  0),
              ('withdraw', 6)]

class ClanBanRec(Record, metaclass=BuildRecordClass):
    Fields = [('idnum', Record.Long  ), # Player banned
              ('by'   , Record.Long  ), # Who did the banning
              ('when' , Record.TimeT )]

    BANTIME_FORMAT = '%a, %b %e (%T)'

    def __str__(self):
        timestr = datetime.fromtimestamp(self.when).strftime(BANTIME_FORMAT)
        return '&C%-20.20s &Nby &C%-20.20s&N on %s' % \
               (self.idnum, self.by, timestr)

def ReadClanBankFile(fp):
    for line in fp:
        if line == '':
            break

        line = line.strip()
        if line == '$':
            break

        (vnum, amount) = line.split()
        yield (int(vnum),
               int(amount))

def ReadClanInformation(fp):
    return fp.read()

# Indexing.
from stuphlib.dblib import LocalIndex, INDEX_FILE
from stuphlib.wldlib import Record as WorldRecord, Initializer
from stuphlib.binary import ReadFile

ClanDataPrefix = 'data'
ClanDataSuffix = 'dat'

ClanInfoPrefix = 'info'
ClanInfoSuffix = 'inf'

ClanBanPrefix  = 'ban'
ClanBanSuffix  = 'ban'

CLAN_BANK_FILE = 'bank'

class ClanIndex:
    def clanFileName(self, prefix, vnum, suffix):
        return self.joinpath(prefix, '%d.%s' % (vnum, suffix))

    def clandatafile(self, vnum):
        return self.clanFileName(ClanDataPrefix, vnum, ClanDataSuffix)
    def claninfofile(self, vnum):
        return self.clanFileName(ClanInfoPrefix, vnum, ClanInfoSuffix)
    def clanbanfile(self, vnum):
        return self.clanFileName(ClanBanPrefix , vnum, ClanBanSuffix)

    def openClanDataFile(self, vnum):
        return self.open(self.clandatafile(vnum))
    def openClanInfoFile(self, vnum):
        return self.open(self.claninfofile(vnum))
    def openClanBanFile(self, vnum):
        return self.open(self.clanbanfile(vnum))

    def clanbankfile(self):
        return CLAN_BANK_FILE
    def openClanBankFile(self):
        return self.open(self.clanbankfile())

class ClanLocalIndex(ClanIndex, LocalIndex):
    pass

class ClanBank:
    def __init__(self, balance):
        self.balance = balance
    def __repr__(self):
        return '%s: %d gold' % (self.__class__.__name__,
                                self.balance)

class Clan(WorldRecord):
    class Meta(WorldRecord.Meta):
        __attributes__ = ('name', 'bank', 'ranks', 'information')

    def __init__(self, base, vnum):
        Initializer.__init__(self)
        self.base = base

        (self) << (vnum)

    # Implementation of Record.
    ReaderClass = ClanReader

    def loadFromReader(self, reader):
        reader.parseFile()
        recordSet = reader.consumeRecordSet()
        self.vnum = list(recordSet.keys())[0]
        self.__dict__.update(recordSet[self.vnum])

    def loadFrom(self, vnum):
        self.loadFromFile(self.base.openClanDataFile(vnum))
        self.information = ReadClanInformation(self.base.openClanInfoFile(vnum))
        self.ban_list = list(ReadFile(self.base.openClanBanFile(vnum),
                                      ClanBanRec))

def LoadClans(clan_base, index_file):
    index = ClanLocalIndex(clan_base)

    clans = dict()
    for (vnum, fix) in index.iterindex(index_file):
        clans[vnum] = Clan(index, vnum)

    # Load bank data.
    for (vnum, bank) in ReadClanBankFile(index.openClanBankFile()):
        clans[vnum].bank = ClanBank(bank)

    return clans

def main(argv = None):
    from optparse import OptionParser
    from code import InteractiveConsole as IC

    parser = OptionParser()
    parser.add_option('-i', '--index-file', default = INDEX_FILE)
    parser.add_option('-b', '--clan-base')
    (options, args) = parser.parse_args(argv)

    index_file = options.index_file
    clan_base = options.clan_base
    assert clan_base

    clans = LoadClans(clan_base, index_file)

    import readline
    IC(locals = dict(clans = clans)).interact(banner = '')

##        print '========================================================================'
##        print 'Currently Banned:'
##        print '========================================================================'
##                print '&Y%3d. %s' % (x, ban)

if __name__ == '__main__':
    main()
