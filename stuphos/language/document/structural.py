# From WRLC
# Typed Yaml -- Revelations 7-12
# Copyright 2021 runphase.com .  All rights reserved
#  
# Notes:
#   OrderedDict? (omap)
#   Raw? :: or : | -> convert :: to : |? What about the indentation?
# #include "fs/supplemental.struct"

# Todo: decorator (attribute) syntax for yaml constructs:
#   This could be pre-parsed by 'extended yaml' and inserted into
#   the Loading message map, programming the headers to hold the
#   information, associated with the 'path' down to the structural
#   element, before it is carried down by the building algorithm
#   (by path) and applied to the item.

from pprint import pprint as pp
from email import message_from_string
from types import ModuleType
from types import new_class as newClassObject, new_class as ClassType

TypeType = type

import json
import re


from .wrlc import *


# from common.runtime.functional.routines import stepAroundBuiltins

# Relies on data.formats, relying on Structr
#from common.platform.filesystem import FilePoints

RegularExpressionType = type(re.compile(r''))

# Dependency: path relies on data/formats, which relies on this module..
def isPathType(object):
    return isinstance(object, getPathType())

# Interestingly, we rely pretty heavily on yaml here, but really it's the only dependency.
# (Oh yeah, mime. json)
try: from yaml import load as loadYaml, SafeLoader # safe_load? load_all?
except ImportError as e: loadYaml = e

if 0:
    # Structural Loader.
    from yaml import SafeLoader as Loader

    PENRO_MAPPING_TAG = 'tag:penrolabs.org,2013:omap'
                      # u'tag:yaml.org,2002:map'

    class ConstructedOrderedMap(dict):
        def __init__(self, *args, **kwd):
            # todo: load args sequentially..
            dict.__init__(*args, **kwd)
            self.__sequencing = []

        def __iter__(self):
            return iter(self.__sequencing)

        def load(self, sequence):
            for (name, value) in sequence:
                self[name] = value
                self.__sequencing = name # shouldn't this be append??

    class StructuralLoader(Loader):
        DEFAULT_MAPPING_TAG = PENRO_MAPPING_TAG

        def construct_penro_omap(self, node):
            i = self.construct_yaml_omap(node)
            omap = ConstructedOrderedMap()

            yield omap

            pairs = first(i)
            eat(i)

            omap.load(pairs)

        # Implementation of SafeConstructor.construct_yaml_omap
        ##    def construct_yaml_omap(self, node):
        ##        # Note: we do not check for duplicate keys, because it's too
        ##        # CPU-expensive.
        ##        omap = []
        ##        yield omap
        ##        if not isinstance(node, SequenceNode):
        ##            raise ConstructorError("while constructing an ordered map", node.start_mark,
        ##                    "expected a sequence, but found %s" % node.id, node.start_mark)
        ##        for subnode in node.value:
        ##            if not isinstance(subnode, MappingNode):
        ##                raise ConstructorError("while constructing an ordered map", node.start_mark,
        ##                        "expected a mapping of length 1, but found %s" % subnode.id,
        ##                        subnode.start_mark)
        ##            if len(subnode.value) != 1:
        ##                raise ConstructorError("while constructing an ordered map", node.start_mark,
        ##                        "expected a single mapping item, but found %d items" % len(subnode.value),
        ##                        subnode.start_mark)
        ##            key_node, value_node = subnode.value[0]
        ##            key = self.construct_object(key_node)
        ##            value = self.construct_object(value_node)
        ##            omap.append((key, value))

        @classmethod
        def LoadDocument(self, stream):
            loader = self(stream)
            return loader.get_single_data()

    StructuralLoader.add_constructor \
        (PENRO_MAPPING_TAG, StructuralLoader \
         .construct_penro_omap)

    loadYaml = StructuralLoader.LoadDocument


WMC_PROLOG = 'Westmetal Configuration::'

def multilineLiteral(lines, start, end):
    # Dedent.
    i = indentOf(lines[start])
    for x in range(start, end):
        lines[x] = lines[x][i:]

    def _():
        for e in lines[start:end]:
            yield e

        yield ''

    def escape(s):
        s = s.replace('\\', '\\\\')
        # s = s.replace("'", '\\047')
        s = s.replace('"', '\\"') # '\\042')
        return s

    literal = list(map(escape, _()))
    literal = '\\n'.join(literal)
    literal = '"%s"' % literal

    return literal

def ConvertMultilineSyntax(source, rebuild):
    # XXX Unfortunately, this clashes with reStructuredText format
    # (which could possibly be embedded within the document)

    # todo: use iterLineSegments?

    # XXX puts everything under view, cutting off first two characters of all lines after:
    # - view(method)::
    #     return doc.default$document$view

    #   caption: default

    # Allow extended blocks::
    lines = source.split('\n')

    def findings():
        i = None
        start = 0

        for (x, n) in enumerate(lines):
            # todo: look at the next line, use its indentation level.
            # yield this indentation level and dedent with it instead
            # of re-calculating it in multilineLiteral.
            if i is None:
                if n.endswith('::'):
                    i = indentOf(n)
                    start = x

            # Allow blank lines in this block.
            elif n.strip():
                nI = indentOf(n)
                if nI <= i:
                    # Need to scan each line in block to see when we're out.
                    yield (start, x)
                    if n.endswith('::'):
                        i = nI
                        start = x
                    else:
                        i = None

        if i is not None:
            yield (start, x)

    def blockOf(array, k, p):
        for e in array[k:p]:
            yield e

    def reconstructing():
        alpha = 0
        for (start, end) in findings():
            if alpha < start:
                yield '\n'.join(blockOf(lines, alpha, start))

            # Reconstruct this block.
            f = lines[start]
            lines[start+1:end]

            dedentBy(lines, indentOf(f), start, end)
            f = f[:-1] # Chop off ':' # XXX Need to account for non-':' formats.
            yield rebuild(f, lines, start + 1, end)

            alpha = end

        if alpha < len(lines):
            yield '\n'.join(blockOf(lines, alpha, len(lines)))

        yield ''

    return '\n'.join(reconstructing())

def rebuildYamlMultiline(directive, linesArray, start, end):
    return '%s %s' % (directive, multilineLiteral(linesArray, start, end))

def convertExtendedYaml(source):
    return ConvertMultilineSyntax(source, rebuildYamlMultiline)

def parseExtendedYaml(source):
    source = convertExtendedYaml(source)
    return loadYaml(source, Loader = SafeLoader)

##    class Cloning:
##        def __init__(derived, base, *names):
##            for n in names:
##                n = '__%s__' % n
##                setattr(derived, n, getattr(base, n))
##
##    class Item(Cloning):
##        def __init__(self, object):
##            Cloning.__init__(self, object, 'repr', 'str', 'setitem', 'getitem', 'iter')
##            self.__dict__ = object

##    class Item:
##        def __init__(self, object):
##            self.__dict__ = object
##        def __repr__(self):
##            return repr(self.__dict__)
##        def __getitem__(self, name):
##            return self.__dict__[name]
##        def __setitem__(self, name, value):
##            self.__dict__[name] = value
##        def __iter__(self):
##            return iter(self.__dict__)

# Hmm, what about these:
#    name(type[and attributes for type, example=value])
#    name[type(arg1, arg2, kwd1 = value)]
#    name[type(tags, for, this, type)]
#

# $ -> %?
# name(type$sub@param=value@param=value)
TYPE_PATTERN = r'^([^()]*)' + \
               r'(?:\(([^$()]*)' + \
               r'(?:\$?([^()]*))\))$'

TYPE_PATTERN = re.compile(TYPE_PATTERN)
TYPE_PATTERN_MATCH = TYPE_PATTERN.match

def parseTypeDecl(decl):
    '''
    def map$type(factory, v):
        if is$list(v):
            return sequence(map(map$type.action(factory), v))

        if is$mapping(v):
            return mapping(sequence(map \
                (map$type$item.action(factory), \
                 v.items())))

        return v

    def map$type$item(factory, kv):
        scatter(kv, 'name', 'value')
        scatter('kernel/callObject$' \
            ('stuphos.language.document.structural.parseTypeDecl', \
             name), 'name', 'typeName', 'subtype')

        if typeName: # and subtype
            return factory(typeName, subtype, name, value)

        return [name, value]


    def factory$doc(api, typeName, subtype, name, value):
        return [name, api[typeName][subtype](name, value)]

    def factory$map$type(api):
        return map$type.action(factory$doc.action(api))

        usage:
            factory$map$type(api.value)(data.value) <- api:
                '':
                    identity(method)::
                        scatter$args('name', 'value')
                        return mapping(name = name, value = value)

            <- data:
                (identity):
                    []

            {'': {'name': '', 'value': []}}


    def doc$identity(typeName, subtype, name, value):
        return [name, (not typeName and subtype == 'identity') \
            and mapping(name = name, value = value) or value]

        usage:
            map$type(doc$identity, mapping(['(identity)', []]))


    def submapping$(submapping):
        return mapping([keywords$('name', ''), submapping])
    def singlemap$(name, value):
        return submapping$(value, name = name)

    def identity$(name, value):
        return mapping(name = name, value = value)

    def singletype$(name, build):
        return act(submapping$, [submapping$(build, \
            name = name)], keywords$())

        usage:
            map$type(singletype$('identity', identity$), \
                singlemap$('(identity)', [])) \

            <- identity:
                return mapping(name = name, value = value)

    '''

    try: m = TYPE_PATTERN_MATCH(decl)
    except TypeError as e:
        # Hmm, internal building error:
        #   XXX this may be because the YAML produced a numeral-typed key.
        raise TypeError('%s: %r' % (e.message, decl))

    if m is None:
        return (decl, '', '')
        raise SyntaxError(decl)

    (name, typeName, subtype) = m.groups()
    if not subtype:
        subtype = typeName
        typeName = '' # default

    return (name, typeName, subtype)

    # return m.groups()

