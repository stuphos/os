# Todo: this better.
#  Copyright 2011-2014 Thetaplane.  All rights reserved.
#  
from urllib.parse import urlparse, urlunparse, ParseResult #, ResultMixin
from urllib.request import urlopen
from urllib.parse import urlencode
from collections import namedtuple

try: from cgi import parse_qsl
except ImportError:
    from urllib.parse import parse_qsl

from http.cookiejar import split_header_words # 2 seconds debugging

# from op.runtime import Object

def query2dict(qs):
    return dict(parse_qsl(qs))

##    @apply
##    class V1:
##        # namedtuple-based class, similar to urlparse construct, separate query
##        # string class.
##        class Url(namedtuple('Url', 'scheme netloc path params queryString fragment'), ResultMixin):
##            @classmethod
##            def Parse(self, url):
##                pr = urlparse(url)
##                return self(pr.scheme, pr.netloc, pr.path, pr.params,
##                            pr.query, pr.fragment)
##
##            __slots__ = ()
##
##            def geturl(self):
##                return urlunparse(self)
##
##            @property
##            def query(self):
##                try: return self.__queryObj
##                except AttributeError:
##                    q = self.QueryObject(query2dict(self.queryString))
##                    qo = self.__queryObj = q
##                    return qo
##
##            class QueryObject(dict):
##                def __init__(self, values):
##                    dict.__init__(self, values)
##                    self.__dict__ = self
##
##                    for (n, v) in self.items():
##                        self[n] = self.Value(v)
##
##                class Value(str):
##                    def __init__(self, u):
##                        # str.__init__(self, u)
##                        self.url = Url.Parse(u)
##
##            @classmethod
##            def Open(self, urlString):
##                return urlopen(urlString)
##
##            def get(self, **data):
##                # todo: merge data into query string
##                return self.Open(self.geturl())
##
##            def post(self, **data):
##                return self.Open(self.geturl())
##
##            @property
##            def soup(self):
##                from BeautifulSoup import BeautifulSoup as bsoup
##                return bsoup(self.get())
##
##        DEFAULT_PORT = None # 80
##        DEFAULT_PROTO = 'http'
##
##        class Host:
##            # host = Host('localhost')
##            # host[host / 'structure'] = dict(param = 'this data')
##            def __init__(self, name, port = None, proto = None):
##                self.__name = name
##                self.__port = port or DEFAULT_PORT
##                self.__proto = proto or DEFAULT_PROTO
##
##            class Request:
##                # Hmm, why decoupled from host object?
##                def __init__(self, path):
##                    self.path = path
##                    self.params = dict()
##
##                def getUrl(self, proto, hostname, port):
##                    host = hostname if port is None else '%s:%s' % (hostname, port)
##                    query = urlencode(self.params) # pass as query
##                    return Url(proto, host, self.path, '', query, '')
##
##                def set(self, name, value):
##                    self.params[name] = value
##                    return self
##
##                def update(self, **kwd):
##                    self.params.update(kwd)
##                    return self
##
##            def __div__(self, path):
##                return self.Request(path)
##
##            def path(self, request):
##                if isinstance(request, basestring):
##                    request = self.Request(request)
##                if not isinstance(request, self.Request):
##                    raise TypeError(type(request).__name__)
##
##                return self.urlFor(request)
##
##            def __getitem__(self, request):
##                return self.path(request).get()
##            def __setitem__(self, request, value):
##                self.path(request).post(**value)
##
##            def urlFor(self, request):
##                return request.getUrl(self.__proto, self.__name, self.__port)

# Pentacle Urls:
# who cares.
##    import re
##    class PentacleServiceEndpoint(namedtuple('PentacleServiceEndpoint', 'scheme host port service')):
##        # Parses into the 'netloc' part (excluding username, password -> to be provided separately)
##        # Excludes // from netloc
##        # Preceding / in 'path' (service) unecessary
##        # xor2=lambda s, k:''.join(chr(ord(c) ^ ord(i)) for (c,i) in zip(s,k*(len(s)/len(k))+k*(len(s)%len(k))))
##        _pentacle_endpoint = re.compile('^([^/:]+):([^/?]*):([0-9]+)(.*)$')
##
##        @classmethod
##        def Parse(self, endpoint):
##            m = self._pentacle_endpoint.match(endpoint)
##            assert m is not None
##            (scheme, host, port, service) = m.groups()
##            return self(scheme, host, port, service)
##
##        __slots__ = ()
##
##        def getendpoint(self):
##            return '%s:%s:%s%s' % (self.scheme, self.host, self.port, self.service)

