# Copyright 2023 Thetaplane.  All rights reserved.
# mud.management.structure

# XXX :skip: upgrade this to use lang.document.structural
# from op.runtime.structural.document import Submapping, Core
from stuphos.language.document.structural import Submapping, Core

from stuphos.runtime import Object
from stuphos.runtime.architecture.api import writeprotected, extension, NoAccessException
from stuphos.etc.tools.strings import renderTemplate # This can also come from rt.arch.api
from stuphos.etc.tools.logs import tracebackString, exceptionHeader
from stuphos.etc.tools import isYesValue
from stuphos.kernel import Subroutine, grammar, Girl, Script, executeGirl, newModuleTask
from stuphos.kernel import vmNewMapping, AutoMemoryMapping, AutoMemorySequence, Processor
from stuphos.kernel import vmNewSequence, vmCurrentTask, BypassReturn, MemorySequence
from stuphos.kernel import MemoryMapping, Instance, protectedMemoryLoad
from stuphos.kernel import constrainStructureMemory, TaskCreation, findUserByName
from stuphos.kernel import resolve_procedure

from stuphos import getConfig

from queue import Queue
from urllib.parse import splitquery, parse_qs
import json, re

from sys import getrefcount


class MarshalizedObject(writeprotected, extension):
    def __init__(self, object):
        extension.__init__(self, json.dumps(object))
    def __call__(self):
        return protectedMemoryLoad(vmCurrentTask(), json.loads(self._object))


def convertTaskValue(task, value):
    if isinstance(value, MemorySequence):
        return task.sequence(convertTaskValue(task, i) for i in value)
    if isinstance(value, MemoryMapping):
        return task.mapping(*(convertTaskValue(task, i) for i in value.items()))
    if isinstance(value, Instance):
        return MarshalizedObject(value)

    return value

def vmConvertTaskValue(value):
    return convertTaskValue(vmCurrentTask(), value)

def outcomeOf(task, onComplete):
    c = vmCurrentTask()

    # todo: if self._task is currently not running,
    # then return self._task.stack[-1] immediately.

    c -= c.frame # this pure frame.

    if task.state == task.STATE_DONE:
        # If the task already completed (if it was fast),
        # we can't rely on the completion handler.  No
        # worries: just return value now.
        try: value = task.stack[-1]
        except IndexError:
            value = None

        return convertTaskValue(c, value)


    s = c.machine.suspendedTasks
    s.suspendTask(c)

    @onComplete
    def complete(_, exception = None, **kwd):
        # print(f'[TriggerTask.result.complete] e: {exception}')

        # debugOn()
        if exception:
            (etype, value, tb) = exception
            s.resumeTask(c, c.machine, exception = value)

        else:
            # try: value = task.stack.pop()[0]
            try: value = task.stack[-1]
            except IndexError:
                # print(f'[outcome$complete] no stack')
                value = None

            value = convertTaskValue(c, value)
            s.resumeTask(c, c.machine, value = value)

    raise BypassReturn

def getPrimaryIdentity(user):
    if user.is_authenticated:
        for default in user.default_players.all():
            return default.player.player_name


class Emulation(Script):
    # todo: override exception-handling, storing exception on task.
    # Then, read flag on (rendering) task completion handler
    # to know what to do (push q reponse) with it.

    debugging = False # True
    if debugging:
        def tracing(self, frame, pos, instr, args):
          # import pdb; pdb.set_trace()
          name = getattr(instr, '__name__', '?')
          msg = '%04d: %s(%s)' % (pos, name, ', '.join(map(repr, args)))

          # print(frame.procedure)
          print(msg)

          # if name == 'call':
          #     print '    %r' % frame.task.stack[-1]
          #     if frame.task.name:
          #         print '    %s' % frame.task.name


class EmulatedCodeTaskCreation(TaskCreation):
    def __init__(self, trigger, operator = None, audit = None, trace = None,
                 account = None, traceback = None, initialize = None, name = None,
                 timeout = None, finishingScript = None, onComplete = None,
                 *args, **kwd):

        TaskCreation.__init__(self, *args, **kwd)
        self.trigger = trigger

        self.operator = operator
        self.audit = audit
        self.trace = trace
        self.account = account
        self.traceback = traceback
        self.initialize = initialize
        self.name = name
        self.timeout = timeout
        self.finishingScript = finishingScript
        self.onComplete = onComplete

    # def __del__(self):
    #     print(f'[{self.__class__.__name__}] delete')

    def createTask(self, environ):
        return self.taskClass.Load(environ = environ, user = self.user)

    def preInitTask(self, task, *args, **kwd):
        # debugOn()
        if self.audit in ['debug', 'trace', 'stack']:
            if self.operator is not None:
                # This sends stylized html traces to the session, but since
                # we don't have a peer object, only operator name, we need
                # to interface with debugInstructionPeer at an operator level.
                # self.tracing = self.debugInstructionPeer(self.peer)

                task.tracing = task.debugInstructionOperator # (self.operator)
                task.debugStack = self.audit == 'stack'
                task.operator = self.operator

        elif self.audit is True:
            task.tracing = task.__class__.auditInstruction

        elif self.audit is None:
            if self.trace is not None:
                task.tracing = self.trace

        # For billing API.
        if self.account is not None:
            task.account = self.account

        self.procedure.setEnvironment(task.environ)

        return TaskCreation.preInitTask(self, task, *args, **kwd)


    def postInitTask(self, task, frame):
        if self.traceback is not None:
            try: runtime.call.System.Journal.waitLogs(task, self.traceback)
            except runtime.doesNotExist: pass

        if self.initialize:
            # A chance to construct memory-bound objects.
            # debugOn()
            self.initialize(task)

        if self.name is not None:
            task.name = self.name

        if self.timeout: # Is non-zero.
            self.applyTimeout(task, self.timeout)

        if self.onComplete:
            task.onComplete(self.onComplete)

        # todo: pass remaining kwd from _activate (synchronous).
        # TaskCreation.postInitTask(self, task, frame)
        executeGirl(task)

        if self.finishingScript:
            @task.onComplete
            def done(task, exception = None):
                # Spawn new task.
                newModuleTask(self.finishingScript, trigger = self,
                              completedTask = task)

        return task

    def applyTimeout(self, task, timeout):
        self.trigger.checkValidTimeout(timeout)

        from world import heartbeat as vm
        from stuphos.kernel import Pure
        from ph.interpreter.mental.native import _setTimeout # todo: get from stuphos.kernel

        def terminateTask():
            task.Terminate(task.machine)

        # environ['timeout$'] = \
        _setTimeout(vm, self.user,
                    self.programmer,
                    Pure(terminateTask),
                    timeout, None)


class TriggerTask(writeprotected, Object):
    def __init__(self, task, procedure):
        self._task = task
        self._procedure = procedure

    @property
    def _onComplete(self):
        return self._task.onComplete

    @property
    def _result(self):
        return self._task.stack.pop()[0]

    # @property
    def result(self):
        # Marshalized Object and data.
        return outcomeOf(self._task, self._onComplete)


