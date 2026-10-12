# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Tender Candidate Notice: written only by the Tenders commands (AUD-XC-013). A Desk save, REST
call or script outside `command_write("Tenders")` is refused; see
`kentender_core.services.command_write_guard`."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class TenderCandidateNotice(CommandWriteGuardMixin, Document):
	command_write_family = "Tenders"
