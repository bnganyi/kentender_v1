# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe.utils import getdate, today

from kentender_suppliers.services import history as history_service


def recompute_compliance(supplier_profile: str) -> str:
	"""
	Return new compliance_status: Complete | Incomplete | Expired | Non-Compliant
	(C3) -- does not persist unless caller saves profile.
	"""
	# Required registration document types
	req_types = frappe.get_all(
		"KTSM Document Type",
		filters={"required_for_registration": 1, "is_active": 1},
		pluck="name",
	)
	if not req_types:
		# no rules configured
		return "Complete"

	missing = []
	today_s = getdate(today())
	for dt in req_types:
		expires = frappe.db.get_value("KTSM Document Type", dt, "expires")
		doc = frappe.db.get_value(
			"KTSM Supplier Document",
			{
				"supplier_profile": supplier_profile,
				"document_type": dt,
				"is_current": 1,
			},
			[
				"name",
				"verification_status",
				"expiry_date",
			],
			as_dict=True,
		)
		if not doc:
			missing.append(dt)
			continue
		if doc.verification_status != "Verified":
			missing.append(dt)
			continue
		if expires and doc.expiry_date and getdate(doc.expiry_date) < today_s:
			return "Expired"

	if missing:
		return "Incomplete"
	return "Complete"


def recompute_and_save_profile(supplier_profile: str) -> None:
	"""Update profile compliance_status in DB and log if compliance status changed."""
	prof = frappe.get_doc("KTSM Supplier Profile", supplier_profile)
	before = prof.compliance_status
	after = recompute_compliance(supplier_profile)
	if before == after:
		return
	prof.db_set("compliance_status", after, update_modified=False)
	history_service.log_status_change(
		supplier_profile,
		"Compliance",
		after,
		before,
		None,
	)
