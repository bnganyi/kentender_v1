# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""NDS-CHG-001 v1.1 §7.1 — one durable row of the Departmental Needs outbox.

Rows are appended by a successful command in the same transaction as its
decision record, so an event exists if and only if the state change it
describes was committed. Payloads are immutable: a consumer that needs a
correction receives a later event, never a rewritten earlier one (§13).
"""

import frappe
from frappe.model.document import Document

from kentender_procurement.departmental_needs.errors import fail

IMMUTABLE_FIELDS = (
	"event_id",
	"event_type",
	"departmental_need",
	"sequence",
	"need_version",
	"superseded_version",
	"occurred_at",
	"payload",
)


class DepartmentalNeedEvent(Document):
	def validate(self):
		if self.is_new():
			return
		before = self.get_doc_before_save()
		if not before:
			return
		changed = [f for f in IMMUTABLE_FIELDS if self.get(f) != before.get(f)]
		if changed:
			fail(
				"NDS_STATE_CONFLICT",
				f"A published event is immutable. Attempted to change: {', '.join(changed)}.",
			)

	def on_trash(self):
		fail("NDS_STATE_CONFLICT", "Departmental Need Events are retained permanently.")