# Todo: general tree visitation.
# XXX This is kind of a mess because it should be all integrated into building/loading alog.
def flatten(x, buildingClass = None):
    # Err, toplevel..
    if buildingClass is None:
        buildingClass = StructuredEncoding.ClassMap.Building

    def f(v):
        # hmm, buildingClass here?
        return v.flatten() if isinstance(v, buildingClass) else v

    if isinstance(x, dict):
        i = list(x.items())
        x.clear()

        for (n, v) in i:
            x[n] = f(v)

    elif isinstance(x, list):
        x = list(map(f, x))
    elif isinstance(x, tuple):
        x = tuple(f(n) for n in x)

    return x


def _findAutomapped(module):
    # Find auto-mapped objects.
    # The marker for a submappable object is that it has a FromStructure method.
    # __automap__ can be used to explicitly set the name.
    for (name, object) in iteritems(dictOf(module)):
        try: name = getattr(object, '__automap__', name)
        except AttributeError: pass
        else:
            if hasattr(object, 'FromStructure'):
                yield (name, object)

def _newAutomappedFactory(mapping, name = None):
    if mapping:
        if not name:
            name = mapping['__name__'].split('.')
            name = camelize(*name) + 'AutomappedFactory'

        return create.type(name, Submapping, **mapping)

def loadFactory(module, name = None):
    try: return module.Factory
    except AttributeError: pass

    return _newAutomappedFactory(dict(_findAutomapped(module)),
                                 name = nameOf(module) if name \
                                        is None else name)


# Yaml provides YAMLObject, which makes for pickle serialization.
class Yamllike:
    @classmethod
    def FromStructure(self, name, value, **kwd):
        this = self.__new__()
        this.__setstate__(value)
        return this

    @classmethod
    def Type(self, name):
        return create.type('%s$%s' % (name, nameOf(self)),
                           self, __automap__ = name)

# This goes one step further, exposing named types as subclass (which is how it belongs).
#Yamllike.Named = attributable(Yamllike.Type)
#yamllike = picklike = serialike = Yamllike.Named

##    builtin(yamllike = yamllike,
##            picklike = picklike,
##            serialike = serialike)

# from common.runtime.structural.document import serialike

##    class Features(serialike.features):
##        def __setstate__(self, state):
##            self.__init__(state['styles'],
##                          state['features'])


