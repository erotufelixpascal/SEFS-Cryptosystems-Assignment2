"""P-004: tamper-handling tests, written from CONTEXT.md only.

Tampering is done without relying on dagger-marked format details: bytes are flipped,
files are deleted, truncated, extended, swapped or rolled back as whole files.
"""

import pytest

REPORT = b"A" * 1024 + b"B" * 1024 + b"C" * 500   # 3 chunks (Part 3 demo)
OTHER_USER = "bobuser1"
OTHER_PASS = "B0bPassw0rd#"


def _encrypt(sefs, workdir, user, name, data):
    u, p = user
    (workdir / name).write_bytes(data)
    assert sefs.encrypt_file(name, u, p) == 1


def _flip(path, offset):
    raw = bytearray(path.read_bytes())
    raw[offset] ^= 1
    path.write_bytes(bytes(raw))


def _assert_all_rejected(sefs, workdir, name, u, p, size=None):
    """Integrity check, health check, read, write and decrypt must all fail."""
    assert sefs.file_integrity_check(name, u, p) == -1
    assert sefs.system_health_check(u, p) == -1
    assert sefs.read_from_file(name, 0, 1, u, p) is None
    if size:
        assert sefs.read_from_file(name, 0, size, u, p) is None
    assert sefs.write_to_file(name, 0, b"x", u, p) == -1
    out = workdir / "out.bin"
    if out.exists():
        out.unlink()
    assert sefs.decrypt_file(name, "out.bin", u, p) == -1
    # Part 2 s.3 decrypt_file: integrity is verified FIRST, so no plaintext is written
    assert not out.exists()


@pytest.fixture
def report(sefs, user, workdir, chunk_files):
    _encrypt(sefs, workdir, user, "report", REPORT)
    u, p = user
    assert sefs.file_integrity_check("report", u, p) == 1
    assert sefs.system_health_check(u, p) == 1
    assert len(chunk_files()) == 3
    return "report"


# ---------------- baseline ----------------

# Part 2 s.3 / demo: untouched files pass file_integrity_check and system_health_check.
def test_untampered_passes(sefs, user, workdir):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"hello")
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.file_integrity_check("doc", u, p) == 1
    assert sefs.file_integrity_check("notes", u, p) == 1
    assert sefs.system_health_check(u, p) == 1


# ---------------- modified chunks ----------------

