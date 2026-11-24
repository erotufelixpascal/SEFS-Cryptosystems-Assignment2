# SEFS on-disk format (reference)

This is the format our implementation writes and reads. Any other group using the same format can read our files, and we can read theirs. Values marked † were open specification points; Q1–Q8 have been settled by the group, keeping the values shown (see the [README](../README.md#open-specification-points)). Every constant lives in [`src/sefs/config.py`](../src/sefs/config.py).

All files are binary, with `\n` line endings only, and live in the current working directory:

```
passwd            user accounts (Part 1)
master.key        master key and IV
masterlist        Master File List
<name>.meta       one encrypted meta file per SEFS file
chunks/<32 hex>   encrypted chunks
```

---

## 1. `passwd`

One line per user:

```
<username>:<salt hex>:<hash hex>\n
```

| Field | Value |
|---|---|
| username | 6–31 chars `[A-Za-z0-9]` † |
| salt | 32 random bytes → 64 hex chars |
| hash | PBKDF2-HMAC-SHA1(password, salt, 20,000 iterations), 20 bytes † → 40 hex chars |
| hex case | lowercase written †; uppercase and lowercase both accepted when reading |

Passwords are 9–31 chars of `[A-Za-z0-9@#$%&*()-+=]` †.

## 2. `master.key`

Exactly 32 bytes: a 16-byte AES-128 key followed by a 16-byte IV †. Create one with `python -m sefs keygen`.

## 3. Chunk file `chunks/<name>`

`<name>` is 32 lowercase hex chars (16 random bytes) †. Every chunk file is exactly **1,076 bytes**:

```
offset  length  content
     0      16  IV (plaintext, random, new on every write)
    16    1060  AES-128-CTR(chunk key, IV) of the body:
                  body[0:32]     next chunk name (ASCII); "NULL" + 28 zero bytes for the last chunk †
                  body[32:36]    content size, unsigned 32-bit big-endian †
                  body[36:1060]  content, padded to 1,024 bytes with 0x00 †
```

**Chunk HMAC** = HMAC-SHA256(chunk key, all 1,076 bytes of the file) †. It is stored in the meta file, not in the chunk. On read the HMAC is checked **before** decrypting †.

Every chunk has its own random 16-byte key. A new key and IV are generated each time a chunk is written, so a CTR keystream is never reused for chunk data.

## 4. Meta file `<name>.meta`

AES-128-CTR(master key, master IV) of this ASCII text †:

```
<owner>\n
<number of chunks>\n
<file size in bytes>\n
<start chunk name>\n
<end chunk name>\n
<chunk name> <chunk key hex> <chunk HMAC hex>\n     ← one line per chunk, in chain order
```

Rules checked on every read:

- number of chunks = max(1, ⌈size / 1024⌉);
- the start and end names equal the first and last chunk lines;
- every chunk except the last holds exactly 1,024 bytes, and its next-name field names the next chunk line;
- the last chunk's next-name field is `NULL`;
- the chunk sizes add up to the file size.

## 5. Master File List `masterlist`

Plaintext †, one line per SEFS file:

```
<name> <SHA-256 hex of the <name>.meta bytes as stored on disk>\n
```

Changing any byte of a meta file changes its SHA-256, so the edit is detected.

## 6. Worked example

`encrypt_file("doc")` on the 5-byte plaintext `hello` by `alice01` produces:

```
masterlist   doc 5be1…(64 hex)\n
doc.meta     AES-CTR(master) of:
               alice01\n1\n5\n3fa9…\n3fa9…\n3fa9… 8c02…(32 hex) 77de…(64 hex)\n
chunks/3fa9…  IV(16) ‖ AES-CTR(chunk key, IV)( "NULL"+0×28 ‖ 00 00 00 05 ‖ "hello" + 0×1019 )
```

The known-answer tests in [`tests/format/test_format_kat.py`](../tests/format/test_format_kat.py) build these files by hand with plain `hashlib` and `cryptography` calls and check that SEFS reads them. If another group's files fail to load, those tests are the quickest way to find which field differs.
