# Generic In-MUD XMLRPC Server.
# --
# Designed to be hooked into by various components.
# 
#
# todo: Access-Control-Max-Age
from xmlrpc.server import SimpleXMLRPCServer as XMLRPC
from xmlrpc.server import SimpleXMLRPCRequestHandler as XMLRPCRequestHandler
# from thread import start_new_thread as nth
from urllib.parse import urlparse
from errno import EINTR
from select import error as select_error
from threading import Thread

import xmlrpc.client
import sys
import json

from stuphos import enqueueHeartbeatTask, logException
from stuphos.etc import nth, reraiseSystemException, getSystemExceptionString, isYesValue
from stuphos.etc.tools.timing import getCurrentTime as now

ALLOWED_PORT_ORIGINS = [#8000,
                        2180, None, 443]

# CSRF Access Control.
def getOriginAccess(request, origin):
    # Todo: Obviously, this is seriously unfinished:
    # This should come from an access table defined via mud-control.
    if origin and urlparse(origin).port in ALLOWED_PORT_ORIGINS:
        # note: this is no longer good enough for firefox/chrome
        # It must match the value passed for the Origin: header by client.
        #return origin # extracted during do_POST
        return origin
        return '*'

def redirectStderr(function, *args, **kwd):
    import sys
    try: __stderr__ = sys.__stderr__
    except AttributeError:
        return function(*args, **kwd)
    else:
        stderr = sys.stderr
        sys.stderr = __stderr__
        try: return function(*args, **kwd)
        finally:
            sys.stderr = stderr

class Deferrable:
    # For GETs (handled but undispatched).
    deferred = False

    billableIdentity = None

    def handleAccessControl(self):
        # https://developer.mozilla.org/En/HTTP_Access_Control
        allowOrigin = getOriginAccess(self, getattr(self, 'origin', None))
        if allowOrigin:
            #print 'Sending header', allowOrigin
            self.send_header('Access-Control-Allow-Origin', allowOrigin)

    # Deferred Methods Branch:
    def finish_this_request(self, response, other_headers = None, status = 200):
        redirectStderr(self.send_response, status)

        if response is not None:
            responseEncoded = response.encode('utf-8')

            self.send_header("Content-type", "text/xml")
            self.send_header("Content-length", str(len(responseEncoded)))

        self.handleAccessControl()
        self.send_header('Access-Control-Allow-Credentials', 'true')

        if other_headers:
            for (name, value) in other_headers.items():
                #print 'Sending other header', name, value
                self.send_header(name, value)

        self.end_headers()

        if response is not None:
            # print(response)
            # if response:
            #     print(response)
            #     debugOn()

            # bug in debugger?  just putting debugOn here means
            # that any subsequent post-preflight (options) request
            # will be somehow corrupted by the debugger and cause
            # it to return effectively xmlrpclib.dumps('[]')
            # instead of the proper (offending sample) response.

            self.wfile.write(responseEncoded)

        # shut down the connection
        #   File "/usr/lib/python2.7/socket.py", line 307, in flush
        #     self._sock.sendall(view[write_offset:write_offset+buffer_size])
        # AttributeError: 'NoneType' object has no attribute 'sendall'
        try: self.wfile.flush()
        except AttributeError as e:
            if str(e) != "'NoneType' object has no attribute 'sendall'":
                raise e

        self.connection.shutdown(1)

        identity = getattr(self, 'billableIdentity', None)
        if identity is not None:
            self.chargeUserContent(identity, response)


    def chargeUserContent(self, identity, response):
        pass


    def finish(self):
        if not self.deferred:
            if not self.wfile.closed:
                self.wfile.flush()
            self.wfile.close()
            self.rfile.close()

            # Carried over from server.close_request.
            self.request.close()

    # Deferment Request Methods:
    def defer(self):
        # Go into deferred mode, so that this request handler finishes
        # its construction phase, but the connection isn't closed yet.
        self.deferred = True
        raise HostRpc.DeferredMethodSignal(self)


