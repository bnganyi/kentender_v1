# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""What a tender gives the contract (CM-CHG-001 v0.8 section 19.4; plan D20; tracker CM8-515): the issued instance, the schedules, the commercial conditions, the acceptance criteria and Form No. 4.

Additive and read-only: no Tenders rule, record or screen changes. Award lists these as the contract's sources (S1, S4, S5, S6, S7) and Contract Management reads them back through the core source
seam, verifying each against the digest Award froze, so a tender that changed after the award is seen. Every function reads the **issued** thing: the effective published bid definition (the
addenda already applied), the approved tender version's projection and the template release the tender was bound to, never the latest release. Typed values are only what the issued tender states as
values; a term that exists only as prose in the conditions is not invented as a value here (it stays out, and Contract Management reports the exact term as missing).

Each function returns a plain dict (or raises `Unavailable` with the reason, which Contract Management shows to the head of procurement)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

COMPARATORS = {"Minimum": ">=", "Maximum": "<=", "Required": "=", "Exact": "=", "Equal": "=", "At least": ">=", "At most": "<="}


class Unavailable(Exception):
	"""The tender owns this but cannot give it, and says why."""


def _root(tender: str):
	root = frappe.db.get_value("Tender", tender, ["name", "tender_reference", "requirement_title", "overall_status", "publication", "approved_version", "current_version", "template_key", "template_release",
		"template_release_id", "bundle_digest", "official_source_digest", "published_at"], as_dict=True)
	if not root or not root.published_at:
		raise Unavailable("The tender is not published.")
	return root


def _definition(tender: str) -> dict[str, Any]:
	from kentender_procurement.tenders.services import bid_definition

	stored = bid_definition.current(tender)
	if not stored or not stored.get("definition"):
		raise Unavailable("The tender has no published bid definition.")
	return stored


def _groups(body: dict[str, Any], rule: str) -> list[dict[str, Any]]:
	return [g for s in body.get("sections") or [] for g in s.get("groups") or [] if g.get("rule_id") == rule]


def _document(tender: str, kind: str, **filters) -> Any:
	rows = frappe.get_all("Tender Document", filters={"tender": tender, "kind": kind, **filters}, fields=["name", "digest", "html_file", "tender_version", "addendum", "generated_at"], order_by="creation desc", limit=1)
	return rows[0] if rows else None


def issued_instance(tender: str) -> dict[str, Any]:
	"""S1: the issued tender, its template release and its addenda (an empty list is stated, not left out)."""
	root = _root(tender)
	stored = _definition(tender)
	complete = _document(tender, "Complete Tender")
	if not complete:
		raise Unavailable("The issued tender document is not held.")
	addenda = []
	for a in frappe.get_all("Tender Addendum", filters={"tender": tender, "status": "Issued"}, fields=["name", "addendum_number", "addendum_reference", "change_class", "affected_area", "reason", "addendum_digest", "issued_at"], order_by="addendum_number asc"):
		notice = _document(tender, "Addendum notice", addendum=a.name)
		addenda.append({"id": a.name, "number": int(a.addendum_number or 0), "reference": a.addendum_reference, "change_class": a.change_class, "affected_area": a.affected_area, "reason": a.reason,
			"digest": a.addendum_digest, "issued_at": cstr(a.issued_at), "notice_digest": notice.digest if notice else ""})
	from kentender_procurement.tenders.services import evaluation_seam

	fact = evaluation_seam.publication_fact(tender) or {}
	return {
		"tender": root.name, "tender_reference": root.tender_reference, "title": cstr(fact.get("title") or root.requirement_title), "procurement_category": _category(stored),
		"release": cstr(root.template_key), "release_id": cstr(root.template_release_id), "template_release": cstr(root.template_release), "bundle_digest": cstr(root.bundle_digest),
		"official_source_digest": cstr(root.official_source_digest),
		"issued": {"version": cstr(complete.tender_version), "document": complete.name, "digest": complete.digest},
		"definition": {"id": stored.get("bid_definition_id"), "version": stored.get("definition_version"), "digest": stored.get("definition_digest")},
		"addenda": addenda,
	}


