# Copyright (c) 2026, KenTender and contributors
"""REQ §10 measurement result derivation."""

from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def compute_measurement_result(
	*,
	measurement_type: str,
	comparison_direction: str | None,
	target_numeric: float | None,
	tolerance_value: float | None,
	actual_numeric: float | None,
	actual_text: str | None = None,
) -> dict[str, Any]:
	"""Pure derivation used by save path and Submit UI live preview (STR-FR-073/074)."""
	direction = comparison_direction or ""
	mtype = measurement_type or ""

	if mtype in ("Milestone", "Boolean"):
		achieved = False
		if actual_text and str(actual_text).lower() in ("yes", "true", "achieved", "1"):
			achieved = True
		if actual_numeric is not None and float(actual_numeric) >= 1:
			achieved = True
		return {"result_status": "On track" if achieved else "Off track", "variance": None}

	if actual_numeric is None or actual_numeric == "":
		return {"result_status": "No data", "variance": None}

	actual = float(actual_numeric)
	if target_numeric is None:
		frappe.throw(_("Target numeric value is required for quantitative measurements"))
	target = float(target_numeric)
	tol = float(tolerance_value) if tolerance_value is not None else None
	variance = actual - target

	if direction in ("At least", "Increase to"):
		if actual >= target:
			status = "On track"
		elif tol is not None and actual >= target - tol:
			status = "At risk"
		else:
			status = "Off track"
	elif direction in ("At most", "Reduce to"):
		if actual <= target:
			status = "On track"
		elif tol is not None and actual <= target + tol:
			status = "At risk"
		else:
			status = "Off track"
	elif direction == "Equal to":
		if tol is not None:
			status = "On track" if abs(actual - target) <= tol else "Off track"
		else:
			status = "On track" if actual == target else "Off track"
	else:
		status = "On track" if actual >= target else "Off track"

	return {"result_status": status, "variance": variance}


def derive_measurement_result(doc) -> None:
	"""Mutate doc.variance and doc.result_status from target definition."""
	tgt = frappe.get_doc("Performance Target", doc.performance_target)
	ind = frappe.get_doc("Performance Indicator", tgt.performance_indicator)
	out = compute_measurement_result(
		measurement_type=ind.measurement_type,
		comparison_direction=tgt.comparison_direction,
		target_numeric=tgt.target_numeric,
		tolerance_value=tgt.tolerance_value,
		actual_numeric=doc.actual_numeric,
		actual_text=doc.actual_text,
	)
	doc.variance = out["variance"]
	doc.result_status = out["result_status"]
