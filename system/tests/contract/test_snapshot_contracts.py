"""
Contracts for snapshot image conversion and early-return guard.

Maps: R7.
"""

from __future__ import annotations

import numpy as np

from openpilot.system.camerad.snapshot import snapshot as snap


def test_yuv_to_rgb_shape_and_type():
  y = np.zeros((4, 4), dtype=np.uint8)
  u = np.zeros((2, 2), dtype=np.uint8)
  v = np.zeros((2, 2), dtype=np.uint8)
  rgb = snap.yuv_to_rgb(y, u, v)
  assert rgb.shape == (4, 4, 3)
  assert rgb.dtype == np.uint8


def test_extract_image_uses_planes_from_buffer():
  class _Buf:
    width = 4
    height = 4
    stride = 4
    uv_offset = 16
    data = bytearray([16] * 16 + [128, 128] * 4)

  img = snap.extract_image(_Buf())
  assert img.shape == (4, 4, 3)


def test_snapshot_returns_none_when_not_offroad(monkeypatch):
  class _Params:
    def get_bool(self, key):
      if key == "IsOffroad":
        return False
      return False

  monkeypatch.setattr(snap, "Params", lambda: _Params())
  rear, front = snap.snapshot()
  assert rear is None and front is None
