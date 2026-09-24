# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §5A — the nine product-compatibility checks, run at
`PrepareITEquipmentRequisition` before any Draft exists and again at
`AuthoriseRequisition`.

Each check is independent and named on failure (REQ19-AC-053, REQ111-AC-005).
They are product compatibility only: not a candidate-entitlement decision and
never an APP-wide 30% calculation. The designation and County checks consume
the exact item treatment and verified rule snapshots Planning publishes and
the exact supported treatment the installed `IT-EQUIPMENT-OPEN-V1` release
declares; REQ derives neither.

"Requirement type" has no field of its own in the spec; Planning's
`requirement_type` (the statutory classification) is the nearest real fact,
so the check requires `Goods` there, beside `procurement_category`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

BASE_DESIGNATIONS = ("None", "Youth", "Women", "Persons with disabilities")
TEMPLATE_KEY = "IT-EQUIPMENT-OPEN-V1"

UNSUPPORTED = "REQ_PRODUCT_UNSUPPORTED"
RULE_UNAVAILABLE = "REQ_RESERVATION_RULE_UNAVAILABLE"


@dataclass(frozen=True)
class Check:
	test: str
	label: str
	ok: bool
	result: str
	failure: str = ""
	code: str = UNSUPPORTED

	def as_dict(self) -> dict[str, Any]:
		return {"test": self.test, "check": self.label, "ok": self.ok, "result": self.result, "failure": self.failure, "code": "" if self.ok else self.code}


def template_support() -> dict[str, Any]:
	"""The installed release's own declared treatment, read through the
	template owner's published loader/registry. Unavailable is a fact here,
	not an exception."""
	from kentender_procurement.tender_templates import loader, registry

	try:
		meta = loader.metadata()
	except Exception:  # noqa: BLE001 — a missing bundle is simply "not available"
		meta = {}
	available = False
	try:
		registry.resolve()
		available = True
	except Exception:  # noqa: BLE001 — TND_TEMPLATE_UNAVAILABLE or not installed
		available = False
	return {
		"template_key": meta.get("template_key") or TEMPLATE_KEY,
		"available": available and (meta.get("template_key") == TEMPLATE_KEY),
		"categories": tuple(c for c in (meta.get("supported_reservation_categories") or ()) if c in BASE_DESIGNATIONS),
		"county_residents": bool(meta.get("supports_county_residents")),
		"method": meta.get("supported_method") or "Open Tender",
	}


def _designation(projection: dict[str, Any], template: dict[str, Any]) -> Check:
	designation = (projection.get("reservation_category") or "None").strip() or "None"
	rule = projection.get("reservation_rule") or {}
	label = "Planned designation"
	if designation not in BASE_DESIGNATIONS or designation not in template["categories"] or not template["available"]:
		return Check("reservation_category", label, False, designation, f"{designation} is not supported by the installed IT-equipment Tender format.")
	if not rule.get("available"):
		return Check("reservation_category", label, False, designation, "The applicable reservation rule is not ready.", RULE_UNAVAILABLE)
	result = "None" if designation == "None" else f"{designation} — supported; exact verified rule snapshot bound"
	return Check("reservation_category", label, True, result)


def _county(projection: dict[str, Any], template: dict[str, Any]) -> Check:
	label = "County-residents restriction"
	if not projection.get("county_resident_reservation"):
		return Check("county_resident_reservation", label, True, "Not applicable")
	if not template["county_residents"]:
		return Check("county_resident_reservation", label, False, "County residents · overlap not supported", "This reservation treatment is not supported by the installed IT-equipment Tender format.")
	if not (projection.get("county_rule") or {}).get("available"):
		return Check("county_resident_reservation", label, False, "County residents · rule not ready", "The applicable reservation rule is not ready.", RULE_UNAVAILABLE)
	return Check("county_resident_reservation", label, True, "County residents — supported; exact verified rule snapshot bound")


def check(projection: dict[str, Any], template: dict[str, Any] | None = None) -> list[Check]:
	"""Every §5A row, in §13.1 table order."""
	template = template if template is not None else template_support()
	category = projection.get("procurement_category") or ""
	requirement_type = projection.get("requirement_type") or ""
	lotting = projection.get("lotting_indicator") or ""
	currency = projection.get("currency") or ""
	packages = str(projection.get("award_packages") or "")
	method = projection.get("procurement_method") or ""
	horizon = projection.get("plan_horizon") or ""
	return [
		Check("procurement_category", "Procurement category", category == "Goods", category or "Not stated", f"Procurement category {category or 'not stated'} is not Goods."),
		Check(
			"requirement_type", "Requirement type", requirement_type == "Goods",
			"Straightforward off-the-shelf IT equipment" if requirement_type == "Goods" else (requirement_type or "Not stated"),
			f"This approved purchase requires {requirement_type or 'an unstated requirement type'}, which this release does not support.",
		),
		_designation(projection, template),
		_county(projection, template),
		Check("lotting_indicator", "Lotting indicator", lotting == "Single lot", lotting or "Not stated", f"Lotting {lotting or 'not stated'} is not Single lot."),
		Check("currency", "Currency", currency == "KES", currency or "Not stated", f"Currency {currency or 'not stated'} is not KES."),
		Check("award_packages", "Award package", packages == "1", "One" if packages == "1" else packages, "This release supports one award package."),
		Check("procurement_method", "Planned method", method == template["method"], method or "Not stated", f"Planned method {method or 'not stated'} is not {template['method']}."),
		Check("plan_horizon", "Plan horizon", horizon == "Single year", horizon or "Not stated", "This release supports purchases completed within one financial year."),
	]


def first_failure(projection: dict[str, Any], template: dict[str, Any] | None = None) -> Check | None:
	for row in check(projection, template):
		if not row.ok:
			return row
	return None


def require_compatible(projection: dict[str, Any], template: dict[str, Any] | None = None) -> list[Check]:
	"""Raise the failing check's own code, naming it; otherwise return all nine."""
	from kentender_procurement.procurement_requisitions.services.errors import fail

	rows = check(projection, template)
	for row in rows:
		if not row.ok:
			fail(row.code, row.failure or None, {"test": row.test, "check": row.label, "result": row.result, "checks": [r.as_dict() for r in rows]})
	return rows
