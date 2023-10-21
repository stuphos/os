from stuphos.kernel import Girl
import json, pdb

def tokenize(source):
	i = Girl.Module.prebuiltGrammar.tokenize

	for t in i(source):
		yield t

class Yield(Exception):
	def __init__(self, b):
		self.buffer = b

class Unget(Yield):
	def __init__(self, b, token):
		Yield.__init__(self, b)
		self.token = token

class Dedent(Yield):
	pass

def countws(n):
	x = 0

	for c in n:
		if c in '\r\t ':
			x += 1
		else:
			break

	return x

def listing(function):
	def call(*args, **kwd):
		return list(function(*args, **kwd))

	return call

joinNL = '\n'.join

def nling(function):
	def call(*args, **kwd):
		return joinNL(function(*args, **kwd))

	return call

@nling
def insertColons(source):
	lines = source.split('\n')
	previous = 0
	ln = None

	for n in lines:
		ws = countws(n)

		if ln is not None: # don't break on source-start whitespace.
			if ln[-1:] != ':' and (ln or ws > previous):
				yield ln + ':'
			else:
				yield ln

		previous = ws
		ln = n

	if ln is not None:
		yield ln


def parse(source):
	# XXX this is actually quirky with the tokenizer, because it's a single COLON,
	# so technically, all single-identifier token lines will always parse as TEXT blocks.
	#
	# The prevelant problem is that the indent lexer requires at least one COLON anyway
	# to produce indentation tokens, so it must be redesigned: either the lexer must
	# provide aCOLONic mode indentation, or something else.

	# Because this utilizes the gs_index_lexer tokenizer, it should parse inline TEXT tokens:
	# object method
	#	  arg
	#		  This text is passed as the first argument to object.method
	#		  and the TEXT token name (arg1) is ignored.
	#
	#	  arg
	#		  Similarly, this text string is passed as second argument.
	#		  The tokenizer requires an IDENTIFIER before COLON, but its
	#		  asymbolic.
	#

	# It could somehow recognize double colons, or insertColons could more intelligently
	# add colons so that a single colon works.

	# Another functionality could be something like this:
	# decorator
	# 	  function name$ (string arg1, string arg2)
	#	  	  return arg1 + arg2
	#
	# or
	# function name
	#	  code
	#	  	  def name(arg1, arg2):
	#		  	  return arg1 + arg2
	#
	# or
	# call
	# 	  attributeOf name
	# 	  	  module
	# 	  	  	  def name(arg1, arg2):
	# 		      	  return arg1 + arg2
	#	  string a
	#	  string b

	source = insertColons(source)
	source = source.replace('\t', '    ')
	return _parse(tokenize(source))

def _parse(i):
	b = []
	o = []
	e = ''

	# print '_parse'
	for token in i:
		# print token
		if token.type == 'ENDMARKER':
			# (Do not care if there is not any trailing newline.)
			if o:
				b.append(o) # technically this should be [o]

			return b

		if e == '':
			if token.type == 'NEWLINE':
				if o: # (blank lines)
					b.append([o])
					o = []

					# There can be no indent without a preceding header.
					e = 'indent'

			elif token.type == 'DEDENT':
				# print o

				if o: # ENDMARKER following this DEDENT
					b.append([o])

				raise Dedent(b)

			else:
				o.append(token)

		elif e == 'indent':
			if token.type == 'INDENT':
				# print 'subparse'

				# todo: quotational attribute grammatical lookahead.

				try: d = _parse(i)
				except Dedent as d:
					d = d.buffer

				# print d
				# print b[-1]
				b[-1].append(d)
				e = ''
				continue

			elif token.type == 'DEDENT':
				# really, this means terminate this _parse,
				# and the _parse before it.

				if o: # ENDMARKER following this DEDENT
					b.append([o])

				raise Dedent(b)

			elif token.type == 'NEWLINE':
				# XXX if o: b.append([o])!
				pass

			else:
				# XXX A newline doesn't NECESSITATE an indent.
				o.append(token)

				e = ''
				continue

	else:
		raise SyntaxError('Expected newline')


@nling
def dedent(source):
	lines = iter(source.split('\n'))

	for i in lines:
		n = countws(i)
		if len(i) != n:
			yield i[n:]
			break

	for i in lines:
		yield i[n:]

from ply.lex import LexToken
def newToken(type, value):
	x = LexToken()
	x.type = type
	x.value = value
	x.lineno = 0
	x.lexpos = 0
	return x

class extension:
	# Todo: implement this (don't rely on WRLC)
	pass

