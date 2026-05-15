# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0310 — ``DsmGenerator.generateDSM`` (Cursor pack §9).

Builds DSM ``content_json`` from a ``Tender STD Instance``: submission metadata,
``requirements`` (Form of Tender, security, qualification, Works-driven rows, BOQ
rate entry), ``boq_rate_entry`` block, and ``addendum_acknowledgements`` derived
from ``source_addendum_code`` on parameters / works requirement rows.
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
from kentender_procurement.tender_management.derived_models.dsm.schema import (
	DSM_GENERATION_FAILED,
	dsm_default_boq_rate_entry,
)
from kentender_procurement.tender_management.works_completion.services.works_requirements_completion import (
	COMPONENT_TO_SECTION_CODE,
)


def _truthy_param(raw: str | None) -> bool:
	s = (raw or "").strip().lower()
	return s in ("1", "true", "yes", "y", "on")


def _param_map(inst: Document) -> dict[str, str]:
	out: dict[str, str] = {}
	for row in inst.parameter_values or []:
		pc = (getattr(row, "parameter_code", None) or "").strip()
		if pc:
			out[pc] = (getattr(row, "value", None) or "").strip()
	return out


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


def _p_trace(parameter_code: str) -> dict[str, str]:
	return {"source_type": "Parameter", "source_parameter_code": parameter_code}


