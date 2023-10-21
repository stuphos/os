# Routines for the StuphMUD Text Library.
from os.path import join as joinpath
from os.path import basename, splitext

def ReadTildeString(fp, area = 'no particular', newline = '\n'):
    '''
    Read lines from file until terminated by "~\n", removing this sequence.
    Return 2-tuple of (text, nr_lines).

    '''

    buffer = []
    append = buffer.append

    nrlines = 0
    while True:
        line = fp.readline()
        nrlines += 1

        if line == '':
            raise EOFError('Area: %s [EOF expecting ~string]' % area)

        # XXX should not strip every line (is this done in C source??)
        line = line.strip()
        tildeNdx = line.find('~')
        last = len(line) - 1

        if tildeNdx > -1:
            if tildeNdx == last and tildeNdx != 0:
                line = line[:-1]
                append(line)

            break

        else:
            append(line)

    # There is a tilde: put it on, break on ~\n
    # Q: What about ending newline?
    buffer = newline.join(buffer)

    return (buffer, nrlines)

def ReadTextFile(fp):
    # like, most found in the "lib/text" directory"
    return fp.read()
ReadMiscFile = ReadTextFile

def ReadFileNumber(fp):
    line = fp.readline()
    if line == '':
        raise EOFError

    return int(line.strip())

def ReadFightMessages(fp, none_value = ''):
    '''
    * Note: all lines between records which start with '*' are comments and
    * are ignored.  Comments can only be between records, not within them.
    *
    * This file is where the damage messages go for offensive spells, and
    * skills such as kick and backstab.  Also, starting with Circle 3.0, these
    * messages are used for failed spells, and weapon messages for misses and
    * death blows.
    *
    * All records must start with 'M' in the first column (for 'Message').
    * The next line must contain the damage number (defined in spells.h),
    * then the messages (one per line):
    *   Death Message (damager, damagee, onlookers)
    *   Miss Message (damager, damagee, onlookers)
    *   Hit message (damager, damagee, onlookers)
    *   God message (damager, damagee, onlookers)
    *
    * All messages must be contained in one line.  They will be sent through
    * act(), meaning that all standard act() codes apply, and each message will
    * automatically be wrapped to 79 columns when they are printed.  '#' can
    * be substituted for a message if none should be printed.  Note however
    * that, unlike the socials file, all twelve lines must be present for each
    * record, regardless of any '#' fields which may be contained in it.
    '''

    linenr = [0] # as cell
    def readMessageLine(fp, message = 'fight'):
        line = fp.readline()
        if line == '':
            raise SyntaxError('Expected %s message (line %d)' % (message, linenr[0]))

        linenr[0] += 1
        if line.strip() == '#':
            return none_value

        # Q: Strip newline?  "All messages must be contained in one line."
        return line

    last_comment = none_value
    while True:
        # Read up to the first part of the message record.
        line = fp.readline()
        if line == '':
            # Expected a terminating '$', but...
            break

        linenr[0] += 1
        line = line.strip()
        if not line:
            continue

        if line[0] == '*':
            last_comment = line[1:].strip()
            continue

        # Beginning of message record.
        if line == '$':
            # The only proper way to terminate the file.
            break

        if line != 'M':
            raise SyntaxError('Expected message marker ("M"), got %r (line %d)' % (line, linenr[0]))

        line = fp.readline()
        if line == '':
            raise SyntaxError('Expected message code (line %d)' % linenr[0])

        start_line = linenr[0]
        linenr[0] += 1
        line = line.strip()
        if not line.isdigit():
            raise SyntaxError('Expected message code, got %r (line %d)' % (line, linenr[0]))

        code = int(line) # id

        # Now read messages.
        yield dict(message_code = code,
                   line_number = start_line,
                   last_comment = last_comment,

                   death = dict(damager = readMessageLine(fp, 'death-damager'),
                                damagee = readMessageLine(fp, 'death-damagee'),
                                onlookers = readMessageLine(fp, 'death-onlookers')),
                   miss = dict(damager = readMessageLine(fp, 'miss-damager'),
                               damagee = readMessageLine(fp, 'miss-damagee'),
                               onlookers = readMessageLine(fp, 'miss-onlookers')),
                   hit = dict(damager = readMessageLine(fp, 'hit-damager'),
                              damagee = readMessageLine(fp, 'hit-damagee'),
                              onlookers = readMessageLine(fp, 'hit-onlookers')),
                   god = dict(damager = readMessageLine(fp, 'god-damager'),
                              damagee = readMessageLine(fp, 'god-damagee'),
                              onlookers = readMessageLine(fp, 'god-onlookers')))

        last_comment = none_value

