"""The one command-write family of the Departmental Needs app (AUD-XC-008,
AUD-XC-014, AUD-XC-015).

Every Need, Revision, Review Task, Withdrawal Request, Decision, Event and the
three Planning projections change only inside `needs_command()`; a Desk form,
`/api/resource` or `frappe.client` write is refused by the controller
(`kentender_core.services.command_write_guard`). Test and seed clean-up that
must write a record directly uses `maintenance_write(NEEDS_WRITE_FAMILY, ...)`.
"""

from __future__ import annotations

from functools import wraps

from kentender_core.services.command_write_guard import command_write

NEEDS_WRITE_FAMILY = "Departmental Needs"


def needs_command(func):
	"""Open the Needs write window for one service command. Applied to the
	service function (never an endpoint), so the authorisation lives in the
	owning service and not in the request."""

	@wraps(func)
	def wrapper(*args, **kwargs):
		with command_write(NEEDS_WRITE_FAMILY):
			return func(*args, **kwargs)

	return wrapper
