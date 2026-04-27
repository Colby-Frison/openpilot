"""
Contracts for power monitor sampling helpers.

Maps: R10.
"""

from __future__ import annotations

from openpilot.system.hardware.tici import power_monitor as pm


def test_get_power_averages_samples(monkeypatch):
  monkeypatch.setattr(pm, "sample_power", lambda seconds=5: [1.0, 2.0, 3.0])
  assert pm.get_power(5) == 2.0


def test_wait_for_power_breaks_when_range_stable(monkeypatch):
  seq = iter([4.0, 5.0, 6.0, 5.5, 5.2])
  monkeypatch.setattr(pm, "get_power", lambda _s=1: next(seq))
  monkeypatch.setattr(pm.time, "monotonic", lambda: 0.0)

  avg = pm.wait_for_power(min_pwr=5.0, max_pwr=6.0, min_secs_in_range=2, timeout=3)
  assert 5.0 <= avg <= 6.0
