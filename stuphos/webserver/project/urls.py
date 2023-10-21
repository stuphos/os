#from django.conf.urls.defaults import *
from django.conf.urls import *


# class urlApplicationConfiguration(object):
#     'This organizes all of the application-specific components.'

#     def __new__(self, *args, **kwd):
#         # This behavior may present problems for some derivations.
#         i = object.__new__(self)
#         i.__init__(*args, **kwd)
#         return i()


#     # This object provides a way to merge a urlconf for a dynamic install.
#     def __init__(self):
#         self.patterns = patterns('')
#         self.installer = self._installer(self)

#     class _installer(object):
#         def __init__(self, config):
#             self.config = config

#         def __getattr__(self, name):
#             try: return object.__getattribute__(self, name)
#             except AttributeError:
#                 return self.mergeInstaller(self, name)

#         class mergeInstaller:
#             def __init__(self, installer, name):
#                 self.installer = installer
#                 self.name = name

#             def __call__(self, *args, **kwd):
#                 return self.installer.config.installComponent(self.name, *args, **kwd)


#     def __call__(self, *args, **kwd):
#         self.load(self.installer, *args, **kwd)

#         return self.patterns

#     def interpretMerge(self, result):
#         if result is not None:
#             if isinstance(result, self.configuration):
#                 result = result()

#             if result is not None:
#                 self.patterns += result

#         return self
#     __lshift__ = interpretMerge

#     def installComponent(self, name, *args, **kwd):
#         proc = getattr(self, name)
#         result = proc(self, *args, **kwd)

#         return self.interpretMerge(result)

#     @property
#     def scopes(self):
#         def scopeName(cls):
#             try: name = cls.name
#             except AttributeError:
#                 name = None

#             if not name:
#                 name = cls.__name__

#                 for ending in ['ConfigurationOptional', 'Configuration']:
#                     if name.endswith(ending):
#                         name = name[:-len(ending)]
#                         break

#             return name


#         def scopeClasses():
#             # todo: provide more scopes for grouping them by name.
#             for name in dir(self):
#                 try: cls = getattr(self, name)
#                 except AttributeError: pass
#                 else:
#                     if isinstance(cls, ClassType):
#                         if issubclass(cls, self.configuration):
#                             yield cls


#         for cls in scopeClasses():
#             yield (scopeName(cls), cls)


#     def loadConfiguration(self, config):
#         scopes = dict(self.scopes)

#         try: pattern = config.pop('url')
#         except AttributeError: pass
#         else:
#             view = config.pop('view')

#             s = config.pop('scope')
#             cls = scopes.get(s, self.configuration)

#             if isinstance(view, basestring):
#                 view = view.split('.')

#             o = cls

#             for n in view:
#                 o = getattr(o, n)

#             return url(pattern, o, **config)


#     class configuration:
#         def __init__(self, mainConfig):
#             self.mainConfig = mainConfig

#         scope = ''
#         name = ''

#         def __call__(self):
#             p = patterns(self.scope)
#             p += list(self.entries)

#             return p

#         @property
#         def entries(self):
#             for a in self:
#                 if isinstance(a, tuple):
#                     yield url(*a)
#                 else:
#                     yield a

#         @property
#         def modules(self):
#             return self.mainConfig.modules


# component = urlApplicationConfiguration.configuration


# debugOn()
try:
	from phsite.network import embedded
	from phsite.network.urls import urlImport as urlApplicationImport

except ImportError:
	from stuphos import logException
	logException(traceback = True)
	embedded = None

# import embedded

# urlpatterns = patterns('',
#     # Apache -- do this if !embedded.installed
#     # (r'^stuph',      include('stuphos.web.application.urls')),

#     # Development/Embedded Server -- Default deferrence.
#     # XXX first of all, why would this have ever worked, that is was previously named wrong... :skip:
#     # Second of all, we are not using the formal django include operation, we're just merging
#     # the urlconf objects using our application urls configuration, as seen later.
#     # (r'^',        include('phsite.network.urls')),
# )

urlpatterns = urlApplicationImport()


# Admin -- !embedded.installed
##    from django.contrib import admin
##    admin.autodiscover()
##
##    from os.path import dirname, join as joinpath
##    ADMIN_MEDIA_DIR = joinpath(dirname(admin.__file__), 'static')
##    ADMIN_MEDIA_DIR = joinpath(ADMIN_MEDIA_DIR, 'admin')
##
##    urlpatterns += patterns('',
##        (r'^admin/doc/',   include('django.contrib.admindocs.urls')),
##        (r'^media/admin/(?P<path>.*)$',
##                           'django.views.static.serve',
##                           {'document_root': ADMIN_MEDIA_DIR}),
##
##        # (r'^admin/(.*)',   admin.site.root)
##        # Django CMS requires this (old form) for template namespaces:
##        (r'^admin/', include(admin.site.urls)), 
##    )

# Databrowse.
##    from django.contrib import databrowse
##
##    databrowse_site_root = databrowse.site.root

# from django.contrib.auth.decorators import login_required
# databrowse_site_root = login_required(databrowse_site_root)

##    urlpatterns += patterns('', (r'^databrowse/(.*)', databrowse_site_root))
##
##    from web.stuph import initializeSite
##    initializeSite(admin, databrowse)

# CMS
##    if not embedded.installed or True: # todo: remove or True
##        from django.conf import settings
##        urlpatterns += patterns('',
##            url(r'^cms/media/(?P<path>.*)$', 'django.views.static.serve',
##                {'document_root': settings.CMS_MEDIA_ROOT, 'show_indexes': True}),
##            url(r'^cms/', include('cms.urls'))
##        )

# Castalian.
# urlpatterns += patterns('', url(r'^cas', include('castalian')))
