# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0210 — Evaluation and qualification options as STD parameters.

Persists only pack-approved parameterized fields. Manual criteria injection is denied.

Output staleness for parameter codes is defined in ``PARAMETER_CODE_TO_STALE_OUTPUTS``.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.parameter import (
	StdInstanceParameterService,
	_normalize_pc,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_EVALUATION_OPTIONS_CHANGED,
	WORKS_MANUAL_CRITERIA_DENIED,
	emit_works_completion_audit,
	emit_works_output_stale_if_new,
	stale_logical_outputs_snapshot,
	union_stale_outputs_for_parameter_codes,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)

SEVERITY_CRITICAL = "Critical"
SEVERITY_HIGH = "High"

# Representative YAML (flattened parameter_code → single ``value`` column).
EVAL_PARAMETER_CODES: tuple[str, ...] = (
	"minimum_average_annual_turnover_amount",
	"minimum_average_annual_turnover_currency",
	"minimum_average_annual_turnover_years",
	"similar_works_experience_minimum_contracts",
	"similar_works_experience_minimum_value_each",
	"similar_works_experience_period_years",
	"key_personnel_required",
	"equipment_schedule_required",
	"margin_of_preference_applicable",
)

PROHIBITED_PAYLOAD_KEYS_LOWER: frozenset[str] = frozenset(
	{
		"manual_criteria",
		"custom_scoring_rules",
		"hidden_rules",
		"free_text_evaluation_method",
		"committee_added_criteria",
	}
)

DENY_CODE = "WORKS_MANUAL_EVALUATION_CRITERIA_DENIED"
DENY_MESSAGE = _(
	"Evaluation criteria must originate from the structured STD template and approved parameterized options."
)


def _stringify_value(val: Any) -> str:
	if val is None:
		return ""
	if isinstance(val, bool):
		return "1" if val else "0"
	if isinstance(val, (int, float)):
		return str(int(val)) if isinstance(val, float) and val == int(val) else str(val)
	return str(val).strip()


def _walk_for_prohibited_keys(obj: Any) -> str | None:
	"""Return first prohibited key found (original key string), else None."""
	if isinstance(obj, dict):
		for k, v in obj.items():
			kn = (k or "").strip().lower()
			if kn in PROHIBITED_PAYLOAD_KEYS_LOWER:
				return str(k)
			found = _walk_for_prohibited_keys(v)
			if found:
				return found
	elif isinstance(obj, list):
		for item in obj:
			found = _walk_for_prohibited_keys(item)
			if found:
				return found
	return None


def find_prohibited_evaluation_key(obj: Any) -> str | None:
	"""Return the first denied evaluation-injection key found in ``obj`` (any JSON tree), else None."""
	if obj is None:
		return None
	return _walk_for_prohibited_keys(obj)


def assert_no_manual_criteria(
	evaluation_options: dict[str, Any] | None,
	*,
	instance_code: str | None = None,
	performed_by: str | None = None,
) -> None:
	"""Reject payloads that attempt ad-hoc evaluation rules (stable denial code).

	Raises ``ValidationError`` when a prohibited key appears anywhere in the structure.
	"""
	if not evaluation_options:
		return
	bad = find_prohibited_evaluation_key(evaluation_options)
	if bad:
		inst = (instance_code or "").strip()
		if inst:
			emit_works_completion_audit(
				WORKS_MANUAL_CRITERIA_DENIED,
				inst,
				details={"prohibited_key": bad, "legacy_deny_code": DENY_CODE},
				performed_by=performed_by,
			)
		frappe.throw(
			_("{0}: {1} (key: {2})").format(DENY_CODE, str(DENY_MESSAGE), bad),
			title=_("Works evaluation options"),
		)


