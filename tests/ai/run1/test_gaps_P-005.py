"""P-005: tests for CONTEXT.md rules not yet checked by P-001..P-004.

Review of P-001..P-004 against CONTEXT.md - rules with no test yet:
  G1  Part 2 s.2 _filename: letters and digits only, 1-20 characters (all file functions).
  G2  Part 2 s.4 "Validate every input": types, negative / out-of-range positions and lengths
      for read_from_file and write_to_file; non-bytes/str data.
  G3  Part 2 s.3 delete_file: removes chunks, the meta file AND the Master File List entry
      (only the chunk part was tested); deleting a missing file; the name is reusable.
  G4  Part 2 s.3 encrypt_file: plaintext file missing on disk; replacing a file leaves no orphan chunks.
  G5  Part 2 s.4 / FILE_FORMAT s.3: fresh key and IV whenever a chunk is (re-)encrypted - same
      plaintext never gives the same chunk bytes.
  G6  Part 3 s.4 "last chunk padded": every chunk file has the same size whatever its content length.
  G7  Part 3 s.2.2 step 5: a failed operation leaves the old file untouched (rejected writes).
  G8  FILE_FORMAT file list: <name>.meta and chunks/ live in the current working directory.
  G9  Part 2 s.3 file_size updates after writes (only checked after single writes so far)
      and read_from_file returns n bytes exactly at the end of the file.

Deliberately NOT tested (dagger-marked or not observable through the API):
  - PBKDF2 iteration count / hash length, chunk/meta/masterlist byte layouts, chunk name format,
    masterlist plaintext format, hex case (all marked with a dagger in FILE_FORMAT.md).
  - Constant-time comparison, fsync/os.replace crash safety for chunks/meta/masterlist,
    "HMAC checked before decrypting" (internal order), use of secrets/CSPRNG.
  - _verify_chain rejecting a meta file with a bad count/size/start/end (needs a hand-built
    meta file, i.e. the dagger-marked meta format).
"""

import pytest

OTHER_USER = "bobuser1"
OTHER_PASS = "B0bPassw0rd#"


def _encrypt(sefs, workdir, user, name, data):
    u, p = user
    (workdir / name).write_bytes(data)
    assert sefs.encrypt_file(name, u, p) == 1


# ---------------- G1: file names ----------------

# Part 2 s.2 _filename: letters and digits only, 1-20 characters - accepted names.
@pytest.mark.parametrize("name", ["a", "Z", "7", "abc123", "A" * 20, "MixedCase09"])
def test_valid_file_names_accepted(sefs, user, name):
    u, p = user
    assert sefs.create_file(name, u, p) == 1
    assert sefs.file_size(name, u, p) == 0


# Part 2 s.2 _filename: empty, too long (21), or non letter/digit characters are rejected by create_file.
@pytest.mark.parametrize("name", [
    "", "A" * 21, "my.doc", "a_b", "a-b", "a b", "../x", "a/b", "a\\b", "x.meta",
    "café", "n１", "abc\n",
])
def test_invalid_file_names_rejected_create(sefs, user, workdir, name):
    u, p = user
    assert sefs.create_file(name, u, p) == -1


# Part 2 s.2 _filename applies to encrypt_file too (the on-disk file exists, but the name is invalid).
@pytest.mark.parametrize("name", ["my.doc", "a_b", "A" * 21])
def test_invalid_file_names_rejected_encrypt(sefs, user, workdir, name):
    u, p = user
    (workdir / name).write_bytes(b"data")
    assert sefs.encrypt_file(name, u, p) == -1


# Part 2 s.2 _filename / s.4 "Validate every input": invalid names or wrong types are rejected by the
# other per-file functions.
@pytest.mark.parametrize("name", ["", "A" * 21, "my.doc", None, 123])
def test_invalid_file_names_rejected_elsewhere(sefs, user, workdir, name):
    u, p = user
    assert sefs.read_from_file(name, 0, 1, u, p) is None
    assert sefs.write_to_file(name, 0, b"x", u, p) == -1
    assert sefs.file_size(name, u, p) == -1
    assert sefs.file_integrity_check(name, u, p) == -1
    assert sefs.delete_file(name, u, p) == -1
    assert sefs.decrypt_file(name, "out.bin", u, p) == -1


