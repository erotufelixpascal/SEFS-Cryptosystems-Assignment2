"""P-001: Part 1 (user authentication) tests, written from CONTEXT.md only."""

import pytest

P = "passwd"
GOOD_USER = "alice01"
GOOD_PASS = "Passw0rd#1"
OTHER_USER = "bobuser1"
OTHER_PASS = "B0bPassw0rd#"


# Part 1 s.1 / s.6 demo: register_user returns 1 for a new valid user; is_user_valid then returns 1.
def test_register_new_user_then_valid(sefs):
    assert sefs.register_user(GOOD_USER, GOOD_PASS, P) == 1
    assert sefs.is_user_valid(GOOD_USER, P) == 1


# Part 1 s.4 register_user: "refuse if the user exists" (demo: duplicate -> -1).
def test_register_duplicate_refused(sefs, user):
    u, p = user
    assert sefs.register_user(u, p, P) == -1
    assert sefs.register_user(u, "Different#pw1", P) == -1
    assert sefs.match_user(u, p, P) == 1  # original password still works


# Part 1 s.4 is_user_valid: 1 only if found.
def test_is_user_valid_unknown_user(sefs, user):
    assert sefs.is_user_valid("nobody01", P) == -1


# Part 1 s.4 match_user: correct password -> 1, wrong password -> -1 (demo).
def test_match_user_correct_and_wrong(sefs, user):
    u, p = user
    assert sefs.match_user(u, p, P) == 1
    assert sefs.match_user(u, "WrongPass#1", P) == -1


# Part 1 s.4 match_user: unknown user -> -1.
def test_match_user_unknown_user(sefs, user):
    assert sefs.match_user("nobody01", GOOD_PASS, P) == -1


# Part 1 s.4 match_user: comparison is exact - a password differing only in case or one char fails.
@pytest.mark.parametrize("wrong", ["passw0rd#1", "PASSW0RD#1", "Passw0rd#2", "Passw0rd#1x", "Passw0rd#"])
def test_match_user_near_miss_passwords(sefs, user, wrong):
    u, _ = user
    assert sefs.match_user(u, wrong, P) == -1


# Part 1 s.4 _find_user: name before first ':' must EXACTLY equal u (alice01 never matches alice012).
def test_find_user_exact_name_match(sefs):
    assert sefs.register_user("alice012", GOOD_PASS, P) == 1
    assert sefs.is_user_valid("alice01", P) == -1
    assert sefs.match_user("alice01", GOOD_PASS, P) == -1
    # registering the prefix name is a different user and must succeed
    assert sefs.register_user("alice01", "Other#pass1", P) == 1
    assert sefs.match_user("alice012", GOOD_PASS, P) == 1
    assert sefs.match_user("alice01", "Other#pass1", P) == 1
    assert sefs.match_user("alice012", "Other#pass1", P) == -1


# Part 1 s.4 _find_user exact equality: usernames are case-sensitive.
def test_username_case_sensitive(sefs, user):
    assert sefs.is_user_valid("ALICE01", P) == -1
    assert sefs.is_user_valid("Alice01", P) == -1


# Part 1 s.4 delete_user: requires correct password; wrong password leaves the user in place.
def test_delete_user_wrong_password(sefs, user):
    u, p = user
    assert sefs.delete_user(u, "WrongPass#1", P) == -1
    assert sefs.is_user_valid(u, P) == 1
    assert sefs.match_user(u, p, P) == 1


# Part 1 s.4 delete_user / demo: correct password removes the user.
def test_delete_user_correct_password(sefs, user):
    u, p = user
    assert sefs.delete_user(u, p, P) == 1
    assert sefs.is_user_valid(u, P) == -1
    assert sefs.match_user(u, p, P) == -1


# Part 1 s.4 delete_user: "drop only that line" - other users are untouched.
def test_delete_user_drops_only_that_line(sefs, user):
    u, p = user
    assert sefs.register_user(OTHER_USER, OTHER_PASS, P) == 1
    assert sefs.register_user("carol001", "Car0l#pass", P) == 1
    assert sefs.delete_user(OTHER_USER, OTHER_PASS, P) == 1
    assert sefs.match_user(u, p, P) == 1
    assert sefs.match_user("carol001", "Car0l#pass", P) == 1
    assert sefs.is_user_valid(OTHER_USER, P) == -1