class Statement(list):
	def __init__(self, node, statements = []):
		self.node = node
		statements = list(statements)
		list.__init__(self, statements)

	@classmethod
	def List(self, statements):
		return self([], statements)

	@property
	def accessorize(self):
		last = None

		for n in self.node:
			if last is not None:
				if last.type == 'NAME':
					if n.type == 'NAME':
						yield newToken('DOT', '.')
						yield n

						last = n
						continue

					elif n.type == 'NUMBER':
						yield newToken('LBRACKET', '[')
						yield n
						yield newToken('RBRACKET', ']')

						last = n
						continue

				elif last.type == 'NUMBER':
					pass

			last = n
			yield n


	@property
	def nodeValues(self):
		return mapi(attributeOf.value, self.node)

	@property
	def accessorizedValues(self):
		return mapi(attributeOf.value, self.accessorize)

	@property
	def line(self):
		# Header line with WS.
		return ' '.join(mapi(str, self.nodeValues))

	@property
	def statements(self):
		return nls(mapi(str, self))

	@nling
	def __str__(self):
		yield self.line
		if self:
			yield indent(self.statements)
			yield ''

	@property
	def lineSource(self):
		return ''.join(mapi(str, self.accessorizedValues))

	@property
	def source(self):
		this = self.lineSource

		if self:
			if this:
				args = ', '.join(mapi(attributeOf.source, self))
				return '%s(%s)' % (self.lineSource, args)

			return '[%s]' % ', '.join(mapi(attributeOf.source, self))

		return this

	@property
	def html(self):
		attrs = ' '.join('%s=%r' % a for a in slices(self, 2))
		yield '<%s %s>' % (self.node[0].value, attrs)

		yield indent(mapi(attributeOf.html, self))
		yield '</%s>' % self.node[0].value

	@property
	def python(self):
		return self.Python(self)

	class Python(extension):
		@property
		def compiled(self):
			pass

	@property
	def emulated(self):
		return self.Emulated(self)

	class Emulated(extension):
		@property
		def compiled(self):
			from stuphos.kernel import Girl
			return Girl(Girl.Expression, self.source)

		@runtime.available(runtime.System.Engine)
		def evaluating(vm, self, **environ):
			from stuphos.kernel import Script, findCurrentUser
			procedure = self.compiled

			with vm.Loading(Script, environ = environ, user = findCurrentUser()) as task:
				procedure.setEnvironment(task.environ) # Unit
				task.addFrameCall(procedure)
				runtime[runtime.System.Journal].waitLogs \
					(task, lambda log, task, traceback:
					 system.print_(nls('%s %s\n%s\n' % \
					 	(f.procedure[i-1], i, indent(nls(mapi(repr, task.stack))))
					 	for (f, i) in traceback)))

				return task


def _syntaxOf(i):
	# print i
	for x in i:
		# print x
		if isinstance(x[0], list): # a line + statements node
			if len(x) > 1: # full
				yield Statement(x[0][:-1], _syntaxOf(x[1])) # -COLON
			else: # a non-dedented, non-parsed statements line node
				# (or, a node with no statements..)
				yield Statement(x[0][:-1])

		else: # a line (- statements) node
			yield Statement(x)

syntaxOf = listing(_syntaxOf)

def compile(source):
	return Statement.List(_syntaxOf(parse(source)))


def shortateCall(frame, source, locals = None):
	'''
	frame task frameCall
		attributeOf compiled
			compile
				source

		locals
	'''

	procedure = compile(source).emulated.compiled

	# def sendToOperator(line, multiline = False, backlog = False):
	# 	print line

	# frame.task.tracing = frame.task.auditInstruction
	# frame.task.sendToOperator = sendToOperator

	# import pdb; pdb.set_trace()

	return frame.task.frameCallSwap(procedure, locals = locals)


def shortate(name, value, **kwd):
	'''
	set node
		attributeOf compiled
			compile
				value

	wrap($class):
		base: extension

		do($method):
			parameters: [*args]
			code::
				pass

	function($shortate)::
		this do
			these are more
			things to do

	run($trigger)::
		this = environment.wrap($('service/wrap', this))
		environment.function(mapping(['this', this]))

	'''

	node = compile(value).emulated.compiled

	def shortateCall(frame, locals = None):
		frame.task.frameCall(node, locals = locals)

	return native

def shortize(function):
	'''
	@shortize
	def lookup(name):
		"""
		accessorOf loading structure value code
			getAttribute my
				name

		"""

	# lookup('jobs').outcome

	'''

	s = compile(dedent(docOf(function))).emulated

	def call(*args, **kwd):
		# kwd.update(dict(zip(function.func_code.co_argnames, args)))
		return s.evaluating(**kwd)

	return call


def parsex():
	# Compile parsed documentation source.
	#  (/ph/lang/layer/gs_indent_lexer.py:139) raise IndentationError("indentation increase but not in new block")
	'''
	this is a line:
		this is a subline:
			subline 1
			subline 2

		subline 3
		subline 4:
			x

	another line 1:
		subline 5

	another line 2

	a:
		b:
			c:
				d:
					e:
						f
							g
	'''

	def f(i):
		if isinstance(i, (list, system.types.generator)):
			return list(map(f, i))

		return i.value

	concating = lambda f: lambda *args, **kwd: ''.join(f(*args, **kwd))

	#@concating
	@nling
	def p(i):
		for x in i:
			if len(x) > 1 and isinstance(x[0], list):
				if isinstance(x[0][0], list):
					yield indent(p(x[0]))
				else:
					yield ' '.join(mapi(str, x[0]))
					yield indent(p(x[1]))

				if len(x) > 2:
					yield str(x[2:])

			elif isinstance(x[0], list):
				yield ' '.join(mapi(str, x[0]))
			else:
				yield ' '.join(mapi(str, x))


	source = docOf(parsex)
	source = dedent(source)
	# print source

	return compile(source)

	# return eat(tokenize(source))
	result = f(parse(source))
	return p(result)

	return json.dumps(result, indent = 1)
