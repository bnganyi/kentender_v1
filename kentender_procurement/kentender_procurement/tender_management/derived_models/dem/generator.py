# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0510 — ``DemGenerator.generateDEM`` (Cursor pack §11 / std engine §9).

Builds DEM ``content_json`` from a ``Tender STD Instance``: seven evaluation stages,
BOQ arithmetic correction block (when BOQ exists), ranking, and parameter-driven
qualification thresholds. Denies manual/hidden evaluation criteria in parameter JSON.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.derived_models.events.audit import emit_derived_model_generation_failed
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUT_GENERATION_FAILED
from kentender_procurement.tender_management.std_instance.parameter import _normalize_pc
from kentender_procurement.tender_management.derived_models.dem.schema import (
	DEM_GENERATION_FAILED,
	MANUAL_EVALUATION_CRITERIA_DENIED,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	EVAL_PARAMETER_CODES,
	find_prohibited_evaluation_key,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	COMPONENT_TO_SECTION_CODE,
)


def _truthy(raw: str | None) -> bool:
	s = (raw or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _param_map(inst: Document) -> dict[str, str]:
	out: dict[str, str] = {}
	for row in inst.parameter_values or []:
		pc = (getattr(row, "parameter_code", None) or "").strip()
		if pc:
			out[pc] = (getattr(row, "value", None) or "").strip()
	return out


def _eval_state(inst: Document) -> dict[str, str]:
	state: dict[str, str] = {c: "" for c in EVAL_PARAMETER_CODES}
	for row in inst.parameter_values or []:
		pc = _normalize_pc(getattr(row, "parameter_code", None) or "")
		if pc in state:
			state[pc] = (getattr(row, "value", None) or "").strip()
	return state


def _scan_parameter_json_for_manual_criteria(inst: Document) -> str | None:
	for row in inst.parameter_values or []:
		raw = (getattr(row, "value", None) or "").strip()
		if not raw or raw[0] not in "{[":
			continue
		try:
			parsed = json.loads(raw)
		except Exception:
			continue
		bad = find_prohibited_evaluation_key(parsed)
		if bad:
			return bad
	return None


def _p_trace(parameter_code: str) -> dict[str, str]:
	return {"source_type": "Parameter", "source_parameter_code": parameter_code}


def _section_trace(section_code: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": section_code}


def _wr_dem_trace(component_code: str) -> dict[str, str]:
	sec = COMPONENT_TO_SECTION_CODE.get(component_code, "VI")
	return {
		"source_type": "WorksRequirement",
		"source_section_code": sec,
		"source_component_code": component_code,
	}


def _boq_section_trace() -> dict[str, str]:
	return {"source_type": "BOQ", "source_section_code": "V"}


def _row_by_component(doc: Document, component_code: str) -> Any | None:
	cc = (component_code or "").strip()
	for row in doc.works_requirements or []:
		if (getattr(row, "component_code", None) or "").strip() == cc:
			return row
	return None


def _parse_flag_required(row: Any | None) -> bool | None:
	if not row:
		return None
	try:
		obj = json.loads(getattr(row, "structured_data", None) or "{}")
	except Exception:
		return None
	if not isinstance(obj, dict) or obj.get("flag_resolved") is not True:
		return None
	return bool(obj.get("required"))


def _rule(
	rule_code: str,
	rule_type: str,
	label: str,
	data_source: str,
	failure_effect: str,
	source_trace: dict[str, str],
	*,
	description: str = "",
	operator: str | None = None,
	threshold_value: Any = None,
) -> dict[str, Any]:
	row: dict[str, Any] = {
		"rule_code": rule_code,
		"rule_type": rule_type,
		"label": label,
		"data_source": data_source,
		"failure_effect": failure_effect,
		"source_trace": source_trace,
	}
	if description:
		row["description"] = description
	if operator is not None:
		row["operator"] = operator
	if threshold_value is not None:
		row["threshold_value"] = threshold_value
	return row


def _qualification_rules(eval_state: dict[str, str]) -> list[dict[str, Any]]:
	rules: list[dict[str, Any]] = []

	amt = (eval_state.get("minimum_average_annual_turnover_amount") or "").strip()
	cur = (eval_state.get("minimum_average_annual_turnover_currency") or "").strip()
	yrs = (eval_state.get("minimum_average_annual_turnover_years") or "").strip()
	if amt or cur or yrs:
		rules.append(
			_rule(
				"DEM-QUAL-TURNOVER",
				"Threshold",
				_("Minimum average annual turnover"),
				_("Disclosed financial qualification — tenderer submissions"),
				"Reject",
				_p_trace("minimum_average_annual_turnover_amount"),
				description=_("Average annual turnover over the stated period must meet the disclosed minimum."),
				threshold_value={
					"amount": amt,
					"currency": cur,
					"years": yrs,
				},
			),
		)

	sc = (eval_state.get("similar_works_experience_minimum_contracts") or "").strip()
	sv = (eval_state.get("similar_works_experience_minimum_value_each") or "").strip()
	sp = (eval_state.get("similar_works_experience_period_years") or "").strip()
	if sc or sv or sp:
		rules.append(
			_rule(
				"DEM-QUAL-SIMILAR",
				"Threshold",
				_("Similar works experience"),
				_("Disclosed experience evidence — tenderer submissions"),
				"Reject",
				_p_trace("similar_works_experience_minimum_contracts"),
				description=_("Similar contracts count, minimum value, and reference period per disclosed criteria."),
				threshold_value={
					"minimum_contracts": sc,
					"minimum_value_each": sv,
					"period_years": sp,
				},
			),
		)

	if _truthy(eval_state.get("key_personnel_required")):
		rules.append(
			_rule(
				"DEM-QUAL-KP",
				"PassFail",
				_("Key personnel requirements"),
				_("Technical proposal schedules"),
				"Reject",
				_p_trace("key_personnel_required"),
				description=_("Key personnel must satisfy disclosed requirements."),
			),
		)

	if _truthy(eval_state.get("equipment_schedule_required")):
		rules.append(
			_rule(
				"DEM-QUAL-EQ",
				"PassFail",
				_("Equipment requirements"),
				_("Technical proposal schedules"),
				"Reject",
				_p_trace("equipment_schedule_required"),
				description=_("Equipment must satisfy disclosed requirements."),
			),
		)

	if _truthy(eval_state.get("margin_of_preference_applicable")):
		rules.append(
			_rule(
				"DEM-QUAL-MOP",
				"System",
				_("Margin of preference"),
				_("Disclosed preference rules — evaluation engine"),
				"Adjust",
				_section_trace("III"),
				description=_("Apply disclosed margin of preference where applicable."),
			),
		)

	if not rules:
		rules.append(
			_rule(
				"DEM-QUAL-DEFAULT",
				"PassFail",
				_("Disclosed qualification criteria"),
				_("Section III criteria and tenderer evidence"),
				"Reject",
				_section_trace("III"),
				description=_("Evaluate against qualification criteria disclosed in the tender."),
			),
		)

	return rules


def _technical_rules(inst: Document) -> list[dict[str, Any]]:
	rules: list[dict[str, Any]] = []
	for comp in ("METHOD_STATEMENT", "WORK_PROGRAMME"):
		if _parse_flag_required(_row_by_component(inst, comp)) is True:
			label = _("Method statement") if comp == "METHOD_STATEMENT" else _("Work programme")
			rules.append(
				_rule(
					f"DEM-TEC-{comp}",
					"PresenceCheck",
					label,
					_("Works completion structured requirements"),
					"Reject",
					_wr_dem_trace(comp),
					description=_("Technical content must satisfy the disclosed Works requirement."),
				),
			)

	for row in inst.works_requirements or []:
		if not getattr(row, "drives_dsm", 0):
			continue
		cc = (getattr(row, "component_code", None) or "").strip()
		if not cc or cc in ("METHOD_STATEMENT", "WORK_PROGRAMME"):
			continue
		if not (getattr(row, "structured_text", None) or "").strip():
			continue
		rules.append(
			_rule(
				f"DEM-TEC-WR-{cc}",
				"PresenceCheck",
				_("Technical compliance — {0}").format(cc),
				_("Works requirement structured content"),
				"Reject",
				_wr_dem_trace(cc),
			),
		)

	if not rules:
		rules.append(
			_rule(
				"DEM-TEC-DEFAULT",
				"PassFail",
				_("Technical compliance"),
				_("Specifications, drawings, and technical proposals"),
				"Reject",
				_section_trace("VI"),
				description=_("Assess technical responsiveness against disclosed scope and requirements."),
			),
		)

	return rules


def _boq_correction_rules() -> list[dict[str, Any]]:
	tr = _boq_section_trace()
	return [
		{
			"rule_code": "DEM-BOQ-COR-MUL",
			"rule_type": "ArithmeticCorrection",
			"label": _("Correct multiplication errors (rate × quantity)"),
			"description": _("Recalculate line amounts where multiplication errors are identified."),
			"source_trace": tr,
		},
		{
			"rule_code": "DEM-BOQ-COR-ADD",
			"rule_type": "ArithmeticCorrection",
			"label": _("Correct addition and sub-total errors"),
			"description": _("Re-total bills and the financial envelope where summation errors are identified."),
			"source_trace": tr,
		},
		{
			"rule_code": "DEM-BOQ-COR-RATEAMT",
			"rule_type": "ArithmeticCorrection",
			"label": _("Resolve rate versus amount discrepancies"),
			"description": _("Apply disclosed treatment when rates and extended amounts disagree."),
			"source_trace": tr,
		},
		{
			"rule_code": "DEM-BOQ-COR-TOTAL",
			"rule_type": "ArithmeticCorrection",
			"label": _("Recalculate corrected evaluated total"),
			"description": _("Produce a corrected evaluated BOQ total after arithmetic adjustments."),
			"source_trace": tr,
		},
		{
			"rule_code": "DEM-BOQ-COR-PRICE",
			"rule_type": "ArithmeticCorrection",
			"label": _("Derive corrected evaluated price"),
			"description": _("Carry forward corrected evaluated price for comparison and award stages."),
			"source_trace": tr,
		},
	]


def _evaluation_method_label(params: dict[str, str]) -> str:
	lot_m = (params.get("LOTS.LOT_EVALUATION_METHOD") or "").strip()
	aw_m = (params.get("LOTS.LOT_AWARD_METHOD") or "").strip()
	parts: list[str] = []
	if lot_m:
		parts.append(_("Lot evaluation: {0}").format(lot_m))
	if aw_m:
		parts.append(_("Award method: {0}").format(aw_m))
	if parts:
		return "; ".join(parts)
	return "LowestEvaluatedResponsiveBid"


def _build_dem_content(inst: Document) -> dict[str, Any]:
	bad = _scan_parameter_json_for_manual_criteria(inst)
	if bad:
		frappe.throw(
			_("Manual or hidden evaluation criteria are not allowed (key: {0})").format(bad),
			title=MANUAL_EVALUATION_CRITERIA_DENIED,
			exc=frappe.ValidationError,
		)

	boq = get_boq_for_instance(inst.name)
	has_boq = bool(boq)
	params = _param_map(inst)
	eval_state = _eval_state(inst)
	n_params = len(inst.parameter_values or [])
	n_attach = len(inst.section_attachments or [])
	n_wr = len(inst.works_requirements or [])

	tr_i = _section_trace("I")
	tr_iii = _section_trace("III")
	tr_iv = _section_trace("IV")
	tr_v = _boq_section_trace()

	stages: list[dict[str, Any]] = [
		{
			"stage_code": "DEM-STG-1",
			"stage_name": _("Responsiveness"),
			"sequence": 1,
			"stage_type": "Responsiveness",
			"mandatory": True,
			"rules": [
				_rule(
					"DEM-RESP-001",
					"PresenceCheck",
					_("Administrative responsiveness of bids"),
					_("DSM submission package"),
					"Reject",
					tr_iii,
					description=_("Verify completeness of submissions against disclosed requirements."),
				),
			],
		},
		{
			"stage_code": "DEM-STG-2",
			"stage_name": _("Eligibility"),
			"sequence": 2,
			"stage_type": "Eligibility",
			"mandatory": True,
			"rules": [
				_rule(
					"DEM-ELIG-001",
					"PassFail",
					_("Eligibility against ITT and mandatory requirements"),
					_("Invitation to Tender and mandatory checks"),
					"Reject",
					tr_i,
					description=_("Confirm tenderers meet statutory and ITT eligibility rules."),
				),
			],
		},
		{
			"stage_code": "DEM-STG-3",
			"stage_name": _("Qualification"),
			"sequence": 3,
			"stage_type": "Qualification",
			"mandatory": True,
			"rules": _qualification_rules(eval_state),
		},
		{
			"stage_code": "DEM-STG-4",
			"stage_name": _("Technical compliance"),
			"sequence": 4,
			"stage_type": "Technical",
			"mandatory": True,
			"rules": _technical_rules(inst),
		},
	]

	if has_boq:
		financial_rules = [
			_rule(
				"DEM-FIN-001",
				"Comparison",
				_("Financial comparison on priced BOQ"),
				_("Priced bills of quantities"),
				"Reject",
				tr_v,
				description=_("Compare responsive financial offers using the disclosed BOQ structure."),
			),
		]
	else:
		financial_rules = [
			_rule(
				"DEM-FIN-NOBOQ",
				"Comparison",
				_("Financial comparison (lump sum / priced offer)"),
				_("Tendering forms and financial envelope"),
				"Reject",
				tr_iv,
				description=_("Compare financial offers where no BOQ applies."),
			),
		]

	stages.append(
		{
			"stage_code": "DEM-STG-5",
			"stage_name": _("Financial evaluation"),
			"sequence": 5,
			"stage_type": "Financial",
			"mandatory": True,
			"rules": financial_rules,
		},
	)

	if has_boq:
		stages.append(
			{
				"stage_code": "DEM-STG-6",
				"stage_name": _("BOQ arithmetic correction"),
				"sequence": 6,
				"stage_type": "BOQArithmetic",
				"mandatory": True,
				"rules": [
					_rule(
						"DEM-BOQ-STG-001",
						"ArithmeticCorrection",
						_("Execute BOQ arithmetic correction"),
						_("Corrected BOQ schedule (Section V)"),
						"Adjust",
						tr_v,
						description=_("Apply the detailed correction rules before financial comparison and ranking."),
					),
				],
			},
		)
	else:
		stages.append(
			{
				"stage_code": "DEM-STG-6",
				"stage_name": _("BOQ arithmetic correction"),
				"sequence": 6,
				"stage_type": "BOQArithmetic",
				"mandatory": False,
				"rules": [
					_rule(
						"DEM-BOQ-SKIP",
						"System",
						_("No BOQ arithmetic correction"),
						_("Not applicable without a bill of quantities"),
						"RecordOnly",
						{"source_type": "SystemRule", "mapping_code": "DEM_NO_BOQ_ARITHMETIC"},
						description=_("Arithmetic correction applies only when a BOQ is part of the tender."),
					),
				],
			},
		)

	stages.append(
		{
			"stage_code": "DEM-STG-7",
			"stage_name": _("Ranking"),
			"sequence": 7,
			"stage_type": "Ranking",
			"mandatory": True,
			"rules": [
				_rule(
					"DEM-RANK-001",
					"Ranking",
					_("Rank responsive evaluated bids"),
					_("Evaluated financial outcomes"),
					"RecordOnly",
					tr_iii,
					description=_("Produce ranking consistent with the disclosed evaluation method."),
				),
			],
		},
	)

	correction_rules = _boq_correction_rules() if has_boq else []

	return {
		"std_inst": inst.name,
		"output_type": "DEM",
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": n_params,
		"attachment_rows": n_attach,
		"works_requirement_rows": n_wr,
		"has_boq": has_boq,
		"evaluation_method": _evaluation_method_label(params),
		"stages": stages,
		"boq_arithmetic_correction": {
			"enabled": has_boq,
			"stage_code": "DEM-STG-6",
			"correction_rules": correction_rules,
		},
		"ranking": {
			"method": "LowestEvaluatedCost",
			"source_trace": tr_iii,
		},
	}


class DemGenerator:
	"""Build DEM ``content_json`` from a ``Tender STD Instance``."""

	@staticmethod
	def generateDEM(instance_code: str, actor_or_job: str | None = None) -> dict[str, Any]:
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor_or_job or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("STD Instance code is required."), title=DEM_GENERATION_FAILED)

			if not frappe.db.exists("Tender STD Instance", code):
				frappe.throw(_("Tender STD Instance not found."), title=DEM_GENERATION_FAILED)

			try:
				inst = frappe.get_doc("Tender STD Instance", code)
				return _build_dem_content(inst)
			except frappe.ValidationError:
				raise
			except Exception as exc:
				emit_std_instance_event(
					EVT_STDINST_OUTPUT_GENERATION_FAILED,
					instance_code=code,
					details={
						"error_code": DEM_GENERATION_FAILED,
						"error": str(exc),
						"source": "DemGenerator.generateDEM",
					},
				)
				emit_derived_model_generation_failed(
					code,
					"DEM",
					str(exc),
					source="DemGenerator.generateDEM",
				)
				frappe.throw(
					_("DEM generation failed: {0}").format(str(exc)),
					title=DEM_GENERATION_FAILED,
					exc=frappe.ValidationError,
				)
		finally:
			frappe.set_user(prev_user)
