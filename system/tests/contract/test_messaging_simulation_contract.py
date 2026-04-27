"""
Cereal pub/sub smoke under **simulation** (no device daemons).

Uses ``system_pub_sub_factory`` from the shared harness. Mirrors the pattern in
``system/tests/support/tests/test_system_support_messaging_multi_service.py`` but
targets a single service often used by offroad tooling (``deviceState``).

Hardware boundary: no ``managed_processes`` start; only in-process messaging.
``SIMULATION=1`` avoids assumptions about live hardware state.

Maps: R4 (IPC path sanity for system-level tests).
"""

from __future__ import annotations

import cereal.messaging as messaging


def test_device_state_pub_sub_roundtrip(system_pub_sub_factory, monkeypatch):
  monkeypatch.setenv("SIMULATION", "1")
  pub, sub = system_pub_sub_factory(["deviceState"], ["deviceState"], ignore_alive=["deviceState"])

  msg = messaging.new_message("deviceState")
  msg.deviceState.started = False
  pub.send("deviceState", msg)
  sub.update(3000)

  assert sub.updated["deviceState"]
  assert sub["deviceState"].started is False
