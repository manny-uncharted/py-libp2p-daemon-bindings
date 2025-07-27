import logging
import socket
from contextlib import closing

import anyio
from anyio.abc import ByteStream
from google.protobuf.message import Message as PBMessage

from .exceptions import ControlFailure
from .pb import p2pd_pb2 as p2pd_pb
from .serialization import (
    _recv_exactly,
    read_unsigned_varint,
    write_unsigned_varint,
)

# Type alias for compatibility
SocketStream = ByteStream

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def raise_if_failed(response: p2pd_pb.Response) -> None:
    if response.type == p2pd_pb.Response.ERROR:
        raise ControlFailure(f"connect failed. msg={response.error.msg}")


async def write_pbmsg(stream: SocketStream, pbmsg: PBMessage) -> None:
    size = pbmsg.ByteSize()
    await write_unsigned_varint(stream, size)
    msg_bytes: bytes = pbmsg.SerializeToString()
    await stream.send(msg_bytes)
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("write_pbmsg (%d bytes): %s", size, msg_bytes.hex())


async def read_pbmsg_safe(stream: SocketStream, pbmsg: PBMessage) -> None:
    # Length prefix
    # length = await read_unsigned_varint(stream)
    # msg_bytes = await _recv_exactly(stream, length)

    with anyio.fail_after(1):
        length = await read_unsigned_varint(stream)

    with anyio.fail_after(2):
        msg_bytes = await _recv_exactly(stream, length)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("read_pbmsg (%d bytes): %s", length, msg_bytes.hex())

    pbmsg.ParseFromString(msg_bytes)


def get_unused_tcp_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("localhost", 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]
