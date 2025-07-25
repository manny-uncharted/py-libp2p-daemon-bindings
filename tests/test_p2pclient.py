import io

import anyio
import pytest
from google.protobuf.message import EncodeError
from multiaddr import Multiaddr, protocols
from anyio.abc import SocketAttribute

import p2pclient.pb.p2pd_pb2 as p2pd_pb
from p2pclient import config
from p2pclient.control import parse_conn_protocol
from p2pclient.p2pclient import ControlClient, DaemonConnector
from p2pclient.serialization import write_unsigned_varint
from p2pclient.utils import read_pbmsg_safe, write_pbmsg


class MockReaderWriter(io.BytesIO):
    async def receive_exactly(self, n):
        await anyio.sleep(0)
        return self.read(n)

    async def receive(self, n=4096):
        await anyio.sleep(0)
        return self.read(n)

    async def send(self, b):
        await anyio.sleep(0)
        return self.write(b)


@pytest.mark.parametrize(
    "maddr_str, expected_proto",
    (("/unix/123", protocols.P_UNIX), ("/ip4/127.0.0.1/tcp/7777", protocols.P_IP4)),
)
def test_parse_conn_protocol_valid(maddr_str, expected_proto):
    assert parse_conn_protocol(Multiaddr(maddr_str)) == expected_proto


@pytest.mark.parametrize(
    "maddr_str",
    (
        "/p2p/QmbHVEEepCi7rn7VL7Exxpd2Ci9NNB6ifvqwhsrbRMgQFP",
        "/onion/timaq4ygg2iegci7:1234",
    ),
)
def test_parse_conn_protocol_invalid(maddr_str):
    maddr = Multiaddr(maddr_str)
    with pytest.raises(ValueError):
        parse_conn_protocol(maddr)


@pytest.mark.parametrize("control_maddr_str", ("/unix/123", "/ip4/127.0.0.1/tcp/6666"))
def test_client_ctor_control_maddr(control_maddr_str):
    c = DaemonConnector(Multiaddr(control_maddr_str))
    assert c.control_maddr == Multiaddr(control_maddr_str)


def test_client_ctor_default_control_maddr():
    c = DaemonConnector()
    assert c.control_maddr == Multiaddr(config.control_maddr_str)


@pytest.mark.parametrize("listen_maddr_str", ("/unix/123", "/ip4/127.0.0.1/tcp/6666"))
def test_control_client_ctor_listen_maddr(listen_maddr_str):
    c = ControlClient(
        daemon_connector=DaemonConnector(), listen_maddr=Multiaddr(listen_maddr_str)
    )
    assert c.listen_maddr == Multiaddr(listen_maddr_str)


def test_control_client_ctor_default_listen_maddr():
    c = ControlClient(daemon_connector=DaemonConnector())
    assert c.listen_maddr == Multiaddr(config.listen_maddr_str)


@pytest.mark.parametrize(
    "msg_bytes",
    (
        b'\x08\x00"R\n"\x12 F\xec\xd3p0X\xbeT\x95p^\xc8{\xc8\x13\xa3\x9c\x84d\x0b\x1b\xbb\xa0P\x98w\xc1\xb3\x981i\x16\x12\x02\xa2\x02\x12\x08\x04\x7f\x00\x00\x01\x06\xc7\xb6\x12\x08\x04\xc0\xa8\n\x87\x06\xc7\xb6\x12\x14)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\xc7\xb7',  # noqa: E501
        b'\x08\x00"R\n"\x12 \xd0\xf0 \x9a\xc6v\xa6\xd3;\xcac|\x95\x94\xa0\xe6:\nM\xc53T\x0e\xf0\x89\x8e(\x0c\xb9\xf7\\\xa5\x12\x02\xa2\x02\x12\x08\x04\x7f\x00\x00\x01\x06\xc9%\x12\x08\x04\xc0\xa8\n\x87\x06\xc9%\x12\x14)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\xc9&',  # noqa: E501
        b'\x08\x00"R\n"\x12 \xc3\xc3\xee\x18i\x8a\xde\x13\xa9y\x905\xeb\xcb\xa4\xd07\x14\xbe\xf4\xf8\x1b\xe8[g94\x94\xe3f\x18\xa9\x12\x02\xa2\x02\x12\x08\x04\x7f\x00\x00\x01\x06\xc9`\x12\x08\x04\xc0\xa8\n\x87\x06\xc9`\x12\x14)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\xc9a',  # noqa: E501
    ),
    # give test cases ids to prevent bytes from ruining the terminal
    ids=("pb example Response 0", "pb example Response 1", "pb example Response 2"),
)
@pytest.mark.anyio
async def test_read_pbmsg_safe_valid(msg_bytes):
    s = MockReaderWriter()
    await write_unsigned_varint(s, len(msg_bytes))
    s.write(msg_bytes)
    # reset the offset back to the beginning
    s.seek(0, 0)
    pb_msg = p2pd_pb.Response()
    await read_pbmsg_safe(s, pb_msg)
    assert pb_msg.SerializeToString() == msg_bytes



