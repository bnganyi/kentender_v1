# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cstr


# Publication setup fields only — never tender configuration / STD / schema content.
PUBLICATION_SETUP_FIELDS = frozenset(
	{
		"publication_datetime",
		"clarification_deadline",
		"submission_deadline",
		"opening_datetime",
		"bidder_visibility",
		"supplier_visibility",
		"tender_notice",
		"activate_bidder_workspace",
		"bidder_workspace_activation",
		"acknowledgement_confirmed",
		"status",
	}
)

PACKAGE_LOCKED_FIELDS = frozenset(
	{
		"configuration",
		"confirmed_package",
		"document_hash",
		"package_payload",
		"configuration_ref",
		"publication_ref",
		"electronic_template_id",
		"electronic_template_version",
		"electronic_template_snapshot",
		"electronic_template_hash",
		"publication_version",
		"prior_publication_version",
	}
)

TERMINAL_STATUSES = frozenset({"Cancelled", "Returned", "Published"})


def allocate_publication_ref() -> str:
	"""Business code for UI (mock: PUB-2026-00018). Internal name stays hash."""
	return cstr(make_autoname("PUB-.YYYY.-.#####"))


class ITTenderPublicationRecord(Document):
	def before_insert(self):
		if not cstr(self.publication_ref or "").strip():
			self.publication_ref = allocate_publication_ref()

	def validate(self):
		# Sync legacy checkboxes with v7 field names.
		if self.activate_bidder_workspace and not self.bidder_workspace_activation:
			self.bidder_workspace_activation = self.activate_bidder_workspace
		elif self.bidder_workspace_activation and not self.activate_bidder_workspace:
			self.activate_bidder_workspace = self.bidder_workspace_activation
		if self.bidder_visibility and not self.supplier_visibility:
			self.supplier_visibility = self.bidder_visibility
		elif self.supplier_visibility and not self.bidder_visibility:
			self.bidder_visibility = self.supplier_visibility
		if not cstr(self.publication_ref or "").strip():
			self.publication_ref = allocate_publication_ref()

		if self.is_new() or getattr(self.flags, "ignore_publication_boundary", False):
			return
		prior_status = cstr(frappe.db.get_value(self.doctype, self.name, "status") or "")
		if prior_status in TERMINAL_STATUSES and not getattr(
			self.flags, "ignore_publication_lock", False
		):
			frappe.throw(
				frappe._("Published, cancelled, or returned publication records cannot be edited."),
				title="PUBLICATION_LOCKED",
			)
		if cint_flag(frappe.db.get_value(self.doctype, self.name, "setup_locked")) and not getattr(
			self.flags, "ignore_publication_lock", False
		):
			frappe.throw(
				frappe._("Publication setup is locked after publish."),
				title="PUBLICATION_LOCKED",
			)
		# Block mutation of package-bound identity / payload fields.
		for field in PACKAGE_LOCKED_FIELDS:
			db_val = frappe.db.get_value(self.doctype, self.name, field)
			if cstr(self.get(field) or "") != cstr(db_val or ""):
				frappe.throw(
					frappe._(
						"Publications cannot change the confirmed tender document package "
						"or tender configuration artifacts."
					),
					title="PUBLICATION_BOUNDARY",
				)


def cint_flag(value) -> int:
	try:
		return 1 if int(value or 0) else 0
	except (TypeError, ValueError):
		return 1 if value else 0
