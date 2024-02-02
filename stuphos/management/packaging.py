# Extensions -- Executable.
from stuphos.etc.tools.strings import indent, nling

from base64 import b64encode
from json import dumps as toJsonString, loads as loadJsonString

PACKAGE_META_NAME = '.package.meta'


def root_rewriteNode(node):
    # Transform tree root node name.
    if node['name'] is None:
        node['name'] = ''

    # debugOn()
    return node


# renderLibraryPackage
def node_type_libraryConvert(type, node):
    if type == 'directory':
        return (type, node['name'], map(node_libraryConvert, node['children']))

    elif type == 'module':
        return (type, node['name'], node['program'])

    elif type == 'structure':
        return (type, node['name'], node['document'])

    elif type == 'media':
        # content_type
        return (type, node['name'], node['content'])


def node_libraryConvert(node):
    type = node['type']

    if type == 'module':
        # programmer
        yield from node_type_libraryConvert(node)[:2]

    elif type == 'structure':
        # programmer content owner
        yield from node_type_libraryConvert(node)[:2]

    elif type == 'media':
        yield from node_type_libraryConvert(node)[2:]

    elif type == 'directory':
        for (i_type, i_name, i_data) in map(node_type_libraryConvert, node['children']):
            if i_type == 'directory':
                # Collect interfaces
                i = dict()
                r = dict(interfaces = i)

                for (name, data) in i_data:
                    if name == 'interfaces':
                        r.update(data)
                    else:
                        i[name] = data

                yield r

                # yield (i_name, dict(i_data))

            elif i_type == 'module':
                yield (i_name, i_data)

            elif i_type == 'structure':
                yield ('interfaces', {i_name: i_data})


def node_libraryToPackage(node):
    return node_libraryConvert \
        (root_rewriteNode(node))

def libraryToPackage(node):
    return node_libraryToPackage \
        (node.exported)


# Render from library node.
def b64_encode(s):
    # treat as bytes (for media content)
    # s = s.encode()

    return b64encode(s).decode()
# b64_encode = b64encode 

def quoteStringIf(s):
    return repr(s) if (not s or ':' in s) else s

def renderOwnedContent(node, srcContent, srcOwner, destContent, destOwner, fixupContentHeading):
    progr = node.get(srcOwner)
    if progr: # Note: filter all emptinesses
        yield '%s:' % quoteStringIf(node['name'])

        yield '    %s: %s' % (destOwner, progr)
        yield '    %s::' % destContent

        yield indent(indent(node[srcContent])) # todo: fixupContentHeading?

    else:
        yield '%s::' % quoteStringIf(node['name'])
        yield indent(fixupContentHeading(node[srcContent]))


def render_packageConvert(node, fixupHeading = False):
    def fixupContentHeading(content):
        return content.lstrip() if fixupHeading else content

    @nling
    def packageConvert(node):
        type = node['type']

        if type == 'directory':
            i = node['children']

            if i:
                yield '%s:' % quoteStringIf(node['name'])

                s = [] # structures collection
                m = [] # media collection

                for c in i:
                    if c['type'] == 'structure':
                        s.append(c)
                        continue

                    elif c['type'] == 'media':
                        m.append(c)
                        continue

                    yield indent(packageConvert(c))

                if s:
                    # yield indent('interfaces$:')
                    yield indent('interfaces:')

                    for c in s:
                        yield indent(packageConvert(c), level = 2)

                if m:
                    # yield indent('media$:')
                    yield indent('media:')

                    for c in m:
                        yield indent(packageConvert(c), level = 2)

            else:
                yield '%s: []' % quoteStringIf(node['name'])

        elif type == 'module':
            yield from renderOwnedContent(node,
                                          'program', 'programmer',
                                          'program', 'programmer',
                                          fixupContentHeading)

        elif type == 'structure':
            yield from renderOwnedContent(node,
                                          'document', 'programmer',
                                          'content', 'owner',
                                          fixupContentHeading)

        elif type == 'media':
            content_type = node['content_type']
            if content_type:
                yield '%s:' % quoteStringIf(node['name'])

                yield '    content_type: %s' % content_type
                yield '    content::'

                content = node['content']
                if isinstance(content, str):
                    content = content.encode()

                yield indent(indent(b64_encode(content)))

            else:
                yield '%s::' % quoteStringIf(node['name'])
                yield indent(b64_encode(node['content']))


    return packageConvert(root_rewriteNode(node))


