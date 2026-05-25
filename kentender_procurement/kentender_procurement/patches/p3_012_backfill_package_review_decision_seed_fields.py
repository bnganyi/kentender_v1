# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	METHDEC_CODE,
	METHDEC_REVIEWER_USER_CODE,
	PKG_CODE,
	PKGREV_AUDIT_EVENT_REF,
	PKGREV_CODE,
	PKGREV_DECIDED_AT,
	PKGREV_DECISION_REASON,
	PKGREV_FROM_STATE,
	PKGREV_TO_STATE,
	PKGRDY_CODE,
)


def _user_by_code(user_code: str) -> str | None:
	return frappe.db.get_value("User", {"username": user_code}, "name")


def execute():
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		return

	decided_by = _user_by_code(METHDEC_REVIEWER_USER_CODE)
	readiness_code = PKGRDY_CODE if frappe.db.exists("Package Readiness Result", PKGRDY_CODE) else None
	values = {
		"package_code": PKG_CODE,
		"decision_type": "Approved",
		"decided_at": get_datetime(PKGREV_DECIDED_AT),
		"from_state": PKGREV_FROM_STATE,
		"to_state": PKGREV_TO_STATE,
		"decision_reason": PKGREV_DECISION_REASON,
		"required_correction": None,
		"readiness_code": readiness_code,
		"method_decision_code": METHDEC_CODE if frappe.db.exists("Package Method Decision", METHDEC_CODE) else None,
		"audit_event_ref": PKGREV_AUDIT_EVENT_REF,
		"is_master_seed": 1,
	}
	if decided_by:
		values["decided_by"] = decided_by

	if frappe.db.exists("Package Review Decision", PKGREV_CODE):
		frappe.db.set_value(
			"Package Review Decision",
			PKGREV_CODE,
			values,
			update_modified=False,
		)
	else:
		doc = frappe.get_doc(
			{"doctype": "Package Review Decision", "review_decision_code": PKGREV_CODE, **values}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)

	for code in frappe.get_all(
		"Package Review Decision",
		filters={"package_code": PKG_CODE},
		pluck="review_decision_code",
	):
		if code != PKGREV_CODE:
			frappe.delete_doc("Package Review Decision", code, force=1)

	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{"latest_review_code": PKGREV_CODE},
		update_modified=False,
	)
