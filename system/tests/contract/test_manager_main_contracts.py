"""
Contracts for ``system.manager.manager`` top-level lifecycle behavior.

These tests do not start daemons; they monkeypatch manager entrypoints and
assert control-flow guarantees.

Maps: R4.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from openpilot.system.manager import manager as manager_mod


def test_manager_cleanup_stops_all_processes_twice(monkeypatch):
  calls: list[tuple[str, bool]] = []

  class _Proc:
    def __init__(self, name):
      self.name = name

    def stop(self, block=False):
      calls.append((self.name, block))

  fake = {"a": _Proc("a"), "b": _Proc("b")}
  monkeypatch.setattr(manager_mod, "managed_processes", fake)
  monkeypatch.setattr(manager_mod.cloudlog, "info", lambda _m: None)

  manager_mod.manager_cleanup()

  assert calls == [("a", False), ("b", False), ("a", True), ("b", True)]


def test_main_returns_early_when_prepareonly(monkeypatch):
  called = {"init": 0, "thread": 0, "cleanup": 0}
  monkeypatch.setenv("PREPAREONLY", "1")
  monkeypatch.setattr(manager_mod, "manager_init", lambda: called.__setitem__("init", called["init"] + 1))
  monkeypatch.setattr(manager_mod, "manager_thread", lambda: called.__setitem__("thread", called["thread"] + 1))
  monkeypatch.setattr(manager_mod, "manager_cleanup", lambda: called.__setitem__("cleanup", called["cleanup"] + 1))

  manager_mod.main()

  assert called["init"] == 1
  assert called["thread"] == 0
  assert called["cleanup"] == 0


def test_main_calls_cleanup_even_when_manager_thread_raises(monkeypatch):
  called = {"cleanup": 0, "sentry": 0}
  monkeypatch.delenv("PREPAREONLY", raising=False)
  monkeypatch.setattr(manager_mod, "manager_init", lambda: None)
  monkeypatch.setattr(manager_mod, "manager_thread", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
  monkeypatch.setattr(manager_mod, "manager_cleanup", lambda: called.__setitem__("cleanup", called["cleanup"] + 1))
  monkeypatch.setattr(manager_mod.sentry, "capture_exception", lambda: called.__setitem__("sentry", called["sentry"] + 1))

  class _Params:
    def get_bool(self, _k):
      return False

  monkeypatch.setattr(manager_mod, "Params", lambda: _Params())
  monkeypatch.setattr(manager_mod.cloudlog, "warning", lambda _m: None)
  monkeypatch.setattr(manager_mod.HARDWARE, "uninstall", lambda: None)
  monkeypatch.setattr(manager_mod.HARDWARE, "reboot", lambda: None)
  monkeypatch.setattr(manager_mod.HARDWARE, "shutdown", lambda: None)

  manager_mod.main()

  assert called["cleanup"] == 1
  assert called["sentry"] == 1


@pytest.mark.parametrize("flag, method", [
  ("DoUninstall", "uninstall"),
  ("DoReboot", "reboot"),
  ("DoShutdown", "shutdown"),
])
def test_main_hardware_action_selection(monkeypatch, flag, method):
  monkeypatch.delenv("PREPAREONLY", raising=False)
  monkeypatch.setattr(manager_mod, "manager_init", lambda: None)
  monkeypatch.setattr(manager_mod, "manager_thread", lambda: None)
  monkeypatch.setattr(manager_mod, "manager_cleanup", lambda: None)
  monkeypatch.setattr(manager_mod.sentry, "capture_exception", lambda: None)
  monkeypatch.setattr(manager_mod.cloudlog, "warning", lambda _m: None)

  class _Params:
    def get_bool(self, key):
      return key == flag

  monkeypatch.setattr(manager_mod, "Params", lambda: _Params())

  called = {"uninstall": 0, "reboot": 0, "shutdown": 0}
  monkeypatch.setattr(manager_mod.HARDWARE, "uninstall", lambda: called.__setitem__("uninstall", called["uninstall"] + 1))
  monkeypatch.setattr(manager_mod.HARDWARE, "reboot", lambda: called.__setitem__("reboot", called["reboot"] + 1))
  monkeypatch.setattr(manager_mod.HARDWARE, "shutdown", lambda: called.__setitem__("shutdown", called["shutdown"] + 1))

  manager_mod.main()

  assert called[method] == 1
  for k, v in called.items():
    if k != method:
      assert v == 0