class StructuredEncoding:
    # Objects??
    class ItemClass: # (an item factory base class)
        # Todo: upgrade this runtime representation:
        # What about serialization? fq class name.
        # Todo: this needs to consist more like 'Synthetic', sharing the dictionary
        # given to it, whilst exposing items as attributes.  My only question is
        # whether or not it must subclass dict.  So, reconcile Namespace-Synthetic,
        # or at least provide a similar enough situation here because this part of
        # the building process does array copies thereby losing association with
        # internal structural element products.
        class Item(Namespace):
            ##    def __init__(self, object):
            ##        dict.__init__(self, object)
            ##        self.__dict__ = self

            def __repr__(self):
                return '<%s: %s>' % (self.__class__.__name__,
                                     ', '.join(list(self.keys())))

            def __str__(self):
                return json.dumps(self, indent = 1, default = lambda o: None)

        # Factory.
        def buildItem(self, loader, subtype, name, value, **kwd):
            # Todo: subclass this in order to instantiate the type.

            # Basically this is recursive Namespace.FromStructure..
            # return self.Item.FromStructure(value) # but only for dict..

            if isinstance(value, dict):
                # Note: executing in 'container' (for builtins) and using recursive FromStructure after isn't a good idea.
                # Todo: make Item.FromStructure more resistant to this.

                return self.Item.FromStructure(value)

                # XXX :skip: Get rid of the runtime-error checking
                ##    try: return self.Item.FromStructure(value)
                ##    except RuntimeError:
                ##        builtin(_ = value)
                ##        raise

                return self.Item(value)

                ##    return self.Item(dict((n, self.buildItem \
                ##                           (loader, None, n, v, **kwd))
                ##                          for (n, v) in value.iteritems()))

                # XXX :skip: I don't see why this should _ever_ happen from here.
                # This recursion should be happening in the Building class.
                #
                # I think this is the strategy for yielding an Item, but,
                # as presented above, we should do this recursion here.

                # The reason is because this is the indirect recursion method
                # for building through lists of typed items -- allowing a depth-
                # first approach to building (using runtime stack only).
                # return self.Item(loader.classes.buildTypedItemMap(loader, value))

            # For item-constructing purposes, not sure if this is exactly what I want.
            # Not even sure this needs to be done..
            ##    elif isinstance(value, tuple):
            ##        return tuple(self.buildItem(loader, None, None, v, **kwd)
            ##                     for v in value)
            ##
            ##    elif isinstance(value, list):
            ##        return [self.buildItem(loader, None, None, v, **kwd)
            ##                for v in value]

            ##    if isinstance(value, (list, tuple)):
            ##        # Top-level type-mapping routine determines resulting type.
            ##        return [self.buildItem(loader, None, None, v, **kwd)
            ##                for v in value]
            ##
            ##        # XXX :skip: I don't see why this should _ever_ happen from here.
            ##        # This recursion should be happening in the Building class.
            ##        return [loader.classes.buildTypedItemMap(loader, v)
            ##                for v in value]

            return value
            return self.SUBTYPES[subtype].buildItem(loader, name, value, **kwd)
                # ^ Not implemented

    class ClassMap(dict):
        @classmethod
        def loadCore(self, this):
            this.update(CORE_CLASSES)

        # What if the package isn't loaded yet?  (or available because it's
        # defined in another structure).  Then, make loadStructure/Factory
        # store a promise (or something like StructuredEncoding.FactoryBase
        # for Impl).
        #
        # Todo: how to load factory mappings from _this_ document?
        # Some kind of syntax in 'name'?
        def loadStructure(self, name):
            # Load the factory -- a specific symbol within the named structure module.
            # return self[self.default]

            classModule = LookupObject(name) # __import__(name, fromlist = [''])
            baseClass = loadFactory(classModule)

            return self.loadFactory(name, baseClass)

        def loadFactory(self, name, baseClass):
            if isinstance(baseClass, list): # todo: or tuple?
                return MultipleSubmapping \
                    (self.loadFactory(*args)
                     for args in baseClass)

            if isinstance(baseClass, dict):
                # baseClass = dict((name, classmethod(value)) for (name, value) in baseClass.iteritems())
                baseClass = ClassType('baseMapping', (Submapping,), baseClass)

            factoryClass = ClassType(name + 'Impl', (baseClass, StructuredEncoding.ItemClass), dict())
            factoryClass.ItemClassBase = StructuredEncoding.ItemClass

            return factoryClass()

        @classmethod
        def FromClasses(self, classes, default = None):
            map = self((), default = default)
            for (prefix, factory) in classes.items():
                map[prefix] = map.loadFactory(prefix, factory)

            return map

        def __init__(self, classes, default = None, resolve = True):
            self.loadCore(self)
            self.default = default or DEFAULT_PREFIX

            for cls in classes:
                (prefix, object) = splitOne(cls, '=')
                prefix = prefix.strip()
                object = object.strip()
                if prefix and object:
                    if resolve: # for flat parses
                        object = self.loadStructure(object)

                    self[prefix] = object

        def getType(self, name, **kwd):
            try: return self[name or self.default]
            except KeyError as e:
                try: return kwd['default']
                except KeyError:
                    raise e

        @Object.Format('{name}({typeName}${subtype})')
        class Building(Object):
            def __init__(self, xxx_todo_changeme1,
                         typeClass,
                         value):

                (name, typeName, subtype) = xxx_todo_changeme1
                self.name = name
                self.typeName = typeName
                self.subtype = subtype

                self.typeClass = typeClass
                self.value = value

            def getAttributeString(self):
                if self.subtype: # or typeName-significant?
                    if self.typeName:
                        return '%s(%s$%s)' % (self.name, self.typeName, self.subtype)

                    return '%s(%s)' % (self.name, self.subtype)

                return self.name

            # Hmm, as a wrapper over value..?
            # Note: so far, the only reason I can see doing this is to make us compatible with search..
            # Note sure if it'll allow rest of structural document system to work, though.
            ##    def __getitem__(self, item):
            ##        return self.value[item]
            ##    def __len__(self):
            ##        return len(self.value)
            ##    def __iter__(self):
            ##        return iter(self.value)


            # todo: emulate aggregate components at this-object level to inhibit indentation.
            def toStringBuffer(self, buf = None):
                buf = Indent.Buffer.Get(buf)

                def writeIndentedString(s):
                    buf.write(indent(s, tab = (buf.tab.level + 1) * buf.tab.amount))
                def writeString(s, n = None):
                    if '\n' in s:
                        if n:
                            # XXX the extended parser is missing :: cases (thinks the key name ends with ':')
                            # Todo: ::
                            buf.indent('%s:' % n)
                            writeIndentedString(s)
                        else:
                            writeIndentedString(s)

                        buf.write('\n')
                    elif n:
                        buf.indent('%s: %r' % (n, s))
                    else:
                        buf.indent(repr(s))

                if isinstance(self.value, str):
                    writeString(self.value, self.getAttributeString())

                # todo: multi-leveled 'o'
                else:
                    buf.indent('%s:' % self.getAttributeString())

                    def o(x):
                        # Hmm, this looks alot like emitting yaml (but sensitive with the building structure)
                        if isinstance(x, classOf(self)):
                            with buf:
                                x.toStringBuffer(buf)

                        elif isinstance(x, dict):
                            for (n, v) in x.items():
                                # buf.write('%s%s: ' % (buf.tab, n))
                                if isinstance(v, classOf(self)):
                                    o(v)

                                elif isinstance(v, str):
                                    writeString(v, n)
                                else:
                                    buf.indent('%s: ' % n)

                                    with buf:
                                        o(v)

                        elif isinstance(x, (list, tuple)):
                            with buf:
                                for v in x:
                                    # buf.write('%s- ' % (buf.tab,))
                                    buf.indent('- ')

                                    o(v) # hmm, more introspection here...

                        elif isinstance(x, str):
                            # paragraphIndent (by plus one)
                            writeString(x)

                        else: # some other type...
                            # print >> buf, repr(x)
                            with buf:
                                buf.indent(repr(x))

                            buf.write('\n')

                    o(self.value)

                return buf

                # todo: walk down the building value (duh) for recursive/indented print.
                # return '%s:\n%s' % (self.getAttributeString(), indent(str(self.value)))

            def toString(self):
                return self.toStringBuffer().getvalue()
            __str__ = toString

            def build(self, loader, **kwd):
                return self.typeClass.buildItem(loader, self.subtype, self.name, self.value,
                                                **kwd)

            __call__ = build

            def buildAsync(self, loader, object, name, build, **kwd):
                return self.typeClass.buildItemAsync(self, loader, object, name, build, **kwd)

            def flatten(self):
                return flatten(self.value, self.__class__)

        def parseTypedItems(self, loader, object):
            # Simply extract the typed items structure: do not load/build.

            # Any kind of object can be passed in here...
            if isinstance(object, dict):
                # Do fancy class magic, in the case of a dictionary.
                items = list(object.items())
                object.clear() # is this really necessary?

                for (name, value) in items:
                    if isinstance(name, (int, float)):
                        object[name] = self.parseTypedItems(loader, value)
                        continue

                    (name, typeName, subtype) = parseTypeDecl(name)

                    typeClass = self.getType(typeName, default = None)

                    # Hmm, pair type with parsed value.
                    object[name] = self.Building((name, typeName, subtype),
                                                 typeClass,
                                                 self.parseTypedItems(loader, value))


            # Yes, this should be done here instead of in the ItemClass.buildItem

            elif isinstance(object, tuple):
                object = tuple(self.parseTypedItems(loader, value)
                               for value in object)
        
            elif isinstance(object, list):
                object = [self.parseTypedItems(loader, value)
                          for value in object]


            return object


        class buildContinue:
            build = False

            def __init__(self, *args):
                if len(args):
                    self.value = args[0]

                    if len(args) == 2:
                        self.build = args[1]
                    else:
                        self.build = True

        class buildReturn(buildContinue):
            pass


        def typeAsync(self, classMap, name, typeName, subtype, object, loader, value, build):
            # loader.classMap.buildTypedItemMap(loader, object, \
            #     typeAsync = loader.classMap.typeAsync)

            typeClass = classMap.getType(typeName)


            # todo: self.buildTypedItemMap or buildTypedItemMap.Building?
            value = self.buildTypedItemMap(loader, value,
                typeAsync = self.typeAsync, buildAsync = build)


            # Todo: Are we making any of these decisions here?
            # if isinstance(value, self.buildReturn):
            #     if value.build is True:
            #         return value.build(value.value)

            #     return value.value

            if isinstance(value, self.buildContinue):
                return value


            # todo: self.Building or classMap.Building?
            builder = self.Building((name, typeName, subtype),
                                    typeClass,
                                    value)


            # todo: pass classMap (loader.classMap)?
            return builder.buildAsync(loader, object, name, build)




            #     r = builder.buildAsync(loader, container = object)

            #     if isinstance(r, self.buildReturn):
            #         # Always return.
            #         if r.build is True:
            #             object[name] = r.value

            #         elif r.build:
            #             return r.build(r.value)

            #         return r.value

            #     if isinstance(r, self.buildContinue):
            #         if r.build:
            #             object[name] = r.value

            #         # What would this mean?
            #         return r # ?

            #     else:
            #         object[name] = r


        def buildTypedItemMap(self, loader, object, typeAsync = None, buildAsync = None):
            # Todo: glean from parsedTypedItems, and then re-crawl object structure.
            # (This means copying crawling code from parse..?)
            if isinstance(object, dict):
                items = list(object.items())
                object.clear() # is this really necessary?

                for (name, value) in items:
                    if isinstance(name, (int, float)):
                        # Integrated type-sensitive async build algorithm.
                        r = self.buildTypedItemMap(loader, value, typeAsync = typeAsync)
                            # buildContext = (object, name)

                        if isinstance(r, self.buildContinue):
                            if r.build:
                                object[name] = r.value

                            continue

                        if isinstance(r, self.buildReturn):
                            if r.build:
                                object[name] = r.value

                            return r.value

                        return r


                    (name, typeName, subtype) = parseTypeDecl(name)

                    if typeAsync:
                        # Integrated type-sensitive async build algorithm.
                        def buildAsync_map(value):
                            with Context(container = object):
                                object[name] = value

                        r = typeAsync(self, name, typeName, subtype,
                            object, loader, value, buildAsync_map)

                        if isinstance(r, self.buildContinue):
                            if r.build:
                                buildAsync_map(r.value)

                            continue

                        # The question is to require an optional/explicit buildReturn here?
                        return r # ?


                    typeClass = self.getType(typeName)

                    ##    object[name] = typeClass.buildItem(loader, subtype, name, value,
                    ##                                       object)

                    builder = self.Building((name, typeName, subtype),
                                            typeClass,

                                            # Possibly defer this build-point,
                                            # so that the typeClass impl can
                                            # actually decide what to do with
                                            # the Building object..
                                            #
                                            # This will allow customed types to
                                            # access the typing information
                                            # symbolically before committing to
                                            # the configuration's construct.
                                            #
                                            self.buildTypedItemMap \
                                                (loader, value))


                    with Context(container = object):
                        object[name] = builder.build(loader, container = object)

                # todo: post-load behavioral compilation


            elif typeAsync:
                # Integrated type-sensitive async build algorithm.
                if isinstance(object, (tuple, list)):
                    rv = [None] * len(object)

                    for (i, value) in enumerate(object):
                        def buildAsync_seq(value):
                            rv[i] = value

                        r = self.buildTypedItemFromMap(loader, value,
                            typeAsync = typeAsync, buildAsync = buildAsync_seq)

                        if isinstance(r, self.buildContinue):
                            if r.build:
                                rv.append(r.value)

                            continue

                        if isinstance(r, self.buildReturn):
                            if r.build is not True:
                                return r.build(r.value)

                            return r.value

                        rv.append(r)

                    if isinstance(object, tuple):
                        return tuple(rv)

                    return rv

                if isinstance(object, self.Building):
                    raise NotImplementedError

                    # err, container is Building??
                    # Integrated buildAsync algorithm decision:
                    return object.buildAsync(loader, object, name)
                    return object.build(loader, container = object)

            elif isinstance(object, tuple):
                object = tuple(self.buildTypedItemFromMap(loader, value)
                               for value in object)

            elif isinstance(object, list):
                object = [self.buildTypedItemFromMap(loader, value)
                          for value in object]

            elif isinstance(object, self.Building):
                return object.build(loader, container = object) # err, container is Building??

            # Just return object as-is.
            return object

        # Note that SequencedItemMap can't be defined in this inner class (Building),
        # so it's defined after and assigned procedurally.
        def buildTypedItemFromMap(self, loader, value, typeAsync = None, buildAsync = None):
            object = self.buildTypedItemMap(loader, value,
                typeAsync = typeAsync, buildAsync = buildAsync)

            return self.SequencedItemMap.buildFromMap(loader, value)

        def buildToplevelItem(self, loader, object):
            # Todo: redevelop my notion of what the toplevel is.
            # Also, see Submapping.
            # debugOn()

            with Context(loader = loader, root = object):
                object = self.buildTypedItemMap(loader, object)

            if isinstance(object, (list, tuple)):
                return object # Do no mapping of key-values.

            return StructuredEncoding.ItemClass.Item(object)


    class Loading:
        # Central loading environment for injection into client.
        # Eventually develop this into support/interface for affecting
        #    it from the inside (class map from submapped types, etc.)
        #
        # Separate from ClassMap?

        # container.document.Context.loader
        # Put this somewhere else?
        toplevel = ContextStackScope()

        def __init__(self, classes, message, **environ):
            self.classes = classes
            self.message = message
            self.environ = environ

        def parse(self, source, extended = True):
            # debugOn()

            # assert self.message.get_type() == 'text/yaml'
            if extended:
                structure = parseExtendedYaml(source)
            else:
                structure = loadYaml(source)

            return structure

        def parseTypes(self, *args, **kwd):
            structure = self.parse(*args, **kwd)
            return self.classes.parseTypedItems(self, structure) # XXX is this not returning a full dictionary load?  also, check out parse{String|Message} for Loading result.

        def load(self, *args, **kwd):
            structure = self.parse(*args, **kwd)
            return self.classes.buildToplevelItem(self, structure)

        def parseTypesFromMessage(self, **kwd):
            # Parse from main message payload content.
            if 'non-extended' in self.message.get('X-Encoding-Format-Options', ''):
                kwd['extended'] = False

            return self.parseTypes(self.message.get_payload(), **kwd)

        def loadMessage(self, **kwd):
            # Load from main message payload content.
            if 'non-extended' in self.message.get('X-Encoding-Format-Options', ''):
                kwd['extended'] = False

            return self.load(self.message.get_payload(), **kwd)

        # Todo: lifecycle events for loading entire document.
        # (So like, post-load initialization or code execution)

    @classmethod
    def parseClassMap(self, msg, resolve = True):
        classes = msg.get('X-Encoding-Structure', '')
        classes = classes.split(';')
        classes = self.ClassMap(classes, resolve = resolve)

        return classes

    @classmethod
    def parseMessage(self, msg, **env):
        classes = self.parseClassMap(msg)

        # Todo: be able to load system-defined application paths:
        ##    ; X-Application-Path:
        ##    ;    System::MountPoint::Workspace.YTWC

        return self.Loading(classes, msg, **env)

    @classmethod
    def parseString(self, source, **env):
        # Get a Loading object.
        # debugOn()
        msg = parseStructuralSource(source)
        return self.parseMessage(msg, **env)

    @classmethod
    def parse(self, source, **env):
        # Note: this separates the loading phase from the building phase.
        # If you want to build from a parse, you'll need to simulate this
        # function in order to hold onto the loader, and deal with it.
        #
        # (This is also true for the non-resolved classmap)

        # Do a load without building items (just structure).
        if isinstance(source, str):
            # XXX for resolve
            # loading = self.parseString(source, **env)

            msg = parseStructuralSource(source)
            classes = self.parseClassMap(msg, resolve = False)
            loading = self.Loading(classes, msg, **env)

        else:
            # assert isinstance(msg, Message)

            # XXX for resolve (and msg)
            # loading = self.parseMessage(source, **env)

            classes = self.parseClassMap(msg, resolve = False)
            loading = self.Loading(classes, msg, **env)

        return loading.parseTypesFromMessage()

    @classmethod
    def loadStringFromClasses(self, source, classes, **env):
        msg = parseStructuralSource(source)
        classMap = self.ClassMap.FromClasses(classes, env.pop('default', None))
        loading = self.Loading(classMap, msg, **env)
        return loading.loadMessage()

    @classmethod
    def load(self, source, **env):
        if isinstance(source, str):
            loading = self.parseString(source, **env)
        else:
            # assert isinstance(msg, Message)
            loading = self.parseMessage(source, **env)

        return loading.loadMessage()

    @classmethod
    def loadFile(self, path, **env):
        return self.load(getPathType()(path).read(),
                         **dict(merge(env, __file__ = path)))

