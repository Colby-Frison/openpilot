"""Params presets commonly required by ``system/*`` tests."""

from __future__ import annotations

from openpilot.common.params import Params


def seed_system_daemon_params() -> None:
  """
  Baseline Params used by many daemon tests (e.g. loggerd uploader patterns).

  Matches common setup in ``system/loggerd/tests/loggerd_tests_common.py``.
  """
  params = Params()
  params.put("IsOffroad", "1")
  params.put("DongleId", "0000000000000000")


def seed_full_stack_params() -> None:
  """Minimal selfdrive Params plus :func:`seed_system_daemon_params` for cross-layer tests."""
  from openpilot.selfdrive.test.support.params_seed import seed_minimal_openpilot_params

  seed_minimal_openpilot_params()
  seed_system_daemon_params()