class FightMessage:
    class MessageSet:
        def __init__(self, kwd):
            self.__dict__.update(kwd)

        def __repr__(self):
            return 'damager = %r\ndamagee = %r\nonlookers = %r' % \
                   (self.damager, self.damagee, self.onlookers)

    def __init__(self, message_code = None, line_number = None, last_comment = None,
                 death = None, miss = None, hit = None, god = None):

        self.message_code = message_code
        self.line_number = line_number
        self.last_comment = last_comment

        self.death = self.MessageSet(death)
        self.miss  = self.MessageSet(miss)
        self.hit   = self.MessageSet(hit)
        self.god   = self.MessageSet(god)

    def __repr__(self):
        return ('%s:\n  code: #%d\n  line: #%d\n  comment: %r\n' + \
                'death: %s\n  miss : %s\n  hit  : %s\n  god  : %s\n') % \
               (self.__class__.__name__, self.message_code,
                self.line_number, self.last_comment,
                self.death, self.miss, self.hit, self.god)

def ReadSocialMessages(fp):
    # Todo: incorporate line-number information into errors
    linenr = [0] # as cell

    def readSocialLine():
        line = fp.readline()
        if line == '':
            raise EOFError

        linenr[0] += 1
        line = line.strip()
        return line

    while True:
        try: line = readSocialLine()
        except EOFError:
            # Expected a terminating '$', but...
            break

        if line == '$':
            # The only proper termination:
            break

        # Todo: interpret and re-raise error info for this operation:
        (social_name, hide, position) = line.split()

        social = dict(social_name = social_name.lower(),
                      hide = hide,
                      position = position,
                      line_number = linenr[0])

        # Todo: explicitly blank out non-specified lines?

        # Start of messages: end with blank line.
        # Pay close attention to the role of '#'
        line = readSocialLine()
        social['char_no_arg'] = line

        line = readSocialLine()
        if line != '#':
            social['others_no_arg'] = line

        line = readSocialLine()
        if line != '#':
            social['char_found'] = line
            line = readSocialLine()
            social['others_found'] = line
            line = readSocialLine()
            social['vict_found'] = line
            line = readSocialLine()
            social['not_found'] = line
            line = readSocialLine()
            social['char_auto'] = line
            line = readSocialLine()
            if line != '#':
                social['others_auto'] = line

        # End of record marker (empty-line)
        line = readSocialLine()
        if line:
            if not social_name:
                raise SyntaxError('Missing end of record near beginning of file')
            else:
                raise SyntaxError('Missing end of record marker near social %r' % social_name)

        yield social

class SocialMessage:
    def __init__(self, social_name = None, hide = None, position = None,
                 line_number = None, char_no_arg = None, others_no_arg = None,
                 char_found = None, others_found = None, vict_found = None,
                 not_found = None, char_auto = None, others_auto = None):

        self.social_name = social_name
        self.hide = hide
        self.position = position
        self.line_number = line_number
        self.char_no_arg = char_no_arg
        self.others_no_arg = others_no_arg
        self.char_found = char_found
        self.others_found = others_found
        self.vict_found = vict_found
        self.not_found = not_found
        self.char_auto = char_auto
        self.others_auto = others_auto

    def __repr__(self):
        return ('%s: %r (%r; %s; line #%d)\n' + \
                '  char_no_arg = %r\n' + \
                '  others_no_arg = %r\n' + \
                '  char_found = %r\n' + \
                '  others_found = %r\n' + \
                '  vict_found = %r\n' + \
                '  not_found = %r\n' + \
                '  char_auto = %r\n' + \
                '  others_auto = %r\n') % \
                (self.__class__.__name__,
                 self.social_name, bool(self.hide), self.position,
                 self.line_number,
                 self.char_no_arg, self.others_no_arg,
                 self.char_found, self.others_found,
                 self.vict_found, self.not_found,
                 self.char_auto, self.others_auto)

