# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""STD Instance lifecycle state machine — ``StdInstanceStateService``.

STDINST-0120. Enforces allowed transitions (pack §7); terminal statuses cannot change.
"""

from __future__ import annotations

from collections import defaultdict

import frappe
from frappe import _
from frappe.model.document import Document

from kentender_procurement.tender_management.std_instance.instance import INSTANCE_STATUSES

# Pack §7 — terminal rows cannot transition to a different status
TERMINAL_INSTANCE_STATUSES: frozenset[str] = frozenset({"Superseded", "Cancelled"})

# Non-terminal: may transition to Cancelled (and other edges)
_NON_TERMINAL_STATUSES: frozenset[str] = frozenset(set(INSTANCE_STATUSES) - TERMINAL_INSTANCE_STATUSES)

# Pack §7 plus supersession from pre-published states (binding / reissue)
_SUPERSEDE_FROM: frozenset[str] = frozenset(
	{
		"Draft",
		"In Configuration",
		"Validation Blocked",
		"Ready for Publication",
		"Locked for Approval",
		"Published Locked",
		"Addendum Pending",
		"Addendum Regenerated",
	}
)

_RAW_EDGES: tuple[tuple[str, str], ...] = (
	("Draft", "In Configuration"),
	("In Configuration", "Validation Blocked"),
	("Validation Blocked", "In Configuration"),
	("In Configuration", "Ready for Publication"),
	("Ready for Publication", "Locked for Approval"),
	("Locked for Approval", "In Configuration"),
	("Locked for Approval", "Published Locked"),
	("Published Locked", "Addendum Pending"),
	("Addendum Pending", "Addendum Regenerated"),
	("Addendum Regenerated", "Published Locked"),
	("Published Locked", "Superseded"),
)


def _build_allowed_transitions() -> dict[str, frozenset[str]]:
	out: dict[str, set[str]] = defaultdict(set)
	for frm, to in _RAW_EDGES:
		out[frm].add(to)
	for s in _NON_TERMINAL_STATUSES:
		out[s].add("Cancelled")
	for s in _SUPERSEDE_FROM:
		out[s].add("Superseded")
	return {k: frozenset(v) for k, v in out.items()}


ALLOWED_INSTANCE_TRANSITIONS: dict[str, frozenset[str]] = _build_allowed_transitions()


class StdInstanceStateService:
	"""Validate and apply ``Tender STD Instance`` lifecycle transitions."""

	@staticmethod
	def get_allowed_targets(from_status: str) -> frozenset[str]:
		return ALLOWED_INSTANCE_TRANSITIONS.get(from_status, frozenset())

	@staticmethod
	def assert_transition_allowed(from_status: str | None, to_status: str | None) -> None:
		if not to_status:
			frappe.throw(_("Instance status cannot be empty."), title=_("Invalid Transition"))
		if from_status == to_status:
			return
		if from_status in TERMINAL_INSTANCE_STATUSES:
			frappe.throw(
				_("Cannot change instance status from terminal state {0}.").format(from_status),
				title=_("Terminal STD Instance Status"),
			)
		allowed = ALLOWED_INSTANCE_TRANSITIONS.get(from_status or "", frozenset())
		if to_status not in allowed:
			frappe.throw(
				_("Transition not allowed: {0} → {1}").format(from_status, to_status),
				title=_("Invalid STD Instance Transition"),
			)

	@staticmethod
	def apply_transition(
		instance_name: str,
		to_status: str,
		*,
		ignore_permissions: bool = False,
	) -> Document:
		doc = frappe.get_doc("Tender STD Instance", instance_name)
		StdInstanceStateService.assert_transition_allowed(doc.instance_status, to_status)
		doc.instance_status = to_status
		doc.save(ignore_permissions=ignore_permissions)
		return doc
