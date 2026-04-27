"""
Contracts for timed helper behavior.

Maps: R9.
"""

from __future__ import annotations

import datetime

REAL_DATETIME = datetime.datetime
import subprocess

from openpilot.system import timed


def test_set_time_skips_small_delta(monkeypatch):
  called = {"run": 0}
  monkeypatch.setattr(timed.datetime, "datetime", type("D", (), {"now": staticmethod(lambda: REAL_DATETIME(2026,1,1,0,0,0))}))
  monkeypatch.setattr(timed.subprocess, "run", lambda *a, **k: called.__setitem__("run", called["run"] + 1))

  timed.set_time(REAL_DATETIME(2026,1,1,0,0,5))
  assert called["run"] == 0


def test_set_time_runs_date_command(monkeypatch):
  monkeypatch.setattr(timed.datetime, "datetime", type("D", (), {"now": staticmethod(lambda: REAL_DATETIME(2026,1,1,0,0,0))}))
  seen = {"cmd": None}

  def fake_run(cmd, shell, check):
    seen["cmd"] = cmd
    return None

  monkeypatch.setattr(timed.subprocess, "run", fake_run)
  target = REAL_DATETIME(2025, 1, 1, 12, 0, 0)
  timed.set_time(target)
  assert "date -s" in seen["cmd"]


def test_set_time_handles_calledprocesserror(monkeypatch):
  monkeypatch.setattr(timed.datetime, "datetime", type("D", (), {"now": staticmethod(lambda: REAL_DATETIME(2026,1,1,0,0,0))}))
  monkeypatch.setattr(timed.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(subprocess.CalledProcessError(1, 'x')))
  # should not raise
  timed.set_time(REAL_DATETIME(2025,1,1,0,0,0))
