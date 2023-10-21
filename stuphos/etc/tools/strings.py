# String Routines.
toString = str.__str__

# Todo: use regexprs..?
# Todo: test against regexprs.
def buildNonletters():
    return ''.join(chr(c) for c in range(0, ord('A'))) + \
           ''.join(chr(c) for c in range(ord('Z') + 1, ord('a'))) + \
           ''.join(chr(c) for c in range(ord('z') + 1, 256))

def buildAscii():
    return ''.join(chr(c) for c in range(0, 256))

try: from curses.ascii import isprint as isPrintable
except ImportError:
    _printable_chr = '\' !"#$%&\\\'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\\\]^_`abcdefghijklmnopqrstuvwxyz{|}~\''
    def isPrintable(c):
        return c in _printable_chr

def buildNonprintable():
    return ''.join(chr(c) for c in range(0, 256) \
                   if not chr(c) == '\n' and not isPrintable(chr(c)))

_nonletters = buildNonletters()
_ascii = buildAscii()

_nonprintable = buildNonprintable()

_3translate_ascii = dict((n, n) for n in _ascii)
_3translate_ascii_letters = dict(_3translate_ascii)
_3translate_ascii_printable = dict(_3translate_ascii)

for n in _nonletters:
    _3translate_ascii_letters[n] = None
for n in _nonprintable:
    _3translate_ascii_printable[n] = None

def getLetters(string):
    return string.translate(_3translate_ascii_letters)

def getPrintable(string):
    return string.translate(_3translate_ascii_printable)

def splitOne(s, x):
    # Command-line argument passing routine.
    s = s.lstrip()
    parts = s.split(x, 1)
    if not parts:
        return ('', '')

    if len(parts) == 1:
        return (parts[0], '')

    return (parts[0], parts[1])

chopOne = splitOne

def SORP(n):
    return '' if n == 1 else 's'

def ANORA(s):
    return 'an' if s[:1].lower() in 'aeiou' else 'a'


VARIABLE_CODE = '$'
def InterpolateStringVariables(string, **values):
    parts = []
    position = 0

    while True:
        start = string.find(VARIABLE_CODE, position)
        if start < 0:
            break

        end = string.find(VARIABLE_CODE, start + 1)
        if end < 0:
            raise ValueError('Unterminated variable name: %s' % (string[start:]))

        if start > position:
            parts.append(string[position:start])

        name = string[start+1:end]
        if name:
            parts.append(values.get(name, ''))
        else:
            parts.append(VARIABLE_CODE)

        position = end + 1

    if position < len(string):
        parts.append(string[position:])

    return ''.join(parts)

# Other interpolation tools.
import re
SUBMETHOD_PATTERN = re.compile(r'(%(identifier)s)\$(%(identifier)s)\s*\(\s*(\))?' % \
                               dict(identifier = '[a-zA-Z]+[a-zA-Z0-9_]*'))

def TranslateSubmethodPatterns(string):
    def t():
        i = SUBMETHOD_PATTERN.scanner(string)
        c = 0

        while True:
            m = i.search()
            if m is None:
                break

            (s, e) = m.span()
            if s > c:
                yield string[c:s]

            c = e

            (a, b, p) = m.groups()
            if p:
                yield "call(%s, '%s')" % (a, b)
            else:
                yield "call(%s, '%s', " % (a, b)

        if c < len(string):
            yield string[c:]

    return ''.join(t())

# "{percentage(me.hit, me.max_hit)}"

class Expression(str):
    def __call__(self, sandbox):
        # Should, in practice, separate globals, locals
        return sandbox.eval(self)

def TokenizeInterpolatedExpression(string):
    s = 0
    n = len(string)

    while True:
        i = string.find('{', s)
        if i < 0:
            break

        if i > s:
            yield string[s:i]

        # Find ending '}' lexically (looking for nests and quotes).
        v = 0
        q = False

        i += 1
        for e in range(i, n):
            k = string[e]
            if q:
                # Handle quoted matter.
                if k == q:
                    if t != '\\':
                        q = False
                else:
                    q = k

                t = k # always gets set

            elif k == '{':
                v += 1 # deepness
            elif k == '}':
                if v:
                    v -= 1
                else:
                    break
        else:
            raise SyntaxError('No terminating }')

        yield Expression(string[i:e])
        s = e + 1

    if s < n:
        yield string[s:n]

class Interpolated(str):
    @classmethod
    def translateValue(self, sandbox, value):
        def i(t):
            if isinstance(t, Expression):
                return str(t(sandbox))
            if isinstance(t, str):
                return t

            return str(t)

        return ''.join(i(t) for t in TokenizeInterpolatedExpression(value))

    def __call__(self, sandbox):
        return self.translateValue(sandbox, self)

    __mod__ = __call__

class Interpolated2(Interpolated):
    @classmethod
    def translateValue(self, sandbox, value):
        # Convert submethod syntax patterns in string.
        value = TranslateSubmethodPatterns(value)
        return Interpolated.translateValue(sandbox, value)

