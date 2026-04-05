This directory documentation for testing the openpilot project 0.9.8 release done by Group C cluster 1 for the Software Quality and testing course (CS 4223) at the University of Oklahoma under professor Mansoor Abdulhak.

# Table of Contents
* [Assigned Subsystems](#assigned-subsystems)
* [Directories](#directories)
* [Infrastructure overview](#infrastructure-overview)
* [Low-level test plan](#low-level-test-plan)

# Assigned Subsystems
* *selfdrive/modeld* (all files)
* *selfdrive/pandad* (assignment-listed files only):
  * *pandad\_api\_impl.pyx*
  * *pandad.cc*
  * *pandad.h*
  * *pandad.py*
  * *SConscript*
  * *spi.cc*
* *system/* (entire directory)

# Directories

* [testing-plan](testing-plan): Testing plan for the assigned subsystems of openpilot shown in both Markdown and PDF format.

# Infrastructure overview

* [INFRASTRUCTURE-OVERVIEW.md](INFRASTRUCTURE-OVERVIEW.md): How pytest, root `conftest.py`, and the `selfdrive/` + `system/` support packages fit together; diagrams; where to add tests; fixture cheat sheet.

# Low-level test plan

* [LOW-LEVEL-TEST-PLAN.md](LOW-LEVEL-TEST-PLAN.md): Tactical guide aligned with the STP—repository pytest/native conventions, phased shared infrastructure (`selfdrive/test/support/` and `system/tests/support/`), per-subsystem work breakdown, risk traceability (R1–R10), and scoped commands.

**Support harnesses (fixtures + empty plug-in suites):**

* Selfdrive: `python -m pytest selfdrive/test/support/tests -q`
* System: `python -m pytest system/tests/support/tests -q`

Each should report no tests collected and exit successfully until you add `test_*.py` files there. Fixtures from both `support/fixtures.py` modules load globally via root `pytest_plugins` (`openpilot_params_seeded`, `system_daemon_params`, etc.).

