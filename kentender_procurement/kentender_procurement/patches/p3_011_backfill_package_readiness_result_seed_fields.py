# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.pp2_constants import READINESS_PASSED
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKG_CODE,
	PKGRDY_CODE,
	PKGRDY_RUN_AT,
	PLAN_CREATOR_USER_CODE,
	master_readiness_check_items,
	strict_readiness_snapshot,
)
from kentender_procurement.procurement_planning.services.package_readiness_service import (
	evaluate_pp2_readiness_checks,
)


def _user_by_code(user_code: str) -> str | None:
	return frappe.db.get_value("User", {"username": user_code}, "name")


def execute():
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return

	run_by = _user_by_code(PLAN_CREATOR_USER_CODE)
	check_items = master_readiness_check_items()
	live_snapshot = dict((evaluate_pp2_readiness_checks(PKG_CODE) or {}).get("source_snapshot_json") or {})
	for key, value in strict_readiness_snapshot().items():
		if key == "required_std_template_version_code":
			continue
		live_snapshot[key] = value
	values = {
		"package_code": PKG_CODE,
		"run_at": get_datetime(PKGRDY_RUN_AT),
		"result_status": READINESS_PASSED,
		"blocking_failure_count": 0,
		"warning_count": 0,
		"check_items_json": {"checks": check_items},
		"source_snapshot_json": live_snapshot or strict_readiness_snapshot(),
		"stale": 0,
		"stale_reason": None,
		"is_current": 1,
		"is_master_seed": 1,
	}
	if run_by:
		values["run_by"] = run_by

	if frappe.db.exists("Package Readiness Result", PKGRDY_CODE):
		frappe.db.set_value(
			"Package Readiness Result",
			PKGRDY_CODE,
			values,
			update_modified=False,
		)
	else:
		doc = frappe.get_doc({"doctype": "Package Readiness Result", "readiness_code": PKGRDY_CODE, **values})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)

	frappe.db.sql(
		"""
		UPDATE `tabPackage Readiness Result`
		SET is_current = 0
		WHERE package_code = %s AND is_current = 1 AND readiness_code != %s
		""",
		(PKG_CODE, PKGRDY_CODE),
	)
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{
			"readiness_status": READINESS_PASSED,
			"latest_readiness_code": PKGRDY_CODE,
		},
		update_modified=False,
	)