def renderPackageString(node, *args, **kwd):
    return render_packageConvert \
        (node.exported, *args, **kwd)


class filesystem:
    # Represent a folder tree as structural input to the upload routine.

    packageMetaName = PACKAGE_META_NAME

    def __init__(self, path, **kwd):
        self.path = path
        self.config = kwd

        try: self.packageMetaName = kwd.pop('packageMetaName')
        except KeyError: pass

    def contents(self, path):
        value = path.open('r+b').read()
        try: return value.decode()
        except UnicodeDecodeError as e:
            print(f'[pkging$filesystem$items] {path}: {e}')
            return value

        return path.read() # .platformMapped

    def __len__(self):
        return len(self.path.listing)

    def __getitem__(self, name):
        if name == self.packageMetaName:
            return self.path(self.packageMetaName).read()

        if name in ['structures', 'interfaces']:
            try: return dict((p.basename, self.contents(p)) for p in
                             self.path(name).listing if not p.isdir)

            except FileNotFoundError:
                return dict()

        raise KeyError(name)

    def ignore(self, path):
        # import pdb; pdb.set_trace()
        return path.basename in self.config.get('ignore', [])

    def iteritems(self):
        try: i = self.path.listing
        except FileNotFoundError: pass
        else:
            for p in i:
                if self.ignore(p):
                    continue

                if p.isdir:
                    yield (p.basename, self.__class__(p))
                else:
                    try: yield (p.basename, self.contents(p))
                    except UnicodeDecodeError as e:
                        print(f'[pkging$filesystem$items] {p}: {e}')

    def items(self):
        return list(self.iteritems())


def packageBuild(path, **config):
    @nling
    def w(o):
        if isinstance(o, (dict, filesystem)):
            for (name, value) in o.items():
                if isinstance(value, (list, tuple, dict, filesystem)):
                    yield f'{name}:'
                    yield indent(w(value))

                elif isinstance(value, bytes):
                    pass
                elif isinstance(value, str):
                    yield f'{name}::'
                    yield indent(value)

                else:
                    yield f'{name}: {repr(value)}'

        elif isinstance(o, (list, tuple)):
            if o:
                for value in o:
                    o = w(o)
                    o = o.split('\n')
                    if len(o) > 1:
                        yield '- ' + o[0]
                        yield indent('\n'.join[1:], tab = '  ')
                    else:
                        yield '- ' + o[0]
            else:
                yield '[]'

        else:
            yield repr(o)

    return w(filesystem(path, **config))


def extractOwnedContent(s, content, owner):
    try: content = s[content]
    except KeyError: pass
    else:
        # If program is set, programmer must be set or it's added as a folder.
        try: owner = s[owner]
        except KeyError: pass
        else:
            if len(s) == 2:
                return (content, owner)


def uploadAttributes(structure, ignore_package_meta = None):
    '''
    library:
        # No particular structure besides package and library interpretation.
        def module$language(allowed, node, language):
            # assert nodeType(node) == 'Activity' # 'module'

            def filterClass(allowed, item):
                if item[0] in allowed:
                    return item

                return []

            COMPILER_CLASSES = 'kernel/getAttrUnsafe' \
                (node, '_core').COMPILER_CLASSES

            COMPILER_CLASSES = mapping \
                (map(filterClass.action(allowed),, \
                     COMPILER_CLASSES.items()))

            'kernel/getAttrUnsafe'(node, '_node') \
                .compilerClass = 'kernel/lookup$' \
                    (COMPILER_CLASSES[language])


        def enable$package$language(point, package, allowedClasses):
            attrs = 'kernel/callObject$'('stuphos.management.packaging.uploadAttributes', package)

            for item in attrs.items():
                scatter(item, 'name', 'ns')
                path = point + name

                try: language = ns['library.language']
                except key$error: pass
                else: module$language(allowedClasses, \
                    library(path), language)

            usage:
                enable$language('org/path/')

    '''

    name = ignore_package_meta if isinstance(ignore_package_meta, str) else PACKAGE_META_NAME

    # print(f'loading {name}', file = sys.stderr)

    try: attributes = structure[name]
    except KeyError as e:
        # print(', '.join(structure))
        raise e
    else:
        if not isinstance(attributes, str):
            raise ValueError(f'Expected simple text for {name}, got {type(attributes)}')

        return loadJsonString(attributes)


