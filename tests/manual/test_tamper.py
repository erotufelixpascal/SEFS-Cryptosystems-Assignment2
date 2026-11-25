"""Manual arm - tamper handling (modified, missing or swapped files; wrong user or password).

Written by hand by the tester, with NO AI tools of any kind.
Specification: docs/ only. Fixtures: tests/conftest.py (sefs, user, workdir, chunk_files).
Guide: docs/MANUAL_TESTING_GUIDE.md. Time is logged in logs/time_log.csv (arm = manual).
"""

# =============================================================================
# HOW TO USE THIS FILE  (read once, then delete these comment blocks if you like)
# =============================================================================
# Lines starting with "#" are comments: Python ignores them, so nothing below
# runs until YOU write a real test. Fill in every ___ yourself, using ONLY the
# rules in docs/ (the specification). Don't copy a test from anywhere else.
#
#  - A test is a function whose name starts with  test_
#  - Its inputs (sefs, user, workdir, chunk_files) are given to you automatically:
#       sefs         the file system; call its functions like  sefs.match_user(...)
#       user         a registered (username, password) pair:  u, p = user
#       workdir      the temporary folder the test runs in
#       chunk_files  chunk_files() gives the list of chunk files on disk
#  - Each test has three steps:  Arrange (prepare)  ->  Act (call ONE function)
#    ->  Assert (check the result is exactly what the spec says)
#  - Return values in the spec: most functions give 1 (OK) or -1 (ERROR);
#    read_from_file gives bytes, or None on failure; file_size gives the size or -1.
#  - Run your tests:   python -m pytest tests\manual -v
#    PASSED = the code did what your test expects. FAILED = read the message:
#    either the code is wrong (real_defect) or your test is (false_positive).
# =============================================================================

# ---- SHAPE 1: damage a file on disk, then check it is noticed ---------------
# # Rule (from docs/PART3_FULL_SEFS.md, "Integrity across the chain"): ___
# def test____(sefs, user, chunk_files):
#     u, p = user
#     # Arrange: store a file with sefs functions first ...
#     target = chunk_files()[0]                 # pick a chunk file
#     data = bytearray(target.read_bytes())
#     data[___] ^= 0x01                         # flip one bit at position ___
#     target.write_bytes(data)
#     # Act + Assert:
#     assert sefs.___(___) == ___
#
# ---- Other kinds of damage you can do to a file (target is a file path) -----
#     target.unlink()                           # delete the file
#     target.write_bytes(target.read_bytes() + b"___")   # add bytes at the end
#     (workdir / "___").write_bytes(b"___")     # change another file in the folder

# Write your own tests below this line.
# def test_tamper_chunk_file(sefs, user, chunk_files):
#     u, p = user
#     # Arrange: store a file with sefs functions first ...
#     #loggin the chunck size and the number of chunks
#     print(len(chunk_files()))
#     content = b"A" * 2024                     # exactly 2024 bytes
#     target = chunk_files()[1]                 # pick a chunk file
#     data = bytearray(target.read_bytes())
#     data[0] ^= 0x01                         # flip one bit at position 0
#     target.write_bytes(data)
#     # Act + Assert:
#     assert sefs.check_file_integrity("test_file", u, p) == -1

def _store_two_chunks(sefs, u, p, chunk_files):
    """Create 'notes' with 2,024 bytes (2 chunks) and return the chunk files."""
    assert sefs.create_file("notes", u, p) == sefs.OK
    assert sefs.write_to_file("notes", 0, b"A" * 2024, u, p) == sefs.OK
    files = chunk_files()
    assert len(files) == 2
    assert sefs.file_integrity_check("notes", u, p) == sefs.OK
    return files


def test_tamper_chunk_file(sefs, user, chunk_files):
    u, p = user
    target = _store_two_chunks(sefs, u, p, chunk_files)[1]
    data = bytearray(target.read_bytes())
    data[0] ^= 0x01                                   # flip one bit
    target.write_bytes(data)
    assert sefs.file_integrity_check("notes", u, p) == sefs.ERR


def test_deleted_chunk_file(sefs, user, chunk_files):
    u, p = user
    target = _store_two_chunks(sefs, u, p, chunk_files)[1]
    target.unlink()                                   # delete a chunk
    assert sefs.file_integrity_check("notes", u, p) == sefs.ERR


def test_extra_bytes_appended(sefs, user, chunk_files):
    u, p = user
    target = _store_two_chunks(sefs, u, p, chunk_files)[1]
    target.write_bytes(target.read_bytes() + b"HelloWorld")   # add bytes at the end
    assert sefs.file_integrity_check("notes", u, p) == sefs.ERR