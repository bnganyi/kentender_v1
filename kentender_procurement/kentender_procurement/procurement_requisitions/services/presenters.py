# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §12.1/§13 — display helpers and the one result-first
review composition every decision screen shares (REQ-DES-06/07/08/10/11).

Business language is applied here, once (§12.1): Plan Item → approved
purchase, drawdown → amounts requested, reservation_category → "Reserved
for", funding reservation → financial hold. Machine identities stay in
`record_details`. Datetimes are stored as naive site-local (Africa/Nairobi)
values and are shown as "15 Mar 2027, 10:00 EAT" without conversion.
"""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any

import frappe
from frappe.utils import cstr, get_datetime, getdate

from kentender_procurement.procurement_requisitions.services import catalogue, goods_template, precision, records
from kentender_procurement.procurement_requisitions.services import scope as req_scope


def date_label(value) -> str:
	if not value:
		return ""
	d = getdate(value)
	return f"{d.day} {d.strftime('%b %Y')}"


def eat(value) -> str:
	if not value:
		return ""
	dt = get_datetime(value)
	return f"{dt.day} {dt.strftime('%b %Y, %H:%M')} EAT"


def fiscal_year_label(fiscal_year: str) -> str:
	""""FY 2027/28" — the board's financial-year label."""
	if not fiscal_year:
		return ""
	start, end = frappe.db.get_value("Fiscal Year", fiscal_year, ["year_start_date", "year_end_date"]) or (None, None)
	if not start or not end:
		return cstr(fiscal_year)
	return f"FY {getdate(start).year}/{str(getdate(end).year)[-2:]}"


def user_name(user: str) -> str:
	if not user:
		return ""
	return cstr(frappe.db.get_value("User", user, "full_name") or user)


def location_label(location: str) -> str:
	return cstr(frappe.db.get_value("Delivery Location", location, "location_name") or location) if location else ""


def objective_title(objective: str) -> str:
	return cstr(frappe.db.get_value("Strategy Node", objective, "title") or "") if objective else ""


def objective_reference(objective: str) -> str:
	"""The Strategy Node's own reference (`strategy_node_id`, e.g. MOH-NODE-0004), never its database name."""
	if not objective:
		return ""
	return cstr(frappe.db.get_value("Strategy Node", objective, "strategy_node_id") or "")


def money(value) -> str:
	return precision.display_money(precision.stored_money(value))


def quantity(value) -> str:
	return precision.display_quantity(precision.stored_quantity(value))


def departments_label(units: list[str], separator: str = "; ") -> str:
	return separator.join(records.unit_name(u) for u in units)


def ordered_units(lines: list[dict[str, Any]], lead: str) -> list[str]:
	"""Lead department first, then the others by drawn value (§13.1 fixture:
	"Digital Health; HR Management and Development")."""
	totals: dict[str, Decimal] = {}
	for line in lines:
		unit = line.get("contributing_org_unit") or ""
		totals[unit] = totals.get(unit, Decimal(0)) + precision.stored_money(line.get("requested_value"))
	return sorted(totals, key=lambda u: (u != lead, -totals[u], u))


def reserved_for(designation: str) -> str:
	return cstr(designation) or "None"


# --------------------------------------------------------------------------
# The shared review composition (§13.7 — result-first, disclosure-ready)
# --------------------------------------------------------------------------


def technical_groups(package: dict[str, Any], *, include_proposed: bool = True) -> list[dict[str, Any]]:
	rows = [r for r in package.get("technical_requirements") or [] if include_proposed or r.get("row_state") != "Proposed"]
	groups: dict[str, list[dict[str, Any]]] = {name: [] for name, _ in catalogue.TECHNICAL_GROUPS}
	for row in sorted(rows, key=lambda r: int(r.get("row_order") or 0)):
		ch = catalogue.CATALOGUE_BY_KEY.get(row.get("characteristic_key"))
		label = ch.label if ch else cstr(row.get("characteristic_key"))
		comparison = cstr(row.get("comparison") or (ch.comparison if ch else ""))
		if ch and ch.key == "network_connectivity":
			comparison = "Required · every selected capability is required"
		try:
			value = json.loads(row.get("required_value_json") or "{}")
		except (TypeError, ValueError):
			value = {}
		groups.setdefault(catalogue.GROUP_OF.get(cstr(row.get("characteristic_key")), "Performance and storage"), []).append(
			{
				"technical_requirement_id": row.get("technical_requirement_id"), "characteristic_key": row.get("characteristic_key"),
				"label": label, "comparison": comparison, "value": value, "display": cstr(row.get("required_value_display")) or (catalogue.display_value(ch, value) if ch and value else ""),
				"unit": cstr(row.get("unit")) or "—", "state": row.get("row_state") or "Confirmed",
				"applies_to_scope": row.get("applies_to_scope"), "applies_to_id": row.get("applies_to_id"), "reason": row.get("reason"), "other_value": row.get("other_value"),
				"applies_to": row_label(row, package), "applies_to_item_ids": req_scope.item_ids(row, package.get("items") or []), "needs_review": row.get("row_state") == "Needs review",
			}
		)
	return [{"group": name, "rows": items} for name, items in groups.items() if items]


