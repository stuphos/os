import struct

structUnpack = struct.unpack
structPack = struct.pack
structCalcsize = struct.calcsize

BYTEORDER = '@'

def structUnpack(format, buffer):
    def _():
        n = 0
        for c in format: # XXX digitized type buffers (arrays).
            i = n + struct.calcsize(BYTEORDER + c)
            yield struct.unpack(BYTEORDER + c, buffer[n:i])[0]
            n = i

    r = list(_())
    # if len(r) == 1:
    #     return r[0]

    return r

def structCalcsize(format):
    a = 0
    #import pdb; pdb.set_trace()
    for c in format:
        a += struct.calcsize(BYTEORDER + c)

    return a

class BuildRecordClass(object):
    def __new__(self, name, bases, values):
        cls = type(name, bases, values)

        field_data = values.get('Fields')
        if field_data is not None:
            cls._format = self.__build_format(field_data)
            cls._format_size = structCalcsize(cls._format)

            cls._names = self.__build_names(field_data)
            cls._defaults = self.__build_defaults(field_data)

        return cls

    @staticmethod
    def __build_format(fields):
        return ''.join(f[1].FormatString() for f in fields)

    @staticmethod
    def __build_names(fields):
        return [f[0] for f in fields]

    @classmethod
    def __build_defaults(self, field_data):
        return list(map(self.__get_field_default, field_data))

    @staticmethod
    def __get_field_default(field):
        if len(field) > 2:
            return field[2]

        return field[1].DefaultValue()

class Record(metaclass=BuildRecordClass):
    # How to pass this down to subclasses?
    @classmethod
    def FormatString(self):
        return self._format
    @classmethod
    def Size(self):
        return self._format_size
    @classmethod
    def Names(self):
        return self._names
    @classmethod
    def Defaults(self):
        return self._defaults

    # Instances.
    def __load_string(self, record):
        size = self.Size()
        if len(record) != size:
            raise ValueError('Size of record buffer (%d) != format size (%d)' % \
                             (len(record), size))

        values = structUnpack(self.FormatString(), record)
        for (i, (n, f)) in enumerate(self.Fields):
            v = values[i]
            if isinstance(f, (Record.Array, Record, Record.String)):
                # Selectively unpack -- because it's already been done by the
                # record format string, except for arrays and subrecords.
                v = f.Unpack(v)

            setattr(self, n, v)

    def __load_null(self):
        names = self.Names()
        defaults = self.Defaults()
        for x in range(len(names)):
            setattr(self, names[x], defaults[x])

    def __init__(self, record = None):
        if isinstance(record, str):
            self.__load_string(record)
        elif record is None:
            self.__load_null()
        else:
            raise TypeError('Unknown record source type (%s)' % type(record).__name__)

    @classmethod
    def Unpack(self, record):
        return self(record)

    def __iter__(self):
        return (getattr(self, name) for name in self.Names())
    def __pack__(self):
        values = tuple(self)
        return structPack(self.FormatString(), *values)

    # Types.
    @staticmethod
    def Padding(size):
        return '%dx' % size

    # XXX Err, record should subclass type..?
    class Type:
        def __init__(self, format, default = None):
            self.format = format
            self.default = default
            self.size = structCalcsize(format)

        def ArrayOf(self, size):
            return Record.Array(self, size)
        def __mul__(self, size):
            return self.ArrayOf(size)
        def __getitem__(self, size):
            return self.ArrayOf(size)

        def FormatString(self):
            return self.format
        def DefaultValue(self):
            return self.default
        def Size(self):
            return self.size

        def Unpack(self, value):
            return structUnpack(self.FormatString(), value)[0]

        def __str__(self):
            return '%s(%r)' % (self.__class__.__name__,
                               self.FormatString())
        __repr__ = __str__

    class Array(Type):
        def __init__(self, rtype, size):
            self.type = rtype
            self.size = size

            if isinstance(rtype, type):
                # Pack it into a string.
                format = '%ds' % (size * structCalcsize(rtype.FormatString()))
            elif issubclass(getattr(rtype, '__class__', None), Record.Type):
                format = '%d%s' % (size, rtype.FormatString())
            else:
                raise TypeError(type(rtype).__name__)

            Record.Type.__init__(self, format)

        def Unpack(self, value):
            return list(map(self.type.Unpack, slices(value, self.type.Size())))

        def __str__(self):
            return '%s[%s]' % (self.type, self.size)
        __repr__ = __str__

    class String(Type):
        # Was defined as an Array-subclass, but there are no requirements for that.
        def __init__(self, size):
            self.size = size
            Record.Type.__init__(self, '%ds' % size)

        def Unpack(self, value):
            return value

    class CString(String):
        def Unpack(self, value):
            return fromCString(value)

    Pointer = Type('P')

    # Todo: signs.
    Byte  = Type('b')
    Int   = Type('i')
    Short = Type('h')
    Long  = Type('l')
    UInt  = Type('I')

    SByte = Byte
    Char  = Byte
    ShInt = Short
    TimeT = Long
    SizeT = UInt

def pack(record):
    # if issubclass(record.__class__, Record):
    return record.__pack__()

def slices(array, size):
    i = 0
    end = len(array)

    while i < end:
        n = i + size
        yield array[i:n]
        i = n

def fromCString(value):
    i = value.find('\x00')
    if i < 0:
        return value

    return value[:i]

def ReadFile(fileSource, recordClass, nitems = -1):
    size = recordClass.Size()
    n = 0
    try:
        while True:
            buf = fileSource.read(size)
            if buf == '':
                break

            yield recordClass(buf)

            # Limit number of items read if specified.
            if nitems > 0:
                n += 1
                if n >= nitems:
                    break

    except EOFError:
        pass

def ReadOneFromFile(fileSource, recordClass):
    return next(ReadFile(fileSource, recordClass, 1))

def ReadBytes(fp, nr_bytes):
    return fp.read(nr_bytes)
