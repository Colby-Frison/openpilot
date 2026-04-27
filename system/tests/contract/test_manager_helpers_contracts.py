"""
Contracts for manager helper utilities with no hardware/process side effects.

Maps: R4.
"""

from __future__ import annotations

from pathlib import Path

from openpilot.system.manager import helpers


class _ParamsCapture:
  def __init__(self):
    self.calls = []

  def put_bool(self, key, value):
    self.calls.append((key, value))


def test_write_onroad_params_sets_both_flags_consistently():
  p = _ParamsCapture()
  helpers.write_onroad_params(True, p)
  assert ("IsOnroad", True) in p.calls
  assert ("IsOffroad", False) in p.calls

  p2 = _ParamsCapture()
  helpers.write_onroad_params(False, p2)
  assert ("IsOnroad", False) in p2.calls
  assert ("IsOffroad", True) in p2.calls


def test_save_bootlog_invokes_bootlog_and_cleanup(tmp_path, monkeypatch):
  params_src = tmp_path / "params"
  params_src.mkdir()
  (params_src / "k").write_text("v")

  class _FakeParams:
    def get_param_path(self):
      return str(params_src)

  monkeypatch.setattr(helpers, "Params", lambda: _FakeParams())

  calls = {"subprocess": [], "rmtree": []}

  def fake_call(cmd, cwd=None, env=None):
    calls["subprocess"].append((cmd, cwd, env.get("PARAMS_COPY_PATH")))
    return 0

  def fake_rmtree(path):
    calls["rmtree"].append(path)

  class _InlineThread:
    def __init__(self, target, args):
      self._target = target
      self._args = args
      self.daemon = False

    def start(self):
      self._target(*self._args)

  monkeypatch.setattr(helpers.subprocess, "call", fake_call)
  monkeypatch.setattr(helpers.shutil, "rmtree", fake_rmtree)
  monkeypatch.setattr(helpers.threading, "Thread", _InlineThread)

  helpers.save_bootlog()

  assert calls["subprocess"], "bootlog subprocess should be invoked"
  cmd, cwd, params_copy = calls["subprocess"][0]
  assert cmd == "./bootlog"
  assert Path(cwd).as_posix().endswith("system/loggerd")
  assert params_copy is not None
  assert calls["rmtree"], "temporary copy directory should be cleaned"
