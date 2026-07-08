# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0400 — SCC completion (pack blocker codes + STD parameter rows).

Persists representative SCC fields as ``Tender STD Instance`` parameter values via
``StdInstanceParameterService``. GCC clause text is never edited here.

Canonical ``parameter_code`` keys follow Works POC ``render_targets`` (``scc.*``).
Pack-facing aliases map to those codes — e.g. ``completion_period_days`` is accepted
but stored under ``scc.completion_period_months`` (numeric months).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
	_normalize_pc,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_SCC_VALUES_CHANGED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
	union_stale_outputs_for_parameter_codes,
)
from kentender_procurement.tender_management.services.tender_configuration import parse_configuration_json
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

SCC_PAYMENT_CURRENCY_CODE = "bid_currency"

# Canonical parameter_code strings (Works POC template).
SCC_CANONICAL_CODES: tuple[str, ...] = (
	"scc.completion_period_months",
	"scc.defects_liability_period_months",
	"scc.performance_security_required",
	"scc.performance_security_percentage",
	"scc.retention_percentage",
	"scc.liquidated_damages_rate",
	"scc.advance_payment_allowed",
	"scc.insurance_requirements",
	"scc.engineer_or_project_manager",
	"scc.payment_terms",
	"scc.dispute_resolution_forum",
	"scc.maximum_liquidated_damages_percent",
)

# Pack / API aliases → canonical parameter_code.
ALIAS_TO_CANONICAL: dict[str, str] = {
	"completion_period_days": "scc.completion_period_months",
	"defects_liability_period_days": "scc.defects_liability_period_months",
	"performance_security_percent": "scc.performance_security_percentage",
	"retention_percent": "scc.retention_percentage",
	"liquidated_damages_percent_per_day": "scc.liquidated_damages_rate",
	"maximum_liquidated_damages_percent": "scc.maximum_liquidated_damages_percent",
	"advance_payment_allowed": "scc.advance_payment_allowed",
	"payment_currency": SCC_PAYMENT_CURRENCY_CODE,
}

SCC_SAVE_KEYS: frozenset[str] = frozenset(SCC_CANONICAL_CODES) | frozenset({SCC_PAYMENT_CURRENCY_CODE})

_CODE_MESSAGES: dict[str, str] = {
	"WORKS_INSTANCE_NOT_FOUND": _("Tender STD Instance was not found."),
	"SCC_COMPLETION_PERIOD_MISSING": _("Contract completion period (months) is required."),
	"SCC_DEFECTS_LIABILITY_MISSING": _("Defects liability period (months) is required."),
	"SCC_PERFORMANCE_SECURITY_MISSING": _("Performance security percentage is required when performance security is enabled."),
	"SCC_LD_CAP_INVALID": _("Retention, liquidated damages cap, or liquidated damages rate is invalid."),
	"SCC_PAYMENT_CURRENCY_MISSING": _("Payment / bid currency is required."),
	"SCC_INSURANCE_MISSING": _("Insurance requirements text is required."),
}


def _norm(value: str | None) -> str:
	return (value or "").strip()


def _truthy(val: str | None) -> bool:
	s = _norm(val).lower()
	return s in ("1", "true", "yes", "y", "on")


def _stringify_scc_value(val: Any) -> str:
	if val is None:
		return ""
	if isinstance(val, bool):
		return "1" if val else "0"
	if isinstance(val, (int, float)):
		return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
	return str(val).strip()


def _resolve_canonical_key(key: str) -> str:
	k = _norm(key)
	if not k:
		return ""
	if k in SCC_SAVE_KEYS:
		return k
	return ALIAS_TO_CANONICAL.get(k, k)


def _all_state_codes() -> frozenset[str]:
	return SCC_SAVE_KEYS


def _merged_scc_state(instance_name: str, patch: dict[str, Any] | None) -> dict[str, str]:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	state: dict[str, str] = {c: "" for c in _all_state_codes()}
	for row in doc.parameter_values or []:
		pc = _normalize_pc(row.parameter_code)
		if pc in state:
			state[pc] = _norm(row.value)
	if patch:
		for k, v in patch.items():
			canonical = _resolve_canonical_key(str(k))
			if canonical in state:
				state[canonical] = _stringify_scc_value(v)
	return state


def _months_positive(raw: str | None) -> bool:
	s = _norm(raw)
	if not s:
		return False
	try:
		return float(s) > 0
	except Exception:
		return False


def _retention_numeric(raw: str | None) -> float | None:
	s = _norm(raw)
	if not s:
		return None
	try:
		return float(s)
	except Exception:
		return None


def _max_ld_numeric(raw: str | None) -> float | None:
	s = _norm(raw)
	if not s:
		return None
	try:
		return float(s)
	except Exception:
		return None


def _tender_cfg_for_instance(instance_name: str) -> dict[str, Any]:
	tm2 = frappe.db.get_value("Tender STD Instance", instance_name, "tm2_tender")
	if not tm2 or not frappe.db.exists("TM2 Tender", tm2):
		return {}
	tender = frappe.get_doc("TM2 Tender", tm2)
	return parse_configuration_json(tender)


