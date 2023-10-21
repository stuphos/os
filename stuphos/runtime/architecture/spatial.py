# Software Architecture
from contextlib import contextmanager
# from types import ClassType as newClassObject, ClassType
newClassObject = type
TypeType = type
ClassType = type

def classObject(name, *bases, **values):
	return newClassObject(name, bases, values)
def subClass(cls, *bases, **values):
	return classObject(cls.__name__, cls, *bases, **values)

def call(o, *args, **kwd):
	'call(classObject("myClass", baseClass, action = callable), value, keyword = value)'

	return o(*args, **kwd)


def classOf(o): return o.__class__
def nameOf(o): return o.__name__
def dictOf(o): return o.__dict__


class applyWith:
	def __init__(self, *args, **kwd):
		self.args = args
		self.kwd = kwd

	def __call__(self, object):
		return object(*self.args, **self.kwd)


class connective:
	# Coupling Abstraction.
	pass

class event:
	'Describes an action.'


class scopeObject(object): # todo: new-style class?
	def __getitem__(self, name):
		try: return getattr(self, name)
		except AttributeError:
			raise KeyError(name)

class namespace(dict):
	def __init__(self, **kwd):
		self.__dict__ = self
		self.update(kwd)

# class extendMap:
# 	def __init__(self, map):
# 		self.map = map
# 	def __call__(self, **kwd):
# 		self.map.update(kwd)
# 		return self


class action:
	# Curry.

	def __init__(self, callable, *args, **kwd):
		self.callable = callable
		self.args = args
		self.kwd = kwd

	def __call__(self, *args, **kwd):
		return self.callable(*(self.args + args),
							 **dict(self.kwd, **kwd))

deferred = callable = action

class operator(property):
	'''
	class o:
		@operator
		class p(extension):
			pass

	class extendsO(o):
		@operator
		class p(o.p):
			pass

			'''

	# Note that if you subclass or reference an operator defined on a base class,
	# this descriptor will return that base class, so you must wrap it in another
	# operator property:

	# 	class base:
	# 		@operator
	# 		class inner:
	# 			pass

	# 	class subclass(base):
	# 		@operator
	# 		class inner(base.inner):
	# 			pass

	def __init__(self, function):
		self.baseClass = function

	def __get__(self, object, closure):
		if object is None:
			# The descriptor was accessed on the class object, probably so it
			# could be subclassed.  Return the baseClass-implementation.
			return self.baseClass

		return self.build(object)

	def build(self, *args, **kwd):
		return self.baseClass(*args, **kwd)


class memorized(action):
	# todo: this could be used to implement collection.propertyClass.
	# Note: the actual memorized value object is on THIS object.

	def __init__(self, name, *args, **kwd):
		action.__init__(self, *args, **kwd)
		self.name = '__' + name

	def __call__(self, object):
		try: return getattr(object, self.name)
		except AttributeError:
			o = action.__call__(self, object)
			setattr(object, self.name, o)
			return o

	class property(property):
		def __init__(self, object):
			self.memory = memorized(object.__name__, object) # auto
		def __get__(self, object, closure):
			return self.memory()


class memorizedOperator:
	'''
	@operator.memorized('interface')
	class interface(network):
		pass

		'''

	def __init__(self, name):
		self.name = name
	def __call__(self, object):
		return self.memorization(self.name, object)

	class memorization(operator):
		def __init__(self, name, object):
			operator.__init__(self, object)
			self.build = memorized(name, self.build)
	named = memorization


	@classmethod
	def auto(self, object):
		'''
		@operator.memorized.auto
		class interface(network):
			pass

			'''

		return self.memorization(object.__name__, object)


operator.memorized = memorizedOperator


class propertyAlias(property):
	# move into .arch
	def __init__(self, name):
		self.name = name
	def __get__(self, object, closure):
		return getattr(object, self.name)