# URL 2 Implementation.
##    if 0:
##        # Separates communication class, which provides a kind of content
##        # evaluation, but nothing compared to registered content-types
##        # that needs to be implemented.
##        #
##        # The interesting parts are a separate Query class, immediate
##        # access to subdomain parts, a way to extend the path, a way to
##        # rehost the url (extracts path and query, puts in another host),
##        # and a way to move into another url class.
##        #
##        # Can use addition operator on host.
##        from urlparse import urlparse
##        from urllib2 import urlescape
##
##        class base:
##            def __repr__(self):
##                return '<%s>' % (self.__class__.__name__)
##
##        class Scheme(str):
##            @property
##            def name(self):
##                return self
##
##            def url(self, hostname):
##                return Url(self, hostname)
##            __div__ = __add__ = __getitem__ = url
##
##        class Comm:
##            def post(self, *args, **kwd):
##                op = self.new(*args, **kwd) if (args or kwd) else self
##                return urlopen(str(op)) # todo, post-data from kwd
##
##            def get(self, *args, **kwd):
##                op = self.new(*args, **kwd) if (args or kwd) else self
##                return urlopen(str(op))
##
##            open = get
##            def load(self, format = None, **kwd):
##                return self.interpret(self.open(**kwd))
##
##            __call__ = load
##
##            def interpret(self, result):
##                return json.load(result)
##
##        class Query(dict):
##            @classmethod
##            def Build(self, **values):
##                return '?' + '&'.join('%s=%s' % (urlescape(n),
##                                                 urlescape(v))
##                                      for (n, v) in values.iteritems())
##
##            @classmethod
##            def __init__(self, string, **values):
##                self.update(self.ParseString(string))
##                self.update(values)
##
##        # urlparse: 'scheme netloc path params query fragment'
##
##        class Url(Comm):
##            @classmethod
##            def Build(self, scheme, hostname, *path, **query):
##                path = '/' + '/'.join(path) if path else ''
##                query = '?' + Query.Build(**query)
##                return '%s://%s%s%s' % (scheme, hostname, path, query)
##
##            @classmethod
##            def Parse(self, url):
##                u = urlparse(url)
##                return self(u.scheme, u.netloc, u.path, u.query)
##
##            @classmethod
##            def new(self, *args, **kwd):
##                return self(*args, **kwd)
##
##            def __init__(self, scheme, hostname, *path, **query):
##                self.u = urlparse(self.Build(scheme, hostname, *path, **query))
##
##            def extend(self, *path, **kwd):
##                # What if a query object was passed in as part of path?
##                return self.new(self.u.scheme, self.u.netloc,
##                                '%s/%s' % (self.u.path, path),
##                                '')
##
##            __add__ = __div__ = q = extend
##
##            def __setitem__(self, name, value):
##                # XXX must update internally.
##                return self.q(**{name: value})
##
##            @property
##            def parts(self):
##                return self.u.path.split('/')
##
##            def __iter__(self):
##                return iter(self.parts)
##
##            @property
##            def subdomains(self):
##                return self.u.netloc.split('.')
##
##            def __str__(self):
##                return self.Build(self.u.scheme, self.u.netloc,
##                                  *self.u.path, **self.u.query)
##
##            def rehost(self, hostname = None, port = None):
##                # return new object with new host and/or port
##                pass
##
##            def __rshift__(self, newClass):
##                return newClass(self) # xxx from parts
##
##        http = Scheme('http')
##        https = Scheme('https')
##        ftp = Scheme('ftp')
##
##        ##    class Result(list):
##        ##        class Search(Url):
##        ##            def interpret(self, response):
##        ##                # Perform screen-scraping
##        ##                return Result() # from response
##        ##
##        ##    u = http + 'www.google.com' + 'search' \
##        ##        + Query(paginated = '0') >> SearchResults
##        ##
##        ##    for result in u(q = 'kittens'):
##        ##        pass
##
##        class FBGraph(Url):
##            class Object(base, dict):
##                def __init__(self, **values):
##                    self.update(values)
##
##            def interpret(self, response):
##                return self.Object(**json.load(response))
##
##        graph = https + 'graph.facebook.com' >> FBGraph
##        me = graph('me')

def parseCookieString(string):
    return dict(flatteni(*split_header_words(string.split(';'))))
