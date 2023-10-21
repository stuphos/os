# Grammatical text structure.
# Note: the input gets executed as python code (see buildMethod),
# so the grammar should be built from source in the system.
from types import ClassType as newClassObject


def buildCode(name, parameters = None, code = None, docstring = None):
    if not code:
        code = 'pass'
    elif isinstance(code, list):
        code = nls(code)

    def build():
        yield 'def %s(%s):' % (name, ', '.join(parameters or []))

        if docstring:
            yield indent(repr(docstring))

        yield indent(code)

    return nls(build()) + '\n'

def buildMethod(code, name, globals = None):
    if globals is None:
        from builtins import globals
        globals = globals()

    # print code

    ns = {}
    exec(code, globals, ns)
    return ns[name]

def integrateMethod(values, name, parameters, code, docstring, globals = None):
    values[name] = buildMethod(buildCode(name, parameters = parameters,
                                         code = code, docstring = docstring),
                               name, globals)

def integrateMethodMap(values, name, mapping, globals = None):
    return integrateMethod(values, name,
                           mapping.get('parameters'),
                           mapping.get('code'),
                           mapping.get('documentation'),
                           globals)

def _baseClasses(c, default):
    if not c:
        c = default
    if not isinstance(c, (list, tuple)):
        return (c,)

    return c


class Lexicon:
    @classmethod
    def Build(self, className, lexicon, baseClass = None, globals = None):
        # Build lexer input class.
        values = dict()

        # Mandate tokens.

        # Does absence in these names cause this error?
        #   File "C:\Python27\lib\site-packages\ply\lex.py", line 363, in token
        #     func.__name__, newtok.type), lexdata[lexpos:])
        # LexError: <string>:1: Rule 't_NAME' returned an unknown token type 'if'

        tokens = lexicon.get('names')
        if isinstance(tokens, str):
            tokens = tokens.split()
        if not tokens:
            tokens = []

        values['tokens'] = tokens

        # Optional instance constructor.
        try: init = lexicon['init']
        except KeyError: pass
        else: integrateMethodMap(values, '__init__', init, globals)

        # Token match methods.
        for (name, tokdef) in lexicon.items():
            if name.startswith('t_'):
                if isinstance(tokdef, str):
                    values[name] = tokdef

                    # No, this produces lexfuncs that return None!
                    # integrateMethod(values, name,
                    #                 ['self', 't'], None,
                    #                 docstring = tokdef,
                    #                 globals = globals)

                else:
                    integrateMethod(values, name,
                                    tokdef.get('parameters', ['self', 't']),
                                    tokdef.get('match'),
                                    tokdef.get('pattern'),
                                    globals = globals)

            elif isinstance(tokdef, dict):
                integrateMethodMap(values, name, tokdef,
                                   globals = globals)


        baseClass = _baseClasses(baseClass, self)
        return newClassObject(className, baseClass, values)

    def __init__(self, grammar):
        self.grammar = grammar


class Rules:
    @classmethod
    def Build(self, className, rules, baseClass = None, globals = None):
        # Build rule/production input class.
        values = dict()

        # Optional instance constructor.
        try: init = rules['init']
        except KeyError: pass
        else: integrateMethodMap(values, '__init__', init, globals)

        # Rule production methods.
        for (name, ruledef) in rules.items():
            if name.startswith('p_'):
                if isinstance(ruledef, str):
                    integrateMethod(values, name, ['self', 'p'],
                                    None, ruledef, globals)
                else:
                    integrateMethod(values, name,
                                    ruledef.get('parameters', ['self', 'p']),
                                    ruledef.get('production', 'p[0] = p[1]'),
                                    ruledef.get('pattern'),
                                    globals)

            elif isinstance(ruledef, dict):
                integrateMethodMap(values, name, ruledef, globals)


        baseClass = _baseClasses(baseClass, self)
        return newClassObject(className, baseClass, values)

    def __init__(self, grammar):
        self.grammar = grammar
        self.tokens = grammar.lexicon.tokens
        if hasattr(grammar.lexicon, 'literal'):
            self.literals = grammar.lexicon.literals


