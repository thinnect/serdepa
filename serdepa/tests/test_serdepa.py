"""test_serdepa.py: Tests for serdepa packets. """

import unittest
from codecs import decode, encode

from serdepa import (
    SerdepaPacket, Length, List, Array, ByteString,
    nx_uint8, nx_uint16, nx_uint32, nx_uint64,
    nx_int8, nx_int16, nx_int32, nx_int64,
    uint8, uint16, uint32, uint64,
    int8, int16, int32, int64
)


__author__ = "Raido Pahtma, Kaarel Ratas"
__license__ = "MIT"


class PointStruct(SerdepaPacket):
    _fields_ = [
        ("x", nx_int32),
        ("y", nx_int32)
    ]


class OnePacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("timestamp", nx_uint32),
        ("length", Length(nx_uint8, "data")),
        ("data", List(nx_uint8)),
        ("tail", List(nx_uint8))
    ]


class DefaultValuePacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8, 1),
        ("timestamp", nx_uint32, 12345),
        ("length", Length(nx_uint8, "data")),
        ("data", List(nx_uint8), [1, 2, 3, 4]),
        ("tail", List(nx_uint8), [5, 6])
    ]


class AnotherPacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("timestamp", nx_uint32),
        ("origin", PointStruct),
        ("points", Length(nx_uint8, "data")),
        ("data", List(PointStruct))
    ]


class ArrayPacket(SerdepaPacket):
    _fields_ = [
        ("header", nx_uint8),
        ("data", Array(PointStruct, 4))
    ]


class SimpleArray(SerdepaPacket):
    _fields_ = [
        ("data", Array(nx_uint8, 10))
    ]


class MyNodes(SerdepaPacket):
    _fields_ = [
        ("nodeId", nx_uint16),
        ("attr", nx_int16),
        ("inQlty", nx_uint8),
        ("outQlty", nx_uint8),
        ("qlty", nx_uint8),
        ("lifetime", nx_uint8)
    ]


class MyRouters(SerdepaPacket):
    _fields_ = [
        ("beatId", nx_uint32),
        ("routerId", nx_uint16),
        ("partnerId", nx_uint16),
        ("attr", nx_uint16),
        ("qlty", nx_uint8),
        ("lifetime", nx_uint8),
        ("flags", nx_uint8),
    ]


class BeatRecord(SerdepaPacket):
    _fields_ = [
        ("clockstamp", nx_uint32),
        ("nodes_in_beat", Length(nx_uint8, "nodes")),
        ("beats_in_cycle", Length(nx_uint8, "routers")),
        ("my_beat_id", nx_uint32),
        ("nodes", List(MyNodes)),
        ("routers", List(MyRouters))
    ]


class TransformTester(unittest.TestCase):
    p1 = "010000303904010203040506"

    def test_one(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)
        p.tail.append(5)
        p.tail.append(6)

        self.assertEqual(p.serialize(), decode(self.p1, "hex"))

    def test_two(self):
        p = OnePacket()
        p.deserialize(decode(self.p1, "hex"))

        self.assertEqual(p.header, 1)
        self.assertEqual(p.timestamp, 12345)
        self.assertEqual(p.length, 4)
        self.assertEqual(len(p.data), 4)
        self.assertEqual(len(p.tail), 2)
        self.assertEqual(list(p.data), [1, 2, 3, 4])
        self.assertEqual(list(p.tail), [5, 6])


class EmptyTailTester(unittest.TestCase):
    p1 = "01000030390401020304"

    def test_empty_tail_deserialize(self):
        p = OnePacket()
        p.deserialize(decode(self.p1, "hex"))

        self.assertEqual(p.header, 1)
        self.assertEqual(p.timestamp, 12345)
        self.assertEqual(p.length, 4)
        self.assertEqual(list(p.data), [1, 2, 3, 4])
        self.assertEqual(list(p.tail), [])

    def test_empty_tail_serialize(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)

        self.assertEqual(p.serialize(), decode(self.p1, "hex"))


class DefaultValueTester(unittest.TestCase):
    p1 = "010000303904010203040506"
    p2 = "020000303904010203040506"

    def test_default_value_serialize(self):
        p = DefaultValuePacket()
        self.assertEqual(p.serialize(), decode(self.p1, "hex"))

    def test_default_keyword(self):
        p = DefaultValuePacket(header=2)
        self.assertEqual(p.serialize(), decode(self.p2, "hex"))


