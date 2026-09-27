# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-07 shows (BDS-CHG-001 v0.8 §10.8; plan Phase 11, slice 11.7),
decided here from the Published Tender, the Tenders notices addressed to this
candidate and the Draft:

- the official documents and each effective addendum with View and Download;
- for an addendum, the notice to the candidate's Tender notice email while it
  is Queued, Sent without delivery proof, or failed (Delivery problem, with
  Update notice email) — never presented as proof, never blocking reading;
- the addendum acknowledgement the Draft holds (the documents task's own
  confirmation response), who acknowledged it and when;
- the public answers with this candidate's notice result;
- whether a question may still be asked, or when clarifications closed;
- the badge (only while there is something to acknowledge) and whether Save
  and continue waits for an acknowledgement.

Nothing here saves or acknowledges anything."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import labels, projection, supplier_gateway, tenders_gateway

TITLE = "Tender documents, clarifications and addenda"
DESCRIPTION = "Review the current Tender, ask questions before the clarification deadline and acknowledge issued addenda."
BLOCKED_TEXT = "Acknowledge the addendum to continue."
ADDENDUM_NOTICE = {
	"Queued": ("Queued", "pending", "This notice is waiting to be sent. You can read the current Tender information here now."),
	"Pending": ("Queued", "pending", "This notice is waiting to be sent. You can read the current Tender information here now."),
	"Sent": ("Sent", "pending", "Delivery has not been confirmed. You can read the current Tender information here now."),
	"Failed": ("Delivery problem", "attention", "The notice could not be delivered to your selected Tender notice email. The current Tender information remains available here."),
}
ANSWER_NOTICE = {"Delivered": ("Delivered", "live"), "Sent": ("Sent", "pending"), "Queued": ("Queued", "pending"), "Pending": ("Queued", "pending"), "Failed": ("Delivery problem", "attention")}
BADGE_TONES = {"Complete": "live", "Needs attention": "attention"}


def _acknowledgement(ctx, tasks, group) -> dict[str, Any] | None:
	states = {s.field.key: s for s in tasks["documents"].fields}
	fields = [f for f in group.fields if f.key in states and f.editable]
	if not fields:
		return None
	field = fields[0]
	value = bool(states[field.key].value)
	done = ""
	if value:
		change = frappe.get_all(
			"Bid Draft Change", filters={"bid_workspace": ctx.workspace.name, "response_key": field.key}, fields=["actor", "changed_at"], order_by="changed_at desc", limit_page_length=1,
		)
		if change:
			name = cstr(frappe.db.get_value("User", change[0].actor, "full_name") or change[0].actor)
			done = f"Acknowledged by {name} on {labels.datetime_label(change[0].changed_at)}"
	return {"handle": field.handle, "label": projection.label(ctx, field), "value": value, "acknowledged_text": done, "moves_bid": False}


def _pending_acknowledgements(ctx) -> dict[str, dict[str, Any]]:
	"""Addendum reference → the acknowledgement a Draft still bound to an
	earlier definition will be asked for. The Draft moves to the current
	definition on its next save (`RefreshBidForAddendum`); until then the
	response has no handle here, and saving it moves the bid first."""
	from kentender_procurement.bid_submission.services import addendum
	from kentender_procurement.bid_submission.services.definition_model import DefinitionModel

	current = addendum.pending(ctx)
	if not current:
		return {}
	model = DefinitionModel(current["definition"], members=[m.organisation_id for m in ctx.arrangement.members])
	out = {}
	for group in model.groups_of("documents"):
		addendum_id = cstr((group.published_facts or {}).get("addendum_id"))
		fields = [f for f in group.fields if f.editable]
		if addendum_id and fields:
			reference = tenders_gateway.addendum_reference(ctx.workspace.tender, addendum_id)
			out[reference] = {"handle": "", "label": projection.label(ctx, fields[0]), "value": False, "acknowledged_text": "", "moves_bid": True}
	return out


