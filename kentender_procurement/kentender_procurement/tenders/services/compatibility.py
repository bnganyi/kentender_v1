# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.12 §5.3 — the nine compatibility checks (plan D16′). A
Requisition may start this product only when every row answers Yes; a No
blocks with its own §8 code and no free-text bypass:

- a product, category, method, lotting, currency, award-package or
  plan-horizon failure is `TND_PRODUCT_UNSUPPORTED`;
- a reservation category or County-residents treatment the bound release
  does not support is `TND_RESERVATION_UNSUPPORTED`;
- a supported treatment without the applicable verified rule snapshot bound
  in the authorised handoff is `TND_RESERVATION_RULE_UNAVAILABLE`.

The same pure function runs at start, submit, approve, reopen and
publication authorisation against the exact immutable facts each command
holds (TPR09-AC-029). The supported treatments are the bound installed STD
release's own (§5.3), passed in by the caller; a Planning designation is
never bidder entitlement."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Goods equipment categories the released IT Equipment pattern covers
# (REQ-CAT-1.6's own list); anything else is not off-the-shelf equipment.
OFF_THE_SHELF_CATEGORIES = ("Laptop", "Desktop computer", "Tablet", "Monitor", "Printer", "Scanner", "Network equipment", "Power-protection equipment")
PRODUCT_LABEL = "Straightforward off-the-shelf IT equipment"
RESERVATION_CATEGORIES = ("None", "Youth", "Women", "Persons with disabilities")

CODE_PRODUCT = "TND_PRODUCT_UNSUPPORTED"
CODE_RESERVATION = "TND_RESERVATION_UNSUPPORTED"
CODE_RULE = "TND_RESERVATION_RULE_UNAVAILABLE"


@dataclass(frozen=True)
class Check:
	check: str
	required: str
	actual: str
	ok: bool
	code: str = CODE_PRODUCT

	def as_dict(self) -> dict[str, Any]:
		return {"check": self.check, "required": self.required, "actual": self.actual, "ok": self.ok, "code": "" if self.ok else self.code}


@dataclass(frozen=True)
class Support:
	"""What the bound (or bindable) installed release supports."""

	categories: tuple[str, ...] = ()
	county_residents: bool = False


def support_of(value) -> Support:
	"""Accepts a `Support`, a binding-facts dict (`supported_reservation_categories`,
	`supports_county_residents`) or a bare category sequence (county unsupported)."""
	if isinstance(value, Support):
		return value
	if isinstance(value, dict):
		return Support(tuple(value.get("supported_reservation_categories") or ()), bool(value.get("supports_county_residents")))
	if value is None:
		return current_support()
	return Support(tuple(value))


def current_support() -> Support:
	"""The release a new Tender would bind now (none installed or switched on:
	nothing supported)."""
	from kentender_procurement.std_templates.compiler.errors import STDTemplateError
	from kentender_procurement.tenders.services import template_binding

	try:
		return support_of(template_binding.bind())
	except STDTemplateError:
		return Support()


def supported_reservation_categories(categories=None) -> tuple[str, ...]:
	return support_of(categories).categories


def _is_county_entity() -> bool:
	import frappe

	return bool(frappe.db.get_single_value("Site Procuring Entity", "entity_is_county"))


def _rule_ids(payload: dict[str, Any]) -> list[str]:
	ids = payload.get("reservation_rule_snapshot_ids") or []
	return [i for i in ids if i] if isinstance(ids, list) else []


def _reservation(payload: dict[str, Any], support: Support) -> Check:
	designation = str(payload.get("reservation_category_value") or payload.get("reservation_category") or "None").strip() or "None"
	required = "A category supported by the bound template release, with its verified rule"
	if designation not in RESERVATION_CATEGORIES or designation not in support.categories:
		return Check("Reservation", required, designation, False, CODE_RESERVATION)
	if not _rule_ids(payload):
		return Check("Reservation", required, f"{designation} · rule not ready", False, CODE_RULE)
	return Check("Reservation", required, designation, True)


def _county(payload: dict[str, Any], support: Support) -> Check:
	required = "Not applicable, or a verified rule for a county Procuring Entity"
	if not payload.get("county_resident_reservation"):
		return Check("County-residents restriction", required, "Not applicable", True)
	if not support.county_residents or not _is_county_entity():
		return Check("County-residents restriction", required, "County residents · not supported", False, CODE_RESERVATION)
	if len(_rule_ids(payload)) < 2:
		return Check("County-residents restriction", required, "County residents · rule not ready", False, CODE_RULE)
	return Check("County-residents restriction", required, "County residents", True)


def evaluate(payload: dict[str, Any], reservation_support=None) -> list[Check]:
	support = support_of(reservation_support)
	items = payload.get("items") or []
	equipment_ok = bool(items) and payload.get("product_pattern") == "IT Equipment" and all((row.get("equipment_category") in OFF_THE_SHELF_CATEGORIES) and float(row.get("quantity") or 0) > 0 for row in items)
	categories = ", ".join(sorted({str(r.get("equipment_category")) for r in items})) if items else "no items"
	currency = payload.get("currency") or "KES"
	packages = payload.get("award_packages") or 1
	return [
		Check("Procurement category", "Goods", str(payload.get("procurement_category") or "—"), payload.get("procurement_category") == "Goods"),
		Check("Product", PRODUCT_LABEL, f"{payload.get('product_pattern') or '—'}: {categories}", equipment_ok),
		Check("Method", "Open Tender", str(payload.get("planned_method") or "—"), payload.get("planned_method") == "Open Tender"),
		_reservation(payload, support),
		_county(payload, support),
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


def require_supported(payload: dict[str, Any], reservation_support=None) -> list[Check]:
	from kentender_procurement.tenders.services.errors import fail

	checks = evaluate(payload, reservation_support)
	failed = first_failure(checks)
	if failed:
		fail(failed.code, detail={"check": failed.check, "required": failed.required, "actual": failed.actual, "checks": [c.as_dict() for c in checks]})
	return checks
