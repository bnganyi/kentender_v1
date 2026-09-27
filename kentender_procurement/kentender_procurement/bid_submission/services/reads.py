# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bid Submission reads (BDS-CHG-001 v0.8 §7.1). Reads create nothing:
no organisation, workspace, acknowledgement, audit or business event.

`get_available_tenders` — BDS-DES-01: the public list of published Tenders
over the Tenders projection, filtered by title/reference search, method,
reservation and closing state at the trusted instant. It carries only what
the list shows (title, reference, Procuring Entity, method, reservation,
submission deadline and the Tender's public address) — no account status,
internal value, schema family or document count (§10.2)."""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr

from kentender_procurement.bid_submission.services import clock, labels, tenders_gateway

CLOSING = (("open", "Open Tenders"), ("closed", "Closed or cancelled"), ("all", "All Tenders"))
EMPTY_TEXT = "No Tenders match these filters."


def _closing_matches(closing: str, availability: str) -> bool:
	if closing == "all":
		return True
	if closing == "closed":
		return availability in ("closed", "cancelled")
	return availability == "open"


def _options(label: str, values: set[str]) -> list[dict[str, str]]:
	return [{"value": "", "label": label}] + [{"value": v, "label": v} for v in sorted(v for v in values if v)]


def get_available_tenders(*, search: str = "", method: str = "", reservation: str = "", closing: str = "open") -> dict[str, Any]:
	search, method, reservation = cstr(search).strip(), cstr(method).strip(), cstr(reservation).strip()
	closing = closing if closing in {value for value, _label in CLOSING} else "open"
	public = tenders_gateway.available_tenders(at=clock.now())
	needle = search.lower()
	rows = [
		{
			"reference": r["reference"], "title": r["title"], "procuring_entity": r["procuring_entity"], "method": r["method"], "reservation": r["reservation"],
			"submission_deadline_label": labels.datetime_label(r["submission_deadline"]), "href": f"/tenders/{r['reference']}",
		}
		for r in public
		if _closing_matches(closing, r["availability"])
		and (not needle or needle in r["title"].lower() or needle in r["reference"].lower())
		and (not method or r["method"] == method)
		and (not reservation or r["reservation"] == reservation)
	]
	n = len(rows)
	noun = "available Tender" if closing == "open" else "Tender"
	return {
		"rows": rows,
		"count_text": f"{n} {noun}{'' if n == 1 else 's'}" if rows else "",
		"empty_text": "" if rows else EMPTY_TEXT,
		"applied": {"search": search, "method": method, "reservation": reservation, "closing": closing},
		"options": {
			"method": _options("All methods", {r["method"] for r in public}),
			"reservation": _options("All categories", {r["reservation"] for r in public}),
			"closing": [{"value": value, "label": label} for value, label in CLOSING],
		},
	}


# --------------------------------------------------------------------------
# §7.1 supplier reads of a bid — `GetMyBids`, `GetBidWorkspace`, `GetBidTask`.
# A person outside the bid's lead organisation gets Not found. Nothing here
# writes: statuses are derived from the bound definition and saved values.
# --------------------------------------------------------------------------

NEXT_ACTION = {"Draft": "Continue bid", "Needs attention": "Continue bid", "Ready to submit": "Review and submit"}


def _bid_header(ctx, tasks) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import readiness

	ws = ctx.workspace
	saved = ws.last_saved_at or ws.created_at
	return {
		"reference": ws.name, "tender_reference": ws.tender_reference, "tenderer_name": ctx.tenderer_name, "status": readiness.bid_status(tasks),
		"draft_version": int(ws.current_draft_version or 0), "record_version": int(ws.record_version or 0), "last_saved_label": labels.datetime_label(saved),
	}


def _next(tasks) -> dict[str, str] | None:
	for key, state in tasks.items():
		if state.status != "Complete":
			return {"task": key, "text": "Continue with this task."}
	return None


def get_bid_workspace(*, bid_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	import frappe

	from kentender_procurement.bid_submission.services import bid_context, projection, readiness

	ctx = bid_context.load(bid_reference, actor=cstr(user or frappe.session.user), organisation=organisation, at=clock.now())
	tasks = readiness.evaluate(ctx)
	tender = tenders_gateway.published_tender(ctx.workspace.tender_reference, at=clock.now()) or {}
	return {
		"bid": _bid_header(ctx, tasks),
		"tender": {"reference": ctx.workspace.tender_reference, "title": tender.get("title", ""), "deadline_label": labels.datetime_label(tender.get("submission_deadline")), "availability": tender.get("availability", "")},
		"tasks": projection.task_nav(ctx, tasks), "must_fix": readiness.must_fix_total(tasks), "next": _next(tasks),
	}


def get_bid_task(*, bid_reference: str, task: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	import frappe

	from kentender_procurement.bid_submission.services import bid_context, projection, readiness

	ctx = bid_context.load(bid_reference, actor=cstr(user or frappe.session.user), organisation=organisation, at=clock.now())
	if not ctx.model.task(cstr(task)):
		raise frappe.DoesNotExistError("This part of the bid does not exist.")
	tasks = readiness.evaluate(ctx)
	return {"bid": _bid_header(ctx, tasks), "tasks": projection.task_nav(ctx, tasks), **projection.task_view(ctx, tasks, cstr(task))}


def get_my_bids(*, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""The acting organisation's bids, newest first, each with one next action.
	Status here is the recorded one; the bid itself derives the current one."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_authorization as authz

	actor = authz.require_person(cstr(user or frappe.session.user))
	try:
		lead = authz.acting_assignment(actor, organisation, at=clock.now())["organisation_id"]
	except frappe.ValidationError:
		return {"rows": [], "empty_text": "Your organisation has no bids yet."}
	rows = []
	for ws in frappe.get_all("Bid Workspace", filters={"lead_organisation": lead}, fields=["name", "tender_reference", "status", "current_draft_version", "created_at"], order_by="created_at desc", limit_page_length=0):
		tender = tenders_gateway.published_tender(ws.tender_reference, at=clock.now()) or {}
		rows.append({
			"bid_reference": ws.name, "tender_reference": ws.tender_reference, "tender_title": tender.get("title", ""), "status": ws.status,
			"deadline_label": labels.datetime_label(tender.get("submission_deadline")), "draft_version": int(ws.current_draft_version or 0),
			"next_action": {"label": NEXT_ACTION.get(ws.status, "View bid"), "href": f"/tenders/{ws.tender_reference}/bid"},
		})
	return {"rows": rows, "empty_text": "Your organisation has no bids yet."}
