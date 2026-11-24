"""Parts 2-3: the SEFS file functions.

Every function authenticates u/p against the ``passwd`` file and, for a
single file, checks that u owns it. Returns 1 (OKAY) or -1 (ERROR) unless
noted. Files are split into a linked chain of max(1, ceil(size/1024))
encrypted chunks; a file of 1,024 bytes or less is the Part 2 simplified case.
"""

import os

from . import chunk, config, crypto, meta, util
from .auth import _text, match_user
from .config import ERR, OK


def _filename(f) -> str | None:
    f = _text(f)
    if f is None or not 0 < len(f) <= config.FILENAME_MAX:
        return None
    return f if all(c.isascii() and c.isalnum() for c in f) else None


def _nchunks(size: int) -> int:
    return 1 if size == 0 else (size + config.CHUNK_SIZE - 1) // config.CHUNK_SIZE


def _load_checked_meta(filename: str, owner: str | None, check_digest: bool) -> meta.Meta | None:
    """Load a registered file's meta; check its Master File List digest (if asked) and owner."""
    listed, want = meta.masterlist_get(filename)
    if listed != 1:
        return None
    loaded = meta.load(filename)
    if loaded is None:
        return None
    m, got = loaded
    if check_digest and not crypto.equal(want, got):
        return None
    if owner is not None and m.owner != owner:
        return None
    return m


def _authorize(f, u, p, check_digest: bool = True):
    """(filename, meta) if u/p are correct and u owns f; None otherwise."""
    filename = _filename(f)
    if filename is None or match_user(u, p, config.PASSWD_FILE) != OK:
        return None
    m = _load_checked_meta(filename, _text(u), check_digest)
    return (filename, m) if m is not None else None


def _verify_chain(m: meta.Meta) -> bytes | None:
    """Walk the chain verifying every chunk HMAC, next link, the chunk-count rule and the
    total size; return the whole plaintext, or None on any failure."""
    n = m.nchunks
    if not 0 <= m.size <= config.MAX_FILE_SIZE or n != _nchunks(m.size) or len(m.chunks) != n:
        return None
    if m.start != m.chunks[0].name or m.end != m.chunks[-1].name:
        return None
    parts = []
    total = 0
    for i, ref in enumerate(m.chunks):
        got = chunk.read(ref)
        if got is None:
            return None
        content, next_name = got
        if i + 1 < n:
            if len(content) != config.CHUNK_SIZE or next_name != m.chunks[i + 1].name:
                return None
        elif next_name != "":
            return None
        total += len(content)
        if total > m.size:
            return None
        parts.append(content)
    return b"".join(parts) if total == m.size else None


def _store_plaintext(filename: str, owner: str, data: bytes, old: meta.Meta | None) -> int:
    """Split data into the minimum number of chunks, each with a fresh key and IV; write the
    meta file and Master File List entry, and only then remove the old chunks."""
    if len(data) > config.MAX_FILE_SIZE or not util.ensure_dir(config.CHUNK_DIR):
        return ERR
    n = _nchunks(len(data))
    names = []
    for _ in range(n):
        name = chunk.new_name()
        if name is None or name in names:
            return ERR
        names.append(name)

    refs = []
    ok = False
    try:
        for i in range(n):
            block = data[i * config.CHUNK_SIZE:(i + 1) * config.CHUNK_SIZE]
            ref = chunk.write(names[i], names[i + 1] if i + 1 < n else None, block)
            if ref is None:
                return ERR
            refs.append(ref)
        m = meta.Meta(owner, n, len(data), names[0], names[-1], refs)
        if not meta.save(filename, m):
            return ERR
        ok = True
    finally:
        if not ok:
            for ref in refs:
                chunk.delete(ref.name)
    if old is not None:
        for ref in old.chunks:
            chunk.delete(ref.name)
    return OK


