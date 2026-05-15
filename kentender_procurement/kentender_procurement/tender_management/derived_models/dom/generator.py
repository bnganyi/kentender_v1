# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0410 — ``DomGenerator.generateDOM`` (Cursor pack §10 / std engine §8).

Builds DOM ``content_json`` from a ``Tender STD Instance``: TDS/ITT-aligned
``register_fields`` (opening + submission metadata references), canonical
``prohibited_actions``, and optional ``opening_datetime`` / ``opening_location``.
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
from kentender_procurement.tender_management.derived_models.dom.schema import (
	DOM_GENERATION_FAILED,
	DOM_WORKS_REGISTER_BLUEPRINT,
	dom_canonical_prohibited_actions,
)


def _param_map(inst: Document) -> dict[str, str]:
	out: dict[str, str] = {}
	for row in inst.parameter_values or []:
		pc = (getattr(row, "parameter_code", None) or "").strip()
		if pc:
			out[pc] = (getattr(row, "value", None) or "").strip()
	return out


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


def _p_trace(parameter_code: str) -> dict[str, str]:
	return {"source_type": "Parameter", "source_parameter_code": parameter_code}


def _section_trace(section_code: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": section_code}


def _dsm_submission_trace(suffix: str) -> dict[str, str]:
	"""Pack: DSM / submission metadata — opening records bid envelope fields (no evaluation)."""
	return {"source_type": "SystemRule", "mapping_code": f"DSM_SUBMISSION_{suffix}"}


def _register_trace(
	field_code: str,
	*,
	params: dict[str, str],
	has_boq: bool,
	addendum_codes: list[str],
) -> dict[str, str]:
	"""ITT/TDS/DSM/addendum-aligned ``source_trace`` per register field."""
	if field_code == "bidder_name":
		return _dsm_submission_trace("BIDDER_NAME")
	if field_code == "submission_timestamp":
		if (params.get("DATES.SUBMISSION_DEADLINE") or "").strip():
			return _p_trace("DATES.SUBMISSION_DEADLINE")
		return _dsm_submission_trace("SUBMISSION_TIMESTAMP")
	if field_code == "bid_modification_or_withdrawal":
		return _dsm_submission_trace("BID_MODIFICATION_OR_WITHDRAWAL")
	if field_code == "submitted_total_bid_price":
		if has_boq:
			return {
				"source_type": "BOQ",
				"source_section_code": "V",
				"mapping_code": "SUBMITTED_TOTAL_BID_PRICE",
			}
		return _dsm_submission_trace("SUBMITTED_TOTAL_BID_PRICE")
	if field_code == "currency":
		if (params.get("SECURITY.TENDER_SECURITY_CURRENCY") or "").strip():
			return _p_trace("SECURITY.TENDER_SECURITY_CURRENCY")
		return _dsm_submission_trace("CURRENCY")
	if field_code == "tender_security_present":
		return _p_trace("SECURITY.TENDER_SECURITY_MODE")
	if field_code == "addendum_acknowledgement_present":
		if addendum_codes:
			return {"source_type": "Addendum", "source_addendum_code": addendum_codes[0]}
		return {"source_type": "SystemRule", "mapping_code": "NO_ADDENDUM_ACK_REQUIRED"}
	if field_code == "opening_committee_attendance":
		return _section_trace("I")
	if field_code == "opening_timestamp":
		return _p_trace("DATES.OPENING_DATETIME")
	if field_code == "opening_remarks":
		return _section_trace("I")
	return {"source_type": "SystemRule"}


def _build_register_fields(
	*,
	params: dict[str, str],
	has_boq: bool,
	addendum_codes: list[str],
) -> list[dict[str, Any]]:
	rows: list[dict[str, Any]] = []
	for field_code, label_en, ftype, mandatory_base, disc in DOM_WORKS_REGISTER_BLUEPRINT:
		mandatory = mandatory_base
		if field_code == "addendum_acknowledgement_present":
			mandatory = bool(addendum_codes)
		trace = _register_trace(
			field_code,
			params=params,
			has_boq=has_boq,
			addendum_codes=addendum_codes,
		)
		label = _(label_en)
		rows.append(
			{
				"field_code": field_code,
				"label": label,
				"field_type": ftype,
				"mandatory": mandatory,
				"disclosure_status": disc,
				"source_trace": trace,
			},
		)
	rows.sort(key=lambda r: (r.get("field_code") or ""))
	return rows


def _build_dom_content(inst: Document) -> dict[str, Any]:
	boq = get_boq_for_instance(inst.name)
	params = _param_map(inst)
	addendum_codes = _collect_addendum_codes(inst)
	n_params = len(inst.parameter_values or [])
	n_attach = len(inst.section_attachments or [])
	n_wr = len(inst.works_requirements or [])

	payload: dict[str, Any] = {
		"std_inst": inst.name,
		"output_type": "DOM",
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": n_params,
		"attachment_rows": n_attach,
		"works_requirement_rows": n_wr,
		"has_boq": bool(boq),
		"register_fields": _build_register_fields(
			params=params,
			has_boq=bool(boq),
			addendum_codes=addendum_codes,
		),
		"prohibited_actions": dom_canonical_prohibited_actions(),
	}
	opening_dt = (params.get("DATES.OPENING_DATETIME") or "").strip()
	if opening_dt:
		payload["opening_datetime"] = opening_dt
	# TDS / site context — optional opening venue hint (POC: no dedicated opening_place field).
	loc = (params.get("DATES.SITE_VISIT_LOCATION") or "").strip()
	if loc:
		payload["opening_location"] = loc
	return payload


class DomGenerator:
	"""Build DOM ``content_json`` from a ``Tender STD Instance``."""

	@staticmethod
	def generateDOM(instance_code: str, actor_or_job: str | None = None) -> dict[str, Any]:
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor_or_job or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("STD Instance code is required."), title=DOM_GENERATION_FAILED)

			if not frappe.db.exists("Tender STD Instance", code):
				frappe.throw(_("Tender STD Instance not found."), title=DOM_GENERATION_FAILED)

			try:
				inst = frappe.get_doc("Tender STD Instance", code)
				return _build_dom_content(inst)
			except frappe.ValidationError:
				raise
			except Exception as exc:
				emit_std_instance_event(
					EVT_STDINST_OUTPUT_GENERATION_FAILED,
					instance_code=code,
					details={
						"error_code": DOM_GENERATION_FAILED,
						"error": str(exc),
						"source": "DomGenerator.generateDOM",
					},
				)
				emit_derived_model_generation_failed(
					code,
					"DOM",
					str(exc),
					source="DomGenerator.generateDOM",
				)
				frappe.throw(
					_("DOM generation failed: {0}").format(str(exc)),
					title=DOM_GENERATION_FAILED,
					exc=frappe.ValidationError,
				)
		finally:
			frappe.set_user(prev_user)
