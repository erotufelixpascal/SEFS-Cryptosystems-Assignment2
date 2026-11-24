"""File and hex helpers. Every file is handled in binary mode with ``\\n`` line
endings, so files are byte-identical on Windows and Linux."""

import os
import string
from pathlib import Path

from . import config

_HEX = set(string.hexdigits)


def read_all(path) -> bytes | None:
    try:
        with open(path, "rb") as f:
            return f.read()
    except OSError:
        return None


def write_atomic(path, data: bytes) -> bool:
    """Write to ``path.tmp`` and then replace ``path``, so a crash never leaves a half-written file."""
    tmp = f"{path}.tmp"
    try:
        with open(tmp, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
        return True
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return False


def remove(path) -> bool:
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def ensure_dir(path) -> bool:
    p = Path(path)
    if p.exists():
        return p.is_dir()
    try:
        p.mkdir()
        return True
    except OSError:
        return False


def to_hex(data: bytes) -> str:
    h = data.hex()
    return h.upper() if config.HEX_UPPER else h


def from_hex(text: str, n: int) -> bytes | None:
    """Decode exactly ``n`` bytes of hex (either case); None if malformed."""
    if len(text) != 2 * n or not is_hex_string(text):
        return None
    return bytes.fromhex(text)


def is_hex_string(text: str) -> bool:
    return len(text) > 0 and all(c in _HEX for c in text)


def load_master_key() -> tuple[bytes, bytes] | None:
    """Returns (key, iv) from master.key, or None if it is missing or the wrong size."""
    buf = read_all(config.MASTER_KEY_FILE)
    if buf is None or len(buf) != config.KEY_LEN + config.IV_LEN:
        return None
    return buf[: config.KEY_LEN], buf[config.KEY_LEN:]


def meta_path(filename: str) -> str:
    return f"{filename}{config.META_EXT}"


def chunk_path(name: str) -> str:
    return os.path.join(config.CHUNK_DIR, name)
