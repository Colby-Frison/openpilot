# Testing tracker (living document)

**Purpose:** Single place to record what testing work is **done**, **in progress**, and **not started** for the course scope (`selfdrive/modeld`, listed `selfdrive/pandad` files, `system/`). Update this file when you merge tests, open tickets, or change priorities.

**Related plans (strategy and tactics):**

- [Software Test Plan (STP)](testing-plan/TESTING-PLAN.md) — risks R1–R10, scope, verification and validation approach.
- [Low-level test plan](LOW-LEVEL-TEST-PLAN.md) — pytest layout, phases, commands, definition of done.

**Conventions:**

- Use `Maps: R#` in new test docstrings (see LOW-LEVEL §Phase 0).
- Mark items `[x]` when merged and stable in `main` (or your integration branch).
- Mark items `[~]` for in-progress (optional; or use a short note under the item).
- Mark `[-]` when an item is **deferred** (e.g. needs hardware) rather than a remaining task for the current milestone.

---

## Summary

| Subsystem | Done (high level) | Open / next |
|-----------|-------------------|-------------|
| modeld | Parser unit suite; fill + integration test files exist | Extend fill/integration coverage; optional timing tests |
| pandad | **Desktop / course scope complete:** CAN capnp split tests; ``pandad.py`` wrapper + ``flash_panda``; USB gtest (pack/unpack + incomplete buffer + bus filter); in ``our_tests`` CI | **Out of course gate:** loopback, SPI, ``test_pandad`` need real pandas + ``tici`` (see below) |
| system | Upstream tests per component | Team-owned extensions per LOW §4.3 P0–P2 |
| Infra | Shared `support/` packages + pytest plugins; harness smoke + multi-service IPC | Extend harness or extract duplicated setup |

---

## modeld (`selfdrive/modeld/tests/`)