class Grammar:
    @classmethod
    def FromStructure(self, className, value, **kwd):
        # Note: this produces a Grammar subclass with defined lexicon/rules classes.
        # The grammar class must be instantiated with the starting rule: if you specify
        # the 'start' key, it will be.

        globals = kwd.get('globals')

        lexicon = value['lexicon']
        lexiconClass = kwd.get('lexiconClass')
        lexicon = Lexicon.Build('lexicon', lexicon, lexiconClass, globals = globals)

        rules = value['rules']
        ruleClass = kwd.get('ruleClass')
        rules = Rules.Build('rules', rules, ruleClass, globals = globals)

        values = dict(lexiconClass = lexicon, ruleClass = rules)

        for (name, method) in value.items():
            if name not in ['lexicon', 'rules', 'start']:
                if isinstance(method, dict):
                    integrateMethodMap(values, name, method, globals)


        baseClass = _baseClasses(kwd.get('grammarClass'), self)
        grammarClass = newClassObject(className, baseClass, values)

        try: start = value['start']
        except KeyError:
            return grammarClass

        return grammarClass(start, value.get('debug'))


    def __init__(self, start, debug = False):
        from ply import lex, yacc
        self.start = start

        self.lexicon = self.lexiconClass(self)
        self.rules = self.ruleClass(self)

        # try: from ph.lang.layer import gs_indent_lexer
        try: from stuphos.language.gen import gs_indent_lexer
        except ImportError:
            # todo: optionally mandate this.
            self.lexer = lex.lex(object = self.lexicon)
        else:
            self.lexer = gs_indent_lexer.IndentLexer(self.lexicon)

        if debug:
            import sys
            debug = yacc.PlyLogger(sys.stderr)

        ERRORLOG = False
        self.debug = debug
        self.parser = yacc.yacc(module = self.rules,
                                debug = debug,
                                errorlog = None, #  if ERRORLOG else yacc.NullLogger(),
                                tabmodule = 'parsetab_%s' % start,
                                debugfile = 'parser_%s.out' % start,
                                outputdir = '.',
                                start = start,
                                check_recursion = False)

        # Other yacc options:
        #   debug = 0   ...   No debugging output, including writing parser.out
        #   outputdir = "x"   ...   Location of written tab module.
        #   method = "SLR"   ...   Use simpler parser for faster generation.
        #   errorlog = yacc.NullLogger()

    def parse(self, source):
        self.reset_errors()
        try: return self.parser.parse(source, lexer = self.lexer, debug = self.debug) # , tracking = 1)
        finally:
            self.report_errors()

    def tokenize(self, source):
        self.lexer.input(source)
        return self.lexer.token_stream

        # try:
        #     while True:
        #         yield self.lexer.next()

        # except StopIteration:
        #     pass

    def report_errors(self):
        try:
            for e in self.lexical_errors:
                print('Illegal character: %r!' % e)
            for e in self.parse_errors:
                print('Syntax error: %r!' % e)
        except IOError:
            # This might happen if stdout gets closed!
            pass

        self.reset_errors()

    def reset_errors(self):
        self.lexical_errors = []
        self.parse_errors = []


Rules.base = Rules
Lexicon.base = Lexicon
Grammar.base = Grammar


