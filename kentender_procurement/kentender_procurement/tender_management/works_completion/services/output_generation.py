# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0500 — Works output generation orchestration.

Pre-generation gates (pack §14): Works completion context, BOQ structurally valid
per ``WorksBoqCompletionService``, and no prohibited manual-criteria keys in any
parameter value JSON. Template lineage is enforced by ``validate_works_completion_context``.

Generation and publish run through ``DerivedModelGenerationService`` (DERIVED-0700)
with ``publish=True`` and ``rollback_on_failure=True`` so mid-chain failures match
historical transactional cleanup.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.derived_models.orchestration import (
	DerivedModelGenerationService,
)
from kentender_procurement.tender_management.works_completion.audit import (
	WORKS_MANUAL_CRITERIA_DENIED,
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

		from kentender_procurement.tender_management.works_completion.services.boq_completion import (
			WorksBoqCompletionService,
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
			return DerivedModelGenerationService.generate_all(
				code,
				publish=True,
				rollback_on_failure=True,
			)
		finally:
			frappe.set_user(prev_user)