def technical_targets(package: dict[str, Any], version: dict[str, Any] | None = None, *, include_proposed: bool = True) -> list[dict[str, Any]]:
	"""REQ v1.18 §13.6A — the technical rows grouped by what they apply to: Shared requirements (every item), one
	target for each kind of item (a set of items sharing a specification), and any row customised for fewer items.
	Each target keeps the characteristic grouping of `technical_groups`."""
	items = package.get("items") or []
	all_ids = [i.get("requisition_item_id") for i in items]
	kinds = specification_groups(package, version)
	line_unit = {l.get("drawdown_line_id"): records.unit_name(l.get("contributing_org_unit")) for l in (version or {}).get("drawdown_lines") or []}
	by_id = {i.get("requisition_item_id"): i for i in items}
	flat = [(g["group"], r) for g in technical_groups(package, include_proposed=include_proposed) for r in g["rows"]]
	targets: dict[tuple, dict[str, Any]] = {}

	def describe(ids: tuple) -> tuple[str, str, str]:
		if list(ids) == all_ids:
			return "shared", "Shared requirements", "Every item"
		for g in kinds:
			if list(ids) == list(g["requisition_item_ids"]):
				n = len(ids)
				return "kind", g["item_name"], f"{g['equipment_category']} · {n} approved requirement{'s' if n != 1 else ''}"
		if len(ids) == 1 and ids[0] in by_id:
			item = by_id[ids[0]]
			return "item", f"{item.get('item_name')} — customised", f"{item.get('equipment_category')} · {line_unit.get(item.get('drawdown_line_id')) or 'one item'}"
		names = list(dict.fromkeys(cstr(by_id[i].get("item_name")) for i in ids if i in by_id))
		return "set", ", ".join(names) or "Selected items", f"{len(ids)} items"

	for group_name, row in flat:
		key = tuple(row["applies_to_item_ids"])
		target = targets.get(key)
		if target is None:
			kind, title, subtitle = describe(key)
			target = targets[key] = {"key": f"T{len(targets) + 1}", "kind": kind, "title": title, "subtitle": subtitle, "item_ids": list(key), "groups": {}}
		target["groups"].setdefault(group_name, []).append(row)
	order = {"shared": 0, "kind": 1, "set": 2, "item": 3}
	out = []
	for target in sorted(targets.values(), key=lambda t: order[t["kind"]]):
		out.append({**target, "groups": [{"group": name, "rows": rows} for name, rows in target["groups"].items()]})
	return out


def row_label(row: dict[str, Any], package: dict[str, Any]) -> str:
	"""What a requirement row applies to, in words (REQ v1.18 §5.7A): `All items`, an item name, a service type or
	the names of the items a set covers."""
	if row.get("applies_to_scope") == "Items":
		return req_scope.label(row, package.get("items") or [])
	return applies_to_label(row.get("applies_to_scope"), row.get("applies_to_id"), package)


def applies_to_label(scope: str, target: str, package: dict[str, Any]) -> str:
	if scope == "Item":
		item = next((i for i in package.get("items") or [] if i.get("requisition_item_id") == target), None)
		return cstr(item.get("item_name")) if item else target
	if scope == "Service":
		service = next((s for s in package.get("related_services") or [] if s.get("service_requirement_id") == target), None)
		return cstr(service.get("service_type")) if service else target
	return "All items"


