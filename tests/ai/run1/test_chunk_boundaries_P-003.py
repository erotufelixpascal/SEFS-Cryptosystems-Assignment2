"""P-003: chunk-boundary tests, written from CONTEXT.md only."""

import math

import pytest

CHUNK = 1024
SIZES = [0, 1, 1023, 1024, 1025, 2047, 2048, 2049, 3072, 3073]


def pattern(n, seed=0):
    """Deterministic content where nearby positions differ, so a shifted byte is noticed."""
    return bytes(((i * 7 + seed) % 251) for i in range(n))


def nchunks(size):
    return max(1, math.ceil(size / CHUNK))


def _encrypt(sefs, workdir, user, name, data):
    u, p = user
    (workdir / name).write_bytes(data)
    assert sefs.encrypt_file(name, u, p) == 1


# Part 3 s.2.1: a file of size S uses exactly max(1, ceil(S/1024)) chunks; file_size == S.
@pytest.mark.parametrize("size", SIZES)
def test_chunk_count_rule_encrypt(sefs, user, workdir, chunk_files, size):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", pattern(size))
    assert len(chunk_files()) == nchunks(size)
    assert sefs.file_size("doc", u, p) == size


# Part 3 s.1 / s.2.3: content round-trips across chunk boundaries (read whole and decrypt).
@pytest.mark.parametrize("size", SIZES)
def test_round_trip_at_boundary_sizes(sefs, user, workdir, size):
    u, p = user
    data = pattern(size)
    _encrypt(sefs, workdir, user, "doc", data)
    if size:
        assert sefs.read_from_file("doc", 0, size, u, p) == data
    assert sefs.decrypt_file("doc", "out.bin", u, p) == 1
    assert (workdir / "out.bin").read_bytes() == data


# Part 3 s.2.1 table: create_file stores one chunk with size 0.
def test_create_file_one_chunk(sefs, user, chunk_files):
    u, p = user
    assert sefs.create_file("notes", u, p) == 1
    assert len(chunk_files()) == 1
    assert sefs.file_size("notes", u, p) == 0


# Part 3 s.2.3: pos lies in chunk pos//1024 at offset pos%1024 - reads starting/ending around boundaries.
@pytest.mark.parametrize("pos,n", [
    (0, 1), (1023, 1), (1024, 1), (1025, 1), (2047, 1), (2048, 1),
    (1023, 2), (1022, 4), (2047, 2), (1014, 20), (1000, 1049), (0, 2049),
    (1, 2048), (1024, 1024), (1024, 1025),
])
def test_read_positions_around_boundaries(sefs, user, workdir, pos, n):
    u, p = user
    data = pattern(2049)
    _encrypt(sefs, workdir, user, "doc", data)
    assert sefs.read_from_file("doc", pos, n, u, p) == data[pos:pos + n]


# Part 3 demo: read 10 bytes at 1019 of A*1024+B*1024+C*500 -> b'AAAAABBBBB'; 3 chunks, size 2548.
def test_demo_report_cross_boundary(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "report", b"A" * 1024 + b"B" * 1024 + b"C" * 500)
    assert len(chunk_files()) == 3
    assert sefs.file_size("report", u, p) == 2548
    assert sefs.read_from_file("report", 1019, 10, u, p) == b"AAAAABBBBB"
    assert sefs.read_from_file("report", 2043, 10, u, p) == b"BBBBBCCCCC"


# Part 3 demo / s.2.4: insert b"xyz" at 10 shifts content, still 3 chunks; read(8, 7) == b'AAxyzAA'.
def test_demo_report_insert(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "report", b"A" * 1024 + b"B" * 1024 + b"C" * 500)
    assert sefs.write_to_file("report", 10, b"xyz", u, p) == 1
    assert sefs.read_from_file("report", 8, 7, u, p) == b"AAxyzAA"
    assert sefs.file_size("report", u, p) == 2551
    assert len(chunk_files()) == 3
    # content that was at a chunk boundary moved by 3
    assert sefs.read_from_file("report", 1022, 10, u, p) == b"AAAAABBBBB"