# Part 2 s.3: functions on a name that is valid but not in SEFS fail.
def test_unknown_file(sefs, user):
    u, p = user
    assert sefs.read_from_file("nothere", 0, 1, u, p) is None
    assert sefs.write_to_file("nothere", 0, b"x", u, p) == -1
    assert sefs.file_size("nothere", u, p) == -1
    assert sefs.file_integrity_check("nothere", u, p) == -1
    assert sefs.delete_file("nothere", u, p) == -1
    assert sefs.decrypt_file("nothere", "out.bin", u, p) == -1


# ---------------- G2: positions, lengths, types ----------------

# Part 2 s.4 "negative or out-of-range positions and lengths" for read_from_file.
@pytest.mark.parametrize("pos,n", [(-1, 1), (0, -1), (-5, 3), (16, 1), (100, 1), (0, 17)])
def test_read_invalid_pos_or_len(sefs, user, workdir, pos, n):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello SEFS world")
    assert sefs.read_from_file("doc", pos, n, u, p) is None


# Part 2 s.4 "Validate every input ... types": non-integer pos / n for read_from_file.
@pytest.mark.parametrize("pos,n", [("0", 1), (0, "1"), (None, 1), (0, None), (0.0, 1), (0, 1.0)])
def test_read_wrong_types(sefs, user, workdir, pos, n):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello SEFS world")
    assert sefs.read_from_file("doc", pos, n, u, p) is None


# Part 2 s.3/s.4 write_to_file: negative pos and pos beyond the end are rejected.
@pytest.mark.parametrize("pos", [-1, -100, 17, 1000])
def test_write_invalid_pos(sefs, user, workdir, pos):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello SEFS world")
    assert sefs.write_to_file("doc", pos, b"x", u, p) == -1
    assert sefs.read_from_file("doc", 0, 16, u, p) == b"hello SEFS world"


# Part 2 s.3 write_to_file accepts bytes or str only; s.4 validates types.
@pytest.mark.parametrize("data", [None, 123, 1.5, ["x"]])
def test_write_wrong_data_type(sefs, user, workdir, data):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello")
    assert sefs.write_to_file("doc", 0, data, u, p) == -1
    assert sefs.read_from_file("doc", 0, 5, u, p) == b"hello"


# Part 2 s.4: non-integer write positions are rejected.
@pytest.mark.parametrize("pos", ["0", None, 0.0])
def test_write_wrong_pos_type(sefs, user, workdir, pos):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello")
    assert sefs.write_to_file("doc", pos, b"x", u, p) == -1
    assert sefs.file_size("doc", u, p) == 5


# ---------------- G3: delete_file ----------------

# Part 2 s.3 delete_file: removes chunks, meta file and Master File List entry; demo returns 1.
def test_delete_file_removes_everything(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"x" * 1500)
    assert (workdir / "doc.meta").exists()
    assert sefs.delete_file("doc", u, p) == 1
    assert chunk_files() == []
    assert not (workdir / "doc.meta").exists()
    assert sefs.file_size("doc", u, p) == -1
    assert sefs.read_from_file("doc", 0, 1, u, p) is None
    assert sefs.file_integrity_check("doc", u, p) == -1
    # the Master File List entry is gone: the health check no longer looks for the deleted file
    assert sefs.system_health_check(u, p) == 1


# Part 2 s.3 delete_file + create_file "refuse if f exists": after deletion the name can be used again.
def test_delete_then_recreate(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"old")
    assert sefs.delete_file("doc", u, p) == 1
    assert sefs.create_file("doc", u, p) == 1
    assert sefs.file_size("doc", u, p) == 0
    assert sefs.delete_file("doc", u, p) == 1
    assert sefs.delete_file("doc", u, p) == -1   # already gone


