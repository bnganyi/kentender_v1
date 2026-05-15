# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0810 — ``ManualRuleDenialService`` (pack §15).

Maps pack method names::

	assertNoManualSubmissionRequirement → assert_no_manual_submission_requirement
	assertNoManualOpeningEvaluationField → assert_no_manual_opening_evaluation_field
	validateOpeningRegisterPayload → validate_opening_register_payload
	assertNoManualEvaluationCriteria → assert_no_manual_evaluation_criteria
	assertNoContractDivergence → assert_no_contract_divergence

Tests: ``tender_management.tests.test_derived_manual_rule_denial_0810``;
``tender_management.tests.test_o07_tm2_smoke_open_003_no_arithmetic_correction_at_opening`` (O-07 / doc 8 TM2-SMOKE-OPEN-003);
``tender_management.tests.test_p9_16_opening_readiness_tab`` (``test_EX_08_*`` / doc 9 §25 **EX-08**);
``tender_management.tests.test_o08_tm2_smoke_eval_005_arithmetic_correction_only_in_evaluation``;
``tender_management.tests.test_p9_17_evaluation_handoff_tab`` (``test_EX_09_published_dem_boq_arithmetic_correction_allowed_for_evaluation_consumer`` / doc 9 §25 **EX-09**).
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.dsm.schema import DSM_PROHIBITED_KEYS
from kentender_procurement.tender_management.derived_models.dom.schema import DOM_PROHIBITED_KEYS
from kentender_procurement.tender_management.security.authorization.denial_codes import (
	DenialCode,
)
from kentender_procurement.tender_management.derived_models.events.audit import (
	emit_derived_model_audit,
	pack_manual_denial_event_code,
)
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	find_prohibited_evaluation_key,
)

MANUAL_SUBMISSION_REQUIREMENT_DENIED = DenialCode.MANUAL_SUBMISSION_REQUIREMENT_DENIED
MANUAL_OPENING_EVALUATION_FIELD_DENIED = DenialCode.MANUAL_OPENING_EVALUATION_FIELD_DENIED
MANUAL_EVALUATION_CRITERIA_DENIED = DenialCode.MANUAL_EVALUATION_CRITERIA_DENIED
CONTRACT_BINDING_VIOLATION = DenialCode.CONTRACT_BINDING_VIOLATION
BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION = DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION

# Explicit ad-hoc submission requirement injection (pack §15 / std engine submission boundary).
SUBMISSION_MANUAL_INJECTION_KEYS: frozenset[str] = frozenset(
	{
		"manual_submission_requirement",
		"manual_requirement",
		"ad_hoc_requirement",
		"committee_added_requirement",
		"free_text_requirement",
		"custom_submission_rule",
	}
)

# Contract formation shortcuts that imply divergence from bound DCM.
CONTRACT_DIVERGENCE_KEYS: frozenset[str] = frozenset(
	{
		"diverge_from_dcm",
		"override_dcm",
		"silent_contract_change",
		"non_dcm_contract_terms",
		"manual_contract_clause",
	},
)

_BOQ_ARITHMETIC_STRUCTURE_KEYS: frozenset[str] = frozenset(
	{
		"arithmetic_correction",
		"arithmetic_corrections",
		"boq_arithmetic_correction",
		"corrected_evaluated_boq_total",
	}
)


def _as_dict(payload: Any) -> dict[str, Any] | None:
	if payload is None:
		return None
	if isinstance(payload, dict):
		return payload
	if isinstance(payload, str):
		s = payload.strip()
		if not s:
			return {}
		try:
			parsed: Any = json.loads(s)
		except Exception:
			return None
		return parsed if isinstance(parsed, dict) else None
	return None


def _first_prohibited_key(obj: Any, forbidden: frozenset[str]) -> str | None:
	if isinstance(obj, dict):
		for k, v in obj.items():
			kn = (k or "").strip()
			if kn in forbidden:
				return kn
			found = _first_prohibited_key(v, forbidden)
			if found:
				return found
	elif isinstance(obj, list):
		for it in obj:
			found = _first_prohibited_key(it, forbidden)
			if found:
				return found
	return None


