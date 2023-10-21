"""
Implement an interpreter-based OLC, which loads a syslog (by virtual FS) as an input source,
subjecting each line to a match against a pattern database, which matches and processes messages
based on their format.  The menu-based editor is used to process lines against existing templates,
and to allow provision of new templates for processed lines.

Process lines come from streamed sources: they can be from a file, possibly a re-scan of the entire
syslog, or, as a branched processing intercept from the mudlog programmable bridge event.  The editor
can then be used to edit a certain new batch of incoming lines that have not been matched yet.

The matched lines database associates with handlers that are called in the final target processing
of ongoing mudlog events.  It is the responsibility of the scheduler executing these handlers towards
unifying them within the mud whole.

---
Implementation:
        
"""

from stuphos.etc.tools.strings import compactify, safeAttr, isYesValue
from stuphos.runtime.architecture.api import NoAccessException

import re, errno, pickle, traceback,pprint
from os import popen

try: import readline as rl
except ImportError: rl = None

# Generic serializable pattern construct.
class pattern:
    def __init__(self, pattern):
        self.pattern = pattern

    def __getstate__(self):
        return self.pattern

    def __setstate__(self, pattern):
        self.pattern = pattern

    def __str__(self):
        return str(self.pattern)

    __reduce__ = __str__

class compile_pattern(pattern):
    'Implements regular-expression match.'
    TYPE = 'compiled'

    def __init__(self, pattern):
        self.pattern = pattern
        # self._compiled = re.compile(pattern)
        self.match = re.compile(pattern).match

    __setstate__ = __init__

class static_pattern(pattern):
    'Implements a simple equality match.'
    TYPE = 'static'

    def match(self, line):
        return line == self.pattern


logfile_timefmt_header = 'mon day 24h:m:s year     :: '

class PatternMatch:
    'Serializable database pattern-matching algorithm.'

    patternCollection = list # set

    def __init__(self, patterns = None):
        self.patterns = self.patternCollection(patterns) \
                            if patterns else self.patternCollection()
        self.lineno = 0
        self.processMatch = None

    def __getstate__(self):
        return (self.patterns, self.lineno)

    def __setstate__(self, state):
        (patterns, lineno) = state

        self.patterns = self.patternCollection(patterns)
        self.lineno = lineno

    # The algorithm, with callbacks:
    def matchlines(self, source):
        'Scan iteratable line source and generate full-stage pattern recognition processing.'

        for line in self.iterateLines(source):
            self.startMatch(line)

            result = False
            for pat in self.patterns:
                match = pat.match(line)
                if match:
                    result = True
                    yield (match, pat, line, self.lineno)

            if not result:
                yield (None, None, line, self.lineno)

            self.endMatch(line)

    def iterateLines(self, source):
        for line in source:
            self.lineno += 1

            # yield line
            # self.timestamp = strptime(logfile_timefmt_header, line[:28])
            self.timestamp = line[:28]
            yield line[28:]

    def startMatch(self, source):
        pass

    def endMatch(self, source):
        pass

    def addPattern(self, pattern):
        s = self.patterns
        if type(s) is list and pattern not in s:
            s.append(pattern)
        elif type(s) is set:
            s.add(pattern)

    def getPattern(self, index):
        return self.patterns[index] if type(self.patterns) is list else None

    def setPattern(self, index, pattern):
        if type(self.patterns) is list:
            self.patterns[index] = pattern

    __getitem__ = getPattern
    __setitem__ = setPattern

