# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The finite, code-owned source selectors and applicability rules a released
response rule may name (STD-TPL-001 v0.10 §13.5.2 `source_selector`,
`applicability`).

A selector turns the projection into zero or more source instances, each with
an immutable source identity, the read-only published facts the bidder sees,
boolean source flags a named required rule may test, and the source lineage.
A release cannot add a selector: a new one is a code change reviewed with a
new release. Pure Python: no Frappe import.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from kentender_procurement.std_templates.compiler import formats, projection as proj

Instance = dict[str, Any]


@dataclass(frozen=True)
class SelectorSpec:
	families: tuple[str, ...]
	parameters: tuple[str, ...]
	facts: tuple[str, ...]
	flags: tuple[str, ...]
	select: Callable[[dict[str, Any], dict[str, Any], dict[str, Any]], list[Instance]]
	#: The characteristic kinds a CHARACTERISTIC field of this selector may
	#: resolve to: None = none (the placeholder is not allowed), ALL_KINDS =
	#: every released characteristic control (technical requirements).
	characteristic_kinds: tuple[str, ...] | None = None


ALL_KINDS: tuple[str, ...] = ("*",)


def _instance(source_id: str, facts: dict[str, Any], lineage: dict[str, Any], flags: dict[str, bool] | None = None) -> Instance:
	return {"immutable_source_id": source_id, "facts": facts, "lineage": lineage, "flags": dict(flags or {})}


