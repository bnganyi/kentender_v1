# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`TenderVersionProjection v1` — the one canonical input both projections
of a released STD are built from (STD-TPL-001 v0.10 §5.4, §13.7).

The projection carries the exact authorised Requisition facts, the finite
Procurement Officer decisions and the publication identity, in canonical
types (ISO dates, decimal strings, stable identifiers). `validate()` refuses
any unknown or missing key; `document_context()` derives the Jinja context
the Invitation and issued-Tender masters render from; the compiler derives
the Published Bid Definition from the same projection. The curation fixture
(`04_fixture/moh_input.json`) and the production Tenders adapter produce
exactly this shape. Pure Python: no Frappe import.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from kentender_procurement.std_templates.compiler import formats
from kentender_procurement.std_templates.compiler.canonical import (
	canonical_json,
	decimal_string,
	decimal_text,
	iso_date,
	iso_datetime,
	short_hash,
	to_decimal,
)
from kentender_procurement.std_templates.compiler.errors import fail

PROJECTION_NAME = "TenderVersionProjection"
PROJECTION_SCHEMA_VERSION = 1
ALL_ITEMS = "All items"

# ---------------------------------------------------------------------------
# structural schema: key -> type tag, nested dict, or [row schema]
# ---------------------------------------------------------------------------

STR, INT, BOOL, DEC, DATE, DATETIME, LIST_STR, JSON, OPT_STR = (
	"str", "int", "bool", "decimal", "date", "datetime", "list[str]", "json", "str|null",
)

_APPROVAL = {"official_name": STR, "official_title": STR, "approved_date": DATE, "reference": STR}

SCHEMA: dict[str, Any] = {
	"schema_version": INT,
	"projection": STR,
	"template_key": STR,
	"expected_renderer_profile_id": STR,
	"publication": {"publication_id": STR, "effective_addendum_ids": LIST_STR},
	"tender": {
		"tender_id": STR, "tender_version_id": STR, "reference": STR, "title": STR,
		"procurement_method": STR, "currency": STR, "lotting_indicator": STR, "award_packages": INT,
		"issue_date": DATE, "clarification_deadline": DATETIME, "submission_deadline": DATETIME,
		"validity_days": INT,
		"tender_security": {"required": BOOL, "amount": DEC, "currency": STR},
		"pre_tender_meeting": {"enabled": BOOL, "details": STR},
		"approval": ("optional", _APPROVAL),
		"package_digest": STR,
	},
	"procuring_entity": {"name": STR, "address": STR, "contact_office": STR, "is_county_government": BOOL},
	"platform": {"name": STR, "public_url": STR},
	"requisition": {
		"requisition_id": STR, "reference": STR, "requirement_title": STR, "plan_item_reference": STR,
		"handoff_id": STR, "handoff_version": STR, "procurement_category": STR, "product_pattern": STR,
		"plan_horizon": STR,
	},
	"reservation": {"category": STR, "county_residents": STR, "rule_snapshot_ids": LIST_STR, "overlap_treatment": STR},
	"items": [
		{
			"requisition_item_id": STR, "item_name": STR, "equipment_category": STR, "quantity": DEC, "unit": STR,
			"delivery_location": STR, "latest_delivery_date": DATE, "drawdown_line_id": STR, "plan_item_line_id": STR,
			"source_line_id": STR, "intended_use": STR,
		}
	],
	"technical_requirements": [
		{
			"technical_requirement_id": STR, "characteristic_key": STR, "label": STR, "comparison": STR, "control": STR,
			"unit": STR, "options": LIST_STR, "port_options": LIST_STR, "required_value": JSON,
			"required_value_display": STR, "applies_to_scope": STR, "applies_to_id": STR, "row_order": INT,
		}
	],
	"warranty_support": {
		"minimum_warranty_months": INT, "onsite_support_required": BOOL, "maximum_support_response_hours": INT,
		"manufacturer_support_required": BOOL, "service_location_constraint": STR, "support_description": STR,
	},
	"related_services": [
		{
			"service_requirement_id": STR, "service_type": STR, "applies_to_scope": STR, "applies_to_id": STR,
			"required_result": STR, "quantity_or_coverage": STR, "completion_date": DATE, "acceptance_evidence": STR,
		}
	],
	"acceptance_requirements": [
		{
			"acceptance_requirement_id": STR, "check_type": STR, "pass_condition": STR, "evidence_type": STR,
			"applies_to_scope": STR, "applies_to_id": STR,
		}
	],
	"supporting_materials": [
		{
			"supporting_material_id": STR, "title": STR, "document_type": STR, "treatment": STR, "file_digest": STR,
			"linked_requirement_ids": LIST_STR,
		}
	],
	"officer_decisions": {
		"submission": {
			"manufacturer_authorisation_required": BOOL, "datasheet_required": BOOL,
			"comparable_experience": {"required": BOOL, "count": INT, "period_years": INT},
			"after_sales_support_required": BOOL, "after_sales_support_evidence": STR,
		},
		"evidence_requirements": [
			{
				"evidence_requirement_id": STR, "label": STR, "evidence_type": STR, "linked_requirement_type": STR,
				"linked_requirement_id": STR, "mandatory": BOOL,
			}
		],
		"contract": {
			"payment_days": INT,
			"performance_security": {"required": BOOL, "percentage": DEC},
			"delay_damages": {"rate_per_week": DEC, "cap_percent": DEC},
			"inspection_acceptance_office": STR, "contact_office": STR,
		},
	},
}


