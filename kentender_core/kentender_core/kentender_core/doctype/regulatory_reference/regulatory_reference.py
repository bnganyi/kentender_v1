# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.11 §4.6 — one immutable, effective-dated version of a
`Regulatory Reference Set`. Same proven pattern as `Procedure Schedule
Profile` and `Business Day Calendar`: a newer overlapping version
supersedes the earlier one (triggered by the service, not this hook), and
never deleted outside a fixture purge. It freezes once a source check is
recorded against it or once it takes effect; until then it is unfinished
configuration and is corrected in place
(`configuration_versions.version_editable`).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.configuration_versions import guard_in_place_edit

_MUTABLE_AFTER_INSERT = frozenset({"status", "modified", "modified_by", "docstatus", "idx", "verification_status"})


class RegulatoryReference(Document):
	def validate(self):
		if not self.effective_from:
			frappe.throw("Enter the date this reference version takes effect.", title="CFG_REFERENCE_INVALID")
		if self.effective_until and str(self.effective_until) < str(self.effective_from):
			frappe.throw("The reference version cannot end before it takes effect.", title="CFG_REFERENCE_INVALID")
		# `kt_verify` is the source check appending its own result, which is
		# evidence about the version rather than a change to it.
		if getattr(self.flags, "kt_verify", False):
			return
		guard_in_place_edit(self, mutable_fields=_MUTABLE_AFTER_INSERT)

	def on_trash(self):
		if not getattr(self.flags, "kt_fixture_purge", False):
			frappe.throw(
				"Regulator reference versions are retained for audit and cannot be deleted.",
				title="CFG_REFERENCE_IMMUTABLE",
			)
