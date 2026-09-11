# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.4 — the compatibility test. Version 1.1 is offered
only when every row answers Yes; any No blocks Tender creation with no
free-text bypass (`TPR_PRODUCT_UNSUPPORTED`, TPR-AC-001/036/041,
SMOKE-15). Each §6.4 row is one named test so a failure names itself."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from frappe.utils import getdate

from kentender_procurement.tender_templates import loader

TYPED_COMPARISONS = ("Minimum", "Maximum", "Exact", "Required", "One of")
COMPLEX_WORK_TERMS = (
	"software development", "systems implementation", "system implementation", "integration", "data migration",
	"migration", "hosting", "custom development", "bespoke", "erp", "implementation project",
)
# Goods equipment categories the released IT Equipment pattern covers
# (REQ-CAT-1.6's own list); anything else is not off-the-shelf equipment.
OFF_THE_SHELF_CATEGORIES = (
	"Laptop", "Desktop computer", "Tablet", "Monitor", "Printer", "Scanner", "Network equipment", "Power-protection equipment",
)


@dataclass(frozen=True)
class Row:
	test: str
	required: str
	actual: str
	ok: bool

	def as_dict(self) -> dict[str, Any]:
		return {"test": self.test, "required": self.required, "actual": self.actual, "ok": self.ok}


def supported_reservation_categories() -> tuple[str, ...]:
	return tuple(loader.metadata().get("supported_reservation_categories") or ())


def _parse_value(raw: Any) -> dict | None:
	if isinstance(raw, dict):
		return raw
	try:
		value = json.loads(raw or "")
	except (TypeError, ValueError):
		return None
	return value if isinstance(value, dict) else None


def evaluate(payload: dict[str, Any], *, handoff_version: str) -> list[Row]:
	rows: list[Row] = []
	rows.append(Row("Handoff version", f"AuthorisedRequisitionHandoff v{loader.metadata()['handoff_version']}", f"v{handoff_version or payload.get('handoff_version') or '—'}", str(handoff_version or payload.get("handoff_version")) == loader.metadata()["handoff_version"]))
	rows.append(Row("Product pattern", "IT Equipment", str(payload.get("product_pattern") or "—"), payload.get("product_pattern") == "IT Equipment"))
	rows.append(Row("Procurement category", "Goods", str(payload.get("procurement_category") or "—"), payload.get("procurement_category") == "Goods"))
	rows.append(Row("Method", "Open Tender", str(payload.get("planned_method") or "—"), payload.get("planned_method") == "Open Tender"))
	currency = payload.get("currency") or "KES"
	rows.append(Row("Currency", "KES", str(currency), currency == "KES"))
	packages = payload.get("award_packages") or 1
	rows.append(Row("Award package", "One", str(packages), str(packages) in ("1", "One")))
	rows.append(Row("Lotting indicator", "Single lot", str(payload.get("lotting_indicator") or "—"), payload.get("lotting_indicator") == "Single lot"))
	category = payload.get("reservation_category_value") or "None"
	supported = supported_reservation_categories()
	rows.append(Row("Reservation category", ", ".join(supported), str(category), category in supported))
	items = payload.get("items") or []
	equipment_ok = bool(items) and all((row.get("equipment_category") in OFF_THE_SHELF_CATEGORIES) and float(row.get("quantity") or 0) > 0 for row in items)
	rows.append(Row("Equipment", "Straightforward off-the-shelf goods", f"{len(items)} item(s): " + ", ".join(sorted({str(r.get('equipment_category')) for r in items})) if items else "no items", equipment_ok))
	technical = payload.get("technical_requirements") or []
	typed_ok = bool(technical) and all(row.get("comparison") in TYPED_COMPARISONS and _parse_value(row.get("required_value_json")) is not None for row in technical)
	rows.append(Row("Technical response", "Every mandatory requirement can use the typed pass/fail response (§9.1)", f"{len(technical)} typed row(s)" if typed_ok else "an untyped requirement row", typed_ok))
	services = payload.get("related_services") or []
	complex_hits = [s.get("service_type") for s in services if any(term in (f"{s.get('service_type', '')} {s.get('required_result', '')}").lower() for term in COMPLEX_WORK_TERMS)]
	rows.append(Row("Complex work", "No custom development, integration or migration", "none" if not complex_hits else ", ".join(map(str, complex_hits)), not complex_hits))
	latest = payload.get("latest_delivery_date")
	dates_ok = bool(latest)
	if dates_ok:
		try:
			latest_d = getdate(latest)
			dates_ok = all((not s.get("completion_date")) or getdate(s.get("completion_date")) <= latest_d for s in services)
		except Exception:
			dates_ok = False
	value_ok = sum(float(line.get("requested_value") or 0) for line in payload.get("drawdown_lines") or []) > 0
	rows.append(Row("Dates and value", "Inside authorised Requisition boundaries", ("latest delivery " + str(latest) if latest else "no delivery date") + (", authorised value present" if value_ok else ", no authorised value"), dates_ok and value_ok))
	materials = payload.get("supporting_materials") or []
	materials_ok = all(row.get("treatment") and row.get("supporting_material_id") for row in materials)
	rows.append(Row("Supporting materials", "Every operative file obligation has a structured row", f"{len(materials)} material(s)", materials_ok))
	return rows


def first_failure(rows: list[Row]) -> Row | None:
	for row in rows:
		if not row.ok:
			return row
	return None
