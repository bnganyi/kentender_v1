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

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.write_family import NEEDS_WRITE_FAMILY

IMMUTABLE_FIELDS = (
	"event_id",
	"event_type",
	"departmental_need",
	"sequence",
	"need_revision",
	"superseded_revision",
	"occurred_at",
	"payload",
)


class DepartmentalNeedEvent(CommandWriteGuardMixin, Document):
	"""Appended only by the Departmental Needs commands (RG-08): an insert starts a
	departmental plan (`dpp_autostart` hooks `after_insert`), so the command-only
	write guard refuses every user insert, save and delete."""

	command_write_family = NEEDS_WRITE_FAMILY

	def validate(self):
		super().validate()
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
		super().on_trash()
		fail("NDS_STATE_CONFLICT", "Departmental Need Events are retained permanently.")