class InteractiveMatch(PatternMatch):
    'Interactive pattern match shell used for editing the syslog templates.'
    # High-level interface for pattern-matching database.

    def noMatch(self, line, lineno):
        'Interactive prompt when no match is found for a line.'

        while 1:
            resp = self.doPrompt(line).strip()
            if resp == '':
                break

            lresp = resp.lower()

            if resp == '=':
                # Add a static pattern for this line.
                self.addPattern(static_pattern(line))
                print('Static Pattern added for:\n  %r' % line)
                break

            elif lresp in ('-h', '-he', '-hel', '-help', '--h', '--he', '--hel', '--help'):
                self.doHelp(lresp)

            elif lresp in ('-s', '-sh', '-sho', '-show', '--s', '--sh', '--sho', '--show'):
                self.doShow(lresp)

            elif lresp in ('-sa', '-sav', '-save', '--sa', '--sav', '--save'):
                self.save()
                n = len(self.patterns)
                print('%d pattern%s saved.' % (n, 's' if n != 1 else ''))

            elif '-populate'.startswith(lresp):
                self.populatePatternHistory()

            elif '-replace'.startswith(lresp):
                pass
            elif '-up'.startswith(lresp):
                pass
            elif '-down'.startswith(lresp):
                pass
            elif '-back'.startswith(lresp):
                pass
            elif '-forward'.startswith(lresp):
                pass
            elif '-select'.startswith(lresp):
                pass

            else:
                try:
                    pat = compile_pattern(resp)
                except:
                    traceback.print_exc()
                    continue

                if not pat.match(line):
                    print('line does not match:', resp)
                    print('  ', line)
                else:
                    self.addPattern(pat)
                    break

    def doPrompt(self, line):
        return input('Provide a template match for:\n   %r\n? ' % line)

    def doHelp(self, command):
        self.page(re.__doc__)

    def doShow(self, command):
        s = self.patterns

        if type(s) is list:
            from io import StringIO
            b = StringIO()

            for x in range(len(s)):
                print('#%3d :' % x, str(s[x]).rstrip(), file=b)

            self.page(b.getvalue())
        else:
            self.page('\r\n'.join(str(pat).rstrip() for pat in s))

    def page(self, msg, columnize = False):
        popen('less' if not columnize else 'column|less', 'w').write(msg)

    def populatePatternHistory(self):
        s = self.patterns
        if type(s) is list:
            x = len(s)
            def get(i):
                return str(s[i]).rstrip()

            n = rl.get_current_history_length()
            if n > x:
                n = x

            for i in range(n):
                rl.replace_history_item(i, get(i))

            if x > n:
                for i in range(n, x):
                    rl.add_history(get(i))

    def interactive(self, source = None, notifyMatch = None):
        if source is None:
            source = getattr(self, 'source', None)

        assert source
        self.source = source
        if not notifyMatch:
            notifyMatch = getattr(self, 'notifyMatch', None)

        try:
            for (match, pat, line, lineno) in self.matchlines(source):
                if match:
                    notifyMatch(match, pat, line, lineno)
                else:
                    self.noMatch(line, lineno)

        except EOFError:
            pass

    resume = interactive

    def notifyMatch(self, match, pattern, line, lineno):
        if hasattr(pattern, 'handleMatch'):
            return pattern.handleMatch(match, line, lineno)

        print('Found (line #%d): %r' % (lineno, line))
        if type(match) is not type(True):
            print('  ', str(pattern).rstrip())
            print('  ', ', '.join([_f for _f in match.groups() if _f]))

            gd = match.groupdict()
            if gd:
                pprint.pprint(gd)

    def save(self, file = None):
        pickle.dump(self, open(str(file or self.templates_file), 'w'))

    def export(self, filename):
        out = open(filename, 'wt')
        type = None
        nr = 0

        for pattern in self.patterns:
            if type != pattern.TYPE:
                type = pattern.TYPE
                if type is not None:
                    print(file=out)

                print('[%s]' % type.capitalize(), file=out)

            # XXX :skip: careful:
            pattern = str(pattern).rstrip()

            print('%d: %s'  % (nr, pattern), file=out)
            nr += 1

        out.flush()
        out.close()

def loadPatternMatcher(templates_file):
    patternMatcher = InteractiveMatch
    try:
        if templates_file.endswith('.pkl'):
            # Deserialize.
            patmatch = pickle.load(open(templates_file))
        else:
            # Load templates from regular file -- constructing regexprs.
            patmatch = patternMatcher(compile_pattern(pattern) for pattern in open(templates_file))

        patmatch.templates_file = templates_file

    # Else default.
    except:
        from sys import exc_info
        (etype, value, tb) = exc_info()
        print('[syslog pattern loader] %s: %s' % (etype.__name__, value))

        patmatch = patternMatcher()
        patmatch.templates_file = templates_file

    return patmatch