class ArrayTester(unittest.TestCase):
    a1 = "00010203040506070809"
    a2 = "000000000100000002000000030000000400000005000000060000000000000000"

    def test_simple_array(self):
        p = SimpleArray()
        for i in range(10):
            p.data.append(i)
        self.assertEqual(p.serialize(), decode(self.a1, "hex"))

    def test_single_array(self):
        p = ArrayPacket()
        p.header = 0
        p.data.append(PointStruct(x=1, y=2))
        p.data.append(PointStruct(x=3, y=4))
        p.data.append(PointStruct(x=5, y=6))

        self.assertEqual(p.serialize(), decode(self.a2, "hex"))

    def test_single_array_deserialize(self):
        p = ArrayPacket()
        p.deserialize(decode(self.a2, "hex"))

        self.assertEqual(p.header, 0)
        self.assertEqual(len(p.data), 4)
        self.assertEqual(p.data[1].x, 3)
        self.assertEqual(p.data[3].y, 0)


class TestHourlyReport(unittest.TestCase):
    report = (
        "1DD26640"
        "07"
        "0D"
        "0005029E"
        "022B0139FFFF0003"
        "029E010EFFFF3D03"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000000000000000000000"
        "000201AB029E01AB0000001500"
        "00030296029E02350000001500"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "000701FA022B022D00FF381300"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
    )

    def test_hourly_deserialize(self):
        r = BeatRecord()
        r.deserialize(decode(self.report, "hex"))

        self.assertEqual(r.nodes_in_beat, 7)
        self.assertEqual(r.beats_in_cycle, 13)


class StringTester(unittest.TestCase):
    report = (
        "1DD26640"
        "07"
        "0D"
        "0005029E"
        "022B0139FFFF0003"
        "029E010EFFFF3D03"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000000000000000000000"
        "000201AB029E01AB0000001500"
        "00030296029E02350000001500"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "000701FA022B022D00FF381300"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
    )

    def test_str(self):
        r = BeatRecord()
        r.deserialize(decode(self.report, "hex"))

        self.assertEqual(self.report, str(r))


class SerializedSizeTester(unittest.TestCase):
    def test_minimal_serialized_size(self):
        self.assertEqual(OnePacket.minimal_size(), 6)
        self.assertEqual(BeatRecord.minimal_size(), 10)

    def test_serialized_size(self):
        p = OnePacket()
        p.header = 1
        p.timestamp = 12345
        p.data.append(1)
        p.data.append(2)
        p.data.append(3)
        p.data.append(4)
        p.tail.append(5)
        p.tail.append(6)
        self.assertEqual(p.serialized_size(), 12)


class NestedPacketTester(unittest.TestCase):
    p0 = (
        "F1"
        "0000000000000003"
        "0000000100000002"
        "0000000200000001"
        "0000000300000000"
    )
    p1 = (
        "D0"
        "12345678"
        "0000000100000001"
        "01"
        "0000000200000002"
    )

    def test_nested_packet_serialize(self):
        packet = ArrayPacket()
        packet.header = 0xF1
        for i, j in zip(range(4), reversed(range(4))):
            packet.data.append(PointStruct(x=i, y=j))
        self.assertEqual(packet.serialize(), decode(self.p0, "hex"))

        # Test regular nested packet
        packet = AnotherPacket()
        packet.header = 0xD0
        packet.timestamp = 0x12345678
        packet.origin.x = 1
        packet.origin.y = 1
        packet.data.append(PointStruct(x=2, y=2))
        self.assertEqual(packet.serialize(), decode(self.p1, "hex"))

    def test_nested_packet_deserialize(self):
        packet = ArrayPacket()
        packet.deserialize(decode(self.p0, "hex"))
        self.assertEqual(packet.header, 0xF1)
        self.assertEqual(
            list(packet.data),
            [
                PointStruct(x=0, y=3),
                PointStruct(x=1, y=2),
                PointStruct(x=2, y=1),
                PointStruct(x=3, y=0)
            ]
        )

        # Test rgular nested packet
        packet = AnotherPacket()
        packet.deserialize(decode(self.p1, "hex"))
        self.assertEqual(packet.header, 0xD0)
        self.assertEqual(packet.timestamp, 0x12345678)
        self.assertEqual(packet.origin, PointStruct(x=1, y=1))
        self.assertEqual(packet.points, 1)
        self.assertEqual(
            list(packet.data),
            [PointStruct(x=2, y=2)]
        )

    def test_nested_packet_assign(self):
        packet = AnotherPacket()
        try:
            packet.origin = PointStruct(x=1, y=1)
        except ValueError as err:
            self.fail(
                "Assigning PointStruct to packet.origin failed: {}".format(
                    err.args[0] if err.args else "<NO MESSAGE>"
                )
            )
        with self.assertRaises(ValueError):
            packet.origin = AnotherPacket()

    def test_nested_packet_assign_serialize(self):
        packet = AnotherPacket()
        packet.header = 0xD0
        packet.timestamp = 0x12345678
        packet.origin = PointStruct(x=1, y=1)
        packet.data.append(PointStruct(x=2, y=2))
        self.assertEqual(
            encode(packet.serialize(), "hex").decode().upper(),
            self.p1
        )