# Part 2 s.3 delete_file affects only the named file.
def test_delete_leaves_other_files(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "one", b"first")
    _encrypt(sefs, workdir, user, "two", b"second")
    assert sefs.delete_file("one", u, p) == 1
    assert sefs.read_from_file("two", 0, 6, u, p) == b"second"
    assert sefs.file_integrity_check("two", u, p) == 1
    assert sefs.system_health_check(u, p) == 1


# Part 2 demo: the owner can delete after a non-owner was refused.
def test_owner_deletes_after_non_owner_refused(sefs, user, workdir):
    u, p = user
    assert sefs.register_user(OTHER_USER, OTHER_PASS, "passwd") == 1
    _encrypt(sefs, workdir, user, "doc1", b"hello SEFS world")
    assert sefs.delete_file("doc1", OTHER_USER, OTHER_PASS) == -1
    assert sefs.delete_file("doc1", u, p) == 1


# ---------------- G4: encrypt_file specifics ----------------

# Part 2 s.3 encrypt_file reads plaintext file f from disk: missing on disk -> -1.
def test_encrypt_missing_disk_file(sefs, user, workdir):
    u, p = user
    assert not (workdir / "ghost").exists()
    assert sefs.encrypt_file("ghost", u, p) == -1
    assert sefs.file_size("ghost", u, p) == -1


# Part 2 s.3 encrypt_file replace + Part 3 s.2.6 no orphans: replacing a 3-chunk file with 1 chunk
# leaves exactly 1 chunk file.
def test_encrypt_replace_no_orphans(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"x" * 2500)
    assert len(chunk_files()) == 3
    _encrypt(sefs, workdir, user, "doc", b"short")
    assert len(chunk_files()) == 1
    assert sefs.file_size("doc", u, p) == 5
    assert sefs.file_integrity_check("doc", u, p) == 1


# Part 2 s.3 encrypt_file: the encrypting user becomes the owner; another user cannot read it.
def test_encrypt_sets_owner(sefs, user, workdir):
    u, p = user
    assert sefs.register_user(OTHER_USER, OTHER_PASS, "passwd") == 1
    (workdir / "bobs").write_bytes(b"bob data")
    assert sefs.encrypt_file("bobs", OTHER_USER, OTHER_PASS) == 1
    assert sefs.read_from_file("bobs", 0, 8, OTHER_USER, OTHER_PASS) == b"bob data"
    assert sefs.read_from_file("bobs", 0, 8, u, p) is None


# ---------------- G5: fresh keys and IVs ----------------

# Part 2 s.4 "Fresh IV whenever a chunk is re-encrypted" / FILE_FORMAT s.3: the same plaintext stored
# twice gives different chunk file bytes.
def test_same_plaintext_different_ciphertext(sefs, user, workdir, chunk_files):
    _encrypt(sefs, workdir, user, "one", b"identical content")
    (c1,) = chunk_files()
    b1 = c1.read_bytes()
    _encrypt(sefs, workdir, user, "two", b"identical content")
    others = [f.read_bytes() for f in chunk_files() if f != c1]
    assert len(others) == 1
    assert others[0] != b1


# Part 2 s.3 write_to_file "re-encrypt with fresh keys and IVs": re-encrypting the same content again
# never reproduces an earlier chunk file.
def test_reencryption_changes_every_chunk_file(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"q" * 2000)
    seen = {f.read_bytes() for f in chunk_files()}
    for _ in range(3):
        _encrypt(sefs, workdir, user, "doc", b"q" * 2000)   # owner replaces with identical content
        now = {f.read_bytes() for f in chunk_files()}
        assert len(now) == 2
        assert seen.isdisjoint(now)
        seen |= now


# Part 2 s.2 / Part 3 s.1: each chunk has its own random key - two identical 1024-byte blocks in one file
# give different chunk file bytes.
def test_identical_blocks_different_chunks(sefs, user, workdir, chunk_files):
    _encrypt(sefs, workdir, user, "doc", b"R" * 2048)
    a, b = chunk_files()
    assert a.read_bytes() != b.read_bytes()


