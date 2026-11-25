"""P-002: encryption round-trip tests, written from CONTEXT.md only."""

import pytest

SMALL = b"hello SEFS world"
BINARY = bytes(range(256)) * 3          # 768 bytes, every byte value incl. 0x00, \r, \n
TRAILING_ZEROS = b"abc" + b"\x00" * 10  # padding is 0x00, so real trailing zeros must survive
CRLF = b"line1\r\nline2\nline3\r\n"

CONTENTS = {
    "empty": b"",
    "one_byte": b"x",
    "small": SMALL,
    "binary": BINARY,
    "trailing_zeros": TRAILING_ZEROS,
    "all_zeros": b"\x00" * 100,
    "crlf": CRLF,
}


def _encrypt(sefs, workdir, user, name, data):
    u, p = user
    (workdir / name).write_bytes(data)
    assert sefs.encrypt_file(name, u, p) == 1


# Part 2 s.3 create_file: stores an empty file (size 0); file_size reports it from the meta file.
def test_create_file_is_empty(sefs, user):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.file_size("notes", u, p) == 0


# Part 2 s.3 create_file + decrypt_file: an empty file decrypts to an empty plaintext file.
def test_create_then_decrypt_empty(sefs, user, workdir):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.decrypt_file("notes", "out.bin", u, p) == 1
    assert (workdir / "out.bin").read_bytes() == b""


# Part 2 s.3 read_from_file: None when reading past the end - any read of an empty file with n >= 1.
def test_read_from_empty_file_past_end(sefs, user):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.read_from_file("notes", 0, 1, u, p) is None


# Part 2 s.3 encrypt_file / decrypt_file: decrypt_file writes exactly the stored plaintext (empty, small, binary).
@pytest.mark.parametrize("key", list(CONTENTS))
def test_encrypt_decrypt_round_trip(sefs, user, workdir, key):
    u, p = user
    data = CONTENTS[key]
    _encrypt(sefs, workdir, user, "doc", data)
    assert sefs.decrypt_file("doc", "out.bin", u, p) == 1
    assert (workdir / "out.bin").read_bytes() == data


# Part 2 s.3 file_size: size from the meta file equals the plaintext length.
@pytest.mark.parametrize("key", list(CONTENTS))
def test_encrypt_file_size(sefs, user, workdir, key):
    u, p = user
    data = CONTENTS[key]
    _encrypt(sefs, workdir, user, "doc", data)
    assert sefs.file_size("doc", u, p) == len(data)


# Part 2 s.3 read_from_file: returns n bytes from pos as bytes; whole-file read equals the plaintext.
@pytest.mark.parametrize("key", [k for k in CONTENTS if CONTENTS[k]])
def test_encrypt_read_whole(sefs, user, workdir, key):
    u, p = user
    data = CONTENTS[key]
    _encrypt(sefs, workdir, user, "doc", data)
    got = sefs.read_from_file("doc", 0, len(data), u, p)
    assert isinstance(got, bytes)
    assert got == data