class InvalidInputTester(unittest.TestCase):
    p = (
        "1DD26640"
        "07"
        "0D"
        "0005029E"
        "022B0139FFFF0003"
        "029E010EFFFF3D03"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000FFFF0000"
        "00000000000000000000000000"
        "000201AB029E01AB0000001500"
        "00030296029E02350000001500"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "00000000000000000000000000"
        "000701FA0F"
    )

    def test_invalid_length_input(self):
        r = BeatRecord()
        with self.assertRaises(ValueError):
            r.deserialize(decode(self.p, "hex"))


class ByteStringTester(unittest.TestCase):
    p1 = 'F10E323511122213541513A2D21F161C3621B8'
    p2 = '0305E8F02398A9'

    def test_variable_length_bytestring(self):
        class VarLenPacket(SerdepaPacket):
            _fields_ = (
                ("hdr", nx_uint16),
                ("tail", ByteString())
            )
        packet = VarLenPacket()
        try:
            packet.deserialize(decode(self.p1, "hex"))
        except ValueError as e:
            self.fail("Variable length ByteString deserializing failed with message: {}".format(e))
        self.assertTrue(isinstance(packet.tail, ByteString))
        self.assertEqual(packet.hdr, 0xF10E)
        self.assertEqual(packet.tail, 0x323511122213541513A2D21F161C3621B8)
        self.assertEqual(packet.serialize(), decode(self.p1, "hex"))

    def test_fixed_length_bytestring(self):
        class FixLenPacket(SerdepaPacket):
            _fields_ = (
                ('hdr', nx_uint8),
                ('tail', ByteString(6))
            )
        packet = FixLenPacket()
        packet.deserialize(decode(self.p2, "hex"))
        self.assertEqual(packet.hdr, 0x03)
        self.assertEqual(packet.tail, 0x05E8F02398A9)
        self.assertEqual(packet.serialize(), decode(self.p2, "hex"))

    def test_length_object_defined_length_bytestring(self):
        class LenObjLenPacket(SerdepaPacket):
            _fields_ = (
                ('hdr', nx_uint8),
                ('length', Length(nx_uint8, 'tail')),
                ('tail', ByteString())
            )
        packet = LenObjLenPacket()
        packet.deserialize(decode(self.p2, "hex"))
        self.assertEqual(packet.hdr, 0x03)
        self.assertEqual(packet.length, 5)
        self.assertEqual(packet.tail, 0xE8F02398A9)
        self.assertEqual(str(packet.tail), 'E8F02398A9')


class BigTypeTester(unittest.TestCase):
    p1 = '11FF00FF00FF00FF00'

    def test_nx_uint64(self):
        class Packet(SerdepaPacket):
            _fields_ = (
                ('header', nx_uint8),
                ('guid', nx_uint64)
            )

        packet = Packet()
        packet.deserialize(decode(self.p1, "hex"))
        self.assertEqual(packet.header, 0x11)
        self.assertEqual(packet.guid, 0xFF00FF00FF00FF00)

    def test_nx_int64(self):
        class Packet(SerdepaPacket):
            _fields_ = (
                ('header', nx_uint8),
                ('guid', nx_int64)
            )

        packet = Packet()
        packet.deserialize(decode(self.p1, "hex"))
        self.assertEqual(packet.header, 0x11)
        self.assertEqual(packet.guid, 0-0x00FF00FF00FF00FF-1)

    def test_uint64(self):
        class Packet(SerdepaPacket):
            _fields_ = (
                ('header', nx_uint8),
                ('guid', uint64)
            )

        packet = Packet()
        packet.deserialize(decode(self.p1, "hex"))
        self.assertEqual(packet.header, 0x11)
        self.assertEqual(packet.guid, 0x00FF00FF00FF00FF)

    def test_int64(self):
        class Packet(SerdepaPacket):
            _fields_ = (
                ('header', nx_uint8),
                ('guid', int64)
            )

        packet = Packet()
        packet.deserialize(decode(self.p1, "hex"))
        self.assertEqual(packet.header, 0x11)
        self.assertEqual(packet.guid, 0x00FF00FF00FF00FF)


if __name__ == '__main__':
    unittest.main()
