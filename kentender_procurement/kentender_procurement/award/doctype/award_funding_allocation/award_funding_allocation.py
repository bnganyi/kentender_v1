# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""AWD-CHG-001 v0.7 §7.1 — the retained `AwardFundingAllocation.v1`. Immutable: once written, only its status and `superseded_by` change, and only when a corrected source gives a new version."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

IMMUTABLE = ("allocation_id", "award_case", "cycle", "decision", "decision_version", "version", "currency", "supported_total", "payload_json", "digest")


class AwardFundingAllocation(Document):
	def validate(self) -> None:
		# written only by Award commands (`flags.kt_awd_command`), never by a Desk save or script (plan D2)
		if not self.flags.get("kt_awd_command"):
			frappe.throw("%s records change only through Award commands." % self.doctype)
		before = self.get_doc_before_save()
		if before is not None:
			changed = [field for field in IMMUTABLE if str(before.get(field) or "") != str(self.get(field) or "")]
			if changed:
				frappe.throw("An Award funding allocation is immutable; a corrected source gives a new version (%s)." % ", ".join(changed))

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
