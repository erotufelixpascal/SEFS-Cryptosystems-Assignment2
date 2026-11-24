"""Master key generator: writes 16 random key bytes followed by 16 random IV bytes."""

import os

from . import config, crypto


def generate_master_key(path: str = config.MASTER_KEY_FILE, overwrite: bool = False) -> int:
    """Create a fresh master key file. Refuses to overwrite an existing key unless asked,
    because every meta file encrypted under the old key would become unreadable."""
    if os.path.exists(path) and not overwrite:
        return config.ERR
    data = crypto.gen_random(config.KEY_LEN) + crypto.gen_random(config.IV_LEN)
    try:
        with open(path, "wb") as f:
            f.write(data)
    except OSError:
        return config.ERR
    return config.OK