def _flatten_evaluation_payload(raw: dict[str, Any]) -> dict[str, Any]:
	"""Normalize nested pack shapes to flat ``EVAL_PARAMETER_CODES`` keys."""
	out: dict[str, Any] = {}
	for k, v in (raw or {}).items():
		kn = (k or "").strip()
		if kn == "minimum_average_annual_turnover" and isinstance(v, dict):
			for sk in ("amount", "currency", "years"):
				if sk in v:
					out[f"minimum_average_annual_turnover_{sk}"] = v.get(sk)
		elif kn == "similar_works_experience" and isinstance(v, dict):
			for sk in ("minimum_contracts", "minimum_value_each", "period_years"):
				if sk in v:
					out[f"similar_works_experience_{sk}"] = v.get(sk)
		else:
			out[kn] = v
	return out


def _merged_eval_state(instance_name: str, patch: dict[str, Any] | None) -> dict[str, str]:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	state: dict[str, str] = {code: "" for code in EVAL_PARAMETER_CODES}
	for row in doc.parameter_values or []:
		pc = _normalize_pc(row.parameter_code)
		if pc in state:
			state[pc] = (row.value or "").strip()
	if patch:
		for k, v in patch.items():
			if k in state:
				state[k] = _stringify_value(v)
	return state


def _positive_int_or_empty(raw: str) -> tuple[bool, bool]:
	"""Returns (ok, was_empty)."""
	s = (raw or "").strip()
	if not s:
		return True, True
	try:
		n = int(s)
		return n > 0, False
	except Exception:
		return False, False


def _positive_decimal_or_empty(raw: str) -> tuple[bool, bool]:
	s = (raw or "").strip()
	if not s:
		return True, True
	try:
		d = Decimal(s.replace(",", ""))
		return d > 0, False
	except (InvalidOperation, ValueError):
		return False, False


