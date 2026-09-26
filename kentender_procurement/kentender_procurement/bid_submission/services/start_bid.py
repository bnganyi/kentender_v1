# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`StartBid` (BDS-CHG-001 v0.8 §4.3, §4.5, §5.1, §5.2 items 6–9 and §7.2).

The only MVP candidate registration. One committing command rechecks the
Tender's open state, the Active Account, the arrangement, the verified
mandatory-notice email, definition compatibility and uniqueness, then
creates the Tender-bound arrangement (whose identity is the candidate
registration Tenders consumes), its first notice-contact version, the
organisation snapshot and Draft Version 1 on the current definition,
together or not at all. Starting again for the same organisation returns
the existing bid. Starting does not submit a bid, establish eligibility or
show a Draft to the Procuring Entity."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import (
	bid_authorization as authz,
	clock,
	definition_runtime,
	records,
	references,
	snapshot,
	supplier_gateway,
	tenders_gateway,
)
from kentender_procurement.bid_submission.services.errors import MESSAGES, fail, field_errors

ARRANGEMENT = "Bidder Arrangement"
WORKSPACE = "Bid Workspace"
SINGLE = "Single organisation"
JOINT_VENTURE = "Joint venture"
AGREEMENT_EVIDENCE_TYPE = "Joint-venture agreement"


def _candidate_key(tender: str, organisation: str) -> str:
	return f"{tender}::{organisation}"


def _href(tender_reference: str) -> str:
	return f"/tenders/{tender_reference}/bid"


def _result(arrangement: str, *, created: bool) -> dict[str, Any]:
	row = frappe.db.get_value(ARRANGEMENT, arrangement, ["name", "tender_reference"], as_dict=True)
	workspace = frappe.db.get_value(WORKSPACE, {"bidder_arrangement": arrangement}, "name", order_by="creation desc")
	return {"ok": True, "created": created, "bidder_arrangement_id": row.name, "bid_reference": cstr(workspace), "href": _href(row.tender_reference)}