# Part 2 s.3 read_from_file: reading past the end returns None, at each boundary size.
@pytest.mark.parametrize("size", [1, 1023, 1024, 1025, 2047, 2048, 2049])
def test_read_past_end_at_boundaries(sefs, user, workdir, size):
    u, p = user
    data = pattern(size)
    _encrypt(sefs, workdir, user, "doc", data)
    assert sefs.read_from_file("doc", size - 1, 1, u, p) == data[-1:]   # last byte
    assert sefs.read_from_file("doc", size, 1, u, p) is None            # first byte past the end
    assert sefs.read_from_file("doc", 0, size + 1, u, p) is None
    assert sefs.read_from_file("doc", size - 1, 2, u, p) is None


# Part 3 s.2.4 / Part 2 s.3: insert at positions around boundaries gives old[:pos]+data+old[pos:],
# re-split into the minimum number of chunks.
@pytest.mark.parametrize("pos", [0, 1, 1023, 1024, 1025, 2047, 2048])
@pytest.mark.parametrize("ins_len", [1, 1024])
def test_write_positions_around_boundaries(sefs, user, workdir, chunk_files, pos, ins_len):
    u, p = user
    old = pattern(2048)
    _encrypt(sefs, workdir, user, "doc", old)
    ins = pattern(ins_len, seed=99)
    assert sefs.write_to_file("doc", pos, ins, u, p) == 1
    new = old[:pos] + ins + old[pos:]
    assert sefs.file_size("doc", u, p) == len(new)
    assert sefs.read_from_file("doc", 0, len(new), u, p) == new
    assert len(chunk_files()) == nchunks(len(new))


# Part 2 s.3 write_to_file: pos beyond the end is rejected; the file is unchanged.
@pytest.mark.parametrize("size", [0, 1023, 1024, 1025, 2048])
def test_write_beyond_end_rejected(sefs, user, workdir, chunk_files, size):
    u, p = user
    data = pattern(size)
    _encrypt(sefs, workdir, user, "doc", data)
    before = {f.name: f.read_bytes() for f in chunk_files()}
    assert sefs.write_to_file("doc", size + 1, b"x", u, p) == -1
    assert sefs.file_size("doc", u, p) == size
    after = {f.name: f.read_bytes() for f in chunk_files()}
    assert after == before
    if size:
        assert sefs.read_from_file("doc", 0, size, u, p) == data


# Part 2 s.3 / Part 3 demo: pos == size (append at the end) is allowed at every boundary size.
@pytest.mark.parametrize("size", [0, 1, 1023, 1024, 1025, 2047, 2048, 2049])
def test_append_at_end(sefs, user, workdir, chunk_files, size):
    u, p = user
    data = pattern(size)
    _encrypt(sefs, workdir, user, "doc", data)
    assert sefs.write_to_file("doc", size, b"Z", u, p) == 1
    assert sefs.file_size("doc", u, p) == size + 1
    assert sefs.read_from_file("doc", 0, size + 1, u, p) == data + b"Z"
    assert len(chunk_files()) == nchunks(size + 1)