class Trigger(writeprotected, Object):
    # todo: get rid of synchronous attr, it has no meaning
    __public_members__ = ['code', 'environment']

    __name__ = 'trigger' # ?

    _TaskClass = TriggerTask

    TIMEOUT_MAX = 60 * 60 * 24 * 7 * 4 * 3 # 3 Months.

    def __init__(self, code, synchronous = False, environment = None, path = None):
        self.code = code
        self._synchronous = synchronous
        self.environment = environment
        self._path = path

        # todo: on-construct security check for synchronous allowed.

    @property
    def synchronous(self):
        return self._synchronous

    @property
    def preprocessedCode(self):
        # Always a module -- account for single-line yaml.
        return self.code + '\n' # return renderTemplate(self.code, trigger = self)

    @property
    def _module(self):
        # try: return self._m_module
        # except AttributeError:
        #   from mud.lang.girl import Girl
        #   mod = self._m_module = Girl(Girl.Module, self.preprocessedCode)
        #   return mod

        module = Girl(Girl.Module, self.preprocessedCode)
        # module.setCodeSource() # todo
        return module


    @property
    def _expression(self):
        # How will this work with newlines?
        return Girl(Girl.Expression, self.preprocessedCode)

    _Emulation = Emulation


    def checkValidTimeout(self, timeout):
        # raise NotImplementedError

        if not isinstance(timeout, (int, float)):
            raise TypeError(type(timeout).__name__)

        if timeout <= 0 or timeout > self.TIMEOUT_MAX:
            raise ValueError(f'Must be > 0 and <= {self.TIMEOUT_MAX}')


    def _activate(self, procedure, *args, **kwd):
        # Operate TaskCreation API now.
        environ = kwd.pop('environ', dict())
        locals = kwd.pop('locals', None)
        forceLocals = kwd.pop('forceLocals', None)
        progr = kwd.pop('programmer', None)
        user = kwd.pop('user', None)
        onComplete = kwd.pop('onComplete', None)

        operator = kwd.pop('operator', None)
        audit = kwd.pop('audit', None)
        trace = kwd.pop('trace', None)
        account = kwd.pop('account', None)
        traceback = kwd.pop('traceback', None)
        init = kwd.pop('initialize', None)
        name = kwd.pop('name', None)
        timeout = kwd.pop('timeout', None)
        finishingScript = kwd.pop('finishing', '')

        environ.setdefault('trigger', self)
        environ.setdefault('environment', self.environment)
        environ.setdefault('container', self.environment)
        # environ.setdefault('doc', self.environment)
        environ.setdefault('path$', self._path)

        # todo: push remaining kwd into EmulatedCodeTaskCreation for executeGirl.

        create = dict(taskClass = Emulation, environ = environ,
                      operator = operator, audit = audit, trace = trace,
                      account = account, traceback = traceback,
                      initialize = init, name = name, timeout = timeout,
                      finishingScript = finishingScript,
                      programmer = progr, user = user,
                      procedure = procedure, locals = locals,
                      forceLocals = forceLocals,
                      onComplete = onComplete)

        task = EmulatedCodeTaskCreation.Create(self, **create)

        return self._TaskClass(task, procedure)


    def _activateInline(self, procedure, *args, **kwd):
        pass


    # def _activate(self, procedure, *args, **kwd):
    #     kwd['synchronous'] = bool(self.synchronous)

    #     try: environ = kwd.pop('environ')
    #     except KeyError: environ = dict()

    #     environ.setdefault('trigger', self)
    #     environ.setdefault('environment', self.environment)
    #     environ.setdefault('doc', self.environment)

    #     # User might differ from programmer setting as far as claimed identities.
    #     task = self._Emulation.Load(environ = environ, user = kwd.pop('user', None))

    #     try: task.operator = kwd.pop('operator')
    #     except KeyError:
    #         pass

    #     progr = kwd.pop('programmer', None)

    #     try:
    #         audit = kwd.pop('audit')
    #         if audit == 'debug':
    #             task.tracing = task.__class__.debugInstruction
    #         elif audit is True:
    #             task.tracing = task.__class__.auditInstruction

    #     except KeyError:
    #         try: task.tracing = kwd.pop('trace')
    #         except KeyError:
    #             pass

    #     # For billing API.
    #     try: account = kwd.pop('account')
    #     except KeyError: pass
    #     else:
    #         if account is not None:
    #             task.account = account

    #     procedure.setEnvironment(task.environ)

    #     try: locals = kwd.pop('locals')
    #     except KeyError:
    #         task.addFrameCall(procedure, arguments = args,
    #                           programmer = progr)
    #     else:
    #         task.addFrameCall(procedure, locals = locals,
    #                           arguments = args,
    #                           programmer = progr)

    #     finishingScript = kwd.pop('finishing', '')

    #     try: traceback = kwd.pop('traceback')
    #     except KeyError: pass
    #     else:
    #         try: runtime.call.System.Journal.waitLogs(task, traceback)
    #         except runtime.doesNotExist: pass

    #     try: init = kwd.pop('initialize')
    #     except KeyError: pass
    #     else: init(task) # A chance to construct memory-bound objects.

    #     try: name = kwd.pop('name')
    #     except KeyError: pass
    #     else: task.name = name

    #     try: timeout = kwd.pop('timeout')
    #     except KeyError: pass
    #     else:
    #         if timeout:
    #             self.checkValidTimeout(timeout)

    #             from world import heartbeat as vm
    #             from stuphos.kernel import Pure
    #             from ph.interpreter.mental.native import _setTimeout # todo: get from stuphos.kernel

    #             def terminateTask():
    #                 task.Terminate(task.machine)

    #             # environ['timeout$'] = \
    #             _setTimeout(vm, progr, Pure(terminateTask), timeout, None)


    #     # print(f'task.name: {task.name}')

    #     # Todo: don't return this (it's a decorator).  Until a replacement
    #     # can be written, be aware that this is returned to the girl code.
    #     onComplete = executeGirl(task, **kwd)

    #     if finishingScript:
    #         @onComplete
    #         def done(task, exception = None):
    #             # Spawn new task.
    #             newModuleTask(finishingScript, trigger = self,
    #                           completedTask = task)

    #     # @onComplete
    #     # def debugViewTermination(task, exception = None):
    #     #     debugOn()
    #     #     locals

    #     # Returned to the protected girl environment.
    #     return self.Task(task, procedure)

    def _activateAsync(self, procedure, task):
        # Used by asynchronous tasks to schedule evaluation.
        procedure.setEnvironment(task.environ)

        locals = dict(environment = self.environment,
                      doc = self.environment,
                      trigger = self)

        return task.frameCall(procedure, locals = locals)

    def _activateCheck(self, *args, **kwd):
        assert 'programmer' not in kwd, KeyError('programmer')
        assert 'operator' not in kwd, KeyError('operator')
        assert 'audit' not in kwd, KeyError('audit')
        assert 'trace' not in kwd, KeyError('trace')
        assert 'context' not in kwd, KeyError('context')

        return self._activate(*args, **kwd)

    def call(self, *args, **kwd): # spawn
        progr = vmCurrentTask().findProgrammer()
        return self._activate(self._module, *args,
                              **dict(environ = kwd,
                                     user = None if progr is None else \
                                        findUserByName(progr.principal),
                                     programmer = progr))

    def callForResult(self, *args, **kwd):
        return self.call(*args, **kwd).result()
    __call__ = callForResult


    def callInline(self, *args, **kwd):
        pass


    @property
    def _evaluation(self):
        'Synchronous activation: wait for new task/frame call to execute.'

        from stuphos.kernel import Machine

        try: task = Machine.GetContextObject().task
        except AttributeError:
            # Not running within virtual machine task -- synchronously evaluate.
            # Note: there's no authority associated with this activation method.
            task = self._Emulation()

        return self._activateAsync(self._expression, task)


Evaluation = Trigger

class Inline(Trigger):
    @property
    def _module(self):
        return self.code

    @classmethod
    def _Build(self, ast, *args, **kwd):
        return self(Girl(Girl.Built, ast), *args, **kwd)

inline = Inline._Build

class View(writeprotected, Object):
    def register(self): # What is this used for?
        raise NotImplementedError
    def _render(self, request = None):
        raise NotImplementedError
    def _debugging(self, request, task, etype, value, tb, traceback): # *args, **kwd
        # Specifically, there was a bug during execution of the context trigger,
        # so this is a good place to generate a report page with task traceback.

        raise etype(value).with_traceback(tb) # there was a python bug


class NodePath(writeprotected, list):
    # __init__ = list.__init__

    def __init__(self, items):
        # Todo: whatever's constructing NodePath/DeepView must do this encoding..!
        # But this object maintains internal consistancy as a native object.
        # debugOn()
        list.__init__(self, (s.decode('utf-8') if isinstance(s, bytes)
                             else s for s in items))

    @property
    def _controlObject(self):
        return self

    def __getitem__(self, item):
        # When accessing a slice, wrap the result in a NodePath (protected).
        result = list.__getitem__(self, item)
        if isinstance(item, slice):
            result = self._controlObject.__class__(result) # classOf(self._controlObject)(result)

        return result

    # def getElementAt(self, index):
    #     return list.__getitem__(self, index)
    def getTrailingElements(self):
        return vmNewSequence(list.__getitem__(self, slice(1, None, None)))

    @property
    def string(self):
        return '/'.join(self)


class DeepView:
    class _DeepViewPath(NodePath):
        def __init__(self, view, path):
            NodePath.__init__(self, path)
            self._view = view

        def __repr__(self):
            path = ', '.join(map(repr, self))
            return f'<deep-view on {self._view}: {path}>'

        @property
        def _controlObject(self):
            return self._view

        def _render(self, request = None, response = None, **ctxtdct):
            ctxtdct['path'] = self # todo: pass to render as keyword argument.
            return self._view._render(request = request, response = response,
                                      **ctxtdct)

    def lookup(self, *names):
        return self._DeepViewPath(self, names)


# @runtime.available(runtime.System.Journal)
# def debugging(log, self, etype, value, tb):

