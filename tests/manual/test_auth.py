"""Manual arm - authentication (Part 1: the five user functions and their input rules).

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

# ---- SHAPE 1: one test, one rule -------------------------------------------
# # Rule (copy it from docs/PART1_USER_AUTHENTICATION.md): ___
# def test____(sefs):
#     result = sefs.register_user("___", "___", "passwd")
#     assert result == ___
#
# ---- SHAPE 2: using the ready-made user -------------------------------------
# # Rule: ___
# def test____(sefs, user):
#     u, p = user
#     assert sefs.___(u, ___, "passwd") == ___
#
# ---- SHAPE 3: the same check for many inputs (good for length limits) -------
# import pytest
#
# @pytest.mark.parametrize("name, expected", [
#     ("___", ___),
#     ("___", ___),
# ])
# def test____(sefs, name, expected):
#     assert sefs.register_user(name, "___", "passwd") == expected

# Write your own tests below this line.
def test_register_user(sefs):
    result = sefs.register_user("alice01", "Passw0rd#1", "passwd")
    assert result == 1


