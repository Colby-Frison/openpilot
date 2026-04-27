"""
Manager **process_config** contracts: gating helpers and ``managed_processes`` map.

These tests are **desktop-safe**: no process start, no ``HARDWARE`` mutation, no
camera or serial devices. They complement ``system/manager/test/test_manager.py``
(R4) by locking predicate and registry invariants.

Hardware boundary: anything that would start ``camerad``, touch ``/dev/*``, or
require TICI stays out of this module; see ``docs/testing/SYSTEM-TESTING.md``.

Maps: R4.
"""

from __future__ import annotations

from cereal import car
import pytest

from openpilot.common.params import Params
from openpilot.system.manager.process_config import (
  and_,
  managed_processes,
  not_joystick,
  only_onroad,
  or_,
  procs,
  logging,
)


def test_procs_and_managed_processes_names_round_trip():
  assert len(procs) == len(managed_processes)
  for p in procs:
    assert managed_processes[p.name] is p
    assert p.name in managed_processes


def test_logging_predicate_respects_disable_logging():
  params = Params()
  cp = car.CarParams.new_message()
  cp.notCar = True
  params.put_bool("DisableLogging", True)
  try:
    assert logging(True, params, cp) is False
    params.put_bool("DisableLogging", False)
    assert logging(True, params, cp) is True
  finally:
    params.remove("DisableLogging")


def test_only_onroad_matches_started_flag():
  params = Params()
  cp = car.CarParams.new_message()
  assert only_onroad(True, params, cp) is True
  assert only_onroad(False, params, cp) is False


def test_or_and_combinators():
  params = Params()
  cp = car.CarParams.new_message()
  assert or_(only_onroad, only_onroad)(True, params, cp) is True
  assert or_(only_onroad, only_onroad)(False, params, cp) is False
  assert and_(only_onroad, only_onroad)(True, params, cp) is True
  assert and_(only_onroad, only_onroad)(False, params, cp) is False


def test_not_joystick_requires_started_and_param():
  params = Params()
  cp = car.CarParams.new_message()
  params.put_bool("JoystickDebugMode", False)
  try:
    assert not_joystick(True, params, cp) is True
    assert not_joystick(False, params, cp) is False
    params.put_bool("JoystickDebugMode", True)
    assert not_joystick(True, params, cp) is False
  finally:
    params.remove("JoystickDebugMode")
