import logging
from typing import Union

from anyio import IncompleteRead
from anyio.abc import ByteReceiveStream, ByteSendStream, SocketStream
from anyio.streams.buffered import BufferedByteReceiveStream

logger = logging.getLogger(__name__)

DEFAULT_MAX_BITS: int = 64


def _ensure_buffered(stream: ByteReceiveStream) -> BufferedByteReceiveStream:
    # Fast-path reuse
    if isinstance(stream, BufferedByteReceiveStream):
        return stream
    return BufferedByteReceiveStream(stream)


async def _recv_exactly(
    stream: Union[ByteReceiveStream, SocketStream], n: int
) -> bytes:
    """
    Compatibility shim:
      * If the object already has `receive_exactly`, just use it (works with your MockReaderWriter).
      * Else, if it has `receive`, wrap it once in BufferedByteReceiveStream.
      * Else, fall back to blocking `read()` if present (last resort for BytesIO-like fakes).
    """
    recv_exactly = getattr(stream, "receive_exactly", None)
    if recv_exactly is not None:
        return await recv_exactly(n)

    # ByteReceiveStream path
    if hasattr(stream, "receive"):
        buffered = BufferedByteReceiveStream(stream)  # one-off wrapper
        return await buffered.receive_exactly(n)

    # Sync fallback (rare in prod, but keeps tests happy)
    if hasattr(stream, "read"):
        data = stream.read()
        if len(data) != n:
            raise IncompleteRead()
        return data

    raise TypeError(f"Stream {stream!r} has no compatible receive API")


def _hexdump(b: bytes, width: int = 16) -> str:
    return " ".join(f"{x:02x}" for x in b)


async def write_unsigned_varint(
    stream: ByteSendStream,
    integer: int,
    max_bits: int = DEFAULT_MAX_BITS,
) -> None:
    max_int: int = 1 << max_bits
    if integer < 0:
        raise ValueError(f"negative integer: {integer}")
    if integer >= max_int:
        raise ValueError(f"integer too large: {integer}")

    # Emit bytes little-endian 7-bit groups with MSB as continuation flag
    while True:
        value: int = integer & 0x7F
        integer >>= 7
        if integer != 0:
            value |= 0x80
        byte = value.to_bytes(1, "big")
        await stream.send(byte)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("write_unsigned_varint -> %s", _hexdump(byte))
        if integer == 0:
            break


async def read_unsigned_varint(
    stream: ByteReceiveStream,
    max_bits: int = DEFAULT_MAX_BITS,
) -> int:
    max_int: int = 1 << max_bits
    iteration: int = 0
    result: int = 0

    while True:
        data = await _recv_exactly(stream, 1)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("read_unsigned_varint <- %s", _hexdump(data))

        c = data[0]
        value = c & 0x7F
        result |= value << (iteration * 7)
        cont = (c & 0x80) != 0
        iteration += 1

        if result >= max_int:
            raise ValueError(f"varint overflowed: {result}")

        if not cont:
            break

    return result