def _first_prohibited_key_any(root: Any, forbidden: frozenset[str]) -> str | None:
	if isinstance(root, list):
		for it in root:
			found = _first_prohibited_key(it, forbidden)
			if found:
				return found
		return None
	return _first_prohibited_key(root, forbidden)


def _has_boq_arithmetic_stage(obj: Any) -> bool:
	if isinstance(obj, dict):
		if (obj.get("stage_type") or "").strip() == "BOQArithmetic":
			return True
		return any(_has_boq_arithmetic_stage(v) for v in obj.values())
	if isinstance(obj, list):
		return any(_has_boq_arithmetic_stage(x) for x in obj)
	return False


def _submission_requirement_rows_missing_trace(obj: Any) -> bool:
	"""Detect DSM-shaped requirement rows without ``source_trace`` (must trace to STD)."""
	if isinstance(obj, dict):
		for key in ("requirements", "submission_requirements"):
			rows = obj.get(key)
			if not isinstance(rows, list):
				continue
			for row in rows:
				if not isinstance(row, dict):
					continue
				if not (row.get("requirement_code") or "").strip():
					continue
				tr = row.get("source_trace")
				if not isinstance(tr, dict) or not (tr.get("source_type") or "").strip():
					return True
		for v in obj.values():
			if _submission_requirement_rows_missing_trace(v):
				return True
	elif isinstance(obj, list):
		return any(_submission_requirement_rows_missing_trace(x) for x in obj)
	return False


def _canonical_json(val: Any) -> str:
	if val is None:
		return "null"
	if isinstance(val, str):
		s = val.strip()
		if s and s[0] in "{[":
			try:
				return json.dumps(json.loads(s), sort_keys=True, separators=(",", ":"))
			except Exception:
				pass
	return json.dumps(val, sort_keys=True, separators=(",", ":"))


def _parse_content_json(raw: Any) -> dict[str, Any] | None:
	if raw is None:
		return None
	if isinstance(raw, dict):
		return raw
	if isinstance(raw, str):
		s = raw.strip()
		if not s:
			return {}
		try:
			parsed: Any = json.loads(s)
		except Exception:
			return None
		return parsed if isinstance(parsed, dict) else None
	return None


def _emit_denial(
	denial_code: str,
	*,
	hook: str,
	details: dict[str, Any] | None = None,
	instance_code: str | None = None,
) -> None:
	payload = {"denial_code": denial_code, "hook": hook, **(details or {})}
	ic = (instance_code or "").strip() or None
	emit_std_instance_event(
		EVT_STDINST_DENIED_DOWNSTREAM_RULE_INJECTION,
		instance_code=ic,
		document_type="ManualRuleDenialService",
		document_name=denial_code,
		entity="STD_DOWNSTREAM",
		details=payload,
	)
	pack_ev = pack_manual_denial_event_code(denial_code)
	if pack_ev:
		emit_derived_model_audit(
			pack_ev,
			instance_code=ic,
			denial_code=denial_code,
			extra={"hook": hook, **(details or {})},
		)


def _instance_hint(payload: dict[str, Any] | None) -> str | None:
	if not payload:
		return None
	for k in ("std_inst", "tender_std_instance", "instance_code"):
		v = (payload.get(k) or "").strip()
		if v:
			return v
	return None


