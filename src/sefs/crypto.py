"""Thin wrappers around the cryptographic primitives SEFS uses.

AES-128-CTR comes from the ``cryptography`` package (OpenSSL underneath);
PBKDF2, HMAC and SHA-256 come from the standard library.
"""

import hashlib
import hmac
import secrets

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from . import config


def gen_random(n: int) -> bytes:
    """Cryptographically secure random bytes (keys, IVs, salts, chunk names)."""
    return secrets.token_bytes(n)


def aes128_ctr(key: bytes, iv: bytes, data: bytes) -> bytes:
    """AES-128 in CTR mode. Encrypting and decrypting are the same operation."""
    if len(key) != config.KEY_LEN or len(iv) != config.IV_LEN:
        raise ValueError("AES-128-CTR needs a 16-byte key and a 16-byte IV")
    ctx = Cipher(algorithms.AES(key), modes.CTR(iv)).encryptor()
    return ctx.update(data) + ctx.finalize()


def hmac_sha256(key: bytes, data: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()


def sha256(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def pbkdf2_sha1(password: bytes, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha1", password, salt, config.PBKDF2_ITER, config.HASH_LEN)


def equal(a: bytes, b: bytes) -> bool:
    """Constant-time comparison: run time does not reveal how many bytes matched."""
    return hmac.compare_digest(a, b)