# Part 1 s.4 delete_user: unknown user -> -1.
def test_delete_unknown_user(sefs, user):
    assert sefs.delete_user("nobody01", GOOD_PASS, P) == -1


# Part 1 s.4 + demo: a deleted user can be registered again.
def test_reregister_after_delete(sefs, user):
    u, p = user
    assert sefs.delete_user(u, p, P) == 1
    assert sefs.register_user(u, "Fresh#pass9", P) == 1
    assert sefs.match_user(u, "Fresh#pass9", P) == 1
    assert sefs.match_user(u, p, P) == -1


# Part 1 s.4 change_user_password / demo: new password works, old one no longer does.
def test_change_password_success(sefs, user):
    u, p = user
    assert sefs.change_user_password(u, p, "NewPassw0rd=", P) == 1
    assert sefs.match_user(u, "NewPassw0rd=", P) == 1
    assert sefs.match_user(u, p, P) == -1


# Part 1 s.4 change_user_password: only with the correct old password.
def test_change_password_wrong_old(sefs, user):
    u, p = user
    assert sefs.change_user_password(u, "WrongPass#1", "NewPassw0rd=", P) == -1
    assert sefs.match_user(u, p, P) == 1
    assert sefs.match_user(u, "NewPassw0rd=", P) == -1


# Part 1 s.4 change_user_password: "validate the new password" first; invalid new password -> -1, old kept.
@pytest.mark.parametrize("bad_new", ["short", "a" * 32, "Passw0rd!1", "Pass word1", "Passw0rd_1", None])
def test_change_password_invalid_new(sefs, user, bad_new):
    u, p = user
    assert sefs.change_user_password(u, p, bad_new, P) == -1
    assert sefs.match_user(u, p, P) == 1


# Part 1 s.4 change_user_password: unknown user -> -1.
def test_change_password_unknown_user(sefs, user):
    assert sefs.change_user_password("nobody01", GOOD_PASS, "NewPassw0rd=", P) == -1


# Part 1 s.4 change_user_password: "replace only that line" - other users unaffected.
def test_change_password_only_that_user(sefs, user):
    u, p = user
    assert sefs.register_user(OTHER_USER, OTHER_PASS, P) == 1
    assert sefs.change_user_password(u, p, "NewPassw0rd=", P) == 1
    assert sefs.match_user(OTHER_USER, OTHER_PASS, P) == 1


# Part 1 s.4 / s.7: change_user_password generates a FRESH salt (salt and hash fields of the line change),
# even when the new password equals the old one.
def test_change_password_fresh_salt(sefs, user, workdir):
    u, p = user

    def line():
        for ln in (workdir / P).read_bytes().split(b"\n"):
            if ln.split(b":", 1)[0] == u.encode():
                return ln
        raise AssertionError("user line missing")

    before = line()
    assert sefs.change_user_password(u, p, p, P) == 1
    after = line()
    assert before.split(b":")[1] != after.split(b":")[1]
    assert before.split(b":")[2] != after.split(b":")[2]
    assert sefs.match_user(u, p, P) == 1


# Part 1 s.2: salt is 32 random bytes per user -> two users with the same password get different salts and hashes.
def test_same_password_different_salt_and_hash(sefs, workdir):
    assert sefs.register_user("userone1", GOOD_PASS, P) == 1
    assert sefs.register_user("usertwo2", GOOD_PASS, P) == 1
    lines = [ln for ln in (workdir / P).read_bytes().split(b"\n") if ln]
    assert len(lines) == 2
    f1, f2 = lines[0].split(b":"), lines[1].split(b":")
    assert f1[1] != f2[1]
    assert f1[2] != f2[2]


