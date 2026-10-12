# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Opening Incident Access Event: the audit trail of who read an Opening incident's details or exported it, when, why and with
what outcome (Project Owner, 10 October 2026). Append-only, written only by the Bid Opening commands, carrying no incident
content, and a sealed record no Desk, list, search or export reaches; the trail is read through `incident_access.trail`."""

from __future__ import annotations

import frappe
from frappe.model.document import Document

from kentender_procurement.bid_submission.services.sealed import SealedRecordMixin


class OpeningIncidentAccessEvent(SealedRecordMixin, Document):
	def validate(self) -> None:
		if not self.flags.get("kt_bop_command"):
			frappe.throw("%s records change only through Bid Opening commands." % self.doctype)
		if not self.is_new():
			frappe.throw("An access event is never changed.")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("%s records are never deleted outside a fixture wipe." % self.doctype)
