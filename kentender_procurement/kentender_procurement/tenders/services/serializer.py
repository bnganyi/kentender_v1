# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §4.5 — the one canonical serializer (plan D4).

Every schedule, supplier-response definition (§4.5.1), evaluation contract
(§4.5.2), contract-obligation projection (§4.5.3), render context and
package digest is a projection of the Version's immutable snapshot plus its
officer values, computed here and nowhere else. Goods lines group
Requisition items that share one specification into one rendered line while
keeping every `requisition_item_id`, quantity and source allocation (owner
ruling 8 Sep 2026; STD-TPL-001 v0.6 §8.4(2); SEED-001 §5.2). Internal
policy context (Strategic objective, plan horizon, authorised value, funding
evidence) is carried under `_internal` only, never in a supplier-visible key
(§4.3). The render context reproduces the shape of the installed template's
own fixture (`tender_templates/it_equipment_open_v1/fixtures/moh_input.json`).
"""

from __future__ import annotations

import json
from datetime import timedelta
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, formatdate, get_datetime, get_system_timezone, getdate

from kentender_procurement.procurement_requisitions.services import catalogue as req_catalogue
from kentender_procurement.tenders.services import controls, digest
from kentender_procurement.tenders.services import snapshot as snap

TEMPLATE_DISPLAY_NAME = "IT Equipment — Open Tender"
PLATFORM_NAME = "KenTender"
FIXED_PRICE = True
TAX_TREATMENT = "Shown separately"
PERFORMANCE_SECURITY_FORM = "Unconditional Demand Bank Guarantee"
EVALUATION_STAGES = (
	"Submission and eligibility",
	"Pass/fail technical compliance",
	"Arithmetic and financial evaluation",
	"Award to the lowest evaluated responsive Tender",
)
BANK_GUARANTEE_EXTRA_DAYS = 30
INSURANCE_GUARANTEE_EXTRA_DAYS = 28
SUPPLIER = "Completed by supplier"
CALCULATED = "Calculated from supplier response"

# --------------------------------------------------------------------------
# formatting
# --------------------------------------------------------------------------


def fmt_date(value) -> str:
	return formatdate(getdate(value), "d MMMM yyyy") if value else ""


def fmt_date_short(value) -> str:
	return formatdate(getdate(value), "d MMM yyyy") if value else ""


def _eat(value):
	dt = get_datetime(value)
	if (get_system_timezone() or "").upper() == "UTC":
		from frappe.utils import convert_utc_to_timezone

		dt = convert_utc_to_timezone(dt, "Africa/Nairobi")
	return dt


def fmt_datetime_eat(value) -> str:
	"""Officer-entered datetimes are EAT wall-clock values; a stored UTC
	timestamp is converted. Renders "27 May 2027, 17:00 EAT"."""
	if not value:
		return ""
	dt = _eat(value)
	return f"{formatdate(dt.date(), 'd MMMM yyyy')}, {dt.strftime('%H:%M')} EAT"


def fmt_datetime_short(value) -> str:
	"""§10 screen vocabulary: "27 May 2027, 17:00 EAT"."""
	if not value:
		return ""
	dt = _eat(value)
	return f"{formatdate(dt.date(), 'd MMM yyyy')}, {dt.strftime('%H:%M')} EAT"


def fmt_money(value) -> str:
	return f"{Decimal(str(value or 0)).quantize(Decimal('0.01')):,.2f}"


def fmt_number(value) -> str:
	if value is None or value == "":
		return ""
	d = Decimal(str(value))
	if d == d.to_integral_value():
		return str(int(d))
	return f"{d.normalize():f}"


def fmt_quantity(value) -> str:
	return fmt_number(value)


# --------------------------------------------------------------------------
# inherited rows (display projections of the snapshot)
# --------------------------------------------------------------------------


def _item_names(snapshot: dict[str, Any]) -> dict[str, str]:
	return {row.get("requisition_item_id"): row.get("item_name") for row in snapshot.get("items") or []}


def _applies_to_label(row: dict[str, Any], snapshot: dict[str, Any]) -> str:
	if row.get("applies_to_scope") == "All items" or not row.get("applies_to_id"):
		return "All items"
	return _item_names(snapshot).get(row.get("applies_to_id")) or cstr(row.get("applies_to_id"))


def _tech_ids_for_item(item_id: str, snapshot: dict[str, Any]) -> tuple[str, ...]:
	return tuple(
		sorted(
			row.get("technical_requirement_id")
			for row in snapshot.get("technical_requirements") or []
			if row.get("applies_to_scope") == "All items" or not row.get("applies_to_id") or row.get("applies_to_id") == item_id
		)
	)


def technical_rows(snapshot: dict[str, Any], evidence_ids: set[str] | None = None) -> list[dict[str, Any]]:
	out = []
	for row in snapshot.get("technical_requirements") or []:
		characteristic = req_catalogue.CATALOGUE_BY_KEY.get(row.get("characteristic_key"))
		try:
			value_json = json.loads(row.get("required_value_json") or "{}")
		except ValueError:
			value_json = {}
		display = req_catalogue.display_value(characteristic, value_json) if characteristic and value_json else cstr(value_json.get("value") if isinstance(value_json, dict) else "")
		unit = cstr(row.get("unit") or (characteristic.unit if characteristic else ""))
		if unit and display.endswith(f" {unit}"):
			display = display[: -len(unit) - 1]
		out.append(
			{
				"technical_requirement_id": row.get("technical_requirement_id"),
				"label": characteristic.label if characteristic else cstr(row.get("characteristic_key")),
				"characteristic_key": row.get("characteristic_key"),
				"comparison": row.get("comparison"),
				"required_value": display,
				"unit": unit,
				"applies_to": _applies_to_label(row, snapshot),
				"control": characteristic.control if characteristic else "TEXT",
				"options": list(characteristic.options) if characteristic else [],
				"evidence_required": bool(evidence_ids and row.get("technical_requirement_id") in evidence_ids),
			}
		)
	return out


def goods_lines(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	"""One rendered line per group of items sharing one specification
	(item name + category + applicable technical rows + unit + destination
	+ date); every contributing `requisition_item_id`, quantity, source
	allocation and reservation kept (§4.5)."""
	groups: dict[tuple, dict[str, Any]] = {}
	destination = cstr(snapshot.get("delivery_location"))
	latest = snapshot.get("latest_delivery_date")
	months = snapshot.get("minimum_warranty_months")
	lines_by_id = {line.get("drawdown_line_id"): line for line in snapshot.get("drawdown_lines") or []}
	for item in snapshot.get("items") or []:
		item_id = item.get("requisition_item_id")
		key = (item.get("item_name"), item.get("equipment_category"), _tech_ids_for_item(item_id, snapshot), cstr(item.get("unit") or "Each"), destination, cstr(latest))
		group = groups.setdefault(
			key,
			{
				"description": item.get("item_name"), "equipment_category": item.get("equipment_category"), "quantity": 0.0,
				"unit": cstr(item.get("unit") or "Each"), "destination": destination, "latest_delivery_date": fmt_date(latest),
				"latest_delivery_date_iso": cstr(latest), "minimum_warranty": f"{fmt_number(months)} months", "minimum_warranty_months": months,
				"source_items": [], "technical_requirement_ids": list(key[2]),
			},
		)
		group["quantity"] += float(item.get("quantity") or 0)
		drawdown = lines_by_id.get(item.get("plan_item_line_id")) or {}
		group["source_items"].append(
			{
				"requisition_item_id": item_id, "quantity": item.get("quantity"), "plan_item_line_id": item.get("plan_item_line_id"),
				"intended_use": item.get("intended_use"), "source_line_id": drawdown.get("source_line_id"),
				"plan_source_allocation_id": drawdown.get("plan_item_line_id"), "reservation_id": drawdown.get("reservation_id"),
				"contributing_org_unit": drawdown.get("contributing_org_unit"),
			}
		)
	lines = []
	for index, group in enumerate(groups.values(), start=1):
		group["line_number"] = index
		group["source_item_ids"] = ", ".join(s["requisition_item_id"] for s in group["source_items"])
		group["quantity"] = fmt_quantity(group["quantity"])
		lines.append(group)
	return lines


def related_services(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	return [
		{
			"service_requirement_id": row.get("service_requirement_id"), "service_type": row.get("service_type"),
			"required_result": row.get("required_result"), "applies_to": _applies_to_label(row, snapshot),
			"completion_date": fmt_date(row.get("completion_date")), "completion_date_iso": cstr(row.get("completion_date")),
			"acceptance_evidence": row.get("acceptance_evidence"),
		}
		for row in snapshot.get("related_services") or []
	]


def acceptance_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	return [
		{
			"acceptance_requirement_id": row.get("acceptance_requirement_id"), "check_type": row.get("check_type"),
			"pass_condition": row.get("pass_condition"), "evidence_type": row.get("evidence_type"), "applies_to": _applies_to_label(row, snapshot),
		}
		for row in snapshot.get("acceptance_requirements") or []
	]


def supporting_materials(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
	out = []
	for row in snapshot.get("supporting_materials") or []:
		try:
			linked = json.loads(row.get("linked_requirement_ids_json") or "[]")
		except ValueError:
			linked = []
		out.append(
			{
				"supporting_material_id": row.get("supporting_material_id"), "title": row.get("title"), "document_type": row.get("document_type"),
				"treatment": row.get("treatment"), "file_digest": row.get("file_digest"), "linked_requirement_ids": ", ".join(map(str, linked)), "linked_requirement_id_list": linked,
			}
		)
	return out


def warranty_support(snapshot: dict[str, Any]) -> dict[str, Any]:
	return {
		"minimum_warranty_months": fmt_number(snapshot.get("minimum_warranty_months")),
		"onsite_support_required": bool(snapshot.get("onsite_support_required")),
		"maximum_support_response_hours": fmt_number(snapshot.get("maximum_support_response_hours")),
		"manufacturer_support_required": bool(snapshot.get("manufacturer_support_required")),
		"service_location_constraint": cstr(snapshot.get("service_location_constraint")),
		"support_description": cstr(snapshot.get("support_description")),
	}


# --------------------------------------------------------------------------
# generated schedules and mappings (§4.5)
# --------------------------------------------------------------------------


def price_schedule(snapshot: dict[str, Any]) -> dict[str, Any]:
	rows = []
	for line in goods_lines(snapshot):
		rows.append(
			{
				"line": f"{line['line_number']}", "kind": "Goods", "identity": line["source_item_ids"], "description": line["description"],
				"quantity": line["quantity"], "unit": line["unit"], "unit_price": SUPPLIER, "line_total": CALCULATED, "tax": SUPPLIER,
				"source_items": line["source_items"],
			}
		)
	for index, service in enumerate(related_services(snapshot), start=1):
		rows.append(
			{
				"line": f"S{index}", "kind": "Related service", "identity": service["service_requirement_id"], "description": f"{service['service_type']} — {service['required_result']}",
				"quantity": "1", "unit": "service", "unit_price": SUPPLIER, "line_total": CALCULATED, "tax": SUPPLIER, "source_items": [],
			}
		)
	return {"currency": "KES", "fixed_price": FIXED_PRICE, "tax_display_treatment": TAX_TREATMENT, "rows": rows, "tender_total": CALCULATED}


_CONTROL_MAP = {
	req_catalogue.YES_NO: "select", req_catalogue.SELECT: "select", req_catalogue.MULTI_SELECT: "multi_select", req_catalogue.INTEGER: "integer",
	req_catalogue.DECIMAL: "decimal", req_catalogue.TEXT: "text", req_catalogue.PORT_LIST: "port_list",
}


def supplier_response_schema(snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""§4.5.1 — one structured response row per published goods line,
	mandatory technical requirement, service, warranty/support obligation,
	acceptance requirement and evidence requirement, each keeping the
	published stable identifier."""
	from kentender_procurement.tenders.services import evidence as ev

	evidence_ids = ev.technical_ids_with_evidence(evidence_rows)
	technical = []
	for row in technical_rows(snapshot, evidence_ids):
		offered = {"control": _CONTROL_MAP.get(row["control"], "text"), "unit": row["unit"], "max_length": 300}
		if offered["control"] == "select":
			offered["options"] = row["options"]
		technical.append(
			{
				"technical_requirement_id": row["technical_requirement_id"], "published_requirement": row["label"], "comparison": row["comparison"],
				"required_value": row["required_value"], "unit": row["unit"], "applies_to": row["applies_to"],
				"compliance": {"control": "radio", "options": ["Comply", "Do not comply"], "required": True},
				"offered_value": offered, "comment": {"control": "text", "max_length": 500, "required": False},
				"evidence_references": {"required": row["evidence_required"]},
			}
		)
	return {
		"goods": [
			{
				"line": f"{line['line_number']}", "identity": line["source_item_ids"], "description": line["description"], "quantity": line["quantity"], "unit": line["unit"],
				"offered_make_model": {"control": "text", "max_length": 160, "required": True}, "unit_price": {"control": "money", "currency": "KES", "required": True},
				"total_price": {"control": "money", "currency": "KES", "calculated": True}, "delivery_commitment": {"control": "date", "not_later_than": line["latest_delivery_date_iso"]},
				"evidence_references": {"required": True},
			}
			for line in goods_lines(snapshot)
		],
		"technical": technical,
		"services": [
			{"service_requirement_id": s["service_requirement_id"], "confirmation": {"control": "radio", "options": ["Yes", "No"]}, "offered_completion_date": {"control": "date", "not_later_than": s["completion_date_iso"]}, "price_line": f"S{i}", "evidence_references": {"required": True}}
			for i, s in enumerate(related_services(snapshot), start=1)
		],
		"warranty_support": {
			"identity": snap.WARRANTY_ID, "confirmation": {"control": "radio", "options": ["Yes", "No"], "required": True},
			"offered_term_months": {"control": "integer", "minimum": snapshot.get("minimum_warranty_months")},
			"service_escalation_details": {"control": "text", "max_length": 500, "required": True}, "evidence_references": {"required": True},
		},
		"acceptance": [{"acceptance_requirement_id": a["acceptance_requirement_id"], "confirmation": "Accepted with the Tender submission — becomes a contract obligation"} for a in acceptance_rows(snapshot)],
		"evidence": [{"evidence_requirement_id": r["evidence_requirement_id"], "label": r["label"], "linked_requirement_type": r["linked_requirement_type"], "linked_requirement_id": r["linked_requirement_id"], "mandatory": r["mandatory"], "references": {"minimum": 1 if r["mandatory"] else 0}} for r in evidence_rows],
	}