class eventAccessor(scopeObject):
	# todo: collection?
	def __init__(self, object):
		self.object = object

	def __getattr__(self, name):
		try: return object.__getattribute__(self, name)
		except AttributeError:
			ev = delegate(self.object) # Note: does not re-reference this.
			setattr(self, name, ev)
			return ev

# XXX setting eventAccessor.operator works, but gettng it
# causes it to call the operator(property).__get__ method... ?!?
eventAccessorOperator = operator(memorized('eventAccessor', eventAccessor))


class structure:
	@classmethod
	def loadOverlay(self, o, m):
		if isinstance(m, dict):
			for (name, value) in m.items():
				if isinstance(value, ClassType):
					if issubclass(value, actionable.command):
						value(o) # register.
					else:
						self.loadOverlay(getattr(o, name), dictOf(value)) # build network.

				elif isinstance(value, dict):
					self.loadOverlay(getattr(o, name), value)
				else:
					setattr(o, name, value)


class network(list, connective, structure): # entwork
	# generic extensible, symbolic, multiplexed network interface

	# Serves as an object that can have mapped attributes, or
	# attributes that automatically resolve to sub-networks,
	# or functions like an event-observer dispatch model.
	# And, of course it can be subclassed.
	#
	# todo: implement extension/manifold..?
	#
	# Document Object Model Pattern:
	#   each network instance represents an element, because it
	#   has mapped attributes, and child (instance) attributes,
	#   and, it functions as an event listener.  Parent elements
	#   are represented by the 'object' compositional attribute,
	#   the root parent as 'source', and it natively allows
	#   method extension because it's a class.  When compiled
	#   with the operator property decorator, entities can
	#   easily define classes of network interfaces.
	#
	event = event

	def __init__(self, object, *args, **kwd):
		list.__init__(self, args)
		self.object = object
		self.mapping = dict(kwd)
		self.loadOverlay(self, dictOf(classOf(self))) # move into init?
		self.init()


	def init(self):
		pass


	@property
	def source(self):
		o = self
		while isinstance(o, network):
			o = o.object

		return o

	@property
	def subnetworks(self):
		r = list(self.__dict__.keys())
		r.remove('object')
		r.remove('mapping')
		return [s for s in r if not s.startswith('_')]

	def __repr__(self):
		return '<%s: %d subnetworks, %d keys, %d listeners>' % \
				(self.__class__.__name__, len(self.subnetworks),
				 len(self.mapping), len(self))

	def __getattr__(self, name):
		try: return object.__getattr__(self, name)
		except AttributeError:
			i = network(self) # Note: Instantiate basic network type, not subclass-type.
			setattr(self, name, i)
			return i

	def __getitem__(self, name):
		if isinstance(name, int):
			return list.__getitem__(self, name)

		return self.mapping[name]

	def __setitem__(self, name, value):
		self.mapping[name] = value

	def __iadd__(self, function):
		self.append(function)
		return self

	@contextmanager
	def context(self, function):
		self += function
		try: yield
		finally: self -= function

	def __call__(self, *args, **kwd):
		for i in self:
			i(self, *args, **kwd)


# Although, this will generally be customized, it should be extended
# to include structural configuration.  So... it's not actually useful.
interfaceOperator = operator(memorized('interface', network))


