#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." >/dev/null && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT:${PYTHONPATH:-}"
if [[ -d "$ROOT/.venv/bin" ]]; then
  export PATH="$ROOT/.venv/bin:$PATH"
fi
PYTHON_BIN="${PYTHON_BIN:-python3}"
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON_BIN="${PYTHON_BIN:-$ROOT/.venv/bin/python}"
  # If user didn't override PYTHON_BIN explicitly, prefer repo venv.
  if [[ "${PYTHON_BIN}" == "python3" ]]; then
    PYTHON_BIN="$ROOT/.venv/bin/python"
  fi
fi

PROFILE="modeld"
RUN_ALL_PROFILES="0"
OVERRIDE_COV_TARGET="0"
OVERRIDE_BASELINE="0"
OVERRIDE_OURS="0"
OVERRIDE_OUT_DIR="0"
OVERRIDE_COV_CONFIG="0"
INCLUDE_BASELINE_IN_OURS="1"

COV_TARGET=""
BASELINE_TESTS=""
OUR_TESTS=""
OUT_DIR=""
COV_CONFIG=""
CLI_COV_TARGET=""
CLI_BASELINE_TESTS=""
CLI_OUR_TESTS=""
CLI_OUT_DIR=""
CLI_COV_CONFIG=""

function set_profile_defaults() {
  local profile="$1"
  case "$profile" in
    modeld)
      COV_TARGET="selfdrive/modeld"
      BASELINE_TESTS="selfdrive/modeld/tests/test_modeld.py"
      OUR_TESTS="selfdrive/modeld/tests/test_parse_model_outputs.py selfdrive/modeld/tests/test_parse_model_outputs_vision_contracts.py selfdrive/modeld/tests/test_parse_model_outputs_policy_contracts.py selfdrive/modeld/tests/test_fill_model_msg.py selfdrive/modeld/tests/test_fill_model_msg_frame_ids.py selfdrive/modeld/tests/test_fill_model_msg_modelv2_dimensions.py selfdrive/modeld/tests/test_fill_model_msg_pose_odometry.py selfdrive/modeld/tests/test_fill_model_msg_driving_model_data.py selfdrive/modeld/tests/test_fill_model_msg_raw_predictions.py selfdrive/modeld/tests/test_fill_model_msg_fcw_hard_brake.py selfdrive/modeld/tests/test_get_model_metadata_unit.py selfdrive/modeld/tests/test_modeld_package_surfaces.py selfdrive/modeld/tests/test_modeld_phase_c_contracts.py"
      OUT_DIR=".coverage-compare/modeld"
      COV_CONFIG="$ROOT/scripts/testing/coverage-modeld-compare.ini"
      ;;
    pandad)
      COV_TARGET="selfdrive/pandad"
      BASELINE_TESTS="selfdrive/pandad/tests/test_pandad.py selfdrive/pandad/tests/test_pandad_loopback.py selfdrive/pandad/tests/test_pandad_spi.py"
      OUR_TESTS="selfdrive/pandad/tests/test_pandad_can_capnp_roundtrip.py selfdrive/pandad/tests/test_pandad_can_capnp_event_validity.py selfdrive/pandad/tests/test_pandad_can_capnp_multiblob.py selfdrive/pandad/tests/test_pandad_pandad_wrapper.py"
      OUT_DIR=".coverage-compare/pandad"
      COV_CONFIG="$ROOT/scripts/testing/coverage-pandad-compare.ini"
      ;;
    system)
      COV_TARGET="system"
      # Keep default baseline stable on desktop: exclude webrtc ICE/timeouts.
      # Opt in manually with: --baseline "... system/webrtc/tests/test_webrtcd.py"
      BASELINE_TESTS="system/manager/test/test_manager.py system/tests/test_logmessaged.py system/athena/tests/test_registration.py"
      OUR_TESTS="system/tests/support/tests/test_system_support_harness.py system/tests/support/tests/test_system_support_messaging_multi_service.py system/tests/contract/test_manager_process_config_contracts.py system/tests/contract/test_messaging_simulation_contract.py system/tests/contract/test_manager_helpers_contracts.py system/tests/contract/test_process_ensure_running_contracts.py system/tests/contract/test_loggerd_config_contracts.py system/tests/contract/test_manager_main_contracts.py system/tests/contract/test_manager_build_contracts.py system/tests/contract/test_timed_contracts.py system/tests/contract/test_tombstoned_contracts.py system/tests/contract/test_manage_athenad_contracts.py system/tests/contract/test_snapshot_contracts.py system/tests/contract/test_power_monitor_contracts.py system/tests/contract/test_athenad_contracts.py system/tests/contract/test_agnos_contracts.py"
      OUT_DIR=".coverage-compare/system"
      COV_CONFIG="$ROOT/scripts/testing/coverage-system-compare.ini"
      ;;
    *)
      echo "Unknown profile: $profile"
      echo "Valid profiles: modeld, pandad, system"
      exit 1
      ;;
  esac
}

