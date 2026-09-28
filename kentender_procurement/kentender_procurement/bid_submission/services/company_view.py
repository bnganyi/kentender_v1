# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What BDS-DES-08 shows (BDS-CHG-001 v0.8 §10.9; plan Phase 11, slice 11.8),
decided here from the Draft, its organisation snapshot, the arrangement and
the published definition's own compositions — never from board rows:

- the bidding organisation as copied to this bid (single or joint venture),
  whether the Account has changed since, and the two choices when it has;
- the bid's Tender contact (the arrangement's notice email and the bid's own
  email and phone);
- one row per form of the task other than the tender security (tenderer
  information, each joint-venture member, the locked declarations, the
  reservation declaration) in the definition's order, with its state and who
  confirmed it; its fields open in the response drawer;
- the tender security fields, its proof, and the physical original as this
  supplier's own bid knows it (recorded or not yet recorded);
- the Authorised Signatory for this bid and whether their certificate is
  ready.

Nothing here saves anything."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import documents_view, gateways, labels, projection, security_matching, supplier_gateway, tenders_gateway

TITLE = "Company, declarations and tender security"
DESCRIPTION = "Confirm who is bidding and complete the required legal forms."
BADGE_TONES = {"Complete": "live", "Needs attention": "attention"}
SNAPSHOT_FACTS = (("legal_name", "Legal name"), ("registration_number", "Registration number"), ("tax_identifier", "KRA PIN"), ("registered_address", "Address"))
ACCOUNT_UPDATE_NOTE = "Neither action edits the Account. Use updated details refreshes only this Draft and revalidates the affected forms."


def _name(user: str) -> str:
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def organisation(ctx) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import snapshot

	ws, arrangement = ctx.workspace, ctx.arrangement
	row = frappe.db.get_value("Bid Organisation Snapshot", ws.organisation_snapshot, ["facts_json", "taken_at"], as_dict=True) or {}
	facts = json.loads(row.get("facts_json") or "{}").get("organisation") or {}
	joint = arrangement.arrangement_type == "Joint venture"
	out: dict[str, Any] = {"kind": "joint_venture" if joint else "single", "update_account_href": "/account"}
	if joint:
		out["facts"] = [
			{"label": "Joint-venture name", "value": cstr(arrangement.joint_venture_name)}, {"label": "Lead organisation", "value": cstr(facts.get("legal_name"))},
			{"label": "Arrangement", "value": "Joint venture"},
		]
		out["members"] = [{"name": cstr(facts.get("legal_name")), "role": "Lead", "status": "Active"}] + [
			{"name": cstr(m.legal_name), "role": "Member", "status": "Active"} for m in arrangement.members
		]
	else:
		out["facts"] = [{"label": label, "value": cstr(facts.get(key))} for key, label in SNAPSHOT_FACTS] + [{"label": "Arrangement", "value": "Single organisation"}]
	out["snapshot_text"] = f"From your Account · copied to this bid on {labels.datetime_label(row.get('taken_at'))}" if row.get("taken_at") else ""
	compared = snapshot.compare(ws)
	changed = [k for k in compared["changed"] if not k.startswith("members.")]
	if changed:
		key = changed[0]
		label = dict(SNAPSHOT_FACTS).get(key, key.replace("_", " ").capitalize())
		out["update"] = {
			"fact": label, "rows": [{"label": "This bid", "value": cstr(compared["current"].get("organisation", {}).get(key))}, {"label": "Current Account", "value": cstr(compared["latest"]["organisation"].get(key))}],
			"note": ACCOUNT_UPDATE_NOTE, "record_version": int(ws.record_version or 0),
		}
		out["current_text"] = ""
	else:
		out["update"] = None
		out["current_text"] = "This bid is using your current Account details."
	return out


def contact(ctx) -> dict[str, Any]:
	from kentender_procurement.bid_submission.services import tender_contact

	arrangement = ctx.arrangement
	people = tender_contact.people(ctx)
	return {
		"assigned": _name(cstr(arrangement.tender_contact_user)) if arrangement.tender_contact_user else cstr(arrangement.tender_contact_name), "notice_email": cstr(arrangement.mandatory_notice_email), "notice_verified": bool(arrangement.mandatory_notice_email),
		"notice_help": "Mandatory clarification, addendum, deadline and cancellation notices are sent here.",
		"email": cstr(arrangement.tender_contact_email), "phone": cstr(arrangement.tender_contact_phone),
		"note": "These values apply only to this bid.", "record_version": int(arrangement.record_version or 0),
		# §10.9 Assigned person: any active person of the organisation (FU-V08-54)
		"people": [{"assignment_id": p["assignment_id"], "name": p["name"]} for p in people],
		"person": next((p["assignment_id"] for p in people if p["user"] == cstr(arrangement.tender_contact_user)), ""),
		"notice": documents_view.notice_contact(ctx.workspace),
	}


def _confirmed(ctx, group, states) -> str:
	fields = [f for f in group.fields if f.kind == "confirmation"]
	if not fields or not states.get(fields[-1].key) or not states[fields[-1].key].value:
		return ""
	change = frappe.get_all("Bid Draft Change", filters={"bid_workspace": ctx.workspace.name, "response_key": fields[-1].key}, fields=["actor"], order_by="changed_at desc", limit_page_length=1)
	return f"Confirmed by {_name(change[0].actor)}" if change else "Confirmed"


