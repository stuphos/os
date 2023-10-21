# Frozen because it's being merged back into main.
# # Originally from GardenSnake:
# #
# #          Andrew Dalke / Dalke Scientific Software, LLC
# #             30 August 2006 / Cape Town, South Africa

# # Differences:
# #  - utilization of xrange instead of range
# #  - import ply.lex explicitly here
# #  - added module = keyword to lexer constructor to separate from this module.

# ## I implemented INDENT / DEDENT generation as a post-processing filter

# # The original lex token stream contains WS and NEWLINE characters.
# # WS will only occur before any other tokens on a line.

# # I have three filters.  One tags tokens by adding two attributes.
# # "must_indent" is True if the token must be indented from the
# # previous code.  The other is "at_line_start" which is True for WS
# # and the first non-WS/non-NEWLINE on a line.  It flags the check so
# # see if the new line has changed indication level.

# # Python's syntax has three INDENT states
# #  0) no colon hence no need to indent
# #  1) "if 1: go()" - simple statements have a COLON but no need for an indent
# #  2) "if 1:\n  go()" - complex statements have a COLON NEWLINE and must indent
# NO_INDENT = 0
# MAY_INDENT = 1
# MUST_INDENT = 2

# def countws(n):
#     w = 0
#     for c in n:
#         if c in '\t ':
#             w += 1
#         else:
#             break

#     return w

# # only care about whitespace at the start of a line
# def track_tokens_filter(lexer, _tokens):
#     # Todo: this might be a good place to insert lineno info for each token.
#     lexer.at_line_start = at_line_start = True
#     indent = NO_INDENT
#     first = False # True # todo: consider preceding whitespace
#     # saw_colon = False

#     lookahead = [None]

#     def readYaml():
#         l = lexer # .lexer
#         i = l.lexpos
#         d = l.lexdata
#         n = len(d)

#         def line(i):
#             b = []
#             while i < n:
#                 c = d[i]
#                 i += 1
#                 if c == '\n':
#                     break

#                 b.append(c)

#             return (i, ''.join(b))

#         f = True
#         y = []

#         while i < n:
#             s = i
#             (i, b) = line(i)
#             w = countws(b)

#             if w == len(b):
#                 if b or not f:
#                     y.append(b[ws:])

#                 continue

#             if f:
#                 f = False
#                 ws = w

#             elif w < ws:
#                 l.lexpos = s # (-1 doesn't seem to matter: or does it?)
#                 break

#             y.append(b[ws:])
#         else:
#             l.lexpos = n # (-1 doesn't seem to matter: or does it?)

#         return '\n'.join(y) + '\n'


#     def checkYaml(name):
#         n = next(tokens) # or _tokens?
#         if n.type == 'COLON':
#             yaml = readYaml()
#             token = _new_token('YAML', name.lineno) # todo: rename type to something like 'BLOCK'
#             token.name = name
#             token.value = yaml
#             token.at_line_start = at_line_start # probably always true!
#             token.must_indent = (indent == MUST_INDENT)

#             # print repr(lexer.lexdata[lexer.lexpos:])
#             return token

#         lookahead[0] = n

#     @apply
#     def tokens():
#         i = iter(_tokens)
#         while True:
#             if lookahead[0]:
#                 yield lookahead[0]
#                 lookahead[0] = None
#                 continue

#             yield next(i)

#     for token in tokens:
#         token.at_line_start = at_line_start

#         # Experimental inline yaml support:
#         if (first or at_line_start) and token.type == 'NAME':
#             yaml = checkYaml(token)
#             if yaml:
#                 indent = NO_INDENT
#                 yield yaml
#                 continue

#         if token.type == "COLON":
#             at_line_start = False
#             indent = MAY_INDENT
#             token.must_indent = False
            
#         elif token.type == "NEWLINE":
#             at_line_start = True
#             if indent == MAY_INDENT:
#                 indent = MUST_INDENT
#             token.must_indent = False

#         elif token.type == "WS":
#             # XXXXX Why doesn't this work anymore/ever did work??
#             # assert token.at_line_start == True
#             # at_line_start = True # would already be true...
#             token.must_indent = False

#         else:
#             # A real token; only indent after COLON NEWLINE
#             if indent == MUST_INDENT:
#                 token.must_indent = True
#             else:
#                 token.must_indent = False
#             at_line_start = False
#             indent = NO_INDENT

#         yield token
#         lexer.at_line_start = at_line_start

