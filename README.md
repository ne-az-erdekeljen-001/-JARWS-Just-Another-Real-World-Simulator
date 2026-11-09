# JARWS — Just Another Real World Simulator

JARWS is an open, modular development environment for people and AI systems to model, explore, and build digital worlds and complex systems together.

## Project status

JARWS is in early development. Current work establishes a project baseline, governance model, task structure, and testable MVP components.

## What works today

The experimental Task Engine draft includes input and result validation for `DOCUMENT_REVIEW` and `CORE_CHANGE`. Its 28-test suite passed in normal and optimized (`-O`) Python 3.14.4 runs, as reported in [PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5). This is evidence for that test run only; it does not establish that the whole platform is complete, correct, secure, or production-ready.

A separate earlier run of `jarws_mvp_v03.py` reported 5/5 tests passing with JSON persistence. That result applies only to that MVP test run.

## How to explore

Start with the [Task Engine implementation proposal and its limits in PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5), then review the [DOCUMENT_REVIEW prototype in PR #4](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/4). Both PRs describe experimental, noncanonical work and state their verification limits.

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

Governance and safety mechanisms remain under development. This README describes project intent and is not a claim of complete implementation or a security guarantee.
