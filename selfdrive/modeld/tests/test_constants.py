import numpy as np

from openpilot.selfdrive.modeld.constants import index_function, ModelConstants, Plan, Meta


# ---------------------------------------------------------------------------
# index_function
# ---------------------------------------------------------------------------

class TestIndexFunction:
  def test_zero_returns_zero(self):
    assert index_function(0) == 0.0

  def test_max_idx_returns_max_val(self):
    assert index_function(32, max_val=192, max_idx=32) == 192.0

  def test_quadratic_midpoint(self):
    result = index_function(16, max_val=192, max_idx=32)
    assert result == 192.0 * (16 / 32) ** 2
    assert result == 48.0

  def test_custom_parameters(self):
    assert index_function(10, max_val=10.0, max_idx=10) == 10.0
    assert index_function(5, max_val=10.0, max_idx=10) == 10.0 * (0.5 ** 2)

  def test_monotonically_increasing(self):
    vals = [index_function(i) for i in range(33)]
    for i in range(1, len(vals)):
      assert vals[i] >= vals[i - 1]


# ---------------------------------------------------------------------------
# ModelConstants — index lists
# ---------------------------------------------------------------------------

class TestModelConstantsIndices:
  def test_t_idxs_length(self):
    assert len(ModelConstants.T_IDXS) == ModelConstants.IDX_N

  def test_x_idxs_length(self):
    assert len(ModelConstants.X_IDXS) == ModelConstants.IDX_N

  def test_t_idxs_endpoints(self):
    assert ModelConstants.T_IDXS[0] == 0.0
    assert ModelConstants.T_IDXS[-1] == 10.0

  def test_x_idxs_endpoints(self):
    assert ModelConstants.X_IDXS[0] == 0.0
    assert ModelConstants.X_IDXS[-1] == 192.0

  def test_lead_t_idxs_length(self):
    assert len(ModelConstants.LEAD_T_IDXS) == ModelConstants.LEAD_TRAJ_LEN

  def test_lead_t_idxs_values(self):
    assert ModelConstants.LEAD_T_IDXS == [0., 2., 4., 6., 8., 10.]

  def test_meta_t_idxs(self):
    assert ModelConstants.META_T_IDXS == [2., 4., 6., 8., 10.]

  def test_t_idxs_monotonically_increasing(self):
    for i in range(1, len(ModelConstants.T_IDXS)):
      assert ModelConstants.T_IDXS[i] >= ModelConstants.T_IDXS[i - 1]

  def test_x_idxs_monotonically_increasing(self):
    for i in range(1, len(ModelConstants.X_IDXS)):
      assert ModelConstants.X_IDXS[i] >= ModelConstants.X_IDXS[i - 1]


# ---------------------------------------------------------------------------
# ModelConstants — scalar constants
# ---------------------------------------------------------------------------

class TestModelConstantsValues:
  def test_model_freq(self):
    assert ModelConstants.MODEL_FREQ == 20

  def test_temporal_skip(self):
    assert ModelConstants.TEMPORAL_SKIP == ModelConstants.MODEL_FREQ // ModelConstants.HISTORY_FREQ

  def test_full_history_buffer_len(self):
    assert ModelConstants.FULL_HISTORY_BUFFER_LEN == ModelConstants.MODEL_FREQ * ModelConstants.HISTORY_LEN_SECONDS

  def test_input_history_buffer_len(self):
    assert ModelConstants.INPUT_HISTORY_BUFFER_LEN == ModelConstants.HISTORY_FREQ * ModelConstants.HISTORY_LEN_SECONDS

  def test_positive_widths(self):
    for attr in ['POSE_WIDTH', 'WIDE_FROM_DEVICE_WIDTH', 'LEAD_WIDTH',
                 'LANE_LINES_WIDTH', 'PLAN_WIDTH', 'DESIRE_PRED_WIDTH',
                 'DISENGAGE_WIDTH', 'FEATURE_LEN']:
      assert getattr(ModelConstants, attr) > 0

  def test_fcw_thresholds_in_range(self):
    assert np.all(ModelConstants.FCW_THRESHOLDS_5MS2 > 0)
    assert np.all(ModelConstants.FCW_THRESHOLDS_5MS2 <= 1)
    assert np.all(ModelConstants.FCW_THRESHOLDS_3MS2 > 0)
    assert np.all(ModelConstants.FCW_THRESHOLDS_3MS2 <= 1)

  def test_fcw_scalar_thresholds(self):
    assert 0 < ModelConstants.FCW_THRESHOLD_5MS2_LOW < ModelConstants.FCW_THRESHOLD_5MS2_HIGH <= 1
    assert 0 < ModelConstants.FCW_THRESHOLD_3MS2 <= 1

  def test_mhp_counts(self):
    assert ModelConstants.PLAN_MHP_N > 0
    assert ModelConstants.LEAD_MHP_N > 0
    assert ModelConstants.PLAN_MHP_SELECTION > 0
    assert ModelConstants.LEAD_MHP_SELECTION > 0


