# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable handoff surface when a procurement package is released to tender (v2+).

Apps register ``release_procurement_package_to_tender`` in hooks.py; each callable
receives a single ``payload`` dict. Failures in hooks are logged and do not block
the procurement status transition once server-side gates pass.
"""

from __future__ import annotations

from typing import Any

import frappe


def build_release_payload(package_doc) -> dict[str, Any]:
	"""Documented intake shape for downstream tendering hooks (extend when v2 ships)."""
	return {
		"event": "procurement_package_released_to_tender",
		"package": package_doc.name,
		"package_code": package_doc.package_code,
		"plan_id": package_doc.plan_id,
		"template_id": package_doc.template_id,
		"procurement_method": package_doc.procurement_method,
		"estimated_value": float(package_doc.estimated_value or 0),
		"currency": (package_doc.currency or "KES").strip() or "KES",
	}


def deliver_procurement_package_release(payload: dict[str, Any]) -> None:
	for dotted in frappe.get_hooks("release_procurement_package_to_tender") or []:
		try:
			frappe.get_attr(dotted)(payload)
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				title=f"Release-to-tender hook failed: {dotted}",
			)