# def _new_token(type, lineno):
#     tok = lex.LexToken()
#     tok.type = type
#     tok.value = None
#     tok.lineno = lineno
#     tok.lexpos = 0
#     return tok

# # Synthesize a DEDENT tag
# def DEDENT(lineno):
#     return _new_token("DEDENT", lineno)

# # Synthesize an INDENT tag
# def INDENT(lineno):
#     return _new_token("INDENT", lineno)


# # Track the indentation level and emit the right INDENT / DEDENT events.
# def indentation_filter(tokens):
#     # A stack of indentation levels; will never pop item 0
#     levels = [0]
#     token = None
#     depth = 0
#     prev_was_ws = False
#     for token in tokens:
#         # print depth, levels, token

#         ##    if 1:
#         ##        print "Process", token,
#         ##        if token.at_line_start:
#         ##            print "at_line_start",
#         ##        if token.must_indent:
#         ##            print "must_indent",
#         ##        print
                
#         # WS only occurs at the start of the line
#         # ???
#         # There may be WS followed by NEWLINE so
#         # only track the depth here.  Don't indent/dedent
#         # until there's something real.
#         if token.type == "WS":
#             # assert depth == 0 # wtf line start
#             # yeah, but this may be needed to properly emit indentation tokens
#             # ALTHOUGH, it doesn't seem to effect _current_ absence.
#             depth = len(token.value)
#             prev_was_ws = True
#             # WS tokens are never passed to the parser
#             continue

#         if token.type == "NEWLINE":
#             depth = 0
#             if prev_was_ws or token.at_line_start:
#                 # ignore blank lines
#                 # XXX
#                 continue
#             # pass the other cases on through
#             yield token
#             continue

#         prev_was_ws = False # assumed to be in right location
#         if token.type == 'YAML':
#             # supposed to simulate the line-start below, but does
#             # this work in complex nests?
#             if depth in levels:
#                 levels.remove(depth)

#             depth = 0 # err what if must_indent is reset?!?

#             if token.must_indent:
#                 yield INDENT(token.lineno)

#             yield token

#             if token.must_indent:
#                 yield DEDENT(token.lineno)

#             continue

#         # then it must be a real token (not WS, not NEWLINE)
#         # which can affect the indentation level

#         if token.must_indent:
#             # The current depth must be larger than the previous level
#             if not (depth > levels[-1]):
#                 raise IndentationError("expected an indented block")

#             levels.append(depth)
#             yield INDENT(token.lineno)

#         elif token.at_line_start:
#             # Must be on the same level or one of the previous levels
#             if depth == levels[-1]:
#                 # At the same level
#                 pass
#             elif depth > levels[-1]:
#                 raise IndentationError("indentation increase but not in new block")
#             else:
#                 # Back up; but only if it matches a previous level
#                 try:
#                     i = levels.index(depth)
#                 except ValueError:
#                     raise IndentationError("inconsistent indentation")
#                 for _ in xrange(i+1, len(levels)):
#                     yield DEDENT(token.lineno)
#                     levels.pop()

#         yield token

#     ### Finished processing ###

#     # Must dedent any remaining levels
#     if len(levels) > 1:
#         assert token is not None
#         for _ in xrange(1, len(levels)):
#             yield DEDENT(token.lineno)
    

# # The top-level filter adds an ENDMARKER, if requested.
# # Python's grammar uses it.
# def filter(lexer, add_endmarker = True):
#     token = None
#     tokens = iter(lexer.token, None)
#     tokens = track_tokens_filter(lexer, tokens)
#     for token in indentation_filter(tokens):
#         yield token

#     if add_endmarker:
#         lineno = 1
#         if token is not None:
#             lineno = token.lineno
#         yield _new_token("ENDMARKER", lineno)

# # Combine Ply and my filters into a new lexer
# import ply.lex as lex

# class IndentLexer(object):
#     def __init__(self, module=None, debug=0, optimize=0, lextab='lextab', reflags=0):
#         self.lexer = lex.lex(module=module, debug=debug, optimize=optimize, lextab=lextab, reflags=reflags)
#         self.token_stream = None
#         self.lineno = 1
#     def input(self, s, add_endmarker=True):
#         self.lexer.paren_count = 0
#         self.lexer.input(s)
#         self.token_stream = filter(self.lexer, add_endmarker)
#     def token(self):
#         try:
#             return self.token_stream.next()
#         except StopIteration:
#             return None
