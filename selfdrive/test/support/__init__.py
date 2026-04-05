"""
Shared pytest helpers and fixtures for subsystem tests.

Import from here for non-fixture utilities::

    from openpilot.selfdrive.test.support.processes import managed_process_scope
    from openpilot.selfdrive.test.support.messaging import new_live_calibration_message

Fixtures (e.g. ``openpilot_params_seeded``) load via root ``pytest_plugins`` in ``conftest.py``.
"""

from openpilot.selfdrive.test.support.messaging import new_live_calibration_message
from openpilot.selfdrive.test.support.params_seed import seed_minimal_openpilot_params
from openpilot.selfdrive.test.support.processes import managed_process_scope

__all__ = [
  "managed_process_scope",
  "new_live_calibration_message",
  "seed_minimal_openpilot_params",
]
