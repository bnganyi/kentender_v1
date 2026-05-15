# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0200 — ``BundleGenerator.generateBundle`` (pack §8).

``content_json`` shape:

- ``output_type`` (literal ``Bundle``), ``instance_code``, ``template_version_code``,
  ``applicability_profile_code``, ``has_boq``, row counts — metadata for audit/debug.
- ``document_outline``, ``sections``, ``attachments``, ``placeholder_status`` — pack fields.

Rendering and full template merge are out of scope; sections are structural placeholders
with ``Section``-level ``source_trace``.
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
from kentender_procurement.tender_management.derived_models.bundle.schema import (
	BUNDLE_GENERATION_FAILED,
	PLACEHOLDER_COMPLETE,
	PLACEHOLDER_PENDING,
	WORKS_BUNDLE_OUTLINE,
)


def _section_trace(section_code: str) -> dict[str, str]:
	return {"source_type": "Section", "source_section_code": section_code}


def _build_bundle_content(inst: Document) -> dict[str, Any]:
	boq = get_boq_for_instance(inst.name)
	n_params = len(inst.parameter_values or [])
	n_attach = len(inst.section_attachments or [])
	n_wr = len(inst.works_requirements or [])
	n_draw = len(inst.drawing_register or [])

	document_outline: list[dict[str, Any]] = []
	sections: list[dict[str, Any]] = []
	placeholder_status: dict[str, str] = {}

	for seq, (code, title) in enumerate(WORKS_BUNDLE_OUTLINE, start=1):
		document_outline.append({"section_code": code, "title": title, "sequence": seq})

		content_source = "template"
		if code == "II":
			content_source = "instance_parameters"
		elif code == "V":
			content_source = "instance_boq" if boq else "template"
		elif code == "VI":
			content_source = "works_requirements" if n_wr else "template"
		elif code == "VII":
			content_source = "drawing_register" if n_draw else "section_attachments"
		elif code == "IX":
			content_source = "instance_parameters"

		sections.append(
			{
				"section_code": code,
				"title": title,
				"content_source": content_source,
				"summary": "",
				"source_trace": _section_trace(code),
				"components": [],
			},
		)

		if code == "II" and n_params:
			placeholder_status[code] = PLACEHOLDER_COMPLETE
		elif code == "V" and boq:
			placeholder_status[code] = PLACEHOLDER_COMPLETE
		elif code == "VI" and n_wr:
			placeholder_status[code] = PLACEHOLDER_COMPLETE
		elif code == "VII" and (n_draw or n_attach):
			placeholder_status[code] = PLACEHOLDER_PENDING
		else:
			placeholder_status[code] = PLACEHOLDER_PENDING

	attachments: list[dict[str, Any]] = []
	for row in inst.section_attachments or []:
		sc = (row.get("section_code") or "").strip() or "UNKNOWN"
		ac = (row.get("attachment_code") or "").strip() or "ATT"
		fn = (row.get("file_name") or "").strip() or ac
		cc = (row.get("component_code") or "").strip()
		trace: dict[str, str] = {
			"source_type": "Attachment",
			"source_section_code": sc,
		}
		if cc:
			trace["source_component_code"] = cc
		attachments.append(
			{
				"attachment_code": ac,
				"section_code": sc,
				"file_name": fn,
				"source_trace": trace,
			},
		)

	for row in inst.drawing_register or []:
		dc = (row.get("drawing_code") or "").strip() or "DRW"
		sc = (row.get("section_code") or "").strip() or "VII"
		fn = (row.get("file_name") or "").strip() or dc
		attachments.append(
			{
				"drawing_code": dc,
				"section_code": sc,
				"file_name": fn,
				"source_trace": {"source_type": "Drawing", "source_section_code": sc},
			},
		)

	return {
		"output_type": "Bundle",
		"instance_code": inst.name,
		"template_version_code": (inst.template_version_code or "").strip(),
		"applicability_profile_code": (inst.applicability_profile_code or "").strip(),
		"parameter_rows": n_params,
		"attachment_rows": n_attach,
		"works_requirement_rows": n_wr,
		"drawing_register_rows": n_draw,
		"has_boq": bool(boq),
		"document_outline": document_outline,
		"sections": sections,
		"attachments": attachments,
		"placeholder_status": placeholder_status,
	}


class BundleGenerator:
	"""Build Bundle ``content_json`` from a ``Tender STD Instance``."""

	@staticmethod
	def generateBundle(instance_code: str, actor_or_job: str | None = None) -> dict[str, Any]:
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor_or_job or "").strip()
		if act:
			frappe.set_user(act)
		try:
			if not code:
				frappe.throw(_("STD Instance code is required."), title=BUNDLE_GENERATION_FAILED)

			if not frappe.db.exists("Tender STD Instance", code):
				frappe.throw(_("Tender STD Instance not found."), title=BUNDLE_GENERATION_FAILED)

			try:
				inst = frappe.get_doc("Tender STD Instance", code)
				return _build_bundle_content(inst)
			except frappe.ValidationError:
				raise
			except Exception as exc:
				emit_std_instance_event(
					EVT_STDINST_OUTPUT_GENERATION_FAILED,
					instance_code=code,
					details={
						"error_code": BUNDLE_GENERATION_FAILED,
						"error": str(exc),
						"source": "BundleGenerator.generateBundle",
					},
				)
				emit_derived_model_generation_failed(
					code,
					"Bundle",
					str(exc),
					source="BundleGenerator.generateBundle",
				)
				frappe.throw(
					_("Bundle generation failed: {0}").format(str(exc)),
					title=BUNDLE_GENERATION_FAILED,
					exc=frappe.ValidationError,
				)
		finally:
			frappe.set_user(prev_user)
