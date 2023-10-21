from stuphlib.binary import Record, BuildRecordClass, ReadFile
from stuphlib.rent import RentedItemData

HOUSE_PRIVATE = 0
HOUSE_OPEN    = 1

def ModeName(mode):
    return {HOUSE_PRIVATE : 'Private',
            HOUSE_OPEN    : 'Open'}.get(mode) \
            or 'Mode #%d' % mode

class HouseControlRec(Record, metaclass=BuildRecordClass):
    class Types:
        MAX_GUESTS = 10

        RoomVnum   = Record.Int
        GuestArray = Record.Array(Record.Long, MAX_GUESTS)

    Fields = [('vnum',          Types.RoomVnum   ), # vnum of this house
              ('atrium',        Types.RoomVnum   ), # vnum of atrium
              ('exit_num',      Record.ShInt     ), # direction of house's exit
              ('built_on',      Record.TimeT     ), # date this house was built
              ('mode',          Record.Int       ), # mode of ownership
              ('owner',         Record.Long      ), # idnum of house's owner
              ('num_of_guests', Record.Int       ), # how many guests for house
              ('guests',        Types.GuestArray ), # idnums of house's guests
              ('last_payment',  Record.TimeT     ), # date of last house payment
              ('max_item_save', Record.Long      ), # max number of items saved
              ('spare1',        Record.Long      ),
              ('spare2',        Record.Long      ),
              ('spare3',        Record.Long      ),
              ('spare4',        Record.Long      ),
              ('spare5',        Record.Long      ),
              ('spare6',        Record.Long      ),
              ('spare7',        Record.Long      )]

    def __str__(self):
        return HouseToString(self)

def LoadHouseFile(fp):
    return list(ReadFile(fp, RentedItemData))

# Report.
def HouseToString(house):
    return '\n'.join(['House:',
                      '  Room          : #%d' % house.vnum,
                      '  Owner         : #%d' % house.owner,
                      '  Atrium        : #%d' % house.atrium,
                      '  Build Date    : %s' % datestring(house.built_on),
                      '  Mode          : %s' % ModeName(house.mode),

                      '  Guests        : (%d)' % house.num_of_guests,
                      getGuests(house.guests),

                      '  Last Payment  : [%d] %s' % (house.last_payment,
                                                     datestring(house.last_payment)),

                      '  Max Item Save : %d' % house.max_item_save,
                      ''])

from datetime import datetime
def datestring(seconds):
    return datetime.fromtimestamp(seconds).ctime()

def getGuests(guests):
    return '  Guests        : %r' % guests
    return '\n    '.join('Idnum       : #%d' % idnum \
                         for idnum in guests),

Housefix = 'house'
def main(argv = None):
    from os.path import dirname, join as joinpath
    if argv is None:
        from sys import argv

    for filename in argv[1:]:
        housepath = joinpath(dirname(dirname(filename)), Housefix)
        for house in ReadFile(open(filename), HouseControlRec):
            print(house)

            housefile = joinpath(housepath, '%d.%s' % (house.vnum, Housefix))
            for item in LoadHouseFile(open(housefile)):
                print(item)

if __name__ == '__main__':
    main()