# ---------------- G6: padding ----------------

# Part 3 s.4 "last chunk padded" / FILE_FORMAT s.3 (content padded to 1,024 bytes): chunk files of a
# 1-byte, 500-byte, 1024-byte and empty file all have the same length, so the length leaks nothing.
def test_all_chunk_files_same_size(sefs, user, workdir, chunk_files):
    u, p = user
    assert sefs.create_file("empty", u, p) == 1
    _encrypt(sefs, workdir, user, "one", b"x")
    _encrypt(sefs, workdir, user, "mid", b"y" * 500)
    _encrypt(sefs, workdir, user, "full", b"z" * 1024)
    _encrypt(sefs, workdir, user, "multi", b"w" * 1500)
    sizes = {f.stat().st_size for f in chunk_files()}
    assert len(chunk_files()) == 6
    assert len(sizes) == 1


# ---------------- G7: failed operations leave the file untouched ----------------

# Part 3 s.2.2 step 5: "If any step fails ... the old file is untouched" - a rejected write changes no
# chunk file, the meta file or the Master File List.
def test_rejected_write_changes_nothing(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"x" * 1500)
    snap = {f.name: f.read_bytes() for f in chunk_files()}
    meta = (workdir / "doc.meta").read_bytes()
    ml = (workdir / "masterlist").read_bytes()
    assert sefs.write_to_file("doc", 1501, b"y", u, p) == -1
    assert sefs.write_to_file("doc", -1, b"y", u, p) == -1
    assert sefs.write_to_file("doc", 0, None, u, p) == -1
    assert {f.name: f.read_bytes() for f in chunk_files()} == snap
    assert (workdir / "doc.meta").read_bytes() == meta
    assert (workdir / "masterlist").read_bytes() == ml


# Part 2 s.3: a successful write updates the meta file and the Master File List digest together,
# so the file still passes the integrity check afterwards.
def test_write_keeps_meta_and_masterlist_consistent(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"x" * 1500)
    meta = (workdir / "doc.meta").read_bytes()
    ml = (workdir / "masterlist").read_bytes()
    assert sefs.write_to_file("doc", 0, b"y", u, p) == 1
    assert (workdir / "doc.meta").read_bytes() != meta
    assert (workdir / "masterlist").read_bytes() != ml
    assert sefs.file_integrity_check("doc", u, p) == 1
    assert sefs.system_health_check(u, p) == 1


# ---------------- G8: on-disk locations ----------------

# FILE_FORMAT file list: passwd, master.key, masterlist, <name>.meta and chunks/ in the working directory.
def test_files_in_working_directory(sefs, user, workdir, chunk_files):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert (workdir / "passwd").is_file()
    assert (workdir / "master.key").is_file()
    assert (workdir / "masterlist").is_file()
    assert (workdir / "notes.meta").is_file()
    assert (workdir / "chunks").is_dir()
    assert all(f.parent == workdir / "chunks" for f in chunk_files())


# ---------------- G9: sizes and exact-end reads after several writes ----------------

# Part 2 s.3 file_size / read_from_file: size tracks a sequence of inserts; reading exactly up to the end
# works and one byte more returns None.
def test_size_tracks_writes(sefs, user):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    expected = b""
    for pos, data in [(0, b"abc"), (3, b"def"), (0, b"0"), (4, b"--"), (9, b"x" * 1020)]:
        assert sefs.write_to_file("notes", pos, data, u, p) == 1
        expected = expected[:pos] + data + expected[pos:]
        assert sefs.file_size("notes", u, p) == len(expected)
    n = len(expected)
    assert sefs.read_from_file("notes", 0, n, u, p) == expected
    assert sefs.read_from_file("notes", n - 5, 5, u, p) == expected[-5:]
    assert sefs.read_from_file("notes", n - 5, 6, u, p) is None