girl = '''
server:
    # start: program
    start: wmc_document
    debug: true

    lexicon:
        names::
            ASSIGN         AT             BANG           COLON          
            COMMA          DECIMAL        DECIMALSTRING  DEDENT         
            DOT            ELLIPSE        ENDMARKER      EQUAL          
            GREATERTHAN    GREATERTHANEQ  INDENT         INTEGER        
            LBRACKET       LESSTHAN       LESSTHANEQ     LPAREN         
            MINUS          MINUSASSIGN    MODASSIGN      MODULO         
            NAME           NEWLINE        NOT            NOTEQUAL       
            NUMBER         PLUS           PLUSASSIGN     RBRACKET       
            RPAREN         SEMICOLON      SLASH          SLASHASSIGN    
            STAR           STARASSIGN     STRING         WS             
            IF             DEF            ELIF           ELSE
            WHILE          TRY            EXCEPT         FINALLY
            FOR            IN             NOT            RETURN

            DOLLAR TRUE FALSE NULL LBRACE RBRACE WMCLISTVALUE WMCMAPVALUE WMCHERESTRING


        # Simple expressional tokens:
        t_PLUS: '\+'
        t_MINUS: '-'
        t_STAR: '\*'
        t_SLASH: '/'
        t_LPAREN: '\('
        t_RPAREN: '\)'
        t_LBRACKET: '\['
        t_RBRACKET: '\]'

        t_BANG: '!'
        t_NOTEQUAL: '!='
        t_AT: '@'
        t_MODULO: '%'

        t_EQUAL: '=='
        t_LESSTHAN: '<'
        t_LESSTHANEQ: '<='
        t_COMMA: ','
        t_DOT: '\.'
        t_GREATERTHAN: '>'
        t_GREATERTHANEQ: '>='

        t_NOT: 'not'

        t_ELLIPSE: '\.\.\.'

        t_COLON: '\:'
        t_SEMICOLON: ';'
        t_ASSIGN: '='
        t_PLUSASSIGN: '\+='
        t_MINUSASSIGN: '-='
        t_STARASSIGN: '\*='
        t_SLASHASSIGN: '/='
        t_MODASSIGN: '%='

        t_DOLLAR: '\\$'
        t_TRUE: 'true'
        t_FALSE: 'false'
        t_NULL: 'null'

        t_WMCLISTVALUE: '0'
        t_WMCMAPVALUE: '0'
        t_WMCHERESTRING: '0'


        # Compilable rules:

        # Apparently this wants to match trailing colons.......?
        # t_DECIMAL:
        #     # ? Is this parsing integers??  probably because of unordered tokpat?
        #     pattern: '((\d+.\d*)|(\d*.\d+))'
        #     match::
        #         t.value = float(t.value)
        #         return t

        t_NUMBER:
            pattern: '(\d+(\.\d*)?|\.\d+)([eE][-+]? \d+)?'
            match::
                v = t.value
                if v.isdigit():
                    v = int(v)
                else:
                    v = decimal.Decimal(v)

                t.value = v
                return t

        # t_STRING:
        #     # pattern: "'([^\\']+|\\'|\\\\|\\r|\\n)*'"
        #     pattern: 's'
        #     match::
        #         t.value=t.value[1:-1].decode("string-escape")
        #         return t

        init:
            parameters: [self, grammar]
            code::
                self.base.__init__(self, grammar)
                self.reserved = ['while', 'if']

        t_NAME:
            pattern: '[\$a-zA-Z_][\$a-zA-Z_0-9]*'
            match::
                # Check for reserved words.
                if t.value in self.reserved:
                    # t.type = t.value # must be in lexer.tokens
                    t.reserved = True

                # t.type = self.reserved.get(t.value, 'NAME')

                # This is to demonstrate that the token value can acquire a complex
                # value, although since yacc only looks at the 'value' attribute, the
                # token should set any _other_ attributes for further processing...
                # t.value = (t.value, symbol_lookup(t.value))

                return t

        t_comment:
            pattern: "[ ]*\\043[^\\n]*"

        t_WS:
            pattern: '[ ]+'
            match::
                # Note: This is not used in the parser, but by the gs_indent_lexer layer.
                # This terminal will generate a warning, but it is required.
                if t.lexer.at_line_start and t.lexer.paren_count == 0:
                    return t

        t_newline:
            pattern: '\\n+'
            match::
                t.lexer.lineno += len(t.value)
                t.type = 'NEWLINE'
                return t

        t_error:
            match::
                self.grammar.lexical_errors.append(t.value[0])
                t.lexer.skip(1)

    rules:
        p_error:
            production::
                self.grammar.parse_errors.append(p)


        p_testlist:
            pattern::
                testlist : testlist_multi COMMA
                         | testlist_multi

            production::
                if len(p) == 2:
                    p[0] = p[1]
                else:
                    # May need to promote singleton to tuple
                    if isinstance(p[1], list):
                        p[0] = p[1]
                    else:
                        p[0] = [p[1]]

                # Convert into a list?
                if isinstance(p[0], list):
                    p[0] = List(p[0], self.grammar.lexer.lineno)


        p_arglist::
            arglist : arglist COMMA argument
                               | argument

        p_argument::
            argument : test

        p_atom_list::
                    atom : LPAREN testlist RPAREN
                         | LBRACKET testlist RBRACKET
                         | LBRACKET RBRACKET


        p_atom_name::
            atom : NAME

        p_atom_number::
                    atom : NUMBER
                         | STRING


        p_comparison::
                    comparison : comparison PLUS comparison
                               | comparison MINUS comparison
                               | comparison STAR comparison
                               | comparison SLASH comparison
                               | comparison MODULO comparison
                               | comparison NOTEQUAL comparison
                               | comparison EQUAL comparison
                               | comparison LESSTHAN comparison
                               | comparison LESSTHANEQ comparison
                               | comparison GREATERTHAN comparison
                               | comparison GREATERTHANEQ comparison
                               | PLUS comparison
                               | MINUS comparison
                               | NOT comparison
                               | power


        p_compound_stmt::
                    compound_stmt : if_stmt
                                  | while_loop
                                  | for_loop
                                  | try_except
                                  | funcdef


        p_else::
            else : ELSE COLON suite

        p_elseif::
            elseif : ELIF test COLON suite

        p_elseif_chain::
                    elseif_chain : elseif_chain elseif
                                 | elseif


        p_error::


        p_except::
                    except : EXCEPT LPAREN except_type_list RPAREN COMMA NAME COLON suite
                           | EXCEPT NAME NAME COLON suite


        p_except_chain::
                    except_chain : except_chain except
                                 | except


        p_except_type_list::
                    except_type_list : except_type_list COMMA NAME
                                     | NAME


        p_expr_stmt::
                    expr_stmt : lvalue ASSIGN testlist
                              | lvalue PLUSASSIGN testlist
                              | lvalue MINUSASSIGN testlist
                              | lvalue STARASSIGN testlist
                              | lvalue SLASHASSIGN testlist
                              | lvalue MODASSIGN testlist
                              | testlist


        p_flow_stmt::
            flow_stmt : return_stmt

        p_for_loop::
            for_loop : FOR NAME IN test COLON suite

        p_funcdef::
            funcdef : DEF NAME parameters COLON suite

        p_if_stmt::

                    if_stmt : IF test COLON suite elseif_chain else
                            | IF test COLON suite elseif_chain
                            | IF test COLON suite else
                            | IF test COLON suite


        p_lvalue_testlist::
            lvalue : testlist

        p_module::
            module : program ENDMARKER

        p_parameters::
            parameters : LPAREN RPAREN
                                  | LPAREN varargslist RPAREN

        p_power::
                    power : atom
                          | power DOT NAME
                          | power LBRACKET testlist RBRACKET
                          | power trailer


        p_program::
                    program : program NEWLINE
                            | program stmt
                            | NEWLINE
                            | stmt


        p_return_stmt::
                    return_stmt : RETURN
                                | RETURN testlist


        p_simple_stmt::
                    simple_stmt : small_stmts NEWLINE
                                | small_stmts SEMICOLON NEWLINE


        p_small_stmt::
                    small_stmt : flow_stmt
                               | expr_stmt
                               | wmc


        p_small_stmts::
                    small_stmts : small_stmts SEMICOLON small_stmt
                                | small_stmt


        p_stmt_compound::
            stmt : compound_stmt

        p_stmt_simple::
            stmt : simple_stmt

        p_stmts::
                    stmts : stmts stmt
                          | stmt


        p_suite::
                    suite : simple_stmt
                          | NEWLINE INDENT stmts DEDENT


        p_test::
            test : comparison

        p_testlist::
                    testlist : testlist_multi COMMA
                             | testlist_multi


        p_testlist_multi::
                    testlist_multi : testlist_multi COMMA test
                                   | test


        p_trailer::
                    trailer : LPAREN RPAREN
                            | LPAREN arglist RPAREN


        p_try_except::
                    try_except : TRY COLON suite except_chain EXCEPT COLON suite FINALLY COLON suite
                               | TRY COLON suite except_chain EXCEPT COLON suite
                               | TRY COLON suite except_chain FINALLY COLON suite
                               | TRY COLON suite EXCEPT COLON suite
                               | TRY COLON suite FINALLY COLON suite


        p_varargslist::
            varargslist : varargslist COMMA NAME
                                   | NAME

        p_while_loop::
            while_loop : WHILE test COLON suite

        init:
            parameters: [self, grammar]
            code::
                self.base.__init__(self, grammar)

                class WMC:
                    def __init__(self, name, package = None, subtype = None, value = None):
                        self.name = name
                        self.package = package
                        self.subtype = subtype
                        self.value = value

                    @property
                    def defn(self):
                        return '%s(%s$%s)' % (self.name, self.package, self.subtype)

                    def __repr__(self):
                        return self.defn

                    @nling
                    def __str__(self):
                        yield '%s:' % self.defn
                        yield indent(str(self.value))


                self.WMC = WMC

        # YAML
        p_wmc_document:
            pattern::
                wmc_document : wmc ENDMARKER

        # wmc_stmt
        p_wmc:
            pattern::
                wmc : NAME LPAREN NAME DOLLAR NAME RPAREN COLON wmcValue
                    | NAME LPAREN DOLLAR NAME RPAREN COLON wmcValue
                    | NAME LPAREN NAME RPAREN COLON wmcValue
                    | NAME COLON wmcValue
                    | wmcList

            production::
                if len(p) == 9:
                    p[0] = self.WMC(p[1], package = p[3], subtype = p[5], value = p[8])
                elif len(p) == 8:
                    p[0] = self.WMC(p[1], subtype = p[4], value = p[7])
                elif len(p) == 7:
                    p[0] = self.WMC(p[1], subtype = p[3], value = p[6])
                elif len(p) == 4:
                    p[0] = self.WMC(p[1], value = p[3])
                else:
                    # XXX Absorbs SyntaxErrors: yacc.py: 510
                    raise RuntimeError('wmc production length = %d' % len(p))

        p_wmcList:
            pattern::
                wmcList : wmcValue

            # : wmc wmcList
            # | wmc

        p_wmcValue:
            # | NEWLINE INDENT wmc NEWLINE DEDENT

            pattern::
                wmcValue : wmcSingleValue NEWLINE
                         | COLON NEWLINE INDENT WMCHERESTRING DEDENT NEWLINE
                         | NEWLINE INDENT wmcListValue NEWLINE DEDENT
                         | NEWLINE INDENT wmc DEDENT

            # replaced by wmcValue : wmcSingleValue NEWLINE
            # | NEWLINE INDENT wmcSingleValue NEWLINE

            production::
                if len(p) == 7:
                    p[0] = p[4]
                elif len(p) in [5, 6]:
                    p[0] = p[3]
                else:
                    p[0] = p[1]

        p_wmcSingleValue:
            # Need 'rest of line'
            # todo: get rid of NAME
            pattern::
                wmcSingleValue : STRING
                               | INTEGER
                               | DECIMAL
                               | NUMBER
                               | NAME
                               | TRUE
                               | FALSE
                               | NULL
                               | LBRACKET WMCLISTVALUE RBRACKET
                               | LBRACE WMCMAPVALUE RBRACE

            production::
                if len(p) == 4:
                    p[0] = p[2]
                else:
                    p[0] = p[1]

        p_wmcListValue:
            pattern::
                wmcListValue : NEWLINE INDENT MINUS wmcSingleValue wmcListValue NEWLINE

            production::
                p[0] = [p[4]] + p[5]

'''

