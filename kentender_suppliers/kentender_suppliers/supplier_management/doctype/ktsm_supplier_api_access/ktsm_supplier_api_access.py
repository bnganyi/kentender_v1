# Copyright (c) 2026, KenTender and contributors
# License: MIT. See license.txt

from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class KTSMSupplierAPIAccess(CommandWriteGuardMixin, Document):
	"""Who may call the supplier API for a profile. No role edits it by hand: it is written only
	inside `command_write("Supplier Registry")` (RG-13)."""

	command_write_family = "Supplier Registry"