Context = StructuredEncoding.Loading.toplevel

class SequencedItemMapClass(StructuredEncoding.ItemClass):
    # A routine like this is necessary to do complex mapping: it is used by Building/ClassMap.
    def buildFromMap(self, loader, object):
        if type(object) is dict:
            # In other words, bypass Building constructor and instantiate item directly,
            # so that map items built directly under a sequence get the same object-wrapping
            # treatment.
            return self.buildItem(loader, None, None, object)

        return object

StructuredEncoding.ClassMap.SequencedItemMap = SequencedItemMapClass()

parseMessageLoader = StructuredEncoding.parseMessage
parseMessageLoaderFromString = StructuredEncoding.parseString

parseStructuredMessage = StructuredEncoding.parse
# parseStructuredMessageFromClasses ?? (project.coverage.analysis)

loadStructuredMessageFromClasses = StructuredEncoding.loadStringFromClasses
loadStructuredMessage = StructuredEncoding.load

def parseStructuredMessageFlat(source, **env):
    structure = parseStructuredMessage(source, **env)
    return flatten(structure)

def BuildStructuredMimeMessage(content, **classes):
    from email.message import Message
    msg = Message()

    classes = '\n    %s' % ';\n    '.join('%s = %s' % nv for nv in classes.items())
    if classes:
        msg['X-Encoding-Structure'] = classes

    msg.set_type('text/yaml')
    msg.set_payload(content)

    return msg

class WestmetalConfiguration:
    # Implements special form:
    #   Westmetal Configuration::
    #       classes = ...
    #
    # Or, does normal mime processing.
    class StringPositionalLineIterator:
        # Pretty much provides line-based iteration of a string buffer,
        # by spanning with indexes, and then provides access to the rest
        # of the buffer on request.
        #
        # The difference from a file-like/string buffer is that the lines
        # don't include the line endings.  XXX (Also, doesn't handle \rs)
        def __init__(self, string):
            self.string = string
            self.pos = 0

        def __iter__(self):
            return self

        def __next__(self):
            i = self.string.find('\n', self.pos)
            if i < 0:
                raise StopIteration

            try:
                # Hmm, this could be made more efficient by putting
                # everything into __iter__...?

                if i and self.string[i - 1] == '\r':
                    return self.string[self.pos:i-1]

                return self.string[self.pos:i]

            finally:
                self.pos = i + 1

        def rest(self):
            return self.string[self.pos:]

    class NotWestmetalConfigurationException(Exception):
        pass

    # Todo: implement a more complex typing expression syntax:
    #    object-name[python$object(withArg1, andFlag = True)]:
    #       ...
    #
    #    This can be done with a Sandbox and interpolated string
    #    (because of submethod patterning).

    import re
    p_word = r'(?:[a-zA-Z_][a-zA-Z0-9_]*)'
    p_fqName = r'%s(?:.%s)*' % (p_word, p_word)
    p_classDef = r'^\s{4}(%s)\s*(?:\=|\:)\s*(%s)\s*$' % (p_word, p_fqName)

    p_classDef = re.compile(p_classDef)
    p_classDef_Match = p_classDef.match # staticmethod()?

    @classmethod
    def ParseWC(self, source):
        i = self.StringPositionalLineIterator(source)

        # Match header.
        # todo: WMC [name: module.path, ...] form?
        try:
            line = next(i)
            if line.startswith('WMC ['):
                # Parse the classes:
                classes = dict()

                line = line[5:]
                x = line.rfind(']')
                if x < 0:
                    raise ValueError('WMC format does not have terminal ]')

                line = line[:x]
                for defn in line.split('; '):
                    defn = self.p_classDef_Match(defn)
                    if defn is not None:
                        (name, package) = m.groups()
                        classes[name] = package

                return BuildStructuredMimeMessage(i.rest(), **classes)

            assert line.startswith(WMC_PROLOG)

        except (StopIteration, AssertionError):
            raise self.NotWestmetalConfigurationException

        # Parse the classes:
        classes = dict()

        # todo: parse this section as INI?
        for line in i:
            m = self.p_classDef_Match(line)
            if m is None:
                # todo: allowing '    ; Version: 5' attributes:
                #    -- Version: 5
                #    .Version = 5
                break

            (name, package) = m.groups()
            classes[name] = package

        return BuildStructuredMimeMessage(i.rest(), **classes)

    @classmethod
    def ParseMime(self, source):
        return message_from_string(source)

    @classmethod
    def Parse(self, source):
        source = dedent(source)

        try: return self.ParseWC(source)
        except self.NotWestmetalConfigurationException:
            return self.ParseMime(source)

parseStructuralSource = WestmetalConfiguration.Parse

class Submapping(StructuredEncoding.ItemClass):
    @Object.Format('{name}')
    class ItemNode(Object):
        def __init__(self, name, value, **kwd):
            self.name = name
            self.value = value
            self.kwd = kwd

    def buildItem(self, loader, subtype, name, value, **kwd):
        typeImpl = self.getTypeImpl(subtype)
        if typeImpl is None:
            # Default?
            return self.default(loader, subtype, name, value, **kwd)

        # This way, don't have to rely on overriding '__new__'
        buildItem = getattr(typeImpl, 'FromStructure', typeImpl)

        # Todo -- use nested?
        with Context(loader = loader):
            with mutateObject(self, loader = loader):
                return buildItem(name, value, **kwd)


    def buildItemAsync(self, builder, loader, object, name, build):
        typeImplAsync = self.getTypeImplAsync(builder)

        if typeImplAsync:
            try: r = typeImpl(name, builder, loader, object) # xxx todo: what's object?  container?
            except OuterFrame as sub:
                @sub.onComplete
                def doneAsync(this_frame, *error, **kwd):
                    if error[0]:
                        build(None) # error[0])
                        # err, just continue raising
                    else:
                        build(this_frame.task.stack.pop()[0])
            else:
                # And I guess be able to handle 'classical' type impl calls.
                with Context(container = object):
                    build(r)
                    # Hmm, catch Continuations..??

        else:
            with Context(container = object):
                build(builder.build(loader, container = object))
                # Hmm, catch Continuations..??

        return loader.classMap.buildContinue()


    def getTypeImplAsync(self, builder):
        typeImpl = self.getTypeImpl(builder.subtype)

        if getattr(typeImpl, 'isAsync', False):
            return typeImpl

    def isMappedName(self, name):
        bases = [Submapping]

        while bases:
            base = bases[0]
            del bases[0]

            member = getattr(base, name, None)
            if member is not None:
                # print(member)
                return False

            for base in getattr(base, '__bases__', []):
                if base not in bases:
                    bases.append(base)

        return True

    def getTypeImpl(self, name):
        self.resolveAliases()

        if not name: # XXX if isstr
            return

        if name.startswith('_'):
            raise NameError(f'Type implementation name must not start with underscore: {name}')

        if not self.isMappedName(name):
            raise NameError(f'Type implementation name is not mapped: {name}')

        return getattr(self, name, None) # i guess


    @classmethod
    def resolveAliases(self):
        self.Alias.ResolveForClass(self)

    class DefaultError(Exception):
        pass

    def default(self, loader, subtype, name, value, **kwd):
        # Basic 'package/structural' pattern:
        # loader.classes[name] = <submapping-item-factory-object>

        if kwd.get('errorOn'):
            raise self.DefaultError

        return StructuredEncoding.ItemClass.buildItem \
               (self, loader, subtype, name, value, **kwd)

    # @Object.Format('{name}')
    class Alias: # (Object):
        def __init__(self, name, strict = False):
            self.name = name
        def __call__(self, function):
            return function

        @classmethod
        def ResolveForClass(self, cls):
            # Introspect for mapped item names that are reserved Python keywords.
            if not getattr(cls, '_aliases_resolved', False):
                for alias in cls.__dict__.values():
                    if isinstance(alias, self):
                        alias.bind(cls)

                cls._aliases_resolved = True

        def bind(self, cls):
            setattr(cls, self.name, self)

