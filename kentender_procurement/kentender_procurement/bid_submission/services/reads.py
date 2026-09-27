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
	import frappe

	from kentender_procurement.bid_submission.services import readiness

	ws = ctx.workspace
	saved = ws.last_saved_at or ws.created_at
	# Submitted, Withdrawn and Closed are recorded facts; only an open Draft
	# (including a replacement Draft) takes its status from readiness.
	status = ws.status if ws.status in ("Submitted", "Withdrawn", "Closed without submission") else readiness.bid_status(tasks)
	current = None
	if ws.current_submission_version:
		number, receipt = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "receipt"])
		current = {"version_label": f"Submitted bid Version {int(number)}", "receipt_reference": receipt}
	return {
		"reference": ws.name, "tender_reference": ws.tender_reference, "tenderer_name": ctx.tenderer_name, "status": status,
		"draft_version": int(ws.current_draft_version or 0), "record_version": int(ws.record_version or 0), "last_saved_label": labels.datetime_label(saved),
		"current_submission": current,
	}


ADDENDUM_NOTICE = "An addendum changed this Tender. Your next change moves the bid to the current Tender documents; then review the tasks it affects."


def _evaluate(ctx):
	"""Task states with addendum attention; a pending refresh is shown, never
	performed, by a read (plan D10)."""
	from kentender_procurement.bid_submission.services import addendum, readiness

	pending = addendum.pending(ctx) is not None
	tasks = readiness.evaluate(ctx, attention=addendum.attention(ctx) + (["documents"] if pending else []))
	return tasks, (ADDENDUM_NOTICE if pending else "")


def _next(tasks) -> dict[str, str] | None:
	for key, state in tasks.items():
		if state.status == "Needs attention":
			return {"task": key, "text": "Review this task: an addendum changed it."}
	for key, state in tasks.items():
		if state.status != "Complete":
			return {"task": key, "text": "Continue with this task."}
	return None


def bid_for_tender(*, tender_reference: str, actor: str, organisation: str = "", at=None) -> str:
	"""The acting organisation's bid for a Tender (its newest workspace);
	Not found when it has none — never another organisation's."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_authorization as authz

	try:
		lead = authz.acting_assignment(actor, organisation, at=at or clock.now())["organisation_id"]
	except frappe.ValidationError:
		raise frappe.DoesNotExistError("This bid is unavailable or you do not have permission to view it.")
	rows = frappe.get_all("Bid Workspace", filters={"tender_reference": cstr(tender_reference), "lead_organisation": lead}, pluck="name", order_by="created_at desc", limit_page_length=1)
	if not rows:
		raise frappe.DoesNotExistError("This bid is unavailable or you do not have permission to view it.")
	return rows[0]


def get_bid_workspace(*, bid_reference: str = "", tender_reference: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""`GetBidWorkspace` (§7.1, §10.7 BDS-DES-06), by bid or by Tender."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_context, projection, readiness, workspace_view

	from kentender_procurement.bid_submission.services import guidance

	actor, at = cstr(user or frappe.session.user), clock.now()
	if not cstr(bid_reference).strip():
		bid_reference = bid_for_tender(tender_reference=tender_reference, actor=actor, organisation=organisation, at=at)
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	tasks, notice = _evaluate(ctx)
	tender = tenders_gateway.published_tender(ctx.workspace.tender_reference, at=clock.now()) or {}
	guided = guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks)
	return {
		"bid": _bid_header(ctx, tasks),
		"tender": {"reference": ctx.workspace.tender_reference, "title": tender.get("title", ""), "deadline_label": labels.datetime_label(tender.get("submission_deadline")), "availability": tender.get("availability", "")},
		"tasks": projection.task_nav(ctx, tasks), "must_fix": readiness.must_fix_total(tasks), "next": _next(tasks), "addendum_notice": notice,
		"next_step": guided["next_step"], "journey": guided["journey"],
		**workspace_view.view(ctx, tasks, projection.task_nav(ctx, tasks), tender, at=at),
	}


def get_bid_task(*, bid_reference: str = "", task: str, tender_reference: str = "", organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""`GetBidTask` (§7.1), by bid or by Tender; the documents task also
	carries BDS-DES-07's documents, addenda, answers and acknowledgements."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_context, projection, readiness

	actor, at = cstr(user or frappe.session.user), clock.now()
	if not cstr(bid_reference).strip():
		bid_reference = bid_for_tender(tender_reference=tender_reference, actor=actor, organisation=organisation, at=at)
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	if not ctx.model.task(cstr(task)):
		raise frappe.DoesNotExistError("This part of the bid does not exist.")
	tasks, notice = _evaluate(ctx)
	view = {"bid": _bid_header(ctx, tasks), "tasks": projection.task_nav(ctx, tasks), "addendum_notice": notice, **projection.task_view(ctx, tasks, cstr(task))}
	if task == "price":
		from kentender_procurement.bid_submission.services import guidance, price, price_view

		view["price"] = price.summary(ctx)
		guided = guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks)
		view.update({"next_step": guided["next_step"], "journey": guided["journey"]})
		view.update(price_view.view(ctx, tasks, view, at=at))
	if task == "requirements":
		from kentender_procurement.bid_submission.services import guidance, requirements_view

		guided = guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks)
		view.update({"next_step": guided["next_step"], "journey": guided["journey"]})
		view.update(requirements_view.view(ctx, tasks, view, at=at))
	if task == "company":
		from kentender_procurement.bid_submission.services import company_view, guidance, tender_security

		view["security"] = _public_security(tender_security.response(ctx))
		guided = guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks)
		view.update({"next_step": guided["next_step"], "journey": guided["journey"]})
		view.update(company_view.view(ctx, tasks, view, at=at))
	if task == "documents":
		from kentender_procurement.bid_submission.services import documents_view, guidance

		published = tenders_gateway.published_tender(ctx.workspace.tender_reference, at=at) or {}
		guided = guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks)
		view.update({"tender": {"reference": ctx.workspace.tender_reference, "title": published.get("title", "")}, "next_step": guided["next_step"], "journey": guided["journey"]})
		view.update(documents_view.view(ctx, tasks, published, at=at))
	return view


def _public_security(security: dict[str, Any]) -> dict[str, Any]:
	"""The supplier's own security facts for the page (the handle is internal to the review link)."""
	return {k: v for k, v in security.items() if k != "security_form_handle"}


