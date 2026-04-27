"""
Import-time and **pure** helper coverage for ``modeld`` and ``dmonitoringmodeld``.

``test_modeld.py`` exercises the stack by **subprocess**; those lines never
appear in pytest-cov's parent process. This module imports the daemon packages in
the test process and calls small APIs (``FrameMeta``, driver-state packing,
minimal ``Parser`` runs) so coverage and code review see deliberate contracts.

**Does not** call ``main()`` on either daemon (infinite loops, VisionIPC, CL).

Maps: R1.
"""

from __future__ import annotations

import ctypes

import numpy as np
import pytest

from openpilot.selfdrive.modeld.constants import ModelConstants
from openpilot.selfdrive.modeld.parse_model_outputs import Parser
from openpilot.selfdrive.modeld.tests.modeld_parse_fixtures import minimal_policy_parse_outputs, minimal_vision_parse_outputs


def test_modeld_module_exposes_frame_meta_and_process_name():
  from openpilot.selfdrive.modeld import modeld as md

  assert md.PROCESS_NAME == "selfdrive.modeld.modeld"
  assert md.VISION_PKL_PATH.name == "driving_vision_tinygrad.pkl"

  meta = md.FrameMeta()
  assert meta.frame_id == meta.timestamp_sof == meta.timestamp_eof == 0

  class _Vipc:
    frame_id = 9
    timestamp_sof = 100
    timestamp_eof = 200

  meta2 = md.FrameMeta(_Vipc())
  assert meta2.frame_id == 9
  assert meta2.timestamp_sof == 100
  assert meta2.timestamp_eof == 200


def test_model_state_slice_outputs_matches_slices():
  """``ModelState.slice_outputs`` does not use ``self``; avoid ``__init__`` (heavy)."""
  from openpilot.selfdrive.modeld import modeld as md

  shell = object.__new__(md.ModelState)
  arr = np.arange(20, dtype=np.float32)
  sl = {"a": slice(0, 5), "b": slice(10, 15)}
  out = md.ModelState.slice_outputs(shell, arr, sl)
  np.testing.assert_allclose(out["a"], arr[np.newaxis, 0:5])
  np.testing.assert_allclose(out["b"], arr[np.newaxis, 10:15])


def test_dmonitoring_module_constants_and_driverstate_packet():
  from openpilot.selfdrive.modeld import dmonitoringmodeld as dm

  assert dm.PROCESS_NAME == "selfdrive.modeld.dmonitoringmodeld"
  assert dm.OUTPUT_SIZE == 84 + dm.FEATURE_LEN
  assert ctypes.sizeof(dm.DMonitoringModelResult) == dm.OUTPUT_SIZE * ctypes.sizeof(ctypes.c_float)

  buf = np.zeros(dm.OUTPUT_SIZE, dtype=np.float32)
  msg = dm.get_driverstate_packet(buf, frame_id=3, location_ts=1_000, execution_time=0.01, gpu_execution_time=0.02)
  assert msg.which() == "driverStateV2"
  assert msg.driverStateV2.frameId == 3
  assert msg.driverStateV2.modelExecutionTime == pytest.approx(0.01)
  assert msg.driverStateV2.gpuExecutionTime == pytest.approx(0.02)


def test_dmonitoring_fill_driver_state_maps_ctypes_to_capnp():
  from openpilot.selfdrive.modeld import dmonitoringmodeld as dm

  dsr = dm.DriverStateResult()
  dsr.face_orientation[:] = [0.1, -0.2, 0.3]
  dsr.face_orientation_std[:] = [0.0, 0.0, 0.0]
  dsr.face_position[:] = [0.5, -0.25, 0.0]
  dsr.face_position_std[:] = [0.0, 0.0, 0.0]
  dsr.face_prob = 0.0
  dsr.left_eye_prob = 2.0
  dsr.right_eye_prob = -2.0
  dsr.left_blink_prob = 0.0
  dsr.right_blink_prob = 0.0
  dsr.sunglasses_prob = 0.0
  dsr.occluded_prob = 0.0
  dsr.ready_prob[:] = [0.0, 0.0, 0.0, 0.0]
  dsr.not_ready_prob[:] = [0.0, 0.0]

  from cereal import messaging

  m = messaging.new_message("driverStateV2")
  dm.fill_driver_state(m.driverStateV2.leftDriverData, dsr)
  assert len(m.driverStateV2.leftDriverData.faceOrientation) == 3
  assert m.driverStateV2.leftDriverData.faceProb == pytest.approx(0.5)


def test_get_driverstate_packet_raw_predictions_branch(monkeypatch):
  from openpilot.selfdrive.modeld import dmonitoringmodeld as dm

  monkeypatch.setattr(dm, "SEND_RAW_PRED", True, raising=False)
  buf = np.ones(dm.OUTPUT_SIZE, dtype=np.float32)
  msg = dm.get_driverstate_packet(buf, frame_id=1, location_ts=0, execution_time=0.0, gpu_execution_time=0.0)
  assert len(msg.driverStateV2.rawPredictions) == buf.nbytes


def test_parser_parse_outputs_combines_vision_and_policy():
  """One in-process pass through ``Parser.parse_outputs`` (used by ``modeld``)."""
  vision = minimal_vision_parse_outputs(batch=1)
  policy = minimal_policy_parse_outputs(batch=1, with_optional=True)
  combined = {**vision, **policy}
  Parser().parse_outputs(combined)
  assert combined["pose"].shape == (1, ModelConstants.POSE_WIDTH)
  assert combined["plan"].shape[1] == ModelConstants.IDX_N


def test_fill_model_msg_smoke_runs_with_dummy_builders():
  """One ``fill_model_msg`` call so the module is exercised beyond import-only."""
  from openpilot.selfdrive.modeld.fill_model_msg import PublishState, fill_model_msg
  from openpilot.selfdrive.modeld.tests.modeld_test_fixtures import DummyBuilder, minimal_net_output_data

  base, ext = DummyBuilder(), DummyBuilder()
  fill_model_msg(
    base_msg=base,
    extended_msg=ext,
    net_output_data=minimal_net_output_data(batch=1),
    v_ego=0.0,
    delay=0.0,
    publish_state=PublishState(),
    vipc_frame_id=1,
    vipc_frame_id_extra=1,
    frame_id=1,
    frame_drop=0.0,
    timestamp_eof=1,
    model_execution_time=0.0,
    valid=True,
  )
  assert ext.modelV2.frameId == 1
