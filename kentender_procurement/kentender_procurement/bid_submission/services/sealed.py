# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The sealed-bid and tender-security records refuse every read that is not a
service's own (Project Owner, 10 October 2026).

A bid's existence, its count, the bidder's identity, its receipt and the
tender-security intake of a supplier are not Administrator's or System
Manager's to see before the opening — nor after it, unless a business
permission says so. Four layers close the doors:

1. no DocPerm row grants these records to any role;
2. `has_permission` and `permission_query_conditions` hooks (hooks.py) deny
   every user a record or a list — lists, counts, reports, exports, link search;
3. this mixin makes the document itself refuse a read, which closes the one
   door the hooks cannot: Frappe lets Administrator past `has_permission`, so a
   direct record URL or REST read as Administrator would otherwise open;
4. `before_request` refuses the private files attached to these records.

All four are application restrictions. A database or infrastructure operator
is outside them: the production custody and key controls of TRUST-ADR-001 are
what bind that operator, not these screens."""

from __future__ import annotations

import frappe

# Every record family whose existence, count, identity, receipt or security facts
# are sealed until an authorised opening (and then follow business permissions only).
SEALED_DOCTYPES = (
	"Bid Section Response", "Bid Evidence", "Bid Draft Change", "Bid Command Journal", "Bid Receipt", "Bid Submission Change",
	"Bidder Arrangement", "Bid Organisation Snapshot", "Bid Workspace", "Bid Submission Attempt", "Bid Submission Version",
	"Bid Submission Event", "Tender Box Envelope", "Bid Opening Handoff", "Bid Hand-off", "Bid Submission Close", "Bid Submission Incident",
	"Tender Security Intake", "Tender Security Intake Match", "Tender Security Exposure", "Tender Security Duty Conflict", "Tender Security Verification",
	# Project Owner, 10 October 2026: Opening incidents and the opening records that carry an envelope identifier or a bidder's name are the
	# restricted incident workflow's and the committee's, never a Desk read by System Manager status alone
	"Opening Access Incident", "Opening Exception", "Opening Decision Item", "Opening Entry", "Opening Register Request", "Opening Incident Access Event",
)
# Documents whose private files are never served by URL: the owning service delivers them to the right person.
SEALED_ATTACHMENTS = ("Bid Evidence",)


class SealedRecordMixin:
	def has_permission(self, permtype="read", *, debug=False, user=None) -> bool:
		# Only the owning service (it sets `ignore_permissions`) reads or writes these.
		return bool(self.flags.ignore_permissions)


def refuse_sealed_files() -> None:
	"""`before_request`: a private file attached to a sealed record is not served by
	its URL to anyone, Administrator included."""
	path = getattr(frappe.local.request, "path", "") if getattr(frappe.local, "request", None) else ""
	if not path.startswith("/private/files/"):
		return
	from urllib.parse import unquote

	attached = frappe.db.get_all("File", filters={"file_url": unquote(path)}, pluck="attached_to_doctype")
	if any(doctype in SEALED_ATTACHMENTS for doctype in attached):
		raise frappe.PermissionError("This file is not available.")
