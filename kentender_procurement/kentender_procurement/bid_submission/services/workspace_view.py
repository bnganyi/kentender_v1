# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-06 shows beyond the task states (BDS-CHG-001 v0.8 §10.7,
§5.10, §10.19; plan Phase 11, slice 11.6), all decided here from recorded
facts and trusted time:

- the header lines and the one header action this viewer may take (Review
  bid, Continue bid, Review addendum, Continue saved bid, Back to My bids);
- the deadline with the time remaining, or the trusted time once closed;
- the availability notice when submission cannot happen (the production
  gate, a service outage, missing supplier-portal information) — the saved
  work is kept and the deadline stated;
- the current notices: public answers by delivery to this candidate's
  Tender notice email, effective addenda by this bid's acknowledgement;
- each task's last recorded change and action, and who saved last.

Nothing here saves, acknowledges or refreshes anything."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, get_datetime

from kentender_procurement.bid_submission.services import availability, clarification, labels, tenders_gateway

DESCRIPTION = "Complete the five tasks below before an Authorised Signatory submits the bid."
NOTICES_NOTE = "Delivery describes the notice sent to your Tender notice email. The published answer and addendum are available here whether or not a notice was delivered."
# The same words and tones as the documents task (§5.2 item 11): Sent is
# provider acceptance without delivery proof, never shown like Delivered.
DELIVERY = {"Delivered": ("Delivered", "live"), "Sent": ("Sent", "pending"), "Queued": ("Queued", "pending"), "Pending": ("Queued", "pending"), "Failed": ("Delivery problem", "attention")}
CLOSED_STATES = ("Submitted", "Withdrawn", "Closed without submission")


def _plural(count: int, word: str) -> str:
	return f"{count} {word}{'' if count == 1 else 's'}"


