from stuphlib.binary import Record, BuildRecordClass, ReadFile

class RentedItemData(Record, metaclass=BuildRecordClass):
    # obj_file_elem
    class Types:
        class ItemAffectedType(Record, metaclass=BuildRecordClass):
            # obj_affected_type
            Fields = [('location', Record.Byte),
                      ('modifier', Record.SByte)]

        NAME_LENGTH        = 128
        DESCR_LENGTH       = 256
        SHORT_DESCR_LENGTH = 128

        NUM_VALUES         = 4
        MAX_OBJ_AFFECT     = 6

        ObjVnum            = Record.Int

        NameArray          = Record.CString(NAME_LENGTH)
        DescrArray         = Record.CString(DESCR_LENGTH)
        ShortDescrArray    = Record.CString(SHORT_DESCR_LENGTH)

        ValueArray         = Record.Int       [NUM_VALUES        ]

        AffectedArray      = Record.Array(ItemAffectedType, MAX_OBJ_AFFECT)

    Fields = [('item_number'      , Types.ObjVnum          ),
              ('name'             , Types.NameArray        ),
              ('description'      , Types.DescrArray       ),
              ('short_description', Types.ShortDescrArray  ),
              ('locate'           , Record.ShInt           ),
              ('value'            , Types.ValueArray       ),
              ('item_type'        , Record.Int             ),
              ('extra_flags'      , Record.Int             ),
              ('anti_flags'       , Record.Int             ),
              ('wear_flags'       , Record.Int             ),
              ('weight'           , Record.Int             ),
              ('timer'            , Record.Int             ),
              ('bitvector'        , Record.Long            ),
              ('affected'         , Types.AffectedArray    )]

class RentFileInfo(Record, metaclass=BuildRecordClass):
    # rent_info
    Fields = [('time',              Record.Int),
              ('rentcode',          Record.Int),
              ('net_cost_per_diem', Record.Int),
              ('gold',              Record.Int),
              ('account',           Record.Int),
              ('nitems',            Record.Int),
              ('spare0',            Record.Int),
              ('spare1',            Record.Int),
              ('spare2',            Record.Int),
              ('spare3',            Record.Int),
              ('spare4',            Record.Int),
              ('spare5',            Record.Int),
              ('spare6',            Record.Int),
              ('spare7',            Record.Int)]

def LoadRentFile(fp):
    # Crash_load (of sorts -- interprets locate field)
    rent = ReadFile(fp, RentFileInfo, 1)
    model = dict(rent      = list(rent)[0],
                 inventory = []  ,
                 equipment = dict())

    for item in ReadFile(fp, RentedItemData):
        # XXX Put all in inventory
        model['inventory'].append(item)

    return model

# Inspection Front End.
def main(argv = None):
    from optparse import OptionParser
    from os.path import basename, splitext
    parser = OptionParser()

    (options, args) = parser.parse_args(argv)
    for filename in args:
        if basename(filename).lower() == 'plrobjs':
            # Inspect directory (using middle initials)
            pass

        elif splitext(filename)[1].lower() == '.objs':
            model = LoadRentFile(open(filename))
            print(model['rent'])
            print('\n'.join(model['inventory']))

            for (where, item) in model['equipment'].items():
                print('%s: %r' % (where, item))

if __name__ == '__main__':
    main()