def buildCookieString(cookies):
    i = [(str(n), str(v)) for (n, v) in iteritems(cookies)]
    return '; '.join(mapi(sprintf('%s=%s'), i))
    return join_header_words([i])  # this adds "unnecessary" double quotes around alot of things (things with numerals?)


def f(v):
    for x in v:
        if isinstance(x, list):
            for i in f(x):
                yield i
        else:
            yield x

import http.client
from urllib.request import HTTPHandler, HTTPSHandler

class MultiHeaderHTTPHandler(HTTPHandler):
    class MultiHeaderHTTPConnection(http.client.HTTPConnection):
        def putheader(self, header, *values):
            return http.client.HTTPConnection.putheader(self, header, *f(values))

    def http_open(self, req):
        return self.do_open(self.MultiHeaderHTTPConnection, req)

enhancedHandlers = (MultiHeaderHTTPHandler,)

# if hasattr(httplib, 'HTTPS'):
#     class MultiHeaderHTTPSHandler(HTTPSHandler):
#         class MultiHeaderHTTPSConnection(http.client.HTTPSConnection):
#             def putheader(self, header, *values):
#                 return http.client.HTTPConnection.putheader(self, header, *f(values))

#         def https_open(self, req):
#             return self.do_open(self.MultiHeaderHTTPSConnection, req,
#                 context=self._context)

#     enhancedHandlers += (MultiHeaderHTTPSHandler,)

