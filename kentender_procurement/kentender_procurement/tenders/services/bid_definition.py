# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §4.5.4 / §7.2 `BuildPublishedBidDefinition` (plan D25).

Tenders owns the transaction; the exact installed STD release owns the
product rules. This module only translates one Tender Version (plus its
publication identity and effective addenda) into the STD
`TenderVersionProjection v1` and calls the shared
`CompilePublishedBidDefinition` (STD-TPL-IMP-001 v1.1) — it never builds
response, evaluation or contract rows itself and never parses a rendered
document (§16(28), TPR11-AC-007).

- `component_digests()` — the Version's response-schema, evaluation-contract
  and contract-projection digests, computed at submission from a compile
  against a placeholder publication identity. The compiled rows depend only
  on the Tender Version (never on the publication or package digest), so
  the same digests must reconcile at publication authorisation (§4.2, §4.6).
- `build()` — the complete definition for publication authorisation.
- `build_successor()` — the definition for an addendum: the current
  effective content plus the exact addendum, with every prior identity
  classified by the release's addendum-identity rules (§5.6).

Any unsupported control, missing mapping, digest mismatch or reconciliation
failure is one blocking result; nothing partial is returned or stored.
"""

from __future__ import annotations

import copy
import json
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import frappe
from frappe.utils import cstr, get_datetime, get_system_timezone, get_url, getdate

from kentender_procurement.procurement_requisitions.services import catalogue as req_catalogue
from kentender_procurement.std_templates.compiler.errors import STDTemplateError
from kentender_procurement.std_templates.services import runtime as std_runtime
from kentender_procurement.tenders.services import digest, serializer
from kentender_procurement.tenders.services import evidence as ev
from kentender_procurement.tenders.services import snapshot as snap
from kentender_procurement.tenders.services.errors import fail

PROJECTION_NAME = "TenderVersionProjection"
PLACEHOLDER_PUBLICATION = "UNPUBLISHED"
#: STD failure codes → the Tenders error each surfaces as (§8).
_CODE = {
	"STD_RELEASE_WITHDRAWN": "TND_TEMPLATE_RELEASE_WITHDRAWN",
	"STD_RELEASE_INTEGRITY_FAILED": "TND_TEMPLATE_RELEASE_INTEGRITY_FAILED",
	"STD_RENDERER_UNSUPPORTED": "TND_TEMPLATE_RELEASE_INTEGRITY_FAILED",
	"STD_RELEASE_NOT_AVAILABLE": "TND_TEMPLATE_UNAVAILABLE",
}
#: Addendum `affected_reference_key` → how the revised value enters the
#: successor projection (the non-material rows of `addenda.affected_references`).
_ADDENDUM_TARGETS = ("delivery_location", "tender_title", "inspection_location", "contract_contact_office", "pre_tender_meeting")


# --------------------------------------------------------------------------
# canonical value helpers (STD `canonical` validators)
# --------------------------------------------------------------------------


def _tz() -> ZoneInfo:
	return ZoneInfo(get_system_timezone() or "Africa/Nairobi")


def iso_datetime(value) -> str:
	"""Site-time (instants decision, 26 Sep 2026) → ISO with the site offset."""
	if not value:
		return ""
	dt = get_datetime(value)
	if dt.tzinfo is None:
		dt = dt.replace(tzinfo=_tz())
	return dt.replace(microsecond=0).isoformat()


def iso_date(value) -> str:
	return getdate(value).isoformat() if value else ""


def decimal_text(value) -> str:
	if value is None or value == "":
		return "0"
	d = Decimal(str(value))
	return format(d.normalize(), "f") if d != d.to_integral_value() else str(int(d))


def _int(value) -> int:
	try:
		return int(Decimal(str(value or 0)))
	except Exception:
		return 0


# --------------------------------------------------------------------------
# the projection
# --------------------------------------------------------------------------


def _canonical_value(control: str, value: Any) -> Any:
	"""STD canonical JSON admits no floats: a DECIMAL characteristic's value
	is a decimal string ("14.0"), an INTEGER one stays a whole number, and any
	other float becomes its decimal text."""
	if isinstance(value, dict):
		return {k: _canonical_value(control, v) for k, v in value.items()}
	if isinstance(value, list):
		return [_canonical_value(control, v) for v in value]
	if isinstance(value, bool):
		return value
	if control == "DECIMAL" and isinstance(value, (int, float)):
		return str(value)
	if isinstance(value, float):
		return int(value) if control == "INTEGER" and value.is_integer() else repr(value)
	return value


def _technical(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	out = []
	for order, row in enumerate(snapshot.get("technical_requirements") or [], start=1):
		characteristic = req_catalogue.CATALOGUE_BY_KEY.get(row.get("characteristic_key"))
		try:
			value = json.loads(row.get("required_value_json") or "{}")
		except ValueError:
			value = {}
		out.append(
			{
				"technical_requirement_id": cstr(row.get("technical_requirement_id")),
				"characteristic_key": cstr(row.get("characteristic_key")),
				"label": characteristic.label if characteristic else cstr(row.get("characteristic_key")),
				"comparison": cstr(row.get("comparison")),
				"control": characteristic.control if characteristic else "TEXT",
				"unit": cstr(row.get("unit") or (characteristic.unit if characteristic else "")),
				"options": [cstr(o) for o in (characteristic.options if characteristic else ())],
				"port_options": [cstr(o) for o in (getattr(characteristic, "port_options", ()) if characteristic else ())],
				"required_value": _canonical_value(characteristic.control if characteristic else "TEXT", value),
				"required_value_display": cstr(row.get("required_value_display")),
				"applies_to_scope": cstr(row.get("applies_to_scope") or "All items"),
				"applies_to_id": cstr(row.get("applies_to_id")),
				"row_order": order,
			}
		)
	return out


def _items(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	lines = {cstr(line.get("drawdown_line_id")): line for line in snapshot.get("drawdown_lines") or []}
	out = []
	for item in snapshot.get("items") or []:
		drawdown = lines.get(cstr(item.get("drawdown_line_id"))) or {}
		out.append(
			{
				"requisition_item_id": cstr(item.get("requisition_item_id")),
				"item_name": cstr(item.get("item_name")),
				"equipment_category": cstr(item.get("equipment_category")),
				"quantity": decimal_text(item.get("quantity")),
				"unit": cstr(item.get("unit") or "Each"),
				"delivery_location": cstr(item.get("delivery_location") or snapshot.get("delivery_location")),
				"latest_delivery_date": iso_date(item.get("latest_delivery_date") or snapshot.get("latest_delivery_date")),
				"drawdown_line_id": cstr(item.get("drawdown_line_id")),
				"plan_item_line_id": cstr(item.get("plan_item_line_id")),
				"source_line_id": cstr(drawdown.get("source_line_id")),
				"intended_use": cstr(item.get("intended_use")),
			}
		)
	return out


def _approval(tender, version) -> dict[str, Any] | None:
	if not version.approved_by or not version.approved_at:
		return None
	return {
		"official_name": cstr(frappe.db.get_value("User", version.approved_by, "full_name") or version.approved_by),
		"official_title": "Head of Procurement Function",
		"approved_date": iso_date(version.approved_at),
		"reference": f"{tender.tender_reference}-V{int(version.version_number)}",
	}


def projection(tender, version, *, publication_id: str, effective_addendum_ids=(), package_digest: str = "") -> dict[str, Any]:
	"""The exact `TenderVersionProjection v1` for `version` (§4.5.4)."""
	snapshot = snap.load(version)
	state = serializer.officer_state(version)
	contact_display, contact_address = serializer._office_display(state.get("contract_contact_office"))
	warranty = serializer.warranty_support(snapshot)
	county = bool(snapshot.get("county_resident_reservation"))
	experience = bool(state.get("past_experience_required"))
	performance = bool(state.get("performance_security_required"))
	after_sales = bool(state.get("after_sales_evidence_required"))
	return {
		"schema_version": 1,
		"projection": PROJECTION_NAME,
		"template_key": cstr(version.template_key),
		"expected_renderer_profile_id": cstr(version.renderer_profile_id),
		"publication": {"publication_id": cstr(publication_id), "effective_addendum_ids": [cstr(a) for a in effective_addendum_ids]},
		"tender": {
			"tender_id": cstr(tender.name), "tender_version_id": cstr(version.name), "reference": cstr(tender.tender_reference),
			"title": cstr(state.get("tender_title") or tender.requirement_title), "procurement_method": "Open Tender", "currency": "KES",
			"lotting_indicator": cstr(snapshot.get("lotting_indicator") or "Single lot"), "award_packages": _int(snapshot.get("award_packages") or 1),
			"issue_date": iso_date(state.get("issue_date")), "clarification_deadline": iso_datetime(state.get("clarification_deadline")),
			"submission_deadline": iso_datetime(state.get("submission_deadline")), "validity_days": _int(state.get("tender_validity_days")),
			"tender_security": {"required": True, "amount": decimal_text(state.get("tender_security_amount")), "currency": "KES"},
			"pre_tender_meeting": {"enabled": bool(state.get("pre_tender_meeting")), "details": serializer._meeting_details(state)},
			"approval": _approval(tender, version),
			"package_digest": cstr(package_digest or version.package_digest),
		},
		"procuring_entity": {
			"name": cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")), "address": contact_address, "contact_office": contact_display,
			"is_county_government": bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county")),
		},
		"platform": {"name": serializer.PLATFORM_NAME, "public_url": f"{get_url()}/tenders"},
		"requisition": {
			"requisition_id": cstr(snapshot.get("requisition_id") or tender.requisition), "reference": cstr(snapshot.get("requisition_reference")),
			"requirement_title": cstr(snapshot.get("requirement_title")), "plan_item_reference": cstr(snapshot.get("plan_item_id")),
			"handoff_id": cstr(snapshot.get("handoff") or version.requisition_handoff), "handoff_version": cstr(snapshot.get("handoff_version")),
			"procurement_category": cstr(snapshot.get("procurement_category")), "product_pattern": cstr(snapshot.get("product_pattern")),
			"plan_horizon": cstr(snapshot.get("plan_horizon")),
		},
		"reservation": {
			"category": cstr(snapshot.get("reservation_category_value") or "None"),
			"county_residents": "County residents" if county else "Not applicable",
			"rule_snapshot_ids": [cstr(i) for i in (snapshot.get("reservation_rule_snapshot_ids") or []) if i],
			"overlap_treatment": "County residents within the reserved category" if county else "Not applicable",
		},
		"items": _items(snapshot),
		"technical_requirements": _technical(snapshot),
		"warranty_support": {
			"minimum_warranty_months": _int(snapshot.get("minimum_warranty_months")), "onsite_support_required": bool(warranty["onsite_support_required"]),
			"maximum_support_response_hours": _int(snapshot.get("maximum_support_response_hours")), "manufacturer_support_required": bool(warranty["manufacturer_support_required"]),
			"service_location_constraint": warranty["service_location_constraint"], "support_description": warranty["support_description"],
		},
		"related_services": [
			{
				"service_requirement_id": cstr(r.get("service_requirement_id")), "service_type": cstr(r.get("service_type")), "applies_to_scope": cstr(r.get("applies_to_scope") or "All items"),
				"applies_to_id": cstr(r.get("applies_to_id")), "required_result": cstr(r.get("required_result")), "quantity_or_coverage": cstr(r.get("quantity_or_coverage")),
				"completion_date": iso_date(r.get("completion_date")), "acceptance_evidence": cstr(r.get("acceptance_evidence")),
			}
			for r in snapshot.get("related_services") or []
		],
		"acceptance_requirements": [
			{
				"acceptance_requirement_id": cstr(r.get("acceptance_requirement_id")), "check_type": cstr(r.get("check_type")), "pass_condition": cstr(r.get("pass_condition")),
				"evidence_type": cstr(r.get("evidence_type")), "applies_to_scope": cstr(r.get("applies_to_scope") or "All items"), "applies_to_id": cstr(r.get("applies_to_id")),
			}
			for r in snapshot.get("acceptance_requirements") or []
		],
		"supporting_materials": [
			{
				"supporting_material_id": cstr(m["supporting_material_id"]), "title": cstr(m["title"]), "document_type": cstr(m["document_type"]),
				"treatment": cstr(m["treatment"]), "file_digest": cstr(m["file_digest"]), "linked_requirement_ids": [cstr(i) for i in m["linked_requirement_id_list"]],
			}
			for m in serializer.supporting_materials(snapshot)
		],
		"officer_decisions": {
			"submission": {
				"manufacturer_authorisation_required": bool(state.get("manufacturer_authorisation_required")),
				"datasheet_required": bool(state.get("datasheets_required")),
				"comparable_experience": {"required": experience, "count": _int(state.get("minimum_comparable_contracts")) if experience else 0, "period_years": _int(state.get("experience_period_years")) if experience else 0},
				"after_sales_support_required": after_sales,
				"after_sales_support_evidence": serializer._after_sales_text(state) if after_sales else "",
			},
			"evidence_requirements": [
				{
					"evidence_requirement_id": cstr(r["evidence_requirement_id"]), "label": cstr(r["label"]), "evidence_type": cstr(r["evidence_type"]),
					"linked_requirement_type": cstr(r["linked_requirement_type"]), "linked_requirement_id": cstr(r["linked_requirement_id"]), "mandatory": bool(r["mandatory"]),
				}
				for r in ev.rows_as_dicts(version)
			],
			"contract": {
				"payment_days": _int(state.get("payment_timing_days")),
				"performance_security": {"required": performance, "percentage": decimal_text(state.get("performance_security_percent")) if performance else "0"},
				"delay_damages": {"rate_per_week": decimal_text(state.get("delay_damages_per_week_percent")), "cap_percent": decimal_text(state.get("maximum_delay_damages_percent"))},
				"inspection_acceptance_office": cstr(state.get("inspection_location")), "contact_office": contact_display,
			},
		},
	}


def apply_addenda(base: dict[str, Any], addenda: list[Any]) -> dict[str, Any]:
	"""The effective projection: `base` with each addendum's revised value and
	any revised deadline applied in addendum order (§5.6)."""
	out = copy.deepcopy(base)
	for row in addenda:
		key = cstr(row.get("affected_reference_key"))
		value = cstr(row.get("revised_value"))
		if key == "delivery_location":
			for item in out["items"]:
				item["delivery_location"] = value
		elif key == "tender_title":
			out["tender"]["title"] = value
		elif key == "inspection_location":
			out["officer_decisions"]["contract"]["inspection_acceptance_office"] = value
		elif key == "contract_contact_office":
			out["officer_decisions"]["contract"]["contact_office"] = value
		elif key == "pre_tender_meeting":
			out["tender"]["pre_tender_meeting"]["details"] = value
		if row.get("deadline_extension_required") and row.get("revised_submission_deadline"):
			out["tender"]["submission_deadline"] = iso_datetime(row.get("revised_submission_deadline"))
	return out


# --------------------------------------------------------------------------
# compile
# --------------------------------------------------------------------------


def _compile(release_id: str, proj: dict[str, Any]) -> dict[str, Any]:
	try:
		return std_runtime.compile_published_bid_definition_for(release_id, proj)
	except STDTemplateError as exc:
		code = _CODE.get(exc.code, "TND_MAPPING_INCOMPLETE")
		fail(code, detail={"reason": exc.message, "std_code": exc.code, "identity": cstr(exc.identity), "template_release_id": release_id})
	return {}  # unreachable


def component_digests_of(definition: dict[str, Any]) -> dict[str, str]:
	"""§4.2 / §4.6 — each component digest covers exactly the matching
	content of the Published Bid Definition. `sections` is excluded: its
	groups carry the publication identity and effective addendum list (the
	document-acknowledgement task), which do not exist until publication;
	the definition digest still covers them."""
	return {
		"response_schema_digest": digest.sha256_hex({"response_rows": definition["response_rows"], "price_rows": definition["price_rows"], "declaration_texts": definition["declaration_texts"]}),
		"evaluation_contract_digest": digest.sha256_hex({"evaluation_mappings": definition["evaluation_mappings"], "reservation_treatment": definition["reservation_treatment"]}),
		"contract_projection_digest": digest.sha256_hex({"contract_mappings": definition["contract_mappings"]}),
	}


def technical_mapping_sets(definition: dict[str, Any]) -> dict[str, set[str]]:
	"""§5.8(6) — the technical requirement ids that have a supplier response,
	an evaluation mapping and a contract mapping in the compiled definition."""
	technical = {r["response_id"]: cstr(r["identity"]["immutable_source_id"]) for r in definition["response_rows"] if r["identity"]["source_family"] == "technical_requirement"}
	evaluated = {rid for m in definition["evaluation_mappings"] for rid in m["response_ids"]}
	contracted = {rid for m in definition["contract_mappings"] for rid in m["response_ids"]}
	return {
		"supplier response": set(technical.values()),
		"evaluation": {source for rid, source in technical.items() if rid in evaluated},
		"contract": {source for rid, source in technical.items() if rid in contracted},
	}


def compile_version(tender, version) -> dict[str, Any]:
	"""The Version's definition against the placeholder publication (review
	and submission; §4.2)."""
	proj = projection(tender, version, publication_id=PLACEHOLDER_PUBLICATION, package_digest=cstr(version.package_digest) or "0" * 64)
	return _compile(cstr(version.template_release_id), proj)


def component_digests(tender, version) -> dict[str, str]:
	"""The Version's component digests (submission; placeholder publication)."""
	return component_digests_of(compile_version(tender, version))


