"""
Contracts for ``system.manager.process.ensure_running`` selection behavior.

Maps: R4.
"""

from __future__ import annotations

from types import SimpleNamespace

from cereal import car

from openpilot.common.params import Params
from openpilot.system.manager.process import ensure_running


class _FakeManagedProc:
  def __init__(self, name: str, should_run_result: bool, enabled: bool = True):
    self.name = name
    self.enabled = enabled
    self._should = should_run_result
    self.started = 0
    self.stopped = []
    self.watchdog_checks = 0

  def should_run(self, started, params, CP):
    return self._should

  def start(self):
    self.started += 1

  def stop(self, block=False):
    self.stopped.append(block)

  def check_watchdog(self, started):
    self.watchdog_checks += 1


def test_ensure_running_starts_only_eligible_processes():
  params = Params()
  cp = car.CarParams.new_message()

  run_me = _FakeManagedProc("run_me", True)
  not_running = _FakeManagedProc("not_running", False)
  disabled = _FakeManagedProc("disabled", True, enabled=False)
  blocked = _FakeManagedProc("blocked", True)

  running = ensure_running(
    [run_me, not_running, disabled, blocked],
    started=True,
    params=params,
    CP=cp,
    not_run=["blocked"],
  )

  assert [p.name for p in running] == ["run_me"]
  assert run_me.started == 1
  assert not_running.started == 0
  assert disabled.started == 0
  assert blocked.started == 0


def test_ensure_running_stops_non_running_with_block_false():
  params = Params()
  cp = car.CarParams.new_message()

  run_me = _FakeManagedProc("run_me", True)
  stop_me = _FakeManagedProc("stop_me", False)

  ensure_running([run_me, stop_me], started=False, params=params, CP=cp)

  assert run_me.stopped == []
  assert stop_me.stopped == [False]
  assert run_me.watchdog_checks == 1
  assert stop_me.watchdog_checks == 1
