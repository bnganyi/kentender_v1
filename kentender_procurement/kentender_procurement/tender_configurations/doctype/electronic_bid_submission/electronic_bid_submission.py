# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document
from frappe.utils import cstr

# Meta updates allowed on sealed bids (versioning / withdrawal) — never response bodies.
_SEALED_META_FIELDS = frozenset(
	{
		"superseded_by",
		"supersedes",
		"withdrawn_at",
		"withdrawn_by",
		"status",
		"publication",
		"bidder_legal_name",
		"offer_type",
		"lots_json",
	}
)


class ElectronicBidSubmission(Document):
	def validate(self):
		prior = None
		if not self.is_new():
			prior = frappe.db.get_value("Electronic Bid Submission", self.name, "status")
		if cstr(prior) == "Sealed" and cstr(self.status) in ("Sealed", "Withdrawn"):
			if getattr(self.flags, "ignore_sealed_meta_update", False):
				return
			db_hash = frappe.db.get_value("Electronic Bid Submission", self.name, "seal_hash")
			db_resp = frappe.db.get_value("Electronic Bid Submission", self.name, "responses")
			if cstr(self.seal_hash) != cstr(db_hash) or cstr(self.responses) != cstr(db_resp or ""):
				frappe.throw(
					frappe._("Sealed electronic bids are immutable."),
					title="BID_IMMUTABLE",
				)
			# Disallow silent mutation of non-meta sealed fields.
			for field in (
				"schema_snapshot",
				"schema_hash",
				"evidence_seal_snapshot_json",
				"receipt_code",
				"seal_hash",
			):
				db_val = frappe.db.get_value(self.doctype, self.name, field)
				if cstr(self.get(field) or "") != cstr(db_val or ""):
					frappe.throw(
						frappe._("Sealed electronic bids are immutable."),
						title="BID_IMMUTABLE",
					)
			_ = _SEALED_META_FIELDS  # documented allow-list for officers tooling