# Part 1 s.2 (salt = 32 bytes, shown as 64 hex in the passwd example; not dagger-marked) and line shape u:salt:hash.
def test_passwd_line_shape(sefs, user, workdir):
    u, _ = user
    lines = [ln for ln in (workdir / P).read_bytes().split(b"\n") if ln]
    assert len(lines) == 1
    fields = lines[0].split(b":")
    assert len(fields) == 3
    assert fields[0] == u.encode()
    assert len(fields[1]) == 64
    bytes.fromhex(fields[1].decode("ascii"))
    bytes.fromhex(fields[2].decode("ascii"))


# Part 1 s.2: "passwords are never stored" - the password text does not appear in the file.
def test_password_not_stored_in_clear(sefs, user, workdir):
    _, p = user
    assert p.encode() not in (workdir / P).read_bytes()


# Part 1 s.5: interoperable files - binary mode, '\n' only (no '\r').
def test_passwd_uses_lf_only(sefs, user, workdir):
    sefs.register_user(OTHER_USER, OTHER_PASS, P)
    data = (workdir / P).read_bytes()
    assert b"\r" not in data
    assert data.endswith(b"\n")


# Part 1 s.5: crash-safe updates via passwd.tmp + os.replace; no temp file is left behind.
def test_no_temp_file_left_after_change_and_delete(sefs, user, workdir):
    u, p = user
    assert sefs.change_user_password(u, p, "NewPassw0rd=", P) == 1
    assert not (workdir / "passwd.tmp").exists()
    assert sefs.delete_user(u, "NewPassw0rd=", P) == 1
    assert not (workdir / "passwd.tmp").exists()


# Part 1 s.4 _find_user "damaged line": register refuses if the user's line is damaged; match fails.
def test_damaged_line_refused(sefs, workdir):
    (workdir / P).write_bytes(b"alice01:zz:zz\n")
    assert sefs.register_user("alice01", GOOD_PASS, P) == -1
    assert sefs.match_user("alice01", GOOD_PASS, P) == -1


# Part 1 s.1: the pFile argument selects the password file - users in one file are not in another.
def test_password_file_argument_respected(sefs):
    assert sefs.register_user(GOOD_USER, GOOD_PASS, "pwA") == 1
    assert sefs.is_user_valid(GOOD_USER, "pwA") == 1
    assert sefs.is_user_valid(GOOD_USER, "pwB") == -1
    assert sefs.match_user(GOOD_USER, GOOD_PASS, "pwB") == -1


# ---------------- Input-validation boundaries (Part 1 s.3) ----------------

# Part 1 s.3: username length 6-31 (USER_MIN, USER_MAX).
@pytest.mark.parametrize("name,expected", [
    ("a" * 5, -1),
    ("a" * 6, 1),
    ("a" * 7, 1),
    ("a" * 30, 1),
    ("a" * 31, 1),
    ("a" * 32, -1),
    ("", -1),
])
def test_username_length_boundaries(sefs, name, expected):
    assert sefs.register_user(name, GOOD_PASS, P) == expected
    assert sefs.is_user_valid(name, P) == expected


# Part 1 s.3: password length 9-31 (PASS_MIN, PASS_MAX).
@pytest.mark.parametrize("pw,expected", [
    ("A1b2C3d4", -1),          # 8
    ("A1b2C3d4e", 1),          # 9
    ("A1b2C3d4e5", 1),         # 10
    ("Ab1" * 10, 1),           # 30
    ("Ab1" * 10 + "x", 1),     # 31
    ("Ab1" * 10 + "xy", -1),   # 32
    ("", -1),
])
def test_password_length_boundaries(sefs, pw, expected):
    assert sefs.register_user(GOOD_USER, pw, P) == expected
    if expected == 1:
        assert sefs.match_user(GOOD_USER, pw, P) == 1


# Part 1 s.3: username characters a-z A-Z 0-9 only (mixed case and digits allowed).
@pytest.mark.parametrize("name", ["ABCdef", "123456", "aZ09aZ09", "UPPERCASE"])
def test_username_allowed_characters(sefs, name):
    assert sefs.register_user(name, GOOD_PASS, P) == 1