g2 = '''
if 1:
    server:
        start: wmc_document
        debug: true

        lexicon:
            names:
                ASSIGN

            t_PLUS: name
            t_MINUS: name
            t_STAR: name

            t_DECIMAL:
                pattern: name
                match:
                    name

while x[y(z) + t]:
    if n(z):
        while true:
            ok:
                this: is yaml
'''

# from stuphos.lang.document.interface import load
# g = load(girl, dict(), '')
# g = Grammar.FromStructure('server', g.server)

def loadServer():
    g = loadable('WMC []\n\n' + girl).loading.structure.server
    return Grammar.FromStructure('server', g)

def test(s = g2):
    from sys import stdout
    g = loadServer()

    show(g, s, stdout)

def show(g, s, stream):
    w = stream.write

    depth = 0
    tab = '    '

    f = True
    for t in list(g.tokenize(s.lstrip())):
        if t.type == 'NEWLINE':
            f = True
            w('\n')

        elif t.type == 'INDENT':
            # w('INDENT')
            depth += 1
        elif t.type == 'DEDENT':
            # w('DEDENT')
            depth -= 1

        elif t.type == 'YAML':
            w('%s%s:\n' % (tab * depth, t.name.value))
            w(indent(t.value, tab = tab * (depth + 1)))
            w('\n') # needed?

        elif t.type != 'ENDMARKER':
            if f:
                w(tab * depth)
                f = False

            # endmarker..?
            w(str(t.value))

            if getattr(t, 'reserved', False):
                w(' ')
