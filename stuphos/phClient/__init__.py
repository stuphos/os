# Core Content Design and Delivery Client
# Todo: move into stuphos.management
# XMLRPC Python API -- requires WRLC
from xmlrpc.client import ServerProxy, MultiCall
from urllib.parse import quote
import ssl
import sys

import op # actionable


HOSTNAME = 'localhost'
PORT = 2172

HOST = '%s:%s' % (HOSTNAME, PORT)
PROTOCOL = 'https'

# client XMLRPC+HTTPS: TLSv1 Unknown Certificate Authority
# [SSL: TLSV1_ALERT_UNKNOWN_CA] tlsv1 alert unknown ca (_ssl.c:590)
# [SSL: HTTP_REQUEST] http request (_ssl.c:590)
# SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:590)

try: namespace
except NameError:
    namespace = dict

auth = login = namespace

class folderUpload(namespace):
    'Package up a directory structure for deployment upload.'

    @classmethod
    def build(self, path, exclude = []):
        if isinstance(exclude, str):
            import re
            m = re.compile(exclude).match

            def exclude(s):
                return m(s) is not None

        elif isinstance(exclude, (list, tuple)):
            exclude = contains(exclude)

        def node(path, relative, contentName, **kwd):
            content = path.platformMapped # .read()
            return dict(path = relative, name = path.basename,
                        **dict(kwd, **{contentName: content}))

        def structure(p, r):
            return node(p, r, 'document')
        def activities(p, r):
            return node(p, r, 'source')

        def document(p, r):
            typeContent = 'application/binary' # todo: get from mimeType[p.extension]
            return node(p, r, 'content', typeContent = typeContent)

        def c(path, type, relative):
            s = []
            a = []
            k = []
            d = []

            for p in path.listing:
                if p.isdir:
                    r = relative + p.basename

                    if p.basename == 'structures':
                        s.append(c(p, structure, r))
                    elif p.basename == 'activities':
                        a.append(c(p, activity, r))
                    else:
                        k.append(c(p, document, r))

                elif not exclude(p):
                    d.append(type(p, r))

            return self(structures = s, activities = a,
                        folders = k, documents = d)

        return c(path, document, '')

    @property
    def package(self):
        # todo: return a package suitable for upload.
        pass


class phClientFS:
    '''
    client.upload(phClientFS(args).structure,
                  path = 'mount/point')

    '''

    def __init__(self, path):
        self.path = io.path(path)

    @property
    def structure(self):
        if self.path.isdir:
            new = classOf(self)
            return dict((path.basename, new(path).structure)
                        for path in self.path.listing)

        return self.path.read()


def deploy(client, path, *args, **kwd):
    '''
    # python phClient -u me -p none deploy repository/deploy projectName

    def deploy(client, path, *args, **kwd):
        script = r'.*repository/deploy\.py$' # This shouldn't be necessary...
        client.root += client.folderUpload(path.folder(*args), script)

        '''

    path = io.here(path)
    e = path.extension

    if not e:
        path = path.pyOf
    else:
        assert e == 'py'

    try: d = path.loading.module.deploy
    except AttributeError:
        o = dict(client = client, path = path,
                 args = args, kwd = kwd)

        exec(compile(open(path, "rb").read(), path, 'exec'), globals(), o)
    else:
        return d(client, path, *args, **kwd)