def debugging500(self, noAccess, request, task, etype, value, tb, traceback):
    # import pdb; pdb.set_trace()

    # todo: generate html-ready (FO) tracebacks

    if isinstance(value, Processor.UncaughtError):
        etype = value.etype
        tb = value.tb

        traceback = value.traceback # if traceback is None else traceback # (before changing value)
        value = value.value


    from django.template import Context, Template

    if isinstance(value, NoAccessException):
        return Template(noAccess or '''\
        <h2>Error: {{ error }}</h2>

        ''').render(Context(error = value))


    debugShowStringSources = (self.debug == 'show-string-sources')

    if not debugShowStringSources and not isYesValue(self.debug):
        # The idea at this point is that, because this is web view error
        # handling, but it is generally uncaught, we need to communicate
        # to the initiator (and the programmer) the things that we need
        # to.  If the site debug page is disabled, then the initiator
        # will basicaly get a 'didn't work' message.

        raise value.with_traceback(tb)

    if self.debug and traceback and task is not None:
        primaryIdentity = getPrimaryIdentity(request.user)
        vtb = '\n'.join(task._task.formatTraceback \
            (traceback, checkAccess = primaryIdentity,
             hide_string_sources = not debugShowStringSources))
    else:
        vtb = ''


    if isYesValue(getConfig('native-traceback', 'Interpreter')):
        # But we're mostly interested in python exception.
        tb = '%s:\n%s\n' % (exceptionHeader(etype, value),
                            tracebackString(tb))
    else:
        tb = exceptionHeader(etype, value)


    from django.template.loader import get_template
    from django.template.exceptions import TemplateDoesNotExist

    try: t = get_template('wm/500.html')
    except TemplateDoesNotExist:
        return tb + '\n' + vtb

    return t.render(dict(traceback = tb, vtraceback = vtb,
                         task = None if task is None else task._task))

    # return 'Heres where we return a 500 template with traceback!'