def _truthy_cfg(val: Any) -> bool:
	if isinstance(val, bool):
		return val
	s = str(val or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _validate_scc_state(state: dict[str, str], *, require_insurance: bool = True) -> list[dict[str, str]]:
	blockers: list[dict[str, str]] = []

	if not _months_positive(state.get("scc.completion_period_months")):
		blockers.append(
			{
				"code": "SCC_COMPLETION_PERIOD_MISSING",
				"message": str(_CODE_MESSAGES["SCC_COMPLETION_PERIOD_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	if not _months_positive(state.get("scc.defects_liability_period_months")):
		blockers.append(
			{
				"code": "SCC_DEFECTS_LIABILITY_MISSING",
				"message": str(_CODE_MESSAGES["SCC_DEFECTS_LIABILITY_MISSING"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	ps_req = _truthy(state.get("scc.performance_security_required"))
	if ps_req:
		if not _norm(state.get("scc.performance_security_percentage")):
			blockers.append(
				{
					"code": "SCC_PERFORMANCE_SECURITY_MISSING",
					"message": str(_CODE_MESSAGES["SCC_PERFORMANCE_SECURITY_MISSING"]),
					"severity": SEVERITY_CRITICAL,
				}
			)

	ret = _retention_numeric(state.get("scc.retention_percentage"))
	ret_invalid = ret is None or ret < 0 or ret > 100

	ld_empty = not _norm(state.get("scc.liquidated_damages_rate"))

	max_ld = _max_ld_numeric(state.get("scc.maximum_liquidated_damages_percent"))
	max_invalid = max_ld is not None and (max_ld < 0 or max_ld > 100)
	cap_order_bad = (
		ret is not None
		and max_ld is not None
		and max_ld < ret
	)

	if ret_invalid or ld_empty or max_invalid or cap_order_bad:
		blockers.append(
			{
				"code": "SCC_LD_CAP_INVALID",
				"message": str(_CODE_MESSAGES["SCC_LD_CAP_INVALID"]),
				"severity": SEVERITY_CRITICAL,
			}
		)

	if not _norm(state.get(SCC_PAYMENT_CURRENCY_CODE)):
		blockers.append(
			{
				"code": "SCC_PAYMENT_CURRENCY_MISSING",
				"message": str(_CODE_MESSAGES["SCC_PAYMENT_CURRENCY_MISSING"]),
				"severity": SEVERITY_HIGH,
			}
		)

	if require_insurance and not _norm(state.get("scc.insurance_requirements")):
		blockers.append(
			{
				"code": "SCC_INSURANCE_MISSING",
				"message": str(_CODE_MESSAGES["SCC_INSURANCE_MISSING"]),
				"severity": SEVERITY_HIGH,
			}
		)

	return blockers


class WorksSccCompletionService:
	"""Save and validate Works SCC parameter values."""

	@staticmethod
	def validate_scc_values(
		instance_code: str,
		prospective_patch: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``.

		If ``prospective_patch`` is set, keys may be aliases or canonical codes; values
		override persisted state for validation only (no save).
		"""
		code = _norm(instance_code)
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": str(_CODE_MESSAGES["WORKS_INSTANCE_NOT_FOUND"]),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		normalized_patch: dict[str, Any] | None = None
		if prospective_patch:
			normalized_patch = {}
			for k, v in prospective_patch.items():
				ck = _resolve_canonical_key(str(k))
				if ck in _all_state_codes():
					normalized_patch[ck] = v

		state = _merged_scc_state(code, normalized_patch)
		cfg = _tender_cfg_for_instance(code)
		ins_optional = _truthy_cfg(cfg.get("WORKS.SCC_INSURANCE_OPTIONAL"))
		blockers = _validate_scc_state(state, require_insurance=not ins_optional)
		return {"valid": not blockers, "blockers": blockers}

	@staticmethod
	def save_scc_values(
		instance_code: str,
		scc_values: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		code = _norm(instance_code)
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save SCC values: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works SCC completion"),
			)

		raw = scc_values if isinstance(scc_values, dict) else {}
		patch_canon: dict[str, Any] = {}
		for k, v in raw.items():
			ck = _resolve_canonical_key(str(k))
			if ck in SCC_SAVE_KEYS:
				patch_canon[ck] = v

		merged = _merged_scc_state(code, patch_canon)
		cfg = _tender_cfg_for_instance(code)
		ins_optional = _truthy_cfg(cfg.get("WORKS.SCC_INSURANCE_OPTIONAL"))
		blockers = _validate_scc_state(merged, require_insurance=not ins_optional)
		if blockers:
			parts = [str(b.get("message") or b.get("code")) for b in blockers]
			frappe.throw(
				_("SCC validation failed: {0}").format("; ".join(parts)),
				title=_("Works SCC completion"),
			)

		user = actor or frappe.session.user
		stale_before = stale_logical_outputs_snapshot(code)
		for ck in sorted(patch_canon.keys()):
			StdInstanceParameterService.set_parameter_value(
				code,
				ck,
				_stringify_scc_value(patch_canon[ck]) or None,
				source="Works SCC Completion",
				drives_bundle=True,
				drives_dcm=True,
				user=user,
				ignore_publication_lock=False,
			)

		affected = union_stale_outputs_for_parameter_codes(patch_canon.keys())
		emit_works_completion_audit(
			WORKS_SCC_VALUES_CHANGED,
			code,
			affected_outputs=affected,
			details={"parameter_codes": sorted(patch_canon.keys())},
			performed_by=user,
		)
		emit_works_output_stale_if_new(code, stale_before, source="scc", performed_by=user)

		return {"ok": True, "instance_code": code}
