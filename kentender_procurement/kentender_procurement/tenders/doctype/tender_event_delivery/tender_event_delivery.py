# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Event Delivery: written only by the Tenders commands (AUD-XC-013), like the event it tracks. See
`kentender_core.services.command_write_guard`."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class TenderEventDelivery(CommandWriteGuardMixin, Document):
	command_write_family = "Tenders"