ALT_TYPES = ('structures', 'interfaces', 'media')

# Todo: ignore_package_meta is used as the package meta filename.
def uploadStructure(core, path, structure, set_programmers = False,
                    ignore = None, folders = None, attributes = None,
                    ignore_package_meta = False, srcpath = None):
    structs = []
    media = []

    if srcpath is None:
        srcpath = path


    reserved = ALT_TYPES + ((PACKAGE_META_NAME,) if ignore_package_meta is True
                            else (() if not ignore_package_meta else (ignore_package_meta,)))

    # import sys
    # print(f'loading {attributes}', file = sys.stderr)

    if attributes == 'load':
        attributes = uploadAttributes(structure, ignore_package_meta)
        # print(f'loaded {attributes}', file = sys.stderr)

    elif not isinstance(attributes, dict):
        attributes = dict()

    def getOwner(dest, name):
        if srcpath:
            dest = dest[len(srcpath)+1:]

        # import sys
        # print(f'getting owner for {dest}/{name}', file = sys.stderr)

        try: return attributes[f'{dest}/{name}']['owner']
        # try: r = attributes[f'{dest}/{name}']['owner']
        except KeyError:
            pass
        # else:
        #     print(f'result: {r}', file = sys.stderr)
        #     return r


    try: structs.extend(list(structure['structures'].items()))
    except KeyError: pass

    try: structs.extend(list(structure['interfaces'].items()))
    except (KeyError, AttributeError): pass
    # except AttributeError:
    #     # Because the interfaces item might be None...
    #     debugOn()

    try: media.extend(list(structure['media'].items()))
    except KeyError: pass
    # except AttributeError:
    #     debugOn()

    services = [(name, s) for (name, s) in structure.items()
                if name not in reserved]

    def ensure(path):
        try: u = core.root.lookup
        except AttributeError: pass
        else:
            path = path.split('/')

            for i in range(1, len(path)+1):
                folder = path[:i]

                try: u(*folder)
                except KeyError:
                    core.addFolder('/'.join(folder[:i-1]), folder[-1])

    def isFolder(path, name):
        if folders:
            return f'{str.__str__(path)}/{str.__str__(name)}' in folders

    def install(path, struct, add, isMedia = False, isStructure = False):
        # head = (path + '/') if path else ''

        if path:
            head = path + '/'
            ensure(path)
        else:
            head = ''

        for (name, s) in struct:
            name = str(name) # Because it gets __sqlrepr__ attr which might be complex.

            if ignore and ignore(name): # todo: this should probably turn into ignore(path, name)
                continue

            if isMedia:
                if isinstance(s, str):
                    s = b64_decode(s)
                    add(path, name, s)

                elif isinstance(s, (dict, filesystem)):
                    try: content = s['content']
                    except KeyError: pass
                    else:
                        try: content_type = s['type']
                        except KeyError: content_type = None

                        content = b64_decode(content)
                        add(path, name, content, content_type)

            elif isinstance(s, str):
                ensure(path)

                progr = getOwner(path, name) if set_programmers else None

                # import sys
                # print(f'{add.__name__}({path}/{name}, {progr})', file = sys.stderr)

                # if name == 'system:initialize':
                #     debugOn()

                # logOperation(add(path, name, s, programmer = progr).programmer)
                add(path, name, s, programmer = progr)

            elif isinstance(s, (dict, filesystem)):
                if not isFolder(path, name):
                    ownedContent = extractOwnedContent(s, 'content', 'owner') if isStructure \
                                   else extractOwnedContent(s, 'program', 'programmer')

                    if ownedContent is not None:
                        # debugOn()
                        (content, progr) = ownedContent

                        ensure(path)

                        add(path, name, content, programmer = progr if set_programmers else None)

                        # core.addModule(path, name, content,
                        #                programmer = progr if set_programmers else None)


                        # print(f'adding module: {path} {name} [{progr}]')

                        # XXX use add? this will allow structures to set programmer/owner.
                        # core.addModule(path, name, content)
                        # if set_programmers:
                        #     core.setActivityProgrammer(path.split('/') if path else [],
                        #                                name, progr)

                        continue

                # debugOn()

                # print(f'adding folder: {path}/{name}')
                # assert not '/' in name
                if path:
                    ensure(path + '/' + name)
                else:
                    ensure(name)

                # todo: yield these args
                uploadStructure(core, head + name, s,
                                set_programmers = set_programmers,
                                ignore = ignore, folders = folders,
                                attributes = attributes,
                                ignore_package_meta = ignore_package_meta,
                                srcpath = srcpath) # recurse


    # st = dict(structs)
    # if 'library' in st:
    #     debugOn()

    # print(f'install {path} {", ".join}')

    install(path, structs, core.addStructure, isStructure = True)
    install(path, services, core.addModule)
    install(path, media, core.addMedia, isMedia = True)