def _document_package(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	t = p["tender"]
	facts = {
		"tender_reference": t["reference"],
		"tender_title": t["title"],
		"tender_version_id": t["tender_version_id"],
		"publication_id": p["publication"]["publication_id"],
		"effective_addendum_ids": list(p["publication"]["effective_addendum_ids"]),
	}
	return [_instance("DOCUMENT-PACKAGE", facts, {"tender_id": t["tender_id"], "tender_version_id": t["tender_version_id"]})]


def _supplier(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	return [_instance("SUPPLIER", {"tender_reference": p["tender"]["reference"]}, {"tender_id": p["tender"]["tender_id"]})]


def _declaration(p: dict[str, Any], params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	form_id = params["form_id"]
	return [_instance(form_id, {"form_id": form_id, "tender_reference": p["tender"]["reference"]}, {"form_id": form_id})]


def _tender_security(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	t = p["tender"]
	valid_until = proj.validity_date(p)
	facts = {
		"amount": t["tender_security"]["amount"],
		"currency": t["tender_security"]["currency"],
		"validity_date": valid_until,
		"bank_guarantee_expiry_date": formats.add_days(valid_until, constants["bank_guarantee_extra_days"]),
		"insurance_guarantee_expiry_date": formats.add_days(valid_until, constants["insurance_guarantee_extra_days"]),
		"permitted_forms": ["Demand Bank Guarantee", "Insurance Guarantee"],
	}
	return [_instance("TENDER-SECURITY", facts, {"tender_version_id": t["tender_version_id"]})]


def _reservation(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	r = p["reservation"]
	facts = {
		"category": r["category"],
		"rule_snapshot_ids": list(r["rule_snapshot_ids"]),
		"permitted_categories": [r["category"]],
		"submission_deadline_date": formats.eat_date(p["tender"]["submission_deadline"]),
	}
	return [_instance("RESERVATION", facts, {"rule_snapshot_ids": list(r["rule_snapshot_ids"]), "requisition_id": p["requisition"]["requisition_id"]})]


def _goods_groups(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	out = []
	for index, g in enumerate(proj.goods_groups(p), start=1):
		facts = {
			"line": str(index),
			"description": g["description"],
			"equipment_category": g["equipment_category"],
			"quantity": g["quantity"],
			"unit": g["unit"],
			"destination": g["destination"],
			"latest_delivery_date": g["latest_delivery_date"],
			"minimum_warranty_months": g["minimum_warranty_months"],
			"currency": p["tender"]["currency"],
			"technical_requirement_ids": list(g["technical_requirement_ids"]),
		}
		out.append(_instance(g["goods_group_id"], facts, {"source_lineage": g["source_lineage"]}))
	return out


def _technical(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	out = []
	for row in sorted(p["technical_requirements"], key=lambda r: r["row_order"]):
		facts = {
			"label": row["label"],
			"characteristic_key": row["characteristic_key"],
			"comparison": row["comparison"],
			"control": row["control"],
			"required_value": row["required_value"],
			"required_value_display": row["required_value_display"],
			"unit": row["unit"],
			"options": list(row["options"]),
			"port_options": list(row["port_options"]),
			"applies_to": proj.applies_to_label(row, p),
		}
		flags = {"evidence_required": proj.technical_evidence_required(row["technical_requirement_id"], p)}
		lineage = {"technical_requirement_id": row["technical_requirement_id"], "applies_to_scope": row["applies_to_scope"], "applies_to_id": row["applies_to_id"]}
		out.append(_instance(row["technical_requirement_id"], facts, lineage, flags))
	return out


#: Release 1.2 (BDS-CHG-001 v0.8 OD-E; STD-TPL-001 §8.3 "Confirmation and the
#: applicable offered value" per warranty/support fact): each published
#: obligation that applies becomes its own row, in this fixed order.
_WARRANTY_OBLIGATIONS: tuple[tuple[str, str, str, str, str, str], ...] = (
	("WS-MINIMUM-WARRANTY", "minimum_warranty_months", "Minimum warranty period", "Minimum", "INTEGER", "months"),
	("WS-ONSITE-SUPPORT", "onsite_support_required", "On-site support", "Required", "YES_NO", ""),
	("WS-RESPONSE-TIME", "maximum_support_response_hours", "Maximum support response time", "Maximum", "INTEGER", "hours"),
	("WS-MANUFACTURER-SUPPORT", "manufacturer_support_required", "Manufacturer support", "Required", "YES_NO", ""),
	("WS-SERVICE-LOCATION", "service_location_constraint", "Service location", "Required", "TEXT", ""),
	("WS-SUPPORT-CONTACTS", "support_description", "Warranty contact, escalation and service-centre details", "Required", "TEXT", ""),
)


def _warranty_obligations(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	w = p["warranty_support"]
	out = []
	for source_id, key, label, comparison, control, unit in _WARRANTY_OBLIGATIONS:
		value = w.get(key)
		if control == "YES_NO":
			if value is not True:
				continue
			required, display = "Yes", "Yes"
		elif control == "INTEGER":
			if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
				continue
			required, display = value, f"{value} {unit}".strip()
		else:
			if not isinstance(value, str) or not value.strip():
				continue
			required, display = value.strip(), value.strip()
		facts = {
			"obligation_key": key, "label": label, "comparison": comparison, "control": control, "unit": unit,
			"required_value": {"value": required}, "required_value_display": display,
		}
		out.append(_instance(source_id, facts, {"requisition_id": p["requisition"]["requisition_id"], "obligation_key": key}))
	return out


def _effective_addenda(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	"""Release 1.2 (STD-TPL-001 v0.12 §8.1): one acknowledgement per
	effective addendum, in effect order; none when no addendum is effective.
	Bid Submission names the addendum through the `addendum_reference`
	label parameter."""
	t = p["tender"]
	return [
		_instance(addendum_id, {"addendum_id": addendum_id}, {"tender_version_id": t["tender_version_id"], "addendum_id": addendum_id})
		for addendum_id in p["publication"]["effective_addendum_ids"]
	]


def _arrangement_members(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	"""Release 1.2: the one template group Bid Submission repeats for each
	member of the bidder's joint-venture arrangement (per_arrangement_member)."""
	return [_instance("JV-MEMBER", {"tender_reference": p["tender"]["reference"]}, {"tender_id": p["tender"]["tender_id"]})]


def _warranty(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	w = p["warranty_support"]
	return [_instance("WARRANTY-SUPPORT", dict(w), {"requisition_id": p["requisition"]["requisition_id"]})]


def _experience(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	exp = p["officer_decisions"]["submission"]["comparable_experience"]
	if not exp["required"]:
		return []
	window_end = formats.eat_date(p["tender"]["submission_deadline"])
	end = window_end.split("-")
	window_start = f"{int(end[0]) - exp['period_years']:04d}-{end[1]}-{end[2]}"
	if window_start.endswith("-02-29"):
		window_start = window_start[:-2] + "28"
	out = []
	for number in range(1, exp["count"] + 1):
		facts = {"entry_number": number, "required_count": exp["count"], "period_years": exp["period_years"], "window_start": window_start, "window_end": window_end}
		out.append(_instance(f"EXPERIENCE-{number:02d}", facts, {"tender_version_id": p["tender"]["tender_version_id"]}))
	return out


def _related_services(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	out = []
	for index, row in enumerate(p["related_services"], start=1):
		facts = {
			"line": f"S{index}",
			"service_type": row["service_type"],
			"required_result": row["required_result"],
			"quantity_or_coverage": row["quantity_or_coverage"],
			"completion_date": row["completion_date"],
			"acceptance_evidence": row["acceptance_evidence"],
			"applies_to": proj.applies_to_label(row, p),
			"currency": p["tender"]["currency"],
			"quantity": "1",
			"unit": "service",
			"description": f"{row['service_type']} — {row['required_result']}",
		}
		out.append(_instance(row["service_requirement_id"], facts, {"service_requirement_id": row["service_requirement_id"]}))
	return out


def _acceptance(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	return [
		_instance(
			row["acceptance_requirement_id"],
			{"check_type": row["check_type"], "pass_condition": row["pass_condition"], "evidence_type": row["evidence_type"], "applies_to": proj.applies_to_label(row, p)},
			{"acceptance_requirement_id": row["acceptance_requirement_id"]},
		)
		for row in p["acceptance_requirements"]
	]


_EVIDENCE_KINDS: dict[str, tuple[str, str]] = {
	"MANUFACTURER-AUTHORISATION": ("Manufacturer's authorisation", "Proves the Tenderer is duly authorised by the manufacturer or producer of the Goods offered."),
	"DATASHEET": ("Technical datasheets or brochures", "Proves the Goods offered conform to the published Technical Requirements."),
	"AFTER-SALES": ("After-sales support evidence", "Proves the Tenderer's capacity to provide after-sales support for the Goods offered."),
	"ELIGIBILITY-DOCUMENTS": ("Eligibility and registration documents", "Tax compliance, registration and constitution documents required by the Tenderer Information Form."),
}


def _evidence(p: dict[str, Any], params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	kind = params["evidence_kind"]
	label, purpose = _EVIDENCE_KINDS[kind]
	requirement_text = ""
	if kind == "AFTER-SALES":
		requirement_text = p["officer_decisions"]["submission"]["after_sales_support_evidence"]
	facts = {"evidence_kind": kind, "label": label, "purpose": purpose, "requirement_text": requirement_text}
	return [_instance(f"EVIDENCE-{kind}", facts, {"tender_version_id": p["tender"]["tender_version_id"]})]


def _evidence_additional(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	return [
		_instance(
			row["evidence_requirement_id"],
			{"label": row["label"], "evidence_type": row["evidence_type"], "linked_requirement_type": row["linked_requirement_type"], "linked_requirement_id": row["linked_requirement_id"]},
			{"evidence_requirement_id": row["evidence_requirement_id"], "linked_requirement_id": row["linked_requirement_id"]},
			{"mandatory": row["mandatory"]},
		)
		for row in p["officer_decisions"]["evidence_requirements"]
	]


def _submission(p: dict[str, Any], _params: dict[str, Any], constants: dict[str, Any]) -> list[Instance]:
	facts = {
		"tender_reference": p["tender"]["reference"],
		"tender_version_id": p["tender"]["tender_version_id"],
		"effective_addendum_ids": list(p["publication"]["effective_addendum_ids"]),
	}
	return [_instance("SUBMISSION", facts, {"tender_version_id": p["tender"]["tender_version_id"]})]


_DECLARATION_FACTS = ("form_id", "tender_reference", "text_id", "text_version", "source_text_digest", "resolved_text_digest")

SELECTORS: dict[str, SelectorSpec] = {
	"SEL-DOCUMENT-PACKAGE": SelectorSpec(("document",), (), ("tender_reference", "tender_title", "tender_version_id", "publication_id", "effective_addendum_ids"), (), _document_package),
	"SEL-SUPPLIER": SelectorSpec(("supplier",), (), ("tender_reference",), (), _supplier),
	"SEL-DECLARATION": SelectorSpec(("declaration",), ("form_id",), _DECLARATION_FACTS, (), _declaration),
	"SEL-TENDER-SECURITY": SelectorSpec(("tender_security",), (), ("amount", "currency", "validity_date", "bank_guarantee_expiry_date", "insurance_guarantee_expiry_date", "permitted_forms"), (), _tender_security),
	"SEL-RESERVATION": SelectorSpec(
		("reservation",), (),
		("category", "rule_snapshot_ids", "permitted_categories", "submission_deadline_date", "text_id", "text_version", "source_text_digest", "resolved_text_digest"),
		(), _reservation,
	),
	"SEL-GOODS-GROUPS": SelectorSpec(
		("goods", "price_row"), (),
		("line", "description", "equipment_category", "quantity", "unit", "destination", "latest_delivery_date", "minimum_warranty_months", "currency", "technical_requirement_ids"),
		(), _goods_groups,
	),
	"SEL-TECHNICAL-REQUIREMENTS": SelectorSpec(
		("technical_requirement",), (),
		("label", "characteristic_key", "comparison", "control", "required_value", "required_value_display", "unit", "options", "port_options", "applies_to"),
		("evidence_required",), _technical, ALL_KINDS,
	),
	"SEL-WARRANTY-OBLIGATIONS": SelectorSpec(
		("warranty_support",), (),
		("obligation_key", "label", "comparison", "control", "unit", "required_value", "required_value_display"),
		(), _warranty_obligations, ("INTEGER", "YES_NO", "TEXT"),
	),
	"SEL-EFFECTIVE-ADDENDA": SelectorSpec(("document",), (), ("addendum_id",), (), _effective_addenda),
	"SEL-ARRANGEMENT-MEMBERS": SelectorSpec(("supplier",), (), ("tender_reference",), (), _arrangement_members),
	"SEL-WARRANTY-SUPPORT": SelectorSpec(
		("warranty_support",), (),
		("minimum_warranty_months", "onsite_support_required", "maximum_support_response_hours", "manufacturer_support_required", "service_location_constraint", "support_description"),
		(), _warranty,
	),
	"SEL-EXPERIENCE-ENTRIES": SelectorSpec(("experience",), (), ("entry_number", "required_count", "period_years", "window_start", "window_end"), (), _experience),
	"SEL-RELATED-SERVICES": SelectorSpec(
		("related_service", "price_row"), (),
		("line", "service_type", "required_result", "quantity_or_coverage", "completion_date", "acceptance_evidence", "applies_to", "currency", "quantity", "unit", "description"),
		(), _related_services,
	),
	"SEL-ACCEPTANCE-REQUIREMENTS": SelectorSpec(("acceptance_requirement",), (), ("check_type", "pass_condition", "evidence_type", "applies_to"), (), _acceptance),
	"SEL-EVIDENCE": SelectorSpec(("evidence_requirement",), ("evidence_kind",), ("evidence_kind", "label", "purpose", "requirement_text"), (), _evidence),
	"SEL-EVIDENCE-ADDITIONAL": SelectorSpec(("evidence_requirement",), (), ("label", "evidence_type", "linked_requirement_type", "linked_requirement_id"), ("mandatory",), _evidence_additional),
	"SEL-SUBMISSION": SelectorSpec(("declaration",), (), ("tender_reference", "tender_version_id", "effective_addendum_ids"), (), _submission),
}

EVIDENCE_KINDS: tuple[str, ...] = tuple(_EVIDENCE_KINDS)


# ---------------------------------------------------------------------------
# rule-level applicability (named, bounded)
# ---------------------------------------------------------------------------


def _sub(p: dict[str, Any]) -> dict[str, Any]:
	return p["officer_decisions"]["submission"]


APPLICABILITY: dict[str, Callable[[dict[str, Any]], bool]] = {
	"AP-ALWAYS": lambda p: True,
	"AP-TENDER-SECURITY-REQUIRED": lambda p: p["tender"]["tender_security"]["required"],
	"AP-MANUFACTURER-AUTHORISATION-REQUIRED": lambda p: _sub(p)["manufacturer_authorisation_required"],
	"AP-DATASHEET-REQUIRED": lambda p: _sub(p)["datasheet_required"],
	"AP-COMPARABLE-EXPERIENCE-REQUIRED": lambda p: _sub(p)["comparable_experience"]["required"],
	"AP-AFTER-SALES-REQUIRED": lambda p: _sub(p)["after_sales_support_required"],
	"AP-RESERVATION-APPLIES": lambda p: p["reservation"]["category"] != "None",
	"AP-RELATED-SERVICES-PRESENT": lambda p: bool(p["related_services"]),
}
