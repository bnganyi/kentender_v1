# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""TPR-CHG-001 v0.6 §6.3 / plan D13 — the read-only template registry row.

Only ``kentender_procurement.tender_templates.registry.install()`` writes it,
under ``flags.kt_template_install``; no DocPerm grants write to any role,
and no Desk or ordinary administrator action can edit the installed
release (TPR-AC-034).
"""

from __future__ import annotations

import frappe
from frappe.model.document import Document


class SupportedTenderTemplate(Document):
	def validate(self) -> None:
		if not self.flags.get("kt_template_install"):
			frappe.throw("The Supported Tender Template registry is written only by the template installer (TPR-CHG-001 v0.6 §6.3).")

	def on_trash(self) -> None:
		if not self.flags.get("kt_fixture_wipe"):
			frappe.throw("Supported Tender Template rows are never deleted outside a fixture wipe.")