class EmulatedView(View, DeepView):
    __public_members__ = ['context', 'environment', 'source', 'debug', 'path', 'timeout', 'security']
    _debugging = debugging500

    class _Meta(Object._Meta):
        Attributes = ['_path']

    __repr__ = Object.__repr__

    DEFAULT_TIMEOUT = None

    def __init__(self, template, context: Trigger, environment = None,
                 source = None, debug = False, path = '',
                 timeout = None, security = None, values = None,
                 noAccess = None):

        self._template = template
        self.context = context
        self.environment = environment
        self.source = source
        self.debug = debug
        self._path = path.split('/')
        self.timeout = timeout
        self.security = security
        self._values = values
        self._noAccess = noAccess

    @property
    def path(self):
        return vmCurrentTask().sequence(self._path)

    def renderTemplate(self, **kwd):
        if self._template is None:
            return '' # kwd.get('content', '')

        return renderTemplate(self._template, **kwd)

    class _RequestAdapter(writeprotected, Object):
        def __init__(self, request, query = None):
            self._request = request
            self._query = query

        def __repr__(self):
            return f'<request$adapter {self.method} {self.path}>'

        @property
        def method(self):
            return getattr(self._request, 'method', None)

        @property
        def path(self):
            return getattr(self._request, 'path', None)

        @property
        def headers(self):
            return vmNewMapping(*self._request.headers.items())

        @property
        def GET(self):
            # debugOn()
            if getattr(self, '_stuphos_resetGET', False):
                del self.GET, self._stuphos_resetGET

            try: return self.__GET
            except AttributeError:
                g = self.__GET = vmNewMapping(*list(self._request.GET.items()))
                # if self._query:
                #     g.update(self._query)

                return g

        @GET.deleter
        def GET(self):
            try: del self.__GET
            except AttributeError:
                pass

        @property
        def POST(self):
            try: return self.__POST
            except AttributeError:
                g = self.__POST = vmNewMapping(*list(self._request.POST.items()))
                return g


        # These things are currently restricted:
        # @property
        # def META(self):
        #     return vmNewMapping(*self._request.META.items())
        # @property
        # def FILES(self):
        #     try: return self.__FILES
        #     except AttributeError:
        #         g = self.__FILES = vmNewMapping(*list(self._request.FILES.items()))
        #         return g


        @property
        def userAgent(self):
            return self._request.META['HTTP_USER_AGENT']


        @property
        def user(self):
            return self._User(self._request.user, request = self._request)

        @property
        def session(self):
            return # :security:

            try: find = runtime[runtime.Web.Adapter.SessionManager] \
                    .findSessionMappingByPlayerName

            except AttributeError: pass
            else: return find(getPrimaryIdentity \
                    (self._request.user))

            return self._request.session

        @property
        def body(self):
            return self._request.body

        # provide access to persistant storage.


        def _sessionKey(self, name, task = None, identity = None):
            if identity is None:
                if task is None:
                    task = vmCurrentTask()

                identity = task.findProgrammer()
                if identity is not None:
                    identity = identity.principal

            return f'stuphos$request:{identity or ""}:{name}'

        def sessionGet(self, name):
            task = vmCurrentTask()
            return protectedMemoryLoad(task, self._request.session \
                [self._sessionKey(name, task)])

            # return protectedMemoryLoad(vmCurrentTask(), self._request.session \
            #     ['stuphos$request:' + name])

        def _sessionSet(self, name, value):
            # self._request.session['stuphos$request:' + name] = str.__str__(value)
            self._request.session[self._sessionKey(name)] = str.__str__(value)

        def _sessionClear(self, *names):
            for n in names:
                try: del self._request.session[self._sessionKey(n)]
                except KeyError: pass

        '''
        def rqContext(request, name):
            return security$context$new \
                ('apikey:' + request.sessionGet \
                    ('context$' + name))

        def rqContext$call(request, name):
            return act(rqContext(request, name), \
                args$slice(2), keywords$())

        def rq$render(request, path):
            rq = rqContext$call(request, 'web')
            return rq(rq \
                (accessitems, library, path) \
                 .render, request)

            (view):
                context(trigger)::
                    return rq$render(request, path)

        '''

        # Access cache with this user as key.
        def _sessionKeyCurrentUser(self, name, default = None):
            for p in self._request.user.default_players.all():
                identity = p.player.player_name.lower()
                break
            else:
                if default is None:
                    raise RuntimeError('User has no primary identity!')

                identity = default

            return self._sessionKey(name, identity = identity)

        def sessionGetCurrentUser(self, name, defaultIdentity = None):
            return protectedMemoryLoad(vmCurrentTask(),
                self._request.session[self._sessionKeyCurrentUser \
                    (name, default = defaultIdentity)])

        def _sessionSetCurrentUser(self, name, value, defaultIdentity = None):
            self._request.session[self._sessionKeyCurrentUser \
                (name, default = defaultIdentity)] = str.__str__(value)

        def _sessionClearCurrentUser(self, name, defaultIdentity = None):
            'XXX Arguments are single positional name (and optional default keyword).'

            try: del self._request.session[self._sessionKeyCurrentUser \
                    (name, default = defaultIdentity)]

            except KeyError: pass


        @property
        def realIPAddress(self):
            vmCurrentTask().checkAccessSystem(['system:network:identity:self'], 'read')
            return self._request.META.get('HTTP_X_REAL_IP')


        class _User(writeprotected, Object):
            def __init__(self, user, request = None):
                self._user = user
                self._request = request

            def __repr__(self):
                if self._user is None:
                    return '<user$adapter$invalid>'

                return f'<user$adapter>' # ' {self.username}>'

            # @property
            # def username(self):
            #     return self._user.username
            # name = username

            @property
            def is_authenticated(self):
                return self._user.is_authenticated

            @property
            def is_superuser(self):
                return self._user.is_superuser

            @property
            def _primaryIdentity(self):
                return getPrimaryIdentity(self._user)

            @property
            def primaryIdentity(self):
                # User (Adapter) objects are passed to code running with other user permissions,
                # so we hide this.  For now, only current programmers can access their primary
                # identity.
                from stuphos.kernel import vmCurrentTask
                name = self._primaryIdentity
                if name is not None:
                    lowerName = name.lower()

                    progr = vmCurrentTask().findProgrammer()
                    if progr is not None:
                        if progr.principal.lower() == lowerName:
                            return name


            @property
            def _session(self):
                '''
                look-at-room(view):
                    context(trigger)::
                        return lookAtRoom(request.user._session.avatar.location)

                '''

                        # (self._primaryIdentity)

                return runtime[runtime.Web.Adapter.SessionManager] \
                    .findSessionIdByPlayerName \
                        (self.primaryIdentity)


            @property
            def securityContext(self):
                # Note: requiring a login permission here complicates serving user-to-user
                # views, but we can't assume that the requesting user wants to give all
                # control to any other arbitrary user (besides the system) simply because
                # they're viewing the resource.  What is needed is user-specified ACL.
                # debugOn()

                from stuphos.kernel import securityContext, Programmer, vmCurrentTask
                principal = self._primaryIdentity

                resource = ['system:user:context']
                if principal is not None:
                    # The logic here is: If we're "switching into" a user (like AnonymousUser)
                    # that has no primary identity, search for a stronger permission context:
                    # one that is more general.
                    resource.append(principal)

                try: vmCurrentTask().checkAccessSystem(resource, 'impersonate')
                except NoAccessException as e:
                    print(f'[http$request$user$context] {e}')
                    return

                return securityContext(Programmer(principal), user = self._user)

            @property
            def billingContext(self):
                from stuphos.kernel import securityContext, vmCurrentTask
                task = vmCurrentTask()

                # XXX Why are we checking primary identity when what we really want
                # is user identity.
                try: task.checkAccessSystem(['system:user:context', self._primaryIdentity], 'charge')
                except NoAccessException as e:
                    print(f'[http$request$user$context$billing] {e}')
                    return

                return securityContext(task.findProgrammer(), user = self._user)

            def checkAccessError(self, op, resource):
                from stuphos.kernel import Programmer, vmCurrentTask
                principal = self._primaryIdentity.lower()

                if isinstance(resource, str):
                    resource = resource.split('/')

                core = runtime[runtime.Agent.System]
                # debugOn()

                if core is not None and core.principalHasAccess(principal, resource, op):
                    return True

                raise NoAccessException(Programmer(principal), resource, op)


    def _securityCheck(self, core, user, progr, subresource):
        sec = None

        principal = None if progr is None else progr.principal.lower()
        if core.principalHasAccess(principal, ['system:view:security'], 'grant'):
            sec = self.security

        if sec in ['allow', 'allow all', 'allow-all']:
            return True

        # debugOn()
        if sec == 'authenticated':
            return user is not None and user.is_authenticated

        def checkAccess(path):
            # We have to manually build the check because the task
            # has no programmer frames (security context) yet.
            if isinstance(path, str):
                path = path.split('/')

            if core is not None:
                if core.principalHasAccess(principal, path, 'read'):
                    return True

            raise NoAccessException(progr if progr is None else progr.principal.lower(),
                                    path, 'read')

        if sec in [None, 'default', 'path']:
            if self.context:
                return checkAccess(self.context._path + self._path) # + subresource

            return True

        # if isinstance(sec, dict):
        #     path = sec['path']

        #     return checkAccess(path)

        raise NotImplementedError(f'view.security = {sec}')

    def _render(self, request = None, response = None, account = None,
                path = None, requestAdapter = None, programmer = None,
                query = None, core = None, context = None, initiatingUser = None):

        from phsite.network.adapter.commands import CoreRequest
        from world import heartbeat as vm # XXX Todo: runtime.System.Engine

        # Use initiatingUser if set, otherwise use programmer user or request.user
        # if that's not set.
        if initiatingUser is None:
            # Note: this user setting will be overridden below if programmer is set.
            if isinstance(request, CoreRequest):
                user = request._user
            elif request is not None:
                # Common external page requests (unless interface owner is specified).
                user = request.user
            else:
                user = None
        else:
            user = initiatingUser

        progr = programmer
        # debugOn()
        # If progr.principal is '', then the interface doesn't have an owner.
        if programmer is None:
            # from phsite.network.models import DefaultPlayer
            from phsite.network.embedded.olc import WebProgrammer

            # Always use programmer specified (from interface setting),
            # but if it's None, get it from the primary identity.
            #
            # Since we're always using programmer, provide programmer-
            # setting security interface in native for the view.
            #
            # debugOn()
    
            if user is not None and user.is_authenticated:
                for d in user.default_players.all():
                    progr = WebProgrammer(d.player.player_name)
                    break

        elif initiatingUser is None:
            # Use interface owner.
            from stuphos.kernel import findUserByName
            user = findUserByName(programmer.principal)


        # debugOn()
        securityUser = None if request is None else request.user

        # Raises NoAccessException.  But also returns False if the check failed.
        try: passCheck = self._securityCheck(core, securityUser, progr, path)
        except NoAccessException as e:
            securityError = e
        else:
            securityError = None if passCheck else \
                            NoAccessException('<security user>',
                                              path, 'read')

            # progr = None if progr is None else progr.principal
            # progr = None if progr is None else progr.lower()

        if securityError is not None:
            return dict(content = self._debugging \
                        (request, None, securityError.__class__,
                         securityError, None, None),
                        status = 500)


        if self.debug in ['debug', 'trace', 'stack']:
            audit = str.__str__(self.debug)
        else: # what if self.debug is True?
            audit = None

        # *Call from an extra-heartbeat thread.
        q = Queue()

        # def report(logger, task, traceback):
        #     # Log the traceback to console.
        #     logger.systemLog(task, traceback)
        report = None

        if context is None:
            context = dict()

        context['source$'] = self.source # XXX Must use native('source', path) in triggers.
        # context['view'] = self.path # Q: setdefault?
        contextObject = context # todo: wrap to provide other services?

        # print(f'[emulated-view.render] {queryString}')
        # debugOn()

        if requestAdapter is None:
            if request is None:
                requestAdapter = None
            else:
                requestAdapter = self._RequestAdapter(request, query = query)

        locals = dict(request = requestAdapter)

        # locals['source'] = self.source

        protected = None
        protectedCont = [None]
        outputLocals = [None]

        def initializeTask(task):
            nonlocal protected
            outputLocals[0] = o = task.frame.locals

            # Convert source document into memory-safe structure.
            # Note: this is actually an (opaqued) containerAccessor.
            e = constrainStructureMemory(task, self.environment)
            o['environment'] = e
            o['container'] = e

            # Store memory-safe mapping for response local.
            # p = protected[0] = task.memory.Mapping(task.memory, **response)
            # task.frame.locals['response'] = p

            with vm.threadContext(task = task):
                protected = protectedCont[0] = task.memory.Mapping(task.memory, **response)
                o['response'] = protected

                # debugOn()
                environ = task.shared_mapping(*contextObject.items())
                # environ._track('context')
                # print(f'[init$task$1] context: {id(environ)}, refcount: {getrefcount(environ)}')

                # XXX This means variables stored in context will be accessible by default
                # to the rest of the program by default.
                # task.environ = environ
                o['context'] = environ

                environ['context'] = environ
                environ['view'] = task.sequence(self.path)

                # print(f'[init$task] context: {id(environ)}, refcount: {getrefcount(environ)}')

                if isinstance(path, NodePath) or path is None:
                    o['path'] = path
                else:
                    o['path'] = task.sequence(path)


                # print(f'[init$task$environ] {id(task.environ)}, refcount: {getrefcount(task.environ)}')


        task = (isYesValue(configuration.AgentSystem.www_superior_enabled) and \
                self._activateContextSuperior or self._activateContext) \
            (vm, q, response, protectedCont, context,
             path, locals, progr,
             user, initializeTask,
             audit, report, account,
             outputLocals)


        (success, result) = q.get() # *
        if success:
            # debugOn()
            return result

        # debugOn()
        return dict(status = 500, content = self._debugging
            (self._noAccess, request, task, *result))


    def _activateContext(self, vm, q, response, protectedCont, context,
                         path, locals, progr,
                         user, initializeTask,
                         audit, report, account,
                         outputLocals):

        # debugOn()

        module = self.context._module

        # Race request thread doesn't set this onCompleteHandler before heartbeat
        # thread picks up activated context trigger and executes/finishes it.
        #
        # So we pass it as the onComplete parameter to trigger activation.
        def completeViewRequest(task, exception = None, traceback = None):
            # print(f'[view-render-complete]: {task}: {exception}')

            # 5
            # ctx = outputLocals[0]["context"]
            # print(f'[view$context$done] context: {id(ctx)}, refcount: {getrefcount(ctx)}')

            # print(f'[view$complete$response] {id(protectedCont[0])}')

            # debugOn()
            if response is not None:
                response.update(protectedCont[0])

            if exception is not None:
                # Introspect into the ph runtime with debugging view.
                q.put((False, exception + (traceback,)))
            else:
                try: result = self._completeView_render(vm, task, outputLocals, module)
                except:
                    from sys import exc_info
                    q.put((False, exc_info() + (traceback,)))
                else:
                    q.put((True, result))


        task = self.context._activate(module,
                                      name = f'view({path})',
                                      locals = locals,
                                      programmer = progr,
                                      traceback = report,
                                      account = account,
                                      initialize = initializeTask,
                                      timeout = self.timeout or self.getDefaultTimeout(),
                                      audit = audit,
                                      # task.operator is only set if audit is 'debug'
                                      operator = progr.principal if progr is not None else None,
                                      user = user,
                                      onComplete = completeViewRequest)

        return task

    _activateContextServe = _activateContext


    def _completeView_render(self, vm, task, outputLocals, module):
        from stuphos.kernel import EmptyStackError

        try: responseValue = task.stack.pop()[0]
        except EmptyStackError:
            # Treat like returning None, for now.
            responseValue = None

        # from stuphos.etc.tools.strings import compactify
        # print(f'[view$render$complete] {compactify(str(responseValue), 80)}')

        if isinstance(responseValue, (str, bytes)):
            return dict(content = responseValue)
        elif isinstance(responseValue, dict):
            return responseValue
        elif responseValue is not None: # and responseValue != (None,):
            raise TypeError(type(responseValue))
        else:
            # By default, this requires a permission because django templates are
            # unsafe.  When that situation is remedied, grant to group:public.
            # debugOn()
            task.checkAccessSystem(['system:network:template', 'django'], 'render',
                             publicAccess = True)

            # Re-acquire unicode/basestring type for renderTemplate call.

            with vm.threadContext(task = task):
                # environ might be a MemoryMapping which generates a
                # memory.sequence when its items method is called.
                # items = task.environ.items()

                # debugOn()
                try: context = outputLocals[0].pop('context') # delete reference
                except KeyError:
                    context = dict()

                items = context.items()

                # for (key, value) in context.items():
                #     if isinstance(value, str):
                #         context[key] = str.__str__(value)

            for (key, value) in items:
                if isinstance(key, bytes):
                    # del ctxtdct[key] # The bytes key.
                    context[key.decode('ascii')] = value
                else:
                    context[key] = value

            # todo: do as billable
            # debugOn()
            # from code import InteractiveConsole as    
            # IC(locals = dict(context = context,
            #                  environ = environ)).interact()

            # debugOn()
            try: return self.renderTemplate(**context)
            finally:
                outputLocals[0] = None

                with task.machine.threadContext(task = task):
                    context.clear()

                # XXX GC control
                # module.setEnvironment(None)

                # print(f'[render$view$complete] task: {getrefcount(task)}')

                # ctxid = id(context)
                # ctxrefs = getrefcount(context)
                # ctxkeys = ", ".join(context)

                # print(f'[render$view$complete] context: {ctxid}, refcount: {ctxrefs}, {ctxkeys}')

                # debugOn()


    def activateContextInferior(self, name, locals):
        task = vmCurrentTask()
        progr = task.findProgrammer()
        user = task.user

        task = self.context._activate(self.context._module,
                                      name = str.__str__(name),
                                      locals = locals,
                                      programmer = progr,
                                      # initialize = initializeTask,
                                      user = user
                                      )

        @task._onComplete
        def completeViewRequest(task, exception = None, traceback = None):
            if not task.stack:
                task.stack.push(None)

        return task

    def _activateContextSuperior \
        (self, vm, q, response, protectedCont, context,
         path, locals, progr,
         user, initializeTask,
         audit, report, account,
         outputLocals):

        page: EmulatedView

        core = runtime[runtime.Agent.System]
        if core is None:
            raise RuntimeError('Agent System is not installed!')


        try: page = core[configuration.AgentSystem.page_superior or 'www/superior/page']
        except Exception as e:
            # from stuphos import logException
            # logException(traceback = True)

            return self._activateContextServe \
                (vm, q, response, protectedCont, context,
                 path, locals, progr,
                 user, initializeTask,
                 audit, report, account,
                 outputLocals)


        '''
        interfaces/www/superior::
            page(view):
                context(trigger)::
                    ns = locals().copy()
                    del$('view$client', ns)

                    return view$client.activateContextInferior \
                        ('view(%r)' % path, ns).result()

        '''

        localsClient = locals.copy()
        localsClient['view$client'] = self

        task = page._activateContextServe \
                (vm, q, response, protectedCont, context,
                 path, localsClient, progr,
                 user, initializeTask,
                 audit, report, account,
                 outputLocals)

        @task._onComplete
        def updateContext(_, *error, **kwd):
            # debugOn()
            if 'context' in localsClient:
                context.update(localsClient['context'])

        return task

    # _activateContext = _activateContextSuperior


    def getDefaultTimeout(self):
        return self.DEFAULT_TIMEOUT


