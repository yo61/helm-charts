"""Shared fixtures. Application config never leaks in from the developer's shell.

Without this, code that falls back to `os.environ` is satisfied by whatever the
developer happens to have exported, so a test passes without reaching the branch
it names — failing in CI and never locally, or the reverse.
"""

import os

import pytest

_KEEP = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "PWD"}


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key not in _KEEP:
            monkeypatch.delenv(key, raising=False)
