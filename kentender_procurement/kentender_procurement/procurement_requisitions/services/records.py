# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared Requisition record helpers (REQ-CHG-001 v1.11): loading, the
DB-free projections `validation.py` and the digest read, the one-open-slot
guard and the contributor edit scope.

Everything that decides *who may change what* on a Draft lives here once:
- every contributing department's Author/HoD may edit that department's own
  approved-requirement and equipment rows (§7.3A);
- shared request and package content, and routing, need Draft authority in
  the lead department (§7.3A, REQ-DES-03-CONTRIBUTOR).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_requisitions.services import envelope
from kentender_procurement.procurement_requisitions.services import requisition_authorization as authz
from kentender_procurement.procurement_requisitions.services.errors import fail
from kentender_procurement.procurement_requisitions.services.requisition_roles import ROLE_DEPARTMENTAL_AUTHOR, ROLE_HEAD_OF_USER_DEPARTMENT

#: §5.1 — the states in which a root occupies its Plan Item's open slot.
OPEN_STATES = ("Draft", "Awaiting Department Approval", "Submitted to Procurement", "Authorised")

_BOOKKEEPING = frozenset({"name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "parent", "parentfield", "parenttype", "doctype"})


#: REQ v1.18 §5.7A — fields added to a child row after Versions were already locked. A row that holds no value for
#: one is dumped exactly as before, so a Version locked earlier keeps its content digest.
_OMIT_WHEN_EMPTY = frozenset({"applies_to_item_ids_json"})


def child_rows(doc, fieldname: str) -> list[dict[str, Any]]:
	return [
		{k: v for k, v in row.as_dict().items() if k not in _BOOKKEEPING and not (k in _OMIT_WHEN_EMPTY and not v)}
		for row in doc.get(fieldname) or []
	]


#: The commands that put the actor's work into a Draft. The Requisition Command Journal is the immutable
#: record of who ran them (RG-14, REQ v1.14 §7.3: "prepared" is every officer who edited the Draft).
EDIT_COMMANDS = (
	"PrepareITEquipmentRequisition", "SaveRequisitionSummary", "AddSameSpecificationItems", "UpdateSharedItemDetails",
	"UpdateRequisitionItem", "RemoveRequisitionItem", "SaveRequirementProposalDraft", "ApplySelectedRequirementPackage",
	"ResetStandardValues", "SaveWarrantyAndSupport",
	"AddTechnicalRequirement", "UpdateTechnicalRequirement", "RemoveTechnicalRequirement", "CustomiseRequirementForItem",
	"AddRelatedService", "UpdateRelatedService", "RemoveRelatedService",
	"AddAcceptanceRequirement", "UpdateAcceptanceRequirement", "RemoveAcceptanceRequirement",
	"AddSupportingMaterial", "UpdateSupportingMaterial", "RemoveSupportingMaterial",
)


def draft_editors(requisition: str) -> set[str]:
	"""Every officer who ran an editing command on any Version of this
	Requisition, from the Command Journal (a copied Draft carries earlier
	Versions' work forward, so their editors count too)."""
	if not requisition:
		return set()
	rows = frappe.db.sql(
		"""select distinct j.actor from `tabRequisition Command Journal` j
		where j.command in %(commands)s and j.actor is not null and j.actor != ''
		and ((j.document_type = 'Procurement Requisition' and j.document_name = %(requisition)s)
			or (j.document_type = 'Requisition Version' and j.document_name in (
				select v.name from `tabRequisition Version` v where v.requisition = %(requisition)s))
			or (j.document_type = 'IT Equipment Requirement Package Version' and j.document_name in (
				select pv.name from `tabIT Equipment Requirement Package Version` pv
				inner join `tabIT Equipment Requirement Package` p on p.name = pv.package
				where p.requisition = %(requisition)s)))""",
		{"commands": EDIT_COMMANDS, "requisition": cstr(requisition)},
	)
	return {cstr(r[0]) for r in rows}


def prepared_directly(version, actor: str) -> bool:
	"""REQ v1.14 §7.1 — the actor prepared this Requisition in the Head of User Department capacity."""
	return bool(actor) and cstr(version.get("prepared_by")) == actor and cstr(version.get("prepared_capacity")) == ROLE_HEAD_OF_USER_DEPARTMENT


def certifier_conflict(version, actor: str, *, direct: bool = False) -> bool:
	"""§7.3 bullet 1 / REQ19-AC-045 — an actor who prepared, edited or sent the
	Version as a Departmental Author cannot also complete the Head of User
	Department decision on it, unless they hold that role independently and
	prepared the Requisition directly in that capacity. `direct` is the
	Draft-state submit (§7.1: "Head of User Department preparing directly"): no
	approval task exists, so only that preparing Head may certify, never another
	Head. One rule for every submit path and for the offers that mirror it."""
	if prepared_directly(version, actor) and cstr(version.get("sent_for_approval_by")) != actor:
		return False
	if direct:
		return True
	prepared_by, sent_by = cstr(version.get("prepared_by")), cstr(version.get("sent_for_approval_by"))
	return actor in (prepared_by, sent_by) or actor in draft_editors(cstr(version.get("requisition")))


def authoriser_conflict(version, actor: str) -> bool:
	"""§7.3 bullet 4 / REQ19-AC-045 — the Procurement authoriser cannot also be
	the departmental submitting authority, and cannot authorise a Version they
	prepared or edited themselves (no self-authorisation)."""
	if not actor:
		return False
	return actor in (cstr(version.get("submitted_by")), cstr(version.get("prepared_by"))) or actor in draft_editors(cstr(version.get("requisition")))


def unit_name(unit: str) -> str:
	if not unit:
		return ""
	for field in ("unit_name", "organisation_unit_name", "title"):
		if frappe.db.has_column("Organisation Unit", field):
			value = frappe.db.get_value("Organisation Unit", unit, field)
			if value:
				return cstr(value)
	return cstr(unit)


def version_dict(version) -> dict[str, Any]:
	lines = child_rows(version, "drawdown_lines")
	for line in lines:
		line["department_name"] = unit_name(line.get("contributing_org_unit"))
	return {
		"requirement_title": version.requirement_title,
		"delivery_location": version.delivery_location,
		"latest_delivery_date": cstr(version.latest_delivery_date),
		"related_services_required": bool(version.related_services_required),
		"drawdown_lines": lines,
	}


def package_dict(package_version) -> dict[str, Any]:
	return {
		"minimum_warranty_months": package_version.minimum_warranty_months or None,
		"onsite_support_required": bool(package_version.onsite_support_required),
		"maximum_support_response_hours": package_version.maximum_support_response_hours or None,
		"manufacturer_support_required": bool(package_version.manufacturer_support_required),
		"service_location_constraint": package_version.service_location_constraint,
		"support_description": package_version.support_description,
		"standard_profile_key": package_version.standard_profile_key,
		"standard_profile_version": package_version.standard_profile_version,
		"standard_package_review_state": package_version.standard_package_review_state or "Not generated",
		"items": child_rows(package_version, "items"),
		"technical_requirements": child_rows(package_version, "technical_requirements"),
		"related_services": child_rows(package_version, "related_services"),
		"acceptance_requirements": child_rows(package_version, "acceptance_requirements"),
		"supporting_materials": child_rows(package_version, "supporting_materials"),
	}


def digest_payload(version, package_version) -> dict[str, Any]:
	payload = {"version": version_dict(version), "package": package_dict(package_version)}
	for line in payload["version"]["drawdown_lines"]:
		line.pop("department_name", None)
	return payload


def load(requisition: str) -> tuple[Any, Any, Any]:
	root = frappe.get_doc("Procurement Requisition", requisition)
	version = frappe.get_doc("Requisition Version", root.current_version)
	package_version = frappe.get_doc("IT Equipment Requirement Package Version", version.package_version)
	return root, version, package_version


def require_root(requisition: str, *, lock: bool = True):
	if not requisition or not frappe.db.exists("Procurement Requisition", requisition):
		authz.not_found()
	return envelope.locked("Procurement Requisition", requisition) if lock else frappe.get_doc("Procurement Requisition", requisition)


def contributing_units(root) -> set[str]:
	return {row.organisation_unit for row in root.contributing_org_units}


def require_draft(version, package_version) -> None:
	if version.version_status != "Draft" or package_version.version_status != "Draft":
		fail("REQ_STALE_VERSION", "This requisition is no longer a Draft. Review the latest version before saving.")


# --------------------------------------------------------------------------
# Edit scope (§7.3A)
# --------------------------------------------------------------------------


def draft_units(actor: str, candidates: set[str]) -> set[str]:
	"""The contributing departments this actor holds live Draft authority in."""
	from kentender_core.services.authorization import PURPOSE_COMMAND, authorise_record

	units = set()
	for unit in candidates:
		for role in (ROLE_HEAD_OF_USER_DEPARTMENT, ROLE_DEPARTMENTAL_AUTHOR):
			if authorise_record(user=actor, business_role=role, organisation_unit=unit, purpose=PURPOSE_COMMAND).allowed:
				units.add(unit)
				break
	return units


def edit_scope(root, actor: str) -> dict[str, Any]:
	units = draft_units(actor, contributing_units(root))
	lead = cstr(root.lead_org_unit_id)
	return {"units": units, "shared": lead in units, "lead": lead}


def require_edit_units(root, actor: str) -> dict[str, Any]:
	scope = edit_scope(root, actor)
	if not scope["units"]:
		authz.not_found()
	return scope


def require_shared(scope: dict[str, Any]) -> None:
	if not scope["shared"]:
		fail("REQ_RESPONSIBILITY_REQUIRED", "Only the submitting department can change the shared request and requirements.")


def require_unit(scope: dict[str, Any], unit: str) -> None:
	if unit not in scope["units"]:
		fail("REQ_RESPONSIBILITY_REQUIRED", "You can change only your own department's approved requirement and equipment.")


# --------------------------------------------------------------------------
# Lead department (§5.1, §7.3A)
# --------------------------------------------------------------------------


def default_lead(lines: list[dict[str, Any]]) -> str:
	"""Largest drawn value aggregated by contributing department; ties go to
	the sorted stable OU identity."""
	from kentender_procurement.procurement_requisitions.services import precision

	def aggregate(field: str) -> dict[str, Any]:
		totals: dict[str, Any] = {}
		for line in lines:
			unit = line.get("contributing_org_unit") or ""
			totals[unit] = totals.get(unit, 0) + precision.stored_money(line.get(field))
		return totals

	totals = aggregate("requested_value")
	# v1.15 §7.3A: until a valid estimated total cost exists the established rule
	# is applied to what remains on each line, which is what the v1.14 default
	# produced; once estimates exist it follows them.
	if not totals or max(totals.values()) <= 0:
		totals = aggregate("remaining_value")
	if not totals:
		return ""
	best = max(totals.values())
	return sorted(unit for unit, value in totals.items() if value == best)[0]


# --------------------------------------------------------------------------
# One open Requisition per stable Plan Item (§5.1)
# --------------------------------------------------------------------------


def open_root_for(plan_item_id: str) -> str:
	return cstr(frappe.db.get_value("Procurement Requisition", {"open_slot_key": cstr(plan_item_id)}, "name"))


def occupy_slot(root, plan_item_id: str) -> None:
	"""Take the slot atomically; the unique index is the authority, so a
	concurrent second Prepare fails here even if an earlier read missed it."""
	try:
		frappe.db.set_value("Procurement Requisition", root.name, "open_slot_key", cstr(plan_item_id), update_modified=False)
	except frappe.UniqueValidationError:
		fail("REQ_OPEN_EXISTS")
	except Exception as exc:  # noqa: BLE001 — pymysql IntegrityError on the unique index
		if "Duplicate entry" in str(exc):
			fail("REQ_OPEN_EXISTS")
		raise
	root.open_slot_key = cstr(plan_item_id)


def release_slot(root) -> None:
	root.open_slot_key = None
	frappe.db.set_value("Procurement Requisition", root.name, "open_slot_key", None, update_modified=False)


def decision_of(version_name: str, decision: str):
	name = frappe.db.get_value("Requisition Decision", {"requisition_version": version_name, "decision": decision}, "name", order_by="decided_at desc")
	return frappe.get_doc("Requisition Decision", name) if name else None


def json_list(value) -> list:
	try:
		parsed = json.loads(value or "[]")
	except (TypeError, ValueError):
		return []
	return parsed if isinstance(parsed, list) else []