RequestAdapter = EmulatedView._RequestAdapter
UserAdapter = RequestAdapter._User


# from stuphos.kernel import LibraryView as libView
# from django.views.decorators.csrf import csrf_exempt

# class LibraryView(libView):
#     'CMS Library View bound to node configuration.'

#     @runtime.available(runtime.Agent.System)
#     @csrf_exempt
#     def render(core, self, request = None, response = None, **ctxtdct):
#         return libView.render(self(request, core), self.path)

#     def __init__(self, path):
#         self.path = path


import codecs
from hashlib import sha256

class StaticView(View):
    __public_members__ = ['content', 'content_type']

    def __init__(self, content, content_type = None):
        self.content = content
        self.content_type = content_type

    def _render(self, *args, **kwd): # request = None, response = None, account = None):
        return self.content

    @property
    def nonce(self):
        return codecs.encode(sha256(self.content).digest(), 'base64')

class AliasedView(View, DeepView):
    __public_members__ = ['path']

    def __init__(self, path):
        if isinstance(path, str):
            (_, qs) = splitquery(path)
            self._query = parse_qs(qs).items()

            path = path.split('/')
        else:
            self._query = []

        if not isinstance(path, (list, tuple)):
            raise TypeError(type(path).__name__)

        self.path = path

    class _recursionGraph(set):
        def __init__(self, initial):
            self.add('/'.join(initial))

        def __call__(self, new):
            new = '/'.join(new)
            if new in self:
                # Recursion detected.
                return True

            self.add(new)

    def _render(self, request = None, **kwd):
        # XXX Fails to detect recursion.
        from ph.interpreter.mental.library.views import renderWM

        # Recursion control.
        receivingContext = kwd.pop('context', None) # Providing clean initial graph point.

        if isinstance(receivingContext, dict):
            recursion = receivingContext.pop('aliasGraph', None)
            if recursion is None:
                recursion = self._recursionGraph(self.path)
            else:
                if recursion(self.path):
                    raise RecursionError('Alias recursion detected!')

            ctx = dict(aliasGraph = recursion)

        else:
            ctx = dict()


        # debugOn()

        kwd['view_path'] = kwd.pop('path', None) # Already passed as positional argument.
        kwd.pop('programmer', None) # Passed later as positional arg.
        kwd.pop('account', None) # Not permitted by renderView.
        kwd.pop('core', None) # Already passed as positional argument.

        # request.path = self.path

        # path = self.path + kwd['view_path']
        # print(f'[alias] {"/".join(path)}')

        path = self.path

        get = request.GET
        for (name, value) in self._query:
            try: v = get[name]
            except KeyError:
                if isinstance(value, list) and len(value) == 1:
                    # XXX AttributeError: This QueryDict instance is immutable
                    get[name] = value[0]
                    break

                v = []
            else:
                # debugOn()
                if isinstance(v, str):
                    v = [v]

            get[name] = v + value

        if self._query:
            request._stuphos_resetGET = True

        # XXX This appends too many times!!
        # qs = '&'.join(f'{l}={r}' for (l, r) in request.GET.items())
        # if qs:
        #     path.append('?' + qs)

        return renderWM(request, request.user, path, ctx, **kwd)


class HtmlView(View):
    '''
    (stuph$html):
      html:
        - head:
          - title: 'The webpage title'
          - style:
              type: 'text/css'
              .content::
                body { margin: 10px }

        - body:
          - div: 'This is the content'
          - button:
              .content: 'Ok?'
              onclick::
                alert('Ok');
    '''

    __public_members__ = ['document']

    def __init__(self, root, context):
        self.document = root
        self._context = context

    _blacklist_element = []
    _blacklist_attribute = {}
    _blacklist_attribute_star = []

    def _render(self, request = None, response = None):
        def buildMap(xxx_todo_changeme):
            (name, items) = xxx_todo_changeme
            if name in self._blacklist_element:
                return ''

            bla = self._blacklist_attribute.get(name, [])
            attrs = []

            if isinstance(items, dict):
                content = ''
                children = []

                for (k, v) in items.items():
                    if k == '.content':
                        content = v
                    elif k == '.children':
                        children = v
                    else:
                        if not k in bla and k not in self._blacklist_attribute_star:
                            # todo: render v structural item
                            v = repr(v).replace('\\n', '\n').replace('\\t', '\t')
                            attrs.append('%s=%s' % (k, v))

                def buildChildren():
                    for c in children:
                        yield build(c)
                    if content:
                        # todo: escape html entities in content
                        # or, render structural item
                        # or, transform other markup
                        yield content

                children = nls(buildChildren())

            elif isinstance(items, list):
                children = nls(mapi(build, items))
            else:
                children = str(items)

            attrs = ' '.join(attrs)

            return '<%s%s%s>\n%s\n</%s>\n' % (name, attrs and ' ' or '',
                                              attrs, indent(children), name)

        def build(node):
            if isinstance(node, dict):
                return ''.join(mapi(buildMap, iter(node.items())))

            elif isinstance(node, list):
                return nls(mapi(build, node))

            else:
                try: r = node.render
                except AttributeError: pass
                else:
                    return str(r())

            return ''

        return build(self.document)

    class _ScriptElement(writeprotected):
        __public_members__ = ['item']

        def __init__(self, item):
            self.item = item

        def render(self):
            return ''

