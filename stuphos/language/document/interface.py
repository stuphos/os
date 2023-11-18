# mud.lang.structure
# from op.runtime.structural import document as _document
from . import structural as _document
getContextVariable = _document.Context.__getitem__

from stuphos.kernel import Machine as VM


def docClasses():
	return (getattr(configuration, \
		configuration.MUD.document_class or '', \
		None).system_classes or '').split('\n')

def classAssignment(cls):
	r = cls.split('=', 1)
	if len(r) == 2:
		return r

	return [r, None]

def assignClasses(classes):
	return (classAssignment(cls)
			for cls in classes)

def factoryClasses(classes):
	from stuphos.runtime.architecture import LookupObject
	return [(name, LookupObject(factory))
			for (name, factory) in classes
			if name and factory]

def defaultSystemClasses():
	return factoryClasses \
		(assignClasses(docClasses()))

def setSystemClasses(classes):
	'''
	# -f scripts/install-object.ela stuphos.language.document.interface.setSystemClasses.__doc__ gen/kernel/language

	def setSystemDocumentClasses():
		scatter$args(['classes', none])
		if is$none(classes):
			classes = keywords$().items()
		else:
			classes = factoryClasses(assignClasses(classes))

		return run$python(code, mapping \
			(classes = classes)) <- code:

			for cls in classes:
				setSystemClasses(insertSystemClass \
					(getSystemClasses(), cls))


		usage:
			setSystemClasses(['packaged=package.structure.Factory'])

			return wm.value[''] <- wm:
				(packaged$method): null

	'''

	global _systemClasses
	_systemClasses = classes

	return classes

def insertSystemClass(classes, input):
	(name, factory) = classAssignment(input) \
		if isinstance(input, str) else input

	for search in classes:
		if search[0] == name:
			break
	else:
		classes.append(input)

	return classes

def deleteSystemClass(classes, name):
	for cls in classes:
		if cls[0] == name:
			classes.remove(cls)

	return classes

def getSystemClasses(default = defaultSystemClasses):
	try: return _systemClasses
	except NameError:
		return setSystemClasses(default())

def systemClassAdjust(classes):
	for sc in getSystemClasses():
		if sc not in classes:
			classes.append(sc)

	return classes


def getContextEnvironment(name, **kwd):
	loader = getContextVariable('loader')

	try: default = kwd['default']
	except KeyError:
		return loader.environ[name]
	else:
		return loader.environ.get(name, default)

from stuphos.structure import Factory, SystemFactory, HTMLFactory

def load(source, classes, defaultName, **kwd):
	source = source.replace('\r', '') # scrub from any source.
	# source = 'Westmetal Configuration::\n\n' + source
	source = 'WMC []\n\n' + source

	classes = systemClassAdjust(classes)

	# debugOn()
	try: return _document.loadStructuredMessageFromClasses \
				 (source, classes, raw = True,
				  default = defaultName, **kwd)

	except VM.Yield as e:
		# Don't propogate continuations because the document load will be
		# replaced by the yielding factory load, which might be confusing.
		raise RuntimeError('Incompatible continuation stack!') from e


def getFactories():
	yield 'stuph', Factory

	from stuphos import getConfig
	from stuphos.etc import isYesValue

	if isYesValue(getConfig('converge-spatial')):
		from spatial.spherical import structure as spatial
		yield 'world', spatial.Factory

def document(source, **kwd):
	# A raw load skips installation of core factory classes, so we
	# can create a controlled, discriminatory environment.
	# Auto WMC
	#import pdb; pdb.set_trace()
	return load(source, dict(getFactories()), 'stuph', **kwd)

def html(source, **kwd):
	return load(source, dict(getFactories(), html = HTMLFactory), 'html', **kwd)

def system(source, **kwd):
	return load(source, dict(system = SystemFactory), 'system', **kwd)

def resource(base, path, *names):
	base = io.path(base).folder(*path)
	return access(document(base.read()), *names)
