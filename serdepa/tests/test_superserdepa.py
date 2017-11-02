"""test_serdepa.py: Tests for the serdepa metaclass. """

import unittest
from codecs import decode, encode

from serdepa import (
    SerdepaPacket, Length, List, Array, ByteString,
    nx_uint8, nx_uint16, nx_uint32, nx_uint64,
    nx_int8, nx_int16, nx_int32, nx_int64,
    uint8, uint16, uint32, uint64,
    int8, int16, int32, int64
)
from serdepa.exceptions import PacketDefinitionError


class FieldsTester(unittest.TestCase):
    def test_duplicate_field_name(self):
        with self.assertRaises(PacketDefinitionError):
            class TestPacket(SerdepaPacket):
                _fields_ = (
                    ('testfield', nx_uint8),
                    ('testfield', nx_uint64)
                )
        class TestPacket(SerdepaPacket):
            _fields_ = (
                ('testfield1', nx_uint8),
                ('testfield2', nx_uint64)
            )

    def test_length_default_value(self):
        with self.assertRaises(PacketDefinitionError):
            class TestPacket(SerdepaPacket):
                _fields_ = (
                    ('length_field', Length(nx_uint8, 'list_field'), 5),
                    ('list_field', List(nx_uint8))
                )
        class TestPacket(SerdepaPacket):
            _fields_ = (
                ('length_field', Length(nx_uint8, 'list_field')),
                ('list_field', List(nx_uint8))
            )

    def test_missing_field_type(self):
        with self.assertRaises(PacketDefinitionError):
            class TestPacket(SerdepaPacket):
                _fields_ = [
                    ['testfield']
                ]
        class TestPacket(SerdepaPacket):
            _fields_ = [
                ['testfield', nx_uint8]
            ]

    def test_invalid_field_type(self):
        with self.assertRaises(PacketDefinitionError):
            class TestPacket(SerdepaPacket):
                _fields_ = [
                    ['testfield', int]
                ]
        class TestPacket(SerdepaPacket):
            _fields_ = [
                ['testfield', nx_int16]
            ]

    def test_undefined_length_list(self):
        with self.assertRaises(PacketDefinitionError):
            class TestPacket(SerdepaPacket):
                _fields_ = (
                    ('testfield', List(nx_int8)),
                    ('testfield2', nx_uint8)
                )
        class TestPacket(SerdepaPacket):
            _fields_ = (
                ('testfield', List(nx_int8)),
            )
