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
from uuid import uuid4

import frappe
from frappe.utils import cstr

from kentender_core.services.command_write_guard import command_write

PLANNING_WRITE_FAMILY = "Procurement Planning"

_SCOPES = "pln_command_scopes"


class CommandScope:
	"""One running Planning command: its identity, for the idempotency journal.

	A key is bound to the command (the service function's name), the actor and
	the payload (AUD-XC-131). The scope also remembers the keys the command
	claimed so a command that finishes without recording one releases it."""

	def __init__(self, command: str, actor: str):
		self.command, self.actor = command, actor
		self.claimed: list[str] = []
		self.recorded: set[str] = set()


def current_scope() -> CommandScope | None:
	stack = frappe.flags.get(_SCOPES)
	return stack[-1] if stack else None


def planning_write():
	"""Context manager: the owning service writes a guarded Planning record."""
	return command_write(PLANNING_WRITE_FAMILY)


def planning_command(func):
	"""Decorator form of `planning_write()` for a whole service command.

	It also names the command for the idempotency journal and makes the command
	all-or-nothing in process: it runs in a savepoint, so a command that fails
	leaves no claimed key and no partial write behind even for a caller that
	does not go through a request-level rollback."""

	@wraps(func)
	def wrapper(*args, **kwargs):
		scope = CommandScope(func.__name__, cstr(kwargs.get("user") or frappe.session.user).strip())
		stack = frappe.flags.setdefault(_SCOPES, [])
		stack.append(scope)
		savepoint = f"pln_{uuid4().hex[:12]}"
		frappe.db.savepoint(savepoint)
		try:
			with planning_write():
				result = func(*args, **kwargs)
		except BaseException:
			frappe.db.rollback(save_point=savepoint)
			raise
		else:
			from kentender_procurement.procurement_planning.services import envelope

			envelope.release_unrecorded(scope)
			frappe.db.release_savepoint(savepoint)
			return result
		finally:
			stack.pop()

	return wrapper
