# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §4.4 — one open departmental decision task.

The task is available to users holding the Head of User Department role and the
exact native User Permission scope (§4.4). It is never described as assigned to
a named person, and carries no claim, release, priority, score, due date or
free-text note (§1.1, §4.4).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.errors import fail

OPEN = "Open"


class DepartmentalNeedReviewTask(Document):
	def validate(self):
		self._require_single_open_task()

	def _require_single_open_task(self):
		"""One Need has at most one Open task; a decision completes it atomically."""
		if self.status != OPEN:
			return
		duplicate = frappe.db.exists(
			"Departmental Need Review Task",
			{
				"departmental_need": self.departmental_need,
				"status": OPEN,
				"name": ("!=", self.name),
			},
		)
		if duplicate:
			fail(
				"NDS_STATE_CONFLICT",
				f"An open review task already exists for {self.departmental_need}.",
			)

	def on_trash(self):
		frappe.throw(
			"Departmental Need Review Tasks are retained permanently.",
			title="NDS_DELETE_FORBIDDEN",
		)
