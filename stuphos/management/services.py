# Automatic service configuration for zone modules.
#
from stuphos.runtime.registry import getObject as getRegistryObject, RegistryNotInstalled
from ..etc import isYesValue, capitalize, getSystemException, logException

from .config import getStandardPath, getParentPath, loadConfig
from .config import getStandardPath, getParentPath, loadConfig

def getEnablingSection(name):
    # A shorter, sweeter version.
    from stuphos import getSection
    from ..etc import isYesValue

    cfg = getSection(name)
    def isEnabled(option):
        return isYesValue(cfg.get(option))

    return isEnabled

class AutoServices:
    CONFIG_SECTION_NAME = 'Services'

    @classmethod
    def ParentPath(self, base, *parts):
        return self.JoinPath(getParentPath(base), *parts)

    @classmethod
    def JoinPath(self, *parts):
        return getStandardPath(*parts)

    def __init__(self, setup_deferred = False):
        self.reset()

        # Do the actual object setup during load because maybe the
        # (configuration) objects aren't around yet.
        self.setup_deferred = setup_deferred
        if not setup_deferred:
            self.setup()

    def setup(self):
        try:
            configObj = getRegistryObject(self.CONFIG_OBJECT_NAME,
                                          create = lambda:loadConfig \
                                          (self.CONFIG_FILE))

            self.section = configObj.getSection(self.CONFIG_SECTION_NAME)
            self.configObj = configObj
        except RegistryNotInstalled:
            self.section = None

    def getConfigObject(self):
        return self.configObj
    def getConfigSection(self):
        return self.section
    def getConfig(self, name, section = None):
        return self.getConfigObject().get(name, section = self.CONFIG_OBJECT_NAME
                                          if section is None else section)

    def reloadConfig(self):
        # todo: use method-based api..
        del runtime[self.CONFIG_OBJECT_NAME]
        self.setup()

    def reset(self):
        self.loaded = set()

    class ServiceConf:
        def __init__(self, name, value):
            self.name = name
            self.value = value

    def getServiceLoaderName(self, name):
        return 'load' + ''.join(capitalize(part) for part in name.split('-'))

    def findServiceLoader(self, conf):
        methodName = self.getServiceLoaderName(conf.name)
        return getattr(self, methodName, None)

    def iterateConfServices(self):
        if self.section:
            for opt in self.section.options():
                conf = self.ServiceConf(opt, self.section.get(opt))
                function = self.findServiceLoader(conf)

                if callable(function):
                    yield (conf, function)

    def shouldLoad(self, conf):
        try:
            if conf.name not in self.loaded:
                return isYesValue(conf.value)
        finally:
            self.loaded.add(conf.name)

    def __call__(self):
        if self.setup_deferred:
            self.setup()

        for (conf, load) in self.iterateConfServices():
            if self.shouldLoad(conf):
                # debugOn()
                try: load(conf)
                except SyntaxError as e:
                    print('There was a syntax error in module configuration for service:', conf.name)
                    #'args', 'filename', 'lineno', 'message', 'msg', 'offset', 'print_file_and_line', 'text']
                    print('   ', e.filename, '(%d:%d)' % (e.lineno, e.offset))
                except: self.error(*getSystemException())

        self.postOn(self.section)

    def error(self, etype, evalue, tb):
        # Non-fatal.
        logException(etype, evalue, tb, traceback = True)

    def postOn(self, cfg):
        # Called after loading services.  Customize post-load.
        pass
