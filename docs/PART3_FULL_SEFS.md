# Part 3: Full Multi-Chunk SEFS (45 marks)

**Code:** [`src/sefs/fs.py`](../src/sefs/fs.py) (mainly `_store_plaintext` and `_verify_chain`), [`chunk.py`](../src/sefs/chunk.py), [`meta.py`](../src/sefs/meta.py) · **Status:** implemented, acceptance tests passing

## 1. What Part 3 must do

A file spans **many chunks**, each holding at most 1,024 bytes of plaintext, linked like a list. The nine Part 2 functions must work across chunk boundaries.

```
report.meta  (start = A, end = C, 3 chunks, size 2,548)
     │
     ▼
 ┌─────────┐ next  ┌─────────┐ next  ┌─────────┐ next
 │ chunk A │──────►│ chunk B │──────►│ chunk C │──────► NULL
 │ 1,024 B │       │ 1,024 B │       │  500 B  │
 └─────────┘       └─────────┘       │+ padding│
                                     └─────────┘
```

Each chunk has its **own** random key, IV and name. The meta file lists them in order with each chunk's key and HMAC.

## 2. Rules and how each is met

### 2.1 Chunk count
A file of size S uses exactly **max(1, ⌈S / 1024⌉)** chunks (`_nchunks`). No new chunk is created while the last chunk has free space.

| Size | Chunks |
|---|---|
| 0 | 1 (empty) |
| 1 – 1,024 | 1 |
| 1,025 – 2,048 | 2 |
| 2,049 – 3,072 | 3 |

`_verify_chain` rejects a meta file whose chunk count breaks this rule.

### 2.2 Splitting
`_store_plaintext`:
1. Picks all `n` random chunk names first, so each chunk can record the next one's name.
2. For each 1,024-byte block: new key and IV, size field, padding for the last block, next name (`NULL` for the last).
3. Writes each chunk with `chunk.write`.
4. Saves the meta file (count, size, start, end, one line per chunk), which also updates the Master File List digest.
5. **Only then** deletes the old chunks. If any step fails first, the new chunks are removed and the old file is untouched.

### 2.3 Position mapping and reading across chunks
Position `pos` lies in chunk `pos // 1024` at offset `pos % 1024`. `_verify_chain` decrypts the chain into one buffer in chain order, so a read such as 20 bytes from position 1,014 takes 10 bytes from chunk A and 10 from chunk B, with no separate offset arithmetic to get wrong. **Every chunk's HMAC is verified before its plaintext is used.**

### 2.4 Writing and inserting
`write_to_file` verifies and decrypts the whole chain, builds `old[:pos] + data + old[pos:]`, and re-splits into the minimum number of chunks with fresh keys and IVs for all of them.

### 2.5 Appending to a partial chunk
A 512-byte chunk plus a 200-byte append stays **one chunk of 712 bytes**, because ⌈712 / 1024⌉ = 1.

### 2.6 Consistent meta updates and no orphans
Count, size, start, end and every chunk line are rebuilt together and written once (temp file + `os.replace`). Old chunks are removed only after the new meta is saved; `delete_file` removes every chunk in the meta file.

### 2.7 Integrity across the chain

| Attack | How it is detected |
|---|---|
| Modified chunk (any byte) | HMAC mismatch |
| Missing chunk | Chunk file can't be read |
| Swapped chunks | Each is checked with the other's key → HMAC mismatch |
| Extra chunk / changed link | Editing a next-link changes the chunk → HMAC mismatch; count and size checks fail too |
| Broken next link | Decrypted next name ≠ next chunk line in the meta file |
| Wrong count or size in meta | Count must equal ⌈size/1024⌉; sizes must add up; all chunks but the last must be full |
| Edited meta file | SHA-256 no longer matches the Master File List |
| Wrong start/end name | Must equal the first and last chunk line |

`system_health_check` runs this on every file in the Master File List.

## 3. Demonstration

```powershell
mkdir demo; cd demo
python -m sefs keygen
python
```

```python
import sefs, glob, pathlib
U, PW = "alice01", "Passw0rd#1"
sefs.register_user(U, PW, "passwd")
chunks = lambda: len(glob.glob("chunks/*"))

pathlib.Path("report").write_bytes(b"A" * 1024 + b"B" * 1024 + b"C" * 500)
sefs.encrypt_file("report", U, PW)              # 1
chunks()                                        # 3
sefs.file_size("report", U, PW)                 # 2548
sefs.read_from_file("report", 1019, 10, U, PW)  # b'AAAAABBBBB'  across a boundary

sefs.write_to_file("report", 10, b"xyz", U, PW) # insert: content shifts, still 3 chunks
sefs.read_from_file("report", 8, 7, U, PW)      # b'AAxyzAA'

pathlib.Path("small").write_bytes(b"s" * 512)
sefs.encrypt_file("small", U, PW)
sefs.write_to_file("small", 512, b"t" * 200, U, PW)
sefs.file_size("small", U, PW)                  # 712
chunks()                                        # 4  (3 + 1)

sefs.system_health_check(U, PW)                 # 1
victim = sorted(glob.glob("chunks/*"))[0]
raw = bytearray(open(victim, "rb").read()); raw[100] ^= 1
open(victim, "wb").write(raw)
sefs.system_health_check(U, PW)                 # -1  tampering detected
```

Then `sefs.file_integrity_check("report", U, PW)` and `sefs.file_integrity_check("small", U, PW)` show which file was hit. Try deleting or swapping chunk files too.

**Automated tests:** `python -m pytest tests\acceptance -v -k "chunk_round_trip or partial_chunk or spills or tampered"`

## 4. Marking checklist

- [x] Linked list of chunks, at most 1,024 bytes each
- [x] Exactly max(1, ⌈S/1024⌉) chunks
- [x] New key, IV and random name per chunk; last chunk padded; `NULL` link
- [x] Reads across chunk boundaries, HMAC verified first
- [x] Inserts shift later content; re-split to the minimum chunks
- [x] Append to a partial chunk stays in that chunk
- [x] Meta updated consistently and atomically; old chunks removed only afterwards
- [x] Detects modified, missing, swapped and extra chunks, and broken links
- [x] Record the demonstration output in `logs/` (`logs/part_3_log.txt` and `logs/part_3_log.csv`)