def _group_status(group, states) -> str:
	shown = [states[f.key] for f in group.fields if f.key in states and states[f.key].visible and f.editable]
	if any(s.issue and s.issue.get("severity") == "Must fix" and s.value not in (None, "", []) for s in shown):
		return "Needs attention"
	answered = [s for s in shown if s.value not in (None, "", [], False)]
	if not answered:
		return "Not started"
	if any(s.required and s.value in (None, "", [], False) for s in shown) or any(s.issue and s.issue.get("severity") == "Must fix" for s in shown):
		return "In progress"
	return "Complete"


def declarations(ctx, tasks, view_groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
	states = {s.field.key: s for s in tasks["company"].fields}
	rows = []
	for group, shown in zip(ctx.model.groups_of("company"), view_groups):
		if group.rule_id == security_matching.SECURITY_RULE:
			continue
		status = _group_status(group, states)
		confirmed = _confirmed(ctx, group, states) if group.composition_id == "COMP-LOCKED-DECLARATION" and status == "Complete" else ""
		label = "Confirmed" if confirmed else status
		rows.append({
			"key": shown["key"], "label": f"{shown['heading']} — {shown['member']}" if shown.get("member") else shown["heading"], "status": label, "tone": "live" if label in ("Complete", "Confirmed") else ("attention" if label == "Needs attention" else "draft"),
			"confirmed_text": confirmed if confirmed != "Confirmed" else "", "statement": shown.get("statement", ""), "facts": shown.get("facts") or [], "fields": shown["fields"],
		})
	return rows


def security(ctx, tasks, view_groups: list[dict[str, Any]], *, published: dict[str, Any]) -> dict[str, Any] | None:
	from kentender_procurement.bid_submission.services import tender_security

	pairs = [(g, v) for g, v in zip(ctx.model.groups_of("company"), view_groups) if g.rule_id == security_matching.SECURITY_RULE]
	if not pairs:
		return None
	group, shown = pairs[0]
	facts = tender_security.response(ctx)
	return {
		"key": shown["key"], "fields": shown["fields"], "published_facts": [{"label": "Amount · published", "value": facts["required_amount"]}, {"label": "Currency · published", "value": facts["currency"]}],
		"entered": bool(facts.get("security_type")), "physical": physical(facts, published),
	}


def physical(facts: dict[str, Any], published: dict[str, Any]) -> dict[str, Any] | None:
	"""The physical original as this supplier's own bid knows it: recorded (with
	the intake reference and time) or the amber delivery reminder; None until a
	security form is entered."""
	from kentender_procurement.bid_submission.services import tender_security

	if not facts.get("required") or not facts.get("security_type"):
		return None  # nothing entered yet: the region says so
	if facts["physical_receipt_status"] != tender_security.NOT_RECORDED:
		return {"tone": "live", "title": "Physical original recorded as received", "text": "", "facts": [{"label": "Receipt", "value": facts["physical_receipt_reference"]}, {"label": "Received at", "value": facts["physical_received_at"]}]}
	deadline = labels.datetime_label(published.get("submission_deadline"))
	entity = cstr(published.get("procuring_entity"))
	return {
		"tone": "warning", "title": "Physical original not yet recorded",
		"text": f"Deliver the original {facts['security_type'].lower()} to the {entity} procurement office before {deadline}. You may submit electronically, but failure to deliver the original before closing may disqualify the bid.",
		"facts": [],
	}


def signatory(ctx, *, at) -> dict[str, Any] | None:
	from kentender_procurement.bid_submission.services import signature

	arrangement = ctx.arrangement
	named = cstr(arrangement.authorised_signatory_assignment)
	rows = [supplier_gateway.assignment(assignment_id=named, at=at)] if named else supplier_gateway.organisation_signatories(organisation_id=ctx.workspace.lead_organisation, at=at)
	rows = [r for r in rows if r]
	if not rows:
		return None
	row = rows[0]
	certificate = None
	if gateways.trust_healthy():
		found = signature.certificate(row["user"], ctx.workspace.lead_organisation, at)
		certificate = {"status": "Ready" if found.get("status") == "Ready" else "Required", "tone": "live" if found.get("status") == "Ready" else "attention"}
	evidence = cstr(row.get("authority_evidence_id"))
	joint = arrangement.arrangement_type == "Joint venture"
	lead = cstr((supplier_gateway.organisation(organisation_id=ctx.workspace.lead_organisation) or {}).get("legal_name"))
	return {
		"name": _name(row["user"]), "job_title": cstr(row.get("job_title")), "organisation": f"{lead} (lead)" if joint else "", "authority_available": bool(evidence),
		"authority_href": f"/api/method/kentender_suppliers.supplier_accounts.api.download_account_evidence?organisation={ctx.workspace.lead_organisation}&evidence={evidence}&inline=1" if evidence and not joint else "",
		"certificate": None if joint else certificate,
	}


def view(ctx, tasks, task_view: dict[str, Any], *, at) -> dict[str, Any]:
	ws = ctx.workspace
	published = tenders_gateway.published_tender(ws.tender_reference, at=at) or {}
	groups = task_view["groups"]
	status = tasks["company"].status
	next_task = "requirements"
	return {
		"page": {"title": TITLE, "description": DESCRIPTION, "back_href": f"/tenders/{ws.tender_reference}/bid", "refs_line": f"{ws.tender_reference} · {ws.name} · Draft Version {int(ws.current_draft_version or 0)}"},
		"badge": {"label": status, "tone": BADGE_TONES.get(status, "draft")},
		"organisation": organisation(ctx), "contact": contact(ctx), "declarations": declarations(ctx, tasks, groups),
		"tender_security": security(ctx, tasks, groups, published=published), "signatory": signatory(ctx, at=at),
		"footer": {"save_label": "Save and continue", "next_href": f"/tenders/{ws.tender_reference}/bid/{next_task}"},
	}
