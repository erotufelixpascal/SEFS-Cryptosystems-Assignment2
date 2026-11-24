# Part 2: Simplified SEFS (30 marks)

**Code:** [`src/sefs/fs.py`](../src/sefs/fs.py), [`chunk.py`](../src/sefs/chunk.py), [`meta.py`](../src/sefs/meta.py), [`crypto.py`](../src/sefs/crypto.py), [`util.py`](../src/sefs/util.py) · **Format:** [FILE_FORMAT.md](FILE_FORMAT.md) · **Status:** implemented, acceptance tests passing

## 1. What Part 2 must do

In the simplified SEFS each file is **one meta file plus one encrypted chunk**. Nine functions work on these files; each first checks the user's password (Part 1) and that the user owns the file.

> **Relation to Part 3:** the code is written once for the general multi-chunk case. A file of 1,024 bytes or less uses exactly one chunk, which *is* the simplified SEFS. Demonstrate Part 2 with files of 1,024 bytes or less.

## 2. Building blocks

| Module | Function | Purpose |
|---|---|---|
| `crypto` | `gen_random(n)` | Secure random bytes: keys, IVs, chunk names |
| | `aes128_ctr(key, iv, data)` | AES-128-CTR (`cryptography` package); encrypting and decrypting are the same operation |
| | `hmac_sha256(key, data)` | Chunk tamper-detection tag |
| | `sha256(data)` | Meta-file digest for the Master File List |
| `util` | `load_master_key()` | Reads `master.key` (16-byte key + 16-byte IV); never hard-coded, never committed |
| | `write_atomic(path, data)` | Temp file + `fsync` + `os.replace` |
| `chunk` | `write(name, next, data)` | Builds the body, **new random key and IV**, encrypts, computes the HMAC, saves |
| | `read(ref)` | Checks length, **checks the HMAC before decrypting**, decrypts, validates the next-name field and padding |
| `meta` | `save` / `load` | Encrypt/decrypt and parse the meta file; `save` also updates the Master File List digest |

Internal steps in `fs.py`:

| Helper | What it does |
|---|---|
| `_filename` | Letters and digits only, 1–20 characters |
| `_authorize` | `match_user` → listed in the Master File List → meta loads → (optionally) digest matches → user is the owner |
| `_verify_chain` | Reads and verifies every chunk listed in the meta file and returns the whole plaintext |
| `_store_plaintext` | Splits data into chunks, writes them, saves the meta file, and only then deletes the old chunks |

## 3. The nine functions

| Function | Steps |
|---|---|
| `create_file(f, u, p)` | Validate name → check password → refuse if `f` exists → store an empty file (one chunk, size 0) |
| `encrypt_file(f, u, p)` | Read plaintext file `f` from disk → chunk(s) with new keys and IVs → meta → digest. If `f` is already in SEFS, only its owner may replace it |
| `decrypt_file(f, pf, u, p)` | Authorize with digest check → **verify integrity first** → write the plaintext to `pf` |
| `read_from_file(f, pos, n, u, p)` | Verify → return `n` bytes from `pos` as `bytes`; `None` on any error, including reading past the end |
| `write_to_file(f, pos, data, u, p)` | Verify and decrypt → **insert** `data` at `pos` → re-encrypt with fresh keys and IVs → update meta and digest. `pos` beyond the end is rejected |
| `file_size(f, u, p)` | Size from the meta file (after the digest check), or -1 |
| `file_integrity_check(f, u, p)` | Recompute the meta digest and every chunk HMAC and link |
| `delete_file(f, u, p)` | Owner only → remove chunks, meta file and Master File List entry |
| `system_health_check(u, p)` | Integrity-check every file in the Master File List; -1 if any fails |

`write_to_file` accepts `bytes` or `str` (encoded as UTF-8).

## 4. Rules respected

| Rule from the brief | How |
|---|---|
| Fresh IV whenever a chunk is re-encrypted | `chunk.write` always generates a new key and IV |
| Integrity before decryption | `chunk.read` verifies the HMAC before calling AES |
| Validate every input | File names, types, negative or out-of-range positions and lengths |
| Binary file mode | All files opened `"rb"` / `"wb"` / `"ab"` |
| Crash-safe updates | Temp file then `os.replace` for chunks, meta and Master File List |

## 5. Demonstration

First make sure the package is installed in the active venv (once, from the project folder): `pip install -e .`. Without it, `python -m sefs` fails with `No module named sefs`.

`doc1` must contain exactly `hello SEFS world` (16 bytes, no trailing newline), or the expected outputs below will not match. Use the block for the terminal you are in. The prompt shows which: `C:\...>` is Command Prompt, `PS C:\...>` is PowerShell.

**Command Prompt (cmd.exe)**

```bat
mkdir demo
cd demo
python -m sefs keygen
<nul set /p ="hello SEFS world" > doc1
python
```

**PowerShell**

```powershell
mkdir demo; cd demo
python -m sefs keygen
Set-Content -NoNewline -Encoding ascii doc1 "hello SEFS world"
python
```

`Set-Content` only exists in PowerShell; in cmd it fails with `'Set-Content' is not recognized`. If `demo` already exists, skip `mkdir`. To start again from scratch, delete the old `demo` folder first.

```python
import sefs
U, PW = "alice01", "Passw0rd#1"
sefs.register_user(U, PW, "passwd")                  # 1
sefs.create_file("notes", U, PW)                     # 1   empty file, one chunk
sefs.file_size("notes", U, PW)                       # 0
sefs.write_to_file("notes", 0, b"helloworld", U, PW) # 1
sefs.write_to_file("notes", 5, b", ", U, PW)         # 1   insert in the middle
sefs.read_from_file("notes", 0, 12, U, PW)           # b'hello, world'

sefs.encrypt_file("doc1", U, PW)                     # 1
sefs.read_from_file("doc1", 6, 4, U, PW)             # b'SEFS'
sefs.read_from_file("doc1", 10, 100, U, PW)          # None  past the end
sefs.decrypt_file("doc1", "doc1_out.txt", U, PW)     # 1
sefs.file_integrity_check("doc1", U, PW)             # 1
sefs.system_health_check(U, PW)                      # 1

sefs.register_user("mallory1", "Mall0ry#pw", "passwd")
sefs.delete_file("doc1", "mallory1", "Mall0ry#pw")   # -1  not the owner
sefs.delete_file("doc1", U, PW)                      # 1
```

**Show the encryption:** open a file in `demo\chunks\` in a hex viewer. The text `hello SEFS world` does not appear.

**Automated tests:** `python -m pytest tests\acceptance -v -k "create_empty or encrypt_decrypt or write_inserts or non_owner or delete_file"`

## 6. Marking checklist

- [x] Crypto helpers; master key loaded from a file
- [x] Meta file, chunk file and Master File List formats
- [x] All nine functions with password and ownership checks
- [x] Fresh key and IV on every re-encryption; integrity before decryption
- [x] Input validation and crash-safe writes
- [x] Q1, Q3–Q7 settled: the group kept the current values (see the README, "Open specification points")
- [x] Record the demonstration output in `logs/` (`logs/part_2_log.txt` and `logs/part_2_log.csv`)
