# Copyright (c) 2026, KenTender and contributors
"""STR-CHG-001 v1.5 §18.1 — collapse the 3-role/8-status Strategy workflow
onto 2 roles (Strategy Author, Strategy Approver) and 4 statuses (Draft,
Submitted for approval, Active, Superseded).

One-time migration, run in this order:

1. Normalize every existing `Strategic Plan Version.status` per §18.1's
   exact mapping:
     Draft, Returned                        -> Draft
     In Review, Awaiting Approval, Approved  -> Submitted for approval
     Active                                  -> Active
     Superseded, Archived                    -> Superseded
   An old Approved version is NOT auto-activated (§18.1: "Do not activate
   an old Approved version automatically") — it lands on Submitted for
   approval, same as any other not-yet-decided submission.
2. Grant "Strategy Approver" to every existing holder of "Strategy Approval
   Authority" (same responsibility, new name). Existing "Strategy Reviewer"
   holders are NOT promoted to anything (§18.1: "not promoted
   automatically").
3. Strip the "Strategy Reviewer" and "Strategy Approval Authority" `Has
   Role` grants — the old Role master records are left in place
   (documentation-only retirement, matching kentender_core's own
   retire_reference_data_role_proliferation.py precedent), only the live
   grants that would otherwise silently confer no-longer-real authority
   are removed.
"""

from __future__ import annotations

import frappe

_STATUS_MAP = {
	"Draft": "Draft",
	"Returned": "Draft",
	"In Review": "Submitted for approval",
	"Awaiting Approval": "Submitted for approval",
	"Approved": "Submitted for approval",
	"Active": "Active",
	"Superseded": "Superseded",
	"Archived": "Superseded",
}

_ROLE_REVIEWER = "Strategy Reviewer"
_ROLE_APPROVAL_AUTHORITY = "Strategy Approval Authority"
_ROLE_APPROVER = "Strategy Approver"


def execute() -> None:
	if not frappe.db.exists("DocType", "Strategic Plan Version"):
		return

	_normalize_statuses()
	_promote_approval_authority_holders()
	_strip_retired_role_grants()

	frappe.db.commit()


def _normalize_statuses() -> None:
	rows = frappe.get_all("Strategic Plan Version", fields=["name", "status"])
	for row in rows:
		new_status = _STATUS_MAP.get(row.status)
		if new_status and new_status != row.status:
			frappe.db.set_value(
				"Strategic Plan Version", row.name, "status", new_status, update_modified=False
			)


def _promote_approval_authority_holders() -> None:
	if not frappe.db.exists("Role", _ROLE_APPROVER):
		frappe.get_doc({"doctype": "Role", "role_name": _ROLE_APPROVER, "desk_access": 1}).insert(
			ignore_permissions=True
		)

	holders = frappe.get_all(
		"Has Role",
		filters={"role": _ROLE_APPROVAL_AUTHORITY, "parenttype": "User"},
		pluck="parent",
	)
	for user in holders:
		if frappe.db.exists("User", user):
			frappe.get_doc("User", user).add_roles(_ROLE_APPROVER)


def _strip_retired_role_grants() -> None:
	frappe.db.delete("Has Role", {"parenttype": "User", "role": _ROLE_REVIEWER})
	frappe.db.delete("Has Role", {"parenttype": "User", "role": _ROLE_APPROVAL_AUTHORITY})