def acceptance_rows(package: dict[str, Any], *, include_proposed: bool = True) -> list[dict[str, Any]]:
	return [
		{
			"acceptance_requirement_id": r.get("acceptance_requirement_id"), "check_type": r.get("check_type"),
			"applies_to": row_label(r, package),
			"applies_to_scope": r.get("applies_to_scope"), "applies_to_id": r.get("applies_to_id"),
			"applies_to_item_ids": req_scope.item_ids(r, package.get("items") or []), "needs_review": r.get("row_state") == "Needs review",
			"pass_condition": r.get("pass_condition"), "evidence": r.get("other_evidence_name") if r.get("evidence_type") == "Other stated record" else r.get("evidence_type"),
			"evidence_type": r.get("evidence_type"), "other_evidence_name": r.get("other_evidence_name"), "state": r.get("row_state") or "Confirmed",
		}
		for r in sorted(package.get("acceptance_requirements") or [], key=lambda r: int(r.get("row_order") or 0))
		if include_proposed or r.get("row_state") != "Proposed"
	]


def support_values(package: dict[str, Any]) -> list[dict[str, str]]:
	yes_no = lambda v: "Yes" if v else "No"  # noqa: E731
	months, hours = package.get("minimum_warranty_months"), package.get("maximum_support_response_hours")
	rows = [
		{"field": "minimum_warranty_months", "label": "Minimum warranty", "value": f"{months} months" if months else ""},
		{"field": "onsite_support_required", "label": "On-site support required", "value": yes_no(package.get("onsite_support_required"))},
		{"field": "maximum_support_response_hours", "label": "Maximum support response", "value": f"{hours} hours" if hours and package.get("onsite_support_required") else ("Not applicable" if not package.get("onsite_support_required") else "")},
		{"field": "manufacturer_support_required", "label": "Manufacturer support required", "value": yes_no(package.get("manufacturer_support_required"))},
		{"field": "service_location_constraint", "label": "Service location constraint", "value": cstr(package.get("service_location_constraint"))},
		{"field": "support_description", "label": "Support description", "value": cstr(package.get("support_description"))},
	]
	return rows


def item_rows(version: dict[str, Any], package: dict[str, Any]) -> list[dict[str, Any]]:
	lines = {l.get("drawdown_line_id"): l for l in version.get("drawdown_lines") or []}
	out = []
	for item in sorted(package.get("items") or [], key=lambda i: int(i.get("row_order") or 0)):
		line = lines.get(item.get("drawdown_line_id")) or {}
		location = item.get("delivery_location") or version.get("delivery_location")
		latest = item.get("latest_delivery_date") or version.get("latest_delivery_date")
		place = cstr(frappe.db.get_value("Delivery Location", location, "address") or location_label(location)) if location else ""
		out.append(
			{
				"requisition_item_id": item.get("requisition_item_id"), "drawdown_line_id": item.get("drawdown_line_id"),
				"item_name": item.get("item_name"), "equipment_category": item.get("equipment_category"),
				"department": records.unit_name(line.get("contributing_org_unit")), "contributing_org_unit": line.get("contributing_org_unit"),
				"source_reference": line.get("source_line_id"), "approved_requirement": f"{records.unit_name(line.get('contributing_org_unit'))} — {line.get('source_line_id')}",
				"quantity": precision.display_quantity(int(item.get("quantity") or 0)), "quantity_value": int(item.get("quantity") or 0),
				"intended_use": item.get("intended_use"), "delivery": "; ".join(v for v in (_town(place), date_label(latest)) if v),
				"delivery_location": location, "latest_delivery_date": cstr(latest),
			}
		)
	return out


def _town(address: str) -> str:
	parts = [p.strip() for p in cstr(address).split(",") if p.strip()]
	return parts[-1] if parts else ""


def shared_specification(package: dict[str, Any]) -> dict[str, Any] | None:
	items = package.get("items") or []
	if not items:
		return None
	keys = {(i.get("equipment_category"), i.get("item_name"), i.get("delivery_location"), cstr(i.get("latest_delivery_date"))) for i in items}
	if len(keys) != 1:
		return None
	category = items[0].get("equipment_category") or ""
	return {
		"label": f"One shared specification · {len(items)} approved requirement{'s' if len(items) != 1 else ''}",
		"summary": f"{len(items)} item{'s' if len(items) != 1 else ''} · one shared specification",
		"requisition_item_ids": [i.get("requisition_item_id") for i in items], "equipment_category": category,
		"item_name": items[0].get("item_name"), "delivery_location": items[0].get("delivery_location"), "latest_delivery_date": cstr(items[0].get("latest_delivery_date")),
	}