class Template(writeprotected, Object):
    def __init__(self, template):
        self._template = template

    def renderTemplate(self, *args, **kwd):
        for a in args:
            if isinstance(a, (list, tuple)):
                a = dict(a)
            if isinstance(a, dict):
                kwd.update(a)

        return renderTemplate(self._template, **kwd)

    render = __call__ = renderTemplate
    rendering = property(renderTemplate)


class Streaming(writeprotected, Object):
    __public_members__ = ['handler']

    def __init__(self, handler):
        self.handler = handler

    def __call__(self, request, *args, **kwd):
        # todo: setup new task environ with request, and execute handler.
        pass

class EqSet(writeprotected, AutoMemoryMapping):
    def equip(self, ch):
        # :security: native exposure.
        machine.checkAccess(['game:equip'])

        import world
        for (where, vnum) in self.items():
            i = world.item(vnum).instantiate(ch)
            try: ch.equip(i, where)
            except IndexError:
                pass # i.extract()

    __call__ = equip

class AuctionList(writeprotected, AutoMemorySequence):
    def __init__(self, sequence):
        AutoMemorySequence.__init__(self, sequence)
        # self.registerAll()

    def registerAll(self):
        for item in self:
            item.register()
        return self
    __call__ = registerAll


# URLConf patterns.
class UrlConfiguration(writeprotected):
    def __init__(self, value):
        self._patterns = []

        if not isinstance(value, (list, tuple)):
            raise TypeError(type(value).__name__)

        for conf in value:
            if not isinstance(conf, dict):
                raise TypeError(type(conf).__name__)
            if len(conf) != 1:
                raise ValueError(f'{len(conf)}') # : {conf.keys()}')

            (pattern, handler) = next(iter(conf.items()))
            self._patterns.append(UrlPattern(pattern, handler))

    def lookup(self, url, include_pattern = False):
        for pattern in self._patterns:
            match = pattern(url)
            if match is not None:
                if include_pattern:
                    return vmCurrentTask().sequence((pattern, match))

                return match

    __getitem__ = lookup


    @nling
    def __str__(self):
        for (i, pattern) in enumerate(self):
            yield f'#{i}. {pattern._pattern.pattern} -> {pattern.handler}'


import re
class UrlPattern(writeprotected):
    __public_members__ = ['handler']

    def __init__(self, pattern, handler):
        if isinstance(handler, dict):
            handler = handler['handler']

        if isinstance(handler, str):
            handler = handler.split('/')

        if not isinstance(handler, (list, tuple)):
            raise TypeError(type(handler).__name__)

        self._pattern = re.compile(pattern)
        self.handler = handler

    def __repr__(self):
        return f'<pattern {repr(self._pattern.pattern)}: {self.handler}>'

    def __call__(self, input):
        match = self._pattern.match(input)
        if match is not None:
            return UrlMatch(match, self.handler)


from stuphos.kernel import StringValue

class UrlMatch(writeprotected):
    def __init__(self, match, handler):
        self._match = match
        self._handler = handler
    def __call__(self):
        return vmCurrentTask().sequence(self._match.groups())

    @property
    def handler(self):
        return vmCurrentTask().sequence(self._handler)

    @property
    def handlerString(self):
        return StringValue('/'.join(self._handler))


class containerAccessor(writeprotected):
    # Protected structural accessor object.

    def __init__(self, object):
        self._object = object

    def __getitem__(self, item):
        value = self._object[item]
        if isinstance(value, (dict, list, tuple)):
            return containerAccessor(value)

        return value

    def __getattr__(self, name):
        try: return object.__getattribute__(self, name)
        except AttributeError as e:
            try: return self[name]
            except (KeyError, TypeError):
                raise e

    def __iter__(self):
        # debugOn()
        if isinstance(self._object, (list, tuple)):
            return iter(self._object)
        elif isinstance(self._object, dict):
            return iter(self._object.items())


    def lookup(self, *path):
        r = self._object

        while path:
            (n, *path) = path

            try: o = r.lookup
            except AttributeError:
                r = r[n]
            else:
                r = o(n, *path)

        return r