def loadProcessor(name):
    if name:
        name = name.split('.')
        if len(name) == 1:
            return globals().get(name[0])

        try: module = __import__('.'.join(name[:-1]), globals(), locals(), [''])
        except ImportError: pass
        else: return getattr(module, name[-1], None)

def ignoreMatch(*args):
    pass

## Scripted Main.
DEFAULT_PATTERNS = 'stuph-log-patterns.pkl'

def main(argv = None):
    # Parse command line.
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('--database', '--db')
    parser.add_option('-g', '--debug', action = 'store_true')
    parser.add_option('-i', '--input-file', '--source')
    parser.add_option('-s', '--show-patterns', action = 'store_true')
    parser.add_option('-p', '--processor')
    parser.add_option('-x', '--export')
    parser.add_option('--import')
    (options, args) = parser.parse_args()

    if options.input_file:
        source = open(options.input_file)
    elif args:
        assert len(args) == 1
        source = open(args[0])

    templates_file = options.database or DEFAULT_PATTERNS

    if options.debug:
        from pdb import set_trace
        set_trace()

    # Load the pattern matcher.
    patmatch = loadPatternMatcher(templates_file)
    if options.export:
        patmatch.export(options.export)
    else:
        processMatch = loadProcessor(options.processor)

        # Interact.
        if options.show_patterns:
            for pattern in patmatch.patterns:
                print(pattern.pattern)
        else:
            patmatch.interactive(source, processMatch)

if __name__ == '__main__':
    main()

USAGE = \
'''
This subcommand will compare a collection of syslogs against a category
of patterns (use --show=all or --show=static|compiled to get a list of
categories).

Use --show-paths to see a list of paths that the scanner searches, and
--category=<category seen with --show> to do the actual search.
'''

from optparse import OptionParser
syslogCommandParser = OptionParser(USAGE)
syslogCommandParser.add_option('-c', '--category')
syslogCommandParser.add_option('-s', '--show-categories', '--show')
syslogCommandParser.add_option('--show-paths', action = 'store_true')

def parseScanSyslogCmdln(args):
    from ..etc import parseOptionsOverSystem
    return parseOptionsOverSystem(syslogCommandParser, args)

def getScanSyslogPaths(section):
    from glob import glob

    import re
    pathpat = re.compile('path(?:\.(\d+))?').match

    for opt in section.options():
        if pathpat(opt):
            for p in glob(section.get(opt)):
                yield p

class Instruction:
    def __init__(self, command):
        self.command = command

    context = []

    class Context(list):
        def __init__(self, name):
            self.name = name

    @classmethod
    def isState(self, line):
        if line:
            if line[0] == '[' and line[-1] == ']':
                line = line[1:-1].strip()
                i = line.find(' ')
                if i >= 0:
                    state = line[i:]

                state = line.lstrip()

                if state.lower() == 'state:':
                    line = line[len(state):].lstrip()
                    if line[0] == '@':
                        def i():
                            yield self(line[1:])

                        # Return a non-None generator on state match.
                        return i()

    def processState(self, buffer):
        args = self.command.split()
        cmd = args[0]

        if cmd == 'open':
            self.context.append(self.Context(' '.join(args[1:])))

        elif cmd == 'close':
            try: 
                for match in buffer:
                    yield '  ' * len(self.context) + match

            finally:
                del buffer[:]
                self.context.pop()

    def endState(self):
        # Stream the buffer.
        for match in self:
            yield match


    @classmethod
    def build(self, scan):
        # Process state indentation.
        self.context.append(self.Context(''))

        for match in scan(self.isState):
            if isinstance(match, self):
                for match in match.processState(self.context[-1]):
                    yield match
            else:
                self.context[-1].append(match)

        # Unwind any unclosed states.
        for ctx in range(len(self.context)):
            for match in self.context[ctx].endState():
                yield match


