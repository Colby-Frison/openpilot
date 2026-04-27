"""
Unit tests for ``get_model_metadata`` helpers and the CLI ``__main__`` path.

The CLI block is exercised via ``runpy`` with ``onnx.load`` mocked so no real
``.onnx`` fixture is committed; output is a ``*_metadata.pkl`` next to the fake
model path.

Maps: R1.
"""

from __future__ import annotations

import codecs
import pickle
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace

import onnx
import pytest

from openpilot.selfdrive.modeld import get_model_metadata as gmm
from openpilot.selfdrive.modeld.get_model_metadata import get_metadata_value_by_name, get_name_and_shape


def test_get_metadata_value_by_name_hit_and_miss():
  props = [SimpleNamespace(key="output_slices", value="abc"), SimpleNamespace(key="other", value="x")]
  model = SimpleNamespace(metadata_props=props)
  assert get_metadata_value_by_name(model, "output_slices") == "abc"
  assert get_metadata_value_by_name(model, "missing") is None


def test_get_name_and_shape_reads_dims_and_name():
  d0, d1 = SimpleNamespace(dim_value=1), SimpleNamespace(dim_value=64)
  shape = SimpleNamespace(dim=[d0, d1])
  tensor_type = SimpleNamespace(shape=shape)
  t = SimpleNamespace(tensor_type=tensor_type)
  vi = SimpleNamespace(name="output0", type=t)
  name, shape_t = get_name_and_shape(vi)
  assert name == "output0"
  assert shape_t == (1, 64)


def test_main_script_writes_metadata_pickle(tmp_path, monkeypatch):
  """``if __name__ == '__main__'`` pipeline with mocked ``onnx.load`` (no binary model in repo)."""
  raw_slices = pickle.dumps({"outputs": slice(0, 4)})
  b64 = codecs.encode(raw_slices, "base64").decode().replace("\n", "")

  def _vi(name: str, dims: tuple[int, ...]):
    dim_objs = [SimpleNamespace(dim_value=d) for d in dims]
    sh = SimpleNamespace(dim=dim_objs)
    tt = SimpleNamespace(shape=sh)
    return SimpleNamespace(name=name, type=SimpleNamespace(tensor_type=tt))

  fake_model = SimpleNamespace(
    metadata_props=[
      SimpleNamespace(key="output_slices", value=b64),
      SimpleNamespace(key="model_checkpoint", value="test_ckpt"),
    ],
    graph=SimpleNamespace(
      input=[_vi("in0", (1, 3, 4))],
      output=[_vi("out0", (1, 2))],
    ),
  )

  monkeypatch.setattr(onnx, "load", lambda _path: fake_model)

  fake_onnx = tmp_path / "stub.onnx"
  fake_onnx.write_bytes(b"")

  argv = ["get_model_metadata", str(fake_onnx)]
  monkeypatch.setattr(sys, "argv", argv)
  runpy.run_path(str(Path(gmm.__file__)), run_name="__main__")

  out_pkl = tmp_path / "stub_metadata.pkl"
  assert out_pkl.is_file()
  loaded = pickle.loads(out_pkl.read_bytes())
  assert loaded["model_checkpoint"] == "test_ckpt"
  assert loaded["input_shapes"]["in0"] == (1, 3, 4)
  assert loaded["output_shapes"]["out0"] == (1, 2)
