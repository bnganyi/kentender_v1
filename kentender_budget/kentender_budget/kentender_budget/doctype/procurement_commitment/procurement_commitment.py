# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""BUD-CHG-001 v1.16 §4.6 — the current contract obligation: converted from a reservation, or recognised by an approved existing-contract entry.

The commitment carries the Budget Line it is charged to. Every reader of Committed reads the line from here, so a commitment with no reservation counts exactly as one with a reservation does.
A conversion keeps its reservation, and its line is that reservation's line. An entry has no reservation and names the allocation row that created it."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin
from kentender_budget.services.budget_write_family import BUDGET_WRITE_FAMILY

ORIGIN_CONVERSION = "Reservation conversion"
ORIGIN_ENTRY = "Existing-contract entry"


class ProcurementCommitment(CommandWriteGuardMixin, Document):
	command_write_family = BUDGET_WRITE_FAMILY

	def validate(self) -> None:
		super().validate()  # the command-write guard first: a user's direct save is refused before anything else is decided
		self.origin = self.origin or ORIGIN_CONVERSION
		self.entry_row = self.entry_row or None  # NULL, not '': the unique key on entry rows then ignores every conversion
		if self.origin == ORIGIN_CONVERSION:
			if not self.reservation:
				frappe.throw(_("A commitment made by converting a reservation names that reservation."), title="BUDGET_INVALID_STATE")
			held = frappe.db.get_value("Funding Reservation", self.reservation, ["budget", "budget_line"], as_dict=True)
			if not held:
				frappe.throw(_("Funding Reservation {0} not found").format(self.reservation), frappe.DoesNotExistError)
			if self.budget_line and self.budget_line != held.budget_line:
				frappe.throw(_("A converted commitment is charged to its reservation's Budget Line."), title="BUDGET_INVALID_STATE")
			self.budget, self.budget_line = held.budget, held.budget_line
			return
		if self.reservation:
			frappe.throw(_("An existing-contract entry creates no reservation link."), title="BUDGET_INVALID_STATE")
		if not self.entry_row or not self.budget_line:
			frappe.throw(_("An existing-contract commitment names its entry row and its Budget Line."), title="BUDGET_INVALID_STATE")
		self.budget = frappe.db.get_value("Procurement Budget Line", self.budget_line, "budget")
