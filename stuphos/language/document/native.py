from stuphos.runtime.architecture import extensionObject
from ph.interpreter.mental.native import _safe_native

from stuphos.language.document.structural import parseStructuredMessage as parseMessage, StructuredEncoding

from stuphos.kernel import vmNewSequence

from json import dumps as toJsonString

__all__ = ['parseWm', 'typeWm', 'itemsWm']


class BuildingWMNode(extensionObject):
	@property
	def name(self):
		return self._object.name

	@property
	def typeName(self):
		return self._object.typeName

	@property
	def subtype(self):
		return self._object.subtype

	@property
	def value(self):
		# XXX What's wrap supposed to be?
		return BuildingWM.wrap(self._object.value)


	def data(self, value = True):
		yield self.name
		yield self.typeName
		yield self.subtype

		if value:
			yield self.value

	def __iter__(self):
		return self.data(False)


	@property
	def definition(self):
		name = self.name
		name = toJsonString(name) if ('"' in name or "'" in name) else name

		typeName = self.typeName
		subtype = self.subtype

		if typeName:
			defn = f'({typeName}${subtype or ""})'
		elif subtype:
			defn = f'({subtype})'
		else:
			defn = ''

		return name + defn

	def __repr__(self):
		return f'<building {self.definition}>'


class BuildingWM(extensionObject):
	_parseMessage = parseMessage
	_buildingClass = StructuredEncoding.ClassMap.Building
	_buildingNodeClass = BuildingWMNode


	@classmethod
	def _parse(self, source, *args, **kwd):
		return self(self._parseMessage \
			(source, *args, **kwd))


	@property
	def _value(self):
		o = self._object
		return o.value if isinstance(o, self._buildingClass) else o


	def __len__(self):
		return len(self._value)
	def __str__(self):
		return str(self._value)

	def __iter__(self):
		o = self._value

		if isinstance(o, dict):
			return iter(vmNewSequence(o.keys()))

		return iter(o)

	def __getitem__(self, item):
		return self.__class__(self._value[item])

	def __getattr__(self, name):
		try: return object.__getattribute__(self, name)
		except AttributeError as e:
			try: return self[name]
			except (TypeError, KeyError):
				raise e

	def __call__(self):
		if isinstance(self._object, self._buildingClass):
			return self._buildingNodeClass(self._object)

		raise TypeError(self._object.__class__)
	building = property(__call__)


@_safe_native
def parseWm(frame, source, *args, **kwd):
	source = 'WMC []\n\n' + str.__str__(source)
	return BuildingWM._parse(source, *args, **kwd)


@_safe_native
def typeWm(frame, node, default = None):
	if isinstance(node._object, BuildingWM._buildingClass) or \
		isinstance(node._object, BuildingWMNode):
		return 'building'

	if not isinstance(node, BuildingWM):
		raise TypeError(node.__class__)

	if isinstance(node._object, dict):
		return 'mapping'
	if isinstance(node._object, (list, tuple)):
		return 'sequence'
	if isinstance(node._object, str):
		return 'string'
	if isinstance(node._object, None):
		return 'none'
	if isinstance(node._object, bool):
		return 'bool'
	if isinstance(node._object, (int, float)):
		return 'number'

	return default

@_safe_native
def itemsWm(frame, node):
	if not isinstance(node, BuildingWM):
		raise TypeError(node.__class__)

	if not isinstance(node._object, dict):
		raise ValueError(node._object)

	return frame.task.sequence(node._object.items())
