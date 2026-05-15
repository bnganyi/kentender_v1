# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PUB-0310 — append-only publication approval decision rows."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class TenderPublicationApprovalDecision(Document):
	"""Immutable after insert (no ``update`` permissions for desk roles)."""

	def validate(self) -> None:
		tm2 = (self.tm2_tender or "").strip()
		if not tm2:
			frappe.throw(
				_("Set TM2 Tender."),
				title=_("Tender Publication Approval Decision"),
				exc=frappe.ValidationError,
			)
