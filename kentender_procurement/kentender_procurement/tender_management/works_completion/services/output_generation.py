# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0500 — Works output generation orchestration.

Generates and publishes Bundle, DSM, DOM, DEM, DCM in that order via
``StdInstanceGeneratedOutputService`` (stub payloads; hashes on rows).

Pre-generation gates (pack §14): Works completion context, BOQ structurally valid
per ``WorksBoqCompletionService``, and no prohibited manual-criteria keys in any
parameter value JSON. Template lineage is enforced by ``validate_works_completion_context``.
"""

from __future__ import annotations

import json
from typing import Any, Callable

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.generated_output import (
	OUTPUT_KEY_TO_PARENT_FIELD,
	StdInstanceGeneratedOutputService,
)
from kentender_procurement.tender_management.works_completion.services.boq_completion import (
	WorksBoqCompletionService,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_MANUAL_CRITERIA_DENIED,
	WORKS_OUTPUTS_GENERATED,
	emit_works_completion_audit,
)
from kentender_procurement.tender_management.works_completion.services.context_validator import (
	validate_works_completion_context,
)
from kentender_procurement.tender_management.works_completion.services.evaluation_options_completion import (
	DENY_CODE,
	DENY_MESSAGE,
	find_prohibited_evaluation_key,
)

_OUTPUT_ORDER: tuple[tuple[str, Callable[..., Any]], ...] = (
	("Bundle", StdInstanceGeneratedOutputService.generate_bundle),
	("DSM", StdInstanceGeneratedOutputService.generate_dsm),
	("DOM", StdInstanceGeneratedOutputService.generate_dom),
	("DEM", StdInstanceGeneratedOutputService.generate_dem),
	("DCM", StdInstanceGeneratedOutputService.generate_dcm),
)


def _scan_parameter_values_for_prohibited_keys(instance_name: str) -> str | None:
	doc = frappe.get_doc("Tender STD Instance", instance_name)
	for row in doc.parameter_values or []:
		raw = (row.get("value") or "").strip()
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


def _raise_precheck_from_blockers(blockers: list[dict[str, Any]], *, title_code: str) -> None:
	msgs: list[str] = []
	for b in blockers or []:
		c = (b.get("code") or "").strip()
		m = (b.get("message") or "").strip()
		if c and m:
			msgs.append(f"{c}: {m}")
		elif c:
			msgs.append(c)
		elif m:
			msgs.append(m)
	frappe.throw(
		"; ".join(msgs) if msgs else title_code,
		title=title_code,
		exc=frappe.ValidationError,
	)


class WorksOutputGenerationService:
	"""Orchestrates Works STD generated outputs (Bundle through DCM)."""

	@staticmethod
	def assert_prechecks(instance_code: str) -> None:
		"""Raise ``ValidationError`` when pack §14 pre-generation checks fail."""
		code = (instance_code or "").strip()
		if not code:
			frappe.throw(_("Tender STD Instance code is required."), title=_("WORKS_OUTPUT_GEN_INVALID"))

		ctx = validate_works_completion_context(code)
		if not ctx.get("valid"):
			_raise_precheck_from_blockers(list(ctx.get("blockers") or []), title_code="WORKS_OUTPUT_GEN_CONTEXT")

		bad_key = _scan_parameter_values_for_prohibited_keys(code)
		if bad_key:
			emit_works_completion_audit(
				WORKS_MANUAL_CRITERIA_DENIED,
				code,
				details={
					"prohibited_key": bad_key,
					"legacy_deny_code": DENY_CODE,
					"source": "output_generation_precheck",
				},
			)
			frappe.throw(
				_("{0}: {1} (key: {2})").format(DENY_CODE, str(DENY_MESSAGE), bad_key),
				title=DENY_CODE,
				exc=frappe.ValidationError,
			)

		boq = WorksBoqCompletionService.validate_boq(code)
		if not boq.get("valid"):
			_raise_precheck_from_blockers(list(boq.get("blockers") or []), title_code="WORKS_OUTPUT_GEN_BOQ")

	@staticmethod
	def generate_all_works_outputs(instance_code: str, actor: str | None = None) -> dict[str, Any]:
		"""Generate then publish all five output types in canonical order.

		:param instance_code: ``Tender STD Instance`` name
		:param actor: optional Frappe user for ``frappe.set_user`` for the duration of the call
		:returns: ``{"ok": True, "outputs": {"Bundle": row_name, ...}}`` for published rows
		"""
		code = (instance_code or "").strip()
		prev_user = frappe.session.user
		act = (actor or "").strip()
		if act:
			frappe.set_user(act)
		try:
			WorksOutputGenerationService.assert_prechecks(code)
			outputs: dict[str, str] = {}
			try:
				for label, gen_fn in _OUTPUT_ORDER:
					draft = gen_fn(code)
					published = StdInstanceGeneratedOutputService.publish_output(draft.name)
					outputs[label] = published.name
				all_labels = [label for label, _fn in _OUTPUT_ORDER]
				emit_works_completion_audit(
					WORKS_OUTPUTS_GENERATED,
					code,
					affected_outputs=all_labels,
					details={"outputs": outputs},
					performed_by=act or frappe.session.user,
				)
				return {"ok": True, "outputs": outputs}
			except Exception:
				deleted_names = {n for n in outputs.values() if n}
				for _lbl in reversed(list(outputs.keys())):
					name = outputs.get(_lbl)
					if name and frappe.db.exists("Tender STD Generated Output", name):
						try:
							frappe.delete_doc("Tender STD Generated Output", name, force=True, ignore_permissions=True)
						except Exception:
							pass
				if deleted_names:
					try:
						inst = frappe.get_doc("Tender STD Instance", code)
						for _k, field in OUTPUT_KEY_TO_PARENT_FIELD.items():
							if (inst.get(field) or "").strip() in deleted_names:
								inst.set(field, None)
						inst.save(ignore_permissions=True)
					except Exception:
						pass
				raise
		finally:
			frappe.set_user(prev_user)