# Part 3 s.2.7 "Modified chunk (any byte) -> HMAC mismatch": flip one byte at the start, middle or end
# of each chunk file.
@pytest.mark.parametrize("which", [0, 1, 2])
@pytest.mark.parametrize("where", ["first", "middle", "last"])
def test_modified_chunk_byte(sefs, user, workdir, chunk_files, report, which, where):
    u, p = user
    victim = chunk_files()[which]
    size = victim.stat().st_size
    offset = {"first": 0, "middle": size // 2, "last": size - 1}[where]
    _flip(victim, offset)
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 demo: flipping byte 100 of a chunk makes system_health_check return -1.
def test_demo_flip_byte_100(sefs, user, workdir, chunk_files, report):
    u, p = user
    _flip(chunk_files()[0], 100)
    assert sefs.system_health_check(u, p) == -1
    assert sefs.file_integrity_check(report, u, p) == -1


# Part 2 s.2 chunk.read "checks length": a truncated chunk file is rejected.
def test_truncated_chunk(sefs, user, workdir, chunk_files, report):
    u, p = user
    victim = chunk_files()[1]
    victim.write_bytes(victim.read_bytes()[:-1])
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 2 s.2 chunk.read "checks length": a chunk file with an extra trailing byte is rejected.
def test_extended_chunk(sefs, user, workdir, chunk_files, report):
    u, p = user
    victim = chunk_files()[1]
    victim.write_bytes(victim.read_bytes() + b"\x00")
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 s.2.7: an emptied chunk file is rejected.
def test_emptied_chunk(sefs, user, workdir, chunk_files, report):
    u, p = user
    chunk_files()[2].write_bytes(b"")
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 s.2.7 modified chunk on a single-chunk (Part 2) file, including the empty file from create_file.
@pytest.mark.parametrize("data", [None, b"hello SEFS world"])
def test_modified_single_chunk_file(sefs, user, workdir, chunk_files, data):
    u, p = user
    if data is None:
        assert sefs.create_file("doc", u, p) == 1
    else:
        _encrypt(sefs, workdir, user, "doc", data)
    (victim,) = chunk_files()
    _flip(victim, victim.stat().st_size // 2)
    _assert_all_rejected(sefs, workdir, "doc", u, p)


# ---------------- missing chunks ----------------

# Part 3 s.2.7 "Missing chunk -> chunk file can't be read".
@pytest.mark.parametrize("which", [0, 1, 2])
def test_missing_chunk(sefs, user, workdir, chunk_files, report, which):
    u, p = user
    chunk_files()[which].unlink()
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 s.2.7 missing chunks: every chunk file of the file removed.
def test_all_chunks_missing(sefs, user, workdir, chunk_files, report):
    u, p = user
    for f in chunk_files():
        f.unlink()
    _assert_all_rejected(sefs, workdir, report, u, p)


# ---------------- swapped chunks ----------------

# Part 3 s.2.7 "Swapped chunks -> each is checked with the other's key -> HMAC mismatch".
@pytest.mark.parametrize("a,b", [(0, 1), (1, 2), (0, 2)])
def test_swapped_chunks_within_file(sefs, user, workdir, chunk_files, report, a, b):
    u, p = user
    files = chunk_files()
    da, db = files[a].read_bytes(), files[b].read_bytes()
    files[a].write_bytes(db)
    files[b].write_bytes(da)
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 s.2.7 swapped chunks between two different single-chunk files: both are detected.
def test_swapped_chunks_between_files(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "one", b"first file")
    names_one = {f.name for f in chunk_files()}
    _encrypt(sefs, workdir, user, "two", b"second file")
    (c1,) = [f for f in chunk_files() if f.name in names_one]
    (c2,) = [f for f in chunk_files() if f.name not in names_one]
    d1, d2 = c1.read_bytes(), c2.read_bytes()
    c1.write_bytes(d2)
    c2.write_bytes(d1)
    _assert_all_rejected(sefs, workdir, "one", u, p)
    _assert_all_rejected(sefs, workdir, "two", u, p)


# ---------------- extra / substituted chunks ----------------

# Part 3 s.2.7 "Extra chunk / changed link": replacing a chunk with a copy of another chunk of the same
# chain (a duplicated chunk in the chain) is detected.
@pytest.mark.parametrize("src,dst", [(0, 1), (1, 2), (2, 1)])
def test_duplicated_chunk_in_chain(sefs, user, workdir, chunk_files, report, src, dst):
    u, p = user
    files = chunk_files()
    files[dst].write_bytes(files[src].read_bytes())
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))


# Part 3 s.2.7: a chunk replaced by an older, once-valid version of itself (replay of a chunk) is detected,
# because writes generate a fresh key for every chunk.
def test_replayed_old_chunk(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"version one")
    (old,) = chunk_files()
    old_bytes = old.read_bytes()
    assert sefs.write_to_file("doc", 0, b"X", u, p) == 1
    (new,) = chunk_files()
    new.write_bytes(old_bytes)
    _assert_all_rejected(sefs, workdir, "doc", u, p)


# Part 3 s.2.7 / s.2.6: a chunk from a different file copied over one of its chunks is detected
# (wrong key, wrong link and wrong size).
def test_foreign_chunk_substituted(sefs, user, workdir, chunk_files, report):
    u, p = user
    report_chunks = {f.name for f in chunk_files()}
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    (small_chunk,) = [f for f in chunk_files() if f.name not in report_chunks]
    victim = sorted(f for f in chunk_files() if f.name in report_chunks)[0]
    victim.write_bytes(small_chunk.read_bytes())
    assert sefs.file_integrity_check("report", u, p) == -1
    assert sefs.file_integrity_check("small", u, p) == 1
    assert sefs.system_health_check(u, p) == -1


# ---------------- edited meta files ----------------

