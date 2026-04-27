"""
Contracts for tombstoned helper utilities.

Maps: R5.
"""

from __future__ import annotations

import subprocess

from openpilot.system import tombstoned


def test_safe_fn_filters_to_alnum_and_underscore():
  assert tombstoned.safe_fn('ab c/..-12_') == 'abc12_'


def test_clear_apport_folder_ignores_remove_errors(monkeypatch):
  monkeypatch.setattr(tombstoned.glob, "glob", lambda _p: ["/tmp/a", "/tmp/b"])
  calls = []

  def fake_remove(path):
    calls.append(path)
    if path.endswith('b'):
      raise PermissionError()

  monkeypatch.setattr(tombstoned.os, "remove", fake_remove)
  tombstoned.clear_apport_folder()
  assert calls == ["/tmp/a", "/tmp/b"]


def test_get_apport_stacktrace_error_and_timeout(monkeypatch):
  monkeypatch.setattr(tombstoned.subprocess, "check_output", lambda *a, **k: (_ for _ in ()).throw(subprocess.CalledProcessError(1, 'x')))
  assert "Error getting stacktrace" == tombstoned.get_apport_stacktrace('/tmp/x')

  monkeypatch.setattr(tombstoned.subprocess, "check_output", lambda *a, **k: (_ for _ in ()).throw(subprocess.TimeoutExpired('x', 1)))
  assert "Timeout getting stacktrace" == tombstoned.get_apport_stacktrace('/tmp/x')