MY_BIDS_EMPTY = "No bids yet. Find a Tender to start your first bid."
MY_BIDS_STATUSES = ("Draft", "Needs attention", "Ready to submit", "Submitted", "Withdrawn", "Closed without submission")
STATUS_TONES = {"Draft": "draft", "Needs attention": "attention", "Ready to submit": "live", "Submitted": "live", "Withdrawn": "critical", "Closed without submission": "critical"}
RECEIPTS_EMPTY = "No submission or withdrawal receipts for this organisation."
SUSPENDED_TEXT = "This supplier account is suspended. You can read and download existing receipts; no bid can be prepared, submitted, replaced or withdrawn."


def _counted(count: int, one: str, many: str) -> str:
	return f"{count} {one if count == 1 else many}"


def _withdrawal(workspace: str) -> dict[str, Any] | None:
	import frappe

	rows = frappe.get_all("Bid Submission Change", filters={"bid_workspace": workspace, "change_type": "Withdrawal"}, fields=["acknowledgement_ref", "acknowledged_at"], order_by="acknowledged_at desc", limit_page_length=1)
	return rows[0] if rows else None


def _may_start_replacement(actor: str, lead: str, tender_reference: str, at) -> bool:
	"""Start replacement is the Authorised Signatory's, on an Active Account,
	while the Tender is open before its deadline (`PrepareReplacementBid`'s
	own rules, read from the same Tender facts)."""
	import frappe
	from frappe.utils import get_datetime

	from kentender_procurement.bid_submission.services import bid_authorization as authz
	from kentender_procurement.bid_submission.services import supplier_gateway

	root = tenders_gateway.tender_root(tender_reference)
	if not root or not root.submission_deadline or get_datetime(at) >= get_datetime(root.submission_deadline):
		return False
	if tenders_gateway.availability(tender_reference, at=at) != "open":
		return False
	if (supplier_gateway.organisation(organisation_id=lead) or {}).get("account_status") != "Active":
		return False
	try:
		return authz.acting_assignment(actor, lead, at=at)["responsibility"] == authz.SIGNATORY
	except frappe.ValidationError:
		return False


