# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.3 — one revision of the requirement.

Draft content is mutable only until submission; submitted content is immutable
(§4.3, §13). This controller enforces field shape and the immutability guard.
Submission completeness (all six values present) is a service-layer contract.
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.departmental_needs.write_family import NEEDS_WRITE_FAMILY

from kentender_procurement.departmental_needs.constants import (
	DESCRIPTION_MAX,
	DESCRIPTION_MIN,
	MUTABLE_REVISION_STATUSES,
	TITLE_MAX,
	TITLE_MIN,
	REVISION_CONTENT_FIELDS,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.quantity import require_valid_quantity


class DepartmentalNeedRevision(CommandWriteGuardMixin, Document):
	"""Writable only by the Departmental Needs commands (AUD-XC-008/014): the
	command-only write guard refuses every user save, insert and delete."""

	command_write_family = NEEDS_WRITE_FAMILY

	def validate(self):
		super().validate()
		self._guard_immutable_content()
		self._validate_title()
		self._validate_free_text("description", "Description")
		self._validate_free_text("expected_operational_result", "Expected operational result")
		self._validate_quantity()

	def _guard_immutable_content(self):
		"""A revision that has left Draft never changes its requirement content."""
		if self.is_new() or self.revision_status in MUTABLE_REVISION_STATUSES:
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [f for f in REVISION_CONTENT_FIELDS if self.get(f) != before.get(f)]
		if changed:
			fail(
				"NDS_STATE_CONFLICT",
				f"Revision {self.need_revision_id} is {self.revision_status} and its content is immutable. "
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
		"""Exact quantity under the unit's precision and whole-number rule (§4.9)."""
		require_valid_quantity(self.indicative_quantity, self.unit)

	def on_trash(self):
		fail("NDS_STATE_CONFLICT", "Departmental Need Revisions are retained permanently.")
