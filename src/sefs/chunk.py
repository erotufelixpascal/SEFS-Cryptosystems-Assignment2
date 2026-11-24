"""One encrypted chunk.

A chunk file ``chunks/<32 hex chars>`` is exactly 1,076 bytes::

    IV (16, plaintext) || AES-128-CTR(chunk key, IV)( next name (32) || size (4, big-endian) || content (1,024) )

The chunk's HMAC-SHA256(chunk key, whole file) is stored in the meta file,
not in the chunk.
"""

import os
from dataclasses import dataclass

from . import config, crypto, util

_CONTENT_OFF = config.NEXT_FIELD_LEN + config.SIZE_FIELD_LEN


@dataclass
class ChunkRef:
    """One ``name key hmac`` line of a meta file."""
    name: str
    key: bytes
    hmac: bytes


def _valid_name(name) -> bool:
    return isinstance(name, str) and len(name) == config.CHUNK_NAME_LEN and util.is_hex_string(name)


def new_name() -> str | None:
    """A random chunk name not already on disk."""
    for _ in range(8):
        name = util.to_hex(crypto.gen_random(config.CHUNK_NAME_BYTES))
        if not os.path.exists(util.chunk_path(name)):
            return name
    return None


def write(name: str, next_name: str | None, data: bytes) -> ChunkRef | None:
    """Encrypt ``data`` (at most CHUNK_SIZE bytes) under a fresh key and IV and write chunk ``name``.

    ``next_name`` is the next chunk's name, or None for the last chunk.
    """
    if len(data) > config.CHUNK_SIZE or not _valid_name(name):
        return None
    if next_name is not None and not _valid_name(next_name):
        return None

    link = config.NULL_NAME if next_name is None else next_name.encode("ascii")
    body = (
        link.ljust(config.NEXT_FIELD_LEN, b"\x00")
        + len(data).to_bytes(config.SIZE_FIELD_LEN, "big")
        + data.ljust(config.CHUNK_SIZE, bytes([config.PAD_BYTE]))
    )
    # Fresh key and IV on every write, so a CTR keystream is never reused.
    key = crypto.gen_random(config.KEY_LEN)
    iv = crypto.gen_random(config.IV_LEN)
    file = iv + crypto.aes128_ctr(key, iv, body)
    mac = crypto.hmac_sha256(key, file)
    if not util.write_atomic(util.chunk_path(name), file):
        return None
    return ChunkRef(name, key, mac)


def read(ref: ChunkRef) -> tuple[bytes, str] | None:
    """Verify the HMAC first, then decrypt.

    Returns (content, next_name) where next_name is "" for the last chunk,
    or None if the chunk is missing, tampered with or malformed.
    """
    file = util.read_all(util.chunk_path(ref.name))
    if file is None or len(file) != config.CHUNK_FILE_LEN:
        return None
    # Integrity before decryption
    if not crypto.equal(crypto.hmac_sha256(ref.key, file), ref.hmac):
        return None
    iv, ct = file[: config.IV_LEN], file[config.IV_LEN:]
    body = crypto.aes128_ctr(ref.key, iv, ct)

    link = body[: config.NEXT_FIELD_LEN]
    if link.startswith(config.NULL_NAME):
        if any(link[len(config.NULL_NAME):]):
            return None
        next_name = ""
    else:
        name_bytes = link[: config.CHUNK_NAME_LEN]
        if any(link[config.CHUNK_NAME_LEN:]):
            return None
        try:
            next_name = name_bytes.decode("ascii")
        except UnicodeDecodeError:
            return None
        if not _valid_name(next_name):
            return None

    size = int.from_bytes(body[config.NEXT_FIELD_LEN:_CONTENT_OFF], "big")
    if size > config.CHUNK_SIZE:
        return None
    content = body[_CONTENT_OFF:]
    if any(b != config.PAD_BYTE for b in content[size:]):
        return None
    return content[:size], next_name


def delete(name: str) -> bool:
    return util.remove(util.chunk_path(name))
