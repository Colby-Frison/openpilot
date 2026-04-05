"""
Harness-only conftest for ``system/tests/support/tests``.

Add ``test_*.py`` files here for cross-cutting system tests; until then the suite
is empty and maps "no tests collected" to exit 0 (same behavior as
``selfdrive/test/support/tests``).
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
  from _pytest.main import ExitCode

  if exitstatus == ExitCode.NO_TESTS_COLLECTED:
    session.exitstatus = ExitCode.OK
