'''
stuphos/runtime/parallel_subinterpreter.py::
    """
    # eventConsume = 'kernel/moduleOf'('stuphos.runtime.parallel_subinterpreter')

    return 'kernel/moduleOf'('stuphos.runtime.parallel_subinterpreter.eventConsume')

    """

    from stuphos.runtime.module \
        import pathImportFromNS


    pathImportFromNS \
        ('notes/code/subinterpreter-channel-1.ela',
         locals(), 'subinterpreterCall', 'channelsOf',
         'channelCall', 'dispatchCall', eventConsume
            = '__doc__')

            '''

def moduleImportFrom(module, *names, **kwd):
    return (getattr(module, n) for n in names)

def moduleImportFromNS(module, ns, *names, **kwd):
    for n in names:
        setattr(module, n, ns[n])
    for (n, v) in kwd.items():
        setattr(module, n, ns[v])

def pathImportFromNSRelative(path, ns, *names, **kwd):
    from os.path import dirname, join as joinpath
    return pathImportFromNS(kwd.pop('__import_path__') or
        joinpath(dirname(ns['__file__']), path),
        ns, *names, **kwd)

def pathImportFromNS(path, ns, *names, **kwd):
    return moduleImportFromNS(pathImport
        ('', path = path), ns, *names, **kwd)

def pathImportCallOneFrom(path, attr, *args, **kwd):
    return pathImportOneFrom \
        (path, attr, **kwd) \
            (*args, **kwd)

def pathImportOneFrom(path, attr, **kwd):
    return getattr(pathImport(kwd.pop
        ('name', ''), path = path), attr)

def pathImportFrom(path, *names):
    return moduleImportFrom(pathImport
        ('', path = path), *names)

def pathImport(name, code = None, path = None, compile = None):
    if not path:
        if code is None:
            raise ValueError('must specify path or code')

        path = ''

    else:
        code = open(path).read()


    if compile is None:
        from builtins import compile


    code = compile(code)

    module = ModuleType(name)

    exec(code, module.__dict__)

    return module
