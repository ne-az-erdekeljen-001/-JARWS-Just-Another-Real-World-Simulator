"""Experimental Task Engine aligned with the accepted JARWS working framework.

This is an isolated submission draft, not a production security boundary.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from .schemas import (
    DOCUMENT_REVIEW,
    validate_core_change_input,
    validate_document_review_input,
)


GLOBAL_MAX_ROUNDS = 5


class TaskState(str, Enum):
    WAITING = "WAITING"
    RUNNING = "RUNNING"
    BLOCKED = "BLOCKED"
    DONE = "DONE"
    ERROR = "ERROR"


class TaskType(str, Enum):
    NORMAL_TASK = "NORMAL_TASK"
    CORE_CHANGE = "CORE_CHANGE"


class ApprovalRoute(str, Enum):
    NONE = "NONE"
    PRE_APPROVAL = "PRE_APPROVAL"
    POSTHOC_EXCEPTION = "POSTHOC_EXCEPTION"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "NOT_REQUIRED"
    PENDING_PRE_APPROVAL = "PENDING_PRE_APPROVAL"
    APPROVED_PRE = "APPROVED_PRE"
    PENDING_FINAL_APPROVAL = "PENDING_FINAL_APPROVAL"
    APPROVED_FINAL = "APPROVED_FINAL"
    REJECTED = "REJECTED"


class UnblockRole(str, Enum):
    FOUNDER = "FOUNDER"
    DIRECTOR = "DIRECTOR"
    DIRECTOR_DELEGATE = "DIRECTOR_DELEGATE"


@dataclass(frozen=True)
class Provenance:
    source_references: tuple[str, ...]
    initiator: str
    responsible: str
    creation_trace: str

    def validate(self) -> tuple[bool, str]:
        if not self.source_references or any(not item.strip() for item in self.source_references):
            return False, "At least one non-empty source reference is required."
        if not self.initiator.strip():
            return False, "Initiator is required."
        if not self.responsible.strip():
            return False, "Responsible party is required."
        if not self.creation_trace.strip():
            return False, "Creation trace is required."
        return True, "Provenance is complete."


@dataclass
class ApprovalRecord:
    task_id: str
    route: ApprovalRoute
    status: ApprovalStatus
    scope: str
    rationale: str
    evidence: list[str] = field(default_factory=list)
    decision_maker: str | None = None
    decided_at: str | None = None
    active: bool = False
    archived: bool = False

    def approve_pre(self, *, approver: str, rationale: str, evidence: list[str] | None = None) -> None:
        if self.route is not ApprovalRoute.PRE_APPROVAL:
            raise ValueError("Pre-approval can only be recorded on the pre-approval route.")
        if not approver.strip() or not rationale.strip():
            raise ValueError("A named human decision-maker and rationale are required.")
        self.status = ApprovalStatus.APPROVED_PRE
        self.decision_maker = approver
        self.decided_at = datetime.now(timezone.utc).isoformat()
        self.rationale = rationale
        if evidence:
            self.evidence.extend(evidence)

    def decide(self, *, approver: str, accepted: bool, rationale: str, evidence: list[str] | None = None) -> None:
        if not approver.strip():
            raise ValueError("A named human decision-maker is required.")
        if not rationale.strip():
            raise ValueError("The approval decision must include a rationale.")
        self.decision_maker = approver
        self.decided_at = datetime.now(timezone.utc).isoformat()
        self.rationale = rationale
        if evidence:
            self.evidence.extend(evidence)
        if accepted:
            self.status = ApprovalStatus.APPROVED_FINAL
            self.active = True
            self.archived = False
        else:
            self.status = ApprovalStatus.REJECTED
            self.active = False
            self.archived = True


@dataclass
class Task:
    id: str
    goal: str
    task_type: TaskType = TaskType.NORMAL_TASK
    state: TaskState = TaskState.WAITING
    input: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    provenance: Provenance | None = None
    critical_categories: list[str] = field(default_factory=list)
    approval_record_id: str | None = None
    result: Any = None
    evidence: list[str] = field(default_factory=list)
    attempts: int = 0
    requested_rounds: int = GLOBAL_MAX_ROUNDS
    blocker: str | None = None
    blocker_history: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)

    @property
    def effective_round_limit(self) -> int:
        if not isinstance(self.requested_rounds, int) or isinstance(self.requested_rounds, bool):
            raise ValueError("requested_rounds must be an integer.")
        if self.requested_rounds < 1:
            raise ValueError("requested_rounds must be at least 1.")
        return min(self.requested_rounds, GLOBAL_MAX_ROUNDS)

    @property
    def is_critical(self) -> bool:
        return self.task_type is TaskType.CORE_CHANGE or bool(self.critical_categories)

    def block(self, reason: str) -> None:
        self.state = TaskState.BLOCKED
        self.blocker = reason
        self.blocker_history.append(reason)

    def fail(self, reason: str) -> None:
        self.state = TaskState.ERROR
        self.blocker = reason
        self.blocker_history.append(reason)


class ExecutionAccess:
    """Executor API: read-only task context plus writable result and evidence."""

    __slots__ = ("_task",)

    def __init__(self, task: Task) -> None:
        self._task = task

    @property
    def id(self) -> str:
        return self._task.id

    @property
    def goal(self) -> str:
        return self._task.goal

    @property
    def task_type(self) -> TaskType:
        return self._task.task_type

    @property
    def input(self) -> Mapping[str, Any]:
        return deepcopy(self._task.input)

    @property
    def constraints(self) -> tuple[str, ...]:
        return tuple(self._task.constraints)

    @property
    def result(self) -> Any:
        return self._task.result

    @result.setter
    def result(self, value: Any) -> None:
        self._task.result = value

    @property
    def evidence(self) -> tuple[str, ...]:
        return tuple(self._task.evidence)

    def add_evidence(self, item: str) -> None:
        if not item.strip():
            raise ValueError("Evidence entries cannot be empty.")
        self._task.evidence.append(item)


class Validator:
    """Pre-execution validation; it does not approve or execute a change."""

    def validate(self, task: Task, approval: ApprovalRecord | None) -> tuple[bool, str]:
        if not task.goal.strip():
            return False, "Task goal is empty."
        if task.provenance is None:
            return False, "Required provenance is missing."
        provenance_valid, provenance_message = task.provenance.validate()
        if not provenance_valid:
            return False, provenance_message
        if not isinstance(task.input, dict):
            return False, "Task input must be an object."
        work_kind = task.input.get("work_kind")
        if task.task_type is TaskType.CORE_CHANGE:
            input_valid, input_message = validate_core_change_input(task.input)
            if not input_valid:
                return False, input_message
        elif work_kind is not None:
            if work_kind != DOCUMENT_REVIEW:
                return False, f"No input schema is configured for {task.task_type.value}/{work_kind}."
            input_valid, input_message = validate_document_review_input(task.input)
            if not input_valid:
                return False, input_message
        try:
            task.effective_round_limit
        except ValueError as exc:
            return False, str(exc)
        if task.is_critical:
            if approval is None or approval.task_id != task.id:
                return False, "A separate Approval record is required for a critical change."
            if task.approval_record_id and task.approval_record_id != approval.task_id:
                return False, "Task approval record reference does not match."
            if approval.route is ApprovalRoute.NONE:
                return False, "A critical change needs an approval route."
            if approval.route is ApprovalRoute.PRE_APPROVAL and approval.status is not ApprovalStatus.APPROVED_PRE:
                return False, "Pre-approval is required before execution."
            if approval.route is ApprovalRoute.POSTHOC_EXCEPTION:
                if not approval.rationale.strip():
                    return False, "The post-completion exception needs a viability rationale."
                if approval.status not in (ApprovalStatus.PENDING_FINAL_APPROVAL, ApprovalStatus.APPROVED_FINAL):
                    return False, "The post-completion approval route is not in a valid state."
        return True, "Pre-validation passed."


class TransientExecutionError(RuntimeError):
    """Explicitly allow-listed transient failure; retry only if operation is safe."""


ResultValidator = Callable[[Task, Any], tuple[bool, str]]


class Checker:
    """Non-canonical post-check helper; validates task-specific result contracts."""

    def __init__(self, schemas: Mapping[TaskType | tuple[TaskType, str], ResultValidator]) -> None:
        self._schemas = dict(schemas)

    def check(self, task: Task, result: Any) -> tuple[bool, str]:
        work_kind = task.input.get("work_kind") if isinstance(task.input, Mapping) else None
        validator = self._schemas.get((task.task_type, work_kind)) if work_kind is not None else None
        if validator is None:
            validator = self._schemas.get(task.task_type)
        if validator is None:
            return False, f"No result schema is configured for {task.task_type.value}/{work_kind or 'DEFAULT'}."
        try:
            json.dumps(result, ensure_ascii=False, allow_nan=False)
        except (TypeError, ValueError) as exc:
            return False, f"Result is not JSON-compatible: {exc}"
        return validator(task, result)


class Executor:
    """Runs work through the limited Task access API."""

    def execute(self, access: ExecutionAccess, operation: Callable[[ExecutionAccess], Any]) -> Any:
        return operation(access)


class Orchestrator:
    """Coordinates roles and owns Task state transitions."""

    def __init__(self, validator: Validator, executor: Executor, checker: Checker) -> None:
        self.validator = validator
        self.executor = executor
        self.checker = checker

    def run(
        self,
        task: Task,
        operation: Callable[[ExecutionAccess], Any],
        approval: ApprovalRecord | None = None,
    ) -> Task:
        if task.state is not TaskState.WAITING:
            return task

        valid, message = self.validator.validate(task, approval)
        task.validation["pre_validation"] = {"passed": valid, "message": message}
        if not valid:
            task.block(message)
            return task

        approval_pending_final = bool(
            task.is_critical
            and approval is not None
            and approval.route is ApprovalRoute.POSTHOC_EXCEPTION
            and approval.status is ApprovalStatus.PENDING_FINAL_APPROVAL
        )

        task.state = TaskState.RUNNING
        limit = task.effective_round_limit
        while task.attempts < limit:
            task.attempts += 1  # Every Executor start counts, including a pre-Checker failure.
            access = ExecutionAccess(task)
            try:
                returned = self.executor.execute(access, operation)
                if returned is not None:
                    access.result = returned
            except KeyboardInterrupt:
                task.block("Execution interrupted by operator.")
                return task
            except TransientExecutionError as exc:
                task.evidence.append(f"Transient attempt {task.attempts}: {exc}")
                if task.attempts < limit:
                    continue
                task.fail(f"Execution retry limit reached: {exc}")
                return task
            except Exception as exc:
                task.fail(f"Non-retryable execution error: {exc}")
                return task

            try:
                checked, check_message = self.checker.check(task, task.result)
            except Exception as exc:
                task.fail(f"Checker error: {exc}")
                return task
            task.validation["result_check"] = {
                "passed": checked,
                "message": check_message,
                "round": task.attempts,
            }
            task.evidence.append(f"Checker round {task.attempts}: {check_message}")
            if checked:
                task.state = TaskState.DONE
                task.blocker = None
                if task.is_critical and approval is not None:
                    if approval.route is ApprovalRoute.POSTHOC_EXCEPTION and approval_pending_final:
                        approval.status = ApprovalStatus.PENDING_FINAL_APPROVAL
                        approval.active = False
                    else:
                        approval.active = True
                return task
            if task.attempts >= limit:
                task.fail("Checker rejected the result after the allowed execution rounds.")
                return task

        task.fail("Execution round limit reached without an accepted result.")
        return task


def unblock_task(task: Task, *, role: UnblockRole, actor: str, reason: str) -> Task:
    if role not in {UnblockRole.FOUNDER, UnblockRole.DIRECTOR, UnblockRole.DIRECTOR_DELEGATE}:
        raise PermissionError("Only Founder, Director, or a Director delegate may unblock a Task.")
    if not actor.strip() or not reason.strip():
        raise ValueError("Unblock actor and reason are required.")
    if task.state is not TaskState.BLOCKED:
        raise ValueError("Only a BLOCKED Task can be unblocked.")
    previous_blocker = task.blocker or "Unspecified blocker."
    task.blocker_history.append(f"Unblocked by {actor}: {reason}; previous blocker: {previous_blocker}")
    task.blocker = None
    task.state = TaskState.WAITING
    return task


def _json_default(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        result = asdict(value)
        return result
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable.")


def save_task(task: Task, path: str | Path) -> None:
    payload = asdict(task)
    payload["task_type"] = task.task_type.value
    payload["state"] = task.state.value
    if task.provenance is not None:
        payload["provenance"]["source_references"] = list(task.provenance.source_references)
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default), encoding="utf-8")


def load_task(path: str | Path) -> Task:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload["task_type"] = TaskType(payload["task_type"])
    payload["state"] = TaskState(payload["state"])
    if payload.get("provenance") is not None:
        provenance = payload["provenance"]
        provenance["source_references"] = tuple(provenance["source_references"])
        payload["provenance"] = Provenance(**provenance)
    return Task(**payload)


def save_approval_record(record: ApprovalRecord, path: str | Path) -> None:
    payload = asdict(record)
    payload["route"] = record.route.value
    payload["status"] = record.status.value
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_approval_record(path: str | Path) -> ApprovalRecord:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    payload["route"] = ApprovalRoute(payload["route"])
    payload["status"] = ApprovalStatus(payload["status"])
    return ApprovalRecord(**payload)