class fsPackageCore:
    # AgentSystem replacement for extracting packages to filesystem.
    class Node:
        pass

    class Folder(Node, dict):
        def lookup(self, path, *args):
            return self[path]

    def __init__(self):
        self.init()

    def addFolder(self, *args, **kwd):
        print('addfolder ' + str(args))
    def addModule(self, *args, **kwd):
        print('addmodule ' + str(args))
    def addStructure(self, *args, **kwd):
        print('addstructure ' + str(args))
    def addMedia(self, *args, **kwd):
        print('addmedia ' + str(args))

    def init(self):
        self.root = self.Folder()
    def finished(self):
        pass


class bufferPackageCore(fsPackageCore):
    '''
    import AgentSystem as baseAgentSystem

    class package_resident:
        packageString = property(renderPackageString)
        package_library = property(libraryToPackage)


    class packageCore(bufferPackageCore, package_resident):
        # ETL Format Optimization:

        @property
        def packageString(self):
            return renderPackageString(self.root)


        class Node(baseAgentSystem.Node, package_resident):
            class Module(baseAgentSystem.Node.Module, package_resident):
                pass

            class Structure(baseAgentSystem.Node.Structure, package_resident):
                pass

            class Document(baseAgentSystem.Node.Document, package_resident):
                pass


            # class Module(baseAgentSystem.Node.Module):
                # @property
                # def exported(self):
                #     progr = self.programmer
                #     return dict(type = 'module',
                #                 name = self.name,
                #                 nameSlashed = self.nameSlashed,
                #                 programmer = None if progr is None else progr.principal,
                #                 program = self.program)

            # class Structure(baseAgentSystem.Node.Structure):
                # @property
                # def exported(self):
                #     progr = self.programmer
                #     return dict(type = 'structure',
                #                 name = self.name,
                #                 nameSlashed = self.nameSlashed,
                #                 document = self.document,
                #                 programmer = None if progr is None else progr.principal)

            # class Document(baseAgentSystem.Node.Document):
                # @property
                # def exported(self):
                #     return dict(type = self.KEY,
                #                 name = self.name,
                #                 content_type = self.type,
                #                 nameSlashed = self.nameSlashed,
                #                 content = self.content)

            # class Media(Document):

            # class baseLink(baseAgentSystem.Node.baseLink): # (Document):
            # class SystemLink(baseLink, baseAgentSystem.Node.SystemLink):
            # class SymbolicLink(SystemLink):


            # @property
            # def exported(self, children = True):
            #     r = dict(type = 'directory',
            #              name = self.name)

            #     if children:
            #         sub = []
            #         for c in self.values():
            #             try: sub.append(c.exported)
            #             except AttributeError:
            #                 pass

            #         r['children'] = sub
            #     else:
            #         r['children'] = list(self.keys())

            #     return r

    '''

    # Duplicate of library model:
    def addFolder(self, path, name):
        folder = self[path] if path else self.root
        node = folder + name
        self.saveNode(node, setEntityId = True)
        return node
    def addModule(self, path, name, source, programmer = None):
        folder = self[path] if path else self.root
        head = (path + '/') if path else ''
        progr = None if programmer is None else getWebProgrammer()(programmer)
        node = self.Node.Module(name, head + name, source, progr, self)
        folder[name] = node
        self.saveNode(node, setEntityId = True)
        return node
    def addStructure(self, path, name, source, programmer = None):
        folder = self[path] if path else self.root
        head = (path + '/') if path else ''
        progr = None if programmer is None else getWebProgrammer()(programmer)
        node = self.Node.Structure(name, head + name, source, progr, self)

        try: folder[name] = node
        except TypeError:
            raise InvalidNewStructurePath(folder, name)

        # debugOn()
        self.saveNode(node, setEntityId = True)
        return node
    def addDocument(self, path, name, type, source):
        folder = self[path] if path else self.root
        head = (path + '/') if path else ''
        node = self.Node.Document(name, type, head + name, source, self)
        folder[name] = node
        self.saveNode(node, setEntityId = True)
        return node
    def addMedia(self, path, name, content, content_type = None):
        'A version of addDocument that redefines the arguments.'
        folder = self[path] if path else self.root
        head = (path + '/') if path else ''
        node = self.Node.Media(name, content_type, head + name, content, self)
        folder[name] = node
        self.saveNode(node, setEntityId = True)
        return node


