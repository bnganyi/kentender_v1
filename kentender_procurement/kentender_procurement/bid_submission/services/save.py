# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`SaveBidTask` (BDS-CHG-001 v0.8 §4.4.5, §4.5, §4.6 and §7.2).

A save names one task and carries values by field handle. The server
re-resolves the bid's bound definition and refuses, with nothing saved:
an unknown handle, a handle of another task, a supplied fact, evidence (which
has its own commands), the Review and submit task's own fields, and a value
for a field its rule currently hides (`BDS_UNKNOWN_RESPONSE`). A value that
cannot be read as its control, or that its named validation refuses, comes
back as a field error (`BDS_FIELD_INVALID`), again with nothing saved.

A save that changes something advances the Draft version, records each
changed answer with its prior and new value, recalculates every task's
status and the bid's status, and writes one audit event, all together. A
save that changes nothing advances nothing."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import addendum, bid_context, clock, controls, readiness, records, tenders_gateway, validation
from kentender_procurement.bid_submission.services.errors import fail, field_errors

SECTION = "Bid Section Response"
CHANGE = "Bid Draft Change"
CLOSED = ("Submitted", "Withdrawn", "Closed without submission")


def _dump(value) -> str:
	return json.dumps(value, sort_keys=True, default=str)


def save_bid_task(*, bid_reference: str, task: str, values: dict | None, expected_record_version, organisation: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"bid_reference": cstr(bid_reference).strip(), "task": cstr(task).strip(), "values": dict(values or {}), "expected_record_version": expected_record_version, "organisation": cstr(organisation).strip()}
	return records.idempotent(idempotency_key, "SaveBidTask", payload, lambda: _save(actor=actor, **payload), actor=actor, organisation=payload["organisation"])


def require_open(ctx) -> None:
	"""Every Draft change: the bid is an open Draft, the Tender is open, and
	its bound release can still take bid work (§4.4.4: a Draft on a Withdrawn
	or failed release stays readable, not editable)."""
	if ctx.workspace.status in CLOSED:
		fail("BDS_ALREADY_SUBMITTED" if ctx.workspace.status == "Submitted" else "BDS_TENDER_NOT_OPEN")
	if tenders_gateway.availability(ctx.workspace.tender_reference, at=clock.now()) != "open":
		fail("BDS_TENDER_NOT_OPEN")
	from kentender_procurement.bid_submission.services import definition_runtime

	definition_runtime.require_release(ctx)


