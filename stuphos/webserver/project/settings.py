# Django settings for stuph project.

try:
    from stuphos import getConfig, getSection
    from stuphos.etc import isYesValue
except ImportError as e:
    print(f'[webserver.settings] {e}') # ok..
    DEBUG = True

djangoServiceConf = getSection('DjangoService')

def srvcConfig(name):
    return [_f for _f in (djangoServiceConf.get(name) or '').split('\n') if _f]

SHOW_DEBUG_PAGE = djangoServiceConf.get('show-debug-page')
DEBUG = SHOW_DEBUG_PAGE != 'admin' and isYesValue(SHOW_DEBUG_PAGE or 'no')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

from os.path import dirname, join as joinpath, realpath

WEB_PACKAGE_PATH = dirname(dirname(dirname(realpath(__file__)))) # stuphos/
PACKAGES_PATH = dirname(WEB_PACKAGE_PATH)

##    DATABASE_ENGINE = 'sqlite3'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
##    DATABASE_NAME = DB_PATH        # Or path to database file if using sqlite3.
##    DATABASE_USER = ''             # Not used with sqlite3.
##    DATABASE_PASSWORD = ''         # Not used with sqlite3.
##    DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
##    DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.
##
##    DATABASES = {
##        'default': {
##            'NAME': DB_PATH,
##            'ENGINE': 'django.db.backends.sqlite3',
##            'USER': '',
##            'PASSWORD': ''
##        }
##    }

##    DATABASE_ENGINE = 'postgresql_psycopg2'    # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
##    DATABASE_NAME = 'stuph'        # Or path to database file if using sqlite3.
##    DATABASE_USER = 'stuph'             # Not used with sqlite3.
##    DATABASE_PASSWORD = 'password'         # Not used with sqlite3.
##    DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
##    DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

#from person.services.data.pg import getDjangoDatabaseConfig
from stuphos.db.conf import initDjangoDatabaseConfig
#import pdb; pdb.set_trace()

#mud.reloadConfigFile('support/.mud-config.cfg')

database = djangoServiceConf.get('database') or 'primary'

DATABASES = {}

try: DATABASES['default'] = initDjangoDatabaseConfig(database)
except KeyError as e:
    print(f'[webserver.settings] {database}: {e}')

# In case default gets overwritten, we always have access to the conf here.
try: DATABASES['stuphos'] = DATABASES['default']
except KeyError: pass

# XXX hardcoded namespace:
try: DATABASES['stuphosweb'] = initDjangoDatabaseConfig('sqlite')
except KeyError: pass


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY_PATH = djangoServiceConf.get('secret-key-path', 'etc/django.secret.key')
try: SECRET_KEY = open(SECRET_KEY_PATH).read().strip()
except IOError as e:
    print('ERROR: Using default django site secret key.', e)
    SECRET_KEY = 'lla4r9dp9g8x)q4kuod-biqz0+=&-7&p(&p5$(1a9igwcr%+0%'


CMS_PROJECT_NAME = 'cms' # Name of directory in packages/web/
CMS_PROJECT_PATH = WEB_PACKAGE_PATH
CMS_PROJECT_PATH = joinpath(CMS_PROJECT_PATH, CMS_PROJECT_NAME)

CMS_MEDIA_ROOT = joinpath(CMS_PROJECT_PATH, 'media')
CMS_MEDIA_URL = '/cms/media/'

gettext = (lambda text: text)
CMS_TEMPLATES = (
    # ('page_base.html', gettext('StuphMUD Site Default')),
    # ('cms_base.html',  gettext('StuphCMS Base Page')),
)

LOGIN_URL = '/accounts/login'
LOGIN_REDIRECT_URL = '/' # menu.  "after login where to redirect (?)"

STATIC_ROOT = 'web/cms/media' # in lib: directory with cms -> package static dir
STATIC_URL = '/media/'

SEKIZAI_IGNORE_VALIDATION = True
SEKIZAI_VARNAME = 'my_sekizai_VarName'


DEFAULT_VMTEMPLATES = 'vm/ph/interpreter/mental/library/templates'

