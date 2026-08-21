# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.constants import STATE_DRAFT, STATE_RETURNED


class DepartmentalNeedAttachment(Document):
	def validate(self):
		if self.is_new():
			return
		before = frappe.db.get_value(
			"Departmental Need Attachment", self.name, ["is_active", "scan_status"], as_dict=True
		)
		# The only legal post-insert mutations are: a scan-status transition (the
		# external scanner callback), or the single logical-delete flip 1->0 (only
		# while the Need is still Draft/Returned). Everything else is immutable.
		deleted = before.is_active and not self.is_active
		scan_changed = before.scan_status != self.scan_status
		if not deleted and not scan_changed:
			frappe.throw("Departmental Need Attachment records are immutable once uploaded.", title="NDS_ATTACHMENT_IMMUTABLE")
		if deleted:
			state = frappe.db.get_value("Departmental Need", self.departmental_need, "status")
			if state not in {STATE_DRAFT, STATE_RETURNED}:
				frappe.throw(
					"Attachments on an Accepted or Submitted Departmental Need are immutable.",
					frappe.PermissionError, title="NDS_CONTENT_LOCKED",
				)

	def on_trash(self):
		frappe.throw(
			"Departmental Need Attachments are retained and cannot be deleted — use the logical remove action.",
			frappe.PermissionError, title="NDS_DELETE_FORBIDDEN",
		)
