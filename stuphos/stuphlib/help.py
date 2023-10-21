from stuphlib.textlib import ReadTildeString

def ReadHelpFile(fp):
    # Hash Mark (#) - separated records with tilde-strings:
    #   suggests use of FileReader, but without vnum syntax...
    linenr = 0
    while True:
        line = fp.readline()
        if line == '':
            # Expected a terminating '$', but...
            break

        linenr += 1
        line = line.strip()

        if line == '$':
            # Normal terminator.
            break

        if line != '#':
            # Just an empty hash mark for count_hash_records
            raise SyntaxError('Expected hash mark (#) or terminator ($), got empty line (line #%d)' % linenr)

        # Read help entry.
        keywords = fp.readline()
        if keywords == '':
            raise EOFError('Expected keywords (line #%d)' % (linenr))

        linenr += 1
        keywords = keywords.strip()
        if not keywords:
            raise SyntaxError('Expected keywords, not empty line (line #%d)' % linenr)

        minlevel = fp.readline()
        if keywords == '':
            raise EOFError('Expected minlevel (line #%d)' % (linenr))

        linenr += 1
        minlevel = minlevel.strip()
        try: minlevel = int(minlevel)
        except ValueError:
            raise SyntaxError('Expected minlevel, not %r (line #%d)' % (minlevel, linenr))

        (text, nrlines) = ReadTildeString(fp)
        linenr += nrlines

        yield dict(keywords = keywords,
                   minlevel = minlevel,
                   text = text)

def LoadHelpFile(fp):
    records = dict()
    for help_entry in ReadHelpFile(fp):
        keywords = help_entry.pop('keywords')
        records[keywords] = help_entry

    return records

def ReadHelpScreen(fp):
    return fl.read()

# Indexing.
from stuphlib.dblib import LocalIndex, INDEX_FILE

class HelpIndex:
    def iterindex(self, index):
        for n in self.open(index):
            n = n.strip()
            if n == '$':
                break

            yield n.strip()

    def openHelpFile(self, helpfile):
        return self.open(helpfile)

class HelpLocalIndex(HelpIndex, LocalIndex):
    pass

def LoadHelpIndex(help_base, index_file = None):
    index = HelpLocalIndex(help_base)
    if index_file is None:
        index_file = INDEX_FILE

    help_table = dict()
    for helpfile in index.iterindex(index_file):
        # By help savefile.
        help_table[helpfile] = LoadHelpFile(index.openHelpFile(helpfile))

    return help_table

# Inspection Front End.
def main(argv = None):
    from sys import argv
    if len(argv) == 2:
        help_table = LoadHelpIndex(argv[1])

        from code import InteractiveConsole as IC
        import readline

        IC(locals = dict(help_table = help_table)).interact(banner = '')

if __name__ == '__main__':
    main()