class HostRpc(XMLRPC):
    # Passed to server on construction.
    LOG_REQUESTS = True

    class DeferredMethodSignal(Exception):
        # Signals a method that will be finished by another thread!
        def __init__(self, request):
            self.request = request

    class RequestHandler(Deferrable, XMLRPCRequestHandler):
        def setup(self):
            # XXX :network:
            self.request.settimeout(30)
            XMLRPCRequestHandler.setup(self)

        # def log_message(self, format, request_line, status = '-', *args, **kwd):
            # Todo: log to sys/mudlog.
            # return XMLRPCRequestHandler.log_message(self, *args, **kwd)
            # debugOn()

        def log_request(self, code='-', size='-'):
            """Log an accepted request.

            This is called by send_response().

            """
            from http import HTTPStatus

            if isinstance(code, HTTPStatus):
                code = code.value
            # self.log_message('"%s" %s %s',
            #                  self.requestline, str(code), str(size))

            request_line = self.requestline
            status = code
            args = ()

            # Reformat logging of RPC.

            # if httpMethod is not 'OPTIONS':
            rpcMethod = getattr(self, 'method', '-')

            # self.logRpcMessage(rpcMethod, getattr(self, 'params', []))

            if self.ignoreRpcMethod(rpcMethod):
                return

            httpMethod = request_line.split(' ', 1)[0]
            args = f'RPC {httpMethod} {rpcMethod} {", ".join(map(str, args))}'

            # debugOn()
            # Todo: logOperation
            from sys import stderr
            stderr.write(f'{self.address_string()} - - [{self.log_date_time_string()}] {repr(args)} {status} -\n')

        @runtime.available(runtime.System.Journal)
        def logRpcMessage(log, self, method, params):
            if method == 'session.command' and params and \
                params[0] in ['do-interpret-script',
                              'do-interpret-agent']:

                content = json.dumps(dict(code = params[1])) # Todo: params..?

                log += dict(source = f'rpc:{self.address_string()}',
                            type = 'webrequest-rpc/command/json',
                            timestamp = now(),
                            content = content)

        def ignoreRpcMethod(self, name):
            return name in ['session.messages', 'session.command']

        ##    def setup(self):
        ##        # StreamRequestHandler.setup(self)
        ##        XMLRPCRequestHandler.setup(self)
        ##
        ##        class socketWrapper(object):
        ##            def __init__(self, realsocket):
        ##                self.__dict__['__realsocket'] = realsocket
        ##            def __setattr__(self, name, value):
        ##                return setattr(self.__dict__['__realsocket'], name, value)
        ##            def __getattr__(self, name):
        ##                try: return getattr(self.__dict__['__realsocket'], name)
        ##                finally:
        ##                    if name in ['close', 'shutdown']:
        ##                        print 'tracing...'
        ##
        ##                        from pdb import set_trace
        ##                        set_trace()
        ##
        ##        self.request = socketWrapper(self.request)
        ##        self.connection = socketWrapper(self.connection)

        # What about adding 'internal' to this??
        rpc_paths = XMLRPCRequestHandler.rpc_paths + ('/rpc', '') # '/stuph/rpc'

        ##    def setup(self):
        ##        self.rpc_paths = self.rpc_paths + (str(self.request.path),)
        ##        XMLRPCRequestHandler.setup(self)

        import re
        METHOD_MATCH = r'[a-zA-Z_\.\ ]+' # r'*?' # Non-greedy.
        UNSUPPORTED_METHOD_MSG = re.compile(r'method "' + METHOD_MATCH + r'" is not supported')

        # XXX This method is no longer needed since the override is rewritten in the server class:
        # (However, log message relies on its functionality)

        def _dispatch(self, method, params):
            # Intercept method dispatch to see if it was recognized.
            # Also, prepend this handler instance to the arglist.

            # For log_message when this request finishes.
            self.method = method
            self.params = params

            try: result = self.server._dispatch(self, method, params)
            except HostRpc.DeferredMethodSignal:
                # Todo: filter out logging for certain methods.
                # self.log_message('RPC: %r' % str(method))
                raise

            except Exception as e:
                if self.UNSUPPORTED_METHOD_MSG.match(str(e)):
                    # Log unsupported method call.
                    self.log_message('UNKNOWN: %r {%s}', str(method), ', '.join(map(repr, params)))
                else:
                    # self.log_message('ERROR:\n%s', getSystemExceptionString())
                    logException(traceback = True)

                reraiseSystemException()

            # Log supported method call.
            # Todo: filter out logging for certain methods.
            # self.log_message('RPC: %r', str(method))
            return result

        def do_OPTIONS(self):
            # Handle CORS Preflight check.
            #print inspect(self.headers)

            ##    dict                           (dict)               {'origin': 'http://localhost:8000', 'accept-language': 'en-U
            ##    encodingheader                 (NoneType)           None
            ##    fp                             (socket._fileobject) <socket._fileobject object at 0x04EF38B0>
            ##    headers                        (list)               ['Host: localhost:2172\r\n', 'User-Agent: Mozilla/5.0 (Windo
            ##    maintype                       (str)                'text'
            ##    plist                          (list)               []
            ##    plisttext                      (str)                ''
            ##    seekable                       (int)                0
            ##    startofbody                    (NoneType)           None
            ##    startofheaders                 (NoneType)           None
            ##    status                         (str)                ''
            ##    subtype                        (str)                'plain'
            ##    type                           (str)                'text/plain'
            ##    typeheader                     (NoneType)           None
            ##    unixfrom                       (str)                ''

            # print nls(self.headers.headers)
            # print self.headers # MIME Message object.

            ##    Host: localhost:2172
            ##    User-Agent: Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0
            ##    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
            ##    Accept-Language: en-US,en;q=0.5
            ##    Accept-Encoding: gzip, deflate
            ##    Origin: http://localhost:8000
            ##    Access-Control-Request-Method: POST
            ##    Access-Control-Request-Headers: content-type
            ##    Connection: keep-alive
            ##    Pragma: no-cache
            ##    Cache-Control: no-cache

            self.origin = self.headers.get('Origin')
            self.finish_this_request('', {'Access-Control-Allow-Methods': 'GET, POST, OPTIONS', # Should this include OPTIONS?
                                          # Q: Are OPTIONS requests sending headers??
                                          'Access-Control-Allow-Headers': 'Content-Type'})

            # print 'finished OPTIONS'


        # Overwrite original stdlib method for deferred methods:
        def do_POST(self):
            """Handles the HTTP POST request.

            Attempts to interpret all HTTP POST requests as XML-RPC calls,
            which are forwarded to the server's _dispatch method for handling.

            Some methods may be deferred for another thread to finish.
            """

            # Check that the path is legal
            if not self.is_rpc_path_valid():
                self.report_404()
                return

            self.deferred = False

            try:
                # :set-user: :authentication: note: this only returns a dictionary...
                self.user = self.authenticate(self.headers.get('Authorization'))


                # from python3.9:
                # Get arguments by reading body of request.
                # We read this in chunks to avoid straining
                # socket.read(); around the 10 or 15Mb mark, some platforms
                # begin to have problems (bug #792570).
                max_chunk_size = 10*1024*1024
                size_remaining = int(self.headers["content-length"])
                L = []

                # self.socket.setblocking(0)
                # self.socket.settimeout(10)

                while size_remaining:
                    chunk_size = min(size_remaining, max_chunk_size)
                    # if chunk_size == 2: # XXX :skip: HACK
                    #     print('setting blocking to 0')
                    #     self.socket.setblocking(0)

                    chunk = self.rfile.read(chunk_size)
                    if not chunk:
                        break
                    L.append(chunk)
                    size_remaining -= len(L[-1])

                    # print(f'[xmlrpc] {size_remaining}')

                # self.socket.setblocking(1)
                # self.socket.settimeout(None)

                # if size_remaining:
                #     print(f'[xmlrpc] incomplete read')

                data = b''.join(L)

                data = self.decode_request_content(data)
                if data is None:
                    # print('[xmlrpc] response has been sent')
                    return #response has been sent


                # debugOn()

                # max_chunk_size = 10*1024*1024
                # size_remaining = int(self.headers["content-length"])
                # L = []
                # while size_remaining:
                #     chunk_size = min(size_remaining, max_chunk_size)

                #     # XXX :skip: if unicode characters are included, the size_remaining will be wrong..?
                #     # Meaning we'll read more than is available and block (forever).
                #     L.append(self.rfile.read(chunk_size).decode('utf-8'))
                #     size_remaining -= len(L[-1])
                # data = ''.join(L)


                # This qualifies as a "preflight" because of POST method and content-type.
                self.origin = self.headers.get('Origin')

                contentType = self.headers.get('Content-Type', 'application/xml')
                response = self.server.handleContentType(contentType, self, data)

                if response is None:
                    # debugOn()

                    # In previous versions of SimpleXMLRPCServer, _dispatch
                    # could be overridden in this class, instead of in
                    # SimpleXMLRPCDispatcher. To maintain backwards compatibility,
                    # check to see if a subclass implements _dispatch and dispatch
                    # using that method if present.
                    response = self.server._marshaled_dispatch(
                            data, getattr(self, '_dispatch', None)
                        )

                # print(f'[xmlrpc] response: {response}')

            except HostRpc.DeferredMethodSignal:
                # Done (for now).
                ##    print 'tracing...'
                ##
                ##    from pdb import set_trace
                ##    set_trace()

                return

            except:
                # This should only happen if the module is buggy
                # internal error, report as HTTP server error
                self.error_this_request(fault = False)
            else:
                self.finish_this_request(response)

                # todo: debug
                #print 'finished POST'

        def authenticate(self, header):
            from django.contrib.auth import authenticate
            if header and header.startswith('Basic '):
                auth = header[6:]

                import base64
                auth = base64.decodestring(auth)
                (username, password) = auth.split(':')

                return authenticate(username = username,
                                    password = password)

        # Q: Write do_GET for preflight checks?!

        def error_this_request(self, fault = True):
            # Q: Log error?
            e = getSystemExceptionString()
            # debugOn()
            self.log_message('SERVER-ERROR:\n%s', e)

            if fault:
                response = self.server._dump_method_response(xmlrpc.client.Fault(1, e))
            else:
                response = None

            self.finish_this_request(response, status = 500)
            self.end_headers()

        def complete(self, response):
            self.deferred = False

            # debugOn()
            try: response = self.server._dump_method_response(response)
            except: self.error_this_request()
            else: self.finish_this_request(response)

            try: self.finish()
            except AttributeError as e:
                if str(e) != "'NoneType' object has no attribute 'close'":
                    raise e


    def __init__(self, config, methods = None):
        XMLRPC.__init__(self, (config.hostname, config.port),
                        requestHandler = self.RequestHandler,
                        logRequests = self.LOG_REQUESTS)

        if config.certificate is not None:
            import ssl
            self.socket = ssl.wrap_socket (self.socket, certfile = config.certificate,
                                           keyfile = config.keyfile,
                                           server_side = True)

        if methods is not None:
            self.funcs = methods

        self.register_introspection_functions()
        self.register_multicall_functions()

    def _marshaled_dispatch(self, data, dispatch_method = None):
        # This override passes as much of the exception data as part
        # of the fault structure value.  It could also implement JSON!
        #
        # debugOn()

        try:
            # Todo: parse 'parsererror' element in data.
            params, method = xmlrpc.client.loads(data)

            # generate response
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(None, method, params)
            # wrap response in a singleton tuple
            response = (response,)
            response = xmlrpc.client.dumps(response, methodresponse=1,
                                       allow_none=self.allow_none, encoding=self.encoding)

        except xmlrpc.client.Fault as fault:
            response = xmlrpc.client.dumps(fault, allow_none=self.allow_none,
                                       encoding=self.encoding)

        except xmlrpc.client.ResponseError as e:
            print(f'[xmlrpc$dispatch] {e}')
            print(data)

            raise

        except self.DeferredMethodSignal:
            raise

        except Exception as e:
            # report exception back to server -- X-exception, X-traceback ??
            info = getSystemExceptionString()

            if isinstance(e, ValueError) and isYesValue(configuration.XMLRPC.show_parse_source):
                info = f'{data.decode()}\n{info}'

            response = xmlrpc.client.dumps(
                xmlrpc.client.Fault(1, info),
                encoding=self.encoding,
                allow_none=self.allow_none,
                )

        # debugOn()
        return response

    contentTypeHandlers = {'application/json': None}

    def handleContentType(self, contentType, request, data):
        try: handler = self.contentTypeHandlers[contentType]
        except KeyError: pass
        else: return handler(request, data)

    def handleMethod(self, request, method, *params):
        return self._dispatch(request, method, params)

    def _handleMethodDjango(self, request, method, *params):
        return self._dispatch(request, method, params)

    def handleMethodDjango(self, request, method, *params):
        'Handle a request coming from Django WSGI application.  May defer.'

        return self._handleMethodDjango(self.DjangoRequestWrapper(request), method, params)

    class DjangoRequestWrapper(Deferrable):
        # Powerful bridge between XMLRPC request handler and django request object.
        def __init__(self, django):
            self.django = django

        def address_string(self):
            return ''

        # .wfile.closed, .wfile.flush(), .wfile.close(), .rfile.close()
        # .request.close(), .connection.shutdown(1), .wfile.write(response)
        # .end_headers(), .send_header(name, value), .origin, .send_response()

        def complete(self, msgs):
            self.finish_this_request(msgs)
            self.finish()

        @property
        def META(self):
            # REMOTE_ADDR
            return self.django.META

        @property
        def user(self):
            return self.django.user

        @property
        def server(self):
            return self.django.server


    def close_request(self, request):
        # Request handler class differentiates between closable socket modes.
        pass

    def shutdown_request(self, request):
        # XXX request is the socket._socketobject
        ##    if not request.deferred:
        ##        XMLRPC.shutdown_request(self, request)
        pass

    # Overridden to expose the request object.
    def _dispatch(self, request, method, params):
        """Dispatches the XML-RPC method.

        XML-RPC calls are forwarded to a registered function that
        matches the called XML-RPC method name. If no such function
        exists then the call is forwarded to the registered instance,
        if available.

        If the registered instance has a _dispatch method then that
        method will be called with the name of the XML-RPC method and
        its parameters as a tuple
        e.g. instance._dispatch('add',(2,3))

        If the registered instance does not have a _dispatch method
        then the instance will be searched to find a matching method
        and, if found, will be called.

        Methods beginning with an '_' are considered private and will
        not be called.

        All methods are passed the server instance and the request
        handler object instance as the first parameters.
        """

        # print(f'[xmlrpc.host.dispatch] {method} {", ".join(map(repr, params))}')
        # if method == 'session.command' and params[1] == 'do-interpret-script':
        #     debugOn()

        func = None
        try:
            # check to see if a matching function has been registered
            func = self.funcs[method]
        except KeyError:
            if self.instance is not None:
                # check for a _dispatch method
                if hasattr(self.instance, '_dispatch'):
                    return self.instance._dispatch(method, params)
                else:
                    # call instance method directly
                    try:
                        func = resolve_dotted_attribute(
                            self.instance,
                            method,
                            self.allow_dotted_names
                            )
                    except AttributeError:
                        pass

        if func is not None:
            # Passes this server instance and the request handler object instance.
            # print(f'[xmlrpc] func: {func}')
            return func(self, request, *params)
        else:
            raise Exception('method "%s" is not supported' % method)

    def _dump_method_response(self, response):
        response = (response,)
        response = xmlrpc.client.dumps(response, methodresponse=1,
                                   allow_none=self.allow_none,
                                   encoding=self.encoding)
        return response

    # Compatibility Overrides.
    def system_listMethods(self, host, request):
        return XMLRPC.system_listMethods(self, )
    def system_methodSignature(self, host, request, method_name):
        return XMLRPC.system_methodHelp(self, method_name)
    def system_methodHelp(self, host, request, method_name):
        return XMLRPC.system_methodHelp(self, method_name)


    # why?
    # http.server:419
    # def handle_one_request(self):
    #     except socket.timeout as e:
    #         #a read or a write timed out.  Discard this connection
    #         self.log_error("Request timed out: %r", e)


    def handle_request(self):
        while True:
            # import pdb; pdb.set_trace()
            try: return XMLRPC.handle_request(self)
            except select_error as e:
                if e.args[0] is EINTR:
                    # A process signal was sent, ignore and continue.
                    continue

                (etype, value, tb) = sys.exc_info()
                raise etype(value).with_traceback(tb)

    def _handle_request_noblock(self):
        'Override method to explicitly handle socket errors.'
        import socket
        try:
            request, client_address = self.get_request()
        except socket.error as e:
            if not str(e).startswith('[SSL: SSLV3_ALERT_CERTIFICATE_UNKNOWN]'):
                print(f'[_handle_request_noblock]: {e}')

            return

        if self.verify_request(request, client_address):
            try:
                self.process_request(request, client_address)
            except:
                self.handle_error(request, client_address)
                self.shutdown_request(request)
        else:
            self.shutdown_request(request)

    def handle_error(self, request, client_address):
        from stuphos.system.api import syslog
        from stuphos import logException
        syslog('Exception happened during processing of request from %s' % (client_address,))
        logException(traceback = True)

    # Todo: expound on the result-bearing functionality.
    def register_heartbeat_function(self, function, result, *args, **kwd):
        XMLRPC.register_function(self, self._get_heartbeat_dispatcher(function, result),
                                 *args, **kwd)

    def _get_heartbeat_dispatcher(self, function, result):
        def heartbeat_dispatcher(*args, **kwd):
            enqueueHeartbeatTask(function, *args, **kwd)
            # XXX :skip: This is wrong, isn't it?  It should be called from the heartbeat?
            # Or, maybe what I want is for this function to block, waiting for the
            # heartbeat.  In which case, we'll need to program some synchronicity
            # primitives here (like Queue).
            if callable(result):
                return result()

        return heartbeat_dispatcher

    def unregister_function(self, name):
        try: del self.funcs[name]
        except KeyError:
            pass

    # Server-Control.
    def is_running(self):
        try: return self.__running
        except AttributeError:
            return False

    def start(self):
        if not self.is_running():
            self.__running = True
            Thread(target = self.serve_cooperatively, daemon = True).start()
            # nth(self.serve_cooperatively)

    def stop(self):
        try: del self.__running
        except AttributeError:
            pass

        self.server_close()

    def serve_cooperatively(self):
        try:
            while self.is_running():
                self.handle_request()

        finally:
            # This might not be proper form, but it's a shortcut to cleanup.
            self.stop()


    # def server_bind(self):
    #     self.socket.setblocking(0) # XXX :skip: What I want is nonblocking peers.
    #     return XMLRPC.server_bind(self)


    ##    def __registry_delete__(self):
    ##        self.stop()


def installMarshaller():
    from stuphos.kernel import StringValue, baseStringClass

    class AgentMarshaller(xmlrpc.client.Marshaller):
        dispatch = xmlrpc.client.Marshaller.dispatch.copy()
        dispatch[StringValue] = dispatch[str]
        dispatch[baseStringClass] = dispatch[str]

        @property
        def allow_none(self):
            return True

        @allow_none.setter
        def allow_none(self, value):
            'Compat with initializer.'


    # This is the interface used by dumps.
    xmlrpc.client.FastMarshaller = AgentMarshaller