# These should be: complex and basic
KNOWN_PATTERN_TYPES = ['Compiled', 'Static']
MINIMUM_LEVEL = 115
def doScanSyslog(peer, cmd, argstr):
    # todo: caching of patterns object, syslogs (pre-match index)
    # to disk.. reloaded via md5 checksum change detection.
    args = argstr.split() if argstr else []
    if not args or args[0].lower() != 'scan':
        return False

    del args[0]
    if peer.avatar and peer.avatar.level >= MINIMUM_LEVEL:
        try:
            (options, args) = parseScanSyslogCmdln(args)

            from stuphmud.server import getSection
            section = getSection('Syslog')

            syslog_paths = getScanSyslogPaths(section)
            patterns = section.get('patterns')

            if options.show_paths:
                def showPaths():
                    yield '&ySyslog Paths:&N'
                    yield '============='
                    yield ''

                    for path in syslog_paths:
                        yield path

                peer.page_string('\n'.join(showPaths()) + '\n')
                raise SystemExit

            if not patterns:
                print('Not syslog patterns defined!', file=peer)
                raise SystemExit

            # Load appropriate pattern category:
            # todo: actually provide categorical combinations.
            from configparser import ConfigParser, NoOptionError, NoSectionError
            cfg = ConfigParser()
            cfg.readfp(open(patterns), patterns)

            show = options.show_categories
            if show:
                # todo: wildcard--search patterns themselves!
                show = show.lower()

                def showSections():
                    yield '&ySyslog Categories:&N'
                    yield '=================='
                    yield ''

                    for section in cfg.sections():
                        if section not in KNOWN_PATTERN_TYPES:
                            continue

                        lsection = section.lower()
                        if show in ['any', 'all'] or show == lsection:
                            yield str(section)
                            for opt in cfg.options(section):
                                yield '  [%-5s] %s' % (opt, cfg.get(section, opt))

                            yield ''

                peer.page_string('\n'.join(showSections()) + '\n')
                raise SystemExit

            if not options.category:
                print('Category is required.', file=peer)
                print(file=peer)

                parseScanSyslogCmdln(['-h'])
                raise SystemExit

            # Check aliases, first:
            category_id = options.category
            try: category_id = cfg.get('Aliases', category_id)
            except (NoOptionError, NoSectionError): pass

            for type in KNOWN_PATTERN_TYPES:
                try: pattern = cfg.get(type, category_id)
                except (NoOptionError, NoSectionError): pass
                else:
                    if type == 'Compiled':
                        category = compile_pattern(pattern)
                    elif type == 'Static':
                        category = static_pattern(pattern)

                    # Get presentation format.
                    try: category_header = cfg.get('Presentation', '%s.header' % category_id, raw = True)
                    except (NoOptionError, NoSectionError): category_header = None

                    try: category_format = cfg.get('Presentation', '%s.format' % category_id, raw = True)
                    except (NoOptionError, NoSectionError): category_format = None

                    break
            else:
                print('Unknown category: %r' % category_id, file=peer)
                raise SystemExit

            # Do processing.
            def scanSyslog(isState):
                yield '&ySyslog Contents:&N'
                yield '================'
                yield str(category)
                yield ''

                for path in syslog_paths:
                    try: stream = open(path)
                    except IOError:
                        # todo: test for non (is-directory or enoent)
                        continue

                    first_in_file = True
                    linenr = 0
                    for line in stream:
                        linenr += 1

                        # XXX :skip: Careful:
                        line = line.rstrip()
                        line = line[28:]

                        match = isState(line)
                        if match is not None:
                            # Process state.
                            for match in match:
                                yield match

                            # Move to next incoming stream line.
                            continue

                        match = category.match(line)

                        if match is True:
                            if first_in_file:
                                yield '%s:' % path
                                first_in_file = False

                            yield '  %-5d: %s' % (linenr, line)

                        elif match not in (False, None):
                            if first_in_file:
                                yield '%s:' % path
                                if category_header:
                                    yield '         %s' % category_header
                                    yield '         %s' % ('-' * len(category_header))

                                first_in_file = False

                            groups = match.groupdict()
                            if not groups:
                                groups = match.groups()

                            if category_format:
                                yield '  %-5d: %s' % (linenr, category_format % groups)
                            else:
                                yield '  %-5d: %s' % (linenr, groups)

                    if not first_in_file:
                        yield ''

            # In another thread (how might this affection the active syslog??)
            def process(page_string):
                from stuphos import enqueueHeartbeatTask
                enqueueHeartbeatTask(page_string, '\r\n'.join(Instruction.build(scanSyslog)))

            from _thread import start_new_thread as nth
            nth(process, (peer.page_string,))

        except SystemExit:
            pass

        return True