def specification_groups(package: dict[str, Any], version: dict[str, Any] | None = None) -> list[dict[str, Any]]:
	"""Items that share one specification (category, name, delivery location and
	date), in the order they were first entered. Each group is edited as a unit
	by `UpdateSharedItemDetails`, so a request that mixes laptops and monitors
	can still change either group's name, category, location or date. Quantity
	and intended use stay on the item rows."""
	version = version or {}
	groups: dict[tuple, dict[str, Any]] = {}
	for item in sorted(package.get("items") or [], key=lambda i: int(i.get("row_order") or 0)):
		key = (item.get("equipment_category"), item.get("item_name"), item.get("delivery_location"), cstr(item.get("latest_delivery_date")))
		group = groups.get(key)
		if group is None:
			location = item.get("delivery_location") or version.get("delivery_location")
			latest = item.get("latest_delivery_date") or version.get("latest_delivery_date")
			place = cstr(frappe.db.get_value("Delivery Location", location, "address") or location_label(location)) if location else ""
			group = groups[key] = {
				"group_id": f"G{len(groups) + 1}", "equipment_category": item.get("equipment_category") or "", "item_name": item.get("item_name") or "",
				"delivery_location": item.get("delivery_location") or "", "latest_delivery_date": cstr(item.get("latest_delivery_date")),
				"delivery": "; ".join(v for v in (_town(place), date_label(latest)) if v), "requisition_item_ids": [],
			}
		group["requisition_item_ids"].append(item.get("requisition_item_id"))
	return list(groups.values())


def amounts_rows(
	version: dict[str, Any], sources: dict[str, dict[str, Any]], *, editable_units: set[str] | None = None,
	package: dict[str, Any] | None = None, only_used: bool = False, unreviewed: set[str] | None = None,
) -> list[dict[str, Any]]:
	"""One row per source line. v1.15 §5.3: the requested quantity is the sum of
	the line's items (so it is read from `package`), the estimated total cost is
	the requester's own entry (blank until entered), and what stays available
	after this request is shown beside them. `only_used` leaves out the sources
	the submission will omit (no items and no estimate)."""
	out = []
	unreviewed = unreviewed or set()
	for line in version.get("drawdown_lines") or []:
		source = sources.get(line.get("plan_item_line_id")) or {}
		line_id = line.get("drawdown_line_id")
		derived = goods_template.itemised(package.get("items"), line_id) if package is not None else int(precision.stored_quantity(line.get("requested_quantity")))
		estimate = precision.stored_money(line.get("requested_value"))
		if only_used and derived <= 0 and estimate <= 0:
			continue
		remaining_quantity = precision.stored_quantity(line.get("remaining_quantity"))
		remaining_value = precision.stored_money(line.get("remaining_value"))
		out.append(
			{
				"drawdown_line_id": line_id, "plan_item_line_id": line.get("plan_item_line_id"),
				"contributing_org_unit": line.get("contributing_org_unit"), "department": records.unit_name(line.get("contributing_org_unit")),
				"requirement": cstr(source.get("title")) or cstr(line.get("source_line_id")), "source_reference": line.get("source_line_id"),
				"available_quantity": quantity(line.get("remaining_quantity")), "available_value": money(line.get("remaining_value")),
				"requested_quantity": precision.display_quantity(derived), "requested_value": precision.display_money(estimate) if estimate > 0 else "",
				"requested_quantity_value": str(derived), "requested_value_value": precision.money_text(estimate) if estimate > 0 else "",
				"remaining_quantity_value": precision.quantity_text(remaining_quantity), "remaining_value_value": precision.money_text(remaining_value),
				"after_quantity": precision.display_quantity(remaining_quantity - derived), "after_value": precision.display_money(remaining_value - estimate),
				"after_quantity_value": precision.quantity_text(remaining_quantity - derived), "after_value_value": precision.money_text(remaining_value - estimate),
				"needs_review": line_id in unreviewed,
				"editable": editable_units is None or line.get("contributing_org_unit") in editable_units,
				"reservation_id": line.get("reservation_id"), "planning_drawdown_reference": line.get("planning_drawdown_reference"),
			}
		)
	return out