color_codes = dict(N = 0, r = 31, g = 32, y = 33,
                   b = 34, m = 35, c = 36, w = 37)
 # //#define KNRM  "\033[0m"
 # //#define KRED  "\033[31m"
 # //#define KGRN  "\033[32m"
 # //#define KYEL  "\033[33m"
 # //#define KBLU  "\033[34m"
 # //#define KMAG  "\033[35m"
 # //#define KCYN  "\033[36m"
 # //#define KWHT  "\033[37m"

def parse_color(text):
    SC = 1
    CC = 2

    s = SC
    b = ''

    for c in text:
        if c == '&':
            if s == CC:
                if b:
                    yield b
                    b = ''

                yield '&'
                s = SC
            else:
                s = CC

        elif s == CC:
            if b:
                yield b
                b = ''

            try: yield '\033[%sm' % color_codes[c]
            except KeyError:
                yield '&' + c

            s = SC
        else:
            b += c

    if b:
        yield b


def renderTemplate(*args, **kwd):
    global renderTemplate
    from stuphos.runtime.architecture.api import renderTemplate
    return renderTemplate(*args, **kwd)


def compactify(string, width):
    string = str(string)
    if len(string) <= width:
        return string

    return '%s...%s' % (string[:int(width/2)-1], string[-(int(width/2)-2):])


def escapeXmlOutput(s):
    # Todo: regexprs
    s = s.replace('&', '&amp;')
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = getPrintable(s)
    return s

# escapeStreamOutput = escapeXmlOutput
# escapeStreamOutput = getPrintable

def escapeOutputIdentity(s):
    return s


def safeAttr(s):
    'Return string escaped for embedding in an HTML attribute value.'

    return s.replace('"', '&quot;')

def escapeSingleQuotes(s):
    return s.replace("'", "\\'")
def escapeDoubleQuotes(s):
    return s.replace('"', '\\"')

def escapeQuotes(s):
    return escapeSingleQuotes(escapeDoubleQuotes(s))

def escapeHtmlJSQuotes(s):
    return safeAttr(escapeSingleQuotes(s))


def nling(function):
    def nl(*args, **kwd):
        return '\n'.join(function(*args, **kwd))

    return nl

def indent(string, tab = '    ', level = 1):
    tab *= level
    return tab + ('\n' + tab).join(string.split('\n'))


class Indent: # (Object):
    DEFAULT_TAB = '    ' # four -- inline with python's default

    def __init__(self, tab = None):
        self.amount = tab or self.DEFAULT_TAB
        self.level = 0

    def getAttributeString(self):
        return 'level: %d (%r)' % (self.level, self.amount)

    def adjust(self, n):
        self.level += n
        return self

    increase = property(lambda self: self.adjust( 1))
    decrease = property(lambda self: self.adjust(-1))

    def __enter__(self):
        return self.increase
    def __exit__(self, etype = None, evalue = None, tb = None):
        try: return self.decrease
        finally:
            if evalue is not None:
                raise etype(evalue).with_traceback(tb)

    def getTab(self):
        return self.amount * self.level

    __str__ = getTab
    tab = property(getTab) # memorized..

    # Erm, yes this is different then plain add.
    __iadd__ = adjust

    ##    def __add__(self, string):
    ##        return self.tab + str(string)

    def format(self, string, *args, **kwd):
        if args:
            assert not kwd
            return self.tab + (string % args)

        assert kwd
        return self.tab + (string % kwd)

    __call__ = format

    def paragraph(self, text):
        return self.amount + ('\n' + self.amount).join(text.split('\n'))

    @classmethod
    def Paragraph(self, text, tab = None):
        return self(tab = tab).paragraph(text)

    # class Buffer(Object, StringBufferType):
    #     # Maintains a StringIO buffer and also an indent state.

    #     @classmethod
    #     def Get(self, buf = None, *args, **kwd):
    #         return self(*args, **kwd) if buf is None else buf

    #     def __init__(self, *args, **kwd):
    #         StringBufferType.__init__(self)
    #         try: indent = kwd['indent']
    #         except KeyError: indent = Indent(*args, **kwd)
    #         self.tab = indent

    #     def __str__(self):
    #         return self.getvalue()

    #     def indent(self, string):
    #         print(self.tab.tab + string, file=self)
    #         return self

    #     # Todo: how to enable printing directly to this stream?
    #     __lshift__ = indent

    #     def __enter__(self):
    #         return self.tab.increase
    #     def __exit__(self, etype = None, evalue = None, tb = None):
    #         try: return self.tab.decrease
    #         finally:
    #             if evalue is not None:
    #                 raise etype(evalue).with_traceback(tb)

    #     def indentParagraph(self, amount = 1):
    #         # Todo: indent the text buffer, in place (or dedent).
    #         raise NotImplementedError

indent = paragraphIndent = Indent.Paragraph


def isYesValue(value):
    if value is True:
        return True
    if isinstance(value, str):
        return value.lower() in ['yes', 'true', '1', 'on']

    return bool(value)

def isNoValue(value):
    if value is False:
        return True
    if isinstance(value, str):
        return value.lower() in ['no', 'false', '0', 'off']

    return not bool(value)
