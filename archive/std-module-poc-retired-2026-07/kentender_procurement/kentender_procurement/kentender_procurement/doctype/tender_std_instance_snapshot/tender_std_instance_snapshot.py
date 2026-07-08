# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD Instance Snapshot — STDINST-0500."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.snapshot import assert_final_snapshot_honored


class TenderSTDInstanceSnapshot(Document):
	def validate(self) -> None:
		tm2 = (self.tm2_tender or "").strip()
		if not tm2:
			frappe.throw(
				_("Set TM2 Tender."),
				title=_("Tender STD Instance Snapshot"),
				exc=frappe.ValidationError,
			)
		if not self.is_new():
			prev = frappe.get_doc("Tender STD Instance Snapshot", self.name)
			assert_final_snapshot_honored(prev, self)