def totals(version: dict[str, Any]) -> tuple[Decimal, Decimal]:
	qty = sum((precision.stored_quantity(l.get("requested_quantity")) for l in version.get("drawdown_lines") or []), Decimal(0))
	value = sum((precision.stored_money(l.get("requested_value")) for l in version.get("drawdown_lines") or []), Decimal(0))
	return qty, value


def review_sections(*, root, version: dict[str, Any], package: dict[str, Any], projection: dict[str, Any], findings: list[dict[str, Any]], lead: str) -> list[dict[str, Any]]:
	"""§13.7 — ordered, complete sections. A section with a blocker, warning
	or requested correction starts open; the rest start closed with a plain
	summary. Disclosure is presentation only (§14.4)."""
	sources = {s["plan_item_line_id"]: s for s in projection.get("sources", [])}
	used = {**version, "drawdown_lines": [l for l in version.get("drawdown_lines") or [] if goods_template.itemised(package.get("items"), l.get("drawdown_line_id")) > 0 or goods_template.has_estimate(l)]}
	units = ordered_units(used["drawdown_lines"], lead)
	qty = Decimal(sum(goods_template.itemised(package.get("items"), l.get("drawdown_line_id")) for l in used["drawdown_lines"]))
	value = sum((precision.stored_money(l.get("requested_value")) for l in used["drawdown_lines"]), Decimal(0))
	by_section: dict[str, list[dict[str, Any]]] = {}
	for f in findings:
		by_section.setdefault(f.get("section") or "", []).append(f)
	designation = reserved_for(frappe.db.get_value("IT Equipment Requirement Package", {"requisition": root.name}, "reservation_category"))
	county = bool(frappe.db.get_value("IT Equipment Requirement Package", {"requisition": root.name}, "county_resident_reservation"))
	need = "; ".join(sorted({s.get("description", "") for s in projection.get("sources", []) if s.get("description")}))
	result = "; ".join(sorted({s.get("expected_operational_result", "") for s in projection.get("sources", []) if s.get("expected_operational_result")}))
	title_short = cstr(version.get("requirement_title"))
	purpose_facts = [
		{"label": "Requirement title", "value": title_short},
		{"label": "Method", "value": cstr(projection.get("procurement_method"))},
		{"label": "Reserved for", "value": designation},
	]
	if county:
		purpose_facts.append({"label": "County requirement", "value": "County residents"})
	technical = [g for g in technical_groups(package, include_proposed=False)]
	technical_count = sum(len(g["rows"]) for g in technical)
	months = package.get("minimum_warranty_months")
	location = cstr(package.get("service_location_constraint"))
	items = item_rows(version, package)
	spec = shared_specification(package)
	acceptance = acceptance_rows(package, include_proposed=False)
	services = package.get("related_services") or []
	materials = package.get("supporting_materials") or []

	def section(key, title, icon, summary, body, *, compact=False, empty_text=""):
		issues = by_section.get(key, []) + ([f for s in ("request_information",) for f in by_section.get(s, [])] if key == "purpose" else [])
		return {"key": key, "title": title, "icon": icon, "summary": summary, "open": bool(issues), "issues": issues, "compact": compact, "empty_text": empty_text, **body}

	out = [
		section(
			"purpose", "Purpose and approved purchase", "target",
			" · ".join(v for v in (title_short.split(" for ")[0], " and ".join(records.unit_name(u) for u in units), cstr(projection.get("procurement_method")), f"Reserved for {designation}") if v),
			{
				"facts": purpose_facts,
				"narrative": [
					{"label": "Business need", "value": need},
					{"label": "Strategic objective", "value": objective_title(root.strategic_objective_id)},
					{"label": "Expected operational result", "value": result},
				],
				"dates": [
					{"label": "Estimated completion", "value": date_label(projection.get("estimated_completion_date"))},
					{"label": "Latest delivery date", "value": date_label(version.get("latest_delivery_date"))},
					{"label": "Plan completion boundary", "value": date_label(projection.get("plan_completion_boundary"))},
				],
			},
		),
		section(
			"amounts", "Request summary", "coins",
			f"{len(units)} department{'s' if len(units) != 1 else ''} · {precision.display_quantity(qty)} · {precision.display_money(value)}",
			{"rows": amounts_rows(version, sources, package=package, only_used=True), "total_quantity": precision.display_quantity(qty), "total_value": precision.display_money(value)},
		),
		section("equipment", "Items", "monitor", spec["summary"] if spec else f"{len(items)} item{'s' if len(items) != 1 else ''}", {"rows": items}),
		section(
			"requirements", "Requirements and support", "sliders",
			" · ".join(v for v in (f"{technical_count} technical requirement{'s' if technical_count != 1 else ''}", f"{months}-month warranty" if months else "", f"support {location.lower()}" if location and location != "None" else "") if v),
			{"groups": technical, "support": support_values(package)},
		),
		section(
			"services", "Related services", "wrench", "None requested" if not services else f"{len(services)} service{'s' if len(services) != 1 else ''}",
			{"rows": [{**s, "applies_to": row_label(s, package), "applies_to_item_ids": req_scope.item_ids(s, package.get("items") or []), "completion_date_label": date_label(s.get("completion_date"))} for s in services]},
			compact=not services, empty_text="None requested",
		),
		section("acceptance", "Acceptance", "check-square", f"{len(acceptance)} delivery check{'s' if len(acceptance) != 1 else ''}", {"rows": acceptance}),
		section(
			"supporting_materials", "Supporting materials", "paperclip", "None added" if not materials else f"{len(materials)} file{'s' if len(materials) != 1 else ''}",
			{"rows": [{**m, "linked": records.json_list(m.get("linked_requirement_ids_json"))} for m in materials]},
			compact=not materials, empty_text="None added",
		),
	]
	# A date warning belongs to the purpose section (§13.7: it starts open).
	for f in findings:
		if f.get("code") == "DATE_AFTER_ESTIMATE" and f not in out[0]["issues"]:
			out[0]["issues"].append(f)
			out[0]["open"] = True
	return out


