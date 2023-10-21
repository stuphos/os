"""CircleMUD mobile database file interpreter.

Version: %(__version__)f

Class: MobileReader
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

__version__ = 0.1

def usage():return __doc__%{'__version__':__version__}

from .dblib import *

class MobileReader(RecordReader):
    def parseRecord(self):
        """Load record area into logical Python object

        file argument is an open file handle

        Format of textually-defined object mobile:

        #<vnum>
        <Name String (keywords)>~<NL>
        <Short Description>~<NL>
        <Long Room Description (multiline)><NL>
        ~<NL>
        <Description (multiline)><NL>
        ~<NL>
        <ASCII-flag for Mob Bits> <ASCII-flag for Aff Bits> <Alignment> S|E

        Simple Monsters:
        <Level> <Hitroll> <AC> <Hit>d<Mana>+<Move> <DamNoDice>d<DamSizeDice>+<DamRoll>
        <Gold> <Experience>
        <Position> <Default Position> <Gender>

        Circle3 Enhanced Monsters:
        MoveMessage: [0-99]
        BareHandAttack: [0-99]
        Str: [3-25]
        StrAdd: [0-100]
        Int: [3-25]
        Wis: [3-25]
        Dex: [3-25]
        Con: [3-25]
        Cha: [3-25]
        gen_spec_act: <type> <chance> <spell> <self> "<command>"
        SpecProc: <specproc name>
        E
        """

        self.recordField('name', self.tildeString('name'))
        self.recordField('shortdescr', self.tildeString('shortdescr'))
        self.recordField('longdescr', self.tildeString('longdescr'))
        self.recordField('descr', self.tildeString('descr'))

        mobflags, affbits, align, monster_type = self.readLine().split()
        self.recordField('mobflags', ASCIIFlagDecode(mobflags))
        self.recordField('affbits', ASCIIFlagDecode(affbits))
        self.recordField('alignment', align)

        if monster_type in 'SE':
            level, hitroll, ac, hmm, ddd = self.readLine().split()
            self.recordField('level', level)
            self.recordField('hitroll', hitroll)
            self.recordField('armorclass', ac)

            try: hit, mana, move = parseDice(hmm)
            except FormatError as e:
                raise self.error(str(e))

            self.recordField('max_hit', hit)
            self.recordField('max_mana', mana)
            self.recordField('max_move', move)

            try: damnodice, damsizedice, damroll = parseDice(ddd)
            except FormatError as e:
                raise self.error(str(e))

            self.recordField('damnodice', damnodice)
            self.recordField('damsizedice', damsizedice)
            self.recordField('damroll', damroll)

            gold, exp = self.readLine().split()
            self.recordField('gold', gold)
            self.recordField('experience', exp)

            pos, default_pos, gender = self.readLine().split()
            self.recordField('position', pos)
            self.recordField('default_pos', default_pos)
            self.recordField('gender', gender)

        if monster_type == 'E':
            line = self.readLine()
            while line != '':
                code = line.strip()
                if code == '$':
                    # Natural termination of records.
                    return None

                elif code == 'E':
                    # Natural termination of enhanced mobile.
                    break

                colon = line.find(':')
                if colon >= 0:
                    field = line[:colon].strip()
                    value = line[colon+1:]
                    ival = value.strip()
                    if ival.isdigit():
                        value = int(ival)
                else:
                    field = line
                    value = ''

                field = field.lower()

                # Eww.. pollution?
                self.recordField(field, value)

                line = self.readLine()

            if line == '':
                self.EOFNoDollar()

        return self.readNextVnum()