class V3:
    # from op.runtime import Object, callMergingArgs
    # from op.runtime.functional.parallelized import nth
    # from op.runtime.virtual.objects import mergedict

    # 2 seconds
    try: from BeautifulSoup import BeautifulSoup as bsoup
    except ImportError: bsoup = False
    from urllib.request import urlopen, ProxyHandler, build_opener as newUrlOpener0
    from urllib.request import Request as URLLibRequest
    from urllib.parse import urlencode
    from urllib.parse import urlparse

    try: from cgi import parse_qsl
    except ImportError:
        from urllib.parse import parse_qsl

    import json
    import sys

    # Host(..., urlopen = newUrlOpener(systemProxyManager()))
    @staticmethod
    def systemProxyManager():
        return V3.ProxyHandler()
    @staticmethod
    def httpProxyManager(url):
        return V3.ProxyHandler(dict(http = url))

    newUrlOpener0 = staticmethod(newUrlOpener0)
    # callMergingArgs = staticmethod(callMergingArgs)
    # mergedict = staticmethod(mergedict)

    @staticmethod
    def newUrlOpener(*args, **kwd):
        return V3.newUrlOpener0(*args, **kwd).open

    # merge_dict = mergedict
    def merge_dict(d1, d2):
        d3 = d1.copy()
        d3.update(d2)

        return d3

    def urlparse2(*args, **kwd):
        u = urlparse(*args, **kwd)
        u = namespace(scheme = u.scheme,
                      netloc = u.netloc,
                      path = u.path,
                      params = u.params,
                      query = u.query,
                      fragment = u.fragment)

        if u.path[:1] == '/':
            u.path = u.path[1:]

        return u

    defaultBrowserShellName = 'browseWebMozilla' # 'browseWebDefault'
    defaultUrlVar = 'url'

    @staticmethod
    def OpenInDefaultBrowser(url):
        return url.openInBrowserShell(getattr(my, V3.defaultBrowserShellName))

    # The way it should be:
    class Protocol: # (Object):
        @classmethod
        def Convert(self, value):
            if isinstance(value):
                return self(value)

            assert isinstance(value, self)
            return self

        def __init__(self, name, *args, **kwd):
            self.name = name

            self.args = args
            self.kwd = kwd

        def getHost(self, host, port = None, *args, **kwd):
            # Todo: merge with self.{args|kwd} to compartmentalize other
            # connect settings apart from hostname:
            #
            #    Protocol('http', urlopen = newUrlOpener(httpProxyManager(...)))
            #    _['google.com']['search'].set(q = ...).value
            #
            if isinstance(host, Host):
                port = host.port
                host = host.name

            return \
            V3.callMergingArgs(V3.Host, ((host,) + args, self.args),
                               (V3.mergedict(dict(port = port, proto = self.name),
                                             self.kwd), kwd))

        __call__ = __getitem__ = __add__ = getHost

        def getAttributeString(self):
            return self.name

    Scheme = Protocol

    class Host: # (Object):
        # _acceptable_name_chars = 'abcdefghijklmnopqrstuvwxyz'
        _unacceptable_name_chars = '/'

        @classmethod
        def CleanName(self, name):
            return ''.join(c for c in name if c not in
                           self._unacceptable_name_chars)

            return ''.join(c for c in name if c in _acceptable_name_chars)
            return name.replace('/', '')

        def __init__(self, name, port = None, proto = 'http', urlopen = urlopen):
            self.name = self.CleanName(name)
            self.proto = proto
            self.port = port
            self.urlopen = urlopen

        def getAttributeString(self):
            return '%s://%s' % (self.proto, self.name)

        def request(self, *path):
            if len(path) == 1 and isinstance(path[0], int):
                return self.report(path[0])

            return self.Request(self, *path)

        __add__ = __getitem__ = __div__ = request

        @property
        def host(self):
            if self.port is None:
                return self.name

            return '%s:%d' % (self.name, self.port)

        def reproto(self, proto):
            return Protocol.Convert(proto)[self]
        def report(self, port):
            return call(classOf(self), self.name, port = port,
                        proto = self.proto, urlopen = self.urlopen)

        @property
        def subdomains(self):
            return self.name.split('.')

        def getUrlString(self, *path, **query):
            # Todo: reverse parse_qsl here to create multiples for sequence values.
            query = V3.urlencode(query)

            # Hmm, urlunparse?
            return '%s://%s%s' % (self.proto, self.host,
                                  self.getPathStringEx(path, query, leadingSlash = True))

        def getPathStringEx(self, path, query, leadingSlash = True):
            return '%s%s%s%s' % \
                   ((path and path[0][:1] == '/') and '' or '/',
                    '/'.join(path),
                    query and '?' or '',
                    query)

        def getPathString(self, *path, **query):
            return self.getPathStringEx(path, query)

        __call__ = getUrlString

        def open(self, url, body = None, headers = None):
            return self.urlopen(V3.URLLibRequest(url, headers = headers), body)

        def evaluate(self, response):
            return response.read()

        # Todo: use as base class.
        class Request: # (Object):
            def __init__(self, host, *path, **query):
                self.host = host
                self.path = path
                self.query = self.QueryClass(self, **query)

                # todo: automatic cookie management
                # headers as mime-message object?
                self.headers = dict()

            class QueryClass:
                def __init__(self, req, **query):
                    self.req = req
                    self.query = query

                def __repr__(self):
                    return repr(self.query)

                def __call__(self, *args, **kwd):
                    self.update(*args, **kwd)
                    return self.req

                # UserDictMixin
                def update(self, *args, **kwd):
                    return self.query.update(*args, **kwd)

                def __getitem__(self, name):
                    return self.query[name]
                def __setitem__(self, name, value):
                    self.query[name] = value

                def get(self, *args, **kwd):
                    return self.query.get(*args, **kwd)

                def keys(self):
                    return list(self.query.keys())
                def iterkeys(self):
                    return iter(self.query.keys())
                def values(self):
                    return list(self.query.values())
                def itervalues(self):
                    return iter(self.query.values())
                def items(self):
                    return list(self.query.items())
                def iteritems(self):
                    return iter(self.query.items())

                def __contains__(self, name):
                    return name in self.query
                def __iter__(self):
                    return iter(self.query)

                def copy(self):
                    return self.__class__(self.req, **self.query.copy())

            def getAttributeString(self):
                return self.urlString

            def set(self, **kwd):
                self.query.update(kwd)
                return self

            def getUrlString(self):
                return self.host.getUrlString(*self.path,
                                              **self.query)

            __str__ = getUrlString
            urlString = property(getUrlString)

            def getPathString(self):
                return self.host.getPathString(*self.path, **self.query)
            pathString = property(getPathString)

            def rehost(self, host):
                return host[self.pathString]

            def subpath(self, *path, **query):
                new = self.__class__(self.host, *(self.path + path),
                                     **V3.merge_dict(self.query, query))

                for (name, value) in self.headers:
                    new.addHeader(name, value)

                return new

            __call__ = __div__ = __getitem__ = __add__ = subpath

            def addHeader(self, name, value):
                self.headers[name] = value
                # return self

            ##    @property
            ##    def query(self):
            ##        try: return self.__queryObj
            ##        except AttributeError:
            ##            q = self.QueryObject(query2dict(self.queryString))
            ##            qo = self.__queryObj = q
            ##            return qo
            ##
            ##    class QueryObject(dict):
            ##        def __init__(self, values):
            ##            dict.__init__(self, values)
            ##            self.__dict__ = self
            ##
            ##            for (n, v) in self.items():
            ##                self[n] = self.Value(v)

            ##    class Query(dict):
            ##        @classmethod
            ##        def Build(self, **values):
            ##            return '?' + '&'.join('%s=%s' % (urlescape(n),
            ##                                             urlescape(v))
            ##                                  for (n, v) in values.iteritems())
            ##
            ##        @classmethod
            ##        def __init__(self, string, **values):
            ##            self.update(self.ParseString(string))
            ##            self.update(values)

            def request(self, *path, **query):
                if path or query:
                    # Extend more specific.
                    return self.subpath(*path, **query).request()

                r = self.host.open(self.urlString,
                                   headers = self.headers)

                return self.Response(self, r)

            get = request

            def post(self, body = None):
                r = self.host.open(self.urlString,
                                   body = body,
                                   headers = self.headers)

                return self.Response(self, r)

            def evaluate(self, response):
                return self.host.evaluate(response)

            def openInBrowserShell(self, browserShell, urlVar = None):
                if urlVar is None:
                    urlVar = V3.defaultUrlVar

                # return browserShell.spawn(**{urlVar: self.urlString})
                return browserShell.spawn('-new-tab', '"%s"' % self.urlString)

            @property
            def browse(self):
                return V3.OpenInDefaultBrowser(self)

            @property
            def soup(self):
                return V3.bsoup(self.get().read())

            @property
            def value(self):
                return self.get().value

            class Response: # (Object):
                def __init__(self, request, r):
                    self.request = request
                    self.r = r
                    self.read = r.read

                def getAttributeString(self):
                    return 'to ' + self.request.getAttributeString() # + ': ' + repr(self.r)

                @property
                def status(self):
                    return self.r.code

                code = status

                @property
                def value(self):
                    return self.request.evaluate(self)


    def buildHost(u, evaluate):
        if evaluate:
            class ObjectifiedHost(Host):
                evaluate = evaluate # staticmethod(evaluate)?

            return ObjectifiedHost(u.netloc, proto = u.scheme)

        return V3.Host(u.netloc, proto = u.scheme)

    # Todo: use as a structure that composes a request..?
    # Or, as a structure over an opaque uri that can decipher it.
    # Or, subclass Host.Request
    def Url(string, evaluate = None, headers = None):
        # Parse existing url into structure.
        # XXX incomplete because it's ignoring #fragments and ;params
        u = V3.urlparse2(string)
        path = u.path # todo: urllib.quote_plus this, now..  so that we're storing a correct syntax.
                      # RFC 2396

        if u.fragment:
            path = '%s#%s' % (u.path, u.fragment)

        q = dict(parse_qsl(u.query))
        host = V3.buildHost(u, evaluate)
        u = host[path].set(**q)

        if headers:
            u.headers.update(headers)

        return u

    http = Scheme('http')
    https = Scheme('https')

    # https[http['www.google.com'][9080]] / u.pathString

    def EvaluateContent(response):
        # todo: evaluate and raise error response types...

        content_type = response.headers.get('content-type')

        # from op.data import loadFromContentType
        # return loadFromContentType(content_type, response.read())

        if content_type == 'application/json':
            value = response.read()
            value = json.loads(value)

            # return value
            return Namespace.FromStructure(value)

        return response.read()

    class ContentHost(Host):
        def evaluate(self, *args, **kwd):
            return V3.EvaluateContent(*args, **kwd)

        @classmethod
        def Url(self, string):
            # Parse existing url into structure.
            u = V3.urlparse2(string)
            path = u.path
            if u.fragment:
                path = '%s#%s' % (self.path, u.fragment)

            host = self(u, evaluate)
            return host[path].set(**q)

    ContentUrl = ContentHost.Url

    # For V3 Compartmentalization.
    urlopen = staticmethod(urlopen)
    urlencode = staticmethod(urlencode)
    urlparse = staticmethod(urlparse)
    urlparse2 = staticmethod(urlparse2)

    parse_qsl = staticmethod(parse_qsl)

    merge_dict = staticmethod(merge_dict)
    buildHost = staticmethod(buildHost)
    Url = staticmethod(Url)

    Parse = Url