def ReadOlcZones(fp):
    linenr = 0
    while True:
        line = fp.readline()
        if line == '':
            # Expected a terminating '$', but...
            break

        line = line.strip()
        linenr += 1
        if line == '$':
            # The only proper termination:
            break

        # Read zone vnum.
        try:
            if not line or line[0] != '#':
                raise ValueError

            vnum = int(line[1:])

        except ValueError:
            raise SyntaxError('Expected #<zone vnum>, got %r (line #%d)' % (line, linenr))

        # Read player idnums.
        idnums = []
        while True:
            line = fp.readline()
            if line == '':
                raise EOFError('Expected list of idnums (line #%d)' % line)

            line = line.strip()
            linenr += 1

            if line == 'S':
                # Normal end of idnums.
                break

            try: idnums.append(int(line))
            except ValueError:
                raise SyntaxError('Expected idnum, got %r (line #%d)' % (line, linenr))

        # Return result.
        yield (vnum, idnums)

def ReadTrustFile(fp):
    linenr = 0
    while True:
        line = fp.readline()
        if line == '':
            # Expected a terminating '$', but...
            break

        line = line.strip()
        linenr += 1
        if line == '$':
            # The only proper termination:
            break

        # Read player idnum.
        try:
            if not line or line[0] != '#':
                raise ValueError

            idnum = int(line[1:])

        except ValueError:
            raise SyntaxError('Expected #<player idnum>, got %r (line #%d)' % (line, linenr))

        # Read command names.
        commands = []
        while True:
            line = fp.readline()
            if line == '':
                raise EOFError('Expected list of command names (line #%d)' % line)

            line = line.strip()
            linenr += 1

            if line == '*':
                # Normal end of commands.
                break

            if not line:
                raise SyntaxError('Expected command name or *, got empty line (line #%d)' % line)

            commands.append(line)

        # Return result.
        yield (idnum, commands)

def ReadMudTime(fp):
    return ReadFileNumber(fp)

def ReadDnsCache(fp):
    linenr = 0
    while True:
        line = fp.readline()
        if line == '':
            # End of Records.
            break

        linenr += 1
        line = line.strip()
        if not line:
            raise SyntaxError('Expected <ip> <hostname>, got empty line (line #%d)' % linenr)

        # Todo: interpret and re-raise error info for this operation:
        (ipaddr, hostname) = line.split()

        # Todo: further process ipaddr x.x.x.x into host-order int value.
        yield (ipaddr, hostname)

def ReadXNames(fp):
    return set([_f for _f in fp if _f])

_misc_files = ['bugs', 'ideas', 'typos']
_text_files = ['background', 'clanhelp', 'credits', 'handbook',
               'immlist', 'imotd', 'info', 'motd', 'news', 'policies',
               'title', 'wizlist']

# Player Files.
_middle_names = ['A-E', 'F-J', 'K-O', 'P-T', 'U-Z', 'ZZZ']
_middle_name_initials = [(ord(m[0]), ord(m[2])) for m in _middle_names[:-1]]

def GetMiddleInitial(name):
    try: i = ord(name[0].upper())
    except IndexError:
        raise ValueError(name)

    for x in range(len(_middle_name_initials)):
        range = _middle_name_initials[x]
        if i >= range[0] and i <= range[1]:
            return _middle_names[x]

    return _middle_names[-1]

ALIAS_SIMPLE	= 0
ALIAS_COMPLEX	= 1

ALIAS_SEP_CHAR	= ';'
ALIAS_VAR_CHAR	= '$'
ALIAS_GLOB_CHAR	= '*'

NUM_TOKENS	    = 9

def ReadPlayerAliases(fp):
    linenr = 0
    try:
        while True:
            (alias, nrlines) = ReadTildeString(fp, area = '')

            linenr += nrlines

            (replacement, nrlines) = ReadTildeString(fp, area = 'alias replacement')
            linenr += nrlines

            line = fp.readline()
            if line == '':
                raise EOFError('Expected alias complexity type (line #%d)' % linenr)

            linenr += 1
            line = line.strip()
            try: complex = int(line)
            except ValueError:
                raise SyntaxError('Expected alias complexity type, got %r (line #%d)' % (line, linenr))

            yield dict(alias       = alias,
                       replacement = replacement,
                       type        = complex)
    except EOFError:
        # Normal end of records.
        pass

class Alias:
    def __init__(self, alias = None, replacement = None, type = None):
        self.alias       = alias
        self.replacement = replacement
        self.type        = type

    def IsComplex(self):
        return self.type == ALIAS_COMPLEX

    def __repr__(self):
        return '%s%s: %s => %r' % (self.__class__.__name__,
                                   self.IsComplex() and ' (Complex)' or '',
                                   self.alias, self.replacement)

