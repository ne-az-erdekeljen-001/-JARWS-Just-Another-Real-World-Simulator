"""Experimental task input and result schemas for the JARWS working draft."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
DOCUMENT_REVIEW_VERSION = "0.1"
DOCUMENT_REVIEW_CATEGORIES = {
    "AGREEMENT",
    "GAP",
    "CONTRADICTION",
    "RISK",
    "OPEN_QUESTION",
}


def validate_document_review_input(value: Any) -> tuple[bool, str]:
    if not isinstance(value, Mapping):
        return False, "DOCUMENT_REVIEW input must be an object."
    if value.get("work_kind") != DOCUMENT_REVIEW:
        return False, "work_kind must be DOCUMENT_REVIEW."
    if not isinstance(value.get("request"), str) or not value["request"].strip():
        return False, "A non-empty request is required."

    sources = value.get("sources")
    if not isinstance(sources, list) or not sources:
        return False, "At least one review source is required."
    source_ids: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, Mapping):
            return False, f"Source {index + 1} must be an object."
        source_id = source.get("source_id")
        reference = source.get("reference")
        if not isinstance(source_id, str) or not source_id.strip():
            return False, f"Source {index + 1} needs a non-empty source_id."
        if source_id in source_ids:
            return False, f"Duplicate source_id: {source_id}."
        if not isinstance(reference, str) or not reference.strip():
            return False, f"Source {source_id} needs a non-empty reference."
        source_ids.add(source_id)

    criteria = value.get("acceptance_criteria")
    if not isinstance(criteria, list) or not criteria:
        return False, "At least one acceptance criterion is required."
    criterion_ids: set[str] = set()
    for index, criterion in enumerate(criteria):
        if not isinstance(criterion, Mapping):
            return False, f"Acceptance criterion {index + 1} must be an object."
        criterion_id = criterion.get("criterion_id")
        description = criterion.get("description")
        if not isinstance(criterion_id, str) or not criterion_id.strip():
            return False, f"Acceptance criterion {index + 1} needs a non-empty criterion_id."
        if criterion_id in criterion_ids:
            return False, f"Duplicate criterion_id: {criterion_id}."
        if not isinstance(description, str) or not description.strip():
            return False, f"Acceptance criterion {criterion_id} needs a description."
        criterion_ids.add(criterion_id)

    return True, "DOCUMENT_REVIEW input is structurally valid."


def validate_document_review_result(task: Any, result: Any) -> tuple[bool, str]:
    input_valid, input_message = validate_document_review_input(task.input)
    if not input_valid:
        return False, f"Invalid DOCUMENT_REVIEW input: {input_message}"
    if not isinstance(result, Mapping):
        return False, "DOCUMENT_REVIEW result must be an object."
    if result.get("schema_version") != DOCUMENT_REVIEW_VERSION:
        return False, f"schema_version must be {DOCUMENT_REVIEW_VERSION}."
    if result.get("task_type") != task.task_type.value:
        return False, "Result task_type does not match the Task."
    if result.get("work_kind") != DOCUMENT_REVIEW:
        return False, "Result work_kind must be DOCUMENT_REVIEW."
    if result.get("outcome") != "COMPLETED":
        return False, "Result outcome must be COMPLETED."
    if not isinstance(result.get("summary"), str) or not result["summary"].strip():
        return False, "A non-empty result summary is required."

    source_ids = {source["source_id"] for source in task.input["sources"]}
    findings = result.get("findings")
    if not isinstance(findings, list):
        return False, "findings must be a list."
    finding_ids: set[str] = set()
    for index, finding in enumerate(findings):
        if not isinstance(finding, Mapping):
            return False, f"Finding {index + 1} must be an object."
        finding_id = finding.get("finding_id")
        category = finding.get("category")
        statement = finding.get("statement")
        refs = finding.get("source_refs")
        if not isinstance(finding_id, str) or not finding_id.strip():
            return False, f"Finding {index + 1} needs a non-empty finding_id."
        if finding_id in finding_ids:
            return False, f"Duplicate finding_id: {finding_id}."
        if not isinstance(category, str) or category not in DOCUMENT_REVIEW_CATEGORIES:
            return False, f"Finding {finding_id} has an unsupported category."
        if not isinstance(statement, str) or not statement.strip():
            return False, f"Finding {finding_id} needs a statement."
        if not isinstance(refs, list) or not refs:
            return False, f"Finding {finding_id} needs at least one source reference."
        if any(not isinstance(ref, str) or ref not in source_ids for ref in refs):
            return False, f"Finding {finding_id} references an unknown source."
        finding_ids.add(finding_id)

    criteria_ids = {criterion["criterion_id"] for criterion in task.input["acceptance_criteria"]}
    checks = result.get("acceptance_checks")
    if not isinstance(checks, list):
        return False, "acceptance_checks must be a list."
    checked_ids: set[str] = set()
    for index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            return False, f"Acceptance check {index + 1} must be an object."
        criterion_id = check.get("criterion_id")
        status = check.get("result")
        refs = check.get("evidence_refs")
        if not isinstance(criterion_id, str) or criterion_id not in criteria_ids:
            return False, f"Acceptance check {index + 1} references an unknown criterion."
        if criterion_id in checked_ids:
            return False, f"Duplicate acceptance check: {criterion_id}."
        if not isinstance(status, str) or status not in {"PASS", "FAIL"}:
            return False, f"Acceptance check {criterion_id} result must be PASS or FAIL."
        if not isinstance(refs, list) or not refs:
            return False, f"Acceptance check {criterion_id} needs evidence references."
        if any(not isinstance(ref, str) or ref not in source_ids for ref in refs):
            return False, f"Acceptance check {criterion_id} references an unknown source."
        if status != "PASS":
            return False, f"Acceptance criterion {criterion_id} failed."
        checked_ids.add(criterion_id)

    missing = criteria_ids - checked_ids
    if missing:
        return False, f"Missing acceptance checks: {', '.join(sorted(missing))}."
    return True, "DOCUMENT_REVIEW result is structurally valid and covers every acceptance criterion."
