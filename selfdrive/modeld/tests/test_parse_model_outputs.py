import numpy as np
import pytest

from openpilot.selfdrive.modeld.parse_model_outputs import Parser, sigmoid, softmax


def test_softmax_float32_is_inplace_and_normalized():
  raw = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
  out = softmax(raw, axis=-1)

  assert out is raw
  np.testing.assert_allclose(np.sum(out, axis=-1), np.array([1.0], dtype=np.float32))
  assert out[0, 2] > out[0, 1] > out[0, 0]


def test_softmax_float16_returns_new_array_and_normalized():
  raw = np.array([[1.0, 2.0, 3.0]], dtype=np.float16)
  out = softmax(raw, axis=-1)

  assert out is not raw
  np.testing.assert_allclose(np.sum(out, axis=-1), np.array([1.0], dtype=np.float16), atol=1e-3)
  assert out[0, 2] > out[0, 1] > out[0, 0]


def test_sigmoid_handles_extreme_values():
  vals = np.array([-1000.0, 0.0, 1000.0], dtype=np.float32)
  out = sigmoid(vals)

  assert np.isfinite(out).all()
  assert out[0] < 1e-4
  assert out[1] == pytest.approx(0.5)
  assert out[2] > 1.0 - 1e-4


def test_missing_output_raises_by_default():
  parser = Parser(ignore_missing=False)
  outs = {}

  with pytest.raises(ValueError, match="Missing output missing"):
    parser.parse_binary_crossentropy("missing", outs)


def test_missing_output_is_ignored_when_configured():
  parser = Parser(ignore_missing=True)
  outs = {}

  parser.parse_binary_crossentropy("missing", outs)
  assert outs == {}


def test_parse_categorical_crossentropy_reshapes_and_normalizes():
  parser = Parser()
  outs = {"desire_state": np.array([[1.0, 2.0, 3.0, 4.0]], dtype=np.float32)}

  parser.parse_categorical_crossentropy("desire_state", outs, out_shape=(2, 2))

  parsed = outs["desire_state"]
  assert parsed.shape == (1, 2, 2)
  np.testing.assert_allclose(np.sum(parsed, axis=-1), np.ones((1, 2), dtype=np.float32))


def test_parse_mdn_single_output_selects_highest_weight_hypothesis():
  parser = Parser()
  # shape before parse: (batch, in_N * (2 * n_values + out_N))
  # here: batch=1, in_N=3, out_N=1, n_values=2 => 1 x (3 * 5) = 1 x 15
  raw = np.array([[
    10.0, 11.0, 0.0, 0.0, -2.0,   # hyp 0, low weight
    20.0, 21.0, 0.0, 0.0, 6.0,    # hyp 1, highest weight
    30.0, 31.0, 0.0, 0.0, 1.0,    # hyp 2, medium weight
  ]], dtype=np.float32)
  outs = {"plan": raw}

  parser.parse_mdn("plan", outs, in_N=3, out_N=1, out_shape=(2,))

  parsed = outs["plan"]
  assert parsed.shape == (1, 2)
  np.testing.assert_allclose(parsed[0], np.array([20.0, 21.0], dtype=np.float32))

  weights = outs["plan_weights"]
  assert weights.shape == (1, 3, 1)
  assert weights[0, 0, 0] >= weights[0, 1, 0] >= weights[0, 2, 0]

