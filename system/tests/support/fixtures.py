"""
Pytest fixtures for ``system/*`` tests (names prefixed with ``system_`` to avoid
clashing with :mod:`openpilot.selfdrive.test.support.fixtures`).
"""

from __future__ import annotations

import pytest


@pytest.fixture
def system_daemon_params():
  """Maps: infra. Params many ``system/*`` daemons expect (offroad, dongle id)."""
  from openpilot.system.tests.support.params_seed import seed_system_daemon_params

  seed_system_daemon_params()


@pytest.fixture
def system_full_stack_params():
  """Maps: infra. Selfdrive minimal Params plus :func:`seed_system_daemon_params`."""
  from openpilot.system.tests.support.params_seed import seed_full_stack_params

  seed_full_stack_params()


@pytest.fixture
def system_managed_processes_ctx():
  """Maps: infra. Returns :func:`openpilot.selfdrive.test.support.processes.managed_process_scope`."""
  from openpilot.selfdrive.test.support.processes import managed_process_scope

  return managed_process_scope


@pytest.fixture
def system_pub_sub_factory():
  """Maps: infra. Build ``PubMaster`` / ``SubMaster`` via :func:`openpilot.system.tests.support.messaging.make_pub_sub`."""

  def _make(pub_services: list[str], sub_services: list[str], **sub_kw):
    from openpilot.system.tests.support.messaging import make_pub_sub

    return make_pub_sub(pub_services, sub_services, **sub_kw)

  return _make
