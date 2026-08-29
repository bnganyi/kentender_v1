# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Planning's record of an accepted Need represented in a Plan Item.

BOUNDARY (firm D1 decision, 2026-08-29): Procurement Planning consumes Accepted
Needs only through the published handoff contract. This controller validates
through `get_current_accepted_need` (§8.1) and reads no Departmental Needs
table: that contract already establishes that the Need is accepted, that the
version is the current accepted one, and that the caller's content hash is not
stale — raising `NDS_NOT_ACCEPTED` or `NDS_SOURCE_STALE` when it is.

NDS-CHG-001 v1.1 §1.1 removes partial Need allocation: when Planning uses an
accepted Need it takes the full accepted quantity (NDS-AC-014).
"""

import frappe
from frappe.model.document import Document
from frappe.utils import cstr, flt

from kentender_procurement.departmental_needs.services.workspace import get_current_accepted_need


class PlanNeedAllocation(Document):
	def validate(self):
		if flt(self.allocated_quantity) <= 0:
			frappe.throw(
				"Allocated quantity must be greater than zero.",
				title="NDS_ALLOCATION_QUANTITY_INVALID",
			)
		source = get_current_accepted_need(
			need=self.departmental_need,
			expected_content_hash=cstr(self.source_content_hash or ""),
		)
		# §7.2 / NDS-AC-014 — only the current accepted version, at full quantity.
		if source["accepted_version"] != self.departmental_need_version:
			frappe.throw(
				"Only the current accepted version of a Need may be allocated.",
				title="NDS_SOURCE_STALE",
			)
		if flt(self.allocated_quantity) > flt(source["indicative_quantity"]):
			frappe.throw(
				"Allocated quantity exceeds the accepted Need quantity.",
				title="NDS_ALLOCATION_EXCEEDS_LINE",
			)
		if not self.source_content_hash:
			# Pin the lineage the allocation was created against (NDS-AC-037).
			self.source_content_hash = source["content_hash"]