def record_details(*, root, version: dict[str, Any], projection: dict[str, Any], package_row=None, handoff=None, with_digests: bool = False) -> list[dict[str, str]]:
	"""Level 3 — exact identities as labelled supporting evidence. Every identity reads "<thing> reference" or
	"<thing> version", sentence case. The two integrity digests are for the Technical and Auditor reads only
	(`with_digests`): to anyone else a 64-character hash is noise (REQ-CHG-001 v1.18 §13.7A)."""
	sources = [s for s in (l.get("source_line_id") for l in version.get("drawdown_lines") or []) if s]
	# A source is a departmental need unless Planning took it from another origin (a direct entry).
	origin = {src.get("plan_item_line_id"): src.get("source_origin") for src in projection.get("sources", [])}
	lines = [l for l in version.get("drawdown_lines") or [] if l.get("source_line_id")]
	needs_only = bool(lines) and all(origin.get(l.get("plan_item_line_id")) == "Accepted Departmental Need" for l in lines)
	source_label = "Departmental need references" if needs_only else "Source references"
	facts = [
		{"label": "Requisition reference", "value": root.requisition_reference},
		{"label": "Plan item reference", "value": root.plan_item_id},
		{"label": "Plan version", "value": cstr(root.plan_version_id)},
		{"label": "Plan item version reference", "value": cstr(root.plan_item_version_id)},
		{"label": source_label, "value": "; ".join(sources)},
		{"label": "Strategic objective reference", "value": objective_reference(root.strategic_objective_id)},
	]
	drawdowns = [l.get("planning_drawdown_reference") for l in version.get("drawdown_lines") or [] if l.get("planning_drawdown_reference")]
	if drawdowns:
		facts.append({"label": "Planning drawdown references", "value": "; ".join(drawdowns)})
	reservations = [l.get("reservation_code") or l.get("reservation_id") for l in version.get("drawdown_lines") or [] if l.get("reservation_id")]
	if reservations:
		facts.append({"label": "Reservation references", "value": "; ".join(reservations)})
	if with_digests:
		if handoff:
			facts.append({"label": "Handoff digest", "value": cstr(handoff.handoff_digest)})
		if version.get("content_digest"):
			facts.append({"label": "Content digest", "value": cstr(version.get("content_digest"))})
	return facts
