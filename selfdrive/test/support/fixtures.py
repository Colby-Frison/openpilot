"""
Pytest fixtures for plugging subsystem tests into shared setup.

Loaded from the repository root via ``pytest_plugins`` so any test under
``testpaths`` can request these fixtures by name.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def openpilot_params_seeded():
  """Maps: infra. Seeds Params for a minimal enabled openpilot configuration."""
  from openpilot.selfdrive.test.support.params_seed import seed_minimal_openpilot_params

  seed_minimal_openpilot_params()


@pytest.fixture
def managed_processes_ctx():
  """Maps: infra. Returns :func:`openpilot.selfdrive.test.support.processes.managed_process_scope`."""
  from openpilot.selfdrive.test.support.processes import managed_process_scope

  return managed_process_scope


@pytest.fixture
def pub_sub_factory():
  """
  Maps: infra. Build ``PubMaster`` / ``SubMaster`` pairs with explicit service lists
  (``SubMaster`` cannot be constructed with an empty service list).
  """

  def _make(pub_services: list[str], sub_services: list[str], **sub_kw):
    import cereal.messaging as messaging

    return messaging.PubMaster(pub_services), messaging.SubMaster(sub_services, **sub_kw)

  return _make
