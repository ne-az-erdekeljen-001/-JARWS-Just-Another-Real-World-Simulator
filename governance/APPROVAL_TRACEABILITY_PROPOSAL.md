# Human approval traceability — proposal

**Status: PROPOSED.** This note is a process proposal, not an accepted JARWS governance rule.

## Observed gap

The descriptions of [PR #4](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/4) and [PR #5](https://github.com/ne-az-erdekeljen-001/-JARWS-Just-Another-Real-World-Simulator/pull/5) say they were merged after human approval. The GitHub PR review lists currently show no submitted reviews. The repository therefore does not expose a review record that independently documents those approvals.

This observation does not establish whether approval happened elsewhere. It does not retroactively certify or reject either change.

## Proposed rule for future changes

For every approval request that is closed, record the decision in a project record linked directly from the PR.

1. **Default record:** use a DEC record under `decisions/`, linked from the PR. Under the current single-account workflow, this is the practical default because the PR author cannot submit an independent approval review on their own PR.
2. **Optional GitHub review:** when a distinct, authorized human reviewer is available, link their review as additional evidence. A review does not replace the DEC if the decision must remain part of JARWS's durable decision history.
3. **Record location, ID, and format:** create one Markdown file named `decisions/DEC-NNNN.md`, using the next unused stable four-digit DEC ID (for example, `decisions/DEC-0017.md`). Follow specification §11: YAML front matter plus a Markdown body. Use the common DEC fields and DEC-specific fields from specification §§4 and 6; do not invent a second format for PR approvals.
4. **Required decision details:** identify the human decision-maker and their role at the time; state the outcome and rationale; identify the approved candidate commit SHA and scope; and link the PR and approval evidence. Include the required DEC fields, including `tema`, `dontes`, `indoklas`, `alternativak`, `dontesHozo`, `kovetkezmenyek`, `eredet`, and `szerzoseg`.
5. **Which SHA is approved:** the approval applies to the exact candidate PR head SHA reviewed and named in the DEC. After the human decision, add the DEC in a follow-up documentation commit or separate documentation PR; that record must cite the already approved candidate SHA, not its own later commit or a moving branch name. Do not treat the later DEC commit or merge commit as the approval target. If the proposed change changes after approval, obtain a new decision for the new candidate SHA. A later merge SHA may be added only as a new DEC version if needed.
6. **Outcome, dates, and provenance:** record `APPROVED`, `REJECTED`, or `NO_APPROVAL` as the decision outcome in `dontes`. Use `REJECTED` only when a human explicitly rejects the proposed change. Use `NO_APPROVAL` when an approval request is closed without approval, including when it is withdrawn, cancelled, or closed after no response; this records the closure outcome and does not imply that a reviewer rejected the change. Record both when the decision or closure happened (`esemenyDatuma`) and when it was entered into the project record (`rogzitveDatuma`). If AI contributed to drafting the record, list the AI model and version in `kozremukodok`, or mark either as `ISMERETLEN`.
7. Do not describe a change as human-approved unless the linked record identifies the approval evidence. A merge alone is not that evidence.

For every closed request without explicit approval, create a DEC with outcome `NO_APPROVAL`; identify the human who closed it and their role, the closure reason, and the evidence (such as the PR closure or withdrawal). Do not infer an intentional rejection from silence. If the request has not been explicitly closed, it remains pending and unapproved; do not describe or merge it as approved.

## Historical records

Do not infer missing approval details from a merge alone. Add retrospective decision records only after the Founder confirms the approval event, its outcome, and its scope. Record both the event date and the later entry date. If the evidence cannot be established, record the approval status as unknown.

## Decision needed

The Founder must decide whether to accept, revise, or reject this proposal before it becomes canonical. If accepted, a separate DEC should record that decision and link to the merged change; this proposal itself does not constitute its own approval record.
