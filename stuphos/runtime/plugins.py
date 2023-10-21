# Plugin Component Services Manager.
# ---
# Purpose: configuring optional (external to core) components generically
#
from .facilities import Facility, LoadFacility
from .registry import getObject
from . import LookupObject as LookupPluginAction
from stuphos.management.config import loadConfig

from stuphos.etc.tools.logs import logException

from os.path import abspath, exists as fileExists
import traceback

import re
COMPONENT_PATTERN = re.compile('^component(?:\.\d+)?$')
GROUP_PATTERN = re.compile('component-group(?:\.\d+)?$')
FACILITY_PATTERN = re.compile('facility(?:\..+)?$')

PKGDEP_PATTERN = re.compile('package(?:\.\d+)?$')
SVCDEP_PATTERN = re.compile('service(?:\.\d+)?$')

import sys
if sys.platform == 'win32':
    PATH_PATTERN = re.compile('^windows-path(?:\.\d+)?$')
elif sys.platform == 'cygwin':
    PATH_PATTERN = re.compile('^path(?:\.\d+)?$')
else:
    PATH_PATTERN = re.compile('^path(?:\.\d+)?$')

class PluginManager(Facility):
    NAME = 'Plugin::Manager'
    CACHE_NAME = 'Plugin::Manager::Cache'

    def loadBootPlugins(self):
        pluginCache = getObject(self.CACHE_NAME, create = dict)
        thesePlugins = []
        facilities = []

        from stuphos import getSection
        cfg = getSection('Services')
        for opt in cfg.options():
            if COMPONENT_PATTERN.match(opt) is not None:
                plugin = self.loadPluginFromConfig(cfg[opt])
                if plugin is not None:
                    if plugin.name not in pluginCache:
                        pluginCache[plugin.name] = plugin
                        thesePlugins.append(plugin)

            elif GROUP_PATTERN.match(opt) is not None:
                # todo: load a group of services/plugins from file/directory
                pass

            elif FACILITY_PATTERN.match(opt) is not None:
                facilities.append((opt, cfg[opt]))

        # Load facilities from command-line.
        facilities.extend(self.parseServicesCmdline(core.cmdln['options'].services))

        # from ph.interpreter.mental.library.theta import psOpGameVsz
        # print(f'[vsz] {psOpGameVsz()}')

        for (n, f) in sorted(dict(facilities).items(),
                             key = lambda a_b: a_b[0]):

            try: LoadFacility(f)
            except:
                print('Loading [%s]: %s' % (n, f))
                logException(traceback = True)

            # print(f'[vsz] {psOpGameVsz()}')

        for plugin in thesePlugins:
            try: plugin.boot()
            except: traceback.print_exc() # XXX warn :skip:

    __init__ = loadBootPlugins

    def loadPluginFromConfig(self, config_file):
        config_file = abspath(config_file)
        if fileExists(config_file):
            try: return Plugin.LoadFromConfig(config_file)
            except: traceback.print_exc()

    def parseServicesCmdline(self, cmdline):
        for (n, line) in enumerate(cmdline):
            i = line.find('=')
            if i >= 0:
                yield (line[:i], line[i+1:])
            else:
                yield (n, line)