def _opening_payload_violation(payload: Any) -> dict[str, Any] | None:
	"""Return violation envelope for :meth:`ManualRuleDenialService.assert_no_manual_opening_evaluation_field`, or None."""
	if payload is None:
		return None
	if isinstance(payload, dict) and not payload:
		return None
	if not isinstance(payload, (dict, list)):
		return None
	data_dict: dict[str, Any] = payload if isinstance(payload, dict) else {}

	if _has_boq_arithmetic_stage(payload) or _first_prohibited_key_any(payload, _BOQ_ARITHMETIC_STRUCTURE_KEYS):
		return {
			"denial_code": DenialCode.BOQ_ARITHMETIC_CORRECTION_STAGE_VIOLATION.value,
			"message": _("BOQ arithmetic correction is only allowed in DEM / evaluation stages."),
			"emit_details": {"reason": "boq_arithmetic_in_opening"},
			"data_dict": data_dict,
		}
	bad = _first_prohibited_key_any(payload, DOM_PROHIBITED_KEYS)
	if bad:
		return {
			"denial_code": DenialCode.MANUAL_OPENING_EVALUATION_FIELD_DENIED.value,
			"message": _("Opening/register payloads cannot include evaluation or arithmetic fields (key: {0}).").format(
				bad
			),
			"emit_details": {"prohibited_key": bad},
			"data_dict": data_dict,
		}
	bad = find_prohibited_evaluation_key(payload)
	if bad:
		return {
			"denial_code": DenialCode.MANUAL_OPENING_EVALUATION_FIELD_DENIED.value,
			"message": _("Opening cannot carry evaluation-option injection (key: {0}).").format(bad),
			"emit_details": {"prohibited_evaluation_key": bad},
			"data_dict": data_dict,
		}
	return None