# ---------------------------------------------------------------------------
# Plan slices
# ---------------------------------------------------------------------------

class TestPlanSlices:
  def test_position_slice(self):
    data = np.arange(ModelConstants.PLAN_WIDTH, dtype=np.float32)
    pos = data[Plan.POSITION]
    assert len(pos) == 3
    np.testing.assert_array_equal(pos, [0, 1, 2])

  def test_velocity_slice(self):
    data = np.arange(ModelConstants.PLAN_WIDTH, dtype=np.float32)
    vel = data[Plan.VELOCITY]
    assert len(vel) == 3
    np.testing.assert_array_equal(vel, [3, 4, 5])

  def test_acceleration_slice(self):
    data = np.arange(ModelConstants.PLAN_WIDTH, dtype=np.float32)
    acc = data[Plan.ACCELERATION]
    assert len(acc) == 3
    np.testing.assert_array_equal(acc, [6, 7, 8])

  def test_slices_non_overlapping(self):
    indices = set()
    for s in [Plan.POSITION, Plan.VELOCITY, Plan.ACCELERATION,
              Plan.T_FROM_CURRENT_EULER, Plan.ORIENTATION_RATE]:
      current = set(range(*s.indices(ModelConstants.PLAN_WIDTH)))
      assert len(indices & current) == 0, "Overlapping slices found"
      indices |= current

  def test_slices_cover_full_width(self):
    indices = set()
    for s in [Plan.POSITION, Plan.VELOCITY, Plan.ACCELERATION,
              Plan.T_FROM_CURRENT_EULER, Plan.ORIENTATION_RATE]:
      indices |= set(range(*s.indices(ModelConstants.PLAN_WIDTH)))
    assert indices == set(range(ModelConstants.PLAN_WIDTH))


# ---------------------------------------------------------------------------
# Meta slices
# ---------------------------------------------------------------------------

class TestMetaSlices:
  def test_engaged_single_element(self):
    data = np.arange(55, dtype=np.float32)
    assert len(data[Meta.ENGAGED]) == 1

  def test_disengage_slices_length(self):
    data = np.arange(55, dtype=np.float32)
    assert len(data[Meta.GAS_DISENGAGE]) == 5
    assert len(data[Meta.BRAKE_DISENGAGE]) == 5
    assert len(data[Meta.STEER_OVERRIDE]) == 5
    assert len(data[Meta.HARD_BRAKE_3]) == 5
    assert len(data[Meta.HARD_BRAKE_4]) == 5
    assert len(data[Meta.HARD_BRAKE_5]) == 5

  def test_press_and_blinker_slices_length(self):
    data = np.arange(55, dtype=np.float32)
    assert len(data[Meta.GAS_PRESS]) == 6
    assert len(data[Meta.BRAKE_PRESS]) == 6
    assert len(data[Meta.LEFT_BLINKER]) == 6
    assert len(data[Meta.RIGHT_BLINKER]) == 6

  def test_engaged_starts_at_zero(self):
    assert Meta.ENGAGED.start == 0
    assert Meta.ENGAGED.stop == 1