def _save(*, actor: str, bid_reference: str, task: str, values: dict, expected_record_version, organisation: str) -> dict[str, Any]:
	at = clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	authz.active_account(ctx.workspace.lead_organisation)  # a suspended Account cannot edit its Draft (BDS01-AC-010)
	require_open(ctx)
	records.check_version(ctx.workspace, expected_record_version)
	refreshed = addendum.refresh(ctx, actor=actor, at=at)
	if refreshed:
		return refreshed  # the bid moved to the current definition; review first
	if not ctx.model.task(task) or task == readiness.REVIEW_TASK:
		fail("BDS_UNKNOWN_RESPONSE")
	submitted = {}
	for handle, raw in values.items():
		field = ctx.model.by_handle(cstr(handle))
		if not field or field.task_key != task or not field.editable or field.kind == "evidence":
			fail("BDS_UNKNOWN_RESPONSE")
		submitted[field.key] = (field, raw)
	problems: dict[str, str] = {}
	canonical: dict[str, Any] = {}
	for key, (field, raw) in submitted.items():
		value, problem = controls.canonical(field.control_id, raw, field.validation_parameters)
		if problem:
			problems[field.handle] = problem
		else:
			canonical[key] = value
	before = dict(ctx.values)
	ctx.values = {**before, **canonical}
	for key, (field, _raw) in submitted.items():
		if key not in canonical:
			continue  # unreadable: already reported
		if canonical.get(key) is not None and not validation.rule_holds(field.visibility_rule, ctx.group_values(field)):
			fail("BDS_UNKNOWN_RESPONSE")
		if canonical.get(key) is not None:
			problem = validation.check(field.validation_id, field.validation_parameters, canonical[key])
			if problem:
				problems[field.handle] = problem
	if problems:
		return field_errors(problems)
	changed = {key: value for key, value in canonical.items() if before.get(key) != value}
	ws = ctx.workspace
	reviewed = [t for t in addendum.attention(ctx) if t != task]
	if not changed and reviewed == addendum.attention(ctx):
		return {"ok": True, "changed": False, "draft_version": int(ws.current_draft_version), "record_version": int(ws.record_version), "status": ws.status}
	version = int(ws.current_draft_version or 0) + 1
	with records.atomic("save-bid-task"):
		task_keys = {f.key for f in ctx.model.fields_of(task)}
		section_values = {k: v for k, v in ctx.values.items() if k in task_keys and v is not None}
		_write_section(ctx, task, section_values, version=version, actor=actor, at=at)
		for key, value in changed.items():
			records.insert(frappe.get_doc({
				"doctype": CHANGE, "bid_workspace": ws.name, "draft_version": version, "section_key": task, "response_key": key,
				"change_kind": "Cleared" if value is None else "Saved", "prior_value": _dump(before.get(key)), "new_value": _dump(value), "actor": actor, "changed_at": at,
			}))
		if task == "company":
			from kentender_procurement.bid_submission.services import security_matching

			security_matching.match_tender(ws.tender)  # the private physical-original match (OD-H)
		ctx.sections = _sections(ws.name)
		ws.attention_json = json.dumps(reviewed)
		status = refresh_derived(ctx)
		records.bump(ws, current_draft_version=version, last_saved_by=actor, last_saved_at=at, attention_json=json.dumps(reviewed), **_status_values(ws, status, at))
		records.emit("BidTaskSaved", tender=ws.tender, arrangement=ws.bidder_arrangement, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at, payload={"task": task, "draft_version": version, "changed": len(changed)})
	return {"ok": True, "changed": True, "draft_version": version, "record_version": int(ws.record_version), "status": status}


def _sections(workspace: str) -> dict[str, Any]:
	return {row.section_key: row for row in frappe.get_all(SECTION, filters={"bid_workspace": workspace}, fields=["name", "section_key", "values_json", "status", "blocker_count", "warning_count", "record_version"], limit_page_length=0)}


def _write_section(ctx, task: str, values: dict[str, Any], *, version: int, actor: str, at) -> None:
	existing = frappe.db.get_value(SECTION, {"bid_workspace": ctx.workspace.name, "section_key": task}, "name")
	if existing:
		doc = frappe.get_doc(SECTION, existing)
		records.bump(doc, values_json=_dump(values), draft_version=version, last_saved_by=actor, last_saved_at=at)
	else:
		records.insert(frappe.get_doc({
			"doctype": SECTION, "bid_workspace": ctx.workspace.name, "section_key": task, "unique_key": f"{ctx.workspace.name}::{task}", "draft_version": version,
			"values_json": _dump(values), "status": "In progress", "blocker_count": 0, "warning_count": 0, "last_saved_by": actor, "last_saved_at": at, "record_version": 0,
		}))


def _status_values(ws, status: str, at) -> dict[str, Any]:
	return {"status": status, "status_since": at} if ws.status != status else {}


def refresh_derived(ctx) -> str:
	"""Store each saved task's derived status and counts; return the bid's."""
	tasks = readiness.evaluate(ctx, attention=addendum.attention(ctx))
	for key, row in ctx.sections.items():
		state = tasks.get(key)
		if state and (row.status, int(row.blocker_count or 0), int(row.warning_count or 0)) != (state.status, state.must_fix, state.review_notes):
			records.save(frappe.get_doc(SECTION, row.name).update({"status": state.status, "blocker_count": state.must_fix, "warning_count": state.review_notes}))
	return readiness.bid_status(tasks)