def qualification_criteria(state: dict[str, Any]) -> list[dict[str, Any]]:
	return [
		{"criterion": "Manufacturer's authorisation", "required": bool(state.get("manufacturer_authorisation_required"))},
		{"criterion": "Technical datasheets or brochures", "required": bool(state.get("datasheets_required"))},
		{"criterion": "Warranty confirmation", "required": True},
		{"criterion": "Comparable supply experience", "required": bool(state.get("past_experience_required")), "minimum_contracts": state.get("minimum_comparable_contracts") if state.get("past_experience_required") else None, "period_years": state.get("experience_period_years") if state.get("past_experience_required") else None},
		{"criterion": "After-sales support evidence", "required": bool(state.get("after_sales_evidence_required")), "evidence": state.get("after_sales_evidence") if state.get("after_sales_evidence_required") else None},
	]


def evaluation_contract(state: dict[str, Any], snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
	"""§4.5.2 — the fixed governed stage order, one pass/fail check per
	mandatory technical requirement identity, the published eligibility and
	evidence checklist, and nothing hidden."""
	from kentender_procurement.tenders.services import evidence as ev

	return {
		"stages": list(EVALUATION_STAGES),
		"eligibility_checklist": [{"evidence_requirement_id": r["evidence_requirement_id"], "label": r["label"], "linked_requirement_type": r["linked_requirement_type"], "linked_requirement_id": r["linked_requirement_id"], "mandatory": r["mandatory"]} for r in evidence_rows],
		"qualification_criteria": qualification_criteria(state),
		"technical_pass_fail": [{"technical_requirement_id": row["technical_requirement_id"], "published_requirement": row["label"], "comparison": row["comparison"], "required_value": row["required_value"], "unit": row["unit"], "mandatory": True, "evidence_required": row["evidence_required"]} for row in technical_rows(snapshot, ev.technical_ids_with_evidence(evidence_rows))],
		"financial": {"currency": "KES", "basis": "Lowest evaluated responsive Tender", "award_packages": 1, "fixed_price": FIXED_PRICE, "tax_display_treatment": TAX_TREATMENT},
		"hidden_criteria": [],
	}


def contract_obligations(state: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
	"""§4.5.3 — identified obligations for every item/source allocation,
	technical requirement, service, warranty/support value, acceptance
	requirement, price row and finite officer-authored parameter."""
	lines_by_id = {line.get("drawdown_line_id"): line for line in snapshot.get("drawdown_lines") or []}
	return {
		"items": [
			{
				"requisition_item_id": i.get("requisition_item_id"), "item_name": i.get("item_name"), "quantity": i.get("quantity"), "unit": i.get("unit"),
				"plan_item_line_id": i.get("plan_item_line_id"), "plan_source_allocation_id": (lines_by_id.get(i.get("plan_item_line_id")) or {}).get("plan_item_line_id"),
				"reservation_id": (lines_by_id.get(i.get("plan_item_line_id")) or {}).get("reservation_id"),
				"delivery_location": snapshot.get("delivery_location"), "latest_delivery_date": snapshot.get("latest_delivery_date"),
			}
			for i in snapshot.get("items") or []
		],
		"price_rows": [{"line": r["line"], "identity": r["identity"], "quantity": r["quantity"], "unit": r["unit"], "agreed_price": "From awarded response"} for r in price_schedule(snapshot)["rows"]],
		"technical": [{"technical_requirement_id": r["technical_requirement_id"], "published_requirement": r["label"], "comparison": r["comparison"], "required_value": r["required_value"], "unit": r["unit"], "mandatory": True, "accepted_offered_value": "From awarded response"} for r in technical_rows(snapshot)],
		"services": [{"service_requirement_id": s["service_requirement_id"], "service_type": s["service_type"], "required_result": s["required_result"], "completion_date": s["completion_date_iso"], "acceptance_evidence": s["acceptance_evidence"]} for s in related_services(snapshot)],
		"warranty_support": warranty_support(snapshot),
		"acceptance": acceptance_rows(snapshot),
		"parameters": {
			"payment_timing_days": state.get("payment_timing_days"), "performance_security_required": bool(state.get("performance_security_required")),
			"performance_security_percent": state.get("performance_security_percent") if state.get("performance_security_required") else None,
			"performance_security_form": PERFORMANCE_SECURITY_FORM if state.get("performance_security_required") else None,
			"delay_damages_per_week_percent": state.get("delay_damages_per_week_percent"), "maximum_delay_damages_percent": state.get("maximum_delay_damages_percent"),
			"inspection_location": state.get("inspection_location"), "contract_contact_office": state.get("contract_contact_office"),
			"tender_validity_days": state.get("tender_validity_days"),
		},
	}


# --------------------------------------------------------------------------
# officer state and derived dates
# --------------------------------------------------------------------------


def officer_state(version) -> dict[str, Any]:
	"""The Version's officer values (`officer_payload_json`) in canonical
	Python types; every catalogue field present (None when unset)."""
	try:
		raw = json.loads(version.officer_payload_json or "{}")
	except (TypeError, ValueError):
		raw = {}
	return controls.normalise(raw)


def derived_dates(state: dict[str, Any]) -> dict[str, Any]:
	submission = get_datetime(state.get("submission_deadline")) if state.get("submission_deadline") else None
	validity = int(state.get("tender_validity_days") or 0)
	validity_date = (submission.date() + timedelta(days=validity)) if submission and validity else None
	return {
		"opening_datetime": submission,
		"validity_date": validity_date,
		"bank_guarantee_expiry_date": (validity_date + timedelta(days=BANK_GUARANTEE_EXTRA_DAYS)) if validity_date else None,
		"insurance_guarantee_expiry_date": (validity_date + timedelta(days=INSURANCE_GUARANTEE_EXTRA_DAYS)) if validity_date else None,
	}


# --------------------------------------------------------------------------
# render context (the template contract — fixtures/moh_input.json shape)
# --------------------------------------------------------------------------


def _office_display(office: str) -> tuple[str, str]:
	if not office or not frappe.db.exists("Contact Office", office):
		return "", ""
	doc = frappe.get_doc("Contact Office", office)
	return doc.display(), cstr(doc.address)


def _meeting_details(state: dict[str, Any]) -> str:
	if not state.get("pre_tender_meeting"):
		return ""
	parts = [fmt_datetime_eat(state.get("meeting_datetime"))]
	if state.get("meeting_mode") == "Physical":
		parts.append(f"at {state.get('meeting_venue')}")
	elif state.get("meeting_mode") == "Online":
		parts.append(f"online — {state.get('online_joining_information')}")
	return " ".join(p for p in parts if p) + "."


def _after_sales_text(state: dict[str, Any]) -> str:
	choice = cstr(state.get("after_sales_evidence"))
	if choice == "Both":
		return "Kenya service-centre details and escalation contacts, and a manufacturer or authorised service-partner commitment"
	return choice


def pending_approval() -> dict[str, str]:
	return {"official_name": "To be confirmed at approval", "official_title": "Head of Procurement Function", "approved_date": "Pending approval", "reference": "Pending approval"}


def render_context(tender, version, snapshot: dict[str, Any], *, approval: dict[str, str] | None = None) -> dict[str, Any]:
	from kentender_procurement.tenders.services import evidence as ev

	state = officer_state(version)
	dates = derived_dates(state)
	evidence_rows = ev.rows_as_dicts(version)
	evidence_ids = ev.technical_ids_with_evidence(evidence_rows)
	contact_display, contact_address = _office_display(state.get("contract_contact_office"))
	services = related_services(snapshot)
	items = snapshot.get("items") or []
	unit = cstr((items[0].get("unit") if items else "") or "Each")
	context = {
		"procuring_entity": {
			"name": cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name")),
			"address": contact_address,
			"contact_office": contact_display,
		},
		"requisition": {
			"requirement_title": cstr(snapshot.get("requirement_title")),
			"authorised_quantity": f"{fmt_quantity(snap.total_quantity(snapshot))} {unit}",
			"authorised_value": f"KES {fmt_money(snap.total_value(snapshot))}",
			"expected_delivery_date": fmt_date(snapshot.get("latest_delivery_date")),
			"related_services_authorized": bool(services),
			"reference": cstr(snapshot.get("requisition_reference")),
		},
		"plan_item": {"reference": cstr(snapshot.get("plan_item_id"))},
		"reservation": {"category": cstr(snapshot.get("reservation_category_value") or "None")},
		"tender": {
			"reference": cstr(tender.tender_reference),
			"title": cstr(state.get("tender_title")),
			"procurement_method": "Open Tender",
			"issue_date": fmt_date(state.get("issue_date")),
			"clarification_deadline": fmt_datetime_eat(state.get("clarification_deadline")),
			"submission_deadline": fmt_datetime_eat(state.get("submission_deadline")),
			"validity_days": fmt_number(state.get("tender_validity_days")),
			"validity_date": fmt_date(dates["validity_date"]),
			"opening_datetime": fmt_datetime_eat(dates["opening_datetime"]),
			"currency": "KES",
			"tender_security": {
				"type": "Tender Security", "currency": "KES", "amount": fmt_money(state.get("tender_security_amount")),
				"bank_guarantee_expiry_date": fmt_date(dates["bank_guarantee_expiry_date"]),
				"insurance_guarantee_expiry_date": fmt_date(dates["insurance_guarantee_expiry_date"]),
			},
			"pre_tender_meeting": {"enabled": bool(state.get("pre_tender_meeting")), "details": _meeting_details(state)},
			"approval": approval or pending_approval(),
		},
		"platform": {"name": PLATFORM_NAME, "public_url": f"{frappe.utils.get_url()}/tenders"},
		"price": {"fixed_price_confirmed": FIXED_PRICE, "tax_display_treatment": TAX_TREATMENT},
		"submission": {
			"manufacturer_authorisation_required": bool(state.get("manufacturer_authorisation_required")),
			"datasheet_required": bool(state.get("datasheets_required")),
			"comparable_experience": {"required": bool(state.get("past_experience_required")), "count": cstr(state.get("minimum_comparable_contracts") or ""), "period_years": cstr(state.get("experience_period_years") or "")},
			"after_sales_support_required": bool(state.get("after_sales_evidence_required")),
			"after_sales_support_evidence": _after_sales_text(state) if state.get("after_sales_evidence_required") else "",
			"additional_evidence": {"required": bool(evidence_rows), "description": "; ".join(r["label"] for r in evidence_rows), "linked_requirement": "; ".join(r["linked_requirement_id"] for r in evidence_rows)},
		},
		"contract": {
			"payment_terms": f"Payment within {cstr(state.get('payment_timing_days') or '')} days after delivery, inspection, acceptance and receipt of a valid invoice",
			"payment_days": cstr(state.get("payment_timing_days") or ""),
			"performance_security": {"required": bool(state.get("performance_security_required")), "percentage": fmt_number(state.get("performance_security_percent")) if state.get("performance_security_required") else "", "form_variant": PERFORMANCE_SECURITY_FORM},
			"delay_damages": {"rate_per_week": fmt_number(state.get("delay_damages_per_week_percent")), "cap_percent": fmt_number(state.get("maximum_delay_damages_percent"))},
			"inspection_acceptance_office": cstr(state.get("inspection_location")),
			"contact_office": contact_display,
		},
		"goods": [{k: v for k, v in line.items() if k in ("source_item_ids", "description", "quantity", "unit", "destination", "latest_delivery_date", "minimum_warranty")} for line in goods_lines(snapshot)],
		"related_services": [{k: v for k, v in s.items() if k != "completion_date_iso"} for s in services],
		"technical_requirements": [{k: v for k, v in r.items() if k in ("technical_requirement_id", "label", "comparison", "required_value", "unit", "applies_to", "evidence_required")} for r in technical_rows(snapshot, evidence_ids)],
		"warranty_support": warranty_support(snapshot),
		"acceptance_requirements": acceptance_rows(snapshot),
		"supporting_materials": [{k: v for k, v in m.items() if k in ("supporting_material_id", "title", "document_type", "treatment", "linked_requirement_ids")} for m in supporting_materials(snapshot)],
		# Never rendered — internal readers only (§4.3).
		"_internal": snap.internal_context(snapshot),
	}
	return context


def public_context(context: dict[str, Any]) -> dict[str, Any]:
	return {k: v for k, v in context.items() if not k.startswith("_")}


# --------------------------------------------------------------------------
# digests and the package
# --------------------------------------------------------------------------


def generated(state: dict[str, Any], snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
	return {
		"goods": goods_lines(snapshot), "price_schedule": price_schedule(snapshot),
		"supplier_response_schema": supplier_response_schema(snapshot, evidence_rows),
		"evaluation_contract": evaluation_contract(state, snapshot, evidence_rows), "contract_obligations": contract_obligations(state, snapshot),
	}


def generated_digests(state: dict[str, Any], snapshot: dict[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, str]:
	"""§4.2 `response_schema_digest`, `evaluation_contract_digest`,
	`contract_projection_digest`."""
	return {
		"response_schema_digest": digest.sha256_hex(supplier_response_schema(snapshot, evidence_rows)),
		"evaluation_contract_digest": digest.sha256_hex(evaluation_contract(state, snapshot, evidence_rows)),
		"contract_projection_digest": digest.sha256_hex(contract_obligations(state, snapshot)),
	}


def content_material(tender, version, snapshot: dict[str, Any]) -> dict[str, Any]:
	from kentender_procurement.tenders.services import evidence as ev

	state = officer_state(version)
	evidence_rows = ev.rows_as_dicts(version)
	return {
		"binding": {
			"template_release_id": version.template_release_id, "official_source_digest": version.official_source_digest, "bundle_digest": version.bundle_digest,
			"requisition_handoff": version.requisition_handoff, "handoff_digest": snapshot.get("handoff_digest"), "requisition_version": version.requisition_version,
			"requisition_content_digest": snapshot.get("content_digest"),
		},
		"requisition_snapshot_digest": version.requisition_snapshot_digest,
		"officer_values": state,
		"evidence": evidence_rows,
		"generated": generated(state, snapshot, evidence_rows),
	}


def package_digest(tender, version, snapshot: dict[str, Any], *, renders: dict[str, Any] | None = None) -> str:
	"""§4.2 `package_digest` — every inherited/officer/generated value plus
	both document digests when they exist."""
	material = content_material(tender, version, snapshot)
	material["documents"] = {"invitation_digest": (renders or {}).get("invitation_digest") or version.invitation_digest, "issued_tender_digest": (renders or {}).get("issued_tender_digest") or version.issued_tender_digest}
	return digest.sha256_hex(material)
