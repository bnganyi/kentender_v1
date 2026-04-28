# Copyright (c) 2026, KenTender and contributors

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class STDAuditEvent(Document):
	def on_trash(self):
		frappe.throw(_("STD Audit Event is append-only and cannot be deleted."), title=_("Delete blocked"))

