"""
Contracts for system.manager.build retry and cache-pruning behavior.

Maps: R4.
"""

from __future__ import annotations

from pathlib import Path

from openpilot.system.manager import build as build_mod


class _Spinner:
  def __init__(self):
    self.progress = []
    self.closed = 0

  def update_progress(self, p, total):
    self.progress.append((p, total))

  def close(self):
    self.closed += 1


class _Proc:
  def __init__(self, rc=0):
    self.returncode = rc
    self._stderr = [b"progress: 100", b"line"]
    self.stderr = self

  def poll(self):
    if self._stderr:
      return None
    return self.returncode

  def readline(self):
    return self._stderr.pop(0) if self._stderr else b""

  def read(self):
    return b""


def test_build_success_updates_progress_and_prunes_cache(monkeypatch, tmp_path):
  spinner = _Spinner()
  monkeypatch.setattr(build_mod, "AGNOS", False)
  monkeypatch.setattr(build_mod.os, "cpu_count", lambda: 2)
  monkeypatch.setattr(build_mod.subprocess, "Popen", lambda *a, **k: _Proc(0))

  cache = tmp_path / "cache"
  cache.mkdir()
  old = cache / "a.o"
  new = cache / "b.o"
  old.write_bytes(b"a" * 6)
  new.write_bytes(b"b" * 6)
  # deterministic mtime ordering
  old.touch()
  new.touch()

  monkeypatch.setattr(build_mod, "CACHE_DIR", cache)
  monkeypatch.setattr(build_mod, "MAX_CACHE_SIZE", 10)

  build_mod.build(spinner, dirty=False, minimal=False)

  assert spinner.progress, "should report scons progress"
  assert not old.exists() and new.exists(), "oldest cache file should be pruned first"


def test_build_uses_minimal_flag(monkeypatch):
  spinner = _Spinner()
  seen = {"args": None}

  def fake_popen(args, **kwargs):
    seen["args"] = args
    return _Proc(0)

  monkeypatch.setattr(build_mod, "AGNOS", False)
  monkeypatch.setattr(build_mod.os, "cpu_count", lambda: 1)
  monkeypatch.setattr(build_mod.subprocess, "Popen", fake_popen)
  monkeypatch.setattr(build_mod, "CACHE_DIR", Path('/tmp'))
  monkeypatch.setattr(build_mod, "MAX_CACHE_SIZE", 10**12)

  build_mod.build(spinner, dirty=False, minimal=True)
  assert "--minimal" in seen["args"]