def build(tender, version, *, publication_id: str) -> dict[str, Any]:
	"""`BuildPublishedBidDefinition` for publication authorisation: the
	complete definition, reconciled with the approved Version's component
	digests. Raises one blocking §8 result on any failure."""
	definition = _compile(cstr(version.template_release_id), projection(tender, version, publication_id=publication_id))
	components = component_digests_of(definition)
	mismatched = [field for field, value in components.items() if cstr(version.get(field)) and cstr(version.get(field)) != value]
	if mismatched:
		fail("TND_MAPPING_INCOMPLETE", detail={"reason": "The compiled supplier definition does not reconcile with the approved Tender Version.", "digests": mismatched})
	if definition["package_digest"] != cstr(version.package_digest):
		fail("TND_PUBLICATION_DIGEST_MISMATCH", detail={"reason": "The compiled definition does not carry the approved package digest."})
	return {"definition": definition, "components": components}


def build_successor(tender, version, *, publication_id: str, prior: dict[str, Any], issued_addenda: list[Any], candidate) -> dict[str, Any]:
	"""The complete successor definition for `candidate` (an addendum awaiting
	issue) over every already-issued addendum, with every prior response
	identity classified (`unchanged` / `converted` / `fresh_response_required`
	/ `removed` / `new`) and the required responses bidders must complete
	afresh listed."""
	from kentender_procurement.std_templates.compiler import addenda as std_addenda

	release_id = cstr(version.template_release_id)
	effective_ids = [cstr(a.get("name")) for a in issued_addenda] + [cstr(candidate.name)]
	base = projection(tender, version, publication_id=publication_id, effective_addendum_ids=effective_ids)
	successor = _compile(release_id, apply_addenda(base, list(issued_addenda) + [candidate]))
	try:
		rules = std_runtime.installed_assets(std_runtime.release_doc(release_id)).addendum_rules
		classifications = std_addenda.classify(prior, successor, rules)
		incomplete = std_addenda.incomplete_required(successor, classifications)
	except STDTemplateError as exc:
		fail(_CODE.get(exc.code, "TND_MAPPING_INCOMPLETE"), detail={"reason": exc.message, "std_code": exc.code, "identity": cstr(exc.identity)})
		return {}  # unreachable
	# `incomplete` is not a failure: it lists the required responses bidders
	# must complete afresh under the successor (§5.6: labels, order and text
	# similarity never migrate a bidder response).
	return {"definition": successor, "classifications": classifications, "fresh_required": incomplete, "components": component_digests_of(successor)}