class Factory(Submapping):
    from .db.vardb import db, table

    def trigger(self, name, value, **kwd):
        from stuphos.language.document.interface import getContextEnvironment

        if isinstance(value, str):
            code = value
            synchronous = False
        else:
            code = value['code']
            synchronous = value.get('synchronous', False)
            if synchronous:
                raise RuntimeError('Synchronous triggers not allowed!') # Keep this for now. :security:

        # Todo: kwd['container'] is a dict (not a Building.Item)
        # debugOn()
        env = containerAccessor(kwd['container'])

        # For relative dotlevel path lookups.
        path = getContextEnvironment('document', default = None)
        return Trigger(code, synchronous, env, path = path)

    task = let = evaluation = code = trigger

    def emulation(self, name, value, **kwd):
        return None

        # Todo: Pass a procedure/module and emulate a buffered version of those instructions.
        if isinstance(value, grammar.Node):
            pass # validated, but compile todo
        elif not isinstance(value, str):
            raise TypeError(type(value))

        # todo: compile the value?
        # value = Girl(Girl.Module, value)

        from stuphos.system.api import game
        task = game.emulateTask(value) # as module?
        return Trigger.Task(task, None)

    def view(self, name, value, **kwd):
        content_type = None

        if isinstance(value, str):
            content = value
        else:
            try: content = value.pop('content')
            except TypeError as e:
                # XXX Err
                content = str(e)

            except KeyError:
                # Build an emulator program for rendering data.
                template = value.pop('template', None)
                context = value.pop('context')
                timeout = value.pop('timeout', None) # int(configuration.Management.default_view_timeout))
                security = value.pop('security', None)

                debug = value.pop('debug', False)

                # debugOn()
                env = containerAccessor(kwd['container'])

                # if isinstance(context, str):
                #     context = LibraryPathTrigger(context)

                if not isinstance(context, (Trigger,)): # Procedure._Interface)):
                    raise ValueError(context)

                return EmulatedView(template, context, env,
                                    # todo: 'onerror: traceback'
                                    values = value,
                                    debug = debug,

                                    # XXX I thought this was: stuphos.language.document.interface.getContextEnvironment('document')
                                    source = kwd.get('document'), # source is a positional keyword in mud.lang.structure.document

                                    path = name, # XXX use document loader path, since this is relative
                                    timeout = timeout,
                                    security = security)

            else:
                content_type = value.get('content-type')

        return StaticView(content, content_type = content_type)

    def alias(self, name, value, **kwd):
        return AliasedView(value)


    def python(self, name, value, **kwd):
        from stuphos.runtime.architecture.api import _safe_native
        vmCurrentTask().checkAccessSystem(['system:language:python'], 'execute')

        if not isinstance(value, str):
            raise TypeError(type(value))

        code = compile(value, f'<{name}>', 'exec')

        @_safe_native
        def call(*args, **kwd):
            ns = dict(arguments = args, keywords = kwd,
                      environment = kwd)

            exec(code, ns, ns)

            return ns.get('__return')

        # call.__name__ = name
        return call


    def include(self, name, value, **kwd):
        raise NotImplementedError('Experimental')

        if isinstance(value, str):
            value = value.split('/')

        if not isinstance(value, (list, tuple)):
            raise TypeError(type(value).__name__)

        task = vmCurrentTask()
        return task.native.structure(task.frame, value)


    def urlconf(self, name, value, **kwd):
        return UrlConfiguration(value)
    patterns = urlconf


    # def libraryView(self, name, value, **kwd):
    #     return LibraryView(value)

    def template(self, name, value, **kwd):
        return Template(value)

    def streaming(self, name, value, **kwd):
        return # Streaming(self.trigger(name, value, **kwd))

    def html(self, name, value, **kwd):
        return # HtmlView(value, kwd)

    def encoded(self, name, value, **kwd):
        return # value.decode('base64')
    def zencoded(self, name, value, **kwd):
        return # value.decode('base64').decode('zlib')

    def configuration(self, name, value, **kwd):
        return # XXX :skip: Provide native-supported Configuration impl.

        from io import StringIO
        from configparser import ConfigParser
        from .management.config import Configuration

        cfg = ConfigParser()
        cfg.readfp(StringIO(value))

        return Configuration(cfg, name)

    # def pgAuth(self, name, value, **kwd):
    #     from .management.db import dbCore
    #     value['type'] = 'pg-auth'
    #     return dbCore.installConfiguration(name, **value)

    def planet(self, name, value, **kwd):
        return # XXX :skip: use spatial api

        from stuphmud.server.zones import Planet # , core
        p = Planet(value['vnum'], value['name'], value['object'])
        for c in value.get('continents', []):
            p.newContinent(c['vnum'], c['name'], c['object'])

        # p._enterSystem(mud.zones.core)
        return p

    def eqSet(self, name, value, **kwd):
        return # XXX :skip: Use native-supported constraint for item.

        if isinstance(value, dict):
            return EqSet(value)

    def auctionItem(self, name, value, **kwd):
        return # XXX :skip: Use native-supported constraint for item.

        item = runtime[runtime.StuphMUD.Auction].Item \
               (-1, value['vnum'], name, value['minlevel'], value['minbid'], 0,
                description = value.get('description', ''),
                payload = value.get('payload', ''))
        return item

    def auction(self, name, value, **kwd):
        return # AuctionList(iter(value.values()))

    # Returns a non-native-safe object.
    # from stuphmud.server.magic.structure import spell
    # spell = staticmethod(spell)

    def rst(self, name, value, **kwd):
        from docutils.core import publish_parts
        return vmCurrentTask().mapping(*publish_parts(value, writer_name = 'html').items())

    def quest(self, name, value, **kwd):
        # :security: internal load
        # return # todo: move into tool

        from ph.emulation.machine import vmCurrentTask
        try: task = vmCurrentTask()
        except AttributeError: return
        task.checkAccessSystem(['zones:autoquest'], 'create')

        from stuphmud.server.zones.specials.autoquest import loadQuest

        VALID_QUEST_TYPES = ['$builtin.ProtectedSenario']

        assert value['quest-type'] in VALID_QUEST_TYPES
        return loadQuest(value, source = kwd.get('document', []) + [name])

    def value(self, name, value, **kwd):
        return value # identity

    # def synthetic(self, name, value, **kwd):
    #     return Synthetic(value)

    def url(self, name, value, **kwd):
        # :security: XXX :skip: unsafe load package
        raise NotImplementedError('Blocking unsafe operation')

        from phsite.network import url, importView, patterns, include_urlpatterns
        try:
            try: value = value['include']
            except KeyError:
                view = value['view'].split('.')
                viewModule = '.'.join(view[:-1])
                viewName = view[-1]

                view = importView(viewModule, viewName)
                try: view = view.view
                except AttributeError:
                    pass

                return url(value['pattern'], view)
            else:
                if isinstance(value, list):
                    return patterns('', value)

                # from stuphmud.server.runtime import LookupObject
                from stuphos.runtime.architecture import LookupObject

                include = LookupObject(value['package']).urlpatterns
                return include_urlpatterns(value['pattern'],
                                           include)

        except Exception as e:
            return e

        '''
        patterns:
          - (stuph$url):
            pattern: '^/html/format$'
            view: person.services.web.views.format_html
          - (stuph$url):
            include:
              pattern: '^game/'
              package: web.stuph.embedded.urls
          - (stuph$url):
            include:
            - (stuph$url):
              pattern: '^accounts/profile'
              view: web.stuph.accounts.profile
        '''

    def library(self, name, value, **kwd):
        # XXX :skip: This introduces a lowlevel object that has no memory management.
        raise NotImplementedError('Blocking unsafe operation')

        return LibraryCore(value.getSection('LibraryCore'),
                           LibraryCore.Node)

    class factory(Object, object):
        '''
        my/application:
            interfaces/interface::
                object($submapping):
                    classes:
                        object: my/components/object/kernel

                    document::
                        component($object): true


            documents/usage::
                structure('my/application/interface').object.component

                '''

        def __new__(self, name, value, **kwd):
            raise NotImplementedError

            core = runtime[runtime.Agent.System]
            if not core:
                raise NotImplementedError('%s not installed' % runtime.Agent.System)

            try: classes = value['classes']
            except NameError:
                classes = value
                document = None
            else:
                document = value['document']

            # Todo: merge parent-document 'value' structure into sub-document result object?

            f = object.__new__(self, core, name, classes, **kwd)
            f.__init__(core, name, classes, **kwd)

            if document is None:
                return f

            # Load sub-document.
            return f(document, **kwd) # kwd env?


        def __init__(self, core, name, classes, **kwd):
            self._classes = dict((n, self._lookupSubmapping(core, v))
                                 for (n, v) in classes.items())

        def _lookupSubmapping(self, core, n):
            s = n.split('/')

            for i in range(len(s), -1, -1):
                n = s[:i]

                try: n = core.lookup(*n) # XXX :skip: won't the Node.Tool just dereference its scope..?
                except KeyError:
                    continue

                if isinstance(n, core.Node.Tool):
                    n = n.scope

                    for o in s[i:]:
                        n = getattr(n, o) # todo: catch AttributeError and restart library search?


                    # An object was found, now decide what to do with it.

                    # if isinstance(n, Submapping):
                    #   return n


                    # SECURITY NOTE:  Because structures are intended to be loaded from the
                    # virtual machine, they are restricted to only loaded native tool library
                    # paths, which should only be producing object encapsulations.
                    #
                    # Additionally, native tool structural objects must be loaded from the
                    # tool's "_Factory" object, because structural item building methods do
                    # not take frame parameters.  Instead, the factory must detect the vm's
                    # task context instance if it needs to do frame-dependent actions.

                    return n._Factory


                if isinstance(n, core.Node.Module):
                    return self._activity(self, core, n, s)


        @property
        def _machine(self):
            from world import heartbeat as vm
            return vm
            return runtime[runtime.System.Engine]

        def __call__(self, source, **env):
            from stuphos.language.document.interface import load

            def coprocess():
                # XXX :skip: object-load/instantiation order is arbitrary!
                return load(source, self._classes, '', **env)

            try: task = self._machine.taskObject # contextObject.task
            except AttributeError:
                return coprocess()
            else:
                # a parallel document-loading routine object that submaps to library activities
                # and when loading, evaluates the instantiations asynchronously

                # XXX :skip: it's not asynchronous, it's callAsynchronous, or some bull*.
                task.callAsynchronous(coprocess)


        class _activity:
            def __init__(self, submapping, core, node, segments):
                self._submapping = submapping
                self._core = core
                self._node = node
                self._segments = segments

            def __call__(self, name, value, **kwd):
                from stuphos.kernel import LibraryNode, Script, findCurrentUser
                from world import heartbeat as vm

                with vm.Loading(Script, environ = kwd, user = findCurrentUser()) as task:
                    lib = LibraryNode._WithCore(self._core, self._node, self._segments)
                    instance = lib.instantiate(arguments = dict(value = value))

                    @task.onComplete
                    def buildComplete():
                        # Hack the stack to assert an exact task return value.
                        task.stack[:] = [instance]


                    # Wait for the virtual task to complete, and return the
                    # object result inserted from the activity instantation.
                    # Todo: errors.
                    return task.returnValue


    submapping = factory

    def structure(self, name, value, **kwd):
        '''
        my/application:
            interfaces/interface::
                object($structure):
                    classes:
                        # The path is to a Native Tool with a Factory definition.
                        '': my/components/object/kernel

                    document::
                        # object is defined in the native tool factory.
                        component($object): true


            documents/usage::
                structure('my/application/interface').object.component


        '''

        # This can wrap a factory.
        raise NotImplementedError('Blocking unsafe operation')

        core = runtime[runtime.Agent.System]
        if core is not None:
            classes = value['classes']
            document = value['document']
            default = value.get('default', '') # 'stuph'

            if isinstance(classes, self.factory):
                classes = classes._classes
            else:
                def factory(path):
                    node = core[path]
                    if isinstance(node, core.Node.Module):
                        # Todo: invoke method (like call) within activity.
                        # Because this means raising a Continuation that a
                        # would require a rewrite of the document loading
                        # code, we can do it synchronously, waiting on
                        # invocations in the outer-frame but this must be
                        # done from a non-heartbeat thread!  So, move the
                        # document load into a pooled thread executor.
                        pass
                    elif isinstance(node, core.Node.Structure):
                        pass

                    elif isinstance(node, core.Node.Tool):
                        # XXX :skip: check permission.
                        return node.scope._Factory

                classes = dict((type, factory(path))
                                for (type, path) in classes)

            # from mud.lang.structure import Factory
            # classes['stuph'] = Factory

            from stuphos.language.document.interface import load
            return load(document, classes, default)


    class _MethodInterface(Subroutine._Interface):
        # As a Subroutine.Interface, this object is callable by the emulation
        # runtime by dereferencing the procedure.  This object generates new
        # subroutine instances on property dereference for individual frames.

        def __init__(self, module, name, **env):
            self._module = module
            self._name = name
            self._environ = env

        @property
        def _programmer(self):
            # Used by call instruction.
            return self._environ.get('programmer')

        @property
        def _subroutine(self):
            # debugOn()
            proc = self._module.getSubroutine(self._name)
            proc._setEnvironment(self._module._getEnvironment())
            return proc
        _procedure = _subroutine


        # XXX Should these exist?
        def _getEnvironment(self, *args, **kwd):
            proc = self._module.getSubroutine(self._name)
            return proc._getEnvironment(*args, **kwd)

        def setEnvironment(self, *args, **kwd):
            proc = self._module.getSubroutine(self._name)
            return proc.setEnvironment(*args, **kwd)


        @property
        def _activation(self):
            from ph.emulation.operation.application import Invocation
            proc = self._module.getSubroutine(self._name)
            # debugOn()
            return Invocation(proc.main_program, proc.name, proc.start_position)

        def __repr__(self):
            return f'<method$interface {repr(self._name)}>'


    def method(self, name, value, **kwd):
        # Not really sure what the point of this is, to be part of
        # a synthetic (structural) class.  It could be wrapped by
        # something to mark it and get passed to the class constructor,
        # but, a method definition really has no use alone.
        if isinstance(value, dict):
            '''
            x(method):
                code::
                    return container.x._environ['content']

                content::

            '''

            methodValue = value
            value = value['code']
        else:
            methodValue = dict()

        module = buildMethodFromStructure(name, value, **kwd)

        # print('[structure.method]')
        # print(indent(module))

        from stuphos.kernel import Girl, FastLocals, GrammaticalError
        from stuphos.language.document.interface import getContextEnvironment

        try: module = Girl(Girl.Module, module, types = \
            getContextEnvironment('types', default = None))

        except GrammaticalError as e:
            raise ValueError(module) from e

        env = dict(container = containerAccessor(kwd['container']))

        try: task = vmCurrentTask()
        except AttributeError:
            task = None

        else:
            env = FastLocals(task.memory, env, module._variableNames,
                             module._variableIndices)
            # print(f'[method$locals] {id(env)}')

        # print(f'[method def] {", ".join(kwd.keys())}')

        try: path = getContextEnvironment('document')
        except KeyError: pass
        else:
            module._setAttribute('_interface_path', '%s/%s' % ('/'.join(path), name))

            if task:
                env['path$'] = task.sequence(path + [name])

        module.setEnvironment(env)

        # def getEnvironmentVariable(name):
        #     return getContextEnvironment('document')[name]

        # module.environ['getenv'] = _safe_native(getEnvironmentVariable)

        # module.setEnvironment(vmCurrentTask().environ)

        # Get the owner of the (agent system) interface, if it exists.
        # from stuphos.language.document.structural import Context
        # progr = Context['loader'].environ.get('programmer')

        methodValue['programmer'] = getContextEnvironment('programmer', default = None)

        return self._MethodInterface(module, name, **methodValue)

    procedure = subroutine = method


    # Currently fails.  Also, returns a non-native-safe object.
    # from stuphos.language.shortate import shortate
    # shortate = staticmethod(shortate)


    def command(self, name, value, **kwd):
        # XXX :skip: Provide a memory-sensitive implementation of actionable.command[.verb]
        raise NotImplementedError('Blocking unsafe operation')

        # Requires implementation.
        from spatial.architecture import actionable

        if isinstance(value, str):
            value = dict(implementation = value)

        parse = value.get('parse')

        if isinstance(parse, str):
            parse = buildMethodFromStructure(parse, **kwd)

        impl = value['implementation']

        if isinstance(impl, str):
            impl = buildMethodFromStructure(impl, **kwd)

        # if isinstance(parse, subroutine):
        #   parse = compileSubroutine(parse)
        # if isinstance(impl, subroutine):
        #   impl = compileSubroutine(impl)


        ns = dict(__call__ = impl)
        if parse is not None:
            ns['parseArgs'] = parse


        verbClass = newClassType('implementation', (actionable.command.verb,), ns)
        ns = dict(name = name, implementation = verbClass)

        return newClassType('%sCommand' % name, (actionable.command,), ns)