class unpackCoreAttr:
    packageMetaName = PACKAGE_META_NAME

    def init(self):
        self.attributes = dict()

    def setOwnerAttribute(self, path, name, owner):
        self.attributes.setdefault \
            (f'{path}/{name}', dict()) \
                ['owner'] = owner


class fsUnpackCore(unpackCoreAttr, fsPackageCore):
    def __init__(self, path):
        self.path = io.path(path)
        super().__init__()

    def finished(self):
        # Overwrite.
        self.path(self.packageMetaName).write \
            (toJsonString(self.attributes))


    def getLocalPath(self, path, name, ensure = False):
        nparts = len(self.path.parts)
        local = self.path
        for p in path.split('/') + [name]:
            local = local(p)
            if len(local.parts) < nparts:
                raise ValueError(f'{path}/{name}')

        if ensure:
            local.folder.ensure()

        return local

    def addFolder(self, path, name):
        # print('folder', self.getLocalPath(path, name, ensure = False))
        self.getLocalPath(path, name, ensure = False).ensure()

    def addModule(self, path, name, content, programmer = None):
        # print('module', self.getLocalPath(path, name, ensure = True))
        if programmer is not None:
            self.setOwnerAttribute(path, name, programmer)

        self.getLocalPath(path, name, ensure = True).write(content)

    def addStructure(self, path, name, content, content_type = None, programmer = None):
        # print('structure', self.getLocalPath(f'{path}/interfaces', name, ensure = True))
        if programmer is not None:
            self.setOwnerAttribute(path, name, programmer)

        self.getLocalPath(f'{path}/interfaces', name, ensure = True) \
            .write(content)

    def addMedia(self, path, name, content, content_type = None):
        # print('media', self.getLocalPath(f'{path}/media', name, ensure = True))
        self.getLocalPath(f'{path}/media', name, ensure = True) \
            .write(content)


