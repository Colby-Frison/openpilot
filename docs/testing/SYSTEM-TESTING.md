# System subsystem testing (contract suite)

**Purpose:** Describe how we test `system/` under the Software Test Plan (STP) and [Low-level test plan](LOW-LEVEL-TEST-PLAN.md), with emphasis on the **software / hardware boundary** and what runs on a developer machine versus on a comma device (TICI).

**Audience:** implementers extending `system/` tests without duplicating upstream suites or destabilizing CI.

---

## 1. Scope and priorities (sparse coverage)

`system/` is large (manager, loggerd, camerad, athena, webrtc, hardware, ublox, sensord, updated, etc.). The STP maps risks **R4–R10** to these areas ([LOW-LEVEL §4.3](LOW-LEVEL-TEST-PLAN.md#43-system)).

**Contract-test strategy:** keep **small, high-signal** tests under `system/tests/contract/` that:

- Assert **contracts** (process names, gating predicates, messaging patterns) without owning full integration matrices.
- Prefer **pure logic** and **mocked I/O** over long-running or device-bound flows.
- Link to existing upstream tests under each component (`system/manager/test/`, `system/loggerd/tests/`, `system/athena/tests/`, …) as the **primary** evidence for R4–R6; the contract suite **supplements** traceability and desktop CI.

---

## 2. Software vs hardware boundary

| Layer | Examples | Typical test approach |
|--------|-----------|------------------------|
| **Pure Python / config** | `process_config` predicates, `managed_processes` map | Unit tests anywhere (e.g. `system/tests/contract/`). No hardware. |
| **Daemons on loopback** | `logmessaged`, pub/sub to cereal services | `managed_processes['…'].start()` in **existing** tests (e.g. `system/tests/test_logmessaged.py`); use `SIMULATION=1` where the tree expects it. Watch for flakiness and timeouts. |
| **Native binaries + devices** | `camerad`, `pandad`, `ubloxd` on `/dev/*` | Mark **`@pytest.mark.tici`** or **`@pytest.mark.slow`** per [root `pyproject.toml`](../../pyproject.toml) markers; skip on desktop via existing conftest patterns. **Do not** assume cameras, GPS UART, or Panda in `system/tests/contract/`. |
| **HAL / power** | `system/hardware/tici/tests/` | Device-only; document as such in test docstrings. |

### 2.1 How the barrier is handled in this repo

1. **Markers:** `tici`, `slow`, `skip_tici_setup` are defined globally; strict markers are on. New system tests that touch hardware **must** declare the correct marker and state assumptions in the docstring.

2. **Environment:** Many tests set `SIMULATION=1` or `FAKEUPLOAD=1` (see `system/manager/test/test_manager.py`) to avoid real uploads or device-specific branches where the code already supports it.

3. **Fixtures:** Use `system_daemon_params`, `system_full_stack_params`, and `system_pub_sub_factory` from [`system/tests/support/fixtures.py`](../../system/tests/support/fixtures.py) so Params and messaging match what daemons expect—**without** implying a full car is present.

4. **Contract suite vs component suites:** Upstream tests under `system/athena/tests/`, `system/manager/test/`, etc. remain the **authority** for deep behavior. `system/tests/contract/` holds **additional** STP-aligned checks without forking those trees.

5. **When in doubt:** Skip with `pytest.skip("…")` and a one-line reason (e.g. missing `/dev/ttyHS0`) rather than failing desktop CI.

---

## 3. Where tests live

| Location | Role |
|----------|------|
| `system/tests/support/` | **Package** (fixtures, params seed, messaging helpers)—importable code, no `test_*.py` here. Same role as `selfdrive/test/support/`. |
| `system/tests/support/tests/` | **Tests of the support package** (harness smoke). Not redundant with `support/`; one is the library, the other verifies it. |
| `system/tests/contract/` | **Contract tests** (manager config, messaging simulation, …). Uses `system_*` fixtures; does not test the harness itself. |
| `system/tests/test_logmessaged.py` | Integration test colocated under `system/tests/`; not inside `support/`. |
| `system/manager/test/`, `system/loggerd/tests/`, … | Upstream-style integration per component; run as documented in LOW-LEVEL §6. |

See also [`system/tests/README.md`](../../system/tests/README.md) for a short directory map.

---

## 4. Commands (copy-paste)

```bash
# Contract tests only (fast, no hardware assumed)
pytest system/tests/contract -q

# Existing harness + multi-service messaging smoke
pytest system/tests/support/tests -q

# Upstream manager / loggerd suites (heavier; may start processes)
pytest system/manager/test/ -q
pytest system/loggerd/tests/ -q

# Athena (network / crypto; may use mocks in-tree)
pytest system/athena/tests/ -q
```

---

## 5. Traceability

| STP risk | Focus | Primary evidence | Contract supplement |
|-----------|--------|------------------|---------------------|
| R4 | Manager orchestration | `system/manager/test/test_manager.py` | `system/tests/contract/test_manager_process_config_contracts.py` |
| R5 | Logger integrity | `system/loggerd/tests/*` | Documented above; extend loggerd only when justified |
| R6 | Athena / webrtc | `system/athena/tests/*`, `system/webrtc/tests/*` | Keep using mocks; no secrets in tests |
| R7–R10 | Camera, update, GPS, thermal | Component `tests/` under each folder | Markers + skips; no fake hardware in `contract/` |

---

## 6. Changelog

| Date | Change |
|------|--------|
| 2026-04-24 | Initial `SYSTEM-TESTING.md`; `system/tests/contract/` (manager config + messaging simulation). |
| 2026-04-24 | Renamed `course/` → `contract/` for industry-standard naming. |
| 2026-04-24 | Expanded contract suite to manager/build/timed/tombstoned/snapshot/power monitor/athenad/agnos helper coverage (desktop-safe, mocked I/O). |


## 7. What we do not test in contract suite

Some files are intentionally **not** covered by `system/tests/contract/` because a
meaningful test requires hardware, long-running threads, or external network state:

- `system/hardware/tici/esim.py` — talks to `/dev/ttyUSB2` modem and real eSIM endpoints.
- `system/hardware/tici/precise_power_measure.py` — CLI sampling loop around live power rails.
- Large portions of `system/athena/athenad.py` — websocket threads, proxy sockets, upload I/O, and network conditions are exercised better in integration/system tests than in narrow unit mocks.

For these paths we keep contract tests to deterministic helpers and document the
remaining risk as integration/device work.