# --------------------------------------------------------------------------
# storage (plan W4)
# --------------------------------------------------------------------------


def store(tender, version, *, definition: dict[str, Any], publication: str, addendum: str = "", status: str = "Frozen", at=None) -> Any:
	from kentender_procurement.tenders.services import clock, envelope

	components = component_digests_of(definition)
	return envelope.insert(
		frappe.get_doc(
			{
				"doctype": "Tender Bid Definition", "tender": tender.name, "tender_version": version.name, "publication": publication, "addendum": addendum or None,
				"bid_definition_id": definition["bid_definition_id"], "definition_version": int(definition["definition_version"]), "definition_digest": definition["definition_digest"],
				"status": status, "definition_json": digest.canonical_json(definition), **components, "frozen_at": at or clock.now(),
				"effective_at": (at or clock.now()) if status == "Effective" else None, "record_version": 0, "fixture_namespace": tender.fixture_namespace,
			}
		)
	)


def current(tender_name: str) -> dict[str, Any] | None:
	"""The bidder-current definition: the one Effective row (§5.6: a frozen
	successor is never current while channel confirmation is outstanding)."""
	name = frappe.db.get_value("Tender Bid Definition", {"tender": tender_name, "status": "Effective"}, "name", order_by="definition_version desc")
	if not name:
		return None
	row = frappe.get_doc("Tender Bid Definition", name)
	return {"name": row.name, "bid_definition_id": row.bid_definition_id, "definition_version": int(row.definition_version), "definition_digest": row.definition_digest, "definition": json.loads(row.definition_json or "{}")}


def activate(tender, row_name: str, *, at) -> None:
	"""Make `row_name` the bidder-current definition and supersede the prior
	Effective one, atomically (called inside the final confirmation)."""
	from kentender_procurement.tenders.services import envelope

	for name in frappe.get_all("Tender Bid Definition", filters={"tender": tender.name, "status": "Effective", "name": ("!=", row_name)}, pluck="name"):
		envelope.bump(frappe.get_doc("Tender Bid Definition", name), status="Superseded")
	row = frappe.get_doc("Tender Bid Definition", row_name)
	if row.status != "Effective":
		envelope.bump(row, status="Effective", effective_at=at)
