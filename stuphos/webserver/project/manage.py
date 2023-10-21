#!/usr/bin/env python
from django.core.management import execute_manager
import imp
try:
    # Also, manually must construct registry because fraun.services.web/subdaemon import relies on it
    from stuphos.runtime.registry import getRegistry
    getRegistry(create = True)

    # Um, find_module apparently is more strict.
    # import pdb; pdb.set_trace()
    # imp.find_module('settings') # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

from . import settings

if __name__ == "__main__":
    execute_manager(settings)

    # #!/usr/bin/env python
    # import os
    # import sys

    # if __name__ == "__main__":
    #     os.environ.setdefault("DJANGO_SETTINGS_MODULE", "b.settings")
    #     try:
    #         from django.core.management import execute_from_command_line
    #     except ImportError:
    #         # The above import may fail for some other reason. Ensure that the
    #         # issue is really that Django is missing to avoid masking other
    #         # exceptions on Python 2.
    #         try:
    #             import django
    #         except ImportError:
    #             raise ImportError(
    #                 "Couldn't import Django. Are you sure it's installed and "
    #                 "available on your PYTHONPATH environment variable? Did you "
    #                 "forget to activate a virtual environment?"
    #             )
    #         raise
    #     execute_from_command_line(sys.argv)
