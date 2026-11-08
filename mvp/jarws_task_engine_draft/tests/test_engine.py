from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from jarws_task_engine.engine import (  # noqa: E402
    ApprovalRecord,
    ApprovalRoute,
    ApprovalStatus,
    Checker,
    ExecutionAccess,
    Executor,
    GLOBAL_MAX_ROUNDS,
    Orchestrator,
    Provenance,
    Task,
    TaskState,
    TaskType,
    TransientExecutionError,
    UnblockRole,
    Validator,
    load_approval_record,
    load_task,
    save_approval_record,
    save_task,
    unblock_task,
)
from jarws_task_engine.schemas import (  # noqa: E402
    validate_core_change_result,
    DOCUMENT_REVIEW,
    validate_document_review_result,
)


def valid_provenance() -> Provenance:
    return Provenance(
        source_references=("user-request:example",),
        initiator="human:tester",
        responsible="human:tester",
        creation_trace="test-fixture-001",
    )


def result_schemas() -> dict:
    return {
        TaskType.NORMAL_TASK: lambda _task, value: (
            isinstance(value, dict) and value.get("status") == "ok",
            "Expected an object with status='ok'.",
        ),
        TaskType.CORE_CHANGE: validate_core_change_result,
        (TaskType.NORMAL_TASK, DOCUMENT_REVIEW): validate_document_review_result,
    }


def orchestrator() -> Orchestrator:
    return Orchestrator(Validator(), Executor(), Checker(result_schemas()))