def start_bid(*, tender_reference: str, organisation: str = "", arrangement: dict | None = None, notice_contact_id: str = "", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	actor = authz.require_person(cstr(user or frappe.session.user))
	payload = {"tender_reference": cstr(tender_reference).strip(), "organisation": cstr(organisation).strip(), "arrangement": dict(arrangement or {}), "notice_contact_id": cstr(notice_contact_id).strip()}
	return records.idempotent(idempotency_key, "StartBid", payload, lambda: _start(actor=actor, **payload), actor=actor, organisation=payload["organisation"])


def _start(*, actor: str, tender_reference: str, organisation: str, arrangement: dict, notice_contact_id: str) -> dict[str, Any]:
	at = clock.now()
	root = tenders_gateway.tender_root(tender_reference)
	if not root:
		fail("BDS_TENDER_NOT_FOUND")
	assignment = authz.acting_assignment(actor, organisation, at=at)
	lead = assignment["organisation_id"]
	account = authz.active_account(lead)
	if tenders_gateway.availability(tender_reference, at=at) != "open":
		fail("BDS_TENDER_NOT_OPEN")
	existing = frappe.db.get_value(ARRANGEMENT, {"candidate_key": _candidate_key(root.name, lead)}, "name")
	if existing:
		return _result(existing, created=False)
	_require_portal_information()
	binding = definition_runtime.bind_current(root.name)
	problems, members, signatory = _check_arrangement(arrangement, lead=lead, options=definition_runtime.arrangement_options(binding["definition"]), at=at)
	if problems:
		return field_errors(problems, code="BDS_ARRANGEMENT_INVALID")
	contact = next((c for c in supplier_gateway.verified_contacts(organisation_id=lead) if c.get("contact_id") == notice_contact_id), None)
	if not contact:
		return field_errors({"notice_contact_id": MESSAGES["BDS_NOTICE_CONTACT_REQUIRED"]}, code="BDS_NOTICE_CONTACT_REQUIRED")
	with records.atomic("start-bid"):
		number = references.next_number(root.name)
		doc = _create_arrangement(root, number=number, account=account, arrangement=arrangement, members=members, signatory=signatory, contact=contact, actor=actor, at=at)
		workspace = _create_workspace(root, doc, number=number, binding=binding, actor=actor, at=at)
		records.emit(
			"BidStarted", tender=root.name, arrangement=doc.name, workspace=workspace.name, organisation=lead, actor=actor, at=at,
			payload={"arrangement_type": doc.arrangement_type, "bid_definition_id": binding["bid_definition_id"], "definition_version": binding["definition_version"], "notice_contact_version": 1},
		)
	return _result(doc.name, created=True)


def _require_portal_information() -> None:
	"""§8 `BDS_PORTAL_INFORMATION_UNAVAILABLE`: a new Start waits until the
	required support and legal links resolve (System setup, CFG-CHG-002)."""
	from kentender_core.services import public_portal

	if (public_portal.get_public_portal_information() or {}).get("status") != "Complete":
		fail("BDS_PORTAL_INFORMATION_UNAVAILABLE")


def _check_arrangement(arrangement: dict, *, lead: str, options: list[str], at) -> tuple[dict[str, str], list[dict[str, Any]], dict[str, Any] | None]:
	"""Field problems, the ordered member organisations (lead first, for a
	joint venture) and the named signatory assignment."""
	problems: dict[str, str] = {}
	kind = cstr(arrangement.get("arrangement_type")).strip()
	if kind not in options:
		return {"arrangement_type": "Choose how your organisation is bidding: " + " or ".join(options).lower() + "."}, [], None
	signatory = None
	signatory_id = cstr(arrangement.get("signatory_assignment_id")).strip()
	if signatory_id:
		signatory = authz.active_signatory(signatory_id, lead, at=at)
		if not signatory:
			problems["signatory_assignment_id"] = "Choose an active Authorised Signatory of the lead organisation."
	if kind == SINGLE:
		return problems, [], signatory
	name = cstr(arrangement.get("joint_venture_name")).strip()
	if not (3 <= len(name) <= 160):
		problems["joint_venture_name"] = "Enter the joint-venture name."
	if not signatory_id:
		problems["signatory_assignment_id"] = "Choose the Authorised Signatory who will sign for the joint venture."
	evidence_id = cstr(arrangement.get("agreement_evidence_id")).strip()
	if not any(e.get("evidence_id") == evidence_id and e.get("status") == "Available" for e in supplier_gateway.account_evidence(organisation_id=lead)):
		problems["agreement_evidence_id"] = "Choose the joint-venture agreement or letter of intent from the lead organisation's account evidence."
	rows = arrangement.get("members") or []
	if not rows:
		problems["members"] = "Add each other member of the joint venture."
	members: list[dict[str, Any]] = [{"organisation_id": lead}]
	for index, row in enumerate(rows):
		found = supplier_gateway.find_active_account(country=cstr((row or {}).get("country")).strip(), registration_number=cstr((row or {}).get("registration_number")).strip())
		if not found:
			problems[f"members.{index}"] = "No active supplier account has this country and registration number. The member must set up its own account first."
		elif found["organisation_id"] == lead:
			problems[f"members.{index}"] = "The lead organisation is already part of the joint venture."
		elif any(m["organisation_id"] == found["organisation_id"] for m in members):
			problems[f"members.{index}"] = "This member is listed more than once."
		else:
			members.append({"organisation_id": found["organisation_id"]})
	return problems, members, signatory


def _create_arrangement(root, *, number: int, account: dict, arrangement: dict, members: list[dict], signatory: dict | None, contact: dict, actor: str, at) -> Any:
	doc = frappe.get_doc({
		"doctype": ARRANGEMENT, "bidder_arrangement_id": references.arrangement_id(root.tender_reference, number), "tender": root.name, "tender_reference": root.tender_reference,
		"candidate_key": _candidate_key(root.name, account["organisation_id"]), "arrangement_type": cstr(arrangement.get("arrangement_type")).strip(),
		"lead_organisation": account["organisation_id"], "lead_legal_name": account["legal_name"],
		"joint_venture_name": cstr(arrangement.get("joint_venture_name")).strip() if members else "",
		"agreement_evidence": cstr(arrangement.get("agreement_evidence_id")).strip() if members else "",
		"authorised_signatory_assignment": (signatory or {}).get("assignment_id", ""),
		"tender_contact_user": actor, "tender_contact_name": cstr(frappe.utils.get_fullname(actor)), "tender_contact_email": actor, "tender_contact_phone": "",
		"candidate_registered_at": at, "mandatory_notice_email": contact["value"], "notice_contact_version": 1, "status": "Active", "status_since": at,
		"created_by": actor, "record_version": 0,
	})
	for order, member in enumerate(members, start=1):
		facts = supplier_gateway.organisation(organisation_id=member["organisation_id"]) or {}
		doc.append("members", {"member_order": order, "organisation_id": member["organisation_id"], "legal_name": facts.get("legal_name", ""), "country": facts.get("country", ""), "registration_number": facts.get("registration_number", "")})
	doc.append("notice_contacts", {"notice_contact_version": 1, "email": contact["value"], "contact_id": contact["contact_id"], "contact_version": int(contact.get("contact_version") or 1), "set_by": actor, "set_at": at})
	return records.insert(doc)


def _create_workspace(root, arrangement, *, number: int, binding: dict, actor: str, at) -> Any:
	reference = references.bid_reference(root.tender_reference, number)
	taken = snapshot.take(arrangement=arrangement, workspace=reference, version=1, actor=actor, at=at)
	return records.insert(frappe.get_doc({
		"doctype": WORKSPACE, "bid_reference": reference, "tender": root.name, "tender_reference": root.tender_reference, "bidder_arrangement": arrangement.name,
		"active_key": f"{root.name}::{arrangement.name}", "lead_organisation": arrangement.lead_organisation,
		"bid_definition_id": binding["bid_definition_id"], "definition_version": binding["definition_version"], "definition_digest": binding["definition_digest"],
		"organisation_snapshot": taken.name, "organisation_snapshot_version": 1, "status": "Draft", "status_since": at, "current_draft_version": 1,
		"created_by": actor, "created_at": at, "record_version": 0,
	}))