class actionable(network):
	# A verb (command-line) interactivity base class. 
	# todo: this "conflicts" with named core type.  So as a spatial.architecture,
	# it is still qualified different, by the problem is that the name 'action'
	# is appropriate for this kind of behavior, and it is 'able' because it is
	# basically a base class...  So it means that if you want to build with it,
	# but also use the core type, you're going to have to be aware until I can
	# come up with a more suitable name.

	'''
	extending:

	class rpcAction(actionable):
		class command(actionable.command):
			@classmethod
			def parse(self, input):
				(verb, args, kwd) = loadable(input).loading.json
				return self.implementation(verb, *args, **kwd)

	class object:
		'object().rpc("[method, [], {}]")'

		def do(self, *args, **kwd):
			pass

		@operator
		class rpc(rpcAction):
			def init(self):
				self.method(self) # Register method command.
				self.methods['do'] = self.object.do

			class method(rpcAction.command):
				name = 'method'

				class implementation(rpcAction.command.verb):
					def __init__(self, name, *args, **kwd):
						self.name = name
						self.args = args
						self.kwd = kwd

					def __call__(self, actor, *args, **kwd):
						actor.interface.methods[self.name] \
							(*self.args, **self.kwd)


		'''

	class NotFound(Exception):
		pass
	class Yield(Exception):
		pass

	def __call__(self, interface, input, *args, **kwd):
		# Currently this controls the command-implementation-and-dispatch lifecycle
		# for a particular network interface mapping.
		#
		# todo: Override network invocator to provide event-oriented dispatch
		# (that is, the event itself defines the invocation).
		#
		# To provide another input type, subclass the 'command' class on the interface,
		# and override the parse methods.

		verb = self.command.parseActionVerb(interface, input)
		return verb(self.object, *args, **kwd)


	class interpretable:
		nonalpha = '!"#$%&\'()*+,-./0123456789:;<=>?@[\\]^_`{|}~'

		@classmethod
		def parseCommandArgs(self, command):
			# command = command.lstrip()
			if command:
				if command[0] in self.nonalpha:
					return (command[0], command[1:])

				i = command.find(' ')
				if i > 0:
					return (command[:i], command[i:])

				return (command, '')

			return ('', '')


		parseCommand = parseCommandArgs


		class unparseable(Exception):
			def __init__(self, command):
				self.command = command


		@classmethod
		def parse(self, command):
			# This is kind of dumb: but, it is used to initiating command events.
			if isinstance(command, str):
				command = command.lstrip()
				if command:
					return self.parseCommand(command)

			raise self.unparseable(command)


		@classmethod
		def parseActionVerb(self, interface, command):
			# This implementation defines the input type (text line string).
			# Pre-parse the command into parts by relying on base command type.
			(verb, argstr) = self.parse(command)

			# Search for this command implementation in the network.
			try: action = interface[verb]
			except KeyError:
				raise actionable.NotFound(verb)

			# Build the interface-command-specific verb implementation.
			# The action is now an polymorphic instance of the command type.
			return action.implementation(action, command, verb, argstr)


	class command(interpretable):
		def __init__(self, interface):
			interface[self.name] = self

		def parseSubcommandArgs(self, verb, *args, **kwd):
			# Also gives an opportunity to rebind the verb instance.
			return verb.parseArgs(*args, **kwd)

		def __call__(self, verb, actor, *args, **kwd):
			verb = self.parseSubcommandArgs(actor, *args, **kwd)
			return verb(actor, *args, **kwd) # and pass *args, **kwd?


		class verb(network.event):
			def __init__(self, action, command, verb, argstr):
				self.action = action
				self.command = command
				self.verb = verb
				self.argstr = argstr

			def parseArgs(self, *args, **kwd):
				# object, subject, direct object, preposition, etc.
				self.args = self.argstr.split() # shlex.split?
				return self

			def __call__(self, *args, **kwd):
				return self.action(self, *args, **kwd)

			def __str__(self):
				return '<%s: %s>' % (self.__class__.__name__, self.verb)


		class define:
			'''
			@operator
			class interface(action):
				def init(self):
					@actionable.command.define('look', self)
					def lookCommand(actor, verb):
						pass

						'''

			def __init__(self, name, interface = None):
				self.name = name
				self.interface = interface

			def __call__(self, function):
				o = definition(self.name, function)
				i = self.interface

				if i is not None:
					return o(o)

				return o


			class definition:
				def __init__(self, name, function):
					self.name = name
					self.function = function

				def __call__(self, network):
					# Registration.
					return call(classObject(self.name, actionable.command,
											implementation = self.implementation,
											name = self.name), network)

				@property
				def implementation(self):
					from new import instancemethod as bind
					return classObject('implementation', action.command.verb,
									   __call__ = bind(self.run, self))

				def run(self, verb, actor, *args, **kwd):
					return self.function(actor, verb) # Note: rearrangement of pos args.



	# (any source) initiate location change
	#	 start virtual method for begin change
	#	 on completion, perform location transfer
	#	 fire location-transfer event
	#	 on completion of event, call virtual machine for change completion
	#		 or, resume existing task-call as completion.
	#
	# "(any source)" must wait for completion, which means it must pass
	# a callback to location-change routine, or, it must somehow state
	# conditional invariance (?) by asserting control over the operation.
	#
	# transitively atomic operation

	# def resumeVMCall(frame, result):
	# 	from stuphos.kernel import resumeTask
	# 	resumeTask(frame.task, value = result)

	# class chain(list):
	# 	def __init__(self, *functions):
	# 		list.__init__(self, functions)

	# 	def __call__(self, *args, **kwd):
	# 		e = []

	# 		for o in self:
	# 			e = o(*((e,) + arg), **kwd)

	# 		return e


	# class entity:
	# 	def locationChangeComplete(self, frame, location):
	# 		# Stylized as native.
	# 		evCall = deferred(self.events.locationChangeComplete,
	# 						  location = location)

	# 		evCall = chain(evCall, deferred(resumeVMCall, frame))


