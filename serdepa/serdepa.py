"""serdepa.py: Binary packet serialization and deserialization library. """

__author__ = "Raido Pahtma, ..."
__license__ = "MIT"


# TODO probably should define custom types to represent different variable types
# ... or maybe use ctypes types like in the initial tests ...?

def add_property(cls, attr, default):
    if hasattr(cls, attr):
        print "NOT adding property %s to %s" % (attr, cls)  # In the final version this should probably raise an exception once metaclasses are handled properly
    else:
        print "adding property %s to %s" % (attr, cls)

        def setter(self, v):
            print "setter for %s" % (attr)  # TODO remove this debug
            setattr(self, '_%s' % attr, v)

        def getter(self):
            return getattr(self, '_%s' % attr, default)

        setattr(cls, attr, property(getter, setter))


class SuperSerdepaPacket(type):

    def __init__(cls, what, bases=None, attrs=None):
        print "SuperTransformPacket cls:%s what:%s bases:%s attrs:%s" % (cls, what, bases, attrs)  # TODO remove

        if '_fields_' in attrs:
            for field in attrs['_fields_']:
                if len(field) == 3 and field[2] == "list":
                    setattr(cls, field[0], [])
                else:
                    add_property(cls, field[0], "")

            # del attrs['_fields_']

        super(SuperSerdepaPacket, cls).__init__(what, bases, attrs)


class SerdepaPacket(object):
    __metaclass__ = SuperSerdepaPacket

    def serialize(self):
        # TODO loop over _fields_ and serialize them
        return ""

    def deserialize(self, data):
        # TODO loop over _fields_ and deserialize their values from data
        pass