class ManualRuleDenialService:
	"""Pack §15 hooks — stable ``frappe.throw`` titles + audit on every denial."""

	@staticmethod
	def assert_no_manual_submission_requirement(payload: Any) -> None:
		if isinstance(payload, list):
			data: dict[str, Any] | None = {"requirements": payload}
		else:
			data = _as_dict(payload)
		if not data:
			return

		bad = _first_prohibited_key(data, DSM_PROHIBITED_KEYS)
		if bad:
			_emit_denial(
				MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				hook="assert_no_manual_submission_requirement",
				details={"prohibited_key": bad},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Submission requirements must be derived from DSM; prohibited key: {0}").format(bad),
				title=MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				exc=frappe.ValidationError,
			)

		bad = _first_prohibited_key(data, SUBMISSION_MANUAL_INJECTION_KEYS)
		if bad:
			_emit_denial(
				MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				hook="assert_no_manual_submission_requirement",
				details={"injection_key": bad},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Manual submission requirement injection is not allowed (key: {0}).").format(bad),
				title=MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				exc=frappe.ValidationError,
			)

		if _submission_requirement_rows_missing_trace(data):
			_emit_denial(
				MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				hook="assert_no_manual_submission_requirement",
				details={"reason": "missing_source_trace"},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Each submission requirement must include a DSM-grade source_trace."),
				title=MANUAL_SUBMISSION_REQUIREMENT_DENIED,
				exc=frappe.ValidationError,
			)

	@staticmethod
	def validate_opening_register_payload(payload: Any) -> dict[str, Any]:
		"""Doc 8 **TM2-SMOKE-OPEN-003** / doc 9 §25 **EX-08** — opening-side JSON must not carry arithmetic or evaluation injection.

		Returns ``{"ok": True, "message": ...}`` or ``{"ok": False, "denial_code", "message"}`` (no audit; no throw).
		For pack §15 audits + ``frappe.throw``, use :meth:`assert_no_manual_opening_evaluation_field`.
		"""
		v = _opening_payload_violation(payload)
		if v:
			return {
				"ok": False,
				"denial_code": v["denial_code"],
				"message": str(v["message"]),
			}
		return {"ok": True, "message": _("Opening register payload is acceptable.")}

	@staticmethod
	def validateOpeningRegisterPayload(payload: Any) -> dict[str, Any]:
		"""CamelCase alias for :meth:`validate_opening_register_payload`."""
		return ManualRuleDenialService.validate_opening_register_payload(payload)

	@staticmethod
	def assert_no_manual_opening_evaluation_field(payload: Any) -> None:
		v = _opening_payload_violation(payload)
		if not v:
			return
		dc = str(v["denial_code"])
		_emit_denial(
			dc,
			hook="assert_no_manual_opening_evaluation_field",
			details=v.get("emit_details"),
			instance_code=_instance_hint(v.get("data_dict")),
		)
		frappe.throw(
			v["message"],
			title=dc,
			exc=frappe.ValidationError,
		)

	@staticmethod
	def assert_no_manual_evaluation_criteria(payload: Any) -> None:
		if payload is None:
			return
		if isinstance(payload, dict) and not payload:
			return
		if not isinstance(payload, (dict, list)):
			return
		data = payload if isinstance(payload, dict) else {}
		bad = find_prohibited_evaluation_key(payload)
		if bad:
			_emit_denial(
				MANUAL_EVALUATION_CRITERIA_DENIED,
				hook="assert_no_manual_evaluation_criteria",
				details={"prohibited_key": bad},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Evaluation criteria must come from DEM; prohibited key: {0}").format(bad),
				title=MANUAL_EVALUATION_CRITERIA_DENIED,
				exc=frappe.ValidationError,
			)

	@staticmethod
	def assert_no_contract_divergence(contract_payload: Any, dcm_output_code: str) -> None:
		data = _as_dict(contract_payload)
		if not data:
			return

		name = (dcm_output_code or "").strip()
		if not name or not frappe.db.exists("Tender STD Generated Output", name):
			_emit_denial(
				CONTRACT_BINDING_VIOLATION,
				hook="assert_no_contract_divergence",
				details={"reason": "dcm_output_not_found", "dcm_output_code": name},
				instance_code=_instance_hint(data),
			)
			frappe.throw(_("DCM output not found."), title=CONTRACT_BINDING_VIOLATION, exc=frappe.ValidationError)

		doc = frappe.get_doc("Tender STD Generated Output", name)
		if (doc.output_type or "").strip() != "DCM":
			_emit_denial(
				CONTRACT_BINDING_VIOLATION,
				hook="assert_no_contract_divergence",
				details={"reason": "not_dcm_row", "output_type": doc.output_type},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Bound output must be a DCM row."),
				title=CONTRACT_BINDING_VIOLATION,
				exc=frappe.ValidationError,
			)

		bad = _first_prohibited_key(data, CONTRACT_DIVERGENCE_KEYS)
		if bad:
			_emit_denial(
				CONTRACT_BINDING_VIOLATION,
				hook="assert_no_contract_divergence",
				details={"prohibited_key": bad, "dcm_output_code": name},
				instance_code=_instance_hint(data),
			)
			frappe.throw(
				_("Contract cannot diverge from DCM (key: {0}).").format(bad),
				title=CONTRACT_BINDING_VIOLATION,
				exc=frappe.ValidationError,
			)

		dcm_content = _parse_content_json(doc.get("content_json"))
		if not dcm_content:
			return

		dcm_terms: dict[str, dict[str, Any]] = {}
		for row in dcm_content.get("contract_terms") or []:
			if not isinstance(row, dict):
				continue
			tc = (row.get("term_code") or "").strip()
			if tc:
				dcm_terms[tc] = row

		terms = data.get("contract_terms")
		if not isinstance(terms, list):
			return

		for row in terms:
			if not isinstance(row, dict):
				continue
			tc = (row.get("term_code") or "").strip()
			if not tc:
				continue
			if tc not in dcm_terms:
				_emit_denial(
					CONTRACT_BINDING_VIOLATION,
					hook="assert_no_contract_divergence",
					details={"reason": "unknown_term", "term_code": tc, "dcm_output_code": name},
					instance_code=_instance_hint(data),
				)
				frappe.throw(
					_("Contract term {0} is not present on the bound DCM output.").format(tc),
					title=CONTRACT_BINDING_VIOLATION,
					exc=frappe.ValidationError,
				)
			base = dcm_terms[tc]
			editable = bool(base.get("editable_in_contract"))
			if editable:
				continue
			if _canonical_json(row.get("value")) != _canonical_json(base.get("value")):
				_emit_denial(
					CONTRACT_BINDING_VIOLATION,
					hook="assert_no_contract_divergence",
					details={
						"reason": "immutable_term_changed",
						"term_code": tc,
						"dcm_output_code": name,
					},
					instance_code=_instance_hint(data),
				)
				frappe.throw(
					_("Contract cannot change non-editable DCM term {0}.").format(tc),
					title=CONTRACT_BINDING_VIOLATION,
					exc=frappe.ValidationError,
				)