def remaining(deadline, at) -> str:
	minutes = max(0, int((get_datetime(deadline) - get_datetime(at)).total_seconds()) // 60)
	days, rest = divmod(minutes, 1440)
	hours, mins = divmod(rest, 60)
	parts = ([_plural(days, "day")] if days else []) + ([_plural(hours, "hour")] if days or hours else []) + [_plural(mins, "minute")]
	return "Closes in " + " ".join(parts)


def _closed(root, at) -> bool:
	return bool(root and root.submission_deadline and get_datetime(at) >= get_datetime(root.submission_deadline))


def deadline(root, at) -> dict[str, Any]:
	close = labels.datetime_label(root.submission_deadline) if root else ""
	if _closed(root, at):
		return {"rows": [{"label": "Submission deadline", "value": close}, {"label": "Trusted server time", "value": labels.datetime_seconds_label(at)}]}
	return {"rows": [{"label": "Submissions close", "value": close}, {"label": "Time remaining", "value": remaining(root.submission_deadline, at) if root else ""}]}


def _support_links() -> list[dict[str, str]]:
	from kentender_core.services import public_portal

	email = cstr((public_portal.get_public_portal_information().get("support") or {}).get("email"))
	return [{"label": "Supplier support", "href": f"mailto:{email}"}] if email else []


def portal_incomplete() -> bool:
	from kentender_core.services import public_portal

	return public_portal.get_public_portal_information().get("status") != "Complete"


def availability_notice(ws, root, at) -> dict[str, Any] | None:
	"""§5.10 as the bidder reads it, above the tasks; None when submission can happen."""
	if ws.status in CLOSED_STATES or _closed(root, at):
		return None
	close = labels.datetime_label(root.submission_deadline) if root else ""
	if portal_incomplete():
		return {"tone": "warning", "title": "Submission is unavailable", "text": "Supplier portal information is being restored. Your saved bid can still be reviewed and saved.", "links": []}
	code = availability.get_submission_availability()["code"]
	if code == "BDS_PRODUCTION_SUBMISSION_NOT_ENABLED":
		return {"tone": "critical", "title": "Electronic bid submission is not available yet", "text": f"Your bid remains saved and has not been submitted. Submissions close {close}.", "links": _support_links()}
	if code in ("BDS_SIGNATURE_UNAVAILABLE", "BDS_SUBMISSION_SERVICE_UNAVAILABLE"):
		status = {"label": "View status", "href": f"/tenders/{ws.tender_reference}/bid/status"}
		return {"tone": "critical", "title": "Electronic submission is temporarily unavailable", "text": f"Your bid remains saved and no receipt exists. Submissions close {close}.", "links": [status, *_support_links()]}
	return None


def _acknowledged(ctx, tasks) -> dict[str, bool]:
	"""Addendum reference → whether this bid's current Draft acknowledged it
	(the confirmation response the documents task holds for each addendum)."""
	out: dict[str, bool] = {}
	states = {s.field.key: s for s in tasks["documents"].fields} if "documents" in tasks else {}
	for group in ctx.model.groups_of("documents"):
		addendum_id = cstr((group.published_facts or {}).get("addendum_id"))
		if not addendum_id:
			continue
		reference = tenders_gateway.addendum_reference(ctx.workspace.tender, addendum_id)
		values = [states[f.key].value for f in group.fields if f.key in states]
		out[reference] = bool(values) and all(v is True or v == 1 or v == "1" for v in values)
	return out


def notices(ctx, tasks, tender: dict[str, Any]) -> list[dict[str, Any]]:
	from kentender_procurement.bid_submission.services import overview

	ws = ctx.workspace
	view = tenders_gateway.candidate_view(ws.tender, ws.bidder_arrangement) or {"notices": []}
	delivery = {(n["kind"], n["subject_key"]): n["status"] for n in view["notices"]}
	rows = []
	for answer in tender.get("answers") or []:
		status, tone = DELIVERY.get(delivery.get(("answer", answer["key"]), ""), ("Not sent", "draft"))
		rows.append({
			"key": answer["key"], "label": f"Clarification answer · {labels.date_label(answer['answered_at'])}", "status": status, "tone": tone,
			"action": {"label": "View answer", "href": f"/tenders/{ws.tender_reference}/bid/documents"},
		})
	public = {a["key"] for a in tender.get("answers") or []}
	for q in clarification.my_questions(ws.name):
		if q["status"] == "Answered" and q["key"] in public:
			continue  # a general answer is already listed above
		rows.append({
			"key": f"question:{q['key']}", "label": f"Your question · {q['received']}", "status": "Waiting for an answer" if q["status"] == "Received" else q["status_label"], "tone": q["tone"],
			"action": {"label": "View answer" if q["status"] == "Answered" else "View question", "href": f"/tenders/{ws.tender_reference}/bid/documents"},
		})
	acknowledged = _acknowledged(ctx, tasks)
	pending = _addendum_pending(ctx)
	for addendum in tender.get("addenda") or []:
		reference = addendum["reference"]
		done = acknowledged.get(reference, False) and not pending
		action = (
			{"label": "View addendum", "href": overview.document_href(ws.tender_reference, addendum["document_key"], inline=True)} if done and addendum.get("document_key")
			else {"label": "Review addendum", "href": f"/tenders/{ws.tender_reference}/bid/documents"}
		)
		rows.append({
			"key": reference, "label": f"{reference} · {addendum['summary']}", "status": "Acknowledged" if done else "Not acknowledged", "tone": "live" if done else "attention", "action": action,
		})
	return rows


def _addendum_pending(ctx) -> bool:
	from kentender_procurement.bid_submission.services import addendum

	return addendum.pending(ctx) is not None


def _updated(ws) -> dict[str, Any]:
	rows = frappe.db.sql(
		"""select section_key, max(changed_at) from `tabBid Draft Change` where bid_workspace = %s group by section_key""", (ws.name,),
	)
	return {cstr(key): at for key, at in rows}


def task_rows(ctx, tasks, nav: list[dict[str, Any]], *, closed: bool) -> list[dict[str, Any]]:
	ws = ctx.workspace
	updated = _updated(ws)
	out = []
	for row in nav:
		key, status = row["key"], row["status"]
		when = (ws.last_saved_at if status == "Complete" else None) if key == "review" else updated.get(key)
		if closed:
			action = {"label": "View", "primary": False}
		elif key == "review":
			action = {"label": "Review bid", "primary": True} if status == "Complete" else {"label": "View", "primary": False}
		else:
			action = {"label": "View" if status == "Complete" else "Continue", "primary": False}
		out.append({**row, "updated_label": labels.datetime_label(when).replace(f" {labels.TIME_ZONE_LABEL}", "") if when else "—", "action": {**action, "href": f"/tenders/{ws.tender_reference}/bid/{key}"}})
	return out


def header(ctx, nav: list[dict[str, Any]], tender: dict[str, Any], *, closed: bool, release_blocked: bool = False) -> dict[str, Any]:
	ws = ctx.workspace
	base = f"/tenders/{ws.tender_reference}/bid"
	first_open = next((row["key"] for row in nav if row["status"] != "Complete"), "")
	if release_blocked and not closed:
		action = None  # BDS-DES-06-WITHDRAWN-RELEASE: the guidance links are the only ways on
	elif closed:
		action = {"label": "Back to My bids", "href": "/my-bids", "tone": "secondary"}
	elif _addendum_pending(ctx) or any(row["key"] == "documents" and row["status"] == "Needs attention" for row in nav):
		action = {"label": "Review addendum", "href": f"{base}/documents", "tone": "primary"}
	elif portal_incomplete():
		action = {"label": "Continue saved bid", "href": f"{base}/{first_open or 'review'}", "tone": "secondary" if not first_open or first_open == "review" else "primary"}
	elif not first_open or first_open == "review":
		action = {"label": "Review bid", "href": f"{base}/review", "tone": "primary"}
	else:
		action = {"label": "Continue bid", "href": f"{base}/{first_open}", "tone": "primary"}
	return {
		"title_line": tender.get("title", ""), "refs_line": f"{ws.tender_reference} · {ws.name} · Draft Version {int(ws.current_draft_version or 0)}", "description": DESCRIPTION, "action": action,
	}


def saved_text(ws) -> str:
	if not ws.last_saved_at or not ws.last_saved_by:
		return ""
	name = cstr(frappe.db.get_value("User", ws.last_saved_by, "full_name") or ws.last_saved_by)
	return f"Saved {labels.datetime_label(ws.last_saved_at)} by {name}."


def view(ctx, tasks, nav: list[dict[str, Any]], tender: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	root = tenders_gateway.tender_root(ws.tender_reference)
	closed = ws.status in CLOSED_STATES or _closed(root, at)
	from kentender_procurement.bid_submission.services import definition_runtime

	# §4.4.4 / BDS-DES-06-WITHDRAWN-RELEASE: a Draft whose bound release is
	# Withdrawn or fails its checks is kept for reading, with the waiting line
	# and two ways on (View current Tender, Supplier support)
	release_blocked = not closed and not definition_runtime.bid_condition(ctx)["ok"]
	return {
		"header": header(ctx, nav, tender, closed=closed, release_blocked=release_blocked),
		"deadline": deadline(root, at),
		"availability_notice": None if release_blocked else availability_notice(ws, root, at),
		"guidance_links": [{"label": "View current Tender", "href": f"/tenders/{ws.tender_reference}"}, *_support_links()] if release_blocked else [],
		"notices": notices(ctx, tasks, tender),
		"notices_note": NOTICES_NOTE,
		"tasks": task_rows(ctx, tasks, nav, closed=closed or release_blocked),
		"saved_text": saved_text(ws),
	}
