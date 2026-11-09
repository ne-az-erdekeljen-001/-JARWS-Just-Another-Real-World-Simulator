# Human approval traceability — proposal

**Status: PROPOSED.** This note is a process proposal, not an accepted JARWS governance rule.

## Observed gap

The descriptions of [PR #4](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/4) and [PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5) say they were merged after human approval. The GitHub PR review lists currently show no submitted reviews. The repository therefore does not expose a review record that independently documents those approvals.

This observation does not establish whether approval happened elsewhere. It does not retroactively certify or reject either change.

## Proposed rule for future changes

For changes that require human approval, record the decision in a project record linked directly from the PR.

1. **Default record:** use a DEC record under `decisions/`, linked from the PR. Under the current single-account workflow, this is the practical default because the PR author cannot submit an independent approval review on their own PR.
2. **Optional GitHub review:** when a distinct, authorized human reviewer is available, link their review as additional evidence. A review does not replace the DEC if the decision must remain part of JARWS's durable decision history.
3. **Required decision details:** identify the human decision-maker and their role at the time; state the outcome and rationale; identify the approved commit SHA and scope; and link the approval evidence and the decision record's location.
4. **Dates and provenance:** record both when the decision happened (`esemenyDatuma`) and when it was entered into the project record (`rogzitveDatuma`). If AI contributed to drafting the record, list the AI model and version, or mark either as `ISMERETLEN`.
5. Do not describe a change as human-approved unless the linked record identifies the approval evidence. A merge alone is not that evidence.

The DEC should use the project's accepted DEC format. This proposal does not choose a new schema or status vocabulary.

## Historical records

Do not infer missing approval details from a merge alone. Add retrospective decision records only after the Founder confirms the approval event, its outcome, and its scope. Record both the event date and the later entry date. If the evidence cannot be established, record the approval status as unknown.

## Decision needed

The Founder must decide whether to accept, revise, or reject this proposal before it becomes canonical. If accepted, a separate DEC should record that decision and link to the merged change; this proposal itself does not constitute its own approval record.