def buildURL(proto, host, path):
    if isinstance(host, (tuple, list)):
        host = '%s:%d' % host
    if isinstance(path, (tuple, list)):
        path = '/'.join(path)

    return URL('%s://%s/%s' % (proto, host, path))

# from op.runtime import memorized
class memorized:
    property = property

class RESTAPI:
    # Basically a URL layer.
    @memorized.property
    def url(self, _):
        try: return self.URL
        except AttributeError:
            return buildURL(self.protocol, self.host, self.path)

    request = get = memorized.property(lambda self:self.url.get)
    post = memorized.property(lambda self:self.url.get)
    path = memorized.property(lambda self:self.PATH)

    @property
    def protocol(self):
        return getattr(self, 'PROTOCOL', 'https' if self.secure else 'http')

    @property
    def secure(self):
        return getattr(self, 'SECURE', False)

    @property
    def host(self):
        try: return self.HOSTNAME
        except AttributeError:
            try: return (self.HOSTNAME, self.PORT)
            except AttributeError:
                return self.HOSTNAME

    def __init__(self, *path, **kwd):
        try: self.URL = kwd['url'] # does this include protocol??
        except KeyError: pass

        try: self.PROTOCOL = kwd['protocol']
        except KeyError:
            try: self.SECURE = kwd['secure']
            except KeyError: pass

        try: self.HOST = kwd['host']
        except KeyError:
            try:
                self.HOSTNAME = kwd['hostname']

                try: self.PORT = kwd['port']
                except KeyError: pass

                self.PATH = path

            except KeyError:
                try: self.PORT = kwd['port']
                except KeyError:
                    self.HOST = path[0]
                else:
                    self.HOSTNAME = path[0]

                self.PATH = path[1:]
        else:
            self.PATH = path

