"""Context managers around ``managed_processes`` for tests."""

from __future__ import annotations

from collections.abc import Sequence
from contextlib import contextmanager


@contextmanager
def managed_process_scope(
  names: Sequence[str],
  *,
  init_time: float = 0,
  ignore_stopped: list[str] | None = None,
):
  """
  Start a set of named processes, yield, then stop them (even on failure).

  Wraps ``selfdrive.test.helpers.processes_context`` with a stable import path
  for new tests.
  """
  from openpilot.selfdrive.test.helpers import processes_context

  with processes_context(list(names), init_time=init_time, ignore_stopped=ignore_stopped):
    yield