def create_file(f, u, p) -> int:
    filename = _filename(f)
    if filename is None or match_user(u, p, config.PASSWD_FILE) != OK:
        return ERR
    listed, _ = meta.masterlist_get(filename)
    if listed != 0 or os.path.exists(util.meta_path(filename)):
        return ERR
    return _store_plaintext(filename, _text(u), b"", None)


def encrypt_file(f, u, p) -> int:
    """Encrypt the plaintext file ``f`` from disk into SEFS. If f is already in SEFS,
    only its owner may replace it."""
    filename = _filename(f)
    if filename is None or match_user(u, p, config.PASSWD_FILE) != OK:
        return ERR
    owner = _text(u)
    listed, _ = meta.masterlist_get(filename)
    if listed < 0:
        return ERR
    old = None
    if listed:
        old = _load_checked_meta(filename, owner, check_digest=False)
        if old is None:
            return ERR
    elif os.path.exists(util.meta_path(filename)):
        return ERR
    data = util.read_all(filename)
    if data is None:
        return ERR
    r = _store_plaintext(filename, owner, data, old)
    if r == OK and config.REMOVE_PLAINTEXT:
        util.remove(filename)
    return r


def decrypt_file(f, pf, u, p) -> int:
    """Verify the whole file, then write its plaintext to ``pf``."""
    pf = _text(pf) if isinstance(pf, bytes) else pf
    if not isinstance(pf, (str, os.PathLike)) or not os.fspath(pf):
        return ERR
    auth = _authorize(f, u, p)
    if auth is None:
        return ERR
    data = _verify_chain(auth[1])
    if data is None:
        return ERR
    return OK if util.write_atomic(pf, data) else ERR


def read_from_file(f, position, length, u, p) -> bytes | None:
    """``length`` bytes from ``position``; None on any error, including reading past the end."""
    if not isinstance(position, int) or not isinstance(length, int) or position < 0 or length < 0:
        return None
    auth = _authorize(f, u, p)
    if auth is None:
        return None
    data = _verify_chain(auth[1])
    if data is None or position > len(data) or length > len(data) - position:
        return None
    return data[position:position + length]


def write_to_file(f, position, content, u, p) -> int:
    """Insert ``content`` at ``position`` (0..size); later content shifts forward."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    if not isinstance(content, (bytes, bytearray)) or not isinstance(position, int) or position < 0:
        return ERR
    auth = _authorize(f, u, p)
    if auth is None:
        return ERR
    filename, m = auth
    data = _verify_chain(m)
    if data is None or position > len(data) or len(data) + len(content) > config.MAX_FILE_SIZE:
        return ERR
    if not content:
        return OK
    new = data[:position] + bytes(content) + data[position:]
    return _store_plaintext(filename, m.owner, new, m)


def file_size(f, u, p) -> int:
    """File size in bytes, or -1."""
    auth = _authorize(f, u, p)
    return auth[1].size if auth is not None else ERR


def file_integrity_check(f, u, p) -> int:
    """Recompute the meta digest and every chunk HMAC and link."""
    auth = _authorize(f, u, p)
    if auth is None:
        return ERR
    return OK if _verify_chain(auth[1]) is not None else ERR


def delete_file(f, u, p) -> int:
    # No digest check: an owner may still delete a file whose meta digest was tampered with.
    auth = _authorize(f, u, p, check_digest=False)
    if auth is None:
        return ERR
    filename, m = auth
    for ref in m.chunks:
        chunk.delete(ref.name)
    if not util.remove(util.meta_path(filename)):
        return ERR
    return OK if meta.masterlist_put(filename, None) else ERR


def system_health_check(u, p) -> int:
    """Integrity-check every file in the Master File List; -1 if any fails."""
    if match_user(u, p, config.PASSWD_FILE) != OK:
        return ERR
    names = meta.masterlist_names()
    if names is None:
        return ERR
    healthy = True
    for name in names:
        filename = _filename(name)
        m = _load_checked_meta(filename, None, True) if filename else None
        if m is None or _verify_chain(m) is None:
            healthy = False
    return OK if healthy else ERR
