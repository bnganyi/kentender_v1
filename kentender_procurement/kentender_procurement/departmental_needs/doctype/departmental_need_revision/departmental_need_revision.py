# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.3 — one version of the requirement.

Draft content is mutable only until submission; submitted content is immutable
(§4.3, §13). This controller enforces field shape and the immutability guard.
Submission completeness (all six values present) is a service-layer contract.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import flt

from kentender_procurement.departmental_needs.constants import (
	DESCRIPTION_MAX,
	DESCRIPTION_MIN,
	MUTABLE_VERSION_STATUSES,
	QUANTITY_DECIMALS,
	TITLE_MAX,
	TITLE_MIN,
	VERSION_CONTENT_FIELDS,
)
from kentender_procurement.departmental_needs.errors import fail


class DepartmentalNeedVersion(Document):
	def validate(self):
		self._guard_immutable_content()
		self._validate_title()
		self._validate_free_text("description", "Description")
		self._validate_free_text("expected_operational_result", "Expected operational result")
		self._validate_quantity()

	def _guard_immutable_content(self):
		"""A version that has left Draft never changes its requirement content."""
		if self.is_new() or self.version_status in MUTABLE_VERSION_STATUSES:
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [f for f in VERSION_CONTENT_FIELDS if self.get(f) != before.get(f)]
		if changed:
			fail(
				"NDS_STATE_CONFLICT",
				f"Version {self.need_version_id} is {self.version_status} and its content is immutable. "
				f"Attempted to change: {', '.join(changed)}.",
			)

	def _validate_title(self):
		title = (self.title or "").strip()
		self.title = title
		if not (TITLE_MIN <= len(title) <= TITLE_MAX):
			fail("NDS_FIELD_REQUIRED", f"Title must be {TITLE_MIN}-{TITLE_MAX} characters.")

	def _validate_free_text(self, fieldname: str, label: str):
		"""Bounds apply to a supplied value; presence is a submission-time rule."""
		value = (self.get(fieldname) or "").strip()
		self.set(fieldname, value)
		if value and not (DESCRIPTION_MIN <= len(value) <= DESCRIPTION_MAX):
			fail("NDS_FIELD_REQUIRED", f"{label} must be {DESCRIPTION_MIN}-{DESCRIPTION_MAX} characters.")

	def _validate_quantity(self):
		if self.indicative_quantity in (None, ""):
			return
		quantity = flt(self.indicative_quantity)
		if quantity <= 0:
			fail("NDS_FIELD_REQUIRED", "Indicative quantity must be greater than zero.")
		if flt(quantity, QUANTITY_DECIMALS) != quantity:
			fail(
				"NDS_FIELD_REQUIRED",
				f"Indicative quantity allows at most {QUANTITY_DECIMALS} decimals.",
			)

	def on_trash(self):
		fail("NDS_STATE_CONFLICT", "Departmental Need Versions are retained permanently.")
