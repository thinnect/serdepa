"""
serdepa.py: Binary packet serialization and deserialization library.
"""

from __future__ import unicode_literals

from functools import reduce
import struct
import collections
import warnings
import copy
import math
from codecs import encode

from six import add_metaclass, BytesIO

__author__ = "Raido Pahtma, Kaarel Ratas"
__license__ = "MIT"

version = '0.2.6.dev0'


def add_property(cls, attr, attr_type):
    if hasattr(cls, attr):
        # print "NOT adding property %s to %s" % (attr, cls)
        # In the final version this should probably raise an exception once everything is handled properly
        pass
    else:

        if isinstance(attr_type, BaseIterable) or isinstance(attr_type, ByteString):
            setter = None

            def getter(self):
                return getattr(self, '_%s' % attr)

        elif isinstance(attr_type, Length):
            setter = None

            def getter(self):
                return len(getattr(
                    self,
                    '_field_registry'
                )[getattr(self, '_depends')[attr]])

        elif isinstance(attr_type, SuperSerdepaPacket):
            def setter(self, v):
                if isinstance(v, self._fields[attr][0]):
                    setattr(self, '_%s' % attr, v)
                    self._field_registry[attr] = v
                else:
                    raise ValueError(
                        "Cannot assign a value of type {} "
                        "to field {} of type {}".format(
                            v.__class__.__name__,
                            attr,
                            getattr(self, '_%s' % attr).__class__.__name__
                        )
                    )

            def getter(self):
                return getattr(self, '_%s' % attr)

        else:
            def setter(self, v):
                setattr(getattr(self, '_%s' % attr), "value", v)

            def getter(self):
                return getattr(self, '_%s' % attr).value

        setattr(cls, attr, property(getter, setter))


class SuperSerdepaPacket(type):
    """
    Metaclass of the SerdepaPacket object. Essentially does the following:
        Reads the _fields_ attribute of the class and for each 2- or
        3-tuple entry sets up the properties of the class to the right
        names. Also checks that each (non-last) List instance has a
        Length field associated with it.
    """

    def __init__(cls, what, bases=None, attrs=None):

        setattr(cls, "_fields", collections.OrderedDict())
        setattr(cls, "_depends", dict())
        if '_fields_' in attrs:
            for field in attrs['_fields_']:
                if len(field) == 2 or len(field) == 3:
                    if len(field) == 2:
                        default = None
                    elif isinstance(field[1], Length):
                        raise TypeError(
                            "A Length field can't have a default value: {}".format(
                                field
                            )
                        )
                    else:
                        default = field[2]
                    add_property(cls, field[0], field[1])
                    getattr(cls, "_fields")[field[0]] = [field[1], default]
                    if isinstance(field[1], Length):
                        getattr(cls, "_depends")[field[0]] = field[1]._field
                    elif isinstance(field[1], List) or isinstance(field[1], ByteString):
                        if not (field[0] in getattr(cls, "_depends").values() or field == attrs['_fields_'][-1]):
                            raise TypeError("Only the last field can have an undefined length ({} of type {})".format(
                                field[0],
                                type(field[1])
                            ))
                else:
                    raise TypeError("A field needs both a name and a type: {}".format(field))

        super(SuperSerdepaPacket, cls).__init__(what, bases, attrs)


@add_metaclass(SuperSerdepaPacket)
class SerdepaPacket(object):
    """
    The superclass for any packets. Defining a subclass works as such:
        class Packet(SerdepaPacket):
            _fields_ = [
                ("name", type[, default]),
                ("name", type[, default]),
                ...
            ]

    Has the following public methods:
    .serialize() -> bytearray
    .deserialize(bytearray)         raises ValueError on bad input

    and the class method
    .minimal_size() -> int
    """

    def __init__(self, **kwargs):
        self._field_registry = collections.OrderedDict()
        for name, (_type, default) in self._fields.items():
            if name in kwargs:
                self._field_registry[name] = _type(initial=copy.copy(kwargs[name]))
            elif default:
                self._field_registry[name] = _type(initial=copy.copy(default))
            else:
                self._field_registry[name] = _type()
            setattr(self, '_%s' % name, self._field_registry[name])

    def serialize(self):
        serialized = BytesIO()
        for name, field in self._field_registry.items():
            if name in self._depends:
                serialized.write(
                    field.serialize(self._field_registry[self._depends[name]].length)
                )
            else:
                serialized.write(field.serialize())
        ret = serialized.getvalue()
        serialized.close()
        return ret

    def deserialize(self, data, pos=0):
        for i, (name, field) in enumerate(self._field_registry.items()):
            if pos >= len(data):
                if i == len(self._field_registry) - 1 and (isinstance(field, List) or isinstance(field, ByteString)):
                    return pos
                else:
                    raise ValueError("Invalid length of data to deserialize.")
            try:
                pos = field.deserialize(data, pos)
            except AttributeError:
                for key, value in self._depends.items():
                    if name == value:
                        pos = field.deserialize(data, pos, self._field_registry[key]._type.value)
                        break
                else:
                    pos = field.deserialize(data, pos, -1)
            if pos > len(data):
                raise ValueError("Invalid length of data to deserialize. {}, {}".format(pos, len(data)))
        return pos

    def serialized_size(self):
        size = 0
        for name, field in self._field_registry.items():
            size += field.serialized_size()
        return size

    @classmethod
    def minimal_size(cls):
        size = 0
        for name, (_type, default) in cls._fields.items():
            size += _type.minimal_size()
        return size

    def __str__(self):
        return encode(self.serialize(), "hex").decode().upper()

    def __eq__(self, other):
        return str(self) == str(other)