def _section_trace(section_code: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": section_code}


def _wr_trace(component_code: str) -> dict[str, str]:
	sec = COMPONENT_TO_SECTION_CODE.get(component_code, "SPECIFICATIONS")
	return {
		"source_type": "WorksRequirement",
		"source_section_code": sec,
		"mapping_code": component_code,
	}


def _boq_trace() -> dict[str, str]:
	return {"source_type": "BOQ", "source_section_code": "V"}


def _requirement(
	*,
	code: str,
	requirement_type: str,
	label: str,
	mandatory: bool,
	supplier_action: str,
	source_trace: dict[str, str],
	description: str = "",
) -> dict[str, Any]:
	row: dict[str, Any] = {
		"requirement_code": code,
		"requirement_type": requirement_type,
		"label": label,
		"mandatory": mandatory,
		"supplier_action": supplier_action,
		"source_trace": source_trace,
	}
	if description:
		row["description"] = description
	return row


def _collect_addendum_rows(inst: Document) -> list[dict[str, Any]]:
	codes: set[str] = set()
	for row in inst.parameter_values or []:
		c = (getattr(row, "source_addendum_code", None) or "").strip()
		if c:
			codes.add(c)
	for row in inst.works_requirements or []:
		c = (getattr(row, "source_addendum_code", None) or "").strip()
		if c:
			codes.add(c)
	return [{"addendum_code": c, "mandatory": True} for c in sorted(codes)]


def _build_requirements(inst: Document, boq: Any, params: dict[str, str]) -> list[dict[str, Any]]:
	reqs: list[dict[str, Any]] = []

	reqs.append(
		_requirement(
			code="DSM-FORE-001",
			requirement_type="Form",
			label=_("Form of Tender"),
			mandatory=True,
			supplier_action="CompleteForm",
			source_trace=_section_trace("IV"),
			description=_("Complete the Form of Tender (Section IV)."),
		),
	)

	mode = (params.get("SECURITY.TENDER_SECURITY_MODE") or "").strip().upper()
	if mode == "TENDER_SECURITY":
		reqs.append(
			_requirement(
				code="DSM-SEC-001",
				requirement_type="Document",
				label=_("Tender security"),
				mandatory=True,
				supplier_action="UploadDocument",
				source_trace=_p_trace("SECURITY.TENDER_SECURITY_MODE"),
				description=_("Submit tender security as described in the ITT/TDS."),
			),
		)
	elif mode == "TENDER_SECURING_DECLARATION":
		reqs.append(
			_requirement(
				code="DSM-SEC-002",
				requirement_type="Declaration",
				label=_("Tender-securing declaration"),
				mandatory=True,
				supplier_action="Declare",
				source_trace=_p_trace("SECURITY.TENDER_SECURITY_MODE"),
				description=_("Sign the tender-securing declaration where applicable."),
			),
		)

	is_works = (inst.procurement_category or "").strip().upper() == "WORKS"
	if is_works:
		reqs.extend(
			[
				_requirement(
					code="DSM-QUAL-NCA",
					requirement_type="Document",
					label=_("NCA / contractor registration evidence"),
					mandatory=True,
					supplier_action="UploadDocument",
					source_trace=_p_trace("QUALIFICATION.NCA_REGISTRATION_REQUIRED"),
				),
				_requirement(
					code="DSM-QUAL-TAX",
					requirement_type="Document",
					label=_("Tax compliance evidence"),
					mandatory=True,
					supplier_action="UploadDocument",
					source_trace=_p_trace("QUALIFICATION.TAX_COMPLIANCE_REQUIRED"),
				),
				_requirement(
					code="DSM-QUAL-BO",
					requirement_type="Document",
					label=_("Beneficial ownership disclosure"),
					mandatory=True,
					supplier_action="UploadDocument",
					source_trace=_p_trace("QUALIFICATION.BENEFICIAL_OWNERSHIP_REQUIRED"),
				),
			],
		)

	if _truthy_param(params.get("QUALIFICATION.KEY_PERSONNEL_REQUIRED")):
		reqs.append(
			_requirement(
				code="DSM-QUAL-KP",
				requirement_type="TechnicalProposal",
				label=_("Key personnel schedule"),
				mandatory=True,
				supplier_action="UploadDocument",
				source_trace=_p_trace("QUALIFICATION.KEY_PERSONNEL_REQUIRED"),
			),
		)

	if _truthy_param(params.get("QUALIFICATION.EQUIPMENT_REQUIRED")):
		reqs.append(
			_requirement(
				code="DSM-QUAL-EQ",
				requirement_type="TechnicalProposal",
				label=_("Equipment schedule"),
				mandatory=True,
				supplier_action="UploadDocument",
				source_trace=_p_trace("QUALIFICATION.EQUIPMENT_REQUIRED"),
			),
		)

	for comp in ("METHOD_STATEMENT", "WORK_PROGRAMME"):
		flag_val = _parse_flag_required(_row_by_component(inst, comp))
		if flag_val is True:
			label = (
				_("Method statement") if comp == "METHOD_STATEMENT" else _("Work programme")
			)
			reqs.append(
				_requirement(
					code=f"DSM-WR-{comp}",
					requirement_type="TechnicalProposal",
					label=label,
					mandatory=True,
					supplier_action="UploadDocument",
					source_trace=_wr_trace(comp),
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
		reqs.append(
			_requirement(
				code=f"DSM-WR-{cc}",
				requirement_type="TechnicalProposal",
				label=_("Works submission content ({0})").format(cc),
				mandatory=True,
				supplier_action="UploadDocument",
				source_trace=_wr_trace(cc),
			),
		)

	if boq:
		reqs.append(
			_requirement(
				code="DSM-BOQ-RATES",
				requirement_type="BOQRateEntry",
				label=_("Bills of Quantities — rate entry"),
				mandatory=True,
				supplier_action="EnterRates",
				source_trace=_boq_trace(),
				description=_("Enter rates only; quantities and descriptions are locked."),
			),
		)

	reqs.sort(key=lambda r: (r.get("requirement_code") or ""))
	return reqs


def _build_dsm_content(inst: Document) -> dict[str, Any]:
	boq = get_boq_for_instance(inst.name)
	params = _param_map(inst)
	n_params = len(inst.parameter_values or [])
	n_attach = len(inst.section_attachments or [])
	n_wr = len(inst.works_requirements or [])

	submission_deadline = (params.get("DATES.SUBMISSION_DEADLINE") or "").strip()
	out: dict[str, Any] = {
		"std_inst": inst.name,
		"output_type": "DSM",
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": n_params,
		"attachment_rows": n_attach,
		"works_requirement_rows": n_wr,
		"has_boq": bool(boq),
		"requirements": _build_requirements(inst, boq, params),
		"boq_rate_entry": dsm_default_boq_rate_entry(enabled=bool(boq)),
		"addendum_acknowledgements": _collect_addendum_rows(inst),
		"submission_mode": "Electronic",
	}
	if submission_deadline:
		out["submission_deadline"] = submission_deadline
	return out


class DsmGenerator:
	"""Build DSM ``content_json`` from a ``Tender STD Instance``."""

	@staticmethod
	def generateDSM(instance_code: str, actor_or_job: str | None = None) -> dict[str, Any]:
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor_or_job or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("STD Instance code is required."), title=DSM_GENERATION_FAILED)

			if not frappe.db.exists("Tender STD Instance", code):
				frappe.throw(_("Tender STD Instance not found."), title=DSM_GENERATION_FAILED)

			try:
				inst = frappe.get_doc("Tender STD Instance", code)
				return _build_dsm_content(inst)
			except frappe.ValidationError:
				raise
			except Exception as exc:
				emit_std_instance_event(
					EVT_STDINST_OUTPUT_GENERATION_FAILED,
					instance_code=code,
					details={
						"error_code": DSM_GENERATION_FAILED,
						"error": str(exc),
						"source": "DsmGenerator.generateDSM",
					},
				)
				emit_derived_model_generation_failed(
					code,
					"DSM",
					str(exc),
					source="DsmGenerator.generateDSM",
				)
				frappe.throw(
					_("DSM generation failed: {0}").format(str(exc)),
					title=DSM_GENERATION_FAILED,
					exc=frappe.ValidationError,
				)
		finally:
			frappe.set_user(prev_user)