def _category(stored: dict[str, Any]) -> str:
	from kentender_procurement.tenders.services import snapshot as snap

	version = frappe.get_doc("Tender Version", stored["definition"]["tender_version_id"])
	return cstr(snap.load(version).get("procurement_category"))


def schedule_of_requirements(tender: str) -> dict[str, Any]:
	"""S4: the goods and delivery schedule (with any addendum applied), the technical requirements, the warranty and support obligations, the related services and the acceptance schedule."""
	_root(tender)
	body = _definition(tender)["definition"]
	goods = [g for g in _groups(body, "RR-PRICE-GOODS")]
	if not goods:
		raise Unavailable("The published definition carries no goods schedule.")
	lines, due = [], ""
	for g in goods:
		f = g.get("published_facts") or {}
		lines.append({"line": cstr(f.get("line")), "description": cstr(f.get("description")), "category": cstr(f.get("equipment_category")), "quantity": cstr(f.get("quantity")), "unit": cstr(f.get("unit")),
			"latest_delivery_date": cstr(f.get("latest_delivery_date")), "destination": cstr(f.get("destination")), "technical_requirement_ids": list(f.get("technical_requirement_ids") or []),
			"minimum_warranty_months": f.get("minimum_warranty_months")})
		due = max(due, cstr(f.get("latest_delivery_date")))
	technical = []
	for g in _groups(body, "RR-TECHNICAL"):
		f = g.get("published_facts") or {}
		technical.append({"id": cstr(g.get("immutable_source_id")), "label": cstr(f.get("label")), "characteristic": cstr(f.get("characteristic_key")), "comparison": cstr(f.get("comparison")),
			"required_value": (f.get("required_value") or {}).get("value"), "display": cstr(f.get("required_value_display")), "unit": cstr(f.get("unit")), "applies_to": cstr(f.get("applies_to"))})
	warranty = [{"id": cstr(g.get("immutable_source_id")), "label": cstr((g.get("published_facts") or {}).get("label")), "obligation": cstr((g.get("published_facts") or {}).get("obligation_key")),
		"required_value": ((g.get("published_facts") or {}).get("required_value") or {}).get("value"), "display": cstr((g.get("published_facts") or {}).get("required_value_display")),
		"unit": cstr((g.get("published_facts") or {}).get("unit"))} for g in _groups(body, "RR-WARRANTY-SUPPORT")]
	related = [{"id": cstr(g.get("immutable_source_id")), **{k: cstr(v) for k, v in (g.get("published_facts") or {}).items() if not isinstance(v, (list, dict))}} for g in _groups(body, "RR-RELATED-SERVICES")]
	return {"delivery_schedule": {"due": due, "destination": lines[0]["destination"], "lines": lines}, "technical": technical, "warranty_support": warranty, "related_services": related,
		"definition": {"version": _definition(tender).get("definition_version"), "digest": _definition(tender).get("definition_digest")}}


def acceptance_criteria(tender: str) -> dict[str, Any]:
	"""S6: the criteria inspection records against. Typed criteria are the technical requirements that state a comparison and a value; the acceptance checks the tender states only as text are carried
	as such, untyped, so nothing is invented as a measurable value."""
	_root(tender)
	body = _definition(tender)["definition"]
	criteria, untyped = [], []
	for g in _groups(body, "RR-TECHNICAL"):
		f = g.get("published_facts") or {}
		comparator = COMPARATORS.get(cstr(f.get("comparison")))
		value = (f.get("required_value") or {}).get("value")
		if comparator and value not in (None, ""):
			criteria.append({"id": cstr(g.get("immutable_source_id")), "name": cstr(f.get("label")), "comparator": comparator, "value": value, "unit": cstr(f.get("unit")), "line_id": "", "coverage": "every unit",
				"applies_to": cstr(f.get("applies_to")), "source": cstr(g.get("group_key"))})
	for g in _groups(body, "RR-ACCEPTANCE"):
		f = g.get("published_facts") or {}
		untyped.append({"id": cstr(g.get("immutable_source_id")), "check": cstr(f.get("check_type")), "pass_condition": cstr(f.get("pass_condition")), "evidence": cstr(f.get("evidence_type")), "applies_to": cstr(f.get("applies_to"))})
	if not criteria and not untyped:
		raise Unavailable("The tender states no acceptance criteria.")
	return {"criteria": criteria, "untyped": untyped}


