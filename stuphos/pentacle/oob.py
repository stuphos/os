# Out-Of-Band (Object-oriented binding)
import struct
from ..etc.hashlib import sha1

# Server-Side:
CHUNK_SIZE = 100
def asOOB(data, secret_key, chunk_size = CHUNK_SIZE):
    def slices(array, size, start = 0):
        n = len(array)
        while start < n:
            x = start + size
            yield array[start:x]
            start = x

    # Todo: forget about compressing the digest: just eat the overhead.
    # Simply deal with compression before utilizing oob channel.
    # Ugh, why does base64 break newlines?
    def e(b):
        b = '%s%s' % (sha1(secret_key + b).digest(), b)
        return '~%s' % b.encode('zlib').encode('base64').replace('\n', '')

    # Deal with first packet separately by injecting the total payload size as header.
    first = chunk_size - struct.calcsize('i')
    yield e(struct.pack('i', len(data)) + data[:first])

    for bit in slices(data, chunk_size, start = first):
        yield e(bit)

SECRET_KEY = 'xxxxxx'

def test(data):
    return '\n'.join(asOOB(data, SECRET_KEY, 40))

# Programmatic response/fault transport:
try: from pentacle.packaging import EntitySpace, Response, Command, Package
except ImportError: pass
else:
    class PentacleOOB:
        def __init__(self, peer, secret_key = SECRET_KEY,
                                 chunk_size = CHUNK_SIZE,
                                 entity_space = None):

            self.dataChannel = EntitySpace() if entity_space is None else entity_space
            self.peer = peer
            self.secret_key = secret_key
            self.chunk_size = chunk_size
            self.call = self.CommandAttr(self)

        def send(self, msg):
            for line in self.encode(msg):
                self.peer.sendln(line)

        def encode(self, msg):
            if not isinstance(msg, Package):
                msg = Response.Success(value)

            packed = msg.pack(self.dataChannel)

            for line in asOOB(packed, self.secret_key, self.chunk_size):
                yield line

        def __iadd__(self, msg):
            self.send(msg)
            return self

        def closure(self, function, *args, **kwd):
            # Call a method, handling error or success: Send to peer.
            #   self += self(anotherMethod, *args, **kwd)

            try: return Response.Success(function(*args, **kwd))
            except: return Response.Fault(getSystemExceptionInfo())

        __call__ = closure

        class CommandAttr(object):
            class Call:
                def __init__(self, oob, name):
                    self.oob = oob
                    self.name = name

                def __call__(self, *args, **kwd):
                    self.oob += Command.Nonserial(self.name, args, kwd)

            def __init__(self, oob):
                self.__oob = oob

            def __getattr__(self, name):
                if name.startswith('__'):
                    return object.__getattribute__(self, name)

                return PentacleOOB.CommandAttr.Call(self.__oob, name)

try: from stuphmud.server.player import ACMDLN, Option
except ImportError: pass
else:
    @ACMDLN('oob*', Option('--chunk-size', '-s', type = int, default = CHUNK_SIZE),
                    Option('--secret-key', '-k', default = SECRET_KEY))
    def doProduceOOB(peer, command):
        if peer is not None:
            name = ' '.join(command.args)
            if name:
                # Take a page from the notebook.
                from stuphmud.server.player.notebook import Notebook
                nb = Notebook.Open(peer)
                content = nb.shelf[name]
                nb.close()

                # print '[ Sending OOB: %d ]' % len(content)

                # Render with PentacleOOB:
                try: oob = peer.oob
                except AttributeError:
                    (key, chunk) = (command.options.secret_key, command.options.chunk_size)
                    oob = PentacleOOB(peer, secret_key = key, chunk_size = chunk)

                oob += Response.Success(content)

                # Old: Send as is.
                ##    for line in asOOB(content, key, chunk):
                ##        peer.sendln(line)

                return True

try: from stuphos.runtime import Component
except ImportError: pass
else:
    class OOBNetwork(Component):
        def onNewConnection(self, cltr, peer):
            peer.oob = PentacleOOB(peer)
