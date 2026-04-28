# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

import frappe
from frappe import _


def assert_not_same_user_upload_and_verify(
	document_row_name: str | None, action: str
) -> None:
	"""C4: if verifying/rejecting a document, uploader (if known) must not be current user."""
	if action not in ("verify", "reject"):
		return
	if not document_row_name:
		return
	external = frappe.db.get_value(
		"KTSM Supplier Document", document_row_name, "owner"
	)
	# Simplified: if external upload flag, check; else allow internal verify
	# For v1, block same session user on document that they own from external submit path.
	ext = frappe.db.get_value("KTSM Supplier Document", document_row_name, "external_uploaded")
	if ext and frappe.db.get_value("KTSM Supplier Document", document_row_name, "owner") == frappe.session.user:
		frappe.throw(_("Separation of duties: you cannot verify your own upload."))


def assert_not_same_user_submit_and_approve(submitter: str | None) -> None:
	"""C4: approver != submitter for supplier qualification."""
	if submitter and submitter == frappe.session.user:
		frappe.throw(_("Separation of duties: you cannot approve a supplier you submitted for review."))
