# `system/tests/` layout

This tree is **intentional**, not a duplicate by mistake. It mirrors the same idea as `selfdrive/test/support/` (reusable helpers) plus a **contract** test area.

| Path | What it is | Why it exists |
|------|-------------|----------------|
| **`support/`** | Importable package `openpilot.system.tests.support` | Shared **fixtures** (`system_daemon_params`, `system_pub_sub_factory`, …), **params** seeding, **messaging** helpers, re-export of `managed_process_scope`. Consumed by tests under `system/` and registered via root `pytest_plugins`. **Not** a pytest collection root by itself—there are no `test_*.py` files here. |
| **`support/tests/`** | Tests **for** that support package | Smoke tests that the harness works (`test_system_support_harness.py`, `test_system_support_messaging_multi_service.py`). Same pattern as `selfdrive/test/support/tests/`. |
| **`contract/`** | **Contract tests** for `system/` (predicates, messaging IPC, …) | Small, desktop-safe checks aligned with the STP / low-level plan. Uses `system_*` fixtures; does not replace component suites under `system/manager/test/`, `system/loggerd/tests/`, etc. |
| **`test_logmessaged.py`** (root of `system/tests/`) | Upstream-style integration | Lives next to `support/` because it is a **system-level** test that starts `logmessaged`; it is not part of the small support package. |

**Summary:** `support/` = **library**, `support/tests/` = **tests of the library**, `contract/` = **contract tests** for product behavior using the library (and other code). No merge or rename is required unless you want a flatter tree (would break symmetry with selfdrive and imports).

Strategy and hardware boundaries: [docs/testing/SYSTEM-TESTING.md](../../docs/testing/SYSTEM-TESTING.md).
