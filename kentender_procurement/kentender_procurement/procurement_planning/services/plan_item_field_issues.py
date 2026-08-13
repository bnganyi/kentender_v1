# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Soft field issues for Draft Plan Item editor (PLN-UI-06).

Draft save always persists; these issues flag fields for inline UI and
validation projection / sign-off — they must not block ``update_plan_item``.
"""

from __future__ import annotations

from typing import Any

from frappe.utils import cstr, flt, getdate

from kentender_procurement.procurement_planning.services.preference_reservation import (
	validate_designation,
)

MILESTONE_FIELDS = (
	"ms_invitation_published",
	"ms_tender_opening",
	"ms_evaluation_completed",
	"ms_award_approval",
	"ms_contract_signature",
	"ms_delivery_completion",
)

PREF_KEYS = (
	"preference_reservation_scheme",
	"reservation_scope",
	"eligible_groups",
	"planned_reserved_value",
)


def _merged(iv: Any, payload: dict[str, Any], key: str) -> Any:
	if key in payload:
		return payload.get(key)
	return getattr(iv, key, None)


def collect_plan_item_field_issues(
	*,
	iv: Any,
	payload: dict[str, Any] | None = None,
	include_preference: bool = True,
) -> dict[str, str]:
	"""Return field → human message for incomplete / invalid editor values."""
	payload = payload or {}
	issues: dict[str, str] = {}

	method = cstr(_merged(iv, payload, "procurement_method") or "").strip()
	recommended = cstr(getattr(iv, "recommended_method", None) or "Open tender").strip() or "Open tender"
	if method and method != recommended:
		if not cstr(_merged(iv, payload, "method_override_grounds") or "").strip():
			issues["method_override_grounds"] = "Alternative method requires configured grounds."
		if not cstr(_merged(iv, payload, "method_override_reason") or "").strip():
			issues["method_override_reason"] = "Alternative method requires a reason."
		if not cstr(_merged(iv, payload, "method_override_evidence") or "").strip():
			issues["method_override_evidence"] = "Alternative method requires evidence."

	lotting = cstr(_merged(iv, payload, "lotting_decision") or "").strip()
	if lotting == "Multiple lots":
		try:
			count = int(_merged(iv, payload, "expected_lot_count") or 0)
		except (TypeError, ValueError):
			count = 0
		if count < 2:
			issues["expected_lot_count"] = (
				"Multiple lots requires an expected lot count of at least 2."
			)
		if not cstr(_merged(iv, payload, "lot_basis") or "").strip():
			issues["lot_basis"] = "Confirm the indicative lot basis before submit for review."

	dates: list[tuple[str, Any]] = []
	for key in MILESTONE_FIELDS:
		raw = _merged(iv, payload, key)
		if raw:
			try:
				dates.append((key, getdate(raw)))
			except Exception:
				issues[key] = "Invalid date."
	for i in range(1, len(dates)):
		if dates[i][1] < dates[i - 1][1]:
			issues[dates[i][0]] = "Milestone dates must be in chronological order."

	if include_preference and (
		any(k in payload for k in PREF_KEYS)
		or cstr(getattr(iv, "preference_reservation_scheme", None) or "").strip()
	):
		scheme = _merged(iv, payload, "preference_reservation_scheme")
		scope = _merged(iv, payload, "reservation_scope")
		groups = _merged(iv, payload, "eligible_groups")
		planned = _merged(iv, payload, "planned_reserved_value")
		pref_errors, _pref_norm = validate_designation(
			scheme=scheme,
			scope=scope,
			eligible_groups=groups,
			planned_reserved_value=planned,
			item_value=flt(getattr(iv, "confirmed_estimate", 0)),
		)
		issues.update(pref_errors)

	return issues
