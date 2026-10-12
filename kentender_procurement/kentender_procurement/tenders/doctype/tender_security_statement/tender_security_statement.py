# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Security Statement: the auditable correction that records, for a Tender published before it stated them, the
tender-security submission method and original delivery its published documents already make explicit (Project Owner,
10 October 2026). Written only by the Tenders commands (AUD-XC-013); one per Tender; never edited."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class TenderSecurityStatement(CommandWriteGuardMixin, Document):
	command_write_family = "Tenders"
