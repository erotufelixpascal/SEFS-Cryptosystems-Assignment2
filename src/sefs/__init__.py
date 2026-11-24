"""SEFS: Secure Encrypted File System (Group 6, Python implementation).

All functions work on files in the current working directory (``passwd``,
``master.key``, ``masterlist``, ``*.meta`` and ``chunks/``) and return
1 (OKAY) or -1 (ERROR), except ``read_from_file`` (bytes or None) and
``file_size`` (size or -1).
"""

from .auth import (
    change_user_password,
    delete_user,
    is_user_valid,
    match_user,
    register_user,
    valid_password,
    valid_username,
)
from .config import ERR, OK
from .fs import (
    create_file,
    decrypt_file,
    delete_file,
    encrypt_file,
    file_integrity_check,
    file_size,
    read_from_file,
    system_health_check,
    write_to_file,
)
from .keygen import generate_master_key

__version__ = "1.0.0"

__all__ = [
    "OK", "ERR",
    "register_user", "delete_user", "is_user_valid", "match_user", "change_user_password",
    "valid_username", "valid_password",
    "create_file", "encrypt_file", "decrypt_file", "read_from_file", "write_to_file",
    "file_size", "file_integrity_check", "delete_file", "system_health_check",
    "generate_master_key",
]