def packageUnpackTo(structure, dest_dir, mount_point = None, fsUnpackClass = fsPackageCore, **kwd):
    'Output package to filesystem (or something that takes an argument).'

    if isinstance(structure, str):
        from stuphos.language.document.interface import document
        structure = document(structure)

    # debugOn()

    try: root_name = kwd.pop('root_name')
    except KeyError: pass
    else:
        if len(structure) != 1:
            raise ValueError(f'root_name specified but input structure mapping must have length of 1 (has {len(structure)}')

        current = list(structure.keys())[0]
        if current != root_name:
            structure[root_name] = structure.pop(current)

    core = fsUnpackClass(dest_dir, **kwd)
    # debugOn()
    uploadStructure(core, mount_point or '', structure, set_programmers = True)
    core.finished()

    return core


def packageStreamUnpackTo(input, output, mount_point = None):
    '''
    --admin-script=ph.interpreter.mental.library.extensions.packageStreamUnpackTo \
    -x bin.package -x bin

    '''

    if input == '<stdin>':
        from sys import stdin as input
    else:
        input = open(input).read()

    return packageUnpackTo(input, output, mount_point = mount_point,
                           fsUnpackClass = fsUnpackCore)


class packageArchiveCore(unpackCoreAttr, fsPackageCore):
    '''
    code::
        tar_packageArchive = action('kernel/callObject$seq', \
            packageArchive.value) <- packageArchive:

            - stuphos
            - management
            - packaging
            - packageArchiveCore
            - unpackTarGzip


        def pathToTarArchive(path):
            return tar_packageArchive \
                (library(path).packageString) \
                    .archive.getvalue()


    interfaces/views::
        # var package_wwwArchive = $.get('/page/views/www');

        www(alias): views/package-archive/www

        package-archive(view):
            context(trigger)::
                if is$deep$view(path):
                    return request.user.securityContext \
                        (..code.pathToArchive(path))

    '''

    @classmethod
    def unpack(self, input, archive, **kwd):
        return packageUnpackTo(input, archive,
            fsUnpackClass = self, **kwd)


    # @classmethod
    # def unpackZip(self, input, *args, **kwd):
    #     return self.unpack(input,
    #         self._zipArchive
    #             (*args, **kwd),
    #             )

    @classmethod
    def unpackTarGzip(self, input, *args, **kwd):
        # return self.unpack(input,
        #     self._tarArchive
        #         (*args, **kwd),
        #         )

        return self.unpack \
            (input, self._tarArchive
                ._bufferCreate())


    class _archiveAdapter:
        def __init__(self, *args, **kwd):
            self.archive = self._open_archiveClass(*args, **kwd)

        def _open_archiveClass(self, *args, **kwd):
            return self._archiveClass(*args, **kwd)

        def writeArchive(self, *args, **kwd):
            return self.archive.writeArchive(*args, **kwd)
        def writeInsertion(self, insertion, path, name, content):
            return self.writeArchive(f'{path}/{insertion}{name}', content)

    class _zipArchive(_archiveAdapter):
        from zipfile import ZipFile as _archiveClass

    class _tarArchive(_archiveAdapter):
        from tarfile import TarFile as _archiveClass

        # def _open_archiveClass(self, name=None, mode="r", fileobj=None, **kwargs):

        @classmethod
        def _bufferCreate(self):
            from io import StringIO as bufferClass # BytesIO as bufferClass
            return self(fileobj = bufferClass())

        def getvalue(self):
            return self.archive.fileobj.getvalue()


    def __init__(self, archive):
        self.archive = archive
        self.init()


    def addOwnedContent(self, insertion, path, name, content, programmer = None):
        if programmer is not None:
            self.setOwnerAttribute \
                (path, name, programmer)

        return self.archive.writeInsertion \
            (insertion, path, name, content)


    def addFolder(self, path, name):
        # self.archive.writestr(f'{path}/{name}', '')
        pass

    def addModule(self, *args, **kwd):
        return self.addOwnedContent('', *args, **kwd)
    def addStructure(self, *args, **kwd):
        return self.addOwnedContent('interfaces/', *args, **kwd)
    def addMedia(self, *args, **kwd):
        return self.addOwnedContent('media/', *args, **kwd)


    def finished(self):
        # Overwrite.
        self.archive.writeArchive \
            (self.packageMetaName,
             toJsonString(self.attributes))