# from op.runtime.functional import Operational
# class HttpObjectFormat(Operational):
#     def __call__(self, *args, **kwd):
#         from op.data import loadStringByFormat
#         value = self.function(*args, **kwd)
#         return loadStringByFormat(value.headers['Content-Type'], value.read())

# httpObject = HttpObjectFormat

##    @apply
##    class fbApi(registry.Container): # (Namespace):
##        ##    fbGraphApi = RESTAPI('graph', 'to', 'me', hostname = 'api.facebook.com', port = 6000)
##        ##    fbGraphApi = RESTAPI(url = 'http://api.facebook.com/graph')
##
##        fbGraphApi = RESTAPI('api.facebook.com', 'graph', secure = True)
##
##        def __init__(self):
##            self.__getitem__ = self.__call__ = chaining(self.activate, httpObject(self.fbGraphApi.get))
##            self.object = attributable(self)
##
##        def activate(self, object):
##            self.register(object.name, object)
##            return object

# fbApi.object.me

try: from op.subsystem.gae import aefetch, install_aefetch
except ImportError as e:
    # from op.runtime import NotImplementedFunction
    # aefetch = install_aefetch = NotImplementedFunction(e)
    pass

# from op.runtime.layer.strings import StringBufferType

def InspectUrl(u):
    ##    if isinstance(u, V3.Host.Request):
    ##        u = u.urlString
    if isinstance(u, str):
        u = Url(u)

    buf = StringBufferType()

    # V3
    print(u.host.name, file=buf)
    print('   ', u.host.proto, 'port', u.host.port, file=buf)
    print(u.path[0], file=buf)

    ##    print >> buf, inspect(dict(protocol = u.host.proto,
    ##                               host = u.host.name,
    ##                               port = u.host.port,
    ##                               path = u.path[0]))
    print(file=buf)

    if u.query:
        print(indent(inspect(u.query)), file=buf)
        print(file=buf)

    ##    def dprint(items, indent = ''):
    ##        items = list(items)
    ##        if items:
    ##            fmt = '%s%%-%ds: %%s' % (indent, max(map(len, items)))
    ##
    ##            for (name, value) in items:
    ##                print >> buf, fmt % (name, value)
    ##
    ##    # V1
    ##    dprint((name, value) for (name, value) \
    ##           in [('protocol'  , u.scheme  ),
    ##               ('host'      , u.netloc  ),
    ##               ('path'      , u.path    ),
    ##               ('fragment'  , u.query),
    ##               ('params'    , u.params  )] \
    ##
    ##           if value)
    ##
    ##    dprint(u.query.iteritems(), indent = '  ')

    if u.headers:
        h = dict(u.headers)

        cookies = h.pop('Cookie', None)
        cookies = parseCookieString(cookies)

        print('headers:', file=buf)
        print(indent(inspect(h)), file=buf)
        print(file=buf)

        if cookies:
            print('cookies:', file=buf)
            print(indent(inspect(cookies)), file=buf)
            print(file=buf)

    return buf.getvalue()