class Plugin:
    class Type(str):
        def __repr__(self):
            return self

    UnknownType = Type('unknown')
    PythonPluginType = Type('python-service')

    @classmethod
    def LoadFromConfig(self, config_file):
        cfg = loadConfig(config_file)
        return self(config_file, cfg)

    MODE_BOOT = 'boot'
    MODE_LOAD = 'load'
    MODE_UNLOAD = 'unload'
    MODE_SHUTDOWN = 'shutdown'

    LIFECYCLE_SECTIONS = [MODE_BOOT, MODE_LOAD, MODE_UNLOAD, MODE_SHUTDOWN]

    def __init__(self, config_file, cfg):
        self.config_file = config_file
        self.mode = None

        # XXX These don't validation as non-None! :skip:
        module = cfg['Module']
        self.name = module['name']
        self.type = module.get('type', self.UnknownType)
        self.package = module['package']
        self.added_paths = []
        self.paths = self.loadPathsFromConfig(module)
        self.lifecycle = {}

        self.dependencies = self.loadDependenciesFromConfig(cfg['Dependencies'])

        for section in cfg.sections():
            mode = section.lower()
            if mode in self.LIFECYCLE_SECTIONS:
                self.lifecycle[mode] = self.loadLifecycle(cfg[section])

    def __repr__(self):
        return '<%s: %s (%s) [%s] %s>' % (self.__class__.__name__, self.name,
                                          self.type, self.package, self.mode)

    class Lifecycle:
        ACTION_NAMES = ['method', 'action', 'object']
        def __init__(self, cfg):
            for name in self.ACTION_NAMES:
                try:
                    value = cfg[name]
                    if value is None:
                        continue

                    self.action = value
                    self.name = name
                    break
                except KeyError:
                    pass
            else:
                raise ValueError('No action name specified in the lifecycle! %s' % self.ACTION_NAMES)

        def __repr__(self):
            return '<%s: action = %s>' % (self.__class__.__name__, self.action)

    loadLifecycle = Lifecycle

    def loadPathsFromConfig(self, module):
        path_collection = []
        for opt in module.options():
            if PATH_PATTERN.match(opt):
                path = module[opt]
                if path and path not in path_collection:
                    path_collection.append(path)

        return path_collection

    def loadPathsIntoSystem(self, these_paths):
        from sys import path as system_path
        added_paths = []
        for path in these_paths:
            path = abspath(path)
            if path not in system_path:
                added_paths.append(path)
                system_path.append(path)

        # For future unload..?
        self.added_paths = added_paths

    def loadDependenciesFromConfig(self, cfg):
        pkgdeps = []
        svcdeps = []

        for opt in cfg.options():
            if PKGDEP_PATTERN.match(opt):
                pkg = cfg.get(opt)
                if pkg not in pkgdeps:
                    pkgdeps.append(pkg)

            elif SVCDEP_PATTERN.match(opt):
               svc = cfg.get(opt)
               if svc not in svcdeps:
                   svcdeps.append(svcdeps)

        deps = []
        for pkg in pkgdeps:
            deps.append(self.PackageDependency(pkg))
        for svc in svcdeps:
            deps.append(self.ServiceDependency(svc))

        return deps

    class PackageDependency:
        def __init__(self, package_name):
            self.package_name = package_name
        def load(self):
            # is this sufficient for full import?
            try: return __import__(self.package_name)
            except ImportError as e:
                from stuphos.system.api import syslog
                syslog('PACKAGE-DEPENDENCY: %s: %s' % (self.package_name, e))
                return False

            return True

    class ServiceDependency:
        def __init__(self, service_name):
            self.service_name = service_name
        def load(self):
            from stuphos.system.api import syslog
            e = NotImplementedError('No way to load service dependencies, yet!')
            syslog('SERVICE-DEPENDENCY: %s: %s' % (self.service_name, e))
            return True

    def loadDependenciesIntoSystem(self, dependencies):
        for dep in dependencies:
            try:
                if not dep.load():
                    return False

            except:
                traceback.print_exc() # todo: log
                return False

        return True

    def lookupAction(self, name):
        if self.type == self.PythonPluginType:
            return LookupPluginAction('%s.%s' % (self.package, name))

        raise TypeError(self.type)

    # Lifecycles.
    def changeMode(self, mode):
        self.mode = mode

        try: action = self.lifecycle[mode].action
        except KeyError: pass
        else:
            action = self.lookupAction(action)
            if callable(action):
                try: action(self, mode)
                except: traceback.print_exc() # XXX change into error mode :skip:

    def boot(self):
        self.loadPathsIntoSystem(self.paths)
        if self.loadDependenciesIntoSystem(self.dependencies):
            self.changeMode(self.MODE_BOOT)
        else:
            # Rollback paths load-in??
            pass

def installPlugins():
    # This is called during mud.bootStart, but eventually I want to be
    # able to hot-plug plugin components, too.
    PluginManager.manage()
    PluginManager.get(create = True)
