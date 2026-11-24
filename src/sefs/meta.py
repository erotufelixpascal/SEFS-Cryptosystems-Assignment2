"""Meta files and the Master File List.

``F.meta`` is AES-128-CTR(master key, master IV) of the text::

    owner\\n chunk count\\n file size\\n start chunk\\n end chunk\\n
    name keyhex hmachex\\n   (one line per chunk, in chain order)

``masterlist`` is plaintext, one ``filename sha256hex\\n`` line per file,
where the digest is SHA-256 of the meta file bytes as stored.
"""

import os
from dataclasses import dataclass, field

from . import config, crypto, util
from .chunk import ChunkRef, _valid_name

MAX_CHUNKS = config.MAX_FILE_SIZE // config.CHUNK_SIZE + 1
_MAX_META_LEN = MAX_CHUNKS * 160 + 256


@dataclass
class Meta:
    owner: str
    nchunks: int
    size: int
    start: str
    end: str
    chunks: list[ChunkRef] = field(default_factory=list)


def _parse_int(s: str) -> int | None:
    if not 0 < len(s) <= 10 or not all("0" <= c <= "9" for c in s):
        return None
    return int(s)


def _parse(text: str) -> Meta | None:
    if not text.endswith("\n"):
        return None
    lines = text[:-1].split("\n")
    if len(lines) < 6:
        return None
    owner = lines[0]
    if not 0 < len(owner) <= config.USER_MAX:
        return None
    nchunks = _parse_int(lines[1])
    size = _parse_int(lines[2])
    if nchunks is None or not 1 <= nchunks <= MAX_CHUNKS:
        return None
    if size is None or size > config.MAX_FILE_SIZE:
        return None
    start, end = lines[3], lines[4]
    if not _valid_name(start) or not _valid_name(end):
        return None
    if len(lines) != 5 + nchunks:
        return None

    chunks = []
    for line in lines[5:]:
        parts = line.split(" ")
        if len(parts) != 3 or not _valid_name(parts[0]):
            return None
        key = util.from_hex(parts[1], config.KEY_LEN)
        mac = util.from_hex(parts[2], config.HMAC_LEN)
        if key is None or mac is None:
            return None
        chunks.append(ChunkRef(parts[0], key, mac))
    return Meta(owner, nchunks, size, start, end, chunks)


def _serialize(m: Meta) -> bytes:
    lines = [m.owner, str(m.nchunks), str(m.size), m.start, m.end]
    lines += [f"{c.name} {util.to_hex(c.key)} {util.to_hex(c.hmac)}" for c in m.chunks]
    return ("\n".join(lines) + "\n").encode("ascii")


def load(filename: str) -> tuple[Meta, bytes] | None:
    """Read and decrypt F.meta. Returns (meta, sha256 of the stored bytes), or None."""
    ct = util.read_all(util.meta_path(filename))
    if ct is None or not 0 < len(ct) <= _MAX_META_LEN:
        return None
    mk = util.load_master_key()
    if mk is None:
        return None
    pt = crypto.aes128_ctr(mk[0], mk[1], ct)
    try:
        text = pt.decode("ascii")
    except UnicodeDecodeError:
        return None
    if "\x00" in text:
        return None
    m = _parse(text)
    return (m, crypto.sha256(ct)) if m is not None else None


def save(filename: str, m: Meta) -> bool:
    """Encrypt and atomically write F.meta, then record its digest in the Master File List."""
    mk = util.load_master_key()
    if mk is None:
        return False
    ct = crypto.aes128_ctr(mk[0], mk[1], _serialize(m))
    if not util.write_atomic(util.meta_path(filename), ct):
        return False
    return masterlist_put(filename, crypto.sha256(ct))


# ---- Master File List: "filename sha256hex\n" per file ----

def _split_entry(line: str) -> tuple[str, str] | None:
    name, sep, hexdigest = line.partition(" ")
    if not sep or not name or len(hexdigest) != 2 * config.DIGEST_LEN:
        return None
    return name, hexdigest


def _read_list() -> str | None:
    data = util.read_all(config.MASTER_LIST)
    if data is None:
        return None
    try:
        return data.decode("ascii")
    except UnicodeDecodeError:
        return None


def masterlist_get(filename: str):
    """(1, digest) if listed, (0, None) if not, (ERR, None) on error."""
    if not os.path.exists(config.MASTER_LIST):
        return 0, None
    text = _read_list()
    if text is None:
        return config.ERR, None
    for line in text.split("\n")[:-1]:  # only '\n'-terminated lines count
        entry = _split_entry(line)
        if entry is not None and entry[0] == filename:
            digest = util.from_hex(entry[1], config.DIGEST_LEN)
            return (1, digest) if digest is not None else (config.ERR, None)
    return 0, None


def masterlist_put(filename: str, digest: bytes | None) -> bool:
    """Add or replace filename's entry; ``digest=None`` removes it. Malformed lines are dropped."""
    text = ""
    if os.path.exists(config.MASTER_LIST):
        text = _read_list()
        if text is None:
            return False
    out = []
    for line in text.split("\n")[:-1]:
        entry = _split_entry(line)
        if entry is None or entry[0] == filename:
            continue
        out.append(f"{entry[0]} {entry[1]}\n")
    if digest is not None:
        out.append(f"{filename} {util.to_hex(digest)}\n")
    return util.write_atomic(config.MASTER_LIST, "".join(out).encode("ascii"))


def masterlist_names() -> list[str] | None:
    """Every filename in the list; None if the list is malformed (itself an integrity failure)."""
    if not os.path.exists(config.MASTER_LIST):
        return []
    text = _read_list()
    if text is None or (text and not text.endswith("\n")):
        return None
    names = []
    for line in text.split("\n")[:-1]:
        entry = _split_entry(line)
        if entry is None:
            return None
        names.append(entry[0])
    return names
