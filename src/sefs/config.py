"""Every format decision for SEFS lives here.

Values marked ``TODO-confirm`` are placeholders for the open specification
points (Q1-Q9 in README.md). Change them here once the lecturer answers;
no other module needs editing for a constant change.

The on-disk format these values define is documented in docs/FILE_FORMAT.md,
so any implementation following it can read files written by this one.
"""

# Return codes used by every public function
OK = 1
ERR = -1

# Files, relative to the current working directory
PASSWD_FILE = "passwd"
MASTER_KEY_FILE = "master.key"  # 16-byte key then 16-byte IV (TODO-confirm: lecturer's sample format)
MASTER_LIST = "masterlist"
CHUNK_DIR = "chunks"
META_EXT = ".meta"

# Part 1: authentication
SALT_LEN = 32
HASH_LEN = 20            # PBKDF2-HMAC-SHA1 output length (decided Q2)
PBKDF2_ITER = 20000
HEX_UPPER = False        # write lowercase hex (decided Q2); reading accepts both cases
USER_MIN = 6
USER_MAX = 31            # decided Q8
PASS_MIN = 9
PASS_MAX = 31            # decided Q8
PASS_EXTRA = "@#$%&*()-+="

# Parts 2-3: file system
FILENAME_MAX = 20
MAX_FILE_SIZE = 64 * 1024 * 1024
KEY_LEN = 16
IV_LEN = 16
HMAC_LEN = 32
DIGEST_LEN = 32
CHUNK_SIZE = 1024
PAD_BYTE = 0x00          # "ASCII character 0": byte 0x00 or '0' (0x30)? (decided Q1: 0x00)
CHUNK_NAME_BYTES = 16    # random bytes; the name is their hex, 32 chars (decided Q5)
CHUNK_NAME_LEN = 2 * CHUNK_NAME_BYTES
NULL_NAME = b"NULL"
REMOVE_PLAINTEXT = False  # encrypt_file deletes the plaintext afterwards? (TODO-confirm)

# Chunk file layout (decided Q3, Q5):
#   IV (16 bytes, plaintext)
#   AES-128-CTR(chunk key, IV) of:
#     next chunk name   32 bytes, "NULL" + zero bytes for the last chunk
#     content size       4 bytes, big-endian unsigned
#     content         1024 bytes, padded with PAD_BYTE
# Chunk HMAC = HMAC-SHA256(chunk key, IV || ciphertext), i.e. over the whole chunk file.
#
# Meta file F.meta (decided Q4): AES-128-CTR(master key, master IV) of the text
#   owner\n chunk count\n file size\n start chunk\n end chunk\n
#   then per chunk: name<space>keyhex<space>hmachex\n
#
# Master File List (decided Q6): plaintext, one "filename<space>sha256hex\n" per file,
#   where the digest is over the meta file bytes as stored (ciphertext).
NEXT_FIELD_LEN = 32
SIZE_FIELD_LEN = 4
BODY_LEN = NEXT_FIELD_LEN + SIZE_FIELD_LEN + CHUNK_SIZE
CHUNK_FILE_LEN = IV_LEN + BODY_LEN

assert NEXT_FIELD_LEN >= CHUNK_NAME_LEN, "next-chunk field must hold a full chunk name"
