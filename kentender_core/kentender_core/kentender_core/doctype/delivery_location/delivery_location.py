# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.6 D2 — a governed delivery/inspection location master.

No Location doctype existed anywhere in KenTender (Needs forbids a
delivery-location field; only ERPNext's assets-module Location tree existed,
which carries geo/tree semantics that do not apply here). This is the
minimal shared master a Requisition's ``delivery_location`` Links to; Tender,
Contract and Inspection reuse the same row rather than each owning a copy.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class DeliveryLocation(Document):
	def validate(self) -> None:
		self.location_name = (self.location_name or "").strip()
		if not self.location_name:
			frappe.throw("Location name is required.")
		self.address = (self.address or "").strip()
		if not self.address:
			frappe.throw("Address is required.")
