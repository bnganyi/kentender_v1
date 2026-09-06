"""The AUTH-ADR-001 v1.6 §10 error contract for role-bound authorization.

§10 defines a closed set of nine codes. They are stable service results, so
`fail()` refuses anything outside the contract — an invented code is a defect
in the caller, not a new error type. This mirrors the pattern
`kentender_procurement.departmental_needs.errors` already proved: a closed set
that raises on violation makes drift impossible to introduce silently.

Domain modules keep their own user-facing codes (`NDS_SCOPE_DENIED`, or a
masked not-found where existence itself is protected) and map these onto them;
§10's codes are the shared vocabulary of the resolver, not a replacement for a
module's published error contract.
"""

from __future__ import annotations

import frappe

# The complete §10 contract. Nothing else may be raised from this layer.
ERROR_CODES: frozenset[str] = frozenset(
	{
		# You are not assigned the responsibility required for this action.
		"AUTH_RESPONSIBILITY_REQUIRED",
		# This record is outside the organisational scope of that responsibility.
		"AUTH_SCOPE_REQUIRED",
		# Your responsibility assignment is not effective at this time.
		"AUTH_ASSIGNMENT_INACTIVE",
		# This action is not currently assigned for decision.
		"AUTH_TASK_REQUIRED",
		# You completed an incompatible earlier step.
		"AUTH_SEGREGATION_BLOCKED",
		# This action is no longer available in the record's current state.
		"AUTH_STATE_CHANGED",
		# Not available for the record's Fiscal Year or current module state.
		"AUTH_PERIOD_UNAVAILABLE",
		# Another person already holds this responsibility for that scope.
		"AUTH_EXCLUSIVE_OFFICE_CONFLICT",
		# The responsibility or organisational scope is not configured consistently.
		"AUTH_CONFIGURATION_INVALID",
	}
)

# §10: "Ordinary user messages shall not name internal tables, hooks or
# permission algorithms." These are the sanctioned user-facing texts; a caller
# may pass a more specific message, but never one naming a DocType, column or
# algorithm.
DEFAULT_MESSAGES: dict[str, str] = {
	"AUTH_RESPONSIBILITY_REQUIRED": "You are not assigned the responsibility required for this action.",
	"AUTH_SCOPE_REQUIRED": "This record is outside the organisational scope of that responsibility.",
	"AUTH_ASSIGNMENT_INACTIVE": "Your responsibility assignment is not effective at this time.",
	"AUTH_TASK_REQUIRED": "This action is not currently assigned for decision.",
	"AUTH_SEGREGATION_BLOCKED": "You cannot perform this action because you completed an incompatible earlier step.",
	"AUTH_STATE_CHANGED": "This action is no longer available in the record's current state.",
	"AUTH_PERIOD_UNAVAILABLE": "This operation is not available for the record's Fiscal Year or current module state.",
	"AUTH_EXCLUSIVE_OFFICE_CONFLICT": "Another person already holds this responsibility for that scope during the selected period.",
	"AUTH_CONFIGURATION_INVALID": "The responsibility or organisational scope is not configured consistently.",
}


class ResponsibilityError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail(code: str, message: str = "") -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the AUTH-ADR-001 v1.6 §10 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	message = message or DEFAULT_MESSAGES[code]
	# Passing an already-constructed instance is what preserves `.code` through
	# frappe.throw() while still populating _server_messages, so the client
	# shows the real rejection reason rather than a generic failure.
	frappe.throw(message, exc=ResponsibilityError(code, message))
