# Cross-Group Interoperability (5 marks)

**Format:** [FILE_FORMAT.md](FILE_FORMAT.md) · **Settings:** [`src/sefs/config.py`](../src/sefs/config.py) · **Log:** [`logs/interop_log.csv`](../logs/interop_log.csv) · **Status:** not started; needs the lecturer's answers and partner groups.

## 1. What interoperability means

Every group writes its own SEFS against the same lecturer-approved format, so:

- our code can decrypt files another group created, and theirs can decrypt ours;
- `passwd` entries created by one implementation verify in the other.

A single difference (padding byte, hex case, a separator, field order) makes the files unreadable to the other group. Don't finalise the format until the lecturer has answered Q1–Q9.

## 2. Procedure

### Step 1: get the agreed format
1. Read `SEFS_Lecturer_Technical_Clarifications.md`; email the lecturer about anything it doesn't settle.
2. Record each answer in the README table.

### Step 2: update the code
1. Change the constants in `src/sefs/config.py`. For layout changes (field order, separators) edit `chunk.write` / `chunk.read` or `meta._serialize` / `meta._parse`.
2. Update the known-answer tests in `tests/format/` to the agreed format.
3. `python -m pytest tests\acceptance tests\format -v` must still pass.

### Step 3: agree the exchange with partner groups (Q9)
- **A shared throwaway master key** used only for interop, never your real one.
- **Test user:** e.g. `group6user` / `Interop#2026`.
- **Test files:**

| File | Size | Why |
|---|---|---|
| `empty` | 0 B | one empty chunk |
| `small` | 100 B | single chunk with padding |
| `exact` | 1,024 B | exactly full, must be 1 chunk |
| `twochunk` | 1,025 B | spills by 1 byte |
| `multi` | 3,000 B | 3 chunks |
| `binary` | 2,000 random bytes, incl. 0x00, 0x0D, 0x1A | catches text-mode bugs |

- **Exchange package:** a zip with `passwd`, `masterlist`, `*.meta`, `chunks/` and the original plaintexts (for byte-for-byte comparison).

### Step 4: produce our files

```powershell
mkdir interop\out; cd interop\out
# copy the shared master.key here, and the six plaintext files
python -m sefs register group6user -p Interop#2026
foreach ($f in "empty","small","exact","twochunk","multi","binary") { python -m sefs encrypt $f -u group6user -p Interop#2026 }
python -m sefs health -u group6user -p Interop#2026
```

Zip `passwd`, `masterlist`, `*.meta`, `chunks\` and the plaintexts.

### Step 5: test their files (incoming)
In a fresh folder with their package and the shared key:

| Check | Command | Expected |
|---|---|---|
| Their passwd verifies | `python -m sefs login their_user -p their_pw` | OKAY |
| Integrity | `python -m sefs health -u their_user -p their_pw` | OKAY |
| Size | `python -m sefs size multi -u …` | 3000 |
| Content | `python -m sefs decrypt multi multi.out -u …`, then `fc.exe /b multi multi.out` | no differences |
| Boundary read | `python -m sefs read multi 1020 10 -u …` | bytes 1,020–1,029 of the original |

### Step 6: they test ours (outgoing)
Ask them to run the same checks on our package and report the results.

### Step 7: log everything
One row per check in `logs/interop_log.csv`:

```
date,group,direction,file_or_entry,result,mismatch,resolution
2026-11-25,Group 3,incoming,multi,pass,,
2026-11-25,Group 3,incoming,passwd,fail,hash written in uppercase hex,both sides now accept either case
2026-11-25,Group 3,outgoing,binary,pass,,
```

## 3. Debugging order when something doesn't match

Work from the outside in:

1. **passwd fails:** compare one line by eye (hex case, 64-hex salt, 40-hex hash, `:` separators).
2. **Master File List digest fails:** they hash different bytes (e.g. the plaintext meta).
3. **Meta won't decrypt or parse:** different master key/IV, field order, separators, or `\r\n`. Decrypt by hand: `aes128_ctr(key, iv, open("x.meta","rb").read())`.
4. **Chunk HMAC fails:** HMAC over different data (plaintext vs ciphertext, with or without the IV) or a different key.
5. **HMAC passes but content is wrong:** padding byte, size-field byte order, or next-name field width.

`tests/format/test_format_kat.py` builds each structure by hand and is the fastest place to try a suspected difference.

## 4. Windows traps (already handled)

| Trap | Protection |
|---|---|
| Text mode turns `\n` into `\r\n` and stops at 0x1A | Every file opened in binary mode |
| Git converting line endings | `.gitattributes` `* -text` |
| PowerShell `>` writes UTF-16 | Create test plaintexts with Python or `Set-Content -Encoding ascii` |

## 5. Checklist

- [ ] Lecturer's answers recorded in README; `config.py` and `tests/format` updated; tests pass
- [ ] Shared key, user and file set agreed with at least one other group
- [ ] Incoming: their files and passwd verify with our code
- [ ] Outgoing: our files and passwd verify with their code
- [ ] Every check and mismatch logged in `logs/interop_log.csv`
