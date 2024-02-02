# mud.lang.structure
# from op.runtime.structural import document as _document
from . import structural as _document
getContextVariable = _document.Context.__getitem__

from stuphos.kernel import Machine as VM, getLibraryCore, vmCurrentTask


# Classes.
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


# Context.
def getContextEnvironment(name, **kwd):
    loader = getContextVariable('loader')

    try: default = kwd['default']
    except KeyError:
        return loader.environ[name]
    else:
        return loader.environ.get(name, default)


# Cache.
from stuphos.runtime.architecture import writeprotected

class documentCache:
    # _refCache = dict()
    _docCacheName = 'cache'


    class miss(Exception):
        pass

    @classmethod
    def instanceOf(self, i):
        return isinstance(i, self)


    def _docCache(self, doc): 
        return getattr(doc, self._docCacheName, None)

    def docSetCache(self, doc, *args, **kwd):
        cache = self._docCache(doc)
        return cache.setCache(doc, *args, **kwd) \
            if self.instanceOf(cache) else doc


    def __init__(self, value, cache = None):
        self.value = value

        if cache is not None:
            self._refCache = cache


class pathCache:
    # Library Model.
    _refCache = dict()

    def __init__(self, docpath = None):
        self._docpath = docpath


    class _nodeCacheClass:
        def __setitem__(self, node, doc):
            node.structure = doc
        def __getitem__(self, node):
            try: return node.structure
            except AttributeError:
                raise KeyError

    _nodeCache = _nodeCacheClass()


    def _assert_docpath(self):
        if not self._docpath:
            raise ValueError(f'no document source')

    def loadCache(self, *args, **kwd): # source, classes, defaultName, **kwd):
        self._assert_docpath()

        try: return self._refCache[self._docpath]
        except KeyError:
            raise self.miss

    def setCache(self, doc, *args, **kwd): # source, classes, defaultName, **kwd):
        self._assert_docpath()

        self._refCache[self._docpath] = doc

        return doc

    def clearCache(self):
        self._assert_docpath()

        del self._refCache[self._docpath]


class loadCache_methodClass:
    # Requires pathCache (docpath)

    # API isolation.
    _methodCache = dict()


    @classmethod
    def load(self, *args, **kwd):
        # Nonstructural
        '''
        documentCache.load('{}', docCache = 'cache-key-name-1')

        '''

        return load(*args, **dict
            (kwd, cache = self
                (kwd.pop('cacheArg', None),
                 cache = self._methodCache,
                 docpath = kwd.pop
                    ('docCache', None))))


class structuralCache:
    # Requires pathCache (nodeCache)

    @classmethod
    def _FromNodeStructure(self, name, value, **kwd):
        if value not in [None, False, '']:
            node = getContextEnvironment('document')
            if node is not None:
                return self(value, getLibraryCore
                    (vmCurrentTask())[node],
                    cache = self._nodeCache)

    @classmethod
    def _FromStructure(self, name, value, **kwd):
        '''
        cache = documentCache._FromStructure


        cache(cache): true


        clear(view):
            context(trigger)::
                is$deep$view(path) and \
                    container.pathClear \
                        ('/'.join(path))

        pathClear(method)::
            cache = documentCache._docCache \
                (structure(path))

            if documentCache.instanceOf(cache):
                cache.clearCache()

        '''

        if value not in [None, False, '']:
            return self(value, getContextEnvironment('document'))


    def __init__(self, value):
        self.value = value


class pathLibraryStructureCache \
    (writeprotected, documentCache,
     loadCache_methodClass,
     pathCache, structuralCache):

    def __init__(self, value, docpath = None, cache = None):
        documentCache.__init__(self, value, cache = cache)
        # structuralCache.__init__(self, value)
        pathCache.__init__(self, docpath = docpath)


# Build Algorithm.
def load(source, classes, defaultName, **kwd):
    # Build parse environment.
    source = source.replace('\r', '') # scrub from any source.
    # source = 'Westmetal Configuration::\n\n' + source
    source = 'WMC []\n\n' + source

    classes = systemClassAdjust(classes)


    # Cache search phase.
    # post = kwd.pop('post', False) # borrow
    cache = kwd.pop('cache', False) # borrow

    if documentCache.instanceOf(cache):
        try: return cache.loadCache(source, classes, defaultName, **kwd)
        except cache.miss: pass


    # debugOn()
    try: doc = _document.loadStructuredMessageFromClasses \
                 (source, classes, raw = True,
                  default = defaultName, **kwd)

    except VM.Yield as e:
        # Don't propogate continuations because the document load will be
        # replaced by the yielding factory load, which might be confusing.
        raise RuntimeError('Incompatible continuation stack!') from e

    else:
        # if post:
        #   # doc = post(doc)
        #   return post(doc)

        # Cache phase.
        if documentCache.instanceOf(cache):
            return cache.docSetCache(doc, source, classes, defaultName, **kwd)

        return doc


# Factories.
from stuphos.structure import Factory, SystemFactory, HTMLFactory

def getFactories(**kwd):
    yield 'stuph', Factory

    from stuphos import getConfig
    from stuphos.etc import isYesValue

    if isYesValue(getConfig('converge-spatial')):
        from spatial.spherical import structure as spatial
        yield 'world', spatial.Factory

    for (name, value) in kwd.items():
        if isinstance(value, Factory):
            yield (name, value)

def document(source, **kwd):
    # A raw load skips installation of core factory classes, so we
    # can create a controlled, discriminatory environment.
    # Auto WMC
    #import pdb; pdb.set_trace()
    return load(source, dict(getFactories(**kwd.pop('classes', dict()))), 'stuph', **kwd)

def html(source, **kwd):
    return load(source, dict(getFactories(**kwd.pop('classes', dict())), html = HTMLFactory), 'html', **kwd)


def system(source, **kwd):
    return load(source, dict(system = SystemFactory), 'system', **kwd)

def resource(base, path, *names):
    base = io.path(base).folder(*path)
    return access(document(base.read()), *names)
