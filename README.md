# `serdepa`

Packet serialization and deserialization library for python.

## Basic usage

The base of the `serdepa` library is the `SerdepaPacket` class. This
class expects to have a `_fields_` attribute that contains the structure
of the packet the class represents:

```python
from serdepa import SerdepaPacket, nx_uint8


class SamplePacket(SerdepaPacket):
    _fields_ = (
        ('field_name', nx_uint8),
        ('field_name_2', nx_uint8),
    )


packet = SamplePacket()
packet.deserialize(b'\x01\x02')
print(packet.field_name == 1)
# True
packet.field_name_2 = 9
print(packet.serialize() == b'\x01\x09')
# True
```

## `_fields_`

The `_fields_` attribute desctibes the structure of the packet. The
structure of the attribute is a list of lists where every inner list
represents a new structure, its name and optionally the default value.

The default value only has an effect when serializing an instance into
binary data.

### Examples

For example, the following field is named `tail` and it is 2 bytes long.
It is big-endian and unsigned.

```python
('tail', nx_uint16)
```

## Field types

### Integer types

TODO

### Array types

TODO

### Embedded structures

TODO