def _my_bid_row(ws, tender: dict[str, Any], *, actor: str, lead: str, at, work: list[dict[str, Any]]) -> dict[str, Any]:
	import frappe

	base = f"/tenders/{ws.tender_reference}/bid"
	status, version_label, updated = ws.status, f"Draft Version {int(ws.current_draft_version or 0)}", ws.last_saved_at or ws.created_at
	if status in ("Draft", "Needs attention"):
		actions = [{"label": "Continue bid", "href": base}]
	elif status == "Ready to submit":
		actions = [{"label": "Review bid", "href": f"{base}/review"}]
	elif status == "Submitted":
		version = frappe.db.get_value("Bid Submission Version", ws.current_submission_version, ["version_number", "receipt", "accepted_at"], as_dict=True) or {}
		version_label, updated = f"Submitted bid Version {int(version.get('version_number') or 1)}", version.get("accepted_at") or ws.status_since
		actions = [{"label": "View receipt", "href": f"{base}/receipt/{version.get('receipt')}"}] if version.get("receipt") else []
	elif status == "Withdrawn":
		change = _withdrawal(ws.name) or {}
		version_label, updated = "", change.get("acknowledged_at") or ws.status_since
		actions = [{"label": "View acknowledgement", "href": f"{base}/receipt/{change.get('acknowledgement_ref')}"}] if change.get("acknowledgement_ref") else []
		if _may_start_replacement(actor, lead, ws.tender_reference, at):
			actions.append({"label": "Start replacement", "href": base, "command": "prepare_replacement", "record_version": int(ws.record_version or 0)})
	else:  # Closed without submission
		updated = ws.status_since or updated
		actions = [{"label": "View bid", "href": base}]
	return {
		"bid_reference": ws.name, "tender_reference": ws.tender_reference, "tender_title": tender.get("title", ""), "status": status, "status_label": status,
		"status_tone": STATUS_TONES.get(status, "draft"), "version_label": version_label, "deadline_label": labels.datetime_label(tender.get("submission_deadline")),
		"updated_label": labels.datetime_label(updated), "draft_version": int(ws.current_draft_version or 0), "actions": actions,
		"next_action": actions[0] if actions else {"label": "View bid", "href": base},
		"work": [{"kind": i["kind"], "title": i["title"]} for i in work if i["bid_reference"] == ws.name],
	}


