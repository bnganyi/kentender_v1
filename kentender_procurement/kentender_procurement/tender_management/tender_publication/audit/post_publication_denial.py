# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0610 — tender publication audit when a post-publication direct edit is denied."""

from __future__ import annotations

import frappe
from frappe.utils import now_datetime

from kentender_core.services.audit_event_service import log_audit_event

from kentender_procurement.tender_management.tender_publication.audit.codes import (
	AUDIT_POST_PUBLICATION_EDIT_DENIED,
	AUDIT_TENDER_PUBLICATION_ADDENDUM_REQUIRED_NOTICE,
	DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
)
from kentender_procurement.tender_management.tender_publication.audit.publication_audit import (
	emit_publication_audit_event,
)


def emit_post_publication_edit_denied_audit(
	*,
	instance_code: str,
	attempted_change: str,
	performed_by: str | None = None,
) -> str:
	"""Append ``TENDER_PUBLICATION_POST_PUBLICATION_EDIT_DENIED`` with stable ``denial_code`` (pack §14)."""
	ic = (instance_code or "").strip()
	ac = (attempted_change or "").strip() or "unknown_change"
	tm2_name = (frappe.db.get_value("Tender STD Instance", ic, "tm2_tender") or "").strip()
	tender = tm2_name
	user = performed_by or getattr(frappe.session, "user", None) or "Administrator"

	if tm2_name and frappe.db.exists("TM2 Tender", tm2_name):
		doc_type = "TM2 Tender"
		doc_name = tm2_name
	else:
		doc_type = "Tender STD Instance"
		doc_name = ic

	row = log_audit_event(
		event_type=AUDIT_POST_PUBLICATION_EDIT_DENIED,
		entity="TENDER_PUBLICATION",
		document_type=doc_type,
		document_name=doc_name,
		action="deny_post_publication_edit",
		performed_by=user,
		timestamp=now_datetime(),
		metadata={
			"event_code": "POST_PUBLICATION_EDIT_DENIED",
			"denial_code": DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
			"instance_code": ic,
			"tender_code": tender or None,
			"attempted_change": ac,
			"guidance": "addendum_required",
		},
	)
	if tm2_name and frappe.db.exists("TM2 Tender", tm2_name):
		tc = (
			frappe.db.get_value("TM2 Tender", tm2_name, "tender_code")
			or tm2_name
		)
		tc = str(tc or "").strip() or tm2_name
		emit_publication_audit_event(
			event_type=AUDIT_TENDER_PUBLICATION_ADDENDUM_REQUIRED_NOTICE,
			tender_code=tc,
			action="addendum_required_notice",
			performed_by=user,
			instance_code=ic,
			details={
				"denial_code": DENIAL_POST_PUBLICATION_EDIT_ADDENDUM_REQUIRED,
				"attempted_change": ac,
				"related_audit_event": row,
			},
		)
	return row
