# Object to file (internal) to script (extract installer)
# Object to path (script) to installed library path (install installer)
# Direct installation invocation from frontend

from stuphos.runtime.architecture.lookup import LookupObject


OBJECT_TO_PATH = r'''\
scatter(args$slice(1), 'object', 'path')
path = path.split('/')

'kernel/module'(path[-1]).setText \
    ('kernel/edit'('/'.join(path.slice(0, -1))), \
     'kernel/lookup$'(object))

'''

# @classmethod
def _objectToFile(name = None, outfile = None):
    '''
    installer=stuphos.language.installer

    --admin-script $installer._objectToFile \
        -x name=$installer.OBJECT_TO_PATH \
        -x outfile=scripts/install-object.ela

    -f scripts/install-object.ela $installer.INIT install

    '''

    assert name and outfile
    return io.path(outfile).write(LookupObject(name))


def objectToString(path):
    from stuphos.kernel import LookupObject
    return LookupObject('.'.join(path) \
        if not isinstance(path, str) else path)


INIT = '''\
# -f scripts/install-object.ela $installer.INIT install

# -c "install/init'('stuphos.language.installer.STAGE_1', key) <- key:
# "

def run(code):
    return act(string(code).compiled,
        args$slice(1), keywords$())

def init(path):
    if not is$string(path):
        path = '.'.join(path)

    return run(format.format \
        (source = 'kernel/callObject$$' \
            (to.value, path)))

    <- format:
        {source}
        return locals()

    <- to:
        - stuphos
        - language
        - installer
        - objectToString


def init$default(path, default):
    try: default = keywords$('default')
    except key$error: return init(path)
    else: return run(default)


if args$() or keywords$():
    return act(run, [default] + args$(), keywords$()) <- default:
        return true

    return init(path.value) <- path:
        - builtins
        - configuration
        - AgentSystem
        - program1

'''

INSTALL = '''\
# -f <> path/to/folder/name
scatter$args('path', 'implfile')
path = path.split('/')

# todo: create module @pathfirst

implfile = 'kernel/callObject$'('builtins.io.path', implfile)

'kernel/module'(path[-1]).setTextSource \
    ('kernel/edit'('/'.join(path.slice(0, -1))),
     implfile.read())

'''

STAGE_1 = '''\
return key

'''
