"""Params presets for tests that need a minimal “openpilot enabled” state."""

from __future__ import annotations


def seed_minimal_openpilot_params() -> None:
  """Apply the same baseline Params as ``selfdrive.test.helpers.set_params_enabled``."""
  from openpilot.selfdrive.test.helpers import set_params_enabled

  set_params_enabled()
