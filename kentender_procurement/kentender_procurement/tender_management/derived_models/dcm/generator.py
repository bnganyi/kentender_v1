# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0610 — ``DcmGenerator.generateDCM`` (Cursor pack §12 / std engine §10).

Builds DCM ``content_json`` from a ``Tender STD Instance``: GCC/SCC/X contract
documents, SCC-forwarded terms, BOQ-aware price source, optional securities from
TDS parameters, addenda as a traced document, and scope references derived from
the instance footprint.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.derived_models.events.audit import emit_derived_model_generation_failed
from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.boq import get_boq_for_instance
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_OUTPUT_GENERATION_FAILED
from kentender_procurement.tender_management.derived_models.dcm.schema import DCM_GENERATION_FAILED


def _param_map(inst: Document) -> dict[str, str]:
	out: dict[str, str] = {}
	for row in inst.parameter_values or []:
		pc = (getattr(row, "parameter_code", None) or "").strip()
		if pc:
			out[pc] = (getattr(row, "value", None) or "").strip()
	return out


def _parse_positive_int(raw: str | None) -> int | None:
	s = (raw or "").strip()
	if not s:
		return None
	try:
		v = int(float(s))
	except ValueError:
		return None
	return v if v > 0 else None


def _parse_percent_int(raw: str | None) -> int | None:
	s = (raw or "").strip().rstrip("%").strip()
	if not s:
		return None
	try:
		v = float(s)
	except ValueError:
		return None
	if v < 0.0 or v > 100.0:
		return None
	return int(round(v))


def _days_from_contract_params(
	params: dict[str, str],
	*,
	day_key: str,
	month_key: str,
	default_days: int,
) -> int:
	d = _parse_positive_int(params.get(day_key))
	if d is not None:
		return d
	m = _parse_positive_int(params.get(month_key))
	if m is not None:
		return m * 30
	return default_days


def _works_boq_commercial_top_level(params: dict[str, str], inst: Document, has_boq: bool) -> dict[str, int]:
	"""Pack §19 — scalar commercial summary for Works tenders with a BOQ."""
	if not has_boq:
		return {}
	if (inst.procurement_category or "").strip().upper() != "WORKS":
		return {}
	completion = _days_from_contract_params(
		params,
		day_key="CONTRACT.COMPLETION_PERIOD_DAYS",
		month_key="CONTRACT.COMPLETION_PERIOD_MONTHS",
		default_days=180,
	)
	defects = _days_from_contract_params(
		params,
		day_key="CONTRACT.DEFECTS_LIABILITY_PERIOD_DAYS",
		month_key="CONTRACT.DEFECTS_LIABILITY_PERIOD_MONTHS",
		default_days=365,
	)
	perf = _parse_percent_int(params.get("SECURITY.PERFORMANCE_SECURITY_PERCENTAGE"))
	if perf is None:
		perf = 10
	ret = _parse_percent_int(params.get("CONTRACT.RETENTION_PERCENTAGE"))
	if ret is None:
		ret = 5
	return {
		"completion_period_days": completion,
		"defects_liability_period_days": defects,
		"performance_security_percent": perf,
		"retention_percent": ret,
	}


def _collect_addendum_codes(inst: Document) -> list[str]:
	codes: set[str] = set()
	for row in inst.parameter_values or []:
		c = (getattr(row, "source_addendum_code", None) or "").strip()
		if c:
			codes.add(c)
	for row in inst.works_requirements or []:
		c = (getattr(row, "source_addendum_code", None) or "").strip()
		if c:
			codes.add(c)
	return sorted(codes)