# Part 2 demo: read_from_file("doc1", 6, 4) == b'SEFS'; read past end -> None.
def test_demo_partial_reads(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc1", SMALL)
    assert sefs.read_from_file("doc1", 6, 4, u, p) == b"SEFS"
    assert sefs.read_from_file("doc1", 10, 100, u, p) is None
    # assert sefs.read_from_file("doc1", 10, 6, u, p) == b"world"   # exactly to the end is fine
    assert sefs.read_from_file("doc1", 10, 6, u, p) == b" world"   # exactly to the end (includes the space)
    assert sefs.read_from_file("doc1", 10, 7, u, p) is None       # one byte past the end


# Part 2 s.3 read_from_file: every single-byte slice of a binary file is returned exactly.
def test_binary_every_byte_position(sefs, user, workdir):
    u, p = user
    data = bytes(range(256))
    _encrypt(sefs, workdir, user, "bin", data)
    for pos in range(256):
        assert sefs.read_from_file("bin", pos, 1, u, p) == data[pos:pos + 1]


# Part 2 demo: create, write b"helloworld", insert b", " at 5, read -> b'hello, world'.
def test_demo_create_write_insert(sefs, user):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.write_to_file("notes", 0, b"helloworld", u, p) == 1
    assert sefs.write_to_file("notes", 5, b", ", u, p) == 1
    assert sefs.read_from_file("notes", 0, 12, u, p) == b"hello, world"
    assert sefs.file_size("notes", u, p) == 12


# Part 2 s.3 write_to_file + read/decrypt/file_size: written data (small and binary) is returned exactly.
@pytest.mark.parametrize("key", [k for k in CONTENTS if CONTENTS[k]])
def test_create_write_round_trip(sefs, user, workdir, key):
    u, p = user
    data = CONTENTS[key]
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.write_to_file("notes", 0, data, u, p) == 1
    assert sefs.file_size("notes", u, p) == len(data)
    assert sefs.read_from_file("notes", 0, len(data), u, p) == data
    assert sefs.decrypt_file("notes", "out.bin", u, p) == 1
    assert (workdir / "out.bin").read_bytes() == data


# Part 2 s.3: write_to_file accepts str, encoded as UTF-8.
def test_write_str_is_utf8(sefs, user):
    u, p = user
    text = "héllo €"
    enc = text.encode("utf-8")
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.write_to_file("notes", 0, text, u, p) == 1
    assert sefs.file_size("notes", u, p) == len(enc)
    assert sefs.read_from_file("notes", 0, len(enc), u, p) == enc


# Part 2 s.3 write_to_file inserts: old[:pos] + data + old[pos:] (start, middle, end of a binary file).
@pytest.mark.parametrize("pos", [0, 1, 128, 767, 768])
def test_insert_into_binary(sefs, user, workdir, pos):
    u, p = user
    _encrypt(sefs, workdir, user, "bin", BINARY)
    ins = b"\x00\xff\r\n"
    assert sefs.write_to_file("bin", pos, ins, u, p) == 1
    expected = BINARY[:pos] + ins + BINARY[pos:]
    assert sefs.file_size("bin", u, p) == len(expected)
    assert sefs.read_from_file("bin", 0, len(expected), u, p) == expected


# Part 2 s.3 encrypt_file: if f is already in SEFS, its owner may replace it - new content round-trips.
def test_encrypt_file_owner_replaces(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"first version")
    _encrypt(sefs, workdir, user, "doc", b"v2")
    assert sefs.file_size("doc", u, p) == 2
    assert sefs.read_from_file("doc", 0, 2, u, p) == b"v2"


# Part 2 s.3 decrypt_file: decrypting does not change the stored file; it can be read again afterwards.
def test_decrypt_does_not_alter_stored_file(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", BINARY)
    assert sefs.decrypt_file("doc", "out1.bin", u, p) == 1
    assert sefs.decrypt_file("doc", "out2.bin", u, p) == 1
    assert (workdir / "out1.bin").read_bytes() == BINARY
    assert (workdir / "out2.bin").read_bytes() == BINARY
    assert sefs.read_from_file("doc", 0, len(BINARY), u, p) == BINARY


# Part 2 s.3 encrypt_file reads from disk: later changes to the on-disk plaintext do not change SEFS content.
def test_stored_copy_independent_of_disk_plaintext(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", SMALL)
    (workdir / "doc").write_bytes(b"changed on disk")
    assert sefs.read_from_file("doc", 0, len(SMALL), u, p) == SMALL


# Part 2 s.5 "Show the encryption": the plaintext does not appear in any chunk file.
def test_plaintext_not_in_chunks(sefs, user, workdir, chunk_files):
    marker = b"SECRETMARKER-" * 20
    _encrypt(sefs, workdir, user, "doc", marker)
    files = chunk_files()
    assert files
    for f in files:
        assert b"SECRETMARKER" not in f.read_bytes()


# FILE_FORMAT s.4: the meta file is encrypted - the owner name and content do not appear in it.
def test_plaintext_not_in_meta(sefs, user, workdir):
    u, _ = user
    _encrypt(sefs, workdir, user, "doc", b"SECRETMARKER-" * 5)
    meta = (workdir / "doc.meta").read_bytes()
    assert b"SECRETMARKER" not in meta
    assert u.encode() not in meta


# Part 2 s.3: several files stored side by side each round-trip independently.
def test_multiple_files_independent(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "aaa", b"first file")
    _encrypt(sefs, workdir, user, "bbb", BINARY)
    assert sefs.create_file("ccc", u, p) == 1
    assert sefs.write_to_file("ccc", 0, b"third", u, p) == 1
    assert sefs.read_from_file("aaa", 0, 10, u, p) == b"first file"
    assert sefs.read_from_file("bbb", 0, len(BINARY), u, p) == BINARY
    assert sefs.read_from_file("ccc", 0, 5, u, p) == b"third"
