# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One bid, as the runtime sees it (BDS-CHG-001 v0.8 §4.4.5, §4.4.8, §4.5).

`load()` checks who is asking, then gathers the exact bound definition (its
digest verified against the one the Draft recorded), the saved answers, the
bid's evidence and the facts the bid never asks the bidder to type: the
organisation snapshot, the arrangement (tenderer name, Tender contact), each
joint-venture member's snapshot and the signatory assignment. A person
outside the lead organisation gets Not found, never a hint that a bid exists
(§8 record-existence masking)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.bid_submission.services import bid_authorization as authz
from kentender_procurement.bid_submission.services import labels, supplier_gateway, tenders_gateway
from kentender_procurement.bid_submission.services.definition_model import DefinitionModel, Field
from kentender_procurement.bid_submission.services.errors import fail

WORKSPACE = "Bid Workspace"
SECTION = "Bid Section Response"
EVIDENCE = "Bid Evidence"
#: Supplied from the signatory who submits; nothing to fix before then.
AT_SUBMISSION = ("SV-SIGNATORY",)


@dataclass
class BidContext:
	workspace: Any
	arrangement: Any
	model: DefinitionModel
	values: dict[str, Any]
	sections: dict[str, Any]
	snapshot: dict[str, Any]
	evidence: dict[str, list[dict[str, Any]]]
	signatory: dict[str, Any] | None
	actor: str
	assignment: dict[str, Any]
	# a read sets this when the Draft cannot change now (closed, or its bound
	# release is Withdrawn or fails its checks): every field reads as fixed
	read_only: bool = False

	# -- values -------------------------------------------------------------
	def supplied_value(self, field: Field):
		source, fact = field.supplied["source_id"], field.supplied["fact"]
		if source == "SV-ORGANISATION":
			return (self.snapshot.get("organisation") or {}).get(fact) or None
		if source == "SV-ARRANGEMENT-MEMBER":
			member = next((m for m in self.snapshot.get("members") or [] if m.get("organisation_id") == field.member), {})
			return member.get(fact) or None
		if source == "SV-ARRANGEMENT":
			a = self.arrangement
			facts = {
				"tenderer_name": cstr(a.joint_venture_name) or cstr(a.lead_legal_name), "arrangement_type": a.arrangement_type,
				"tender_contact_name": cstr(a.tender_contact_name), "tender_contact_email": cstr(a.tender_contact_email), "tender_contact_phone": cstr(a.tender_contact_phone),
			}
			return facts.get(fact) or None
		if source == "SV-SIGNATORY":
			return (self.signatory or {}).get(fact) or None
		return None

	def value(self, field: Field):
		if field.supplied:
			return self.supplied_value(field)
		if field.kind == "evidence":
			files = [e["id"] for e in self.evidence.get(field.key, []) if e["scan_status"] == "Accepted"]
			return files or None
		return self.values.get(field.key)

	def group_values(self, field: Field) -> dict[str, Any]:
		return {f.field_key: self.value(f) for f in field.group.fields}

	@property
	def tenderer_name(self) -> str:
		return cstr(self.arrangement.joint_venture_name) or cstr(self.arrangement.lead_legal_name)


def _signatory(arrangement) -> dict[str, Any] | None:
	assignment = supplier_gateway.assignment(assignment_id=cstr(arrangement.authorised_signatory_assignment)) if arrangement.authorised_signatory_assignment else None
	if not assignment:
		return None
	return {"full_name": labels.person_name(cstr(assignment.get("user"))), "job_title": cstr(assignment.get("job_title"))}


def evidence_of(workspace: str) -> dict[str, list[dict[str, Any]]]:
	out: dict[str, list[dict[str, Any]]] = {}
	for row in frappe.get_all(EVIDENCE, filters={"bid_workspace": workspace, "status": "Current"}, fields=["name", "evidence_requirement", "original_filename", "scan_status", "scan_result", "size_bytes", "uploaded_at", "source_evidence"], order_by="uploaded_at asc, creation asc", limit_page_length=0):
		out.setdefault(row.evidence_requirement, []).append({"id": row.name, "name": row.original_filename, "scan_status": row.scan_status, "scan_result": cstr(row.scan_result), "size_bytes": int(row.size_bytes or 0), "uploaded_at": row.uploaded_at, "source": cstr(row.source_evidence)})
	return out


def workspace_for(bid_reference: str, *, actor: str, organisation: str = "", at=None) -> tuple[Any, dict[str, Any]]:
	"""The workspace and the actor's preparing assignment, or Not found."""
	authz.require_person(actor)
	try:
		assignment = authz.acting_assignment(actor, organisation, at=at)
	except frappe.ValidationError:
		raise frappe.DoesNotExistError("This bid is unavailable or you do not have permission to view it.")
	lead = assignment["organisation_id"]
	if not bid_reference or not frappe.db.exists(WORKSPACE, {"name": bid_reference, "lead_organisation": lead}):
		raise frappe.DoesNotExistError("This bid is unavailable or you do not have permission to view it.")
	return frappe.get_doc(WORKSPACE, bid_reference), assignment


def load(bid_reference: str, *, actor: str, organisation: str = "", at=None) -> BidContext:
	workspace, assignment = workspace_for(bid_reference, actor=actor, organisation=organisation, at=at)
	arrangement = frappe.get_doc("Bidder Arrangement", workspace.bidder_arrangement)
	bound = tenders_gateway.definition_for(workspace.tender, workspace.definition_version)
	if not bound or bound["definition_digest"] != workspace.definition_digest or not tenders_gateway.verify_definition_digest(bound["definition"]):
		fail("BDS_DEFINITION_UNSUPPORTED")
	members = [m.organisation_id for m in arrangement.members]
	sections = {row.section_key: row for row in frappe.get_all(SECTION, filters={"bid_workspace": workspace.name}, fields=["name", "section_key", "values_json", "status", "blocker_count", "warning_count", "record_version"], limit_page_length=0)}
	values: dict[str, Any] = {}
	for row in sections.values():
		values.update(json.loads(row.values_json or "{}"))
	snapshot = json.loads(frappe.db.get_value("Bid Organisation Snapshot", workspace.organisation_snapshot, "facts_json") or "{}")
	return BidContext(
		workspace=workspace, arrangement=arrangement, model=DefinitionModel(bound["definition"], members=members), values=values, sections=sections,
		snapshot=snapshot, evidence=evidence_of(workspace.name), signatory=_signatory(arrangement), actor=actor, assignment=assignment,
	)