class delegate(list):
	# Broadcasting listener.
	# todo: verb reactions may be stored on the object, but they're
	# activated by another entity.
	# Note: this is not necessary because of 'network', but the 'invocation'
	# event-dispatch-handling object is useful.
	def __init__(self, object = None):
		self.object = object

	def listen(self, callback):
		self.append(callback)
		return self

	def unlisten(self, callback):
		self.remove(callback)
		return self

	def __call__(self, *args, **kwd):
		return self.invocation(self).dispatch(*args, **kwd)

	class invocation(list):
		# todo: derive from chain?
		def __init__(self, event):
			self.event = event

		def dispatch(self, *args, **kwd):
			for callback in self:
				self.append(self.dispatchOne(callback, *args, **kwd))

			return self

		def dispatchOne(self, callback, *args, **kwd):
			return callback(self, *args, **kwd)



class collection(list):
	# @operator
	# class collection(list):
	# 	pass

	# class entities(collection):
	# 	pass

	def __init__(self, object):
		self.object = object

	def mapIterator(self, function, *args, **kwd):
		for i in self:
			yield function(i, *args, **kwd) # pass self?
	each = mapIterator
	# map = listing(each)

	def find(self, function):
		for i in self:
			if function(i):
				yield i

	def __iadd__(self, objects):
		self.extend(objects)
		return self
	__add__ = __iadd__


	@classmethod
	def component(self, object):
		# Bind this class derivation to property derivation.
		# Return a property object accessing this class derivation.
		i = subClass(object.propertyClass,
					 collectionClass = object) # XXX shouldn't this be self?

		object.propertyImpl = i
		return i(object.__name__)

	class propertyClass(property):
		def __init__(self, name):
			self.name = name

		def __getitem__(self, object):
			name = '__%s' % self.name
			try: return getattr(object, name)
			except AttributeError:
				c = self.collectionClass(object)
				setattr(object, name, c)
				return c

		def __get__(self, object, closure):
			return self[object]
		def __set__(self, object, value):
			pass


def setAttribute(object, name, attrClass, *args, **kwd):
	try: return getattr(object, name)
	except AttributeError:
		i = attrClass(*args, **kwd)
		setattr(object, name, i)
		return i