def view(ctx, tasks, published: dict[str, Any], *, at) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import overview

	ws = ctx.workspace
	reference = ws.tender_reference
	candidate = tenders_gateway.candidate_view(ws.tender, ws.bidder_arrangement) or {"notices": []}
	delivery = {(n["kind"], n["subject_key"]): n["status"] for n in candidate["notices"]}
	notice_email = cstr(frappe.db.get_value("Bidder Arrangement", ws.bidder_arrangement, "mandatory_notice_email"))
	groups = {cstr((g.published_facts or {}).get("addendum_id")): g for g in ctx.model.groups_of("documents") if (g.published_facts or {}).get("addendum_id")}
	by_reference = {tenders_gateway.addendum_reference(ws.tender, addendum_id): group for addendum_id, group in groups.items()}
	pending = _pending_acknowledgements(ctx)

	addenda = []
	for a in published.get("addenda") or []:
		status = delivery.get(("addendum", a["reference"]), "")
		notice = None
		if status in ADDENDUM_NOTICE:
			label, tone, text = ADDENDUM_NOTICE[status]
			notice = {"status": label, "tone": tone, "text": text, "destination": f"Notice to {notice_email}" if notice_email else "", "can_update_contact": status == "Failed"}
		group = by_reference.get(a["reference"])
		addenda.append({
			"reference": a["reference"], "summary": a["summary"], "label": f"{a['reference']} · {a['summary']}", "issued": labels.datetime_label(a["issued_at"]),
			"revised_deadline": labels.datetime_label(a.get("revised_submission_deadline")) or labels.datetime_label(published.get("submission_deadline")),
			"view_href": overview.document_href(reference, a["document_key"], inline=True) if a.get("document_key") else "",
			"download_href": overview.document_href(reference, a["document_key"], inline=False) if a.get("document_key") else "",
			"notice": notice, "acknowledgement": (_acknowledgement(ctx, tasks, group) if group else None) or pending.get(a["reference"]),
		})
	answers = []
	for q in published.get("answers") or []:
		status = delivery.get(("answer", q["key"]), "")
		label, tone = ANSWER_NOTICE.get(status, ("", ""))
		answers.append({"key": q["key"], "question": cstr(q.get("question")), "answer": cstr(q.get("answer")), "answered": f"Answered {labels.datetime_label(q.get('answered_at'))}", "notice": {"status": label, "tone": tone} if label else None})

	clarification_deadline = labels.datetime_label(published.get("clarification_deadline"))
	open_questions = bool(published.get("clarifications_open")) and ws.status not in ("Submitted", "Withdrawn", "Closed without submission")
	acknowledgements = [a["acknowledgement"] for a in addenda if a["acknowledgement"]]
	status = tasks["documents"].status
	next_task = next((t.key for t in ctx.model.tasks if t.key != "documents"), "review")
	org = supplier_gateway.organisation(organisation_id=ws.lead_organisation) or {}
	return {
		"page": {"title": TITLE, "description": DESCRIPTION, "back_href": f"/tenders/{reference}/bid"},
		"badge": {"label": status, "tone": BADGE_TONES.get(status, "draft")} if acknowledgements else None,
		"documents": [
			{"key": d["key"], "label": d["label"], "published": labels.date_label(d["published_at"]) if d.get("published_at") else "",
			 "view_href": overview.document_href(reference, d["key"], inline=True), "download_href": overview.document_href(reference, d["key"], inline=False)}
			for d in published.get("documents") or []
		],
		"addenda": addenda,
		"answers": answers,
		"clarification": {
			"can_ask": open_questions, "deadline": clarification_deadline,
			"closed_text": "" if published.get("clarifications_open") else (f"Clarifications closed {clarification_deadline}." if clarification_deadline else ""),
		},
		"organisation": {"id": ws.lead_organisation, "legal_name": cstr(org.get("legal_name"))},
		"footer": {
			"save_label": "Save and continue", "next_href": f"/tenders/{reference}/bid/{next_task}",
			"blocked_text": BLOCKED_TEXT if any(not a["value"] for a in acknowledgements) else "",
		},
		"notice_contact": notice_contact(ws),
	}


def notice_contact(ws) -> dict[str, Any]:
	"""The candidate's Tender notice email and the verified Account emails it
	may change to (`UpdateTenderNoticeContact`)."""
	arrangement = frappe.db.get_value("Bidder Arrangement", ws.bidder_arrangement, ["name", "mandatory_notice_email", "record_version"], as_dict=True) or {}
	contacts = [c for c in supplier_gateway.verified_contacts(organisation_id=ws.lead_organisation) if c.get("channel", "Email") == "Email"]
	current = next((c["contact_id"] for c in contacts if c["value"] == arrangement.get("mandatory_notice_email")), "")
	return {
		"arrangement": cstr(arrangement.get("name")), "record_version": int(arrangement.get("record_version") or 0), "current": current, "email": cstr(arrangement.get("mandatory_notice_email")),
		"options": [{"contact_id": c["contact_id"], "value": c["value"]} for c in contacts],
	}
