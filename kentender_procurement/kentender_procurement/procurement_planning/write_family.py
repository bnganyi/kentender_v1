"""The command-write family of Procurement Planning (AUD-XC-007).

Annual Plan, Annual Plan Version, Plan Item (`Annual Plan Item`), Plan Source
Allocation, Departmental Plan, Departmental Plan Version and Departmental Plan
Entry change only inside a Planning service command. A Desk form,
`/api/resource` or `frappe.client` write is refused by the controller
(`kentender_core.services.command_write_guard`), whoever the user is.

`planning_command()` opens the window around a whole service command (used by
`envelope.bump`, the one save every lifecycle step goes through, and by the
create/delete paths that do not). Test and seed code that must write a record
directly uses `maintenance_write(PLANNING_WRITE_FAMILY, reason=...)`.
"""

from __future__ import annotations

from functools import wraps

from kentender_core.services.command_write_guard import command_write

PLANNING_WRITE_FAMILY = "Procurement Planning"


def planning_write():
	"""Context manager: the owning service writes a guarded Planning record."""
	return command_write(PLANNING_WRITE_FAMILY)


def planning_command(func):
	"""Decorator form of `planning_write()` for a whole service command."""

	@wraps(func)
	def wrapper(*args, **kwargs):
		with planning_write():
			return func(*args, **kwargs)

	return wrapper
