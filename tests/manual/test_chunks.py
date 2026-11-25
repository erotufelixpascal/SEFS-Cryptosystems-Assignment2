"""Manual arm - chunk boundaries (sizes and positions around 1,024-byte chunk edges).

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

# ---- SHAPE 1: content of an exact size ---------------------------------------
# # Rule (from docs/PART3_FULL_SEFS.md): ___
# def test____(sefs, user, chunk_files):
#     u, p = user
#     content = b"A" * ___                     # exactly ___ bytes
#     # ... store it with sefs functions ...
#     assert len(chunk_files()) == ___         # how many chunk files the spec says
#
# ---- SHAPE 2: the same check for several sizes ------------------------------
# import pytest
#
# @pytest.mark.parametrize("size, expected", [
#     (___, ___),
#     (___, ___),
# ])
# def test____(sefs, user, chunk_files, size, expected):
#     u, p = user
#     # ... store b"A" * size ...
#     assert ___ == expected

# Write your own tests below this line.
def test_chunk_boundaries(sefs, user, chunk_files):
    u, p = user
    content = b"A" * 2024                     # exactly 2024 bytes
    # ... store it with sefs functions ...
    assert len(chunk_files()) == 0         # how many chunk files the spec says