def _section_trace(section_code: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": section_code}


def _tender_title(inst: Document) -> str:
	code = (getattr(inst, "procurement_tender", None) or "").strip()
	if not code or not frappe.db.exists("Procurement Tender", code):
		return ""
	return (frappe.db.get_value("Procurement Tender", code, "tender_title") or "").strip()


def _build_contract_documents(
	*,
	addendum_codes: list[str],
	tr_viii: dict[str, str],
	tr_ix: dict[str, str],
	tr_x: dict[str, str],
) -> list[dict[str, Any]]:
	docs: list[dict[str, Any]] = [
		{
			"document_code": "DCM-GCC",
			"label": _("General Conditions of Contract (GCC)"),
			"description": _("Base contract conditions — Section VIII; not editable as free text in contract formation."),
			"source_trace": tr_viii,
		},
		{
			"document_code": "DCM-SCC",
			"label": _("Special Conditions of Contract (SCC)"),
			"description": _("Tender-specific conditions — Section IX; carry-forward into the contract bundle."),
			"source_trace": tr_ix,
		},
		{
			"document_code": "DCM-CONTRACT-FORMS",
			"label": _("Contract forms (Section X)"),
			"description": _("Required contract forms bound to the tender STD instance."),
			"source_trace": tr_x,
		},
	]
	if addendum_codes:
		desc = _("Issued addenda affecting contract-bound content: {0}").format(", ".join(addendum_codes))
		docs.append(
			{
				"document_code": "DCM-ADDENDA",
				"label": _("Addenda incorporated into contract model"),
				"description": desc,
				"source_trace": {"source_type": "Addendum", "source_addendum_code": addendum_codes[0]},
			},
		)
	return docs


def _build_contract_terms(
	*,
	inst: Document,
	has_boq: bool,
	params: dict[str, str],
	title: str,
	tr_viii: dict[str, str],
	tr_ix: dict[str, str],
	tr_x: dict[str, str],
	tr_v: dict[str, str],
	tr_vi: dict[str, str],
	tr_vii: dict[str, str],
) -> list[dict[str, Any]]:
	cur = (params.get("SECURITY.TENDER_SECURITY_CURRENCY") or "").strip()
	currency_value: dict[str, Any] = {"source": "TDS/BOQ header"}
	if cur:
		currency_value["currency_code"] = cur

	title_value: dict[str, Any] = {"from_tender_title": True}
	if title:
		title_value["title"] = title

	return [
		{
			"term_code": "DCM-TERM-EMPLOYER",
			"label": _("Employer / procuring entity"),
			"value": {"role": "employer", "placeholder_until_award": True},
			"editable_in_contract": True,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-CONTRACTOR",
			"label": _("Contractor (awarded bidder)"),
			"value": {"role": "contractor", "placeholder_until_award": True},
			"editable_in_contract": True,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-TITLE",
			"label": _("Contract title"),
			"value": title_value,
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-COMPLETION",
			"label": _("Completion period"),
			"value": {"source": "SCC/TDS", "instance_code": inst.name},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-DEFECTS",
			"label": _("Defects liability period"),
			"value": {"source": "SCC/TDS"},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-PERF-SEC",
			"label": _("Performance security"),
			"value": {
				"source": "SCC",
				"tender_security_mode": (params.get("SECURITY.TENDER_SECURITY_MODE") or "").strip() or None,
			},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-RETENTION",
			"label": _("Retention"),
			"value": {"source": "SCC"},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-LD",
			"label": _("Liquidated damages"),
			"value": {"source": "SCC"},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-CURRENCY",
			"label": _("Payment currency"),
			"value": currency_value,
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-INSURANCE",
			"label": _("Insurance requirements"),
			"value": {"source": "SCC/GCC"},
			"editable_in_contract": False,
			"source_trace": tr_viii,
		},
		{
			"term_code": "DCM-TERM-SPECS-REF",
			"label": _("Specifications reference"),
			"value": {"section": "VI", "attachment_rows": len(inst.section_attachments or [])},
			"editable_in_contract": False,
			"source_trace": tr_vi,
		},
		{
			"term_code": "DCM-TERM-DRAWINGS-REF",
			"label": _("Drawings reference"),
			"value": {"section": "VII"},
			"editable_in_contract": False,
			"source_trace": tr_vii,
		},
		{
			"term_code": "DCM-TERM-BOQ-REF",
			"label": _("BOQ reference"),
			"value": {"section": "V", "present": has_boq},
			"editable_in_contract": False,
			"source_trace": tr_v,
		},
		{
			"term_code": "DCM-TERM-PRICE-SOURCE",
			"label": _("Contract price source"),
			"value": {
				"bound_to_price_source_block": True,
				"dem_corrected_evaluated_boq_total": has_boq,
			},
			"editable_in_contract": False,
			"source_trace": tr_ix,
		},
		{
			"term_code": "DCM-TERM-FORMS",
			"label": _("Contract forms schedule"),
			"value": {"section": "X"},
			"editable_in_contract": False,
			"source_trace": tr_x,
		},
	]


def _build_securities(params: dict[str, str]) -> dict[str, Any] | None:
	mode = (params.get("SECURITY.TENDER_SECURITY_MODE") or "").strip()
	if not mode:
		return None
	return {
		"performance_security": {
			"disclosed": True,
			"tender_security_mode": mode,
		},
	}


def _build_dcm_content(inst: Document) -> dict[str, Any]:
	boq = get_boq_for_instance(inst.name)
	has_boq = bool(boq)
	params = _param_map(inst)
	addendum_codes = _collect_addendum_codes(inst)
	n_params = len(inst.parameter_values or [])
	n_attach = len(inst.section_attachments or [])
	n_wr = len(inst.works_requirements or [])

	tr_viii = _section_trace("VIII")
	tr_ix = _section_trace("IX")
	tr_x = _section_trace("X")
	tr_v = _section_trace("V")
	tr_vi = _section_trace("VI")
	tr_vii = _section_trace("VII")

	contract_documents = _build_contract_documents(
		addendum_codes=addendum_codes,
		tr_viii=tr_viii,
		tr_ix=tr_ix,
		tr_x=tr_x,
	)
	contract_terms = _build_contract_terms(
		inst=inst,
		has_boq=has_boq,
		params=params,
		title=_tender_title(inst),
		tr_viii=tr_viii,
		tr_ix=tr_ix,
		tr_x=tr_x,
		tr_v=tr_v,
		tr_vi=tr_vi,
		tr_vii=tr_vii,
	)

	if has_boq:
		price_source: dict[str, Any] = {
			"source_type": "CorrectedEvaluatedBOQTotal",
			"manual_override_allowed": False,
		}
	else:
		price_source = {
			"source_type": "LumpSum",
			"manual_override_allowed": True,
		}

	works_scope_references: dict[str, Any] = {
		"specifications": ["VI"],
		"drawings": ["VII"],
		"boq": {
			"section": "V",
			"instance_boq": has_boq,
			"attachment_rows": n_attach,
			"works_requirement_rows": n_wr,
		},
	}

	out: dict[str, Any] = {
		"std_inst": inst.name,
		"output_type": "DCM",
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": n_params,
		"attachment_rows": n_attach,
		"works_requirement_rows": n_wr,
		"has_boq": has_boq,
		"contract_documents": contract_documents,
		"contract_terms": contract_terms,
		"price_source": price_source,
		"works_scope_references": works_scope_references,
	}

	sec = _build_securities(params)
	if sec:
		out["securities"] = sec

	out.update(_works_boq_commercial_top_level(params, inst, has_boq))

	return out


class DcmGenerator:
	"""Build DCM ``content_json`` from a ``Tender STD Instance``."""

	@staticmethod
	def generateDCM(instance_code: str, actor_or_job: str | None = None) -> dict[str, Any]:
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor_or_job or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("STD Instance code is required."), title=DCM_GENERATION_FAILED)

			if not frappe.db.exists("Tender STD Instance", code):
				frappe.throw(_("Tender STD Instance not found."), title=DCM_GENERATION_FAILED)

			try:
				inst = frappe.get_doc("Tender STD Instance", code)
				return _build_dcm_content(inst)
			except frappe.ValidationError:
				raise
			except Exception as exc:
				emit_std_instance_event(
					EVT_STDINST_OUTPUT_GENERATION_FAILED,
					instance_code=code,
					details={
						"error_code": DCM_GENERATION_FAILED,
						"error": str(exc),
						"source": "DcmGenerator.generateDCM",
					},
				)
				emit_derived_model_generation_failed(
					code,
					"DCM",
					str(exc),
					source="DcmGenerator.generateDCM",
				)
				frappe.throw(
					_("DCM generation failed: {0}").format(str(exc)),
					title=DCM_GENERATION_FAILED,
					exc=frappe.ValidationError,
				)
		finally:
			frappe.set_user(prev_user)