# inspect.url = InspectUrl

Host = V3.Host
Request = Host.Request
from urllib.request import HTTPDigestAuthHandler, HTTPBasicAuthHandler
from urllib.request import HTTPPasswordMgr, HTTPCookieProcessor
from urllib.request import build_opener as buildUrlOpener

from http.cookiejar import MozillaCookieJar
import warnings

# from op.runtime import Object

def loadCookieString(jar, string, *args, **kwd):
    jar._really_load(io.buffer(string), '<internal string>', *args, **kwd)
    return jar

def encode(string):
    return string.encode('zlib').encode('base64')
def decode(string):
    return string.decode('base64').decode('zlib')

class EncodedString(str):
    __automap__ = 'encoded'

    decode = decode
    decoded = property(decode)

    @classmethod
    def FromStructure(self, name, value, **kwd):
        return self(str(value))


class WebAuthSession: # (Object):
    __automap__ = 'session'

    DefaultCookieJar = MozillaCookieJar

    class AuthConfig: # (Object):
        @classmethod
        def CreatePasswordManager(self, sequence):
            h = HTTPPasswordMgr()
            self(sequence, h.add_password)
            return h

        def __init__(self, sequence, addPassword):
            for (uri, realms) in sequence:
                if isinstance(realms, str):
                    warnings.warn('cannot handle htdigest filenames yet: ' + realms)
                    continue

                for (name, users) in iteritems(realms):
                    if isinstance(users, EncodedString):
                        users = users.decoded
                        users = pickle.Unpickle(users)

                        ##    users = loadable(users).loading.csv
                        ##    users = dict((u[0], u[1]) for u in users)

                    for (username, passwd) in iteritems(users):
                        addPassword(realm = name,
                                    uri = uri,
                                    user = username,
                                    passwd = passwd)

    @classmethod
    def FromStructure(self, name, value, **kwd):
        auth = iteritems(value['auth'])
        auth = self.AuthConfig.CreatePasswordManager(auth)

        try: cookies = value['cookies']
        except KeyError:
            try: cookies = value['cookies-encoded']
            except KeyError:
                try: cookies = value['cookiesEncoded']
                except KeyError: cookies = None

            if cookies:
                cookies = decode(cookies)

        jar = self.DefaultCookieJar()
        if cookies:
            # todo: get other cookiejar parameters from structure
            loadCookieString(jar, cookies)

        return self(auth, jar)

    @classmethod
    def New(self, **conf):
        return self.FromStructure(None, conf)

    def __init__(self, auth, cookieJar):
        self.auth = auth
        self.cookieJar = cookieJar

    class Opener: # (Object):
        def __init__(self, session, opener):
            self.session = session
            self.opener = opener

        def __call__(self, *args, **kwd):
            return self.opener.open(*args, **kwd)

    @property
    def urlOpenerObject(self):
        return self.Opener(self, self.urlOpener)

    @property
    def urlOpener(self):
        authHandlers = (HTTPDigestAuthHandler(self.auth),
                        HTTPBasicAuthHandler(self.auth))

        cookieHandler = HTTPCookieProcessor(self.cookieJar)

        return buildUrlOpener(*(enhancedHandlers + authHandlers + (cookieHandler,)))

    def __getitem__(self, host):
        return Host(host, urlopen = self.urlOpenerObject)

    @property
    def protocol(self):
        @attributable
        def getProtocol(name):
            return Protocol(name, urlopen = self.urlOpenerObject)

        return getProtocol

    def saveCookies(self, *args, **kwd):
        with my.tmp.tempfile() as t:
            self.cookieJar.save(t, *args, **kwd)
            return t.read()

    def encodeCookies(self, *args, **kwd):
        return encode(self.saveCookies(*args, **kwd))


    # Serialization:
    def __getstate__(self):
        return dict(auth = self.auth, cookies = self.encodeCookies())

    def __setstate__(self, state):
        self.auth = state['auth']
        self.cookieJar = loadCookieString(self.DefaultCookieJar(),
                                          decode(state['cookies']))

webAuthSession = WebAuthSession.New
