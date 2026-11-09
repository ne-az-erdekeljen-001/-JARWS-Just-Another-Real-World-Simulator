# Human approval traceability — proposal

**Status: PROPOSED.** This note is a process proposal, not an accepted JARWS governance rule.

## Observed gap

The descriptions of [PR #4](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/4) and [PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5) say they were merged after human approval. The GitHub PR review lists currently show no submitted reviews. The repository therefore does not expose a review record that independently documents those approvals.

This observation does not establish whether approval happened elsewhere. It does not retroactively certify or reject either change.

## Proposed rule for future changes

For changes that require human approval, record the approval in a place linked directly from the PR:

1. Prefer a GitHub review submitted by the human decision-maker on the exact PR revision being approved.
2. If approval occurs outside GitHub, link a decision record from the PR. Record the approver, decision date, approved commit SHA, scope, and the source of the approval evidence.
3. Do not describe a change as human-approved unless the linked record identifies the approval evidence.

## Historical records

Do not infer missing approval details from a merge alone. Add retrospective decision records only after the Founder confirms the approval event and its scope. If the evidence cannot be established, record the approval status as unknown.

## Decision needed

The Founder must decide whether to accept, revise, or reject this proposal before it becomes canonical.