# Part 1 s.3: any other username character is rejected (incl. non-ASCII letters / full-width digits).
@pytest.mark.parametrize("name", [
    "alice_01", "alice-01", "alice 01", "alice:01", "alice.01", "alice@01",
    "alicé01",         # e-acute
    "alice０１",    # full-width digits
    "alice01\n",
    "alice01\x00",
])
def test_username_rejected_characters(sefs, name):
    assert sefs.register_user(name, GOOD_PASS, P) == -1
    assert sefs.is_user_valid(name, P) == -1


# Part 1 s.3: every PASS_EXTRA symbol @ # $ % & * ( ) - + = is allowed in passwords.
@pytest.mark.parametrize("sym", list("@#$%&*()-+="))
def test_password_each_extra_symbol_allowed(sefs, sym):
    pw = "Abcdef12" + sym
    assert sefs.register_user(GOOD_USER, pw, P) == 1
    assert sefs.match_user(GOOD_USER, pw, P) == 1


# Part 1 s.3: other symbols, whitespace, ':' and non-ASCII are rejected in passwords.
@pytest.mark.parametrize("pw", [
    "Abcdef12!", "Abcdef12_", "Abcdef12 ", "Abcdef12:", "Abcdef12^", "Abcdef12/",
    "Abcdef12~", "Abcdef12.", "Abcdef12\n",
    "Abcdef12é",         # e-acute
    "Abcdef12１",         # full-width digit
])
def test_password_rejected_characters(sefs, pw):
    assert sefs.register_user(GOOD_USER, pw, P) == -1
    assert sefs.is_user_valid(GOOD_USER, P) == -1


# Part 1 s.3: match_user also validates - a password that is invalid by the rules fails even for a real user.
def test_match_user_invalid_password_format(sefs, user):
    u, _ = user
    assert sefs.match_user(u, "short", P) == -1
    assert sefs.match_user(u, "x" * 32, P) == -1


# Part 1 s.1: arguments may be ASCII bytes; str and bytes refer to the same user/password.
def test_bytes_arguments_accepted(sefs):
    assert sefs.register_user(b"alice01", b"Passw0rd#1", P) == 1
    assert sefs.is_user_valid("alice01", P) == 1
    assert sefs.is_user_valid(b"alice01", P) == 1
    assert sefs.match_user("alice01", "Passw0rd#1", P) == 1
    assert sefs.match_user(b"alice01", b"Passw0rd#1", P) == 1
    assert sefs.change_user_password(b"alice01", b"Passw0rd#1", b"NewPassw0rd=", P) == 1
    assert sefs.match_user("alice01", "NewPassw0rd=", P) == 1
    assert sefs.delete_user(b"alice01", b"NewPassw0rd=", P) == 1
    assert sefs.is_user_valid("alice01", P) == -1


# Part 1 s.1/s.3: bytes that are not ASCII letters/digits are rejected.
def test_non_ascii_bytes_rejected(sefs):
    assert sefs.register_user(b"alic\xe901", GOOD_PASS, P) == -1
    assert sefs.register_user(GOOD_USER, b"Passw0rd#\xe9", P) == -1


# Part 1 s.1: anything other than str/bytes (including None) returns -1, for every function.
@pytest.mark.parametrize("bad", [None, 123, 1.5, ["alice01"], bytearray(b"alice01")])
def test_wrong_types_rejected(sefs, user, bad):
    u, p = user
    assert sefs.register_user(bad, GOOD_PASS, P) == -1
    assert sefs.register_user("newuser1", bad, P) == -1
    assert sefs.is_user_valid(bad, P) == -1
    assert sefs.match_user(bad, p, P) == -1
    assert sefs.match_user(u, bad, P) == -1
    assert sefs.delete_user(bad, p, P) == -1
    assert sefs.delete_user(u, bad, P) == -1
    assert sefs.change_user_password(bad, p, "NewPassw0rd=", P) == -1
    assert sefs.change_user_password(u, bad, "NewPassw0rd=", P) == -1
    assert sefs.change_user_password(u, p, bad, P) == -1
    # nothing changed
    assert sefs.match_user(u, p, P) == 1
