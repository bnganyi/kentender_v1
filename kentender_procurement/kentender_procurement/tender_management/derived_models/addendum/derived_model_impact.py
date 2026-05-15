# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""DERIVED-0900 — ``DerivedModelImpactService`` (Cursor pack §16).

Maps pack method name::

	getAffectedOutputsForChange → get_affected_outputs_for_change

**Policy note (opening vs staleness):** pack §16 maps *opening date/time change* to
``Bundle`` + ``DOM`` only. Tender-stage staleness for ``opening_datetime`` in
``PARAMETER_CODE_TO_STALE_OUTPUTS`` also marks ``DSM`` — regeneration planning for
addenda follows **this pack table**; stale-flag application remains the
parameter/BOQ/drawing engines.

Coordinates with ``WorksAddendumSensitivityService`` where change types overlap
in meaning (e.g. BOQ → same logical outputs as ``BOQ_STALE_OUTPUT_KEYS``).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

from kentender_procurement.tender_management.std_instance.audit import emit_std_instance_event
from kentender_procurement.tender_management.std_instance.events import EVT_STDINST_ADDENDUM_IMPACT_ANALYSED

DERIVED_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE = "DERIVED_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE"

# Canonical pack §16 keys (snake_case, ``_change`` suffix).
CHANGE_SUBMISSION_DEADLINE = "submission_deadline_change"
CHANGE_OPENING_DATETIME = "opening_datetime_change"
CHANGE_TENDER_SECURITY = "tender_security_change"
CHANGE_QUALIFICATION_THRESHOLD = "qualification_threshold_change"
CHANGE_SPECIFICATION = "specification_change"
CHANGE_DRAWING = "drawing_change"
CHANGE_BOQ_ITEM = "boq_quantity_item_change"
CHANGE_SCC_VALUE = "scc_value_change"
CHANGE_CONTRACT_FORM = "contract_form_change"

_OUTPUT_ORDER: tuple[str, ...] = ("Bundle", "DSM", "DOM", "DEM", "DCM")

# Pack §16 — base sets (drawing omits DSM; see acknowledgement flag).
_PACK_TABLE: dict[str, frozenset[str]] = {
	CHANGE_SUBMISSION_DEADLINE: frozenset({"Bundle", "DSM", "DOM"}),
	CHANGE_OPENING_DATETIME: frozenset({"Bundle", "DOM"}),
	CHANGE_TENDER_SECURITY: frozenset({"Bundle", "DSM", "DEM"}),
	CHANGE_QUALIFICATION_THRESHOLD: frozenset({"Bundle", "DSM", "DEM"}),
	CHANGE_SPECIFICATION: frozenset({"Bundle", "DSM", "DEM", "DCM"}),
	CHANGE_DRAWING: frozenset({"Bundle", "DEM", "DCM"}),
	CHANGE_BOQ_ITEM: frozenset({"Bundle", "DSM", "DEM", "DCM"}),
	CHANGE_SCC_VALUE: frozenset({"Bundle", "DCM"}),
	CHANGE_CONTRACT_FORM: frozenset({"Bundle", "DCM"}),
}

_CANONICAL_CHANGE_TYPES: frozenset[str] = frozenset(_PACK_TABLE.keys())

# Normalize free-text / Works-style aliases → canonical pack keys.
_CHANGE_TYPE_ALIASES: dict[str, str] = {
	"submission_deadline": CHANGE_SUBMISSION_DEADLINE,
	"deadline_change": CHANGE_SUBMISSION_DEADLINE,
	"opening_datetime_change": CHANGE_OPENING_DATETIME,
	"opening_date_time_change": CHANGE_OPENING_DATETIME,
	"opening": CHANGE_OPENING_DATETIME,
	"opening_datetime": CHANGE_OPENING_DATETIME,
	"tender_security": CHANGE_TENDER_SECURITY,
	"qualification_threshold": CHANGE_QUALIFICATION_THRESHOLD,
	"evaluation_threshold": CHANGE_QUALIFICATION_THRESHOLD,
	"threshold_change": CHANGE_QUALIFICATION_THRESHOLD,
	"spec": CHANGE_SPECIFICATION,
	"works_specification": CHANGE_SPECIFICATION,
	"drawing": CHANGE_DRAWING,
	"boq": CHANGE_BOQ_ITEM,
	"boq_change": CHANGE_BOQ_ITEM,
	"boq_quantity": CHANGE_BOQ_ITEM,
	"boq_item": CHANGE_BOQ_ITEM,
	"scc": CHANGE_SCC_VALUE,
	"scc_change": CHANGE_SCC_VALUE,
	"scc_value": CHANGE_SCC_VALUE,
	"contract_form": CHANGE_CONTRACT_FORM,
	"forms": CHANGE_CONTRACT_FORM,
}