# FILE_FORMAT s.5 / Part 3 s.2.7 "Edited meta file -> SHA-256 no longer matches the Master File List".
# file_size also fails because it reads the size "after the digest check".
@pytest.mark.parametrize("where", ["first", "middle", "last"])
def test_edited_meta_byte(sefs, user, workdir, report, where):
    u, p = user
    meta = workdir / "report.meta"
    size = meta.stat().st_size
    _flip(meta, {"first": 0, "middle": size // 2, "last": size - 1}[where])
    _assert_all_rejected(sefs, workdir, report, u, p, size=len(REPORT))
    assert sefs.file_size(report, u, p) == -1


# Part 3 s.2.7 edited meta: truncated or extended meta file.
@pytest.mark.parametrize("edit", ["truncate", "extend", "empty"])
def test_meta_length_changed(sefs, user, workdir, report, edit):
    u, p = user
    meta = workdir / "report.meta"
    raw = meta.read_bytes()
    meta.write_bytes({"truncate": raw[:-1], "extend": raw + b"\n", "empty": b""}[edit])
    _assert_all_rejected(sefs, workdir, report, u, p)
    assert sefs.file_size(report, u, p) == -1


# Part 2 s.2 _authorize "meta loads": a missing meta file is rejected.
def test_meta_missing(sefs, user, workdir, report):
    u, p = user
    (workdir / "report.meta").unlink()
    _assert_all_rejected(sefs, workdir, report, u, p)
    assert sefs.file_size(report, u, p) == -1


# Part 3 s.2.7 edited meta: swapping the meta files of two files is detected for both.
def test_meta_files_swapped(sefs, user, workdir, report):
    u, p = user
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    a, b = workdir / "report.meta", workdir / "small.meta"
    da, db = a.read_bytes(), b.read_bytes()
    a.write_bytes(db)
    b.write_bytes(da)
    _assert_all_rejected(sefs, workdir, "report", u, p)
    _assert_all_rejected(sefs, workdir, "small", u, p)
    assert sefs.file_size("report", u, p) == -1
    assert sefs.file_size("small", u, p) == -1


# Part 3 s.2.7 edited meta: rolling back the meta file alone to an earlier version is detected.
def test_meta_rolled_back(sefs, user, workdir, report):
    u, p = user
    meta = workdir / "report.meta"
    old = meta.read_bytes()
    assert sefs.write_to_file(report, 0, b"new", u, p) == 1
    meta.write_bytes(old)
    _assert_all_rejected(sefs, workdir, report, u, p)
    assert sefs.file_size(report, u, p) == -1


# ---------------- edited Master File List ----------------

# Part 2 s.2 _authorize "listed in the Master File List": emptying the list makes the file unusable.
def test_masterlist_emptied(sefs, user, workdir, report):
    u, p = user
    (workdir / "masterlist").write_bytes(b"")
    assert sefs.file_integrity_check(report, u, p) == -1
    assert sefs.read_from_file(report, 0, 1, u, p) is None
    assert sefs.write_to_file(report, 0, b"x", u, p) == -1
    assert sefs.file_size(report, u, p) == -1
    assert sefs.decrypt_file(report, "out.bin", u, p) == -1
    assert not (workdir / "out.bin").exists()


# Part 2 s.2 _authorize: a deleted Master File List makes the file unusable.
def test_masterlist_deleted(sefs, user, workdir, report):
    u, p = user
    (workdir / "masterlist").unlink()
    assert sefs.file_integrity_check(report, u, p) == -1
    assert sefs.read_from_file(report, 0, 1, u, p) is None
    assert sefs.write_to_file(report, 0, b"x", u, p) == -1
    assert sefs.file_size(report, u, p) == -1


# FILE_FORMAT s.5: the stored digest must match the meta bytes - rolling back the Master File List
# to before a write (so its digest is stale) is detected.
def test_masterlist_rolled_back(sefs, user, workdir, report):
    u, p = user
    ml = workdir / "masterlist"
    old = ml.read_bytes()
    assert sefs.write_to_file(report, 0, b"new", u, p) == 1
    ml.write_bytes(old)
    _assert_all_rejected(sefs, workdir, report, u, p)
    assert sefs.file_size(report, u, p) == -1


# FILE_FORMAT s.5: a stale digest for one file fails that file only; system_health_check fails overall.
def test_masterlist_stale_for_one_file(sefs, user, workdir, report):
    u, p = user
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    ml = workdir / "masterlist"
    meta = workdir / "small.meta"
    ml_old, meta_old = ml.read_bytes(), meta.read_bytes()
    assert sefs.write_to_file("small", 0, b"x", u, p) == 1
    # restore the OLD masterlist but keep the NEW small.meta: report's entry is still correct,
    # small's entry is stale
    assert ml_old != ml.read_bytes()
    assert meta_old != meta.read_bytes()
    ml.write_bytes(ml_old)
    assert sefs.file_integrity_check("small", u, p) == -1
    assert sefs.file_integrity_check("report", u, p) == 1
    assert sefs.system_health_check(u, p) == -1


# ---------------- system_health_check scope ----------------

# Part 2 s.3 / Part 3 s.2.7: system_health_check is -1 if ANY file fails; untouched files still pass
# file_integrity_check individually (demo: integrity check shows which file was hit).
def test_health_check_pinpoints_file(sefs, user, workdir, chunk_files, report):
    u, p = user
    report_chunks = {f.name for f in chunk_files()}
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    assert sefs.system_health_check(u, p) == 1
    (small_chunk,) = [f for f in chunk_files() if f.name not in report_chunks]
    _flip(small_chunk, 100)
    assert sefs.system_health_check(u, p) == -1
    assert sefs.file_integrity_check("small", u, p) == -1
    assert sefs.file_integrity_check("report", u, p) == 1
    assert sefs.read_from_file("report", 1019, 10, u, p) == b"AAAAABBBBB"


# Part 2 s.3 write_to_file "verify and decrypt" first: a write to a tampered file is refused and does not
# silently repair it.
def test_write_does_not_repair_tampered_file(sefs, user, workdir, chunk_files, report):
    u, p = user
    _flip(chunk_files()[1], 200)
    assert sefs.write_to_file(report, len(REPORT), b"tail", u, p) == -1
    assert sefs.file_integrity_check(report, u, p) == -1
    assert sefs.system_health_check(u, p) == -1


# ---------------- wrong passwords ----------------

# Part 2 s.1: every function first checks the user's password; wrong password -> -1 / None.
def test_wrong_password_everywhere(sefs, user, workdir, chunk_files, report):
    u, p = user
    bad = "WrongPass#1"
    before = {f.name: f.read_bytes() for f in chunk_files()}
    assert sefs.file_integrity_check(report, u, bad) == -1
    assert sefs.system_health_check(u, bad) == -1
    assert sefs.read_from_file(report, 0, 1, u, bad) is None
    assert sefs.write_to_file(report, 0, b"x", u, bad) == -1
    assert sefs.file_size(report, u, bad) == -1
    assert sefs.decrypt_file(report, "out.bin", u, bad) == -1
    assert not (workdir / "out.bin").exists()
    assert sefs.delete_file(report, u, bad) == -1
    assert sefs.create_file("newfile", u, bad) == -1
    (workdir / "plain").write_bytes(b"data")
    assert sefs.encrypt_file("plain", u, bad) == -1
    assert sefs.encrypt_file(report, u, bad) == -1
    # nothing changed
    assert {f.name: f.read_bytes() for f in chunk_files()} == before
    assert sefs.read_from_file(report, 0, len(REPORT), u, p) == REPORT


# Part 2 s.1: an unregistered user is rejected everywhere.
def test_unregistered_user_everywhere(sefs, user, workdir, report):
    u2, p2 = "ghostusr", "Gh0st#pass"
    assert sefs.file_integrity_check(report, u2, p2) == -1
    assert sefs.system_health_check(u2, p2) == -1
    assert sefs.read_from_file(report, 0, 1, u2, p2) is None
    assert sefs.write_to_file(report, 0, b"x", u2, p2) == -1
    assert sefs.file_size(report, u2, p2) == -1
    assert sefs.decrypt_file(report, "out.bin", u2, p2) == -1
    assert sefs.delete_file(report, u2, p2) == -1
    assert sefs.create_file("newfile", u2, p2) == -1


# Part 2 s.1 + Part 1: after a password change the old password no longer opens files; the new one does.
def test_old_password_after_change(sefs, user, workdir, report):
    u, p = user
    assert sefs.change_user_password(u, p, "NewPassw0rd=", "passwd") == 1
    assert sefs.read_from_file(report, 0, 1, u, p) is None
    assert sefs.file_integrity_check(report, u, p) == -1
    assert sefs.read_from_file(report, 0, 1, u, "NewPassw0rd=") == b"A"
    assert sefs.file_integrity_check(report, u, "NewPassw0rd=") == 1


# Part 1 + Part 2 s.1: an edited passwd hash means the user can no longer log in to SEFS.
def test_edited_passwd_blocks_access(sefs, user, workdir, report):
    u, p = user
    pw = workdir / "passwd"
    line = pw.read_bytes().rstrip(b"\n")
    name, salt, h = line.split(b":")
    h = (b"0" if h[:1] != b"0" else b"1") + h[1:]
    pw.write_bytes(name + b":" + salt + b":" + h + b"\n")
    assert sefs.match_user(u, p, "passwd") == -1
    assert sefs.read_from_file(report, 0, 1, u, p) is None
    assert sefs.file_integrity_check(report, u, p) == -1


# ---------------- wrong owners ----------------

@pytest.fixture
def other(sefs, user):
    assert sefs.register_user(OTHER_USER, OTHER_PASS, "passwd") == 1
    return OTHER_USER, OTHER_PASS


# Part 2 s.1 / s.2 _authorize "user is the owner": a valid non-owner is refused by every per-file function.
def test_non_owner_refused(sefs, user, other, workdir, chunk_files, report):
    u, p = user
    o, op = other
    before = {f.name: f.read_bytes() for f in chunk_files()}
    assert sefs.file_integrity_check(report, o, op) == -1
    assert sefs.read_from_file(report, 0, 1, o, op) is None
    assert sefs.write_to_file(report, 0, b"x", o, op) == -1
    assert sefs.file_size(report, o, op) == -1
    assert sefs.decrypt_file(report, "out.bin", o, op) == -1
    assert not (workdir / "out.bin").exists()
    assert sefs.delete_file(report, o, op) == -1
    assert {f.name: f.read_bytes() for f in chunk_files()} == before
    assert sefs.read_from_file(report, 0, len(REPORT), u, p) == REPORT


# Part 2 s.3 encrypt_file: "if f is already in SEFS, only its owner may replace it".
def test_non_owner_cannot_replace_via_encrypt(sefs, user, other, workdir, report):
    u, p = user
    o, op = other
    (workdir / report).write_bytes(b"mallory's content")
    assert sefs.encrypt_file(report, o, op) == -1
    assert sefs.read_from_file(report, 0, len(REPORT), u, p) == REPORT
    assert sefs.file_integrity_check(report, u, p) == 1


# Part 2 s.3 create_file: "refuse if f exists" - also when another user owns it.
def test_non_owner_cannot_create_over_existing(sefs, user, other, report):
    u, p = user
    o, op = other
    assert sefs.create_file(report, o, op) == -1
    assert sefs.create_file(report, u, p) == -1
    assert sefs.file_size(report, u, p) == len(REPORT)


# Part 2 s.2 _authorize owner check: one user's meta copied over another user's meta does not grant
# access (the digest no longer matches) - the owner of the overwritten file is locked out too.
def test_meta_from_other_owner_substituted(sefs, user, other, workdir, report):
    u, p = user
    o, op = other
    (workdir / "bobs").write_bytes(b"bob data")
    assert sefs.encrypt_file("bobs", o, op) == 1
    (workdir / "bobs.meta").write_bytes((workdir / "report.meta").read_bytes())
    assert sefs.read_from_file("bobs", 0, 1, u, p) is None
    assert sefs.read_from_file("bobs", 0, 1, o, op) is None
    assert sefs.file_integrity_check("bobs", o, op) == -1