# Relative to stuphos package python path.  Section is not DjangoService.
VMTEMPLATES = getConfig('vm-templates', 'AgentSystem') or DEFAULT_VMTEMPLATES

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [joinpath(WEB_PACKAGE_PATH, 'server/templates'), # stuphos/server/templates
                 joinpath(PACKAGES_PATH, 'implementations/person/services/web/templates'),
                 joinpath(PACKAGES_PATH, VMTEMPLATES)] +

                srvcConfig('templates'),

        'APP_DIRS': False, # True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],

            'loaders': ['django.template.loaders.filesystem.Loader',
                        'django.template.loaders.app_directories.Loader',
                        ] + (['ph.interpreter.mental.library.loader.TemplateLoader']
                             if isYesValue(getConfig('virtual-templates', 'AgentSystem'))
                             else []),

            'builtins': [
                'phsite.network.templatetags.style',
                # 'phsite.network.templatetags.tools',
                # 'phsite.network.templatetags.world_lib',
            ]
        },
    },

    # {
    #     'BACKEND': 'person.features.girl.LibraryTemplates'
    # }
]

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
##    'django.template.loaders.filesystem.load_template_source',
##    'django.template.loaders.app_directories.load_template_source',
##    'web.stuph.embedded.entities.load_template_source',
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'web.stuph.embedded.entities',
#     'django.template.loaders.eggs.load_template_source',
)

# MIDDLEWARE_CLASSES
MIDDLEWARE = (
    ##    'django.middleware.common.CommonMiddleware',
    ##    'django.contrib.sessions.middleware.SessionMiddleware',
    ##    'django.contrib.auth.middleware.AuthenticationMiddleware',

#        'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # Does this work? -- It requires apps to be configured first: see embedded.service.py
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
#        'django.middleware.doc.XViewMiddleware',
        # 'django.middleware.csrf.CsrfViewMiddleware',
#        'cms.middleware.multilingual.MultilingualURLMiddleware',
#        'cms.middleware.page.CurrentPageMiddleware',
#        'cms.middleware.user.CurrentUserMiddleware',
#        'cms.middleware.toolbar.ToolbarMiddleware',
        # 'cms.middleware.media.PlaceholderMediaMiddleware',
        'django.middleware.cache.FetchFromCacheMiddleware',
)

if configurationTruth.DjangoService.log_all_requests:
    MIDDLEWARE += ('stuphos.webserver.LoggingMiddleware',)
if configurationTruth.DjangoService.multitenancy:
    MIDDLEWARE += ('stuphos.webserver.MultiTenancy',)
# if configurationTruth.DjangoService.csrf_exempt_middleware:
#     MIDDLEWARE += ('stuphos.webserver.CsrfExemptViewMiddleware',)


MULTITENANCY = {
}


_multitenancy = getSection('DjangoService:Multitenancy')
if _multitenancy is not None:
    for opt in _multitenancy.options():
        MULTITENANCY[opt] = _multitenancy[opt]


# XXX in application config.
# ROOT_URLCONF = 'stuphos.webserver.project.urls'

#import menus
#CMS_MENUS_PATH = dirname(menus.__file__)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    joinpath(CMS_PROJECT_PATH, 'templates'),
    joinpath(CMS_PROJECT_PATH, 'site_templates'),
    # joinpath(CMS_MENUS_PATH, 'templates'),
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
#    'django.core.context_processors.auth',
#    'django.core.context_processors.i18n',
#    'django.core.context_processors.request',
#    'django.core.context_processors.media',
#    'cms.context_processors.media',
#    'sekizai.context_processors.sekizai',
)

AUTHENTICATION_BACKENDS = ['django.contrib.auth.backends.ModelBackend',
                            # XXX
                            # 'phsite.network.accounts.KeyfileBackend'
                            ]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
#    'django.contrib.databrowse',
    # 'django.contrib.admindocs',
    # 'django.contrib.admin',

    'django.contrib.messages',
#        'cms',
#        'cms.plugins.text',
        # 'cms.plugins.picture',
#        'cms.plugins.link',
#        'cms.plugins.file',
#        'cms.plugins.snippet',
#        'cms.plugins.googlemap',
#        'mptt',
        # 'publisher',
#        'menus',

#    'sekizai',

    'phsite.network',
    # 'taskqueues',
) + tuple(srvcConfig('webapps'))

# APPEND_SLASH = True

hostsConf = srvcConfig('hosts')

ALLOWED_HOSTS = (
    #u'*',
    'localhost',
) + tuple(hostsConf)


CSRF_TRUSTED_ORIGINS = \
    [
        # 'https://localhost:2180'
    ] + srvcConfig('csrf-trusted-origins')


# debugOn()
uploadMaxMemorySize = djangoServiceConf.get('upload-max-memory-size')
if uploadMaxMemorySize:
    DATA_UPLOAD_MAX_MEMORY_SIZE = int(uploadMaxMemorySize)


# Default settings for 'identities/{name}'.structure.preferences
defaultGlobalConfig_identities = dict()

CSRF_EXEMPT_PATHS = [
    'script/execute',
]