def _normalize_change_type_key(change_type: str | None) -> str:
	raw = (change_type or "").strip().lower().replace(" ", "_").replace("-", "_")
	if not raw:
		return ""
	return _CHANGE_TYPE_ALIASES.get(raw, raw)


def _parse_affected_source(affected_source: Any) -> dict[str, Any]:
	if affected_source is None:
		return {}
	if isinstance(affected_source, dict):
		return dict(affected_source)
	if isinstance(affected_source, str):
		s = affected_source.strip()
		return {"field": s} if s else {}
	return {}


def _drawing_ack_required(meta: dict[str, Any]) -> bool:
	for k in (
		"drawing_acknowledgement_required",
		"acknowledgement_required",
		"dsm_acknowledgement_required",
		"require_dsm_acknowledgement",
	):
		if meta.get(k) in (True, 1, "1", "true", "True", "yes", "Y"):
			return True
	return False


def _sorted_outputs(outputs: frozenset[str]) -> list[str]:
	return [k for k in _OUTPUT_ORDER if k in outputs]


def _regeneration_plan(outputs: frozenset[str]) -> list[dict[str, Any]]:
	plan: list[dict[str, Any]] = []
	step = 1
	for ot in _OUTPUT_ORDER:
		if ot not in outputs:
			continue
		plan.append(
			{
				"step": step,
				"output_type": ot,
				"action": "regenerate",
				"preserve_prior_versions": True,
				"notes": "Publish supersedes prior Published row per STDINST-0400; history retained by version_number.",
			},
		)
		step += 1
	return plan


class DerivedModelImpactService:
	"""Pack §16 addendum → derived output impact and regeneration planning."""

	@staticmethod
	def get_affected_outputs_for_change(change_type: str, affected_source: Any = None) -> dict[str, Any]:
		"""Return affected output types and an ordered regeneration plan (pack §16).

		:param change_type: Addendum / change category (aliases accepted; see module aliases).
		:param affected_source: Optional ``dict`` with:

			- ``instance_code`` — when set, an ``EVT_STDINST_ADDENDUM_IMPACT_ANALYSED`` audit is emitted.
			- ``addendum_code`` / ``source_addendum_code`` — pass through to generation
			  (``insert_draft_output(..., source_addendum_code=...)``).
			- For ``drawing_change``: ``drawing_acknowledgement_required`` (or aliases) → include ``DSM``.

			May also be a plain string (treated as ``{"field": ...}`` for compatibility).
		"""
		meta = _parse_affected_source(affected_source)
		ct = _normalize_change_type_key(change_type)
		if not ct or ct not in _CANONICAL_CHANGE_TYPES:
			allowed = ", ".join(sorted(_CANONICAL_CHANGE_TYPES))
			frappe.throw(
				_("Unknown addendum change_type {0!r}. Allowed: {1}").format(change_type, allowed),
				title=DERIVED_ADDENDUM_IMPACT_UNKNOWN_CHANGE_TYPE,
				exc=frappe.ValidationError,
			)

		base = frozenset(_PACK_TABLE[ct])
		outputs: frozenset[str]
		if ct == CHANGE_DRAWING and _drawing_ack_required(meta):
			outputs = base | frozenset({"DSM"})
		else:
			outputs = base

		addendum = (meta.get("addendum_code") or meta.get("source_addendum_code") or "").strip() or None
		inst = (meta.get("instance_code") or meta.get("tender_std_instance") or "").strip() or None

		if inst:
			emit_std_instance_event(
				EVT_STDINST_ADDENDUM_IMPACT_ANALYSED,
				instance_code=inst,
				document_type="Tender STD Instance",
				document_name=inst,
				details={
					"change_type": ct,
					"affected_outputs": _sorted_outputs(outputs),
					"source_addendum_code": addendum,
					"source": "DerivedModelImpactService",
				},
			)

		return {
			"change_type": ct,
			"affected_outputs": _sorted_outputs(outputs),
			"affected_outputs_set": sorted(outputs),
			"regeneration_plan": _regeneration_plan(outputs),
			"source_addendum_code": addendum,
			"regeneration_hints": {
				"link_regenerated_outputs": bool(addendum),
				"source_addendum_code": addendum,
				"use_insert_draft_source_addendum": bool(addendum),
			},
			"preservation_policy": (
				"Prior Published outputs are superseded on publish; prior rows remain in the "
				"append-only history (version_number, Superseded status)."
			),
		}
