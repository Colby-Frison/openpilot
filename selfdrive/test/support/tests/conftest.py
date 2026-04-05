"""
Harness-only conftest for ``selfdrive/test/support/tests``.

This package intentionally starts with **no** ``test_*.py`` files so new tests can
be dropped in without changing wiring. Pytest normally exits with code 5 when
nothing is collected; we map that to success so CI and local runs stay green.
"""

from __future__ import annotations

import pytest


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
  from _pytest.main import ExitCode

  if exitstatus == ExitCode.NO_TESTS_COLLECTED:
    session.exitstatus = ExitCode.OK
