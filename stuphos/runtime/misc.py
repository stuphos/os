# Miscellaneous Runtime Tools.
#
# Note: These things aren't really used anymore.
# (This stuff can come from common tools anyway)

# Instrument the Runtime Frame Stack.
from sys import _getframe as thisFrame

def show(order = None):
    for frame in order or stack():
        print(string(frame))

def traceback(frame = None, n = -1):
    frame = frame or thisFrame()
    while frame:
        if n > 0:
            n -= 1
            if n > 0:
                frame = frame.f_back
                continue

        yield frame
        frame = frame.f_back

def stack():
    # Generate return in reverse order from grand-parent calling frame.
    return reversed(list(traceback(n = 2)))

def bottom():
    return list(traceback())[-1]

def string(frame):
    from linecache import getline
    code = frame.f_code
    return '%s:%s:%s%s' % (code.co_name, code.co_filename, code.co_firstlineno,
                           (frame.f_trace and ' (%s)' % frame.f_trace.__name__) or '')

def search(name = None, ascending = False):
    for frame in (ascending and stack() or traceback()):
        if frame.f_code.co_name == name:
            yield frame

def find(*args, **kwd):
    frames = search(*args, **kwd)

    try: return next(frames)
    except StopIteration:
        raise NameError(name)

# Debugger legacy:
##    def set_byframename(name):
##        self.reset()
##        stack = FrameStack.search(name = name, ascending = True)
##
##        try: main = iter(stack).next()
##        except StopIteration:
##            raise NameError(name)
##
##        else:
##            self.set_trace(main)
##            self.set_continue()


# Unused Patterns:
class Bundle:
    # Curry/Delegate Pattern.
    def __init__(self, function, *args, **kwd):
        self.function = function
        self.args = args
        self.kwd = kwd

    def __call__(self, *args, **kwd):
        args = self.args + args
        kwd.update(self.kwd)
        return self.function(*args, **kwd)