class TaskEngineTests(unittest.TestCase):
    def make_task(self, **kwargs) -> Task:
        return Task(
            id=kwargs.pop("id", "T-1"),
            goal=kwargs.pop("goal", "Produce a test result"),
            provenance=kwargs.pop("provenance", valid_provenance()),
            **kwargs,
        )

    def make_document_review_task(self, **kwargs) -> Task:
        input_data = {
            "work_kind": DOCUMENT_REVIEW,
            "request": "Compare the two source documents.",
            "sources": [
                {"source_id": "SRC-1", "reference": "source://one"},
                {"source_id": "SRC-2", "reference": "source://two"},
            ],
            "acceptance_criteria": [
                {"criterion_id": "AC-1", "description": "Cite relevant source material."},
                {"criterion_id": "AC-2", "description": "List disagreements and open questions."},
            ],
        }
        input_data.update(kwargs.pop("input", {}))
        return self.make_task(input=input_data, **kwargs)

    @staticmethod
    def valid_document_review_result() -> dict:
        return {
            "schema_version": "0.1",
            "task_type": TaskType.NORMAL_TASK.value,
            "work_kind": DOCUMENT_REVIEW,
            "outcome": "COMPLETED",
            "summary": "Compared both sources and recorded one difference.",
            "findings": [
                {
                    "finding_id": "F-1",
                    "category": "GAP",
                    "statement": "The second source does not define the status transition.",
                    "source_refs": ["SRC-1", "SRC-2"],
                }
            ],
            "acceptance_checks": [
                {"criterion_id": "AC-1", "result": "PASS", "evidence_refs": ["SRC-1"]},
                {"criterion_id": "AC-2", "result": "PASS", "evidence_refs": ["SRC-2"]},
            ],
        }

    def make_core_change_task(self, **kwargs) -> Task:
        input_data = {
            "change_scope": "non-production Task Engine draft",
            "impact_categories": ["GOVERNANCE"],
            "proposed_changes": [
                {
                    "change_id": "CH-1",
                    "target": "point4_submission_draft/jarws_task_engine/engine.py",
                    "action": "Add a schema validator",
                    "rationale": "Check the reviewed output against the agreed scope.",
                }
            ],
            "acceptance_criteria": [
                {"criterion_id": "AC-1", "description": "The result matches the proposed scope."}
            ],
        }
        input_data.update(kwargs.pop("input", {}))
        return self.make_task(task_type=TaskType.CORE_CHANGE, input=input_data, **kwargs)

    @staticmethod
    def valid_core_change_result() -> dict:
        return {
            "schema_version": "0.1",
            "task_type": TaskType.CORE_CHANGE.value,
            "outcome": "COMPLETED",
            "summary": "Applied the proposed schema validator in the isolated draft.",
            "change_items": [
                {
                    "change_id": "CH-1",
                    "target": "point4_submission_draft/jarws_task_engine/engine.py",
                    "action": "Add a schema validator",
                    "result": "APPLIED",
                    "evidence_refs": ["EV-1"],
                }
            ],
            "verification": [
                {"criterion_id": "AC-1", "result": "PASS", "evidence_refs": ["EV-1"]}
            ],
        }

    def complete_core_change(self, access: ExecutionAccess) -> dict:
        access.add_evidence("EV-1")
        return self.valid_core_change_result()

    def test_document_review_schema_accepts_complete_report(self):
        task = self.make_document_review_task()
        result = orchestrator().run(task, lambda _access: self.valid_document_review_result())
        self.assertEqual(result.state, TaskState.DONE)
        self.assertTrue(result.validation["result_check"]["passed"])

    def test_document_review_requires_valid_input_before_executor(self):
        task = self.make_document_review_task(input={"sources": []})
        called = False

        def operation(_access):
            nonlocal called
            called = True
            return self.valid_document_review_result()

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.BLOCKED)
        self.assertFalse(called)
        self.assertEqual(result.attempts, 0)

    def test_document_review_rejects_unknown_source_reference(self):
        task = self.make_document_review_task(requested_rounds=1)
        invalid = self.valid_document_review_result()
        invalid["findings"][0]["source_refs"] = ["SRC-UNKNOWN"]
        result = orchestrator().run(task, lambda _access: invalid)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("unknown source", result.validation["result_check"]["message"])

    def test_document_review_requires_exact_acceptance_criteria_coverage(self):
        task = self.make_document_review_task(requested_rounds=1)
        invalid = self.valid_document_review_result()
        invalid["acceptance_checks"].pop()
        result = orchestrator().run(task, lambda _access: invalid)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("Missing acceptance checks", result.validation["result_check"]["message"])

    def test_document_review_failed_acceptance_check_is_rejected(self):
        task = self.make_document_review_task(requested_rounds=1)
        invalid = self.valid_document_review_result()
        invalid["acceptance_checks"][0]["result"] = "FAIL"
        result = orchestrator().run(task, lambda _access: invalid)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("criterion AC-1 failed", result.validation["result_check"]["message"])

    def test_document_review_requires_findings_to_have_source_evidence(self):
        task = self.make_document_review_task(requested_rounds=1)
        invalid = self.valid_document_review_result()
        invalid["findings"][0]["source_refs"] = []
        result = orchestrator().run(task, lambda _access: invalid)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("at least one source reference", result.validation["result_check"]["message"])

    def test_core_change_input_requires_scope_categories_changes_and_criteria(self):
        task = self.make_core_change_task(input={"change_scope": ""})
        called = False

        def operation(_access):
            nonlocal called
            called = True
            return self.valid_core_change_result()

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.BLOCKED)
        self.assertIn("change_scope", result.blocker)
        self.assertFalse(called)

    def test_core_change_result_must_match_proposed_scope(self):
        task = self.make_core_change_task(requested_rounds=1, approval_record_id="T-1")
        approval = ApprovalRecord(
            task_id=task.id,
            route=ApprovalRoute.PRE_APPROVAL,
            status=ApprovalStatus.APPROVED_PRE,
            scope="non-production Task Engine draft",
            rationale="Approved for isolated prototype work.",
        )
        result_value = self.valid_core_change_result()
        result_value["change_items"][0]["action"] = "Modify production authentication"
        result = orchestrator().run(task, lambda access: (access.add_evidence("EV-1"), result_value)[1], approval)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("exceeds or differs from the proposed scope", result.validation["result_check"]["message"])

    def test_core_change_result_requires_execution_evidence(self):
        task = self.make_core_change_task(requested_rounds=1, approval_record_id="T-1")
        approval = ApprovalRecord(
            task_id=task.id,
            route=ApprovalRoute.PRE_APPROVAL,
            status=ApprovalStatus.APPROVED_PRE,
            scope="non-production Task Engine draft",
            rationale="Approved for isolated prototype work.",
        )
        result = orchestrator().run(task, lambda _access: self.valid_core_change_result(), approval)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertIn("missing execution evidence", result.validation["result_check"]["message"])

    def test_normal_task_finishes_only_after_checker_pass(self):
        task = self.make_task()
        result = orchestrator().run(task, lambda access: {"status": "ok"})
        self.assertEqual(result.state, TaskState.DONE)
        self.assertEqual(result.attempts, 1)
        self.assertTrue(result.validation["result_check"]["passed"])

    def test_executor_can_write_result_and_evidence_but_not_state_or_goal(self):
        task = self.make_task()
        access = ExecutionAccess(task)
        access.result = {"status": "ok"}
        access.add_evidence("output artifact: result-1")
        with self.assertRaises(AttributeError):
            access.state = TaskState.DONE
        with self.assertRaises(AttributeError):
            access.goal = "replace the goal"
        self.assertEqual(task.state, TaskState.WAITING)
        self.assertEqual(task.result, {"status": "ok"})
        self.assertEqual(task.evidence, ["output artifact: result-1"])

    def test_executor_input_is_a_copy(self):
        task = self.make_task(input={"nested": {"value": 1}})
        access = ExecutionAccess(task)
        access.input["nested"]["value"] = 9
        self.assertEqual(task.input["nested"]["value"], 1)

    def test_missing_provenance_blocks_without_running_executor(self):
        task = self.make_task(provenance=None)
        called = False

        def operation(_access):
            nonlocal called
            called = True
            return {"status": "ok"}

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.BLOCKED)
        self.assertIn("provenance", result.blocker)
        self.assertFalse(called)

    def test_invalid_provenance_blocks_until_human_unblocks_and_repairs(self):
        bad = Provenance((), "human:x", "human:x", "trace")
        task = self.make_task(provenance=bad)
        engine = orchestrator()
        self.assertEqual(engine.run(task, lambda _access: {"status": "ok"}).state, TaskState.BLOCKED)
        task.provenance = valid_provenance()
        unblock_task(task, role=UnblockRole.DIRECTOR, actor="director-1", reason="Added source reference")
        self.assertEqual(task.state, TaskState.WAITING)
        self.assertEqual(engine.run(task, lambda _access: {"status": "ok"}).state, TaskState.DONE)

    def test_critical_change_requires_separate_approval_record(self):
        task = self.make_core_change_task()
        result = orchestrator().run(task, lambda _access: {"change_summary": "update"})
        self.assertEqual(result.state, TaskState.BLOCKED)
        self.assertIn("Approval record", result.blocker)

    def test_pre_approval_is_required_before_executor_runs(self):
        task = self.make_core_change_task(
            approval_record_id="T-1",
            critical_categories=["GOVERNANCE"],
        )
        approval = ApprovalRecord(
            task_id=task.id,
            route=ApprovalRoute.PRE_APPROVAL,
            status=ApprovalStatus.PENDING_PRE_APPROVAL,
            scope="governance file",
            rationale="critical change",
        )
        called = False

        def operation(_access):
            nonlocal called
            called = True
            return self.complete_core_change(_access)

        engine = orchestrator()
        self.assertEqual(engine.run(task, operation, approval).state, TaskState.BLOCKED)
        self.assertFalse(called)
        unblock_task(task, role=UnblockRole.FOUNDER, actor="founder-1", reason="Approval recorded")
        approval.approve_pre(approver="director-1", rationale="Reviewed and approved", evidence=["approval-note-1"])
        self.assertEqual(engine.run(task, operation, approval).state, TaskState.DONE)
        self.assertTrue(approval.active)

    def test_posthoc_change_stays_inactive_until_final_approval(self):
        task = self.make_core_change_task(
            approval_record_id="T-1",
            critical_categories=["SECURITY"],
        )
        approval = ApprovalRecord(
            task_id=task.id,
            route=ApprovalRoute.POSTHOC_EXCEPTION,
            status=ApprovalStatus.PENDING_FINAL_APPROVAL,
            scope="security change",
            rationale="Viable isolated draft; final review requested after work",
        )
        result = orchestrator().run(task, lambda access: self.complete_core_change(access), approval)
        self.assertEqual(result.state, TaskState.DONE)
        self.assertEqual(approval.status, ApprovalStatus.PENDING_FINAL_APPROVAL)
        self.assertFalse(approval.active)
        approval.decide(approver="director-1", accepted=True, rationale="Final review approved", evidence=["review-1"])
        self.assertEqual(approval.status, ApprovalStatus.APPROVED_FINAL)
        self.assertTrue(approval.active)

    def test_rejected_posthoc_change_is_archived_and_inactive(self):
        approval = ApprovalRecord(
            task_id="T-1",
            route=ApprovalRoute.POSTHOC_EXCEPTION,
            status=ApprovalStatus.PENDING_FINAL_APPROVAL,
            scope="test change",
            rationale="post-completion exception",
        )
        approval.decide(approver="director-1", accepted=False, rationale="Not accepted", evidence=["checker-output"])
        self.assertEqual(approval.status, ApprovalStatus.REJECTED)
        self.assertFalse(approval.active)
        self.assertTrue(approval.archived)
        self.assertIn("checker-output", approval.evidence)

    def test_checker_repair_rounds_can_succeed_before_limit(self):
        task = self.make_task(requested_rounds=5)
        calls = 0

        def operation(_access):
            nonlocal calls
            calls += 1
            return {"status": "bad" if calls < 5 else "ok"}

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.DONE)
        self.assertEqual(result.attempts, 5)
        self.assertEqual(calls, 5)

    def test_checker_failure_at_limit_sets_error_and_preserves_evidence(self):
        task = self.make_task(requested_rounds=5)
        result = orchestrator().run(task, lambda access: (access.add_evidence("output retained"), {"status": "bad"})[1])
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertEqual(result.attempts, 5)
        self.assertEqual(len(result.evidence), 10)
        self.assertTrue(any("rejected" in item for item in result.blocker_history))

    def test_per_task_round_limit_can_be_lowered(self):
        task = self.make_task(requested_rounds=2)
        result = orchestrator().run(task, lambda _access: {"status": "bad"})
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertEqual(result.attempts, 2)

    def test_global_round_limit_caps_request_at_five(self):
        task = self.make_task(requested_rounds=99)
        result = orchestrator().run(task, lambda _access: {"status": "bad"})
        self.assertEqual(task.effective_round_limit, GLOBAL_MAX_ROUNDS)
        self.assertEqual(result.attempts, GLOBAL_MAX_ROUNDS)
        self.assertEqual(result.state, TaskState.ERROR)

    def test_allowlisted_transient_error_retries_and_every_executor_start_counts(self):
        task = self.make_task(requested_rounds=5)
        calls = 0

        def operation(_access):
            nonlocal calls
            calls += 1
            if calls < 3:
                raise TransientExecutionError("temporary unavailable")
            return {"status": "ok"}

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.DONE)
        self.assertEqual(result.attempts, 3)
        self.assertEqual(calls, 3)

    def test_non_allowlisted_error_does_not_retry(self):
        task = self.make_task(requested_rounds=5)
        calls = 0

        def operation(_access):
            nonlocal calls
            calls += 1
            raise ValueError("permanent failure")

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertEqual(result.attempts, 1)
        self.assertEqual(calls, 1)

    def test_retry_limit_exhaustion_preserves_execution_evidence(self):
        task = self.make_task(requested_rounds=2)

        def operation(access):
            access.add_evidence(f"round-{task.attempts}")
            raise TransientExecutionError("still unavailable")

        result = orchestrator().run(task, operation)
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertEqual(result.attempts, 2)
        self.assertEqual(len(result.evidence), 4)
        self.assertTrue(any("round-1" in item for item in result.evidence))
        self.assertTrue(any("Transient attempt 2" in item for item in result.evidence))

    def test_interruption_blocks_and_authorized_release_returns_to_waiting(self):
        task = self.make_task()

        def interrupted(_access):
            raise KeyboardInterrupt

        result = orchestrator().run(task, interrupted)
        self.assertEqual(result.state, TaskState.BLOCKED)
        self.assertIn("interrupted", result.blocker.lower())
        with self.assertRaises(PermissionError):
            unblock_task(task, role="DEVELOPER", actor="dev-1", reason="try again")
        unblock_task(task, role=UnblockRole.DIRECTOR_DELEGATE, actor="delegate-1", reason="safe to retry")
        self.assertEqual(task.state, TaskState.WAITING)
        self.assertIsNone(task.blocker)
        self.assertTrue(any("Unblocked by" in item for item in task.blocker_history))

    def test_task_and_approval_json_round_trip(self):
        task = self.make_core_change_task(
            id="T-persist",
            state=TaskState.DONE,
            approval_record_id="T-persist",
            critical_categories=["GOVERNANCE"],
            result=self.valid_core_change_result(),
            evidence=["checker pass"],
            attempts=3,
        )
        approval = ApprovalRecord(
            task_id=task.id,
            route=ApprovalRoute.PRE_APPROVAL,
            status=ApprovalStatus.APPROVED_PRE,
            scope="governance",
            rationale="approved before work",
            evidence=["approval-note"],
            decision_maker="director-1",
            decided_at="2026-11-08T12:00:00+00:00",
        )
        with tempfile.TemporaryDirectory() as directory:
            task_path = Path(directory) / "task.json"
            approval_path = Path(directory) / "approval.json"
            save_task(task, task_path)
            save_approval_record(approval, approval_path)
            restored_task = load_task(task_path)
            restored_approval = load_approval_record(approval_path)
        self.assertEqual(restored_task.state, TaskState.DONE)
        self.assertEqual(restored_task.provenance, task.provenance)
        self.assertEqual(restored_task.result, task.result)
        self.assertEqual(restored_task.attempts, 3)
        self.assertEqual(restored_approval.status, ApprovalStatus.APPROVED_PRE)
        self.assertEqual(restored_approval.evidence, ["approval-note"])

    def test_checker_exception_sets_error_instead_of_leaving_running(self):
        class BrokenChecker(Checker):
            def check(self, _task, _result):
                raise RuntimeError("checker crashed")

        engine = Orchestrator(Validator(), Executor(), BrokenChecker(result_schemas()))
        task = self.make_task()
        result = engine.run(task, lambda _access: {"status": "ok"})
        self.assertEqual(result.state, TaskState.ERROR)
        self.assertEqual(result.blocker, "Checker error: checker crashed")


if __name__ == "__main__":
    unittest.main(verbosity=2)