# This might be more efficient:
# Submapping.resolveAliases = classmethod(Submapping.Alias.ResolveForClass)

class MultipleSubmapping(list):
    # def buildItem(self, loader, subtype, name, value, **kwd):
    def buildItem(self, *args, **kwd):
        if not kwd.get('errorOn'):
            kwd['errorOn'] = True

        error = ValueError

        for sub in self:
            try: return sub.buildItem(*args, **kwd)
            except StructuredEncoding.DefaultError as e:
                error = e

        raise error


def structurize(factoryClass):
    ##    @structurize
    ##    class Factory:
    ##        class myObject: # (structurize.d):
    ##            def __init__(self, name, value, **kwd):
    ##                pass

    # Hmm, these patterns are all about constructing new initialized subclasses.

    ##    class structure(Object):
    ##        Factory = newClassObject('Factory', (factoryClass, Submapping), dict())

    newClass = newClassObject('Factory', (factoryClass, Submapping), dict())
    for (name, value) in list(newClass.__dict__.items()):
        if isinstance(value, StructurizedMapping):
            setattr(newClass, name,
                    newClassObject(name, (newClass, Object,
                                          StructurizedMapping.Item)))

    # And relying on sys._getframe here is bogus.
    with callerAt(-1) as ns:
        ns.structure = newClassObject('structure', (Object,),
                                      dict(Factory = newClass))

    return newClass

class StructurizedMapping:
    class Item(Object):
        # Oh, and also do things that allow typing drawn under the buildItem on Submapping?

        def __init__(self, name, value, **kwd):
            pass

structurize.d = StructurizedMapping

# Todo: put this into the runtime.objects core?
# Also, derive from strings.SourceCode
# Todo: do something like add a certain number of blank newlines to the beginning
#       of this text before compiling, so that embedding documents can effect the
#       internally-loaded offset.  This will also probably have to allow code-source
#       interface (newModule/executeIn/common.runtime.core.ExecuteText interface).
@Object.Format('{name}')
class Script(Executable, Object):
    def __init__(self, script, name = None):
        self.script = script
        self.name = name

    @property
    def space(self):
        self.space = space = Core.Python.space
        return space

    @property
    def codeObject(self):
        return self.script


# Value resolution policies:
def resolveObjectToString(value):
    # An intelligent, presumptive toString.

    if isPathType(value):
    ##    if isinstance(value, PathType):
        value = value.read()

    ##    elif isinstance(value, URL):
    ##        value = value.value
    ##    elif isinstance(value, file):
    ##        value = value.read()
    ##    elif isinstance(value, Expression):
    ##        value = value() # sandbox?

    return value

def simplify(value):
    while True:
        if isinstance(value, dict) and len(value) == 1:
            try: value = value['']
            except KeyError: break
            else: continue
            # Always continue simplifying down, if desired.
        else:
            break

    return value


def Implementation(base): # DOM
    # Type necessary for Item.ToStructure.
    container = base['container']
    ns = Namespace(container)

    parts = __name__.split('.')

    ns[parts[-1]] = LookupObject(__name__)
    if len(parts) > 1:
        ns[parts[0]] = LookupObject(parts[0])

    # values['document'] = thisModule()

    ns.update(base) # merge?

    ns['container'] = Synthetic(container)
    ns['toplevel'] = Context
    ns['this'] = ns

    # XXX container.parent = Context.loader.classes
    # XXX actually, toplevel should ultimately provide
    # access to the returned structured (as postload?)

    return ns