Aligned with [LOW-LEVEL §7.1](LOW-LEVEL-TEST-PLAN.md#71-modeld-rollout-gates) rollout gates.

| Status | Item | Location / command |
|--------|------|---------------------|
| [x] | **Phase A:** `Parser`, `safe_exp`, `sigmoid`, `softmax`, MDN/crossentropy paths; Ruff clean | `selfdrive/modeld/tests/test_parse_model_outputs.py` |
| [x] | **Phase B:** `fill_model_msg` contracts (frame ids, `modelV2` dims, pose/odometry, drivingModelData, raw pred); parser vision/policy including optional policy keys | `modeld_test_fixtures.py`, `modeld_parse_fixtures.py`, `test_fill_model_msg_*.py`, `test_parse_model_outputs_*_contracts.py` |
| [x] | **Phase B+:** deeper per-field assertions on fill/parser paths (pose tensors, lane meta, plan/temporal/leads, parser sigmoid/MDN bounds) | `test_fill_model_msg_*.py`, `test_parse_model_outputs_*_contracts.py` |
| [x] | **Phase C (extension):** Daemon contracts (`modelV2` / `cameraOdometry` / `drivingModelData` frame lock, EOF monotonicity, execution time finite, frame age, timeliness ceiling) — skips if modeld never publishes | `selfdrive/modeld/tests/test_modeld_phase_c_contracts.py` |
| [x] | **Phase C (anchor):** Upstream VisionIPC + `modeld` integration unchanged; gate via scoped pytest | `selfdrive/modeld/tests/test_modeld.py` |
| [x] | **Phase C (timeliness):** Documented `modelExecutionTime` ceiling (subtest; same harness as extension) | `test_modeld_phase_c_contracts.py` (subtest in `test_phase_c_daemon_message_contracts`) |
| [ ] | **Coverage compare (opt-in):** Run `scripts/testing/compare_coverage.sh` and archive reports under `.coverage-compare/modeld/` | See [testing.md](testing.md) snippet |
| [ ] | **Gate:** Full suite green before merge | `pytest selfdrive/modeld/tests -q` |

**Existing files (not necessarily “complete” for course goals):**

- `test_constants.py` — constants / contract checks as implemented.
- `test_fill_model_msg.py` — message fill tests (extend as needed).
- `test_modeld.py` — VisionIPC + managed `modeld` integration.

---

## pandad (assignment-scoped files)

**Definition of done (course / STP desktop):** all rows in **A** are `[x]`. The three rows in **B** are **existing upstream** suites that need **Comma device / multiple pandas**; they are **not** a failing checklist for this fork—**deferred** unless the team runs them on `tici` hardware.

### A — Desktop (no Panda bus), course gate in [`our_tests.yaml`](../../.github/workflows/our_tests.yaml) + gtest binary

| Status | Item | Location / how to run |
|--------|------|-------------------------|
| [x] | CAN capnp serialization (split: roundtrip, event validity, multiblob) — skips if Cython ext missing | `test_pandad_can_capnp_roundtrip.py`, `test_pandad_can_capnp_event_validity.py`, `test_pandad_can_capnp_multiblob.py` |
| [x] | ``pandad.py`` ``get_expected_signature`` (mocked ``Panda``) | `selfdrive/pandad/tests/test_pandad_pandad_wrapper.py` |
| [x] | ``pandad.py`` ``flash_panda`` (mocked device: no-op, reflash, bootstub, post-flash mismatch) | `selfdrive/pandad/tests/test_pandad_flash.py` |
| [x] | USB protocol gtest: pack/unpack (parameterized) + **incomplete receive reassembly** + **bus filter** in ``pack_can_buffer`` | `selfdrive/pandad/tests/test_pandad_usbprotocol.cc` — `scons -j8 selfdrive/pandad/tests/test_pandad_usbprotocol` then `selfdrive/pandad/tests/test_pandad_usbprotocol` |

**One-shot local verification (matches CI intent):**

```bash
# Pytest (after venv + scons; same set as our-tests workflow for pandad+modeld)
source .venv/bin/activate
python -m pytest \
  selfdrive/modeld/tests/test_parse_model_outputs.py \
  selfdrive/modeld/tests/test_constants.py \
  selfdrive/pandad/tests/test_pandad_flash.py \
  selfdrive/pandad/tests/test_pandad_pandad_wrapper.py \
  selfdrive/pandad/tests/test_pandad_can_capnp_roundtrip.py \
  selfdrive/pandad/tests/test_pandad_can_capnp_event_validity.py \
  selfdrive/pandad/tests/test_pandad_can_capnp_multiblob.py \
  -q
scons -j8 selfdrive/pandad/tests/test_pandad_usbprotocol
./selfdrive/pandad/tests/test_pandad_usbprotocol
```

### B — Hardware / `tici` (upstream; optional for this project)

| Status | Item | Location | Note |
|--------|------|----------|------|
| [-] | Loopback: zero message loss (real pandas) | `test_pandad_loopback.py` | `COMMA` + pandas; not in fork CI |
| [-] | SPI fault injection (``SPI_ERR_PROB``) | `test_pandad_spi.py` | `tici` + hardware path |
| [-] | Firmware recovery / safety-adjacent flows | `test_pandad.py` | Device / `tici` as marked |

**Maps:** R2, R3 (A); R2 for full safety/heartbeat (B, device).

---

## `system/`

Priorities from [LOW-LEVEL §4.3](LOW-LEVEL-TEST-PLAN.md#43-system).

| Priority | Status | Item | Location |
|----------|--------|------|----------|
| P0 | [ ] | Manager lifecycle / graph (restart-kill-reconnect if env allows) | `system/manager/test/` |
| P0 | [~] | Manager **config / gating** contracts (desktop; no process start) | `system/tests/contract/test_manager_process_config_contracts.py` + [SYSTEM-TESTING.md](SYSTEM-TESTING.md) |
| P0 | [ ] | Logger encode / delete / backpressure or corruption scenarios | `system/loggerd/tests/` |
| P1 | [~] | Cereal pub/sub smoke under ``SIMULATION`` (harness reuse) | `system/tests/contract/test_messaging_simulation_contract.py` |
| P1 | [~] | Additional contract coverage (manager/build/timed/tombstoned/athenad helpers/snapshot/power monitor/agnos helpers) | `system/tests/contract/test_*_contracts.py` |
| P1 | [ ] | Athena session / auth / failure (mocked) | `system/athena/tests/` |
| P1 | [ ] | WebRTC session / failure modes | `system/webrtc/tests/` |
| P1 | [ ] | Camera timing regression (`slow` / `tici` as needed) | `system/camerad/test/` |
| P2 | [ ] | Update staging / overlay integrity | `system/updated/tests/`, `selfdrive/test/test_updated.py` |
| P2 | [ ] | GPS / sensor parser fixtures | `system/ubloxd/tests/`, `system/sensord/tests/`, `system/qcomgpsd/tests/` |
| P2 | [ ] | Thermal / power policy (device) | `system/hardware/tici/tests/` |

**Maps:** R4–R10 per subsystem (see LOW-LEVEL traceability matrix).

---

## Shared testing infrastructure

| Status | Item | Location |
|--------|------|----------|
| [x] | Selfdrive support: processes, params seed, messaging builders, pytest fixtures | `selfdrive/test/support/` |
| [x] | System support: re-exports + system fixtures | `system/tests/support/` |
| [x] | Root `pytest_plugins` registration | Root `conftest.py` |
| [x] | Harness smoke tests (params seeds, pub/sub factory) | `selfdrive/test/support/tests/test_selfdrive_support_harness.py`, `system/tests/support/tests/test_system_support_harness.py` |
| [x] | Multi-service pub/sub round-trip (system harness) | `system/tests/support/tests/test_system_support_messaging_multi_service.py` |
| [ ] | Extract duplicated setup to support after **third** copy | Per LOW-LEVEL §7 |

---

## GitHub Actions (CI)

Upstream openpilot runs a **large** `selfdrive` workflow (Docker image `ghcr.io/commaai/openpilot-base`, scons in container, `PYTHONWARNINGS=error`, `pytest` with coverage, process replay, car model matrices, static analysis, macOS build, etc.). On a **class / team fork** (e.g. `Colby-Frison/openpilot`), the same job definitions often **fail** for reasons that are not about your new tests: missing `CODECOV_TOKEN`, `AZURE_COMMADATACI_*` secrets, smaller runners, Docker pull limits, or download caches.

| Workflow / file | What it is | Expectation on team fork | Course signal |
|-------------------|------------|---------------------------|---------------|
| [`.github/workflows/our_tests.yaml`](../../.github/workflows/our_tests.yaml) | `our-tests` — native Ubuntu, deps + full `scons` + **pytest** (modeld + pandad course tests) | **Should** pass if `main` + tests are consistent | **Primary** “green” for authored tests |
| [`.github/workflows/selfdrive_tests.yaml`](../../.github/workflows/selfdrive_tests.yaml) | `selfdrive` — build, static analysis, unit + replay + cars + UI report | **Skipped** on pushes/PRs that only use a team fork as **base** (e.g. `Colby-Frison` → `Colby-Frison`). **Runs** on `commaai/openpilot` and on **PRs into** `commaai/openpilot` (incl. from a fork). | Match upstream on PRs to comma; for fork-only branches rely on `our-tests`. |
| [`.github/workflows/docs.yaml`](../../.github/workflows/docs.yaml) | Docs build | Usually passes | Light check |
| `ui_preview`, `PR comments` | Often **skipped** by `if` / draft | N/A | N/A |

**Local equivalents (before push):** `scons` + `pytest` for the same paths as `our_tests.yaml`; optional `tools/op.sh lint` and `selfdrive/pandad/tests/test_pandad_usbprotocol` after `scons` when touching C++.

**Note:** Merging a PR **into** `commaai/openpilot` will still run the full `selfdrive` suite on the **main** repository with proper secrets; fork-only CI is intentionally **narrower** so the team is not blocked by infrastructure.

---

## Nonfunctional themes (STP §7.2)

Track as **additional cases** in the rows above, not as orphan workstreams.

| Status | Theme | Typical target |
|--------|--------|----------------|
| [ ] | Stress / soak with manager-controlled processes | `system/manager/test/` |
| [ ] | Disk pressure / uploader retry behavior | Loggerd + related upload tests |
| [ ] | Security / privacy failure behavior | `system/athena/tests/`, `system/webrtc/tests/` |

---

## Changelog (optional)

Edit when you want a paper trail without git archaeology:

| Date | Change |
|------|--------|
| 2026-04-20 | Initial tracker; Phase A modeld parser suite marked done. |
| 2026-04-20 | Added system + selfdrive support harness tests and pandad `test_pandad_can_capnp.py`. |
| 2026-04-20 | Expanded pandad STP-aligned desktop tests (`test_pandad_can_capnp.py`, `test_pandad_pandad_wrapper.py`). |
| 2026-04-24 | Split pandad CAN tests into `test_pandad_can_capnp_*.py`; added modeld fill contracts + `modeld_test_fixtures.py`; added system multi-service harness test. |
| 2026-04-24 | Modeld: `modeld_parse_fixtures`, vision/policy parser contracts, `fill_pose_msg`, drivingModelData, `SEND_RAW_PRED` tests. |
| 2026-04-24 | Modeld Phase C: `test_modeld_phase_c_contracts.py` (daemon contracts; skips if modeld never publishes). |
| 2026-04-24 | Modeld Phase B+ marked done (deeper fill/parser assertions); Phase C extended (`drivingModelData` lock + timeliness subtest); anchor `test_modeld.py` left unchanged. |
| 2026-04-24 | System: `docs/testing/SYSTEM-TESTING.md` + `system/tests/contract/` (manager predicates, messaging simulation); renamed from `course/`. |
| 2026-04-24 | System contract suite expanded: manager/build/timed/tombstoned/athenad/snapshot/power-monitor/agnos helpers; documented non-contractable device/network files. |
| 2026-04-24 | System contract pass 2: added `athenad` queue/upload helper contracts and `agnos` partition helper contracts; coverage compare now shows `ours` > `baseline` for system profile. |
| 2026-04-25 | Pandad: `test_pandad_flash.py` for `flash_panda()`; USB gtest sections `incomplete_receive_buffering` + `bus_filtering` in `test_pandad_usbprotocol.cc`. |
| 2026-04-26 | Document GitHub Actions: fork vs `commaai` CI; `our_tests` widened; `selfdrive` jobs gated to upstream + optional dispatch; Codecov `fail_ci_if_error: false` on unit/replay/cars. |
| 2026-04-27 | Pandad: section “finished” — A vs B (desktop done vs device deferred); local verification block; summary row updated. `our_tests.yaml` pytest list aligned with pandad capnp split files. |
