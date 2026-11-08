# JARWS Task Engine — working decisions

**Status: user-approved working framework; not a canonical Governance document.**

## Human approval

- Critical changes include Governance, permissions, security, protected-zone, and live-system-impacting changes.
- Prior human approval is the standard route.
- A change judged to advance development or project goals may use the post-completion review exception. The work remains isolated and inactive until the Director's final decision.
- An unapproved post-completion change must not be activated. If rejected, preserve it with rationale and evidence.
- Production authentication and signing remain open for a later security decision.

## Roles

- Governance defines rules.
- Validator checks task structure and prerequisites.
- Approval records the human decision and its evidence.
- Orchestrator coordinates the flow and exclusively manages Task state.
- Executor may write `result` and `evidence`, but not Task state or approval decisions.
- Checker remains a non-canonical post-check helper. It uses task-specific acceptance criteria and cannot approve or set `DONE`.

## Task contract

- Task execution state and critical-change approval state are separate records.
- The Task states remain `WAITING`, `RUNNING`, `BLOCKED`, `DONE`, and `ERROR` as the initial working set.
- Every Executor start counts toward a maximum of five execution rounds per Task, including the first start. The Task proposer may set a lower limit.
- Automatic retry applies only to a predefined list of safe transient errors.
- Checker rejection may trigger more Executor repair rounds up to the Task's round limit. If the final permitted round fails, the Task becomes `ERROR`; result and evidence are retained for human review or a new Task.
- Missing required provenance blocks the Task pending human completion.
- Interruption records a reason and moves the Task to `BLOCKED`. Founder, Director, or a Director delegate may unblock it. Unblocking returns it to `WAITING`; history is kept and Validator/Approval run again.
- Every Task records source references, initiator/responsible party, and a creation trace.
- Output validity is checked against a schema for the Task type. An experimental `DOCUMENT_REVIEW` v0.1 schema now exists in the local working draft, but it is not approved or production-ready. `CORE_CHANGE` and other work-kind schemas remain to be defined and approved.

## Known draft details

- The exact Approval status names and transitions remain provisional.
- The test schemas in this package are examples only.
- The meaning and eventual disposition of the temporary Founder role remain open.
- Authentication, signing, production identity, and secure persistence are not included.
