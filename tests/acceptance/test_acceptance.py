"""Acceptance checklist: SEFS must pass all of these before the experiment starts.

These tests are part of the implementation scaffold, NOT one of the experiment
arms. Neither arm may copy them.
"""

import os
from pathlib import Path

U2, P2 = "mallory1", "Mall0ry#pw"


# ---------------- Part 1: authentication ----------------

def test_register_and_match(sefs):
    assert sefs.register_user("alice01", "Passw0rd#1", "passwd") == 1
    assert sefs.register_user("alice01", "Passw0rd#1", "passwd") == -1  # duplicate
    assert sefs.is_user_valid("alice01", "passwd") == 1
    assert sefs.match_user("alice01", "Passw0rd#1", "passwd") == 1
    assert sefs.match_user("alice01", "WrongPass#1", "passwd") == -1


def test_passwd_file_never_holds_password(sefs):
    sefs.register_user("alice01", "Passw0rd#1", "passwd")
    raw = Path("passwd").read_bytes()
    assert b"Passw0rd#1" not in raw
    name, salt, digest = raw.rstrip(b"\n").split(b":")
    assert name == b"alice01" and len(salt) == 64 and len(digest) == 40
    assert raw.endswith(b"\n") and b"\r" not in raw


def test_input_validation(sefs):
    assert sefs.register_user("bob", "Passw0rd#1", "passwd") == -1           # username too short
    assert sefs.register_user("carol01", "short", "passwd") == -1            # password too short
    assert sefs.register_user("bad user", "Passw0rd#1", "passwd") == -1      # space not allowed
    assert sefs.register_user("carol01", "Passw0rd!1", "passwd") == -1       # '!' not allowed
    assert sefs.register_user(None, "Passw0rd#1", "passwd") == -1
    assert sefs.register_user("abcdef", "abcdefghi", "passwd") == 1          # both at the minimum


def test_change_password(sefs, user):
    u, p = user
    assert sefs.change_user_password(u, "WrongPass#1", "NewPassw0rd=", "passwd") == -1
    assert sefs.change_user_password(u, p, "NewPassw0rd=", "passwd") == 1
    assert sefs.match_user(u, p, "passwd") == -1
    assert sefs.match_user(u, "NewPassw0rd=", "passwd") == 1


def test_delete_user(sefs, user):
    u, p = user
    sefs.register_user(U2, P2, "passwd")
    assert sefs.delete_user(u, "WrongPass#1", "passwd") == -1
    assert sefs.delete_user(u, p, "passwd") == 1
    assert sefs.is_user_valid(u, "passwd") == -1
    assert sefs.is_user_valid(U2, "passwd") == 1  # other users untouched


# ---------------- Part 2: single-chunk file operations ----------------

def test_create_empty_file(sefs, user, chunk_files):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.create_file("notes", u, p) == -1  # already exists
    assert sefs.file_size("notes", u, p) == 0
    assert len(chunk_files()) == 1
    assert sefs.read_from_file("notes", 0, 0, u, p) == b""


def test_encrypt_decrypt_round_trip(sefs, user, chunk_files):
    u, p = user
    Path("doc1").write_bytes(b"hello SEFS world")
    assert sefs.encrypt_file("doc1", u, p) == 1
    assert b"hello SEFS world" not in chunk_files()[0].read_bytes()
    assert sefs.read_from_file("doc1", 6, 4, u, p) == b"SEFS"
    assert sefs.read_from_file("doc1", 10, 100, u, p) is None  # past the end
    assert sefs.decrypt_file("doc1", "out.txt", u, p) == 1
    assert Path("out.txt").read_bytes() == b"hello SEFS world"


def test_write_inserts(sefs, user):
    u, p = user
    sefs.create_file("notes", u, p)
    assert sefs.write_to_file("notes", 0, b"helloworld", u, p) == 1
    assert sefs.write_to_file("notes", 5, b", ", u, p) == 1
    assert sefs.read_from_file("notes", 0, 12, u, p) == b"hello, world"
    assert sefs.write_to_file("notes", 13, b"x", u, p) == -1  # beyond the end


def test_non_owner_rejected(sefs, user):
    u, p = user
    sefs.register_user(U2, P2, "passwd")
    sefs.create_file("notes", u, p)
    sefs.write_to_file("notes", 0, b"secret", u, p)
    assert sefs.read_from_file("notes", 0, 6, U2, P2) is None
    assert sefs.write_to_file("notes", 0, b"x", U2, P2) == -1
    assert sefs.delete_file("notes", U2, P2) == -1
    assert sefs.read_from_file("notes", 0, 6, u, "WrongPass#1") is None


def test_delete_file(sefs, user, chunk_files):
    u, p = user
    sefs.create_file("notes", u, p)
    assert sefs.delete_file("notes", u, p) == 1
    assert not Path("notes.meta").exists()
    assert chunk_files() == []
    assert b"notes" not in Path("masterlist").read_bytes()
    assert sefs.file_size("notes", u, p) == -1


# ---------------- Part 3: multiple chunks ----------------

def test_chunk_round_trip_three_chunks(sefs, user, chunk_files):
    u, p = user
    data = b"A" * 1024 + b"B" * 1024 + b"C" * 500
    Path("report").write_bytes(data)
    assert sefs.encrypt_file("report", u, p) == 1
    assert len(chunk_files()) == 3
    assert sefs.file_size("report", u, p) == 2548
    assert sefs.read_from_file("report", 1019, 10, u, p) == b"AAAAABBBBB"
    assert sefs.decrypt_file("report", "out", u, p) == 1
    assert Path("out").read_bytes() == data


def test_append_to_partial_chunk_stays_one_chunk(sefs, user, chunk_files):
    u, p = user
    Path("small").write_bytes(b"s" * 512)
    sefs.encrypt_file("small", u, p)
    assert sefs.write_to_file("small", 512, b"t" * 200, u, p) == 1
    assert sefs.file_size("small", u, p) == 712
    assert len(chunk_files()) == 1


def test_write_spills_into_new_chunk(sefs, user, chunk_files):
    u, p = user
    Path("full").write_bytes(b"x" * 1024)
    sefs.encrypt_file("full", u, p)
    assert len(chunk_files()) == 1
    assert sefs.write_to_file("full", 10, b"yz", u, p) == 1
    assert len(chunk_files()) == 2
    assert sefs.read_from_file("full", 8, 6, u, p) == b"xxyzxx"
    assert sefs.read_from_file("full", 1024, 2, u, p) == b"xx"


# ---------------- Integrity / tamper detection ----------------

def test_tampered_chunk_detected(sefs, user, chunk_files):
    u, p = user
    Path("report").write_bytes(os.urandom(3000))
    sefs.encrypt_file("report", u, p)
    assert sefs.system_health_check(u, p) == 1
    victim = chunk_files()[1]
    raw = bytearray(victim.read_bytes())
    raw[100] ^= 1
    victim.write_bytes(raw)
    assert sefs.file_integrity_check("report", u, p) == -1
    assert sefs.read_from_file("report", 0, 10, u, p) is None
    assert sefs.system_health_check(u, p) == -1


def test_tampered_meta_detected(sefs, user):
    u, p = user
    Path("doc").write_bytes(b"hello")
    sefs.encrypt_file("doc", u, p)
    raw = bytearray(Path("doc.meta").read_bytes())
    raw[0] ^= 1
    Path("doc.meta").write_bytes(raw)
    assert sefs.file_integrity_check("doc", u, p) == -1
    assert sefs.read_from_file("doc", 0, 5, u, p) is None
    assert sefs.system_health_check(u, p) == -1
