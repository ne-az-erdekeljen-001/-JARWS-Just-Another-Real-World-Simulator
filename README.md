# JARWS — Just Another Real World Simulator

JARWS is an open, modular development environment for people and AI systems to model, explore, and build digital worlds and complex systems together.

## Project status

JARWS is in early development. Current work focuses on a project baseline, governance, task structure, and testable MVP components. Governance and safety mechanisms remain under development.

## What works today

The experimental Task Engine draft includes input and result validation for `DOCUMENT_REVIEW` and `CORE_CHANGE`. Its 28-test suite passed in normal and optimized (`-O`) Python 3.14.4 runs.

**Verified:** 2026-11-09 · commit `f898044c72399fb063b95d91ab018131c5d8778e` · Python 3.14.4 · fresh clone. Both commands below passed 28 tests. This verification applies to that commit and test suite only; it does not establish that the whole platform is complete, correct, secure, or production-ready.

A separate earlier run of `jarws_mvp_v03.py` reported 5/5 tests passing with JSON persistence. That result applies only to that MVP test run.

## Try the Task Engine draft

Requires Python 3.11 or newer. The draft uses only the Python standard library. From a terminal:

```sh
git clone https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator.git jarws
cd jarws/mvp/jarws_task_engine_draft
python3 -B -I -m unittest discover -s tests -v
python3 -B -I -O -m unittest discover -s tests -v
```

The normal and optimized runs each report 28 tests passing. See [the draft's testing notes](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/blob/main/mvp/jarws_task_engine_draft/TESTING.md) for coverage and limitations.

## What this does not prove

The Task Engine and schemas are experimental, noncanonical prototypes. The tests are not a security audit or proof of production safety. They do not verify authentication, signing, concurrent-write protection, crash-safe persistence, or live-system activation. Python object boundaries do not enforce a security sandbox. These limits are described in [PR #3](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/3); see also [PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5) for the current implementation summary.

## Guiding principles

- Human oversight for critical decisions.
- AI systems act as cooperative components, not independent authorities over the project's foundations.
- Modular design and clear boundaries between responsibilities.
- Traceable decisions, explicit status labels, and controlled changes.
- Collaboration and responsible experimentation.

## Status labels

Project notes may use these labels:

- `PROVEN` — supported by a recorded test or other evidence.
- `ACCEPTED` — explicitly accepted as a project decision.
- `IN_DEVELOPMENT` — actively being developed.
- `PROPOSED` — suggested, but not yet accepted or implemented.
- `OPEN_QUESTION` — requires a decision or further investigation.
- `UNKNOWN` — not currently established.

A proposal is not an implementation or a final decision. The status vocabulary is still subject to alignment with the project specification.

## Versioning and scope

The current development baseline is in the early 0.1–0.3 range. Version labels describe the maturity of specific work, not completion of the overall platform.