# Part 3 s.2.5: a 512-byte chunk plus a 200-byte append stays one chunk of 712 bytes.
def test_append_to_partial_chunk_stays_one_chunk(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    assert len(chunk_files()) == 1
    assert sefs.write_to_file("small", 512, b"t" * 200, u, p) == 1
    assert sefs.file_size("small", u, p) == 712
    assert len(chunk_files()) == 1
    assert sefs.read_from_file("small", 0, 712, u, p) == b"s" * 512 + b"t" * 200


# Part 3 s.2.1 "no new chunk while the last chunk has free space": filling to exactly 1024 stays 1 chunk,
# one more byte makes 2.
def test_append_fill_then_spill(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", b"a" * 1000)
    assert sefs.write_to_file("doc", 1000, b"b" * 24, u, p) == 1
    assert sefs.file_size("doc", u, p) == 1024
    assert len(chunk_files()) == 1
    assert sefs.write_to_file("doc", 1024, b"c", u, p) == 1
    assert sefs.file_size("doc", u, p) == 1025
    assert len(chunk_files()) == 2
    assert sefs.read_from_file("doc", 1020, 5, u, p) == b"bbbbc"


# Part 3 s.2.5 with a multi-chunk file: appending to a partial last chunk does not add a chunk.
def test_append_to_partial_last_chunk_of_multichunk(sefs, user, workdir, chunk_files):
    u, p = user
    data = pattern(1500)
    _encrypt(sefs, workdir, user, "doc", data)
    assert len(chunk_files()) == 2
    assert sefs.write_to_file("doc", 1500, b"q" * 548, u, p) == 1  # -> 2048
    assert len(chunk_files()) == 2
    assert sefs.file_size("doc", u, p) == 2048
    assert sefs.read_from_file("doc", 0, 2048, u, p) == data + b"q" * 548


# Part 3 s.2.4: an insert that overflows a full chunk spills into a new chunk; later content shifts.
def test_insert_spills_into_new_chunk(sefs, user, workdir, chunk_files):
    u, p = user
    data = pattern(1024)
    _encrypt(sefs, workdir, user, "doc", data)
    assert len(chunk_files()) == 1
    assert sefs.write_to_file("doc", 0, b"!", u, p) == 1
    assert len(chunk_files()) == 2
    assert sefs.file_size("doc", u, p) == 1025
    assert sefs.read_from_file("doc", 0, 1025, u, p) == b"!" + data
    assert sefs.read_from_file("doc", 1024, 1, u, p) == data[-1:]


# Part 3 s.2.4: an insert in the middle of a nearly full chunk spills (1020 + 10 -> 1030, 2 chunks).
def test_insert_middle_spills(sefs, user, workdir, chunk_files):
    u, p = user
    data = pattern(1020)
    _encrypt(sefs, workdir, user, "doc", data)
    ins = b"0123456789"
    assert sefs.write_to_file("doc", 510, ins, u, p) == 1
    new = data[:510] + ins + data[510:]
    assert len(chunk_files()) == 2
    assert sefs.read_from_file("doc", 0, 1030, u, p) == new


# Part 3 s.2.4: a large write into an empty file is re-split into the minimum chunks (3000 -> 3).
def test_large_write_into_empty_file(sefs, user, chunk_files):
    u, p = user
    data = pattern(3000)
    assert sefs.create_file("notes", u, p) == 1
    assert sefs.write_to_file("notes", 0, data, u, p) == 1
    assert len(chunk_files()) == 3
    assert sefs.file_size("notes", u, p) == 3000
    assert sefs.read_from_file("notes", 0, 3000, u, p) == data


# Part 3 s.2.1: growing one byte at a time across 1024 and 2048 keeps the chunk count rule at every step.
def test_grow_byte_by_byte_across_boundaries(sefs, user, workdir, chunk_files):
    u, p = user
    data = pattern(1022)
    _encrypt(sefs, workdir, user, "doc", data)
    for size in range(1022, 1027):
        assert len(chunk_files()) == nchunks(size)
        assert sefs.write_to_file("doc", size, bytes([size % 256]), u, p) == 1
        data += bytes([size % 256])
    assert sefs.read_from_file("doc", 0, len(data), u, p) == data


# Part 3 s.2.6 no orphans: old chunks are removed after re-encryption, so the total on disk always
# matches the rule summed over all files (demo: 3 + 1 = 4).
def test_no_orphan_chunks_across_files(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "report", b"A" * 1024 + b"B" * 1024 + b"C" * 500)
    _encrypt(sefs, workdir, user, "small", b"s" * 512)
    assert sefs.write_to_file("small", 512, b"t" * 200, u, p) == 1
    assert len(chunk_files()) == 4
    assert sefs.write_to_file("report", 0, b"x" * 600, u, p) == 1   # 3148 -> 4 chunks
    assert len(chunk_files()) == 5


# Part 3 s.2.6: delete_file removes every chunk in the meta file.
@pytest.mark.parametrize("size", [0, 1024, 1025, 2049])
def test_delete_removes_all_chunks(sefs, user, workdir, chunk_files, size):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", pattern(size))
    _encrypt(sefs, workdir, user, "keep", b"k" * 1500)
    assert len(chunk_files()) == nchunks(size) + 2
    assert sefs.delete_file("doc", u, p) == 1
    assert len(chunk_files()) == 2
    assert sefs.read_from_file("keep", 0, 1500, u, p) == b"k" * 1500


# Part 3 s.2.4 "fresh keys and IVs for all of them" / s.2.2 step 5: after a write, all old chunk files are gone.
def test_write_replaces_every_chunk(sefs, user, workdir, chunk_files):
    u, p = user
    _encrypt(sefs, workdir, user, "doc", pattern(2049))
    before = {f.name for f in chunk_files()}
    assert sefs.write_to_file("doc", 2049, b"x", u, p) == 1   # append only touches the last chunk's content
    after = {f.name for f in chunk_files()}
    assert len(after) == 3
    assert before.isdisjoint(after)
