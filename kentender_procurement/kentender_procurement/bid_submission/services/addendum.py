# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`RefreshBidForAddendum` (BDS-CHG-001 v0.8 §4.4.6, §5.1 "Refresh bid", §5.4
items 3–5 and §7.2; plan D10).

When an addendum makes a later Published Bid Definition effective, a Draft
still bound to the earlier one needs attention. Reads say so without
changing anything. The first mutation of the bid (a save, a file, the
Tender contact) refreshes it first and asks the bidder to review before
doing anything else:

- the Draft binds to the current definition (its digest and release
  verified), as a new Draft version;
- each saved answer and file moves only by the stored identity map Tenders
  froze for the addendum: an `unchanged` answer, or a `converted` one whose
  released conversion copies it, carries forward to its successor identity;
  a `fresh_response_required` or `removed` answer is cleared and kept in
  the Draft's history; a `new` response starts unanswered;
- every task with a changed, new or removed response is marked for review
  until the bidder saves it (the acknowledgement of each effective addendum
  is a new response in the documents task).

Nothing is matched by label, position or text."""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.bid_submission.services import definition_runtime, records, tenders_gateway
from kentender_procurement.bid_submission.services.definition_model import DefinitionModel, task_key
from kentender_procurement.bid_submission.services.errors import MESSAGES

REVIEW_REQUIRED = "BDS_ADDENDUM_REVIEW_REQUIRED"


def pending(ctx) -> dict[str, Any] | None:
	"""The effective definition a Draft has not moved to yet, if any."""
	current = tenders_gateway.current_definition(ctx.workspace.tender)
	if current and int(current["definition_version"]) > int(ctx.workspace.definition_version or 0):
		return current
	return None


def attention(ctx) -> list[str]:
	return list(json.loads(ctx.workspace.attention_json or "[]"))


def _remap(key: str, by_prior: dict[str, dict[str, Any]]) -> tuple[str | None, dict[str, Any] | None]:
	response_id, _sep, member = key.partition("#")
	row = by_prior.get(response_id)
	if not row or not row["copy_prior_answer"] or not row["successor_response_id"]:
		return None, row
	return row["successor_response_id"] + (f"#{member}" if member else ""), row


def refresh(ctx, *, actor: str, at) -> dict[str, Any] | None:
	"""Move the Draft to the current definition; None when it is current."""
	current = pending(ctx)
	if not current:
		return None
	definition_runtime.check(current["definition"], digest=current["definition_digest"])
	ws = ctx.workspace
	mapping = tenders_gateway.map_addendum(ws.tender, from_version=int(ws.definition_version), to_version=int(current["definition_version"]))
	values = {k: v for k, v in ctx.values.items() if v is not None}
	evidence_rows = frappe.get_all("Bid Evidence", filters={"bid_workspace": ws.name, "status": "Current"}, fields=["name", "evidence_requirement"], limit_page_length=0)
	evidence_keys = {row.name: row.evidence_requirement for row in evidence_rows}
	affected: set[str] = set()
	history: list[tuple[str, str, Any, Any]] = []  # (kind, key, prior, new)
	for step in mapping["steps"]:
		by_prior = {c["prior_response_id"]: c for c in step["classifications"] if c["prior_response_id"]}
		for c in step["classifications"]:
			if c["classification"] != "unchanged" and task_key(c["affected_task_id"]) != "review":
				affected.add(task_key(c["affected_task_id"]))  # the review task's fields are captured at submission
		moved: dict[str, Any] = {}
		for key, value in values.items():
			new_key, row = _remap(key, by_prior)
			if new_key:
				moved[new_key] = value
				if new_key != key:
					history.append(("Carried forward", new_key, value, value))
			else:
				kind = "Removed" if row and row["classification"] == "removed" else "Fresh response required"
				history.append((kind, key, value, None))
		values = moved
		for name, key in list(evidence_keys.items()):
			new_key, _row = _remap(key, by_prior) if key else (None, None)
			evidence_keys[name] = new_key
	from kentender_procurement.bid_submission.services.bid_context import entities_of

	model = DefinitionModel(current["definition"], members=[m.organisation_id for m in ctx.arrangement.members], entities=entities_of(ctx.arrangement))
	version = int(ws.current_draft_version or 0) + 1
	with records.atomic("refresh-bid-for-addendum"):
		for task in model.tasks:
			keys = {f.key for f in model.fields_of(task.key)}
			section = {k: v for k, v in values.items() if k in keys}
			name = frappe.db.get_value("Bid Section Response", {"bid_workspace": ws.name, "section_key": task.key}, "name")
			if name:
				records.bump(frappe.get_doc("Bid Section Response", name), values_json=json.dumps(section, sort_keys=True, default=str), draft_version=version)
		for name, key in evidence_keys.items():
			doc = frappe.get_doc("Bid Evidence", name)
			if key:
				records.save(doc.update({"evidence_requirement": key}))
			else:
				records.save(doc.update({"status": "Removed", "removed_by": actor, "removed_at": at}))
		for kind, key, prior, new in history:
			records.insert(frappe.get_doc({
				"doctype": "Bid Draft Change", "bid_workspace": ws.name, "draft_version": version, "section_key": "", "response_key": key, "change_kind": kind,
				"prior_value": json.dumps(prior, sort_keys=True, default=str), "new_value": json.dumps(new, sort_keys=True, default=str), "actor": actor, "changed_at": at,
			}))
		tasks = sorted(affected, key=lambda k: [t.key for t in model.tasks].index(k) if model.task(k) else 99)
		records.bump(
			ws, bid_definition_id=current["bid_definition_id"], definition_version=int(current["definition_version"]), definition_digest=current["definition_digest"],
			current_draft_version=version, attention_json=json.dumps(tasks), status="Needs attention", status_since=at, last_saved_by=actor, last_saved_at=at,
		)
		records.emit(
			"BidRefreshedForAddendum", tender=ws.tender, arrangement=ws.bidder_arrangement, workspace=ws.name, organisation=ws.lead_organisation, actor=actor, at=at,
			payload={"definition_version": int(current["definition_version"]), "draft_version": version, "tasks": tasks, "addenda": [s["addendum_reference"] for s in mapping["steps"]]},
		)
	return {"ok": False, "code": REVIEW_REQUIRED, "message": MESSAGES[REVIEW_REQUIRED], "refreshed": True, "tasks": tasks, "draft_version": version, "record_version": int(ws.record_version)}