class BaseField(object):

    def __call__(self, **kwargs):
        ret = copy.copy(self)
        if "initial" in kwargs:
            ret._set_to(kwargs["initial"])
        return ret

#    def __call__(self):
#        return NotImplemented
#
    def serialize(self):
        return bytearray([])

    def deserialize(self, value, pos):
        raise NotImplementedError()

    @classmethod
    def minimal_size(cls):
        raise NotImplementedError()


class BaseIterable(BaseField, list):

    def __init__(self, initial=[]):
        super(BaseIterable, self).__init__()
        for value in initial:
            self.append(self._type(initial=copy.copy(value)))

    def _set_to(self, values):
        while len(self) > 0:
            self.pop()
        for value in values:
            self.append(value)

    def append(self, value):
        if isinstance(value, self._type):
            new_value = value
        else:
            new_value = self._type(initial=value)
        super(BaseIterable, self).append(new_value)

    def serialize(self):
        ret = bytearray()
        for i in range(self.length):
            ret += self[i].serialize()
        return ret

    def deserialize(self, value, pos):
        for i in range(self.length):
            self[i] = self._type()
            pos = self[i].deserialize(value, pos)
        return pos

    def __iter__(self):
        for i in range(len(self)):
            try:
                yield self[i].value
            except AttributeError:
                yield self[i]


