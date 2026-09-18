# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.8 §5.3 — the eight compatibility checks (plan D16). A
Requisition may start this product only when every row answers Yes; any
No blocks with `TND_PRODUCT_UNSUPPORTED` and no free-text bypass. The
same pure function runs at start, submit, approve and publication
authorisation against the exact immutable facts each command holds
(TPR08-AC-029)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from kentender_procurement.tender_templates import loader

# Goods equipment categories the released IT Equipment pattern covers
# (REQ-CAT-1.6's own list); anything else is not off-the-shelf equipment.
OFF_THE_SHELF_CATEGORIES = ("Laptop", "Desktop computer", "Tablet", "Monitor", "Printer", "Scanner", "Network equipment", "Power-protection equipment")
PRODUCT_LABEL = "Straightforward off-the-shelf IT equipment"


@dataclass(frozen=True)
class Check:
	check: str
	required: str
	actual: str
	ok: bool

	def as_dict(self) -> dict[str, Any]:
		return {"check": self.check, "required": self.required, "actual": self.actual, "ok": self.ok}


def supported_reservation_categories() -> tuple[str, ...]:
	return tuple(loader.metadata().get("supported_reservation_categories") or ())


def evaluate(payload: dict[str, Any]) -> list[Check]:
	items = payload.get("items") or []
	equipment_ok = bool(items) and payload.get("product_pattern") == "IT Equipment" and all((row.get("equipment_category") in OFF_THE_SHELF_CATEGORIES) and float(row.get("quantity") or 0) > 0 for row in items)
	categories = ", ".join(sorted({str(r.get("equipment_category")) for r in items})) if items else "no items"
	currency = payload.get("currency") or "KES"
	packages = payload.get("award_packages") or 1
	reservation = payload.get("reservation_category_value") or "None"
	supported = supported_reservation_categories()
	return [
		Check("Procurement category", "Goods", str(payload.get("procurement_category") or "—"), payload.get("procurement_category") == "Goods"),
		Check("Product", PRODUCT_LABEL, f"{payload.get('product_pattern') or '—'}: {categories}", equipment_ok),
		Check("Method", "Open Tender", str(payload.get("planned_method") or "—"), payload.get("planned_method") == "Open Tender"),
		Check("Reservation", "A category supported by the bound template release", str(reservation), reservation in supported),
		Check("Lotting", "Single lot", str(payload.get("lotting_indicator") or "—"), payload.get("lotting_indicator") == "Single lot"),
		Check("Currency", "KES", str(currency), currency == "KES"),
		Check("Award package", "One", str(packages), str(packages) in ("1", "One")),
		Check("Plan horizon", "Single year", str(payload.get("plan_horizon") or "—"), payload.get("plan_horizon") == "Single year"),
	]


def is_supported(checks: list[Check]) -> bool:
	return all(c.ok for c in checks)


def first_failure(checks: list[Check]) -> Check | None:
	for check in checks:
		if not check.ok:
			return check
	return None


def require_supported(payload: dict[str, Any]) -> list[Check]:
	from kentender_procurement.tenders.services.errors import fail

	checks = evaluate(payload)
	failed = first_failure(checks)
	if failed:
		fail("TND_PRODUCT_UNSUPPORTED", detail={"check": failed.check, "required": failed.required, "actual": failed.actual, "checks": [c.as_dict() for c in checks]})
	return checks