def _check(value: Any, spec: Any, path: str) -> None:
	if isinstance(spec, tuple) and spec[0] == "optional":
		if value is None:
			return
		_check(value, spec[1], path)
		return
	if isinstance(spec, dict):
		if not isinstance(value, dict):
			fail("STD_INPUT_UNSUPPORTED", f"{path} must be an object.", identity=path)
		unknown = sorted(set(value) - set(spec))
		missing = sorted(set(spec) - set(value))
		if unknown:
			fail("STD_INPUT_UNSUPPORTED", f"{path} has unknown key(s): {', '.join(unknown)}.", identity=f"{path}.{unknown[0]}")
		if missing:
			fail("STD_INPUT_UNSUPPORTED", f"{path} is missing key(s): {', '.join(missing)}.", identity=f"{path}.{missing[0]}")
		for key, sub in spec.items():
			_check(value[key], sub, f"{path}.{key}")
		return
	if isinstance(spec, list):
		if not isinstance(value, list):
			fail("STD_INPUT_UNSUPPORTED", f"{path} must be a list.", identity=path)
		for index, row in enumerate(value):
			_check(row, spec[0], f"{path}[{index}]")
		return
	if spec == STR and not isinstance(value, str):
		fail("STD_INPUT_UNSUPPORTED", f"{path} must be text.", identity=path)
	if spec == INT and (isinstance(value, bool) or not isinstance(value, int)):
		fail("STD_INPUT_UNSUPPORTED", f"{path} must be a whole number.", identity=path)
	if spec == BOOL and not isinstance(value, bool):
		fail("STD_INPUT_UNSUPPORTED", f"{path} must be true or false.", identity=path)
	if spec == DEC:
		decimal_string(value, field=path)
	if spec == DATE:
		iso_date(value, field=path)
	if spec == DATETIME:
		iso_datetime(value, field=path)
	if spec == LIST_STR and (not isinstance(value, list) or not all(isinstance(v, str) for v in value)):
		fail("STD_INPUT_UNSUPPORTED", f"{path} must be a list of text values.", identity=path)
	if spec == JSON:
		canonical_json(value)


