# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""XMOD-STR-003 — Demand applicable Plan Value Commitments + treatments."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _

TREATMENT_INCLUDED = "Included"
TREATMENT_NOT_APPLICABLE = "Not applicable"
_REQUIRED_PREFIX = "Required"


def list_demand_applicable_pvcs(demand) -> list[dict[str, Any]]:
	"""Fetch Strategy applicable PVCs for this Demand's plan + category filters."""
	plan = (getattr(demand, "strategy_plan_version", None) or "").strip()
	if not plan:
		return []
	try:
		from kentender_strategy.services.strategy_contracts import list_applicable_value_commitments
	except ImportError:
		return []

	category = (getattr(demand, "requisition_type", None) or "").strip() or None
	procurement_type = (getattr(demand, "demand_type", None) or "").strip() or None
	return list_applicable_value_commitments(
		plan_version=plan,
		procurement_category=category,
		procurement_type=procurement_type,
		asset_condition=None,
	)


def _is_required_level(level: str | None) -> bool:
	return (level or "").strip().startswith(_REQUIRED_PREFIX)


def _treatment_rows(demand) -> list[Any]:
	if not hasattr(demand, "get") and not hasattr(demand, "value_treatments"):
		return []
	return list(demand.get("value_treatments") or [])


def required_pvc_treatments_ok(demand) -> tuple[bool, int]:
	"""Return (ok, required_count). ok True when every Required PVC is treated."""
	applicable = list_demand_applicable_pvcs(demand)
	required = [r for r in applicable if _is_required_level(r.get("consideration_level"))]
	if not required:
		return True, 0

	by_id: dict[str, Any] = {}
	by_code: dict[str, Any] = {}
	for row in _treatment_rows(demand):
		pvc_id = (getattr(row, "pvc_id", None) or (row.get("pvc_id") if isinstance(row, dict) else "") or "").strip()
		pvc_code = (
			getattr(row, "pvc_code", None) or (row.get("pvc_code") if isinstance(row, dict) else "") or ""
		).strip()
		if pvc_id:
			by_id[pvc_id] = row
		if pvc_code:
			by_code[pvc_code] = row

	for pvc in required:
		pvc_id = (pvc.get("id") or "").strip()
		obj = pvc.get("objective") or {}
		pvc_code = (obj.get("code") or "").strip()
		row = by_id.get(pvc_id) or by_code.get(pvc_code)
		if not row:
			return False, len(required)
		treatment = (
			getattr(row, "treatment", None) or (row.get("treatment") if isinstance(row, dict) else "") or ""
		).strip()
		rationale = (
			getattr(row, "rationale", None) or (row.get("rationale") if isinstance(row, dict) else "") or ""
		).strip()
		if treatment == TREATMENT_INCLUDED:
			continue
		if treatment == TREATMENT_NOT_APPLICABLE and rationale:
			continue
		return False, len(required)
	return True, len(required)


def assert_required_pvc_treatments(demand) -> None:
	ok, count = required_pvc_treatments_ok(demand)
	if ok:
		return
	frappe.throw(
		_("Required plan value commitments must be Included or Not applicable with a reason ({0} outstanding).").format(
			count
		),
		title=_("Value commitments"),
	)


def apply_value_treatments_to_doc(doc, treatments: list[dict] | None) -> None:
	"""Replace Demand value_treatments child rows from wizard/API payload."""
	if treatments is None:
		return
	if not doc.meta.has_field("value_treatments"):
		return
	doc.set("value_treatments", [])
	for raw in treatments or []:
		if not isinstance(raw, dict):
			continue
		treatment = (raw.get("treatment") or "").strip()
		if treatment not in (TREATMENT_INCLUDED, TREATMENT_NOT_APPLICABLE):
			continue
		pvc_code = (raw.get("pvc_code") or "").strip()
		pvc_name = (raw.get("pvc_name") or "").strip() or pvc_code
		if not pvc_code and not (raw.get("pvc_id") or "").strip():
			continue
		rationale = (raw.get("rationale") or "").strip()
		if treatment == TREATMENT_NOT_APPLICABLE and not rationale:
			frappe.throw(
				_("Not applicable value commitments require a reason ({0}).").format(pvc_code or pvc_name),
				title=_("Value commitments"),
			)
		doc.append(
			"value_treatments",
			{
				"pvc_id": (raw.get("pvc_id") or "").strip(),
				"pvc_code": pvc_code,
				"pvc_name": pvc_name,
				"requirement_level": (raw.get("requirement_level") or "").strip(),
				"treatment": treatment,
				"rationale": rationale,
				"reviewer_accepted": int(raw.get("reviewer_accepted") or 0),
			},
		)