class normalContinue(Exception):
    def __init__(self, options, args):
        self.options = options
        self.args = args

        raise self


def unpackMain(options, args):
    if len(args) != 2:
        print('Usage: unpack <input package> <output path>')
        return

    (input, output) = args

    from stuphos.runtime.registry import getRegistry
    getRegistry(create = True) # stuphos.structure

    packageStreamUnpackTo(input, output, options.mount_point)


class project:
    def __init__(self, path, config, options):
        if config == '.':
            config = '.wmc'

        self.path = path = io.path(path)
        self.configpath = path(config)
        self.options = options

    @property
    def config(self):
        return self.configuration(self.path.config.cfgOf.value)

    class configuration(dict):
        def __init__(self, fileInputValue):
            pass

    def package(self, args):
        self.options.input_file = str(self.path)
        normalContinue(self.options, args)

    def upload(self, args):
        cfg = self.cfg


    @classmethod
    def Operate(self, options, args):
        assert args
        p = project(io.here, options.project, options)

        cmd = args[0]
        rest = args[1:]

        if cmd == 'upload':
            return p.upload(rest)
        elif cmd == 'package':
            return p.package(rest)


def restricted(self, *args):
    r = self

    for a in args:
        if isinstance(a, str) and not isinstance(a, io.path):
            a = io.path(a)

        for p in a.parts:
            if p == '..':
                if len(r) > len(self):
                    r = r.folder

            elif p != '.':
                r = r(p)

    return r

ContentIsFolder = object()

from collections import namedtuple

updateFSOpTuple = namedtuple('UpdateFSOp', 'base path content type')
updateFSTypeTuple = namedtuple('UpdateFSType', 'name commit')

def updateFSTree(base, files):
    base = io.path(base)
    for (name, content) in files:
        path = restricted(base, name)

        if content is ContentIsFolder:
            def op(base, path, content):
                def buildFolder():
                    path.ensure()

                return ('folder', buildFolder)

        else:
            def op(base, path, content):
                def writeFileContent():
                    path.ensure(folder_only = True)
                    path.write(content)

                return ('file', writeFileContent)

        yield updateFSOpTuple(base, path, content, \
               updateFSTypeTuple(*op(base, path, content)))


# @apply
# class defaultIgnore:
#     def __contains__(self, object):
#         return object in ['.git']

defaultIgnore = ['.git']


USAGE = \
'''
export PYTHONPATH=<path-to-common>:<path-to-stuphos>
python -m stuphos.management.packaging -o jhcore.package path/to/LambdaMOO/core.db

'''.rstrip()

def main(argv = None):
    # debugOn()
    from optparse import OptionParser
    parser = OptionParser(usage = USAGE)
    parser.add_option('-o', '--output-file', '--output')
    parser.add_option('-i', '--input-file', '--input')
    parser.add_option('-u', '--unpack', action = 'store_true')
    parser.add_option('--mount-point')
    parser.add_option('-p', '--project') # dest = 'input_file'
    parser.add_option('-v', '--verbose', action = 'store_true')
    (options, args) = parser.parse_args(argv)

    try: import op
    except Exception as e:
        print(f'{e.__class__.__name__}: {e}')

    try:
        if options.project:
            return project.Operate(options, args)

        if options.unpack:
            return unpackMain(options, args)

    except normalContinue as e:
        options = e.options
        args = e.args

    if options.input_file:
        assert not args
        input = options.input_file
    else:
        assert len(args) == 1
        input = args[0]

    if options.output_file:
        output = open(options.output_file, 'w')
    else:
        from sys import stdout as output

    import op

    output.write(str(packageBuild \
        (io.path(input),
         ignore = defaultIgnore)))

if __name__ == '__main__':
    main()
