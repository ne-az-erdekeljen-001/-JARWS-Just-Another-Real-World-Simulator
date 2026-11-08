# JARWS Task Engine — submission draft

**Status: experimental working draft; not canonical and not production security.**

This package is a noncanonical working draft in the main JARWS repository. It demonstrates the Task and approval working rules gathered during the JARWS audit. Publication in the repository does not make it canonical; the remaining project decisions are still open.

## Contents

- `jarws_task_engine/engine.py` — experimental Task Engine implementation.
- `jarws_task_engine/schemas.py` — experimental `DOCUMENT_REVIEW` input and result validator.
- `tests/test_engine.py` — standard-library regression tests for the accepted working matrix.
- `TESTING.md` — reproducible test instructions and current test result.
- `docs/WORKING_DECISIONS.md` — decision provenance and the boundaries of this draft.
- `docs/TASK_TYPE_SCHEMAS_PROPOSAL.md` — noncanonical schema proposal for `DOCUMENT_REVIEW` and future `CORE_CHANGE` work.

## Current verification

The test suite has 25 tests. It passed under both normal Python and optimized Python (`-O`) in an isolated invocation on Python 3.14.4.

See `TESTING.md` for commands, environment details, and limitations.

## Important limits

- The `DOCUMENT_REVIEW` v0.1 validator and the other result schemas are experimental examples. They are not approved production schemas; `CORE_CHANGE` still needs its own result schema.
- The retry allow-list currently uses the explicit `TransientExecutionError` type only. Expanding the list needs review, especially for operations that may have side effects.
- The post-completion approval route keeps work marked inactive until a final decision. This package does not connect to or change a live JARWS system.
- Python object boundaries are not a security sandbox. An Executor is technically able to inspect private attributes at runtime; production enforcement needs a separate security design.
- Authentication, signing, production identity, and secure persistence are not implemented.
- Approval status names and some schema details remain draft choices.

This package should not be presented as a canonical JARWS implementation until the remaining decisions and final human review are completed.