class apiClient:
    @classmethod
    def Main(self, argv = None):
        # See phClient.__main__
        # if __name__ == '__main__': from phClient import apiClient; apiClient.Main()

        from optparse import OptionParser
        parser = OptionParser()
        parser.add_option('--host', default = HOST)
        parser.add_option('--protocol', default = PROTOCOL)
        parser.add_option('--username') # principal
        parser.add_option('--configuration', '-C')
        parser.add_option('--argument-file', '-a', default = list(), action = 'append')
        parser.add_option('--wget-bin')
        parser.add_option('--wget-arg', dest = 'wget_args', default = list(), action = 'append')
        parser.add_option('-c', '--remote-script')
        parser.add_option('--remote-script-path', default = 'script/execute')
        (options, args) = parser.parse_args(argv)

        def buildClient():
            if options.configuration:
                password = open(options.configuration).read().strip()
            else:
                from getpass import getpass
                password = getpass()

            return self(options.username, password,
                        host = options.host,
                        protocol = options.protocol)


        if args:
            import json

            cmd = args[0]
            args = args[1:]

            if cmd == 'call':
                if args:
                    # AUTH = "--username=op -C ~/.ph/runcore/op/password"
                    # SERVICE = "components/services/lisp/do"
                    # INPUT = "ph-runcore-command.lsp"
                    # python -m phClient.cli "$AUTH" call "$SERVICE" -a "$INPUT"

                    args = args + [open(f).read() for f in options.argument_file]
                    print(buildClient().call(*args))

            elif cmd == 'search':
                if args:
                    for (section, results) in buildClient().search(*args).items():
                        print('%s:' % section)
                        print(indent(json.dumps(results)))
                        print('')

            elif cmd == 'deploy':
                if args:
                    deploy(buildClient(), *args, options = options)

            elif cmd == 'upload':
                if args:
                    pass

            elif cmd == 'script':
                import op

                script = options.remote_script
                if script:
                    '''
                    # Browse 'public' permissions in json format.
                    echo public | python3 -m stuphos.phClient script \
                        -c "return 'text/json/dumps'(permissions(), 1)" | less

                    '''

                    assert not args
                    script += '\n'

                else:
                    '''
                    python3 -m stuphos.phClient script -C ~/.thetaplane.apikey \
                            --host thetaplane.com -- << EOF

                        return 'text/json/dumps'(permissions())

                    EOF
                    '''

                    (script,) = args

                    if script == '--':
                        from sys import stdin
                        script = stdin.read()
                    else:
                        script = open(script).read()


                if options.configuration:
                    key = open(options.configuration).read().rstrip()
                else:
                    from getpass import getpass
                    key = getpass('API Key: ')


                wget = io.path(options.wget_bin or '/usr/bin/wget')

                url = f'{options.protocol}://{options.host}/{options.remote_script_path}'

                wgetArgs = (url, '--post-data', f'key={quote(key)}&script={quote(script)}',
                            '-O', '-', '-q', '--content-on-error', '--no-check-certificate')

                wgetArgs += tuple(options.wget_args)

                # import pdb; pdb.set_trace()

                try: r = wget.pipe(*wgetArgs)
                except op.platform.path.CalledProcessError as e:
                    print(f'*** {e.__class__.__name__}', file = sys.stderr)
                    # print(f'  {" ".join(e.cmd)}')
                    print(e.stderrOutput.decode() + '\n' + e.stdOutput.decode(), file = sys.stderr)
                else:
                    print(r.decode())


                # gen/accounts
                '''
                def apikey$exists(key):
                    for p in 'kernel/callObject$' \
                        ('phsite.network.models.Player.objects.filter', \
                         player_name = 'apikey:' + key):

                        return true

                def generate$key():
                    kwd = keywords$()
                    if not 'alphabet' in kwd:
                        kwd['alphabet'] = 'kernel/lookup$'('string.ascii_letters')

                    return '\n'.join(run$python(code, kwd)) <- code:
                        from random import choice
                        __return = (choice(alphabet) for x in range(n))

                def user$claim$generate$apikey(user):
                    while true:
                        key = generate$key()
                        if not apikey$exists(key):
                            user$claim$apikey(user, key)
                            return key


                register$apikey(view):
                    context(trigger)::
                        if request.GET.get('generate'):
                            key = 'gen/accounts/user$claim$generate$apikey' \
                                (request.user)

                            try: filename = request.GET['download']
                            except key$error: pass
                            else:
                                response.headers['Content-Disposition'] = \
                                    'filename=%s; attachment' % 'text/json/dumps' \
                                        (filename)

                            return key

                    template::
                        <a href="?generate=true">Generate new API Key</a><br />
                        <a href="?generate=true&download=true">Download new API Key</a>

                '''


    def __init__(self, username, password, host = HOST, protocol = 'https', runtime = None, **kwd):
        # Note: xmlrpclib._Method.__call__ does not accept keyword arguments.
        if username is None and password is None:
            endpoint = '%s://%s/rpc' % (protocol, host)
        else:
            endpoint = '%s://%s:%s@%s/rpc' % (protocol, username, password, host)

        self.host = host
        self.protocol = protocol

        self.endpoint = endpoint

        self.runtime = runtime if runtime is not None else globals()['runtime'](**kwd)

    @property
    def server(self):
        if self.protocol == 'https':
            return ServerProxy(self.endpoint, context = ssl.SSLContext())

        return ServerProxy(self.endpoint)

    def run(self, *args, **kwd):
        return self.runtime.run(self, *args, **kwd)

    def call(self, method, *args, **kwd):
        return self.server.library.callMethod(method, *args, **kwd)
    __call__ = call

    @property
    def multiCall(self):
        return MultiCall(self.server)

    def search(self, *queryArgs):
        return self.call('core/interface/kernel/librarySearch', *queryArgs)

    def evaluate(self, expression, *args, **kwd):
        return self.server.engine.evaluateAgent(expression, *args, **kwd)


    # Local Emulations.
    def moduleCompile(self, source):
        syntax = self.server.engine.moduleCompile(source)
        return self.syntaxObject(syntax, source = source)

    def moduleAssemble(self, source):
        return self.server.engine.moduleAssemble(source)

    def pathCompile(self, path):
        syntax = self.server.engine.pathCompile(path)
        return self.syntaxObject(syntax, path = path)

    def pathAssemble(self, path):
        return self.server.engine.pathAssemble(path)


    # Object Model.
    def _queryNodeData(self, *args, **kwd):
        return self.server.library.queryNode(*args, **kwd)

    def queryNode(self, *args, **kwd):
        return self.Node(self, self._queryNodeData(*args, **kwd))
    __getitem__ = query = queryNode

    root = property(queryNode)

    def loadChildrenMultiCall(self, children):
        data = self.multiCall
        q = data.library.queryNode

        for c in children:
            q(c.path)

        for (i, c) in data():
            r[i].load(c)

        return children

    def loadChildrenIndividually(self, children):
        for c in children:
            c.load(self._queryNodeData(c.path))

        return children

    loadChildren = loadChildrenIndividually # loadChildrenMultiCall

    def __iter__(self):
        return iter(self.root)

    def node(self, type, **data):
        data['type'] = type
        return self.Node.FromClientAndData(self, **data)

    def folder(self, **data):
        return self.node('directory', **data)
    def module(self, **data):
        return self.node('module', **data)
    def structure(self, **data):
        return self.node('structure', **data)
    def package(self, **data):
        return self.node('package', **data)

    def document(self, **data):
        try: data['content_type'] = data.pop('typeContent')
        except KeyError: pass
        return self.node('document', **data)

    def upload(self, structure, **data):
        return self.node('upload', structure = structure, **data)


    def folderUpload(self, *args, **kwd):
        return self.upload(folderUpload.build(*args, **kwd).package)


    class Node(namespace):
        '''
        client['my/components'] += client.folder \
            (name = 'program', children = \
             [client.structure(name = 'interface', document = '...'),
              client.module(name = 'object', program = '...')])

        '''
        # todo: figure out when exactly nameSlashed is used (read) and not path.

        @classmethod
        def FromClientAndData(self, client, **data):
            # This should be compatible with data from 'exported' node queries,
            # and also from the client.node() method.  But, if you have data
            # directly from exported, use the constructor and skip this method.
            try: path = data['path'] # XXX todo: path as dict item has no meaning... pop?
            except KeyError:
                try: path = data['nameSlashed']
                except KeyError:
                    # An often-used code point.  Note, this gets called for children
                    # of the root node, since no path is supplied.
                    return self(client, **data)
                else:
                    # This _should_ correspond with the trailing part of
                    # nameSlashed.  But if nameSlashed is set and path
                    # is not, then ignore name (which probably shouldn't be set).
                    #
                    # Again: nameSlashed probably shouldn't be used, either...
                    # because it confuses the namespace constructor: it should
                    # be popped from 'data', since it's being passed via keyword.

                    del data['name']

            segments = path
            if isinstance(segments, str):
                segments = segments.split('/')

            # Q: Why was I trying to calculate 'parent'?
            # Parent is derived from nameSlashed, which is set by path...

            try: name = data.pop('name')
            except KeyError:
                name = segments[-1]
                # parent = segments[:-1]

                # If there's no name, then either nameSlashed or path sets
                # the whole name, necessarily.
            else:
                # parent = segments

                # Note: since name is set, if nameSlashed is not set,
                # path must necessarily be set.  But, it is the parent
                # path, so, rebuild the symbol here as a whole name.

                path = '/'.join(segments + [name])

            return self(client, nameSlashed = path,
                        name = name, **data)

        def __init__(self, client, *args, **kwd):
            namespace.__init__(self, *args, **kwd)
            self.client = client

        def __repr__(self):
            # name = nameOf(classOf(self))
            try: return '%s: %s' % (self.type, self.path)
            except TypeError:
                # Unloaded.
                return 'unloaded: %s' % self.name

        def __str__(self):
            return self.name

        @property
        def path(self):
            try: return self.nameSlashed
            except AttributeError:
                # Assume child of root.
                return self.name

        @property
        def parent(self):
            path = self.nameSlashed.split('/')
            if len(path) < 2:
                # Child of root node.
                return '' # None # XXX Must be marshallable!

            return '/'.join(path[:-1])

        @parent.setter
        def parent(self, path):
            if 'nameSlashed' in self:
                raise AttributeError('parent already set; delete it first')

            # Upload nodes may have no names.  These kinds of nodes, when
            # added to their parents, may function relative to the parent.
            try: name = self['name']
            except KeyError: pass
            else:
                if path is not None:
                    path += '/'
                    path += name
                else:
                    path = name

            self.nameSlashed = path

        @parent.deleter
        def parent(self):
            del self.nameSlashed

        def load(self, data = None):
            # Q: Shouldn't this set loaded state upon success?
            try: del self['unloaded']
            except KeyError: pass
            else:
                if data is None:
                    data = self.client._queryNodeData(self.path)

                self.update(data)

            return self
        loaded = property(load)

        def create(self):
            if self.type == 'directory':
                assert self.client.server.library.addFolder(self.parent, self.name)
                self.createChildren()

            elif self.type == 'module':
                assert self.client.server.library.addModule(self.parent, self.name, self.program)
            elif self.type == 'structure':
                assert self.client.server.library.addStructure(self.parent, self.name, self.document)
            elif self.type == 'package':
                assert self.client.server.library.addPackage(self.parent, self.name, self.source)
            elif self.type == 'document':
                assert self.client.server.library.addDocument(self.parent, self.name, self.typeContent, self.content)
            elif self.type == 'upload':
                assert self.upload(self.structure)
            else:
                raise TypeError(self.type)

            return self

        def createChildren(self):
            for node in self.children:
                del node.parent
                self += node

        def add(self, node, name = None):
            if name is not None:
                node.name = name

            node.parent = self.path
            node.create() # XXX todo: if not exists?  Although, this wouldn't be called if it did...

        __add__ = add

        def __iadd__(self, node):
            self.add(node)
            return self

        def __getattr__(self, name):
            try: return object.__getattribute__(self, name)
            except AttributeError as e:
                if name in ('nameSlashed', 'path'):
                    raise e

                try: t = self['type']
                except KeyError:
                    raise TypeError('Untyped node')

                if t == 'module':
                    return self._call(self, name)
                if t == 'directory':
                    return self.getChild(name)

                raise e

        class _call(object):
            def __init__(self, node, name):
                self.node = node
                self.name = name

            def __call__(self, *args):
                return self.node.client.call(self.name, *args)

        def __iter__(self):
            if self.type == 'directory':
                return iter(self.preloadChildren())

            i = client.server.engine.evaluateAgent
            i = i('symbols(node)', node = self.path)
            return iter(i)

        @property
        def children(self):
            if self.type != 'directory':
                raise TypeError('Not a directory')

            return self.preloadChildren()

        def preloadChildren(self):
            try: e = self['children']
            except KeyError:
                return []

            node = classOf(self); client = self.client
            try: path = self.path
            except AttributeError:
                path = None

            for (n, c) in enumerate(e):
                if isinstance(c, str):
                    c = dict(name = c, unloaded = True)
                    if path is not None:
                        c['path'] = path

                    c = self.FromClientAndData(client, **c)
                    e[n] = c

            return e

        @property
        def childrenLoaded(self):
            # Actually retrieve data from server for each child...
            return self.client.loadChildren(self.children)


        @property
        def childrenNames(self):
            return (node.name for node in self.children)

        @property
        def symbols(self):
            return iter(self)

        def getChild(self, name):
            for node in self.children:
                if node.name == name:
                    return node

        __div__ = getChild
        # __getitem__ = getChild


        # Conventional hacks for document type:
        @property
        def typeContent(self):
            try: return self['typeContent']
            except KeyError:
                try: return self['content_type']
                except KeyError:
                    raise AttributeError('content_type/typeContent')

        @typeContent.setter
        def typeContent(self, value):
            self['content_type'] = value

        content_type = typeContent


        def packageUpload(self, structure): # XXX naming
            # note that 'package' in this case is a document structure.
            # todo: something like client.folder('path/to') += client.upload(dict(documents = dict(structures = dict(one = ''))))
            def internalizeType(o):
                if isinstance(o, dict):
                    return dict((n, internalizeType(v)) for (n, v) in o.items())
                elif isinstance(o, (list, tuple)):
                    return list(map(internalizeType, o))

                if not isinstance(o, (int, float, str)): # complex?
                    raise TypeError(o.__class__.__name__)

                return o

            return self.client.server.library.uploadStructure \
                    (self.path, internalizeType(structure))

        upload = packageUpload


    def login(self, playerName, password, *args, **kwd):
        return self.session(self, playerName, password, *args, **kwd)
    def resume(self, sessionId):
        return self.session(self, None, None, sessionId = sessionId)

    class session:
        terminateOnGC = False

        def __init__(self, client, playerName, password, sessionId = None, passwordSend = True):
            self.client = client

            if sessionId is None:
                # XXX Todo: session.open method not supported on circle.
                self.sessionId = self.client.server.session.open(playerName)
                self.terminateOnGC = True

                if passwordSend:
                    self.send(password)
            else:
                self.sessionId = sessionId

        def __repr__(self):
            return '<%s %r>' % (self.__class__.__name__, self.sessionId)

        def __del__(self):
            if self.terminateOnGC:
                # XXX Todo: transition to cleanup object
                pass # self.client.server.session.terminate(self.sessionId)

        def send(self, message):
            return self.client.server.session.send(self.sessionId, message)
        def command(self, name, *args):
            # print(f'[phClient.session.command] {name}')
            return self.client.server.session.command(self.sessionId, name, *args)
        def messages(self, n = -1, timeout = None):
            return self.client.server.session.messages(self.sessionId, n, timeout)

        def loginShell(self, password):
            return self.client.server.session.shell.login(self.sessionId, password)

        # Web Adapter Commands
        def interpretAgent(self, script, params = None):
            return self.command('do-interpret-agent', script,
                                *(() if params is None else (params,)))

        def interpretScript(self, script, params = None):
            return self.command('do-interpret-script', script,
                                *(() if params is None else (params,)))

        def interpretAsyncScript(self, script, nr, params = None):
            return self.command('do-interpret-script-async', script, nr,
                                *(() if params is None else (params,)))