# Order in file:
_player_strings = ('title', 'prename', 'wizname',
                   'poofin', 'poofout',
                   'description', 'plan')

def ReadPlayerStrings(fp):
    # ignoring line number information
    return dict((name, ReadTildeString(fp, 'player ' + name)[0]) \
                for name in _player_strings)

class PlayerStrings:
    def __init__(self, title = None, prename = None, wizname = None,
                 poofin = None, poofout = None, description = None, plan = None):

        self.title       = title
        self.prename     = prename
        self.wizname     = wizname
        self.poofin      = poofin
        self.poofout     = poofout
        self.description = description
        self.plan        = plan

    def __repr__(self):
        return 'Strings:\n  %s' % \
               '\n  '.join('%s = %r' % (name, getattr(self, name)) \
                           for name in _player_strings)

# Mail.
def ReadMail(fp):
    # Todo: parse header info?  Use rfc822.Message?
    try:
        while True:
            (message, nrlines) = ReadTildeString(fp, 'player mail message')
            yield message

    except EOFError:
        # Normal end of records.
        pass

def ReadVerifiedMail(directory, name, middle = None):
    # Pass lib/plrmail directory and player name.
    name = name.lower()
    if middle is False:
        filebase = joinpath(directory, name)
    else:
        if middle is None:
            middle = GetMiddleInitial(name)

        filebase = joinpath(directory, middle, name)

    # Verify number of messages
    count = ReadFileNumber(open('%s.count' % filebase))
    mail = ReadMail(open('%s.mail' % filebase))
    mail = list(mail)

    if len(mail) != count:
        # XXX: Yes, there's a format error, but could we just truncate the
        # rest?  Or just pass the count to the ReadMail subroutine to limit?
        raise ValueError('Expected %d messages, got %d' % (count, len(mail)))

    return mail

# Inspection Front End.
def _get_interpreters():
    def KwdObjectList(array, objectClass):
        return [objectClass(**kwd) for kwd in array]

    interpreters = {'messages' : (ReadFightMessages,
                                 lambda kwd: KwdObjectList(kwd, FightMessage)),
                    'socials'  : (ReadSocialMessages,
                                 lambda kwd: KwdObjectList(kwd, SocialMessage)),

                    'olczones' : (ReadOlcZones , dict),
                    'trust'    : (ReadTrustFile, dict),
                    'time'     : (ReadMudTime  , int ),
                    'dns.cache': (ReadDnsCache , dict),

                    # Extensions.
                    '.alias'   : (ReadPlayerAliases,
                                  lambda kwd: KwdObjectList(kwd, PlayerAlias)),
                    '.strings' : (ReadPlayerStrings,
                                  lambda kwd: PlayerStrings(**kwd)),

                    # Directories.
                    'plralias'  : (lambda *args, **kwd: [],
                                   lambda n: None),
                    'plrstrings': (lambda *args, **kwd: [],
                                   lambda n: None),
                    'plrmail'   : (lambda *args, **kwd: [],
                                   lambda n: None)}

    for filename in _misc_files:
        interpreters[filename] = (ReadTextFile, str)
    for filename in _text_files:
        interpreters[filename] = (ReadTextFile, str)

    return interpreters

def _lookup_interpreter(interpreters, filename):
    filename = basename(filename).lower()
    try: return interpreters[filename]
    except KeyError:
        ext = (splitext(filename)[1] or '').lower()
        return interpreters.get(ext)

def main(argv = None):
    from optparse import OptionParser
    from code import InteractiveConsole as IC
    from types import InstanceType
    from pdb import runcall
    import readline

    try: from simplejson import dump
    except ImportError:
        from pprint import pprint as output
    else:
        from sys import stdout
        def output(record):
            dump(record, stdout, indent = 2)
            print(',', file=stdout)

    parser = OptionParser()
    parser.add_option('-i', '--inspect', action = 'store_true')
    (options, args) = parser.parse_args(argv)

    # Build these.
    interpreters = _get_interpreters()

    for filename in args:
        i = _lookup_interpreter(interpreters, filename)
        if i is not None:
            (loader, internalize) = i
            object = loader(open(filename))
            object = internalize(object)

            if options.inspect:
                object_name = basename(filename).replace('.', '_')
                IC(locals = {object_name: object}).interact(banner = '')
            elif type(object) is InstanceType:
                print(object)
            else:
                # Todo: control formatted output options.
                output(object)

if __name__ == '__main__':
    main()