def conditions(tender: str) -> dict[str, Any]:
	"""S5: the commercial values the issued tender states as values: payment timing, the performance security, delay damages and the warranty. A term the conditions state only in prose (an advance, remedies,
	termination, change) is left out rather than invented."""
	from kentender_procurement.tenders.services import bid_definition

	root = _root(tender)
	stored = _definition(tender)
	version = frappe.get_doc("Tender Version", stored["definition"]["tender_version_id"])
	projection = bid_definition.projection(frappe.get_doc("Tender", root.name), version, publication_id=cstr(stored["definition"].get("publication_id") or root.publication),
		effective_addendum_ids=stored["definition"].get("effective_addendum_ids") or ())
	contract = projection["officer_decisions"]["contract"]
	warranty = projection["warranty_support"]
	security = contract["performance_security"]
	out: dict[str, Any] = {
		"payment": {"days": contract["payment_days"], "source": "Special Conditions of Contract: payment timing"},
		"performance_security": {"required": bool(security["required"]), "percentage": security["percentage"], "source": "Special Conditions of Contract: performance security"},
		"delay_damages": {"rate_per_week_percent": contract["delay_damages"]["rate_per_week"], "cap_percent": contract["delay_damages"]["cap_percent"]},
		"warranty": {"months": warranty["minimum_warranty_months"], "onsite_support_required": warranty["onsite_support_required"], "maximum_support_response_hours": warranty["maximum_support_response_hours"],
			"manufacturer_support_required": warranty["manufacturer_support_required"]},
		"inspection_acceptance_office": contract["inspection_acceptance_office"], "contact_office": contract["contact_office"],
		"template": {"release_id": root.template_release_id, "version": root.template_release},
	}
	if not security["required"]:
		out["performance_security"]["statement"] = "Not required by the Special Conditions of Contract"
	else:
		out["performance_security"]["statement"] = f"{security['percentage']}% of the contract amount"
	return out


def form_no_4(tender: str) -> dict[str, Any]:
	"""S7: Form No. 4 (Contract Agreement) as the **issued** tender holds it, byte for byte from the heading to the next form, after the issued document is checked against its recorded digest. The release
	it came from is the one the tender was bound to, never the latest. The form's blanks are the form's own: this function declares no insertion for any of them (that is the template owner's, CM-TPL-01)."""
	import hashlib

	from kentender_core.services.file_integrity import read_bytes

	root = _root(tender)
	complete = _document(tender, "Complete Tender")
	if not complete or not complete.html_file:
		raise Unavailable("The issued tender document is not held.")
	data = read_bytes(complete.html_file)
	if hashlib.sha256(data).hexdigest() != complete.digest:
		raise Unavailable("The issued tender document no longer matches its recorded digest.")
	html = data.decode("utf-8")
	start = html.find("<h3>Form No. 4 - Contract Agreement</h3>")
	if start < 0:
		raise Unavailable("The issued tender has no Form No. 4.")
	end = html.find("<h3>", start + 10)
	return {"release_id": cstr(root.template_release_id), "release": cstr(root.template_release), "document": complete.name, "document_digest": complete.digest, "fragment": html[start:end if end > start else None]}