@actionable
def stringCall(name, *arguments):
    # Unifies all string states into one string.
    return '%s(%s)' % (name, ', '.join(mapi(str, arguments)))

operator = stringCall('symbolic.operator')
evaluation = stringCall('symbolic')

def symbolic(name):
    return 'symbolic[%r]' % name

class sourceAssemblization:
    'Assemble source nodes.'

    def __call__(self, node):
        (name, children) = node
        # print name

        method = getattr(self, name, self.default)
        return method(name, node, *children)

    def Identifier(self, name, node, identifier):
        # if identifier == 'symbolic':
        #     raise SyntaxError('reserved symbolic keyword')

        return symbolic(identifier)

    def Const(self, name, node, value):
        return value # repr() # Literal.

    def Suite(self, name, node, *children):
        # This may be wrong.
        return str(list(map(self, children)))

    def FunctionCall(self, name, node, method, arguments):
        return evaluation(*list(map(self, [method] + arguments)))

    # def List(self, name, node, identifier):
    #     return

    def FunctionDefinition(self, name, node, functionName, argumentNames, statements):
        pass

    # class Member(BinaryOperation):
    # class Item(BinaryOperation):

    def default(self, name, node, *children):
        return operator(name, *list(map(self, children)))


    # So: these will need to be formed into some kind of
    # assignment virtualization because suites of statements
    # are all formulated into expressions and assignment-
    # based statements shall not be allowed.

    # class Assign(BinaryOperationBase, Statement):
    # class AugmentedAssign(Assign):
    # class PlusAssign(AugmentedAssign):
    # class MinusAssign(AugmentedAssign):
    # class StarAssign(AugmentedAssign):
    # class SlashAssign(AugmentedAssign):
    # class ModAssign(AugmentedAssign):


