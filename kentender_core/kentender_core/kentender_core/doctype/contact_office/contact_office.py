# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §8.5 / plan D6 — a governed contact-office master.

Tender Preparation's Task 5 names a "Contract contact office" that must be an
Active office, never a personal user (§8.5), and the IT Equipment template
renders the same governed office for clarification, submission and contract
notices (`procuring_entity.contact_office`). No office master existed; this
is the minimal shared master, mirroring `Delivery Location` (REQ-CHG-001 D2)
so Tender, Contract and Publication reuse one row rather than each owning a
copy. The rendered contact string is `display()` — never a free-text field.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class ContactOffice(Document):
	def validate(self) -> None:
		self.office_name = (self.office_name or "").strip()
		if not self.office_name:
			frappe.throw("Office name is required.")
		self.contact_email = (self.contact_email or "").strip()
		if not self.contact_email:
			frappe.throw("Contact email is required.")
		self.contact_phone = (self.contact_phone or "").strip()

	def display(self) -> str:
		"""The one string Tender documents render for this office."""
		parts = [self.office_name, self.contact_email]
		if self.contact_phone:
			parts.append(self.contact_phone)
		return ", ".join(parts)