identifier_pattern = re.compile('[a-zA-Z$_][a-zA-Z$_0-9]*').match
def isValidIdentifier(name):
    return identifier_pattern(name) is not None

def buildMethodFromStructure(name, value, **kwd):
    if not isValidIdentifier(name):
        # If it's coming from structure, validate.
        raise NameError(name)

    if isinstance(value, str):
        parameters = []
        code = value
    else:
        parameters = value['parameters']
        code = value['code']

    parameters = ', '.join(parameters)
    return buildMethod(name, parameters, code)

def buildMethod(name, parameters, code = 'pass'):
    # from ph.lang.layer import grammar
    # ast = grammar.Grammar.AST

    # suite = ast.Suite([])
    # module = ast.Suite([ast.FunctionDefinition(name, parameters, suite)])

    code = 'locals().update(keywords$())\n' + code

    return 'def %s(%s):\n%s\n' % (name, parameters, indent(code))


@staticmethod
def htmlScript(name, value, **kwd):
    # XXX :skip: value must be interned here, meaning a memory mapping or sequence,
    # otherwise, structural.Items won't be constrained by mental.objects code.
    raise NotImplementedError('Blocking unsafe operation')

    return HtmlView._ScriptElement(value)

#@staticmethod
def syntheticClass(self, name, value, **kwd):
    '''
    code.value.object.create()() <- code:
        object(class)::
            def call$():
                pass

    '''

    from stuphos.kernel import Girl, SyntheticClass

    # todo: $classInit$ trigger method for initializing
    # environment.  Also, pass kwd/document container
    # for connecting class impl to structure.

    # Todo: use SyntheticClass._BuildProgram/FromStructure
    # This however utilizes SyntheticProgram, which is different
    # from the source-composing strategy happening here.
    #
    # The FromStructure strategy is lower level, although doesn't
    # compose buildMethodFromStructure values and doesn't allow
    # environment.

    attributes = []

    if isinstance(value, str):
        init = value
    else:
        def checkMember(n, m):
            if isinstance(m, (dict, str)):
                return True

            # debugOn()

            attributes.append((n, m))
            return False

        methods = ((n, m) for (n, m) in value.items()
                   if checkMember(n, m))

        init = nls(buildMethodFromStructure(defn, m, **kwd) for
                   (defn, m) in methods)

    types = getContextEnvironment('types', default = None)

    synth = SyntheticClass \
            (name,
             Girl(Girl.Module, init, types = types),
             kwd.get('container'))

    # for (n, m) in attributes:
    #     # todo: is this right?  Shouldn't it be set in environ?
    #     synth._setAttribute(n, m)

    synth._subroutines = dict(attributes)

    # Note: classInit must be called by client.
    return synth


setattr(Factory, 'html.script', htmlScript)
setattr(Factory, 'class', syntheticClass)
Factory.object = Factory.formula = getattr(Factory, 'class')

from stuphos.kernel import GirlCore
class LibraryCore(GirlCore):
    def loadEntities(self, cfg, nodeClass):
        pass
    def saveNode(self, node, recurse = False):
        pass
    def destroyNode(self, node):
        pass


class SystemFactory(Submapping):
    def tool(self, path, sourceCode, **kwd):
        segments = path.split('/')
        assert isinstance(sourceCode, str)
        core = runtime[runtime.Agent.System]
        assert core is not None
        scope = Core.Python().module(path, sourceCode,
                                     container = kwd['container'])
        return core.addPythonTool(segments, scope) # Q: dictOf()?

    # def lock(self, name, value, **kwd):
    #   from threading import Lock
    #   return Lock()


class HTMLFactory(Submapping):
    # XXX __str__ continuation not supported.
    class _iframe(writeprotected):
        def __init__(self, name, value, **kwd):
            if isinstance(value, dict):
                src = value['source']

            elif isinstance(value, str):
                src = value
            else:
                raise ValueError(value)

            self._src = src

        def buildSource(self, src, attrs = ''):
            # todo: escapeXmlContent(src)
            return f'<iframe{attrs and " " or ""}{attrs} src="data:text/html,{src}"></iframe>'

        def build(self):
            src = self._src
            if isinstance(src, str):
                return self.buildSource(src)

            # elif callable(src):
            else:
                new = vmCurrentTask().swapFrameCall(resolve_procedure(src))

                @new.onComplete
                def run(frame, *error, **kwd):
                    stack = frame.task.stack
                    stack.push(self.buildSource(stack.pop()[0]))

                raise new.outer

        __str__ = __call__ = build


        # from stuphos.runtime.architecture.api import _safe_native
        # return _safe_native(build)


from stuphos.language.document.interface import getContextEnvironment
