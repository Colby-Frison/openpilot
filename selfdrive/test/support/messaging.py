"""Small builders for common cereal messages used across subsystem tests."""

from __future__ import annotations

import cereal.messaging as messaging


def new_live_calibration_message(valid_blocks: int = 20, rpy_calib: list[float] | None = None):
  """Return a populated ``liveCalibration`` message (for Params / PubMaster)."""
  msg = messaging.new_message("liveCalibration")
  msg.liveCalibration.validBlocks = valid_blocks
  msg.liveCalibration.rpyCalib = rpy_calib if rpy_calib is not None else [0.0, 0.0, 0.0]
  return msg
