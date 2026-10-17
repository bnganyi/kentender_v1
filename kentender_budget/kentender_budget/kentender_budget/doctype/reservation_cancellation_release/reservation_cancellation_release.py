# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.17 §4.13 — one release of an unused reservation carried out by a verified whole-Tender
cancellation recovery. Its own record, written only by the Budget services; the reservation's original amount
and authorisation are never edited."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY


class ReservationCancellationRelease(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY
