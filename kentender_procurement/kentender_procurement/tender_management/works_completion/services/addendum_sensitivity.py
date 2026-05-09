# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0800 — Works addendum / post-publication output impact map.

Maps high-level **change types** to logical generated outputs (Bundle, DSM, DOM,
DEM, DCM) using the **same sources** as tender-stage staleness (``PARAMETER_CODE_TO_STALE_OUTPUTS``,
``BOQ_STALE_OUTPUT_KEYS``, ``logical_outputs_from_row``, ``logical_outputs_from_drawing_row``)
via [`WorksOutputStalenessService`](output_staleness.py).

Pack §18 table text may differ from the engine (e.g. opening datetime): **staleness
wins** — this module delegates to ``PARAMETER_CODE_TO_STALE_OUTPUTS`` for parameter-driven
changes rather than duplicating a conflicting matrix.
"""

from __future__ import annotations

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.boq import BOQ_STALE_OUTPUT_KEYS
from kentender_procurement.tender_management.std_instance.drawing_register import (
	StdInstanceDrawingRegisterService,
	logical_outputs_from_drawing_row,
)
from kentender_procurement.tender_management.std_instance.parameter import (
	PARAMETER_CODE_TO_STALE_OUTPUTS,
	_normalize_pc,
)
from kentender_procurement.tender_management.std_instance.works_requirement import (
	logical_outputs_from_row,
)
from kentender_procurement.tender_management.works_completion.services.output_staleness import (
	WorksOutputStalenessService,
)

_UNKNOWN_CHANGE_TITLE = "WORKS_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE"

# Canonical ``change_type`` values after normalization (lowercase snake).
_CANONICAL_CHANGE_TYPES: frozenset[str] = frozenset(
	{
		"submission_deadline",
		"opening_datetime",
		"tender_security",
		"evaluation_threshold",
		"specification_change",
		"drawing_change",
		"boq_change",
		"scc_value_change",
	}
)

_CHANGE_TYPE_ALIASES: dict[str, str] = {
	"boq": "boq_change",
	"boq_quantity": "boq_change",
	"boq_item": "boq_change",
	"boq_quantity_item": "boq_change",
	"scc": "scc_value_change",
	"scc_change": "scc_value_change",
	"tender_security_change": "tender_security",
}

_TENDER_SECURITY_PARAMETER_CODES: tuple[str, ...] = (
	"tender_security_required",
	"tender_security_type",
	"tender_security_amount",
	"tender_security_currency",
)

_EVALUATION_THRESHOLD_PARAMETER_CODES: tuple[str, ...] = (
	"margin_of_preference_applicable",
	"minimum_average_annual_turnover_amount",
	"minimum_average_annual_turnover_currency",
	"minimum_average_annual_turnover_years",
	"similar_works_experience_minimum_contracts",
	"similar_works_experience_minimum_value_each",
	"similar_works_experience_period_years",
	"key_personnel_required",
	"equipment_schedule_required",
)

_DEFAULT_SPECIFICATION_OUTPUTS: frozenset[str] = frozenset({"Bundle", "DSM", "DEM", "DCM"})
_DEFAULT_DRAWING_OUTPUTS: frozenset[str] = frozenset({"Bundle", "DEM", "DCM"})


def _normalize_change_type(change_type: str | None) -> str:
	raw = (change_type or "").strip().lower().replace(" ", "_").replace("-", "_")
	return _CHANGE_TYPE_ALIASES.get(raw, raw)


def _union_stale_for_parameter_codes(codes: tuple[str, ...]) -> frozenset[str]:
	out: set[str] = set()
	for pc in codes:
		fs = PARAMETER_CODE_TO_STALE_OUTPUTS.get(pc)
		if fs:
			out |= set(fs)
	return frozenset(out)


def _scc_value_change_outputs() -> frozenset[str]:
	out: set[str] = set()
	for pc, fs in PARAMETER_CODE_TO_STALE_OUTPUTS.items():
		if pc == "bid_currency" or pc.startswith("scc."):
			out |= set(fs)
	return frozenset(out)


class WorksAddendumSensitivityService:
	"""Deterministic Works addendum impact → logical outputs (aligns with staleness engine)."""

	@staticmethod
	def get_works_addendum_impact(
		change_type: str,
		affected_field_or_component: str | None = None,
		*,
		instance_code: str | None = None,
	) -> frozenset[str]:
		"""Return logical outputs affected by a post-publication Works configuration change.

		:param change_type: High-level category (e.g. ``submission_deadline``, ``boq_change``).
		:param affected_field_or_component: Optional ``parameter_code`` (for
			``evaluation_threshold``), ``component_code`` (for ``specification_change`` when
			``instance_code`` is set), or ``drawing_code`` / ``drawing_code|revision`` for
			``drawing_change``.
		:param instance_code: Optional STD instance; required for row-accurate specification
			or drawing impact; when omitted, specification/drawing fall back to pack defaults.
		"""
		ct = _normalize_change_type(change_type)
		if ct not in _CANONICAL_CHANGE_TYPES:
			allowed = ", ".join(sorted(_CANONICAL_CHANGE_TYPES))
			frappe.throw(
				_("[{0}] Unknown Works addendum change_type {1!r}. Allowed: {2}").format(
					_UNKNOWN_CHANGE_TITLE, change_type, allowed
				),
				title=_UNKNOWN_CHANGE_TITLE,
			)

		field = (affected_field_or_component or "").strip()
		inst = (instance_code or "").strip()

		if ct == "submission_deadline":
			return _require_parameter_stale("submission_deadline")
		if ct == "opening_datetime":
			return _require_parameter_stale("opening_datetime")
		if ct == "tender_security":
			return _union_stale_for_parameter_codes(_TENDER_SECURITY_PARAMETER_CODES)
		if ct == "evaluation_threshold":
			pc = _normalize_pc(field)
			if pc:
				got = WorksOutputStalenessService.get_stale_outputs_for_parameter_code(pc)
				if not got:
					frappe.throw(
						_("[WORKS_ADDENDUM_IMPACT_UNKNOWN_FIELD] No staleness mapping for parameter_code {0!r}.").format(
							pc
						),
						title="WORKS_ADDENDUM_IMPACT_UNKNOWN_FIELD",
					)
				return got
			return _union_stale_for_parameter_codes(_EVALUATION_THRESHOLD_PARAMETER_CODES)
		if ct == "specification_change":
			if inst and field:
				doc = frappe.get_doc("Tender STD Instance", inst)
				for row in doc.get("works_requirements") or []:
					if (row.get("component_code") or "").strip() == field:
						affected = logical_outputs_from_row(row)
						return affected if affected else _DEFAULT_SPECIFICATION_OUTPUTS
			return _DEFAULT_SPECIFICATION_OUTPUTS
		if ct == "drawing_change":
			if inst and field:
				dc, _sep, rev = field.partition("|")
				dc = dc.strip()
				rev = rev.strip() or None
				row = StdInstanceDrawingRegisterService.find_row(inst, dc, rev)
				if row is not None:
					return logical_outputs_from_drawing_row(row)
			return _DEFAULT_DRAWING_OUTPUTS
		if ct == "boq_change":
			return WorksOutputStalenessService.get_boq_change_stale_outputs()
		if ct == "scc_value_change":
			return _scc_value_change_outputs()

		# Unreachable: _CANONICAL_CHANGE_TYPES guards all branches
		return frozenset()


def _require_parameter_stale(parameter_code: str) -> frozenset[str]:
	got = WorksOutputStalenessService.get_stale_outputs_for_parameter_code(parameter_code)
	if not got:
		frappe.throw(
			_("[WORKS_ADDENDUM_IMPACT_UNKNOWN_FIELD] No staleness mapping for parameter_code {0!r}.").format(
				parameter_code
			),
			title="WORKS_ADDENDUM_IMPACT_UNKNOWN_FIELD",
		)
	return got
