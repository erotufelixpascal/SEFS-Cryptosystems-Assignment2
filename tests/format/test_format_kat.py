"""Known-answer tests for the on-disk format (interoperability guard).

These build passwd lines, chunk files and meta files by hand from the format
description in docs/FILE_FORMAT.md, using only hashlib / cryptography, and
check that SEFS reads them, and that what SEFS writes decodes the same way.
If another group's format differs from ours, these tests show where.

Part of the implementation scaffold, NOT one of the experiment arms.
"""

import hashlib
import hmac
from pathlib import Path

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


def ctr(key, iv, data):
    c = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
    return c.update(data) + c.finalize()


def master():
    raw = Path("master.key").read_bytes()
    return raw[:16], raw[16:]


def test_handmade_passwd_entry_is_accepted(sefs):
    salt = bytes(range(32))
    digest = hashlib.pbkdf2_hmac("sha1", b"Interop#2026", salt, 20000, 20)
    Path("passwd").write_bytes(f"group6user:{salt.hex()}:{digest.hex().upper()}\n".encode())
    assert sefs.match_user("group6user", "Interop#2026", "passwd") == 1  # uppercase hex is read too
    assert sefs.match_user("group6user", "Interop#2027", "passwd") == -1


def test_handmade_two_chunk_file_is_readable(sefs, user):
    u, p = user
    mk, miv = master()
    names = ["a" * 32, "b" * 32]
    data = [b"X" * 1024, b"tail"]
    refs = []
    Path("chunks").mkdir()
    for i, name in enumerate(names):
        nxt = names[i + 1].encode() if i + 1 < len(names) else b"NULL"
        body = nxt.ljust(32, b"\0") + len(data[i]).to_bytes(4, "big") + data[i].ljust(1024, b"\0")
        key, iv = bytes([i + 1]) * 16, bytes([i + 9]) * 16
        file = iv + ctr(key, iv, body)
        (Path("chunks") / name).write_bytes(file)
        refs.append(f"{name} {key.hex()} {hmac.new(key, file, hashlib.sha256).hexdigest()}")
    text = f"{u}\n2\n1028\n{names[0]}\n{names[1]}\n" + "\n".join(refs) + "\n"
    meta = ctr(mk, miv, text.encode())
    Path("hand.meta").write_bytes(meta)
    Path("masterlist").write_bytes(f"hand {hashlib.sha256(meta).hexdigest()}\n".encode())

    assert sefs.file_integrity_check("hand", u, p) == 1
    assert sefs.file_size("hand", u, p) == 1028
    assert sefs.read_from_file("hand", 1022, 6, u, p) == b"XXtail"


def test_written_chunk_and_meta_match_the_documented_layout(sefs, user):
    u, p = user
    Path("doc").write_bytes(b"hello")
    assert sefs.encrypt_file("doc", u, p) == 1
    mk, miv = master()
    meta_ct = Path("doc.meta").read_bytes()
    lines = ctr(mk, miv, meta_ct).decode().split("\n")
    assert lines[:3] == [u, "1", "5"] and lines[-1] == ""
    name, keyhex, machex = lines[5].split(" ")
    assert lines[3] == lines[4] == name and len(name) == 32 and name == name.lower()

    file = (Path("chunks") / name).read_bytes()
    assert len(file) == 16 + 32 + 4 + 1024
    key = bytes.fromhex(keyhex)
    assert hmac.new(key, file, hashlib.sha256).hexdigest() == machex
    body = ctr(key, file[:16], file[16:])
    assert body[:32] == b"NULL" + b"\0" * 28
    assert body[32:36] == (5).to_bytes(4, "big")
    assert body[36:41] == b"hello" and body[41:] == b"\0" * 1019

    assert Path("masterlist").read_bytes() == f"doc {hashlib.sha256(meta_ct).hexdigest()}\n".encode()
