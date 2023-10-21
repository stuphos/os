from . import CommandMessage, RegisterCommandClass
from ...etc.hashlib import md5
from ...etc.timing import getCurrentSystemTime


def md5sum(*parts):
    hash = md5()
    for p in parts:
        hash.update(p)

    return hash.hexdigest()

class MaterializeResourceCommandMessage(CommandMessage):
    # Memcache equivilant?
    class Pool(dict):
        @classmethod
        def createMaster(self):
            master = self(':MASTER:') # Kind of a container of all pools.
            master.default = self('')
            return master

        RESOURCE_POOL_MASTER_NAME = 'Resource::Pool::Master'

        @classmethod
        def getMaster(self):
            from ....runtime.registry import getObject
            return getObject(self.RESOURCE_POOL_MASTER_NAME,
                             create = self.createMaster)

        def __init__(self, name):
            dict.__init__(self)
            self.name = name

        def addResource(self, name, rsrc):
            self.setdefault(name, []).append(rsrc)
        def getByNamedId(self, name, id = None):
            listed = self.get(name)
            if id is None:
                return listed # or first

            for rsrc in listed:
                if rsrc.id == id:
                    return rsrc

            # Raise??

        def __repr__(self):
            return '<%s: %d entries>' % (self.name, len(self))

    class Resource:
        def __init__(self, id, content_type, payload, original = None, pool = None):
            self.id = id
            self.content_type = content_type
            self.payload = payload
            self.original = original
            self.pool = pool

        def __repr__(self):
            pool = repr(self.pool) if self.pool is not None else ''
            return '<%s: %r%s%s>' % (self.__class__.__name__, self.id,
                                     pool and ' ' or '', pool)

        def __str__(self):
            return str(self.payload)

    @classmethod
    def getPool(self, name):
        master = self.Pool.getMaster()
        if name is None:
            return master.default

        try: return master[name]
        except KeyError:
            pool = master[name] = self.Pool(name)
            return pool

    @classmethod
    def getMessageId(self, pool_name, name, headers, payload):
        try: id = headers['X-Resource-Id']
        except KeyError:
            id = md5sum(getCurrentSystemTime(), payload)

        return '%s:%s:%s' % (pool_name, name, id)

    @classmethod
    def getResource(self, id = None, pool_name = None, name = None):
        if pool_name:
            assert name
        else:
            assert id
            assert not name

            parts = id.split(':', 3)
            if len(parts) == 3:
                (pool_name, name, id) = parts
            elif len(parts) == 2:
                (pool_name, name) = parts
                id = None
            else:
                raise AssertionError('Resource id format error: %s' % id)

        pool = self.getPool(pool_name)
        return pool.getByNamedId(name, id)

    def Execute(self):
        # Yet another embedded message??
        # The (resource) message content and headers should be merged with
        # the communication message, avoiding this extra embedding level.
        # msg = message_from_string(self.payload)

        pool_name = self['X-Resource-Pool-Name']
        pool = self.getPool(pool_name)

        name = msg.get_filename() # XXX err, resolve this from payload?
        id = self.getMessageId(pool_name, name, self.getHeaders(), self.payload)

        pool.addResource(name,
                         self.Resource(id,
                                       self.getContentType(),
                                       self.getHeaders(),
                                       self.payload))

RegisterCommandClass('application/x-stuph-material-resource', MaterializeResourceCommandMessage)