function usage() {
  echo "Compare baseline vs new-test coverage for assignment targets."
  echo ""
  echo "Usage:"
  echo "  bash scripts/testing/compare_coverage.sh [options]"
  echo ""
  echo "Options:"
  echo "  --profile <name>      One of: modeld, pandad, system (default: modeld)"
  echo "  --all-profiles        Run modeld + pandad + system sequentially"
  echo "  --cov-target <path>   Coverage source target (default: selfdrive/modeld)"
  echo "  --baseline <tests>    Quoted baseline test paths/globs"
  echo "  --ours <tests>        Quoted new-test paths/globs"
  echo "  --out-dir <path>      Output directory for coverage artifacts"
  echo "  --cov-config <path>   Coverage rc file (default: profile-specific config)"
  echo "  -h, --help            Show this help"
  echo ""
  echo "Defaults are profile-specific and can be overridden with flags."
  echo ""
  echo "Example:"
  echo "  bash scripts/testing/compare_coverage.sh \\"
  echo "    --profile modeld \\"
  echo "    --cov-target selfdrive/modeld \\"
  echo "    --baseline \"selfdrive/modeld/tests/test_modeld.py\" \\"
  echo "    --ours \"selfdrive/modeld/tests/test_parse_model_outputs.py selfdrive/modeld/tests/test_fill_model_msg.py\""
  echo ""
  echo "Run all assignment targets:"
  echo "  bash scripts/testing/compare_coverage.sh --all-profiles"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    --all-profiles) RUN_ALL_PROFILES="1"; shift ;;
    --cov-target) CLI_COV_TARGET="$2"; OVERRIDE_COV_TARGET="1"; shift 2 ;;
    --baseline) CLI_BASELINE_TESTS="$2"; OVERRIDE_BASELINE="1"; shift 2 ;;
    --ours) CLI_OUR_TESTS="$2"; OVERRIDE_OURS="1"; shift 2 ;;
    --out-dir) CLI_OUT_DIR="$2"; OVERRIDE_OUT_DIR="1"; shift 2 ;;
    --cov-config) CLI_COV_CONFIG="$2"; OVERRIDE_COV_CONFIG="1"; shift 2 ;;
    --ours-only) INCLUDE_BASELINE_IN_OURS="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1"; usage; exit 1 ;;
  esac
done

function run_group() {
  local profile_name="$1"
  local cov_target="$2"
  local out_dir="$3"
  local cov_config="$4"
  local tests_str="$5"
  local group_name="$6"
  local coverage_file="$out_dir/.coverage.${group_name}"
  local xml_file="$out_dir/coverage-${group_name}.xml"
  local html_dir="$out_dir/html-${group_name}"
  local report_file="$out_dir/summary-${group_name}.txt"

  read -r -a test_args <<< "$tests_str"
  if [[ ${#test_args[@]} -eq 0 ]]; then
    echo "No tests specified for ${group_name}"
    exit 1
  fi

  echo ""
  echo "=== Running ${profile_name} (${group_name}) coverage ==="
  echo "Tests: ${tests_str}"
  # -n 0: disable xdist for this run so pytest-cov combines a single data file and
  #        worker processes cannot re-introduce test modules into the trace.
  COVERAGE_FILE="$coverage_file" "$PYTHON_BIN" -m pytest "${test_args[@]}" -n 0 \
    --cov="$cov_target" \
    --cov-config="$cov_config" \
    --cov-report=xml:"$xml_file" \
    --cov-report=html:"$html_dir"

  echo ""
  echo "--- ${profile_name} (${group_name}) coverage summary ---"
  "$PYTHON_BIN" -m coverage report --rcfile="$cov_config" --data-file="$coverage_file" --precision=2 --sort=cover | tee "$report_file"
}

function run_profile() {
  local name="$1"
  set_profile_defaults "$name"

  if [[ "$INCLUDE_BASELINE_IN_OURS" == "1" ]]; then
    OUR_TESTS="$BASELINE_TESTS $OUR_TESTS"
  fi

  if [[ "$RUN_ALL_PROFILES" == "0" ]]; then
    [[ "$OVERRIDE_COV_TARGET" == "1" ]] && COV_TARGET="$CLI_COV_TARGET"
    [[ "$OVERRIDE_BASELINE" == "1" ]] && BASELINE_TESTS="$CLI_BASELINE_TESTS"
    [[ "$OVERRIDE_OURS" == "1" ]] && OUR_TESTS="$CLI_OUR_TESTS"
    [[ "$OVERRIDE_OUT_DIR" == "1" ]] && OUT_DIR="$CLI_OUT_DIR"
    [[ "$OVERRIDE_COV_CONFIG" == "1" ]] && COV_CONFIG="$CLI_COV_CONFIG"
  fi

  mkdir -p "$OUT_DIR"

  run_group "$name" "$COV_TARGET" "$OUT_DIR" "$COV_CONFIG" "$BASELINE_TESTS" "baseline"
  run_group "$name" "$COV_TARGET" "$OUT_DIR" "$COV_CONFIG" "$OUR_TESTS" "ours"

  echo ""
  echo "Coverage artifacts written to: $OUT_DIR"
  echo " - baseline data: $OUT_DIR/.coverage.baseline"
  echo " - baseline xml : $OUT_DIR/coverage-baseline.xml"
  echo " - baseline html: $OUT_DIR/html-baseline/index.html"
  echo " - ours data    : $OUT_DIR/.coverage.ours"
  echo " - ours xml     : $OUT_DIR/coverage-ours.xml"
  echo " - ours html    : $OUT_DIR/html-ours/index.html"
}

if [[ "$RUN_ALL_PROFILES" == "1" ]]; then
  for p in modeld pandad system; do
    run_profile "$p"
  done
else
  run_profile "$PROFILE"
fi
