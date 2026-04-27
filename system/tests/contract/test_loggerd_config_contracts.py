"""
Contracts for ``system.loggerd.config`` storage availability helpers.

Maps: R5.
"""

from __future__ import annotations

from types import SimpleNamespace

from openpilot.system.loggerd import config as loggerd_config


def test_get_available_percent_uses_statvfs_values(monkeypatch):
  monkeypatch.setattr(loggerd_config.Paths, "log_root", lambda: "/tmp/logroot")
  stat = SimpleNamespace(f_bavail=25, f_blocks=100, f_frsize=4096)
  monkeypatch.setattr(loggerd_config.os, "statvfs", lambda _p: stat)

  got = loggerd_config.get_available_percent(default=99.0)
  assert got == 25.0


def test_get_available_percent_falls_back_on_oserror(monkeypatch):
  monkeypatch.setattr(loggerd_config.Paths, "log_root", lambda: "/tmp/logroot")

  def _boom(_p):
    raise OSError("statvfs unavailable")

  monkeypatch.setattr(loggerd_config.os, "statvfs", _boom)
  assert loggerd_config.get_available_percent(default=12.34) == 12.34


def test_get_available_bytes_uses_statvfs_values(monkeypatch):
  monkeypatch.setattr(loggerd_config.Paths, "log_root", lambda: "/tmp/logroot")
  stat = SimpleNamespace(f_bavail=7, f_blocks=100, f_frsize=1024)
  monkeypatch.setattr(loggerd_config.os, "statvfs", lambda _p: stat)

  got = loggerd_config.get_available_bytes(default=0)
  assert got == 7 * 1024


def test_get_available_bytes_falls_back_on_oserror(monkeypatch):
  monkeypatch.setattr(loggerd_config.Paths, "log_root", lambda: "/tmp/logroot")

  def _boom(_p):
    raise OSError("statvfs unavailable")

  monkeypatch.setattr(loggerd_config.os, "statvfs", _boom)
  assert loggerd_config.get_available_bytes(default=123456) == 123456
