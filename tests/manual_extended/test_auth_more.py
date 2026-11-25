"""Manual arm, extended - authentication. Written by the tester (Daniel Odong) without AI.

Moved unchanged from tests/manual/test_auth.py on 2026-11-25, because tests/manual is frozen
at the 120-minute budget.
"""


def test_register_user_invalid(sefs):
    result = sefs.register_user("invalid_user!", "Passw0rd#1", "passwd")
    assert result == -1

def test_register_user_existing(sefs, user):
    u, p = user
    result = sefs.register_user(u, p, "passwd")
    assert result == -1

def test_match_user(sefs, user):
    u, p = user
    assert sefs.match_user(u, p, "passwd") == 1
