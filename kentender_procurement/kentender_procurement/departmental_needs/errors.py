"""Stable Departmental Needs service errors (NDS-CHG-001 v1.1 §9).

§9 defines a closed set of fifteen codes. They are stable service results, not
inferred from button visibility or free-text exception messages, so `fail()`
refuses any code outside the contract: an invented code is a defect in the
caller, not a new error type.
"""

from __future__ import annotations

import frappe

# The complete §9 error contract. Nothing else may be raised from this module.
ERROR_CODES: frozenset[str] = frozenset(
	{
		# No single authorised PE/OU/FY context can be resolved. Create no record.
		"NDS_CONTEXT_REQUIRED",
		# Actor lacks the exact current Frappe role and User Permission scope.
		# Discloses no protected record data, including a record's existence.
		"NDS_SCOPE_DENIED",
		# Initial creation or initial submission is outside the intake window.
		"NDS_INTAKE_NOT_OPEN",
		# Exact missing field identifiers; no task or state change is created.
		"NDS_FIELD_REQUIRED",
		"NDS_REQUIRED_BY_OUTSIDE_FY",
		"NDS_UNIT_INELIGIBLE",
		# Version maker attempted its own decision.
		"NDS_MAKER_CHECKER",
		# Command is invalid for the current Need/version state.
		"NDS_STATE_CONFLICT",
		"NDS_OPEN_SUCCESSOR_EXISTS",
		# Record version or decision token is stale. Overwrite nothing.
		"NDS_STALE_WRITE",
		"NDS_WITHDRAWAL_ALREADY_OPEN",
		# Accepted withdrawal is blocked by the returned Active Plan and Item.
		"NDS_ACTIVE_PLAN_DEPENDENCY",
		# The same key was reused with a different payload.
		"NDS_IDEMPOTENCY_CONFLICT",
		# Requested accepted version/hash is no longer current.
		"NDS_SOURCE_STALE",
		# No current accepted version exists.
		"NDS_NOT_ACCEPTED",
	}
)


class DepartmentalNeedError(frappe.ValidationError):
	def __init__(self, code: str, message: str):
		self.code = code
		super().__init__(message)


def fail(code: str, message: str) -> None:
	if code not in ERROR_CODES:
		raise ValueError(
			f"{code!r} is not part of the NDS-CHG-001 v1.1 §9 error contract. "
			f"Map the condition onto one of: {', '.join(sorted(ERROR_CODES))}."
		)
	# frappe.throw()/msgprint() populates _server_messages, which the client
	# reads to show the real rejection reason. A bare `raise` skips that, so
	# every rejection in this module rendered as a generic "Request failed"
	# regardless of cause — passing an already-constructed instance preserves
	# `.code` (msgprint reuses it as-is; see frappe.utils.messages.msgprint).
	frappe.throw(message, exc=DepartmentalNeedError(code, message))
