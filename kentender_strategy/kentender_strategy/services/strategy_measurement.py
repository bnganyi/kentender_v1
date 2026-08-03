# Copyright (c) 2026, KenTender and contributors
"""REQ §10 measurement result derivation."""

from __future__ import annotations

import frappe
from frappe import _


def derive_measurement_result(doc) -> None:
	"""Mutate doc.variance and doc.result_status from target definition."""
	tgt = frappe.get_doc("Performance Target", doc.performance_target)
	ind = frappe.get_doc("Performance Indicator", tgt.performance_indicator)
	mtype = ind.measurement_type
	direction = tgt.comparison_direction

	if mtype in ("Milestone", "Boolean"):
		achieved = False
		if doc.actual_text and doc.actual_text.lower() in ("yes", "true", "achieved", "1"):
			achieved = True
		if doc.actual_numeric is not None and float(doc.actual_numeric) >= 1:
			achieved = True
		doc.variance = None
		doc.result_status = "On track" if achieved else "Off track"
		return

	if doc.actual_numeric is None:
		doc.result_status = "No data"
		doc.variance = None
		return

	actual = float(doc.actual_numeric)
	target = float(tgt.target_numeric) if tgt.target_numeric is not None else None
	if target is None:
		frappe.throw(_("Target numeric value is required for quantitative measurements"))
	tol = float(tgt.tolerance_value) if tgt.tolerance_value is not None else None
	doc.variance = actual - target

	if direction in ("At least", "Increase to"):
		if actual >= target:
			doc.result_status = "On track"
		elif tol is not None and actual >= target - tol:
			doc.result_status = "At risk"
		else:
			doc.result_status = "Off track"
	elif direction in ("At most", "Reduce to"):
		if actual <= target:
			doc.result_status = "On track"
		elif tol is not None and actual <= target + tol:
			doc.result_status = "At risk"
		else:
			doc.result_status = "Off track"
	elif direction == "Equal to":
		if tol is not None:
			if abs(actual - target) <= tol:
				doc.result_status = "On track"
			else:
				doc.result_status = "Off track"
		else:
			doc.result_status = "On track" if actual == target else "Off track"
	else:
		doc.result_status = "On track" if actual >= target else "Off track"