class Document(Object):
    Building = StructuredEncoding.ClassMap.Building

    def __init__(self, path, caching = True):
        # Note: _requires_ path..
        self.path = io.path(path)
        self.caching = caching
        self._prestructure = None
        self.root = self.Section(self)

        # todo: some kind of attribute-chain accessor for new found sections

    def getAttributeString(self):
        return self.path


    @property
    def noteName(self):
        return self.path.basename

    @property
    def ideObject(self):
        return pythonWin.open(self.path) # already open? and also, this should
                                         # actually be giving us the ide.documents.Document handle...

    class Section(Object, list):
        def __init__(self, doc, *names):
            list.__init__(self, names)
            self.doc = doc

        def getAttributeString(self):
            return '%s:%s' % (self.doc.noteName, ':'.join(list.__iter__(self)))

        # todo: properties and access methods for: structured (extended) document, stringification of Building tree (reconstruction)
        # todo: some kind of attribute-chain accessor for the section

        @property
        def value(self):
            return self.doc.access(*self)

        def subsection(self, *names):
            return self.__class__(self.doc, *(self[:] + list(names)))

        def iterNames(self):
            value = self.value

            if isinstance(value, Document.Building):
                value = value.value

            # should be type(value) in (dict, Namespace)
            if isinstance(value, dict):
                return iter(value.keys())

            if type(value) in (list, tuple):
                return range(len(value))

            return iter(())

        def iterSections(self):
            for n in self.iterNames():
                yield self.subsection(n)
        __iter__ = iterSections

        names = property(iterNames)
        sections = property(iterSections)

        # This could break things: (but, should be used)
        ##    def __getitem__(self, section):
        ##        if not isinstance(section, (tuple, list)):
        ##            section = (section,)
        ##
        ##        return self.subsection(*section)


        def searchValue(self, value, content, recursive = False):
            if isinstance(value, Document.Building):
                value = value.value

            if isinstance(value, str):
                if isinstance(content, RegularExpressionType):
                    return content.match(value) is not None

                elif isinstance(content, str):
                    return content in value

            # actually, a function of walk from here on down:
            elif isinstance(value, (list, tuple)):
                if recursive:
                    for i in range(len(value)):
                        if self.subsection(i).searchText \
                           (content, recursive = recursive):
                            return True

            elif isinstance(value, dict):
                if recursive:
                    for i in iterkeys(value):
                        if self.subsection(i).searchText \
                           (content, recursive = recursive):
                            return True

        def searchText(self, *args, **kwd):
            return self.searchValue \
                   (self.value, *args, **kwd)

        def searchKeys(self, *args, **kwd):
            return self.searchValue \
                   (self[-1], *args, **kwd)

        # what about search key-types in building structure??
        # todo: move this out of Section and into Document.
        class GenericSearch:
            class Criteria(Object, list):
                typeTokenRemap = {'name': 'NameMatch',
                                  'typeName': 'TypeNameMatch',
                                  'type-name': 'TypeNameMatch',
                                  'subType': 'SubTypeMatch',
                                  'sub-type': 'SubTypeMatch',
                                  'typeClass': 'TypeClassMatch',
                                  'type-class': 'TypeClassMatch',
                                  'value': 'ValueMatch'}

                @classmethod
                def GetTypeToken(self, x):
                    if type(x) is (list, tuple, set):
                        # Recurse..
                        return mapi(self.GetTypeToken, x)

                    x = nameOf(x) if isinstance \
                        (x, TypeType) \
                        else x

                    try: x = self.typeTokenRemap[x]
                    except (TypeError, KeyError):
                        pass

                    return x

                def __init__(self, *args, **kwd):
                    list.__init__(self, args)

                    try: self.type = set((self.GetTypeToken(kwd.pop('type')),))
                    except KeyError:
                        self.type = set()

                    self.keywords = kwd

                @classmethod
                def Formulate(self, *args, **kwd):
                    return self(*args, **kwd)

                def getAttributeString(self):
                    return logString(*self, **self.keywords)

                def handleException(self, exc):
                    return # ignore this match

                @classmethod
                def MatchValue(self, object, exceptionHandler,
                               *patterns, **keywords):

                    def m(o, t):
                        try:
                            if isinstance(t, RegularExpressionType):
                                # Force string type and match.
                                return t.match(str(o)) is not None

                            if callable(t):
                                return t(o)

                            return o == t # __match__? __cmp__?

                        except Exception as e:
                            r = exceptionHandler(e)
                            return r is None or bool(r)

                    def p(xxx_todo_changeme):
                        (n, v) = xxx_todo_changeme
                        try: o = getattr(object, n)
                        except AttributeError: pass
                        else: return m(o, v)

                    # Default: AND
                    return all(m(object, a) for a in patterns) and \
                           all(mapi(p, iteritems(keywords)))

                def match(self, object, type = None):
                    if type is not None:
                        if isinstance(type, (list, tuple, set)):
                            type = set(mapi(self.GetTypeToken, type))

                        else:
                            assert isinstance(type, (str, TypeType))
                            type = set((self.GetTypeToken(type),))

                        if self.type.intersection(type) != type:
                            return False

                    return self.MatchValue \
                           (object, self.handleException,
                            *self, **self.keywords)

                    # (Or, return those parts that match..)


                __call__ = match


            @classmethod
            def SearchStructure(self, section, criteria, results):
                # section[-1] <- key/name
                node = section.value

                def against(type, value):
                    # todo: pass more about us to .Match so that results can track
                    # the source (instead of just that there was a value match..)
                    #
                    # todo: this means putting alot of 'section' pairs into each
                    # result.. maybe this could be done by using a context?
                    #
                    # XXX Remember, Document.Search is spanning sections itself,
                    # keeping track of the sections, so, in all actuality, this isn't
                    # needed!
                    #
                    # Having the section and the matched type is really all that's needed.
                    # The _part_ of the value that's matched could be helpful too (like
                    # line number, text span)
                    return type.Match(criteria, value, results) # ,
                                      # section = section)

                if isinstance(node, Document.Building):
                    # or: .search(name = Criteria('xyz', type = .NameMatch))
                    # criteria(node)

                    against(self.NameMatch      , node.name     )
                    against(self.TypeNameMatch  , node.typeName )
                    against(self.SubTypeMatch   , node.subtype  )
                    against(self.TypeClassMatch , node.typeClass)

                # And, do more to differentiate between structural values
                # in building and other data.
                against(self.ValueMatch, node.value)


                ##    if isinstance(node, basestring):
                ##        if criteria(node):
                ##            self += node
                ##
                ##    elif isinstance(node, (list, tuple)):
                ##        # Aren't these sections??
                ##        ##    for i in xrange(len(value)):
                ##        ##        if self.subsection(i).searchText \
                ##        ##           (content, recursive = recursive):
                ##        ##            return True
                ##        pass
                ##
                ##    elif isinstance(node, dict):
                ##        ##    for i in iterkeys(value):
                ##        ##        if self.subsection(i).searchText \
                ##        ##           (content, recursive = recursive):
                ##        ##            return True
                ##        pass

            class MatchResult:
                @classmethod
                def Match(self, criteria, value, results): # ,
                          # *args, **kwd):

                    if criteria(value, type = self):
                        # Todo: track more!
                        results += self(value) # , *args, **kwd)

            class ValueMatch(MatchResult):
                def __init__(self, object): # , *args, **kwd):
                    self.value = object
                    # self.args = args
                    # self.kwd = kwd

            class NameMatch(ValueMatch):
                pass
            class TypeNameMatch(ValueMatch):
                pass
            class SubTypeMatch(ValueMatch):
                pass
            class TypeClassMatch(ValueMatch):
                pass


            class Results(Object, list): # FilePoints?
                def getAttributeString(self):
                    return '%d results' % len(self)

                def __iadd__(self, result):
                    self.append(result)
                    return self


                # User Shell.
                # How do these differ?
                @property
                def points(self):
                    from common.platform.filesystem import FilePoints

                    # Since the current prestructure search can't detect line numbers...
                    return (FilePoints.Location(s.doc.path, 0)
                            for (s, v) in self)

                @property
                def selected(self):
                    from common.platform.filesystem import FileSet
                    return FileSet # ...


            @classmethod
            def Perform(self, walk, *args, **kwd):
                results = self.Results()

                walk(self.SearchStructure,
                     self.Criteria.Formulate \
                     (*args, **kwd),
                     results)

                return results


        def search(self, *args, **kwd):
            return self.GenericSearch.Perform \
                   (self.walk, *args, **kwd)


        def walk(self, visitor, *args, **kwd):
            visitor(self, *args, **kwd)

            for s in self:
                s.walk(visitor, *args, **kwd)

            return visitor


        # On Manipulation:
        #    Regarding adding, removing or moving sections, we'll want to keep
        #    the format as close as possible to what existed before.  In fact,
        #    this is especially important if it also happens to be a document
        #    already open in the ide.
        #
        #    The best way to do this is to break the text into lines, and work
        #    with those, apart from any kind of 'extended-yaml' parsed syntax
        #    structure.  This means using the parse tree as a guideline for
        #    recognizing block definition in the note structure and tracking
        #    line numbers, but doing the actual change in an array (then re-
        #    writing it to synchronize with buffer/disk).
        #
        #    Perhaps one of the best ways to do this is to keep track of the
        #    structure at all times, but only parse blocks that we know need
        #    parsing (that is, starting at a line with a definition, and ending
        #    when its naturally un-indented).  Changing sections in this case
        #    would be restricted to the internal structure, and would remove
        #    the need to reparse on EVERY SINGLE change.
        #
        #    Keeping track of all whitespace, however, as well as comments,
        #    might be more difficult for changes to minor inner elements, though.

        def delete(self):
            return self

        def insertSection(self, other):
            return self
        __add__ = __iadd__ = insertSection

        def moveSection(self, other):
            self.insertSection(other)
            other.delete()

            return self

    def loadStructure(self):
        assert self.path.exists
        return self.path.loading.extended

    @property
    def prestructure(self):
        if self.caching:
            if self._prestructure is None:
                self._prestructure = self.loadStructure()

            return self._prestructure
        return self.loadStructure()

    # Top-level.
    def access(self, *names):
        # XXX 'access'ing over prestructure is moot because Buildings
        # can't be indexed (via getitem) for section purposes.
        return access(self.prestructure, *names)

    # How much of this should be part of Section?
    def iterNames(self):
        return self.root.iterNames()
    def iterSections(self):
        return self.root.iterSections()
    __iter__ = iterSections

    names = property(iterNames)
    sections = property(iterSections)

    def find(self, *names):
        return self.Section(self, *names)
    __getitem__ = __call__ = find

    def toPublishedString(self):
        # essentially, rebuild the document,
        # (but annotate it)
        return ''
        pass
    __str__ = toPublishedString

    def delete(self, *names):
        self.find(*names).delete()
        return self

    def walk(self, visitor, *args, **kwd):
        for s in self:
            s.walk(visitor, *args, **kwd)

        return visitor

    @property
    def edit(self):
        pythonWin.open(self.path)

    # todo: searchTree can be replaced with searching on
    # implementation of Section.walk, Or!  an implementation
    # here search/walking the building prestructure, so that
    # sections aren't being created...

    # Note: yes, searchXxx is inferior because it merely returns
    # true if there's a match in (the whole) document.
    def searchTree(self, search, *args, **kwd):
        onError = kwd.pop('onError', None)
        i = self.iterSections()

        while True:
            try: s = next(i)
            except StopIteration:
                break

            except:
                if onError:
                    onError(*system.lastException.either())
            else:
                try:
                    r = search(s, *args, **kwd)
                    if r:
                        yield (s, r)

                except:
                    # likely to spam alot:
                    #system.printTraceback(*system.lastException.either())

                    if onError:
                        onError(*system.lastException.either())


    def searchText(self, *args, **kwd):
        def text(s, *args0, **kwd0):
            return s.searchText(*args0, **kwd0)

        return (s for (s, r) in self.searchTree(text, *args, **kwd))

    def searchKeys(self, *args, **kwd):
        # XXX re-implement as Building typed-key-search,
        # instead of creating sections just to look at their names.
        def keys(s, *args0, **kwd0):
            return s.searchKeys(*args0, **kwd0)

        return (s for (s, r) in self.searchTree(keys, *args, **kwd))


    # More preferable: return categorized results of comprehensive search.
    def search(self, *args, **kwd):
        # Search everything.
        def generic(s, *args0, **kwd0):
            return s.search(*args0, **kwd0)

        for (s, r) in self.searchTree(generic, *args, **kwd):
            # Compile all results for matching sections.
            for x in r:
                yield (s, x) # x


# example implementation (notes):
##    searches = map(AccessParts, sections)
##        for e in Daily.Entries():
##                for r in searches:
##                    for x in r.search(s):
##                        yield (e, r, x)


