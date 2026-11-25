"""Manual arm, extended - round trips. Written by the tester (Daniel Odong) without AI.

Moved unchanged from tests/manual/test_roundtrip.py on 2026-11-25, because tests/manual is frozen
at the 120-minute budget.
"""


def test_write_nonexistent_file(sefs, user):
    u, p = user
    assert sefs.write_to_file("nonexistent.txt", 0, b"Hello_World", u, p) == -1

def test_decrypt_nonexistent_file(sefs, user):
    u, p = user
    assert sefs.decrypt_file("nonexistent.txt", "output.txt", u, p) == -1