def _truthy_string(val: str | None) -> bool:
	s = (val or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _validate_eval_values(state: dict[str, str]) -> list[dict[str, str]]:
	blockers: list[dict[str, str]] = []

	ok, _amt_empty = _positive_decimal_or_empty(state.get("minimum_average_annual_turnover_amount", ""))
	if not ok:
		blockers.append(
			{
				"code": "EVAL_TURNOVER_AMOUNT_INVALID",
				"message": _("Minimum average annual turnover amount must be a positive number when provided."),
				"severity": SEVERITY_HIGH,
			}
		)

	y_ok, _years_empty = _positive_int_or_empty(state.get("minimum_average_annual_turnover_years", ""))
	if not y_ok:
		blockers.append(
			{
				"code": "EVAL_TURNOVER_YEARS_INVALID",
				"message": _("Minimum average annual turnover years must be a positive whole number when provided."),
				"severity": SEVERITY_HIGH,
			}
		)

	amt = (state.get("minimum_average_annual_turnover_amount") or "").strip()
	cur = (state.get("minimum_average_annual_turnover_currency") or "").strip()
	if amt and not cur:
		blockers.append(
			{
				"code": "EVAL_TURNOVER_CURRENCY_MISSING",
				"message": _("Currency is required when a turnover amount is provided."),
				"severity": SEVERITY_CRITICAL,
			}
		)
	if cur and not amt:
		blockers.append(
			{
				"code": "EVAL_TURNOVER_AMOUNT_MISSING",
				"message": _("Turnover amount is required when currency is provided."),
				"severity": SEVERITY_CRITICAL,
			}
		)

	c_ok, _c_empty = _positive_int_or_empty(state.get("similar_works_experience_minimum_contracts", ""))
	if not c_ok:
		blockers.append(
			{
				"code": "EVAL_SIMILAR_CONTRACTS_INVALID",
				"message": _("Similar works minimum contracts must be a positive whole number when provided."),
				"severity": SEVERITY_HIGH,
			}
		)

	v_ok, _v_empty = _positive_decimal_or_empty(state.get("similar_works_experience_minimum_value_each", ""))
	if not v_ok:
		blockers.append(
			{
				"code": "EVAL_SIMILAR_VALUE_INVALID",
				"message": _("Similar works minimum value must be a positive number when provided."),
				"severity": SEVERITY_HIGH,
			}
		)

	p_ok, _p_empty = _positive_int_or_empty(state.get("similar_works_experience_period_years", ""))
	if not p_ok:
		blockers.append(
			{
				"code": "EVAL_PERIOD_YEARS_INVALID",
				"message": _("Similar works period (years) must be a positive whole number when provided."),
				"severity": SEVERITY_HIGH,
			}
		)

	# Boolean-like fields: if present and non-empty, must parse as bool-ish
	for key in ("key_personnel_required", "equipment_schedule_required", "margin_of_preference_applicable"):
		raw = (state.get(key) or "").strip()
		if raw and not _truthy_string(raw) and raw.lower() not in ("0", "false", "no", "n", "off"):
			blockers.append(
				{
					"code": "EVAL_BOOLEAN_FIELD_INVALID",
					"message": _("Field {0} must be a yes/no value when provided.").format(key),
					"severity": SEVERITY_HIGH,
				}
			)

	return blockers


class WorksEvaluationOptionsService:
	"""Save and validate Works evaluation / qualification parameter values."""

	@staticmethod
	def validate_evaluation_options(
		instance_code: str,
		prospective_values: dict[str, Any] | None = None,
	) -> dict[str, Any]:
		"""Return ``{"valid": bool, "blockers": [{"code","message","severity"}, ...]}``."""
		code = (instance_code or "").strip()
		if not code or not frappe.db.exists("Tender STD Instance", code):
			return {
				"valid": False,
				"blockers": [
					{
						"code": "WORKS_INSTANCE_NOT_FOUND",
						"message": _("Tender STD Instance was not found."),
						"severity": SEVERITY_CRITICAL,
					}
				],
			}

		if prospective_values is not None:
			state = _merged_eval_state(code, prospective_values)
		else:
			state = _merged_eval_state(code, None)

		blockers = _validate_eval_values(state)
		return {"valid": not blockers, "blockers": blockers}

	@staticmethod
	def save_evaluation_options(
		instance_code: str,
		evaluation_options: dict[str, Any],
		actor: str | None = None,
	) -> dict[str, Any]:
		"""Persist evaluation-options patch; raises ``ValidationError`` on context/denial/validation failure."""
		code = (instance_code or "").strip()
		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			msgs = ", ".join(str(b.get("message") or b.get("code")) for b in (ctx.get("blockers") or []))
			frappe.throw(
				_("Cannot save evaluation options: {0}").format(msgs or _("invalid Works completion context")),
				title=_("Works evaluation options"),
			)

		raw = evaluation_options if isinstance(evaluation_options, dict) else {}
		assert_no_manual_criteria(raw, instance_code=code, performed_by=actor or frappe.session.user)

		flat = _flatten_evaluation_payload(raw)
		patch = {k: v for k, v in flat.items() if k in EVAL_PARAMETER_CODES}

		merged = _merged_eval_state(code, patch)
		val = WorksEvaluationOptionsService.validate_evaluation_options(code, prospective_values=merged)
		if not val.get("valid"):
			blocks = val.get("blockers") or []
			parts = [str(b.get("message") or b.get("code")) for b in blocks]
			frappe.throw(
				_("Evaluation options validation failed: {0}").format("; ".join(parts)),
				title=_("Works evaluation options"),
			)

		user = actor or frappe.session.user
		stale_before = stale_logical_outputs_snapshot(code)
		for key in sorted(patch.keys()):
			StdInstanceParameterService.set_parameter_value(
				code,
				key,
				_stringify_value(patch[key]) or None,
				source="Works Evaluation Options",
				user=user,
				ignore_publication_lock=False,
			)

		affected = union_stale_outputs_for_parameter_codes(patch.keys())
		emit_works_completion_audit(
			WORKS_EVALUATION_OPTIONS_CHANGED,
			code,
			affected_outputs=affected,
			details={"parameter_codes": sorted(patch.keys())},
			performed_by=user,
		)
		emit_works_output_stale_if_new(
			code, stale_before, source="evaluation_options", performed_by=user
		)

		return {"ok": True, "instance_code": code}