try: from stuphmud.server.player import ACMD
except ImportError: pass
else: ACMD('syslog*')(doScanSyslog)


from stuphos.runtime.facilities import Facility
from stuphos.db import dbCore
from stuphos.kernel import Native
from stuphos.etc.tools.timing import date as now
from stuphos.etc.tools.logs import tracebackString, exceptionHeader
from stuphos import getConfig

from queue import Queue
from datetime import datetime
from time import time as now

class Journal(Facility):
    NAME = 'System::Journal'

    def __init__(self):
         # [mud/runtime/core.py:225] installServices
         #   Logging.get(create = True)

        # self.taskWaiters = dict()
        self.dbNamespace = getConfig('database', 'Logging')

        self.queue = Queue()

        if self.init() is not False:
            self.startStream()

    def init(self):
        if self.dbNamespace is None:
            return False

        from stuphos.db.orm import Log, createSQLObjectTable
        from stuphos.db import dbCore

        with dbCore.hubThread(self.dbNamespace):
            createSQLObjectTable(Log)


    def processStream(self, write, get):
        # print(f'[vsz] starting stream: {psOpGameVsz()}')
        self.running = True
        try:
            while True:
                job = None
                try:
                    # print(f'[vsz] getting journal job: {psOpGameVsz()}')
                    job = get()
                    write(job)

                except StopIteration:
                    break

                except Exception as e:
                    if job is not None:
                        import json

                        from sys import exc_info
                        (etype, value, tb) = exc_info()

                        try: print(json.dumps(job, indent = 1))
                        except Exception as r:
                            print('reporting job data [%s]: %s' % (r.__class__.__name__, r))
                            print('...%s.%s: %s' % (e.__class__.__module__, e.__class__.__name__, e))

                            from traceback import print_exception
                            print(job)
                            print_exception(etype, value, tb)

                            continue

                    from stuphos import logException
                    logException(traceback = True)
        finally:
            self.running = False

    def startStream(self):
        from stuphos.etc import nth
        nth(self.processStream, self.writeLogTraceback,
            self.queue.get)

    def stopStream(self):
        self.queue.put(StopIteration)

    def __registry_delete__(self):
        self.stopStream()

    def logTraceback(self, task, traceback, exception = None):
        # try: waiter = self.taskWaiters[task.taskName]
        # except KeyError:
        #     pass
        # else:
        #     # Just dispatch the log (don't store)
        #     return waiter(self, task, traceback)

        self.logTracebackDB(task, traceback, exception = exception)

    def writeLogTraceback(self, msg):
        if isinstance(msg, StopIteration) or msg is StopIteration:
            raise msg

        # return # XXX :skip: absorb all until we can migrate Log

        if isinstance(msg, dict):
            source = msg['source']
            type = msg['type']
            content = msg['content']
            timestamp = msg['timestamp']
        else:
            (source, type, content, timestamp) = msg

        from stuphos.db.orm import Log
        from stuphos.db import dbCore

        # print(f'[vsz] writing log: {psOpGameVsz()}')

        with dbCore.hubThread(self.dbNamespace):
            try: Log(source = source, type = type,
                     content = content,
                     timestamp = timestamp).sync()

            except sqlite.module.dberrors.OperationalError as e:
                # Contention?
                logOperation(f'Log ERROR [{self.dbNamespace}]: {e.__class__.__name__}: {e}')

            except ImportError as e:
                # Yep.
                import re
                pattern = re.compile(r'^Failed to import ([_a-zA-Z0-9]+) because the import lock is held by another thread.$').match
                if pattern(str(e)) is not None:
                    # Because this is intermittant, we debug it...
                    print(e)

                    if isYesValue(configuration.Logging.debug_import_lock_error):
                        debugOn() # :production-breakpoint:
                else:
                    raise e

        # print(f'[vsz] wrote log: {psOpGameVsz()}')

    def copyToDB(self, fromNS, toNS):
        from stuphos.db.orm import Log
        from stuphos.db import dbCore

        with dbCore.hubThread(fromNS):
            # Copy to memory.
            data = [(e.source, e.type, e.content, e.timestamp)
                    for e in Log.select()]

        with dbCore.hubThread(toNS):
            try: Log.createTable()
            except Exception as e:
                print(f'{toNS}: {e}')

            for (source, type, content, timestamp) in data:
                # Write to database.
                Log(source = source, type = type,
                    content = content,
                    timestamp = timestamp).sync()

        return len(data)


    def __add__(self, msg):
        self.queue.put(msg)
        return self
    __iadd__ = __add__

    def logTracebackDB(self, task, traceback, exception = None):
        traceback = '\n'.join(task.formatTraceback(traceback))
        if exception is not None:
            (etype, value, tb) = exception
            try: header = exceptionHeader(etype, value)
            except NoAccessException:
                try: header = f'{etype.__name__}: {repr(value)}'
                except NoAccessException:
                    header = f'{etype.__name__}: id #{id(value)}'

            traceback += '\n%s:\n%s\n' % (header, tracebackString(tb))

        self += (task.name, 'traceback', traceback,
                 datetime.fromtimestamp(now()))

    # todo: differentiate between logs: traceback, other?
    def getLogs(self, task = None, n = -1, taskName = None, preserve = False, type = 'traceback'):
        from stuphos.db.orm import Log
        from stuphos.db import dbCore

        if task is None:
            assert taskName
        else:
            taskName = task.taskName

        assert n
        with dbCore.hubThread(self.dbNamespace):
            for log in Log.selectBy(source = taskName, type = type) \
                .orderBy('timestamp'):
                if n > 0:
                    n -= 1

                tb = log.content
                when = log.timestamp

                if not preserve:
                    log.delete()

                yield tb # , when

                if not n:
                    break

    def iterate(self, **criteria):
        from stuphos.db.orm import Log
        from stuphos.db import dbCore

        with dbCore.hubThread(self.dbNamespace):
            return iter(Log.selectBy(**criteria).orderBy('timestamp'))
    __iter__ = iterate

    def deleteAllType(self, type):
        with dbCore.hubThread(self.dbNamespace):
            for e in self.iterate(type = type):
                e.delete(e.id)

    # def waitLogs(self, task, waiter, once = False):
    #     # todo: if already available, call waiter.
    #     # todo: decorator form
    #     self.taskWaiters[task.taskName] = waiter

    def systemLog(self, task, traceback):
        from stuphos.system.api import syslog
        for line in task.formatTraceback(traceback):
            syslog(line)

    @classmethod
    def iterateTracebackData(self, traceback):
        # Compatibility with raise$()d tracebacks that use $stack.
        if traceback is not None:
            try: from ph.emulation.machine.kernel import TracebackFrame, Traceback
            except ImportError:
                Traceback = TracebackFrame = type(None)

            if isinstance(traceback, Traceback):
                # Hide the entire traceback.
                traceback = traceback._iterate()

            for frameTb in traceback:
                if frameTb is None:
                    continue

                if isinstance(frameTb, TracebackFrame):
                    yield (frameTb._frame, frameTb._pos)
                else:
                    yield frameTb


    @staticmethod
    def _formatSource(source):
        if isinstance(source, list): # todo: or tuple?
            source = '/'.join(source)

        return compactify(source, 80).replace('\n', ' ')

    @staticmethod
    def _sourceLinkAttr(source):
        if isinstance(source, list):
            return (safeAttr('/'.join(source[:-1])), safeAttr(source[-1]))

        return safeAttr(str(source))

    @classmethod
    def buildHasAccess(self, kwd):
        # Build security routines with parameter.
        try: checkAccess = kwd['checkAccess']
        except KeyError:
            def hasAccess(source, frame):
                return True
        else:
            agentCore = runtime[runtime.Agent.System]
            if not agentCore:
                def hasAccess(source, frame):
                    return True
            else:
                def hasAccess(source, frame):
                    if isinstance(source, str):
                        if kwd.get('hide_string_sources'):
                            return

                        # return isYesValue(configuration.Interpreter.reveal_all_string_sources)

                        try: source = frame.locals['path$']
                        except KeyError:
                            try: source = frame.procedure.environ['path$']
                            except (TypeError, AttributeError, KeyError):
                                # The TypeError is for None environs.
                                return # Fail access.


                    # checkAccess (as principal) may be None.
                    source = list(source)
                    # source.append('traceback')

                    return agentCore.principalHasAccess \
                        (checkAccess, source, 'read')

        return hasAccess


    @classmethod
    def formatTraceback(self, traceback, **kwd):
        hasAccess = self.buildHasAccess(kwd)

        for (f, pos) in self.iterateTracebackData(traceback):
            p = f.procedure

            if getattr(p, '_omitTraceback', False):
                continue

            # print(pos, p)

            # Todo: get source code line number from position-to-linenr table,
            # or, yield the Program disassembly of the instruction to string.
            # Note: treating position as if it's the next pc to execute.

            if isinstance(p, Native): # Or SubNative
                # XXX
                try: nft = p._formatTraceback
                except:
                    try: name = p._native.__name__
                    except: pass # Could be a NoAccessException if the native is an Instance.
                    else: yield '  %s:' % (name,)
                else:
                    yield nft()

                continue

            try: name = p.name
            except AttributeError:
                name = ''
            else:
                name = f'{name or ""}{name and ":" or ""}'


            # debugOn() # :traceback:
            try: source = p.lineSourceInfo(pos-1)
            except AttributeError:
                source = None

            if source is not None:
                (lnr, source, code) = source
                if hasAccess(source, f):
                    # Todo: get rid of '*' for production.  Todo: debug why hasAccess
                    # succeeds here but fails for Html-gen variant below.
                    yield f'[{self._formatSource(source)}:{lnr} ({name}{pos}*)]'

                    if code:
                        yield '  %s' % code.lstrip() # Assume no one's pumping ws at end.

                else:
                    yield '<hidden> (?)'

            else:
                try: source = p.getSourceMap().source
                except AttributeError: source = None

                if source:
                    yield f'[{self._formatSource(source)} ({name}{pos})]'

                try: (start, g) = p.lineGroup(pos)
                except (TypeError, AttributeError):
                    # No line source info found -- render one instruction string.
                    try: s = p.instructionsString(pos-1, pos, suppress_name = True)
                    except AttributeError:
                        s = '<unknown procedure>'
                else:
                    span = 1 # len(g) # XXX :skip: 20 instructions per line??
                    if pos >= start and pos <= (start + span):
                        s = p.instructionsString(start, start + span,
                                                 suppress_name = True,
                                                 highlight = pos)
                    else:
                        # Why lineGroup isn't returning pos-containing span?
                        s = p.instructionsString(pos-1, pos, suppress_name = True)

                n = getattr(p, 'name', None)
                if n:
                    yield f'  {n}'

                yield indent(s.strip())


    # XXX Duplicate code:
    # Todo: rename to formatTracebackContext
    @classmethod
    def formatTracebackHtml(self, traceback, **kwd):
        hasAccess = self.buildHasAccess(kwd)

        for (f, pos) in self.iterateTracebackData(traceback):
            p = f.procedure

            if getattr(p, '_omitTraceback', False):
                continue

            # print(pos, p)

            # Todo: get source code line number from position-to-linenr table,
            # or, yield the Program disassembly of the instruction to string.
            # Note: treating position as if it's the next pc to execute.

            if isinstance(p, Native): # Or SubNative
                # XXX Todo: what about access check?
                try: name = p._native.__name__
                except: pass # Could be a NoAccessException if the native is an Instance.
                else:
                    # XXX Should be yielding a dict?
                    # Todo: extract line number from association.
                    yield dict(name = name, native = True)
                    # yield '  %s:' % (name,)

                continue

            try: name = p.name
            except AttributeError:
                name = ''
            else:
                name = f'{name or ""}{name and ":" or ""}'


            # todo debug this:
            # services = library('assets/Itham/compon...) \ ('arg1', 'arg2', 'arg3') (9:47) edit
            #         ('arg1', 'arg2', 'arg3')
            # ['assets', 'Itham', 'components', 'encapsule', 'system'] (:) edit
            #     <unknown procedure>

            # debugOn() # :traceback:
            try: source = p.lineSourceInfo(pos-1)
            except AttributeError:
                source = None

            if source is not None:
                (lnr, source, code) = source
                if hasAccess(source, f):
                    r = dict(sourceFormatted = self._formatSource(source),
                             source = source, lineNr = lnr, name = name,
                             sourceAttr = self._sourceLinkAttr(source),
                             nameAttr = safeAttr(str(name)),
                             position = pos)

                    if code:
                        r['code'] = code

                    # print(f'[lineSourceInfo available, has access] {r}')
                    # r['debug_origin'] = 'lineSourceInfo available, has access'

                    yield r

                else:
                    name = '?'
                    r = dict(name = name, nameAttr = safeAttr(str(name)),
                               source = '<hidden>', sourceAttr = '<hidden>',
                               sourceFormatted = '<hidden>', hidden = True)
                    # print(f'[lineSourceInfo available, no access] {r}')
                    # r['debug_origin'] = 'lineSourceInfo available, no access'
                    yield r

                    # Use this one (when not debugging):
                    # yield dict(name = name, nameAttr = safeAttr(str(name)),
                    #            source = '<hidden>', sourceAttr = '<hidden>',
                    #            sourceFormatted = '<hidden>', hidden = True)

                    # yield dict(sourceFormatted = self._formatSource(source),
                    #            source = source, name = name,
                    #            sourceAttr = safeAttr(str(source)),
                    #            nameAttr = safeAttr(str(name)))

            else:
                try: source = p.getSourceMap().source
                except AttributeError: source = None

                r = dict()

                if source:
                    r['sourceFormatted'] = self._formatSource(source)
                    r['source'] = source
                    r['name'] = name
                    r['position'] = name

                    r['sourceAttr'] = self._sourceLinkAttr(source)
                    r['nameAttr'] = safeAttr(str(name))

                try: (start, g) = p.lineGroup(pos)
                except (TypeError, AttributeError):
                    # No line source info found -- render one instruction string.
                    try: s = p.instructionsString(pos-1, pos, suppress_name = True)
                    except AttributeError:
                        s = '<unknown procedure>'
                else:
                    span = 1 # len(g) # XXX :skip: 20 instructions per line??
                    if pos >= start and pos <= (start + span):
                        s = p.instructionsString(start, start + span,
                                                 suppress_name = True,
                                                 highlight = pos)
                    else:
                        # Why lineGroup isn't returning pos-containing span?
                        s = p.instructionsString(pos-1, pos, suppress_name = True)

                n = getattr(p, 'name', None)
                if n:
                    r['codeName'] = n

                r['code'] = s

                # print(f'[default] {r}')
                # r['debug_origin'] = 'default'
                yield r

    formatTracebackContext = formatTracebackHtml


from threading import Thread
from stuphos.runtime.facilities import Facility
from stuphos import getConfig

class ScanThread(Thread, Facility):
    NAME = 'System::Log::Responsive'

    def create(self):
        syslog = getConfig('input-path', 'System:Log')
        syslog = io.path(syslog).open()
        # todo: use the system syslog scanner installed.
        return self(syslog)

    def __init__(self, syslog, scanner):
        self.syslog = syslog
        self.scanner = scanner
        Thread.__init__(self)
        # self.start()

    def run(self):
        while True:
            line = self.syslog.readline()
            self.handle(line, self.scanner.scan(line))

    def handle(self, line, scan):
        pass


try: from stuphos.runtime.registry import registerObject
except ImportError: pass
else:
    class API:
        getScanSyslogPaths = staticmethod(getScanSyslogPaths)

        KNOWN_PATTERN_TYPES = property(lambda self:KNOWN_PATTERN_TYPES)
        compile_pattern = property(lambda self:compile_pattern)
        static_pattern = property(lambda self:static_pattern)

    # Singleton.
    API = API()

    SYSLOG_SCANNER_OBJECT_NAME = 'Syslog::Scanner::API'
    registerObject(SYSLOG_SCANNER_OBJECT_NAME, API)