class BaseInt(BaseField):
    """
    Base class for all integer types. Has _signed (bool) and _format (struct format string).
    """

    _length = None
    _signed = None
    _format = ""

    def __init__(self, initial=0):
        self._value = initial

    def _set_to(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = int(value)

    def serialize(self):
        return struct.pack(self._format, self._value)

    def deserialize(self, value, pos):
        try:
            self._value = struct.unpack(self._format, value[pos:pos+self.serialized_size()])[0]
        except struct.error as e:
            raise ValueError("Invalid length of data!", e)
        return pos + self.serialized_size()

    @classmethod
    def serialized_size(cls):
        """
        Returns the length of this field in bytes. If the length in bits is not directly
        divisible by 8, an extra byte is added.
        """

        return int(math.ceil(cls._length/8.0))

    def __getattribute__(self, attr):
        if attr in ["__lt__", "__le__", "__eq__", "__ne__", "__gt__", "__ge__",
                    "__add__", "__sub__", "__mul__", "__floordiv__", "__mod__",
                    "__divmod__", "__pow__", "__lshift__", "__rshift__", "__and__",
                    "__xor__", "__or__", "__div__", "__truediv__", "__str__"]:
            return self._value.__getattribute__(attr)
        else:
            return super(BaseInt, self).__getattribute__(attr)

    def __int__(self):
        return self._value

    def __repr__(self):
        return "{} with value {}".format(self.__class__, self._value)

    @classmethod
    def minimal_size(cls):
        return int(math.ceil(cls._length/8.0))


class Length(BaseField):
    """
    A value that defines another field's length.
    """

    def __init__(self, object_type, field_name):
        self._type = object_type()
        self._field = field_name

    def serialized_size(self):
        return self._type.serialized_size()

    def serialize(self, length):  # TODO PyCharm does not like this approach, method signatures don't match
        self._type.value = length
        return self._type.serialize()

    def deserialize(self, value, pos):
        return self._type.deserialize(value, pos)

    def minimal_size(self):
        return self.serialized_size()


class List(BaseIterable):
    """
    An array with its length defined elsewhere.
    """

    def __init__(self, object_type, **kwargs):
        self._type = object_type
        super(List, self).__init__(**kwargs)

    @property
    def length(self):
        return len(self)

    def serialized_size(self):
        return self._type.serialized_size() * self.length

    def deserialize(self, value, pos, length=None):
        if length is None:
            raise AttributeError("Unknown length.")
        elif length == -1:
            del self[:]     # clear the internal list - deserialization will overwrite anyway.
            for i in range(len(self), (len(value)-pos)//self._type().serialized_size()):
                self.append(0)
            return super(List, self).deserialize(value, pos)
        else:
            del self[:]     # clear the internal list - deserialization will overwrite anyway.
            for i in range(len(self), length):
                self.append(0)
            return super(List, self).deserialize(value, pos)

    def minimal_size(cls):
        return 0


class Array(BaseIterable):
    """
    A fixed-length array of values.
    """

    def __init__(self, object_type, length, **kwargs):
        self._type = object_type
        self._length = length
        super(Array, self).__init__(**kwargs)

    @property
    def length(self):
        return self._length

    def serialized_size(self):
        return self._type.serialized_size() * self.length

    def serialize(self):
        dl = self.length - len(self)
        if dl < 0:
            warnings.warn(RuntimeWarning("The number of items in the Array exceeds the length of the array."))
        elif dl > 0:
            self += [self._type() for _ in range(dl)]  # TODO is this correct???
        ret = super(Array, self).serialize()
        for i in range(dl):
            self.pop(-1)
        return ret

    def deserialize(self, value, pos):
        for i in range(len(self), self.length):
            self.append(self._type())
        return super(Array, self).deserialize(value, pos)

    def minimal_size(self):
        return self.serialized_size()


class ByteString(BaseField):
    """
    A variable or fixed-length string of bytes.
    """

    def __init__(self, length=None, **kwargs):
        if length is not None:
            self._data_container = Array(nx_uint8, length)
        else:
            self._data_container = List(nx_uint8)
        super(ByteString, self).__init__(**kwargs)

    def __getattr__(self, attr):
        if attr not in ['_data_container']:
            return getattr(self._data_container, attr)
        else:
            return super(ByteString, self).__getattribute__(attr)

    def __setattr__(self, attr, value):
        if attr not in ['_data_container', '_value']:
            setattr(self._data_container, attr, value)
        else:
            super(ByteString, self).__setattr__(attr, value)

    @property
    def _value(self):
        return reduce(
            lambda x, v: x + (v[1] << (8*v[0])),
            enumerate(
                reversed(list(self._data_container))
            ),
            0
        )

    def deserialize(self, *args, **kwargs):
        return self._data_container.deserialize(*args, **kwargs)

    def serialize(self, *args, **kwargs):
        return self._data_container.serialize(*args, **kwargs)

    def __eq__(self, other):
        return self._value == other

    def __repr__(self):
        return "{} with value {}".format(self.__class__, self._value)

    def __str__(self):
        return "{value:0{size}X}".format(
            value=self._value,
            size=self._data_container.serialized_size()*2,
        )

    def __len__(self):
        return len(self._data_container)


class nx_uint8(BaseInt):
    _signed = False
    _length = 8
    _format = ">B"


class nx_int8(BaseInt):
    _signed = True
    _length = 8
    _format = ">b"


class uint8(BaseInt):
    _signed = False
    _length = 8
    _format = "<B"


class int8(BaseInt):
    _signed = True
    _length = 8
    _format = "<b"


class nx_uint16(BaseInt):
    _signed = False
    _length = 16
    _format = ">H"


class nx_int16(BaseInt):
    _signed = True
    _length = 16
    _format = ">h"


class uint16(BaseInt):
    _signed = False
    _length = 16
    _format = "<H"


class int16(BaseInt):
    _signed = True
    _length = 16
    _format = "<h"


class nx_uint32(BaseInt):
    _signed = False
    _length = 32
    _format = ">I"


class nx_int32(BaseInt):
    _signed = True
    _length = 32
    _format = ">i"


class uint32(BaseInt):
    _signed = False
    _length = 32
    _format = "<I"


class int32(BaseInt):
    _signed = True
    _length = 32
    _format = "<i"


class nx_uint64(BaseInt):
    _signed = False
    _length = 64
    _format = ">Q"


class nx_int64(BaseInt):
    _signed = True
    _length = 64
    _format = ">q"


class uint64(BaseInt):
    _signed = False
    _length = 64
    _format = "<Q"


class int64(BaseInt):
    _signed = True
    _length = 64
    _format = "<q"