def get_my_bids(*, organisation: str = "", search: str = "", status: str = "", user: str | None = None) -> dict[str, Any]:
	"""`GetMyBids` (§7.1, §10.6 BDS-DES-05): the acting organisation's bids,
	newest first, each with its recorded status, version, deadline, last
	update and the actions this person may take. A list, not a tracker."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_authorization as authz
	from kentender_procurement.bid_submission.services import handoffs

	actor, at = authz.require_person(cstr(user or frappe.session.user)), clock.now()
	status = cstr(status) if cstr(status) in MY_BIDS_STATUSES else ""
	options = {"status": [{"value": "", "label": "All statuses"}] + [{"value": s, "label": s} for s in MY_BIDS_STATUSES]}
	base = {"empty_text": MY_BIDS_EMPTY, "options": options, "applied": {"search": cstr(search), "status": status}}
	try:
		lead = authz.acting_assignment(actor, organisation, at=at)["organisation_id"]
	except frappe.ValidationError:
		return {**base, "rows": [], "count_text": "", "work": []}
	workspaces = frappe.get_all(
		"Bid Workspace", filters={"lead_organisation": lead}, order_by="created_at desc", limit_page_length=0,
		fields=["name", "tender_reference", "status", "status_since", "current_draft_version", "current_submission_version", "last_saved_at", "created_at", "record_version"],
	)
	work = handoffs.items_for(actor, [w.name for w in workspaces])
	needle = cstr(search).strip().lower()
	rows = []
	for ws in workspaces:
		if status and ws.status != status:
			continue
		tender = tenders_gateway.published_tender(ws.tender_reference, at=at) or {}
		if needle and not any(needle in cstr(v).lower() for v in (ws.name, ws.tender_reference, tender.get("title"))):
			continue
		rows.append(_my_bid_row(ws, tender, actor=actor, lead=lead, at=at, work=work))
	return {**base, "rows": rows, "count_text": _counted(len(rows), "bid", "bids") if rows else "", "work": work}


def get_receipt_history(*, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""`/account/receipts` (§10.20 BDS-DES-17): the acting organisation's
	submission receipts and withdrawal acknowledgements, oldest first — a
	read-only recovery register, also for a suspended Account. Another
	organisation named here is Not found. No price, content or digest."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_authorization as authz
	from kentender_procurement.bid_submission.services import supplier_gateway

	actor, at = authz.require_person(cstr(user or frappe.session.user)), clock.now()
	empty = {"outcome": "OK", "rows": [], "count_text": "", "empty_text": RECEIPTS_EMPTY, "suspended": False, "suspended_text": ""}
	try:
		lead = authz.acting_assignment(actor, organisation, at=at)["organisation_id"]
	except frappe.ValidationError:
		if cstr(organisation).strip():
			raise frappe.DoesNotExistError("This record is unavailable or you do not have permission to view it.")
		return empty
	suspended = (supplier_gateway.organisation(organisation_id=lead) or {}).get("account_status") == "Suspended"
	workspaces = {w.name: w.tender_reference for w in frappe.get_all("Bid Workspace", filters={"lead_organisation": lead}, fields=["name", "tender_reference"], limit_page_length=0)}
	titles: dict[str, str] = {}

	def title(reference: str) -> str:
		if reference not in titles:
			titles[reference] = cstr((tenders_gateway.published_tender(reference, at=at) or {}).get("title"))
		return titles[reference]

	entries = []
	names = list(workspaces)
	if names:
		for r in frappe.get_all("Bid Receipt", filters={"bid_workspace": ("in", names)}, fields=["receipt_reference", "tender_reference", "tender_title", "accepted_at"], limit_page_length=0):
			entries.append((r.accepted_at, r.tender_reference, r.tender_title or title(r.tender_reference), r.receipt_reference, "Submitted", "live"))
		for c in frappe.get_all("Bid Submission Change", filters={"bid_workspace": ("in", names), "change_type": "Withdrawal"}, fields=["bid_workspace", "acknowledgement_ref", "acknowledged_at"], limit_page_length=0):
			reference = workspaces[c.bid_workspace]
			entries.append((c.acknowledged_at, reference, title(reference), c.acknowledgement_ref, "Withdrawn", "critical"))
	entries.sort(key=lambda e: (str(e[0]), e[3]))
	rows = [
		{
			"tender_reference": ref, "tender_title": name, "document": document, "event": event, "event_tone": tone,
			"at_label": labels.datetime_seconds_label(when).replace(f" {labels.TIME_ZONE_LABEL}", ""), "href": f"/tenders/{ref}/bid/receipt/{document}",
		}
		for when, ref, name, document, event, tone in entries
	]
	return {**empty, "rows": rows, "count_text": _counted(len(rows), "record", "records") if rows else "", "suspended": suspended, "suspended_text": SUSPENDED_TEXT if suspended else ""}


def get_bid_review(*, bid_reference: str, organisation: str = "", user: str | None = None) -> dict[str, Any]:
	"""`GetBidReview` (§7.1, §5.3, §5.7 items 1–2): the result first (ready or
	not), then every Must fix and Review note linked to its task and field.
	Viewing it changes nothing (§5.3)."""
	import frappe

	from kentender_procurement.bid_submission.services import bid_context, projection, readiness

	from kentender_procurement.bid_submission.services import guidance

	actor, at = cstr(user or frappe.session.user), clock.now()
	ctx = bid_context.load(bid_reference, actor=actor, organisation=organisation, at=at)
	tasks, notice = _evaluate(ctx)
	must_fix, notes = [], []
	for task in ctx.model.tasks:
		for state in tasks[task.key].fields:
			if not state.issue:
				continue
			item = {"task": task.key, "task_label": task.label, "handle": state.field.handle, "label": projection.label(ctx, state.field), "text": state.issue["text"]}
			(must_fix if state.issue["severity"] == readiness.MUST_FIX else notes).append(item)
	attention = [{"task": key, "task_label": ctx.model.task(key).label} for key, state in tasks.items() if state.status == "Needs attention"]
	from kentender_procurement.bid_submission.services import price, tender_security

	security_note = tender_security.review_note(ctx)
	if security_note:
		notes.append({**security_note, "task_label": ctx.model.task("company").label})
	header = _bid_header(ctx, tasks)
	return {
		"bid": header, "ready": header["status"] == "Ready to submit", "must_fix": must_fix, "review_notes": notes, "needs_attention": attention,
		"tasks": projection.task_nav(ctx, tasks), "addendum_notice": notice, "price": price.summary(ctx),
		"security": _public_security(tender_security.response(ctx)),
		**guidance.for_bid(ctx, actor=actor, at=at, tasks=tasks),
	}