def validate(projection: dict[str, Any]) -> dict[str, Any]:
	"""Structural validation of a `TenderVersionProjection v1`; returns it."""
	_check(projection, SCHEMA, "projection")
	if projection["projection"] != PROJECTION_NAME or projection["schema_version"] != PROJECTION_SCHEMA_VERSION:
		fail("STD_INPUT_UNSUPPORTED", "Not a TenderVersionProjection v1.", identity="projection.projection")
	_unique(projection["items"], "requisition_item_id", "items")
	_unique(projection["technical_requirements"], "technical_requirement_id", "technical_requirements")
	_unique(projection["related_services"], "service_requirement_id", "related_services")
	_unique(projection["acceptance_requirements"], "acceptance_requirement_id", "acceptance_requirements")
	_unique(projection["officer_decisions"]["evidence_requirements"], "evidence_requirement_id", "evidence_requirements")
	item_ids = {i["requisition_item_id"] for i in projection["items"]}
	for family in ("technical_requirements", "related_services", "acceptance_requirements"):
		for row in projection[family]:
			if row["applies_to_scope"] != ALL_ITEMS and row["applies_to_id"] not in item_ids:
				fail("STD_INPUT_UNSUPPORTED", f"{family} row applies to an unknown item.", identity=row["applies_to_id"] or family)
	return projection


def _unique(rows: list[dict[str, Any]], key: str, label: str) -> None:
	seen: set[str] = set()
	for row in rows:
		if row[key] in seen:
			fail("STD_INPUT_UNSUPPORTED", f"Duplicate {key} in {label}.", identity=row[key])
		seen.add(row[key])


# ---------------------------------------------------------------------------
# shared derivations (used by both projections)
# ---------------------------------------------------------------------------


def item_names(projection: dict[str, Any]) -> dict[str, str]:
	return {i["requisition_item_id"]: i["item_name"] for i in projection["items"]}


def applies_to_label(row: dict[str, Any], projection: dict[str, Any]) -> str:
	if row["applies_to_scope"] == ALL_ITEMS or not row["applies_to_id"]:
		return ALL_ITEMS
	return item_names(projection).get(row["applies_to_id"], row["applies_to_id"])


def technical_ids_for_item(item_id: str, projection: dict[str, Any]) -> list[str]:
	return sorted(
		row["technical_requirement_id"]
		for row in projection["technical_requirements"]
		if row["applies_to_scope"] == ALL_ITEMS or row["applies_to_id"] == item_id
	)


def technical_evidence_required(technical_requirement_id: str, projection: dict[str, Any]) -> bool:
	"""Evidence is required against a technical row when the officer requires
	technical datasheets, or an additional evidence row is linked to it."""
	decisions = projection["officer_decisions"]
	if decisions["submission"]["datasheet_required"]:
		return True
	return any(
		row["linked_requirement_type"] == "Technical requirement" and row["linked_requirement_id"] == technical_requirement_id
		for row in decisions["evidence_requirements"]
	)


def goods_groups(projection: dict[str, Any]) -> list[dict[str, Any]]:
	"""STD-TPL-001 v0.10 §13.6 — Goods group only when category, approved
	specification set, unit, delivery location, latest delivery date,
	warranty/support treatment, reservation/County treatment, lot and currency
	are identical. Quantity is summed exactly and is not part of identity."""
	tender = projection["tender"]
	template_key = projection["template_key"]
	warranty_treatment = short_hash(canonical_json(projection["warranty_support"]), length=64)
	grouped: dict[str, dict[str, Any]] = {}
	for item in projection["items"]:
		key = {
			"currency": tender["currency"],
			"delivery_location": item["delivery_location"],
			"equipment_category": item["equipment_category"],
			"latest_delivery_date": item["latest_delivery_date"],
			"lotting_indicator": tender["lotting_indicator"],
			"reservation": {
				"category": projection["reservation"]["category"],
				"county_residents": projection["reservation"]["county_residents"],
			},
			"specification_set": technical_ids_for_item(item["requisition_item_id"], projection),
			"unit": item["unit"],
			"warranty_support_treatment": warranty_treatment,
		}
		canonical_key = canonical_json(key)
		grouped.setdefault(canonical_key, {"key": key, "items": []})["items"].append(item)
	groups = []
	for canonical_key, group in grouped.items():
		items = sorted(group["items"], key=lambda i: i["requisition_item_id"].encode("utf-8"))
		item_ids = [i["requisition_item_id"] for i in items]
		goods_group_id = "GDS-" + short_hash(template_key, tender["tender_version_id"], canonical_key, ",".join(item_ids))
		quantity = sum((to_decimal(i["quantity"], field="items.quantity") for i in items), Decimal(0))
		groups.append(
			{
				"goods_group_id": goods_group_id,
				"canonical_grouping_key": group["key"],
				"description": items[0]["item_name"],
				"equipment_category": items[0]["equipment_category"],
				"quantity": decimal_text(quantity),
				"unit": items[0]["unit"],
				"destination": items[0]["delivery_location"],
				"latest_delivery_date": items[0]["latest_delivery_date"],
				"minimum_warranty_months": projection["warranty_support"]["minimum_warranty_months"],
				"technical_requirement_ids": group["key"]["specification_set"],
				"source_lineage": [
					{
						"requisition_item_id": i["requisition_item_id"],
						"quantity": i["quantity"],
						"drawdown_line_id": i["drawdown_line_id"],
						"plan_item_line_id": i["plan_item_line_id"],
						"source_line_id": i["source_line_id"],
					}
					for i in items
				],
			}
		)
	groups.sort(key=lambda g: g["source_lineage"][0]["requisition_item_id"].encode("utf-8"))
	return groups


