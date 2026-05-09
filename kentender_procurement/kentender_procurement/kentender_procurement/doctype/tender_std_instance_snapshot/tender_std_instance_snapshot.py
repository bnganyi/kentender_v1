# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender STD Instance Snapshot — STDINST-0500."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.snapshot import assert_final_snapshot_honored


class TenderSTDInstanceSnapshot(Document):
	def validate(self) -> None:
		if not self.is_new():
			prev = frappe.get_doc("Tender STD Instance Snapshot", self.name)
			assert_final_snapshot_honored(prev, self)
