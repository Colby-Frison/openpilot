"""
Contracts for manage_athenad main-loop lifecycle.

Maps: R6.
"""

from __future__ import annotations

from openpilot.system.athena import manage_athenad as ma


def test_main_removes_pid_param_on_exit(monkeypatch):
  class _Params:
    def __init__(self):
      self.removed = []

    def get(self, _k):
      return b'DONGLE'

    def remove(self, key):
      self.removed.append(key)

  params = _Params()
  monkeypatch.setattr(ma, "Params", lambda: params)

  class _Build:
    channel = "ch"
    openpilot = type("O", (), {"version": "v", "git_normalized_origin": "o", "git_commit": "c", "is_dirty": False})

  monkeypatch.setattr(ma, "get_build_metadata", lambda: _Build())
  monkeypatch.setattr(ma.HARDWARE, "get_device_type", lambda: "pc")
  monkeypatch.setattr(ma.cloudlog, "bind_global", lambda **kw: None)
  monkeypatch.setattr(ma.cloudlog, "info", lambda *a, **k: None)
  monkeypatch.setattr(ma.cloudlog, "event", lambda *a, **k: None)
  monkeypatch.setattr(ma.cloudlog, "exception", lambda *a, **k: None)

  class _Proc:
    def __init__(self, *a, **k):
      self.exitcode = 0

    def start(self):
      return None

    def join(self):
      raise RuntimeError("stop loop")

  monkeypatch.setattr(ma, "Process", _Proc)
  monkeypatch.setattr(ma.time, "sleep", lambda _s: None)

  ma.main()
  assert ma.ATHENA_MGR_PID_PARAM in params.removed
