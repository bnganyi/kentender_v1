# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CFG-CHG-002 v0.16 §4.9A — the one Supplier portal settings record.

Every field is written only by `kentender_core.services.public_portal.
update_public_portal_settings` (the UpdatePublicPortalSettings command), which
checks setup authority, validates the whole replacement, advances
`record_version` and audits the before/after public projection. A direct save
from anywhere else is refused, so the Desk form cannot bypass the command
(KT-STD-001 v1.9 §4).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class PublicPortalSettings(Document):
	def validate(self):
		if not frappe.flags.kt_public_portal_command:
			frappe.throw(
				"Change the Supplier portal settings in System setup.",
				title="CFG_AUTHORITY_REQUIRED",
			)