class Core:
    class Python(Submapping):
        def value(self, name, value, **kwd):
            # Kind of a hack...
            return value

        space = dict() # Kind of arbitrary.

        # class RecordedProgram(Script): pass
        RecordedProgram = Script

        # About scoping(python.document$rst)::
        # ==============
        #    Have the namespace be that containing the
        #    declared script object?::
        #
        #       environment:
        #           data: [...]
        #           code(...): data[...]
        #
        #    Or, the parent of the containing namespacing::
        #
        #       environment:
        #           data: [...]
        #           code(...): environment.data[...]
        #
        #    But also, symbols for top-level addressing::
        #
        #       document:
        #           environment1:
        #               object: {}
        #
        #           environment2:
        #               code(...): document.environment1.object
        #

        def source(self, name, value, **kwd):
            return SourceCode(value) # todo; bind kwd?
        code = source

        def program(self, name, value, **kwd):
            return self.RecordedProgram(value, name)
        def script(self, name, value, **kwd):
            return self.RecordedProgram(value, name).executeWith(kwd) # todo: merge(kwd, toplevel = toplevel)

        # main = app = shell?

        def module(self, name, value, **kwd):
            # Hmm, value should be a string.
            # Otherwise, force type by passing it to this (loader's) object builder.

            # todo (for modules so that syntax is available):
            # ns['__loader__'] = ...
            # also, utilize structural path-down-to-object in name context

            return self.RecordedProgram(value, name).newModule \
                    (values = Implementation(kwd),
                     # submappingContext.loader.environ['__file__']
                     codeSource = '<embedded:%s>' % name,
                     registration = kwd.pop('registration', None))

        def package(self, name, value, **kwd):
            '''
            my.system.structure(python$package)::
                # A sample way of extending system modules within structure.
                from common.runtime.structural.document import Submapping
                from common.runtime import Object

                class Factory(Submapping):
                    @Object.Format('{name}: {value}')
                    class object(Object, Namespace):
                        def __init__(self, name, value, **kwd):
                            Namespace.__init__(self, **kwd)
                            self.name = name
                            self.value = value
            '''

            # Todo: allow something like this:
            ##    my(python$package):
            ##        container:
            ##            __init__(python$module):
            ##                pass # my.container
            ##
            ##            submodule:
            ##                pass # my.container.submodule
            ##            codemodule(python$module):
            ##                pass # my.container.codemodule

            # And also (for load order when not with ordered dict):
            ##    container:
            ##        - sub1: x = 1
            ##        - sub2: from .sub1 import x
            ##        - sub3:
            ##            sub4: from ..sub2 import x

            def registerWithName(module):
                return registerSystemModule(name, module)

            kwd['registration'] = registerWithName
            # todo: merge(kwd, toplevel = toplevel)

            return self.module(name, value, **kwd)


        def definition(self, name, value, **kwd):
            pass

        def method(self, name, value, **kwd):
            # todo: self/this instance parameter?  Yes!
            # (The problem is in binding it...
            #  an unbound method should have self point to the method itself!)
            #  (Or, a wrap.function!)

            # todo: documentation

            if isinstance(value, str):
                parameters = keywords = decorators = []
                documentation = None
                code = value

            else:
                assert isinstance(value, dict)

                parameters = value.get('parameters', [])
                keywords = value.get('keywords', [])
                decorators = value.get('decorators', [])

                documentation = value.get('documentation', None)

                code = value['code']

            keywords = dict((n, None) for n in keywords)
            # and, combine positional arguments in parameters, with default value assignments.

            def transformParameter(p):
                return p.replace('+', '*') # no validation

            parameters = list(map(transformParameter, parameters))

            # Currently.
            star = doubleStar = None

            if not isinstance(code, SourceCode):
                # assert isinstance(code, basestring)
                code = SourceCode(code)

            # todo (for modules so that syntax is available):
            # kwd['__loader__'] = ...
            # also, utilize structural path-down-to-object in name context

            ns = Implementation(kwd)

            ##    ns['__builtins__'] = dictOf(builtin.module)

            ##    with stepAroundBuiltins(ns):
            ##        return code.GenerateFunction(code.Function(name, *parameters, **keywords),
            ##                                     codeSource = '<embedded:%s>' % name,
            ##                                     namespace = ns)

            function = code.GenerateFunction \
                       (code.Function(name, star, doubleStar,
                                      documentation,
                                      *parameters, **keywords),
                        codeSource = '<embedded:%s>' % name,
                        namespace = ns)

            # Apply decorators.
            for d in decorators:
                function = call(eval(d), function)

            return function

        def expression(self, name, value, **kwd):
            # print value

            # The idea is to set this first, but doesn't the LL runtime do it?
            ##    globals['__builtins__'] = dictOf(builtin.module)
            ##
            ##    with stepAroundBuiltins(globals):
            ##        exec code in globals, ns

            # XXX problems here because it's wiping out __builtins__???
            # (on object.clear during recursive build.  Maybe it's because
            #  the buildItem-chain is doubling up on the call graph.)
            # It shouldn't be a problem to execute directly in the container,
            # but maybe some more scoping is called for.

            # todo (for modules so that syntax is available):
            # kwd['__loader__'] = ...
            # also, utilize structural path-down-to-object in name context

            ns = Implementation(kwd)
            return Script.Evaluate(value, name = name,
                                   globals = ns, # todo: merge(kwd, toplevel = toplevel)
                                   locals = dict(this = ns))

        def instance(self, name, value, **kwd):
            # Should be looking for simplifed class/object in value, and just
            # instantiate it!
            #
            # This could look something like:
            #   (system$register):
            #       (python$instance):
            #           my.logging(python.object$generic):
            #               implementation(python$source)::
            #                   def __call__(self, *args, **kwd):
            #                       return logString(self.getClassName(), *args, **kwd)
            #
            #               __init__(python$method):
            #                   code: system.types.module(self, this.name)
            #
            # system.library.my.logging('a', 'b', c = True)

            return value() # **kwd

        def context(self, name, value, **kwd):
            # Todo: express parameters like method??  Glean code from higher types?
            setup = value.get('setup')
            expr = value['expression']
            cleanup = value.get('cleanup')

            def express(*args, **kwd):
                if setup:
                    exec(setup, locals(), globals())

                try: yield eval(expr)
                finally:
                    if cleanup:
                        exec(cleanup, locals(), globals())

            return express

        def include(self, name, value, **kwd):
            '''
            structure:
                contained(include):
                    object(python.object$path):
                        this(expression):
                            io.common.workspace('.wmc')
            '''

            value = simplify(value)

            if isPathType(value):
                return StructuredEncoding.loadFile(value, **self.loader.environ)
            if isinstance(value, str):
                return Structr(value, **self.loader.environ)

            raise ValueError(value)

        def use(self, name, value, **kwd):
            # XXX access to loading.classes
            raise NotImplemented('access to loading object')

            if not isinstance(value, dict):
                raise ValueError(value)

            # todo: as context for building phase (which means snagging this as a top-down in build order)
            c = Context.loader.classes
            for (name, object) in value.items():
                c[name] = c.loadStructure(object)

            # return c

            # todo: consider structures that re-instantiate the Loading environment or the ClassMap,
            # or, Factories (ItemClasses) themselves (swapping new Core.Python or default).

        def submapping(self, name, value, **kwd):
            '''
            Westmetal Configuration::

            my.machining.structure(python$submapping):
                path::
                    from common.path import PathType
                    return PathType.FromEnv(value)

                url::
                    from common.url import V3
                    return Url(value)

                json::
                    from json import loads
                    return loads(value)

                mime::
                    assert isinstance(value, basestring)
                    from email import message_from_string
                    return message_from_string(value)

                base64::
                    assert isinstance(value, basestring)
                    return value.decode('base64')

            '''

            module = name.split('.')
            className = camelize(*module[-1].split())
            module = module[:-1]

            name = '.'.join(module + [className])

            for o in list(value.keys()):
                v = value[o]

                if isinstance(v, str):
                    v = SourceCode(v)

                if isinstance(v, SourceCode):
                    # todo: bind to this instance.. or as class method.
                    v = v.GenerateFunction(v.Function(o, None, 'kwd', 'name', 'value'),
                                           codeSource = '<submapping:%s>' % o,
                                           namespace = kwd)

                    value[o] = v


            submapClass = newClassObject(className, (Submapping,), value)

            # Todo: option to store in containing environment... or at least
            # set up into loader class-map.
            #
            # (Decorators, or, at least, entity referencing combined with 'use')
            #

            # Note: should this create a surrounding module for the class..?
            # This is the primary support method of populating the class map.
            # .. And, it seems to work.
            return registerSystemModule(name, submapClass)


        # overlay, access notation, registry/subregistry sets
        # builtins? overlay onto special module name...
        # overlay targetted on module names, or containing objects?
        # general, contained expression syntax:
        #   sandbox
        #   istring?
        #   evaluation of registered object names, subregistry address
        #   batching of subregistered objects in WMC files such for importation into scope with Using.
        #   generic <-- using/rehousing structures (for instance, plug into existing module structure)
        # module/import sets/hierarchies:
        #   for batch/group load/unload/reload, ordered reload

        def default(self, loader, subtype, name, value, **kwd):
            if subtype == 'quoted':
                # To be later bound
                return self._quoted(name, value, **kwd) \
                           .setLoadingEnvironment(loader, subtype = subtype)

            # Override nothing else.
            return Submapping.default(self, loader, subtype, name, value, **kwd)

        class _quoted(Submapping.ItemNode):
            # Hmm, the idea is to return an object that can later be applied for construction.
            # But this has to actually be separate from the Submapping behavior of pre-evaluating
            # mapped types.

            def setLoadingEnvironment(self, loader, subtype = None):
                self.loader = loader
                self.subtype = subtype
                return self

            def build(self):
                return self.buildWithArgs(self.loader, subtype = self.subtype)

            def buildWithArgs(self, loader, subtype = None):
                return StructuredEncoding.ItemClass.buildItem \
                       (self, loader, subtype,
                        self.name,
                        self.value,
                        **self.kwd)

            # quoted = _quoted

    class Objects(Submapping):
        def encoded(self, name, value, **kwd):
            # This constructor routine could actually be in common.data.formats
            # see also: Object.formats
            from common.data.formats import Registry # .UnknownFormat

            try: from common.data.formats import loadStringByName
            except ImportError:
                from common.data.formats import loadStreamByName
                def loadStringByName(s, n):
                    # err, non-optimal implementation, and notice switched arg positiosn
                    return loadStreamByName(n, io.buffer(s))

            format = value.get('formats') or value.get('encoding')
            assert format

            if isinstance(format, str):
                format = having(name.strip() for name in format.split(';'))
            else:
                assert isinstance(format, (list, tuple))

            value = value['content']
            for name in format: # reversed..?
                try: value = loadStringByName(value, name)
                except Registry.UnknownFormat:
                    value = value.decode(name)

            return value

        packed = encoded

        def path(self, name, value, **kwd):
            return getPathType().FromEnv(value)

        def url(self, name, value, **kwd):
            from common.platform.url import V3
            return Url(value)

        def json(self, name, value, **kwd):
            from json import loads
            return loads(value)

        def mime(self, name, value, **kwd):
            assert isinstance(value, str)
            from email import message_from_string
            return message_from_string(value)

        def base64(self, name, value, **kwd):
            assert isinstance(value, str)
            return value.decode('base64')

        # Flavors of include...
        def format(self, name, value, **kwd):
            from common.data import loadStringByName
            if isinstance(value, dict): # or Item..?
                name = value['name']
                value = value['content']

            return loadStringByName(resolveObjectToString(simplify(value)), name)

        def structure(self, name, value, **kwd):
            '''
            Westmetal Configuration::

            (python.object$structure):
                (python.object$path):
                    (python$expression):
                        io.user('~/env/.embedded-structural')

            '''

            return Structr(resolveObjectToString(simplify(value)))


        ##    def config(self, name, value, **kwd):
        ##        pass

        ##    def ini(self, name, value, **kwd):
        ##        pass

        class interface(Submapping.ItemNode):
            # Create an interface to an existing object, limiting access.
            def __init__(self, name, value, **kwd):
                print(name, value)
                self.object = value['object']
                self.methods = value['methods']

            def __call__(self, method, *args, **kwd):
                assert method in self.methods
                return getattr(self.object, method)(*args, **kwd)

        _implDefault = dict(bases = [Object])
        _implBases = dict(Object = Object)
        _implDecorators = dict(singleton = apply)

        def implementation(self, name, value, **kwd):
            if isinstance(value, str):
                value = self._implDefault.copy()
                value['init'] = value

            assert isinstance(value, dict)

            bases = value.pop('bases', [])

            try: bases.append(value.pop('base'))
            except KeyError: pass

            def resolve(b, aliases):
                if isinstance(b, str):
                    try: return aliases[b]
                    except KeyError: pass

                    # What about evaluate?  Just use 'expression..?'
                    return system.lookup(b)

                # XXX isinstance, but this is for expressions..
                if isinstance(b, dict):
                    # Simplify.
                    if len(b) == 1 and '' in b:
                        b = b['']

                return b

            def resolve_base(b):
                return resolve(b, self._implBases)
            def resolve_decorator(b):
                return resolve(b, self._implDecorators)

            try: decorators = value.pop('decorators')
            except KeyError: decorators = []

            bases = list(map(resolve_base, bases))
            decorators = list(map(resolve_base, decorators))

            try: init = value.pop('init')
            except KeyError: pass
            else:
                # Todo: Implementation
                init = 'class %s:\n%s\n' % (name, indent(init))
                co = compile(init, '<implementation:%s>' % name, 'exec')
                ns = {}

                exec(co, ns, ns)
                bases.append(ns[name])


            preClassInit = value.pop('classInit', False)

            cls = newClassObject(name, tuple(bases), value)

            if preClassInit is not False:
                assert callable(preClassInit)
                preClassInit(cls)

            for d in decorators:
                cls = d(cls)

            return cls

        class generic(Submapping.ItemNode, GenericContext):
            def __init__(self, name, value, **kwd):
                if isinstance(value, str):
                    value = dict(init = value)

                assert isinstance(value, dict)

                # XXX because we need context destroyed by implementation of Submapping
                remap = Core.Python.RecordedProgram # (value['init'])
                init = remap(value['init']) # todo: basically do a typed item map
                assert isinstance(init, Core.Python.RecordedProgram)

                self.name = name
                self.space = value # kwd?
                self.program = init

                del value['init']
                self.init(**kwd)

            def init(self, **env):
                self.space[self.name] = self
                self.space['this'] = self
                self.space['env'] = env

                self.program.executeIn(self.space, self.space)

            @property
            def namespace(self):
                return Synthetic(self.space)

            def __enter__(self):
                return self.namespace


    class Document(Submapping):
        def xml(self, name, value, **kwd):
            from xml.dom.minidom import parseString
            return parseString(value)

        def rst(self, name, value, **kwd):
            from docutils.core import publish_parts
            return publish_parts(value)

        # yep... what about (.$packed): {encoding: soup, content: <html>}?
        def soup(self, name, value, **kwd):
            return loadable(value).loading.soup
        html = soup

        def extraction(self, *args, **kwd):
            from common.data.html.extraction import extraction
            return extraction(*args, **kwd)

        def processing(self, *args, **kwd):
            from common.data.html.extraction import processing
            return processing(*args, **kwd)

        def template(self, name, value, **kwd):
            return Template(value)

    Structure = Document


