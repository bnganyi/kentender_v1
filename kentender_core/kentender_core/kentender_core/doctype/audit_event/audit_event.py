from frappe.model.document import Document

from kentender_core.services.command_write_guard import CommandWriteGuardMixin


class AuditEvent(CommandWriteGuardMixin, Document):
	"""AUD-XC-010: the ledger is append-only. No user may update or delete a
	row (System Manager and Administrator included) and rows are inserted only
	by `audit_event_service.log_audit_event`. No field is user-editable."""

	command_write_family = "Audit Event"
