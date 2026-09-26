# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""`CheckSTDReleaseCompatibility` — the deterministic supported/rejected
result for an authorised Requisition or Tender input (STD-TPL-IMP-001 v1.0
§6; STD-TPL-001 v0.10 §2).

The product boundary comes only from the release's `product_profile.json`
`supported_use`; nothing is inferred from a Planning label, an address or a
display value. Rejection is a compatibility outcome, never an invitation to
configure the template. Pure Python: no Frappe import.
"""

from __future__ import annotations

from typing import Any

FACT_KEYS: tuple[str, ...] = (
	"procurement_category",
	"product_pattern",
	"equipment_categories",
	"procurement_method",
	"lotting_indicator",
	"award_packages",
	"currency",
	"plan_horizon",
	"reservation_category",
	"county_residents",
	"overlap_treatment",
	"related_service_types",
	"characteristic_controls",
)


def _check(check: str, required: str, actual: str, ok: bool, fact: str) -> dict[str, Any]:
	return {"check": check, "required": required, "actual": actual, "ok": bool(ok), "fact": fact}


def evaluate(profile: dict[str, Any], facts: dict[str, Any]) -> list[dict[str, Any]]:
	missing = [k for k in FACT_KEYS if k not in facts]
	if missing:
		raise ValueError(f"compatibility facts missing: {', '.join(missing)}")
	use = profile["supported_use"]
	categories = list(facts["equipment_categories"])
	services = list(facts["related_service_types"])
	controls = list(facts["characteristic_controls"])
	county = facts["county_residents"]
	county_ok = county == "Not applicable" or (county == "Applicable" and use["county_residents"]["released"])
	return [
		_check("Procurement category", use["procurement_category"], str(facts["procurement_category"]), facts["procurement_category"] == use["procurement_category"], "procurement_category"),
		_check(
			"Product",
			use["product"],
			f"{facts['product_pattern']}: {', '.join(sorted(categories)) or 'no items'}",
			facts["product_pattern"] == use["product_pattern"] and bool(categories) and set(categories) <= set(use["equipment_categories"]),
			"equipment_categories",
		),
		_check("Method", use["procurement_method"], str(facts["procurement_method"]), facts["procurement_method"] == use["procurement_method"], "procurement_method"),
		_check(
			"Reservation",
			", ".join(use["reservation_categories"]),
			str(facts["reservation_category"]),
			facts["reservation_category"] in use["reservation_categories"],
			"reservation_category",
		),
		_check(
			"Reservation and County-residents overlap",
			", ".join(use["county_residents"]["supported_overlap_treatments"]) or "No overlap treatment is released",
			str(facts["overlap_treatment"]) if county == "Applicable" and facts["reservation_category"] != "None" else "Not applicable",
			not (county == "Applicable" and facts["reservation_category"] != "None")
			or facts["overlap_treatment"] in use["county_residents"]["supported_overlap_treatments"],
			"overlap_treatment",
		),
		_check("County-residents restriction", use["county_residents"]["treatment"], str(county), county_ok, "county_residents"),
		_check("Lotting", use["lotting_indicator"], str(facts["lotting_indicator"]), facts["lotting_indicator"] == use["lotting_indicator"], "lotting_indicator"),
		_check("Currency", use["currency"], str(facts["currency"]), facts["currency"] == use["currency"], "currency"),
		_check("Award package", str(use["award_packages"]), str(facts["award_packages"]), str(facts["award_packages"]) == str(use["award_packages"]), "award_packages"),
		_check("Plan horizon", use["plan_horizon"], str(facts["plan_horizon"]), facts["plan_horizon"] == use["plan_horizon"], "plan_horizon"),
		_check(
			"Related services",
			"Ancillary " + ", ".join(use["related_service_types"]).lower() + " only",
			", ".join(services) or "None",
			set(services) <= set(use["related_service_types"]),
			"related_service_types",
		),
		_check(
			"Technical requirements",
			"Characteristics the released renderer supports",
			", ".join(sorted(set(controls))) or "None",
			bool(controls) and set(controls) <= set(profile["characteristic_controls"]),
			"characteristic_controls",
		),
	]


def is_supported(checks: list[dict[str, Any]]) -> bool:
	return all(c["ok"] for c in checks)


def first_failure(checks: list[dict[str, Any]]) -> dict[str, Any] | None:
	return next((c for c in checks if not c["ok"]), None)


def facts_from_projection(projection: dict[str, Any]) -> dict[str, Any]:
	req = projection["requisition"]
	tender = projection["tender"]
	return {
		"procurement_category": req["procurement_category"],
		"product_pattern": req["product_pattern"],
		"equipment_categories": sorted({i["equipment_category"] for i in projection["items"]}),
		"procurement_method": tender["procurement_method"],
		"lotting_indicator": tender["lotting_indicator"],
		"award_packages": tender["award_packages"],
		"currency": tender["currency"],
		"plan_horizon": req["plan_horizon"],
		"reservation_category": projection["reservation"]["category"],
		"county_residents": projection["reservation"]["county_residents"],
		"overlap_treatment": projection["reservation"]["overlap_treatment"],
		"related_service_types": sorted({s["service_type"] for s in projection["related_services"]}),
		"characteristic_controls": sorted({t["control"] for t in projection["technical_requirements"]}),
	}
