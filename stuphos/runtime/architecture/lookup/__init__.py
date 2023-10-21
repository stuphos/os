'Package designed for isolating the import call so that no relative modules block others in the toplevel.'

def LookupObject(name, raise_import_errors = False):
    'A clever routine that can import an object from a system module from any attribute depth.'
    # XXX This doesn't import modules that aren't imported by their parent package initialization code.  (Yes it does :skip:)
    parts = name.split('.')

    moduleObject = None
    module = None
    n = len(parts)
    x = 0

    importError = None

    for x in range(n, 0, -1):
        name = '.'.join(parts[:x])

        try: moduleObject = __import__(name, globals(), locals())
        except (ImportError, ModuleNotFoundError):
            from sys import exc_info
            importError = exc_info()
        else:
            break

    # while x < n:
    #     name = '.'.join(parts[:x+1])
    #     moduleObject = module

    #     # Try to find the module that contains the object.
    #     try: module = __import__(name, globals(), locals(), [''])
    #     except ImportError:
    #         from sys import exc_info
    #         importError = exc_info()
    #         break
    #     else:
    #         # Q: Will this break the following code?  It needs to be here so that a full
    #         # subpackage name can be looked up, when no sub-object is needed.  Because,
    #         # when x < n, the (module)Object is returned and this setlocal phase will be
    #         # skipped.
    #         moduleObject = module

    #     x += 1

    # No top-level module could be imported.
    if moduleObject is None:
        if importError is None:
            raise AssertionError

        (etype, value, tb) = importError
        raise value.with_traceback(tb)

    object = moduleObject
    x = 1

    while x < n:
        # Now look for the object value in the module.

        # If an attribute can't be found -- this is where we raise the original import-error?
        #
        # This is a good idea: so that LookupObject is consistantly raising ImportError (since
        # that's basically what its function is -- an import-from).
        #
        ##    if raise_import_errors:
        ##        module = __import__(name, globals(), locals(), [''])

        try: object = getattr(object, parts[x])
        except AttributeError as e:
            if importError is None:
                raise e

            (c, e, t) = importError
            raise c(e).with_traceback(t)

        x += 1

    # todo: raise prior ImportError if it existed because of a problem in the loaded module.
    return object
