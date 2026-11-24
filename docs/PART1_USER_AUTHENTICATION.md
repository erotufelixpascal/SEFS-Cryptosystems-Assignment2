# Part 1: User Authentication (20 marks)

**Code:** [`src/sefs/auth.py`](../src/sefs/auth.py) · **Settings:** [`src/sefs/config.py`](../src/sefs/config.py) · **Status:** implemented, acceptance tests passing

## 1. What Part 1 must do

Five functions manage users in a password file. Each returns **1** (OKAY) or **-1** (ERROR).

| Function | Purpose |
|---|---|
| `register_user(u, p, pFile)` | Add a new user |
| `delete_user(u, p, pFile)` | Remove a user, only with the correct password |
| `is_user_valid(u, pFile)` | Does this username exist? |
| `match_user(u, p, pFile)` | Is this the right password? (the login) |
| `change_user_password(u, p, pn, pFile)` | Replace the password, only with the correct old one |

Arguments may be `str` or ASCII `bytes`. Anything else (including `None`) returns -1.

## 2. The core idea: passwords are never stored

```
alice01:9f3a…(64 hex)…:c81e…(40 hex)…
└─user─┘ └─ salt (32 B) ─┘ └─ hash (20 B) ─┘
```

| Term | Meaning | Why |
|---|---|---|
| **Salt** | 32 random bytes per user (`secrets.token_bytes`) | Two users with the same password get different hashes; pre-computed rainbow tables are useless |
| **Hash** | PBKDF2-HMAC-SHA1(password, salt, 20,000 iterations, 20 bytes) | One-way; 20,000 rounds make every guess slow for an attacker |

**Login** = hash the password the user typed with their stored salt, and compare it with the stored hash in constant time (`hmac.compare_digest`).

## 3. Input rules

| Field | Allowed characters | Length | Constants |
|---|---|---|---|
| Username | `a-z A-Z 0-9` | 6–31 | `USER_MIN`, `USER_MAX` |
| Password | `a-z A-Z 0-9 @ # $ % & * ( ) - + =` | 9–31 | `PASS_MIN`, `PASS_MAX`, `PASS_EXTRA` |

Only ASCII letters and digits count: `é` or a full-width digit is rejected.

## 4. How each function works

| Helper | What it does |
|---|---|
| `valid_username` / `valid_password` | Apply the rules above |
| `_hash_password` | PBKDF2-HMAC-SHA1 with the configured iterations and length |
| `_find_user` | Finds the line whose name before the first `:` **exactly** equals `u` (so `alice01` never matches `alice012`); decodes salt and hash. Returns found / not found / damaged line |
| `_make_entry` | Fresh random salt + hash → `u:salthex:hashhex\n` |
| `_rewrite_user` | Rewrites the file with one user's line replaced or dropped, via a temp file and `os.replace` |

- **`register_user`:** validate both inputs → refuse if the user exists (or their line is damaged) → append a new entry.
- **`match_user`:** validate → look up salt and hash → re-hash → constant-time compare.
- **`is_user_valid`:** validate the username → 1 if found.
- **`delete_user`:** `match_user` must succeed → drop only that line.
- **`change_user_password`:** validate the new password → `match_user` with the old one → new entry with a **fresh salt** → replace only that line.

## 5. Safety rules applied

| Rule | How |
|---|---|
| Crash-safe updates | Write `passwd.tmp`, `fsync`, then `os.replace`; the original is never half-written |
| Interoperable files | Binary mode, `\n` only |
| Constant-time comparison | `hmac.compare_digest` |
| Secure randomness | `secrets.token_bytes` (OS CSPRNG) |

## 6. Demonstration

```powershell
.venv\Scripts\Activate.ps1
mkdir demo; cd demo
python
```

```python
import sefs
P = "passwd"
sefs.register_user("alice01", "Passw0rd#1", P)      #  1
sefs.register_user("alice01", "Passw0rd#1", P)      # -1  duplicate
sefs.register_user("bob", "Passw0rd#1", P)          # -1  username too short
sefs.register_user("carol01", "short", P)           # -1  password too short
sefs.is_user_valid("alice01", P)                    #  1
sefs.match_user("alice01", "Passw0rd#1", P)         #  1
sefs.match_user("alice01", "WrongPass#1", P)        # -1
sefs.change_user_password("alice01", "Passw0rd#1", "NewPassw0rd=", P)  # 1
sefs.match_user("alice01", "Passw0rd#1", P)         # -1  old password no longer works
sefs.delete_user("alice01", "NewPassw0rd=", P)      #  1
sefs.is_user_valid("alice01", P)                    # -1
```

Open `passwd` in Notepad between calls to show the line being added, changed (new salt and hash) and removed.

**Automated tests:** `python -m pytest tests\acceptance -v -k "register or passwd_file or validation or change_password or delete_user"` (5 tests).

## 7. Marking checklist

- [x] All five functions implemented, returning 1 / -1
- [x] Username and password validation, including boundaries and non-ASCII input
- [x] 32-byte random salt per user; fresh salt on password change
- [x] PBKDF2-HMAC-SHA1, 20,000 iterations
- [x] Constant-time comparison
- [x] Crash-safe rewrite for delete and change
- [x] Q2 and Q8 settled: the group kept the current values (see the README, "Open specification points")
- [x] Record the demonstration output in `logs/` (`logs/part_1_log.txt` and `logs/part_1_log.csv`)
