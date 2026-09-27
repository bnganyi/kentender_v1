# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Readiness of one bid against its exact bound definition (BDS-CHG-001 v0.8
§4.4.5, §4.6, §5.3 and §5.7 items 1–2).

Every field is shown or hidden, required or optional, by its named rules over
the same group's current values. A required field without a value, or a
value its named validation refuses, is **Must fix**. A bidder's own statement
that the offer does not comply is a **Review note**: it never blocks
submission, and the bid does not evaluate it. Hidden fields keep their saved
values in history but take no part in readiness. The Review and submit
task's own fields (the signatory and the final confirmation) are captured
when the signatory submits, so they are not Must fix before then.

Task status: Complete with no Must fix; In progress once something in the
task is saved; otherwise Not started. A task with nothing to answer (the
documents task without an effective addendum) is Complete. Review and submit
is Complete when no task has a Must fix (§5.3). The bid is Ready to submit
when every task is Complete, otherwise Draft."""

from __future__ import annotations

from dataclasses import dataclass, field as dataclass_field
from typing import Any

from kentender_procurement.bid_submission.services import validation
from kentender_procurement.bid_submission.services.bid_context import AT_SUBMISSION, BidContext
from kentender_procurement.bid_submission.services.definition_model import Field

MUST_FIX = "Must fix"
REVIEW_NOTE = "Review note"
REVIEW_TASK = "review"

_MISSING = {
	"confirmation": "Tick the box to confirm.",
	"evidence": "Add the required supporting evidence.",
	"single_choice": "Choose an answer.",
	"yes_no": "Choose Yes or No.",
	"multi_select": "Choose at least one option.",
	"ports": "Add each port type and how many.",
}
_SUPPLIED_MISSING = {
	"tender_contact_phone": "Add the Tender contact's telephone number.",
	"tender_contact_email": "Add the Tender contact's email address.",
}


@dataclass
class FieldState:
	field: Field
	visible: bool
	required: bool
	value: Any
	issue: dict[str, str] | None = None


@dataclass
class TaskState:
	key: str
	status: str
	must_fix: int = 0
	review_notes: int = 0
	fields: list[FieldState] = dataclass_field(default_factory=list)


def _blank(value) -> bool:
	return value is None or value == "" or value == []


REJECTED_FILE = "Replace the rejected file."


def field_state(ctx: BidContext, field: Field) -> FieldState:
	group = ctx.group_values(field)
	visible = validation.rule_holds(field.visibility_rule, group)
	required = visible and validation.rule_holds(field.required_rule, group)
	value = ctx.value(field)
	state = FieldState(field=field, visible=visible, required=required, value=value)
	if not visible or field.task_key == REVIEW_TASK:
		return state
	if field.supplied:
		if _blank(value) and required and field.supplied["source_id"] not in AT_SUBMISSION:
			state.issue = {"severity": MUST_FIX, "text": _SUPPLIED_MISSING.get(field.supplied["fact"], "This fact is missing from the supplier account.")}
		return state
	if _blank(value):
		if required:
			rejected = field.kind == "evidence" and any(e["scan_status"] == "Rejected" for e in ctx.evidence.get(field.key, []))
			state.issue = {"severity": MUST_FIX, "text": REJECTED_FILE if rejected else _MISSING.get(field.kind, "Answer this question.")}
		return state
	problem = validation.check(field.validation_id, field.validation_parameters, value)
	if problem:
		state.issue = {"severity": MUST_FIX, "text": problem}
	elif field.field_key == "compliance" and value == "Do not comply":
		state.issue = {"severity": REVIEW_NOTE, "text": "You state that the offer does not meet this requirement."}
	return state


def evaluate(ctx: BidContext, *, attention: list[str] | None = None) -> dict[str, TaskState]:
	"""`attention`: tasks an addendum changed that the bidder has not saved since."""
	tasks: dict[str, TaskState] = {}
	for task in ctx.model.tasks:
		states = [field_state(ctx, f) for f in ctx.model.fields_of(task.key)]
		state = TaskState(key=task.key, status="", fields=states)
		state.must_fix = sum(1 for s in states if s.issue and s.issue["severity"] == MUST_FIX)
		state.review_notes = sum(1 for s in states if s.issue and s.issue["severity"] == REVIEW_NOTE)
		tasks[task.key] = state
	blocking = sum(t.must_fix for key, t in tasks.items() if key != REVIEW_TASK)
	for key, state in tasks.items():
		if key == REVIEW_TASK:
			state.status = "Complete" if blocking == 0 else "Not started"
		elif key in (attention or []) or any(s.issue and s.issue["text"] == REJECTED_FILE for s in state.fields):
			# an addendum change, or a file the malware check rejected (§10.8 "Needs attention")
			state.status = "Needs attention"
		elif state.must_fix == 0:
			state.status = "Complete"
		elif key in ctx.sections and ctx.sections[key].values_json not in (None, "", "{}"):
			state.status = "In progress"
		elif any(ctx.evidence.get(s.field.key) for s in state.fields):
			state.status = "In progress"
		else:
			state.status = "Not started"
	return tasks


def bid_status(tasks: dict[str, TaskState]) -> str:
	if any(t.status == "Needs attention" for t in tasks.values()):
		return "Needs attention"
	return "Ready to submit" if all(t.status == "Complete" for t in tasks.values()) else "Draft"


def must_fix_total(tasks: dict[str, TaskState]) -> int:
	return sum(t.must_fix for key, t in tasks.items() if key != REVIEW_TASK)
