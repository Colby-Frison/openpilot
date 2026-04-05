"""
Shared pytest helpers for ``system/*`` daemon and integration tests.

Lives under the existing ``system/tests/`` tree (alongside e.g. ``test_logmessaged.py``),
not a separate ``system/test/`` path.

Reuses :mod:`openpilot.selfdrive.test.support` for process scoping; adds Params
and messaging helpers common across loggerd, athena, manager-adjacent tests, etc.

Fixtures (``system_*``) load via root ``pytest_plugins`` in the repo ``conftest.py``.
"""

from openpilot.selfdrive.test.support.processes import managed_process_scope
from openpilot.system.tests.support.messaging import make_pub_sub
from openpilot.system.tests.support.params_seed import (
  seed_full_stack_params,
  seed_system_daemon_params,
)

__all__ = [
  "make_pub_sub",
  "managed_process_scope",
  "seed_full_stack_params",
  "seed_system_daemon_params",
]
