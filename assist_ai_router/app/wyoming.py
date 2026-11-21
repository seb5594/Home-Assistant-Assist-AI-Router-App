"""Dependency-free Wyoming framing.

An event is one JSON header line, optionally followed by extra JSON data and a binary
payload (PCM audio). Only what the speech gateway needs is implemented.
"""
import asyncio
import json
from urllib.parse import urlsplit

MAX_HEADER_BYTES = 65_536
MAX_DATA_BYTES = 1_048_576
MAX_PAYLOAD_BYTES = 1_048_576


class WireError(Exception):
    """The peer sent something that is not a valid Wyoming event."""


class Event:
    __slots__ = ("type", "data", "payload")

    def __init__(self, type, data=None, payload=b""):
        self.type, self.data, self.payload = type, data or {}, payload


def parse_uri(value):
    """Return (host, port) of a ``tcp://host:port`` address or raise ValueError."""
    parsed = urlsplit(value)
    port = parsed.port  # Raises ValueError for malformed or out-of-range ports.
    if (parsed.scheme != "tcp" or not parsed.hostname or not port or parsed.username
            or parsed.password or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("invalid_uri")
    return parsed.hostname, port


def _length(header, key, limit):
    value = header.get(key, 0)
    if type(value) is not int or not 0 <= value <= limit:
        raise WireError("invalid_" + key)
    return value


async def read_event(reader):
    """Return the next event, or None when the peer closed the connection between events."""
    try:
        line = await reader.readline()
    except ValueError:
        raise WireError("header_too_large") from None
    if not line:
        return None
    try:
        header = json.loads(line)
        if not isinstance(header, dict) or not isinstance(header.get("type"), str) or not header["type"]:
            raise ValueError()
        if not isinstance(header.get("data", {}), dict):
            raise ValueError()
    except (ValueError, UnicodeError):
        raise WireError("invalid_header") from None
    data_length = _length(header, "data_length", MAX_DATA_BYTES)
    payload_length = _length(header, "payload_length", MAX_PAYLOAD_BYTES)
    try:
        data = dict(header.get("data", {}))
        if data_length:
            extra = json.loads(await reader.readexactly(data_length))
            if not isinstance(extra, dict):
                raise ValueError()
            data.update(extra)
        payload = await reader.readexactly(payload_length) if payload_length else b""
    except asyncio.IncompleteReadError:
        raise WireError("truncated_event") from None
    except (ValueError, UnicodeError):
        raise WireError("invalid_data") from None
    return Event(header["type"], data, payload)


async def write_event(writer, event):
    header = {"type": event.type}
    data = json.dumps(event.data, ensure_ascii=False, separators=(",", ":")).encode() if event.data else b""
    if data:
        header["data_length"] = len(data)
    if event.payload:
        header["payload_length"] = len(event.payload)
    writer.write(json.dumps(header, separators=(",", ":")).encode() + b"\n" + data + event.payload)
    await writer.drain()
