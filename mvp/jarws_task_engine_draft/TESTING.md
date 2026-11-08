# Testing this draft

## Requirements

- Python 3.11 or newer; verified with Python 3.14.4.
- Standard library only; no network access or third-party packages are required.

## Run

From the root of this directory:

```sh
python3 -B -I -m unittest discover -s tests -v
python3 -B -I -O -m unittest discover -s tests -v
```

`-B` prevents bytecode files from being written. `-I` runs Python in isolated mode. The second command checks that optimized mode does not disable test assertions.

## Current result

- Normal mode: 19 tests passed.
- Optimized mode (`-O`): 19 tests passed.

The tests cover role boundaries, critical pre-approval and post-completion review, inactive staging and rejection archival, provenance blocking, per-Task result checks, the five-round maximum, transient retry allow-listing, checker repair rounds, interruption, authorized unblock, state revalidation, and JSON round-trips for Task and Approval records.

## Limits

These are prototype tests, not a security audit or proof of production safety. They do not verify authentication, cryptographic signatures, concurrent writers, crash-safe atomic persistence, live-system activation, or every Task-specific output schema. Approval status names are provisional. The schema validators used in tests are examples, not accepted JARWS schemas.
