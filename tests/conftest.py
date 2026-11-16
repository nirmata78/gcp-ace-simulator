"""The bank every test runs on.

The question bank is private and not in the repository, so the tests run on a generated fixture bank
(``tests/fixture_bank.py``) that has the bank's shape and none of its content. To run the same tests on a real bank,
point ``ACE_TEST_BANK_DIR`` at it, for example ``ACE_TEST_BANK_DIR=banks/private pytest -q``.

``ACE_BANK_DIR`` is set for the whole session, so ``load_bank()``, ``kb.py`` and the app all read the test bank,
never a bank of your own by accident.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from tests.fixture_bank import write

_chosen = os.environ.get("ACE_TEST_BANK_DIR")
TEST_BANK: Path = (Path(_chosen).expanduser().resolve() if _chosen
                   else write(Path(tempfile.mkdtemp(prefix="ace-fixture-bank-"))))
os.environ["ACE_BANK_DIR"] = str(TEST_BANK)
#: True when the tests run on the generated bank rather than a real one.
FIXTURE = not _chosen


@pytest.fixture(scope="session")
def bank_dir() -> Path:
    """The folder of the bank under test: ``sections/``, ``register.json`` and ``retired.json``."""
    return TEST_BANK