class phSyntaxObject(dict):
    # The numerical singleton of the lephton language -- or ella-mental interpreter.
    @classmethod
    def FromServer(self, syntax, **kwd):
        return self(syntax, **kwd)

    def __init__(self, syntax, **kwd):
        dict.__init__(self, kwd)
        self.tree = syntax


    @property
    def emulation(self):
        # 'source' is a builtin provided by op.runtime.virtual.objects
        return source.code(self.sourceAssemblization)

    assemblizationClass = sourceAssemblization

    @property
    def sourceAssemblization(self):
        # Return a text format of the syntax tree encoded into an emulation context.
        #
        # The idea is to return a form of the syntax that virtualizes all of the
        # syntax elements that comform to op.compute.syntactic.operational.

        # For now...
        return self.assemblizationClass()(self.tree)


# Install the following object into into operational client.
apiClient.syntaxObject = phSyntaxObject.FromServer


class runtime:
    '''
    # Use as a base class for evaluating compiled emulations.

    client = apiClient(runtime = runtime({'$': library}))
    parallel = action(future.Work, client.run)
    w = parallel(source)

    '''

    def __init__(self, symbols = None, **kwd):
        # Natives.
        if symbols is None:
            symbols = dict()

        symbols.update(kwd)
        self.symbols = symbols


    # Operations.
    def __getitem__(self, name):
        return self.symbols[name]

    def __call__(self, method, *operands, **kwd):
        return method(*operands, **kwd)

    def operator(self, name, *operands, **kwd):
        method = getattr(self, name)
        return method(*operands, **kwd)


    def Addition(self, left, right):
        return left + right


    # Bind to client.
    def run(self, client, source, *args, **kwd):
        code = client.moduleCompile(source).emulation.code
        function = code.function(dict(symbolic = self))

        return function(*args, **kwd)