@pytest.mark.anyio
async def test_read_pbmsg_safe_readexactly_fails():
    host = "127.0.0.1"
    # port = 5566
    # port = 5567
    # port = 3000
    event = anyio.Event()

    async def handler_stream(stream):
        pb_msg = p2pd_pb.Response()
        try:
            await read_pbmsg_safe(stream, pb_msg)
        except anyio.IncompleteRead:
            event.set()
            return

    # listener = await anyio.create_tcp_listener(local_host=host, local_port=port)
    listener = await anyio.create_tcp_listener(local_host=host, local_port=0)
    # addr = listener.listeners[0].extra(SocketAttribute.local_address)
    # port = addr[1]
    host, port, *_ = listener.listeners[0].extra(SocketAttribute.local_address)

    async with anyio.create_task_group() as tg:
        # spin up server
        tg.start_soon(listener.serve, handler_stream)

        # connect and immediately close to trigger IncompleteRead on the server
        stream = await anyio.connect_tcp(host, port)
        await stream.aclose()

        with anyio.fail_after(5):
            await event.wait()

    await listener.aclose()


@pytest.mark.parametrize(
    "pb_msg, msg_bytes",
    (
        (
            p2pd_pb.Response(),
            b'Z\x08\x00*V\x08\x01\x12R\n"\x12 \x03\x8d\xf5\xd4(/#\xd6\xed\xa5\x1bU\xb8s\x8c\xfa\xad\xfc{\x04\xe3\xecw\xdeK\xc9,\xfe\x9c\x00:\xc8\x12\x02\xa2\x02\x12\x08\x04\x7f\x00\x00\x01\x06\xdea\x12\x08\x04\xc0\xa8\n\x87\x06\xdea\x12\x14)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\xdeb',  # noqa: E501
        ),
        (p2pd_pb.Request(), b"\x02\x08\x05"),
        (
            p2pd_pb.DHTRequest(),
            b'&\x08\x00\x12"\x12 \xd5\x0b\x18/\x9e\xa5G\x06.\xdd\xebW\xf0N\xf5\x0eW\xd3\xec\xdf\x06\x02\xe2\x89\x1e\xf0\xbb.\xc0\xbdE\xb8',  # noqa: E501
        ),
        (
            p2pd_pb.DHTResponse(),
            b'V\x08\x01\x12R\n"\x12 wy\xe2\xfa\x11\x9e\xe2\x84X]\x84\xf8\x98\xba\x8c\x8cQ\xd7,\xb59\x1e!G\x92\x86G{\x141\xe9\x1b\x12\x02\xa2\x02\x12\x08\x04\x7f\x00\x00\x01\x06\xdeA\x12\x08\x04\xc0\xa8\n\x87\x06\xdeA\x12\x14)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x06\xdeB',  # noqa: E501
        ),
        (
            p2pd_pb.StreamInfo(),
            b';\n"\x12 \xf6\x9e=\x9f\xc1J\xfe\x02\x93k!S\x80\xa0\xcc(s\xea&\xbe\xed\x9274qTI\xc1\xf7\xb6\xbd7\x12\x08\x04\x7f\x00\x00\x01\x06\xde\xc5\x1a\x0bprotocol123',  # noqa: E501
        ),
    ),
    ids=(
        "pb example Response",
        "pb example Request",
        "pb example DHTRequest",
        "pb example DHTResponse",
        "pb example StreamInfo",
    ),
)
@pytest.mark.anyio
async def test_write_pbmsg(pb_msg, msg_bytes):
    s_read = MockReaderWriter(msg_bytes)
    await read_pbmsg_safe(s_read, pb_msg)
    s_write = MockReaderWriter()
    await write_pbmsg(s_write, pb_msg)
    assert msg_bytes == s_write.getvalue()


@pytest.mark.parametrize(
    "pb_msg",
    (
        p2pd_pb.Response(),
        p2pd_pb.Request(),
        p2pd_pb.DHTRequest(),
        p2pd_pb.DHTResponse(),
        p2pd_pb.StreamInfo(),
    ),
)
@pytest.mark.anyio
async def test_write_pbmsg_missing_fields(pb_msg):
    with pytest.raises(EncodeError):
        await write_pbmsg(MockReaderWriter(), pb_msg)
