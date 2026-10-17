# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One original source (one drawdown line) of a cancellation recovery, with the exact effects its recovery had. A child row of
`Cancellation Resource Recovery`: inserted, changed and deleted only inside the `command_write("Requisitions")` window of the
owning command (RG-06), because Frappe's REST create inserts a child row on its own."""

from __future__ import annotations

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class CancellationRecoverySource(CommandWriteGuardMixin, Document):
	command_write_family = "Requisitions"