class nativeSession:
    '''
    itham = 'network/game/session'('runphase.com:2172', 'itham', 'ithams-password')
    task$(_processSessionMessages, session, itham)

    def _processSessionMessages(session, player):
        while true:
            _processMessages(session, player.messages)

    def _processMessages(session, messages):
        for msg in messages:
            act(_processMessage, [session] + msg)

    def _processMessage(session, type):
        msg = arguments().slice(2)

        if type == 'output':
            session.sendln(msg[0])

    _processMessages(session, itham + 'return $.network.stats.users().display()')
    itham('look board')

    '''

    def __init__(self, frame, host, playerName, password, passwordSend = True):
        passwordSend = bool(passwordSend)

        task = frame.task
        task.checkAccessSystem(['system:network', 'https', host, 'rpc'], 'write')
        client = apiClient(None, None, host = host) # , protocol = 'http')

        task -= frame

        # print(f'[phClient.session] {client} {task} {self._pool}')
        # debugOn()


        @self._pool.task(task)
        def connect(_):
            from xmlrpc.client import Fault

            print(f'[phClient.session.connect] START: {client} {playerName}')

            try: self._session = client.login(playerName, password, passwordSend = passwordSend)
            except Fault as e:
                # XXX Todo: hide system traceback. :skip:
                raise e

            print(f'[phClient.session.connect] DONE: {self}')
            return self

    def _action(self, function, *args, **kwd):
        from stuphos.kernel import vmCurrentTask
        task = vmCurrentTask()
        task -= task.frame

        @self._pool.task(task)
        def action(_):
            # from xmlrpc.client import Fault

            try: return function(*args, **kwd)
            # except Fault as e:
            except Exception as e:
                # XXX Todo: hide system traceback. :skip:
                raise e

            # try: result = function(*args, **kwd)
            # except Exception as e:
            #     debugOn()
            #     raise e

            # debugOn()
            # return result

    def send(self, message):
        return self._action(self._session.send, message)
    def command(self, name, *args):
        return self._action(self._session.command, name, *args)

    __call__ = send

    # @property
    def messages(self):
        return self._action(self._session.messages, timeout = 30)

    def loginShell(self, password):
        return self._action(self._session.loginShell, password)

    def interpretAgent(self, script, params = None):
        return self._action(self._session.interpretAgent, script, params = params)
    def interpretScript(self, script, params = None):
        return self._action(self._session.interpretScript, script, params = params)

    def interpretAsyncScript(self, script, nr, params = None):
        return self._action(self._session.interpretAsyncScript, script, nr, params = params)


    def __add__(self, script):
        return self.interpretScript(script)
    __lshift__ = __add__


    @property
    def _lookbackSession(self):
        # XXX port
        if self._session.client.host in ['localhost', '127.0.0.1']:
            mgr = runtime[runtime.Web.Adapter.SessionManager]
            return mgr.getSessionByIdEx(None, self._session.sessionId)