class inheritable:
	# Noticeably, this doesn't do much but implement spherical(), search(), and extend shell (and namespace).
	# It shares a hierarchy like that of network.

	def spherical(self, name):
		# Relative attribute.
		try: return getattr(self, name)
		except AttributeError as e:
			if self.location is None:
				raise e

			return self.sphere.spherical(name)


	@property
	def containerization(self):
		s = self

		while s is not None:
			yield s

			try: s = s.sphere
			except AttributeError:
				break


	@property
	def outermost(self):
		s = self

		try:
			while True:
				s = s.sphere

		except AttributeError:
			pass

		return s


	def search(self, callable):
		if isinstance(callable, str):
			def callable(e, name = callable):
				return e.name == name

		for e in self.entities:
			if callable(e):
				yield e


	# todo: what about an 'inheritable' network interface -- manifold?
	# this already kind of exists because of network layering: bind a
	# new network layer, and then access its 'source' property:
	#
	# class object:
	#     'object().interface.extension["source"](...)'

	#     @operator
	#     class interface(network):
	#         @operator
	#         class extension(network):
	#             def init(self):
	#                 # In case anyone cares.. map the item to the interface.
	#                 self.object['source'] = self.source.interface
	#                 self += self.callback

	#                 # Install a new view on the original object.
	#                 self.action = self.behavior(self.source)

	#             class behavior(network):
	#             	'object().interface.extension.action("say Performing command!")'

	#             	def __call__(self, *args, **kwd):
	#             		# Bound to the original source object.
	#             		self.object.interpretCommand(*args, **kwd)

	#             def callback(self, *args, **kwd):
	#                 pass


class graph(list):
	# An interactive view -- an object API.
	# see network

	# This generalizes function call values based on its arguments,
	# which can be either dynamic (programmatic) or simplistic
	# (attribute or index resolution).

	def __init__(self, object):
		self.object = object
		self.namespace = dict()


	class resolution:
		'''
		Formulates a graph lookup by providing a description framework.
		A resolution is a context-sensitive operation defined by the descriptor.

		'''

		def __init__(self, graph):
			self.graph = graph


		class edge:
			pass
		class link(edge):
			pass

		class descriptor(link):
			'Knows how to look up a value in a graph based on another value.'

			# Different interface types:
			#   an object with member methods
			#   an object with members that point to callable objects
			#   an object with members that have members that point to methods
			#   an object with indices that are callable
			#   an object with operators
			#   ...

			def __init__(self, value):
				self.value = value

			@contextmanager
			def __call__(self, graph):
				yield self[graph]

		class string(descriptor):
			def __getitem__(self, graph):
				return graph.namespace[self.value]

		class index(descriptor):
			def __getitem__(self, graph):
				try: return graph.namespace[self.value]
				except KeyError:
					return graph[self.value]

		class sequence(descriptor):
			def __getitem__(self, graph):
				raise NotImplementedError

		def __getitem__(self, o):
			'Maps a description to a graph-resolution operation.'

			if isinstance(o, str):
				return self.string(o)
			if isinstance(o, int):
				return self.index(o)
			if isinstance(o, (list, tuple)):
				return self.sequence(o)

			return o

		class NotFound(KeyError):
			def __init__(self, graph, descriptor):
				self.graph = graph
				self.descriptor = descriptor

		def __getitem__(self, descriptor):
			'Determine graph action lookup method based on description.'

			method = self[descriptor](self.graph)
			if callable(method):
				return method

			raise self.NotFound(self.graph, descriptor)


	def resolve(self, descriptor):
		# A graph could just implement this method to do a simple action lookup.
		# Or, you could implement a more complex resolution description:
		#
		# @apply
		# class lookup(graph.resolution.descriptor):
		#     def __getitem__(self, graph):
		#         return graph(['path', 'to', 'resource', 'method'])
		#
		# i.graph(lookup())

		return self.resolution(self)[descriptor]

	def __call__(self, descriptor, *args, **kwd):
		with self.resolve(descriptor) as method:
			return method(self.object, *args, **kwd)