# Move into objects..?
class Template(Object):
    def __init__(self, string):
        from django.template import Template, Context
        self.template = Template(string)
        self.ContextClass = Context

    def render(self, **values):
        return self.template.render \
               (self.ContextClass(values))

    __call__ = render


DEFAULT_PREFIX = 'python'
CORE_CLASSES = dict(python = Core.Python())
CORE_CLASSES['python.object'] = Core.Objects()
CORE_CLASSES['python.document'] = Core.Document()

CORE_CLASSES['python.structure'] = CORE_CLASSES['python.document'] # Core.Structure()

CORE_CLASSES[''] = CORE_CLASSES['python']
CORE_CLASSES['.object'] = CORE_CLASSES['python.object']
CORE_CLASSES['.document'] = CORE_CLASSES['python.document']
CORE_CLASSES['.structure'] = CORE_CLASSES['python.structure']

Structr = StructuredEncoding.load
YStruct = Structr
Structur = Structr

Item = StructuredEncoding.ItemClass.Item

def docstring(function):
    from common.runtime import memorized

    @memorized.function
    def buildStructure():
        return Structr(function.__doc__)

    return buildStructure

# Todo: integrate formatting with these (structures):
# In otherwords, allow formatting from DOM components.
##    StructuredEncoding.ClassMap
##    StructuredEncoding.ClassMap.Building
##    StructuredEncoding.ClassMap.Loading

def toStructuralString(type, name, values, **classMap):
    # todo: recursive structuralization?
    def _(v):
        if isinstance(v, (list, tuple)):
            return '\n'.join('- %s' % x for x in v) # todo: _(x)
        if isinstance(v, dict):
            # XXX precluding long string forms (::)
            return '\n'.join('%s: %s' % nv for nv in v.items()) # todo: _(nv[1])
        if isinstance(v, str):
            return repr(v)

        ##    if isinstance(v, (long, int, float)):
        ##        return str(v)

        return str(v)

    classMap = '%s\n\n' % indent('\n'.join('%s = %s' % nv for nv in classMap.items())) \
               if len(classMap) else '\n'

    values = indent(_(values))
    return '%s\n%s%s(%s):\n%s\n' % (WMC_PROLOG, classMap, type, name, values)

class FormattingClassMap(dict):
    class Subtype(Object):
        class List(Object, list):
            # In other words:
            #   p = structure.format.subtype('prj', 'common.project.research.structure')
            #   print structure.format.list(p)('a', p('http')) / ['http://google.com']

            # todo: actually be able to list subitems as / members

            ##    def x(name, subtype, *values, **keywords):
            ##        f = structure.format
            ##        p = [f.subtype(n, v) for (n, v) in keywords.iteritems()]
            ##        return f.list(*p)(name, p[0](subtype)) / values

            @property
            def asMap(self):
                return FormattingClassMap((s.name, s.module) for s in self
                                          if isinstance(self, FormattingClassMap.Subtype))

            def __init__(self, *args):
                list.__init__(self, args)
            def __call__(self, *args, **kwd):
                return self.asMap(*args, **kwd)

        def __init__(self, name, module):
            self.name = name
            self.module = module

        def __call__(self, sub):
            return '%s$%s' % (self.name, sub)

    class Item(Object):
        class Bound(Object):
            def __init__(self, item, values):
                self.item = item
                self.values = values

            def __str__(self):
                return self.item.toString(self.values)

        def __init__(self, classMap, type, name):
            self.classMap = classMap
            self.type = type
            self.name = name

        def toString(self, values):
            return self.classMap.toString(self.type, self.name, values)

        def __getitem__(self, values):
            return self.Bound(self, values)
        __div__ = __call__ = __getitem__

    def toString(self, type, name, values):
        return toStructuralString(type, name, values, **self)

    def __call__(self, *args, **kwd):
        return self.Item(self, *args, **kwd)

# todo: blend wmc/wm builtin symbol??
def builtin(**values):
    __builtins__.update(values)

builtin(wmc = Namespace(prolog = WMC_PROLOG),
        structure = Synthetic(format = Synthetic(map = FormattingClassMap,
                                                 subtype = FormattingClassMap.Subtype,
                                                 list = FormattingClassMap.Subtype.List,
                                                 string = toStructuralString)))

def RegisteredStructure(*args, **kwd):
    return Structr(*args, **kwd) # and register

    # getNotePath(object).loading.structure
    # wm(my.workspace["p-cycle"]
    #      .config
    #      .filtering.structure)

regStructr = RegisteredStructure

# Testing.
def main(argv = None):
    global master
    if argv is None:
        from sys import argv

    withArgs = False
    if '-a' in argv:
        argv.remove('-a')
        withArgs = True
    if '--with-args' in argv:
        argv.remove('--with-args')
        withArgs = True

    # Todo: a way to inject the load path into execution environments?

    def readAll(i):
        return i.read().replace('\r', '')
    def loadStructure(filename):
        # Todo: recognize an archive-based structural file, and setup
        # the application objects contained in the landmarks.

        with open(filename) as i:
            return Structr(readAll(i))

    if withArgs:
        filename = argv[1]
        del argv[:2]

        master = {filename: loadStructure(filename)}

        # Todo: Ideally, as an structuralized application component,
        # recognize here, for deferred invocation, replacing master/
        # (gay <generic> object)

        return

    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-d', '--dump', action = 'store_true')
    parser.add_option('-e', '-x', '--examine', action = 'store_true')
    parser.add_option('-g', '--debug', action = 'store_true')
    parser.add_option('-o', '--object')
    (options, args) = parser.parse_args(argv)

    if options.debug:
        import pdb; pdb.set_trace()

    if not options.dump:
        master = StructuredEncoding.ItemClass.Item(dict())
        del args[:1] # apparently this maintains argv

        for filename in args:
            master[filename] = loadStructure(filename)

    elif args:
        for filename in args: # argv[0] script name??
            print(loadStructure(filename))

    # What we're looking here is for the structural module to somehow push a resulting structure up
    # into context, so that we can extract a formal 'main', running as a shell.  I guess we'll just
    # have to use --with-args recognition for now.

    if options.object:
        assert not options.dump

        from os import sep
        (path, members) = splitOne(options.object, ':')
        members = members.split('.')

        path = path.split(sep)
        pathln = len(path)

        for structure in (s for (n, s) in iteritems(master)
                          if n.split(sep)[:-pathln] == path):

            object = access(structure, *members)
            if callable(object):
                object()


    if options.examine:
        from code import InteractiveConsole as IC
        IC(globals()).interact(banner = None)


if __name__ == '__main__':
    main()