def validity_date(projection: dict[str, Any]) -> str:
	tender = projection["tender"]
	return formats.add_days(formats.eat_date(tender["submission_deadline"]), tender["validity_days"])


# ---------------------------------------------------------------------------
# the document (Jinja) context
# ---------------------------------------------------------------------------

PENDING_APPROVAL = {
	"official_name": "To be confirmed at approval",
	"official_title": "Head of Procurement Function",
	"approved_date": "Pending approval",
	"reference": "Pending approval",
}


def _display_required_value(row: dict[str, Any]) -> str:
	display = row["required_value_display"]
	unit = row["unit"]
	if unit and display.endswith(f" {unit}"):
		display = display[: -len(unit) - 1]
	return display


def document_context(projection: dict[str, Any], constants: dict[str, Any]) -> dict[str, Any]:
	"""The exact context the released masters render from. `constants` are
	the release's `document_constants` (product profile)."""
	validate(projection)
	tender = projection["tender"]
	decisions = projection["officer_decisions"]
	submission = decisions["submission"]
	contract = decisions["contract"]
	valid_until = validity_date(projection)
	extra_evidence = decisions["evidence_requirements"]
	approval = tender["approval"]
	services = projection["related_services"]
	return {
		"procuring_entity": {
			"name": projection["procuring_entity"]["name"],
			"address": projection["procuring_entity"]["address"],
			"contact_office": projection["procuring_entity"]["contact_office"],
		},
		"requisition": {
			"reference": projection["requisition"]["reference"],
			"requirement_title": projection["requisition"]["requirement_title"],
			"related_services_authorized": bool(services),
		},
		"reservation": {"category": projection["reservation"]["category"]},
		"tender": {
			"reference": tender["reference"],
			"title": tender["title"],
			"procurement_method": tender["procurement_method"],
			"issue_date": formats.long_date(tender["issue_date"]),
			"clarification_deadline": formats.eat_datetime(tender["clarification_deadline"]),
			"submission_deadline": formats.eat_datetime(tender["submission_deadline"]),
			"validity_days": str(tender["validity_days"]),
			"validity_date": formats.long_date(valid_until),
			"opening_datetime": formats.eat_datetime(tender["submission_deadline"]),
			"currency": tender["currency"],
			"tender_security": {
				"type": "Tender Security",
				"currency": tender["tender_security"]["currency"],
				"amount": formats.money(tender["tender_security"]["amount"], field="tender.tender_security.amount"),
				"bank_guarantee_expiry_date": formats.long_date(formats.add_days(valid_until, constants["bank_guarantee_extra_days"])),
				"insurance_guarantee_expiry_date": formats.long_date(formats.add_days(valid_until, constants["insurance_guarantee_extra_days"])),
			},
			"pre_tender_meeting": dict(tender["pre_tender_meeting"]),
			"approval": (
				{
					"official_name": approval["official_name"],
					"official_title": approval["official_title"],
					"approved_date": formats.long_date(approval["approved_date"]),
					"reference": approval["reference"],
				}
				if approval
				else dict(PENDING_APPROVAL)
			),
		},
		"platform": dict(projection["platform"]),
		"submission": {
			"manufacturer_authorisation_required": submission["manufacturer_authorisation_required"],
			"datasheet_required": submission["datasheet_required"],
			"comparable_experience": {
				"required": submission["comparable_experience"]["required"],
				"count": str(submission["comparable_experience"]["count"]) if submission["comparable_experience"]["required"] else "",
				"period_years": str(submission["comparable_experience"]["period_years"]) if submission["comparable_experience"]["required"] else "",
			},
			"after_sales_support_required": submission["after_sales_support_required"],
			"after_sales_support_evidence": submission["after_sales_support_evidence"] if submission["after_sales_support_required"] else "",
			"additional_evidence": {
				"required": bool(extra_evidence),
				"description": "; ".join(row["label"] for row in extra_evidence),
				"linked_requirement": "; ".join(row["linked_requirement_id"] for row in extra_evidence),
			},
		},
		"contract": {
			"payment_terms": f"Payment within {contract['payment_days']} days after delivery, inspection, acceptance and receipt of a valid invoice",
			"payment_days": str(contract["payment_days"]),
			"performance_security": {
				"required": contract["performance_security"]["required"],
				"percentage": formats.number(contract["performance_security"]["percentage"]) if contract["performance_security"]["required"] else "",
				"form_variant": constants["performance_security_form_variant"],
			},
			"delay_damages": {
				"rate_per_week": formats.number(contract["delay_damages"]["rate_per_week"]),
				"cap_percent": formats.number(contract["delay_damages"]["cap_percent"]),
			},
			"inspection_acceptance_office": contract["inspection_acceptance_office"],
			"contact_office": contract["contact_office"],
		},
		"goods": [
			{
				"source_item_ids": ", ".join(s["requisition_item_id"] for s in group["source_lineage"]),
				"description": group["description"],
				"quantity": group["quantity"],
				"unit": group["unit"],
				"destination": group["destination"],
				"latest_delivery_date": formats.long_date(group["latest_delivery_date"]),
				"minimum_warranty": f"{group['minimum_warranty_months']} months",
			}
			for group in goods_groups(projection)
		],
		"related_services": [
			{
				"service_requirement_id": row["service_requirement_id"],
				"service_type": row["service_type"],
				"required_result": row["required_result"],
				"applies_to": applies_to_label(row, projection),
				"completion_date": formats.long_date(row["completion_date"]),
				"acceptance_evidence": row["acceptance_evidence"],
			}
			for row in services
		],
		"technical_requirements": [
			{
				"technical_requirement_id": row["technical_requirement_id"],
				"label": row["label"],
				"comparison": row["comparison"],
				"required_value": _display_required_value(row),
				"unit": row["unit"],
				"applies_to": applies_to_label(row, projection),
				"evidence_required": technical_evidence_required(row["technical_requirement_id"], projection),
			}
			for row in sorted(projection["technical_requirements"], key=lambda r: r["row_order"])
		],
		"warranty_support": {
			"minimum_warranty_months": str(projection["warranty_support"]["minimum_warranty_months"]),
			"onsite_support_required": projection["warranty_support"]["onsite_support_required"],
			"maximum_support_response_hours": str(projection["warranty_support"]["maximum_support_response_hours"]),
			"manufacturer_support_required": projection["warranty_support"]["manufacturer_support_required"],
			"service_location_constraint": projection["warranty_support"]["service_location_constraint"],
			"support_description": projection["warranty_support"]["support_description"],
		},
		"acceptance_requirements": [
			{
				"acceptance_requirement_id": row["acceptance_requirement_id"],
				"check_type": row["check_type"],
				"pass_condition": row["pass_condition"],
				"evidence_type": row["evidence_type"],
				"applies_to": applies_to_label(row, projection),
			}
			for row in projection["acceptance_requirements"]
		],
		"supporting_materials": [
			{
				"supporting_material_id": row["supporting_material_id"],
				"title": row["title"],
				"document_type": row["document_type"],
				"treatment": row["treatment"],
				"linked_requirement_ids": ", ".join(row["linked_requirement_ids"]),
			}
			for row in projection["supporting_materials"]
		],
	}
