"""Part 1: user authentication.

Each public function returns 1 (OKAY) or -1 (ERROR). The password file holds
one line per user::

    username:salthex:hashhex\\n

where salt is 32 random bytes and hash = PBKDF2-HMAC-SHA1(password, salt,
20,000 iterations, 20 bytes). Passwords are never stored.
"""

import os

from . import config, crypto, util
from .config import ERR, OK


def _text(value) -> str | None:
    """Accept str or bytes; None for anything else or non-ASCII bytes."""
    if isinstance(value, bytes):
        try:
            return value.decode("ascii")
        except UnicodeDecodeError:
            return None
    return value if isinstance(value, str) else None


def _valid_string(s, lo: int, hi: int, extra: str) -> bool:
    s = _text(s)
    if s is None or not lo <= len(s) <= hi:
        return False
    return all((c.isascii() and c.isalnum()) or c in extra for c in s)


def valid_username(u) -> bool:
    return _valid_string(u, config.USER_MIN, config.USER_MAX, "")


def valid_password(p) -> bool:
    return _valid_string(p, config.PASS_MIN, config.PASS_MAX, config.PASS_EXTRA)


def _valid_pfile(pfile) -> bool:
    return isinstance(pfile, (str, bytes, os.PathLike)) and len(os.fspath(pfile)) > 0


def _hash_password(p: str, salt: bytes) -> bytes:
    return crypto.pbkdf2_sha1(p.encode("ascii"), salt)


def _line_user(line: bytes) -> bytes:
    """The username field of a passwd line (text before the first ':'), or b'' if malformed."""
    line = line.split(b"\r", 1)[0].split(b"\n", 1)[0]
    head, sep, _ = line.partition(b":")
    return head if sep else b""


def _find_user(u: str, pfile):
    """(1, salt, hash) if found, (0, None, None) if not, (ERR, None, None) for a malformed entry."""
    data = util.read_all(pfile)
    if data is None:
        return 0, None, None
    ub = u.encode("ascii")
    for line in data.split(b"\n"):
        if _line_user(line) != ub:
            continue
        fields = line.rstrip(b"\r").split(b":")
        if len(fields) != 3:
            return ERR, None, None
        try:
            salt = util.from_hex(fields[1].decode("ascii"), config.SALT_LEN)
            hashed = util.from_hex(fields[2].decode("ascii"), config.HASH_LEN)
        except UnicodeDecodeError:
            return ERR, None, None
        if salt is None or hashed is None:
            return ERR, None, None
        return 1, salt, hashed
    return 0, None, None


def _make_entry(u: str, p: str) -> bytes:
    """``u:salthex:hashhex\\n`` with a fresh random salt."""
    salt = crypto.gen_random(config.SALT_LEN)
    hashed = _hash_password(p, salt)
    return f"{u}:{util.to_hex(salt)}:{util.to_hex(hashed)}\n".encode("ascii")


def _rewrite_user(u: str, entry: bytes | None, pfile) -> int:
    """Rewrite pfile with u's line replaced by ``entry`` (or dropped if None), atomically."""
    data = util.read_all(pfile)
    if data is None:
        return ERR
    ub = u.encode("ascii")
    out = []
    for line in data.splitlines(keepends=True):
        if _line_user(line) == ub:
            if entry is not None:
                out.append(entry)
        else:
            out.append(line)
    return OK if util.write_atomic(pfile, b"".join(out)) else ERR


def register_user(u, p, pfile) -> int:
    if not valid_username(u) or not valid_password(p) or not _valid_pfile(pfile):
        return ERR
    u, p = _text(u), _text(p)
    found, _, _ = _find_user(u, pfile)
    if found != 0:
        return ERR
    try:
        with open(pfile, "ab") as f:
            f.write(_make_entry(u, p))
    except OSError:
        return ERR
    return OK


def is_user_valid(u, pfile) -> int:
    if not valid_username(u) or not _valid_pfile(pfile):
        return ERR
    found, _, _ = _find_user(_text(u), pfile)
    return OK if found == 1 else ERR


def match_user(u, p, pfile) -> int:
    if not valid_username(u) or not valid_password(p) or not _valid_pfile(pfile):
        return ERR
    u, p = _text(u), _text(p)
    found, salt, stored = _find_user(u, pfile)
    if found != 1:
        return ERR
    return OK if crypto.equal(_hash_password(p, salt), stored) else ERR


def delete_user(u, p, pfile) -> int:
    if match_user(u, p, pfile) != OK:
        return ERR
    return _rewrite_user(_text(u), None, pfile)


def change_user_password(u, p, pn, pfile) -> int:
    if not valid_password(pn) or match_user(u, p, pfile) != OK:
        return ERR
    u, pn = _text(u), _text(pn)
    return _rewrite_user(u, _make_entry(u, pn), pfile)
