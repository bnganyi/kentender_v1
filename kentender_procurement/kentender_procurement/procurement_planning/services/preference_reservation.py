# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Preference / reservation designation helpers (REQ v1.5 / PLN-FR-074…078)."""

from __future__ import annotations

import json
from typing import Any

from frappe.utils import cstr, flt

SCHEME_AGPO = "AGPO reservation"
SCHEME_LOCAL = "Local preference"
SCHEME_OPTIONS = (SCHEME_AGPO, SCHEME_LOCAL)

SCOPE_ENTIRE = "Entire Plan Item"
SCOPE_LOTS = "Reserved lot(s)"
SCOPE_OPTIONS = (SCOPE_ENTIRE, SCOPE_LOTS)

ELIGIBLE_GROUP_OPTIONS = (
	"Women-owned enterprises",
	"Youth-owned enterprises",
	"Enterprises owned by PWDs",
)

# MVP required basis: 30% of plan planned total (Contract v2.5 story arithmetic).
COVERAGE_RATE = 0.30


def parse_eligible_groups(raw: Any) -> list[str]:
	if raw is None:
		return []
	if isinstance(raw, list):
		vals = [cstr(x).strip() for x in raw]
	else:
		text = cstr(raw).strip()
		if not text:
			return []
		try:
			parsed = json.loads(text)
			if isinstance(parsed, list):
				vals = [cstr(x).strip() for x in parsed]
			else:
				vals = [p.strip() for p in text.split(",") if p.strip()]
		except Exception:
			vals = [p.strip() for p in text.split(",") if p.strip()]
	allowed = set(ELIGIBLE_GROUP_OPTIONS)
	out: list[str] = []
	for v in vals:
		if v in allowed and v not in out:
			out.append(v)
	return out


def dump_eligible_groups(groups: list[str]) -> str:
	return json.dumps(groups or [], ensure_ascii=False)


def scheme_is_assigned(scheme: str | None) -> bool:
	return cstr(scheme).strip() in SCHEME_OPTIONS


def derived_reserved_value(*, scope: str, item_value: float, planned: float | None) -> float:
	"""Entire Plan Item derives from item value; reserved lots use explicit planned."""
	if cstr(scope).strip() == SCOPE_ENTIRE:
		return flt(item_value)
	return flt(planned)


def validate_designation(
	*,
	scheme: str | None,
	scope: str | None,
	eligible_groups: Any,
	planned_reserved_value: Any,
	item_value: float,
) -> tuple[dict[str, str], dict[str, Any]]:
	"""Return (errors, normalised_fields). Empty scheme clears designation."""
	errors: dict[str, str] = {}
	scheme_s = cstr(scheme).strip()
	if not scheme_s or scheme_s.lower() in ("none", "none assigned"):
		return {}, {
			"preference_reservation_scheme": "",
			"reservation_scope": "",
			"eligible_groups": dump_eligible_groups([]),
			"planned_reserved_value": 0,
		}

	if scheme_s not in SCHEME_OPTIONS:
		errors["preference_reservation_scheme"] = "Select a configured preference or reservation scheme."
		return errors, {}

	scope_s = cstr(scope).strip()
	if scope_s not in SCOPE_OPTIONS:
		errors["reservation_scope"] = "Select Entire Plan Item or Reserved lot(s)."

	groups = parse_eligible_groups(eligible_groups)
	if not groups:
		errors["eligible_groups"] = "Select at least one eligible group."

	value = derived_reserved_value(
		scope=scope_s,
		item_value=item_value,
		planned=flt(planned_reserved_value),
	)
	if scope_s == SCOPE_LOTS:
		if flt(planned_reserved_value) <= 0:
			errors["planned_reserved_value"] = "Reserved lot(s) require a planned reserved value greater than zero."
		elif flt(planned_reserved_value) > flt(item_value) + 0.0001:
			errors["planned_reserved_value"] = "Planned reserved value cannot exceed the Plan Item value."
		value = flt(planned_reserved_value)
	elif scope_s == SCOPE_ENTIRE and flt(item_value) <= 0:
		errors["planned_reserved_value"] = "Plan Item value is required for whole-item reservation."

	if errors:
		return errors, {}

	return {}, {
		"preference_reservation_scheme": scheme_s,
		"reservation_scope": scope_s,
		"eligible_groups": dump_eligible_groups(groups),
		"planned_reserved_value": value,
	}


def format_money(amount: float, currency: str = "KES") -> str:
	return f"{currency} {flt(amount):,.2f}"


def plan_coverage(
	*,
	planned_total: float,
	designation_values: list[float],
	currency: str = "KES",
) -> dict[str, Any]:
	required = flt(planned_total) * COVERAGE_RATE
	planned = sum(flt(v) for v in designation_values if flt(v) > 0)
	if required <= 0:
		status = "Not applicable"
	elif planned + 0.01 >= required:
		status = "Ready"
	elif planned > 0:
		status = "Needs attention"
	else:
		status = "Not started"
	display = (
		f"Preference and reservation coverage: {format_money(planned, currency)} planned of "
		f"{format_money(required, currency)} required · {status}"
	)
	return {
		"required": required,
		"planned": planned,
		"status_label": status,
		"display": display,
		"rate": COVERAGE_RATE,
	}
