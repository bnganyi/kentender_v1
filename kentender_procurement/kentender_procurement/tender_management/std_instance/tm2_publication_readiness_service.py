# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P1-04 — governed insert for **TM2 Publication Readiness** (doc 9 §9.3 step 5).

Callers supply validation outcomes; **TM2 Publication Readiness** ``before_insert`` allocates
``readiness_code`` / ``validation_run_number``. This function sets **TM2-PRD-004** authorization
flags for non-blocked ``readiness_status`` values.
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.model.document import Document


def insert_tm2_publication_readiness_record(
	tm2_tender: str,
	tm2_tender_std_binding: str,
	*,
	readiness_status: str,
	std_readiness_status: str,
	validation_payload: dict[str, Any],
	package_lineage_valid: bool = False,
	template_version_active: bool = False,
	std_instance_exists: bool = False,
	parameters_complete: bool = False,
	sections_complete: bool = False,
	bundle_current: bool = False,
	dsm_current: bool = False,
	dom_current: bool = False,
	dem_current: bool = False,
	dcm_current: bool = False,
	timeline_valid: bool = False,
	supplier_access_valid: bool = False,
	unresolved_blocker_count: int = 0,
	warning_count: int = 0,
) -> Document:
	"""Insert one **TM2 Publication Readiness** row (immutable thereafter; supersede handled on insert).

	Run number and ``readiness_code`` are allocated in ``before_insert`` (single source of truth).

	``readiness_status`` **Ready** / **Ready With Warnings** sets ``allow_tm2_readiness_authorized_ready``.
	"""
	doc = frappe.get_doc(
		{
			"doctype": "TM2 Publication Readiness",
			"tm2_tender": tm2_tender,
			"tm2_tender_std_binding": tm2_tender_std_binding,
			"readiness_status": readiness_status,
			"std_readiness_status": std_readiness_status,
			"validation_payload": validation_payload or {},
			"package_lineage_valid": 1 if package_lineage_valid else 0,
			"template_version_active": 1 if template_version_active else 0,
			"std_instance_exists": 1 if std_instance_exists else 0,
			"parameters_complete": 1 if parameters_complete else 0,
			"sections_complete": 1 if sections_complete else 0,
			"bundle_current": 1 if bundle_current else 0,
			"dsm_current": 1 if dsm_current else 0,
			"dom_current": 1 if dom_current else 0,
			"dem_current": 1 if dem_current else 0,
			"dcm_current": 1 if dcm_current else 0,
			"timeline_valid": 1 if timeline_valid else 0,
			"supplier_access_valid": 1 if supplier_access_valid else 0,
			"unresolved_blocker_count": int(unresolved_blocker_count),
			"warning_count": int(warning_count),
		}
	)
	rs = (readiness_status or "").strip()
	if rs in ("Ready", "Ready With Warnings"):
		doc.flags.allow_tm2_readiness_authorized_ready = True
	doc.insert(ignore_permissions=True)
	return doc
