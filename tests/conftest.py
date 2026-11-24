"""Shared fixtures for every test suite (acceptance, manual, AI runs).

Each test runs in a fresh temporary folder with a throwaway master.key, so
no test can see another test's files and the project folder stays clean.

``SEFS_SRC`` (set by tools/run_mutants.py) points the tests at a mutated
copy of the package instead of src/.
"""

import os
import sys
from pathlib import Path

_src = os.environ.get("SEFS_SRC")
if _src:
    sys.path.insert(0, _src)
    for mod in [m for m in sys.modules if m == "sefs" or m.startswith("sefs.")]:
        del sys.modules[mod]

import pytest  # noqa: E402

import sefs as _sefs  # noqa: E402

if _src and not Path(_sefs.__file__).resolve().is_relative_to(Path(_src).resolve()):
    raise RuntimeError(f"SEFS_SRC={_src} is set but sefs was imported from {_sefs.__file__}")

USER = "alice01"
PASSWORD = "Passw0rd#1"


@pytest.fixture
def sefs(tmp_path, monkeypatch):
    """The sefs module, with the working directory set to an empty temp folder holding a master key."""
    monkeypatch.chdir(tmp_path)
    assert _sefs.generate_master_key() == _sefs.OK
    return _sefs


@pytest.fixture
def user(sefs):
    """(username, password) of a registered user."""
    assert sefs.register_user(USER, PASSWORD, "passwd") == sefs.OK
    return USER, PASSWORD


@pytest.fixture
def workdir(sefs) -> Path:
    """The temp folder the current test runs in."""
    return Path.cwd()


@pytest.fixture
def chunk_files(sefs):
    """A function returning every chunk file on disk, sorted by name.

    (A fixture rather than an importable helper, because --import-mode=importlib
    keeps tests/ off sys.path.)
    """
    def _list() -> list[Path]:
        d = Path.cwd() / "chunks"
        if not d.exists():
            return []
        return sorted(p for p in d.iterdir() if p.is_file() and not p.name.endswith(".tmp"))
    return _list
