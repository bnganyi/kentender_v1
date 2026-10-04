# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD-TPL-IMP-001 v1.0 §4.1 — one installed STD release.

Only the installer (`flags.kt_std_install`) creates a row, and only the
lifecycle commands (`flags.kt_std_lifecycle`), the site switch
(`flags.kt_std_switch`; owner decision OD5) or the integrity verifier
(`flags.kt_std_verify`) may later change it — and then only their own
fields. Content and digest fields are immutable after installation; no Desk
action, role or site configuration can edit, activate or repair a release.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

#: May change after installation, each only through its named service.
LIFECYCLE_FIELDS = frozenset(
	{
		"lifecycle_status", "superseded_by_release_id", "superseded_at", "superseded_by_actor", "withdrawal_reason",
		"withdrawn_by", "withdrawn_at", "withdrawal_successor_release_id",
	}
)
VERIFICATION_FIELDS = frozenset({"integrity_status", "integrity_problem", "last_verified_at", "last_successful_verification_at"})
#: Owner decision OD5 (26 Sep 2026): a release is an On/Off switch on a site.
SWITCH_FIELDS = frozenset({"site_switch", "switched_by", "switched_at"})
#: Recording a later owner decision against the same installed bytes (evidence only).
DECISION_FIELDS = frozenset(
	{
		"owner_decision", "owner_approved_by", "owner_approved_at", "owner_decision_record", "owner_decision_file",
	}
)
_SYSTEM_FIELDS = frozenset({"modified", "modified_by", "creation", "owner", "idx", "docstatus", "_user_tags", "_comments", "_assign", "_liked_by"})


class InstalledSTDRelease(Document):
	def validate(self) -> None:
		flags = self.flags
		if self.is_new():
			if not flags.get("kt_std_install"):
				frappe.throw("An STD release is created only by the approved-release installer (STD-TPL-IMP-001 §5).")
			return
		if flags.get("kt_std_install"):
			# The installer completing its own insert (asset rows and files)
			# inside the one installation transaction.
			return
		if not (flags.get("kt_std_lifecycle") or flags.get("kt_std_verify") or flags.get("kt_std_bind_decision") or flags.get("kt_std_switch")):
			frappe.throw("An installed STD release cannot be edited (STD-TPL-IMP-001 §4.1).")
		allowed = set()
		if flags.get("kt_std_switch"):
			allowed |= SWITCH_FIELDS
		if flags.get("kt_std_bind_decision"):
			allowed |= DECISION_FIELDS
		if flags.get("kt_std_lifecycle"):
			allowed |= LIFECYCLE_FIELDS
		if flags.get("kt_std_verify"):
			allowed |= VERIFICATION_FIELDS
		before = self.get_doc_before_save()
		if not before:
			return
		for field in self.meta.get_valid_columns():
			if field in _SYSTEM_FIELDS or field in allowed:
				continue
			if (before.get(field) or None) != (self.get(field) or None):
				frappe.throw(f"Installed STD release field {field} is immutable.")
		if [a.as_dict(no_default_fields=True) for a in before.assets] != [a.as_dict(no_default_fields=True) for a in self.assets]:
			frappe.throw("Installed STD release assets are immutable.")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Installed STD releases are never deleted; supersede or withdraw them instead.")
