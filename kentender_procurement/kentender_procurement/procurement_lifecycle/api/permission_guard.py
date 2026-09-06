# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R3-019 / LV-R3-019-01 — **Procurement Lifecycle API permission enforcement** (pack §10.4).

## Goal (why this module exists)

Centralise all role/permission checks for the Procurement Lifecycle read APIs so
that the enforcement boundary is **auditable in one place** and consistent across
``journey_api.py`` and ``handoff_api.py``.

Before this module, each API file maintained its own ``_require_*`` helpers. While
functionally equivalent, the scattered placement made it harder to audit the
boundary against the G0-006 threat model and G0-011 role matrix.

## Access model (pack §10.4 + G0-006)

| API | Gate |
|---|---|
| Journey list/detail/by-object/steps | ``read`` on ``Procurement Journey``. |
| Journey evidence timeline | ``read`` on ``Procurement Journey`` (highest-risk endpoint per G0-006 §4). |
| Handoff card detail | ``read`` on ``Procurement Handoff Card``. |
| Refresh handoff | ``write`` on ``Procurement Handoff Card`` (authorised source-module roles / system service). |

**Default deny for Guest** on every operation (G0-006 mitigation 2).

## Internal roles (G0-011 matrix, all hold ``read`` on both DocTypes)

Requisitioner, Planning Authority, Procurement Planner, Procurement Officer,
Finance Reviewer, Department Approver, Auditor, Administrator, System Manager.

("Strategy Manager" was removed here with the Role itself — see
`kentender_strategy/patches/str_chg_001_v1_7_delete_strategy_manager_role.py`.
It named Strategy authority it had not carried since the STR-CHG-001 rebuild,
and survived only as this cross-app read grant.)

## Non-internal actors

Supplier portal users, unauthenticated guests, and any user whose Frappe session
lacks the above permissions are **denied by default** — see G0-006 §3 (access matrix)
and §4 (mitigations).  No supplier-readable variant is defined in v1 rectification
until an explicit contract is designed and accepted (PLC-NB-005).
"""

from __future__ import annotations

import frappe

# ---------------------------------------------------------------------------
# Authoritative role lists (G0-011 LV-G0-011-01, LV-G0-011-02)
# ---------------------------------------------------------------------------

#: All internal Desk roles that should have ``read`` on Procurement Lifecycle objects.
JOURNEY_READ_ROLES: frozenset[str] = frozenset(
    {
        "System Manager",
        "Administrator",
        "Planning Authority",
        "Requisitioner",
        "Procurement Planner",
        "Procurement Officer",
        "Finance Reviewer",
        "Department Approver",
        "Auditor",
    }
)

#: Only System Manager / Administrator carry ``write`` on these objects by default.
#: Source module roles may be granted write via DocPerm configuration; the guard
#: uses ``frappe.has_permission`` dynamically so org-specific overrides take effect.
JOURNEY_WRITE_ROLES: frozenset[str] = frozenset({"System Manager", "Administrator"})
HANDOFF_WRITE_ROLES: frozenset[str] = frozenset({"System Manager", "Administrator"})

# ---------------------------------------------------------------------------
# Core guard: require authentication (non-Guest)
# ---------------------------------------------------------------------------


def _require_auth(operation: str = "") -> None:
    """Raise ``PermissionError`` if the current session is Guest (unauthenticated).

    This is the first gate before any DocType permission check.
    """
    if frappe.session.user == "Guest":
        suffix = f" ({operation})" if operation else ""
        frappe.throw(
            f"Authentication required to access Procurement Lifecycle APIs{suffix}.",
            frappe.PermissionError,
        )


# ---------------------------------------------------------------------------
# Journey permission guards
# ---------------------------------------------------------------------------


def require_journey_read(operation: str = "") -> None:
    """Enforce ``read`` access on ``Procurement Journey`` (pack §10.4 / G0-006).

    Applies to: list_journeys, get_journey, get_journey_by_object,
    get_journey_steps, get_journey_evidence.

    :raises frappe.PermissionError: Guest, or user without read DocPerm.
    """
    _require_auth(operation)
    if not frappe.has_permission("Procurement Journey", "read"):
        suffix = f" ({operation})" if operation else ""
        frappe.throw(
            f"You do not have permission to read Procurement Journey records{suffix}.",
            frappe.PermissionError,
        )


def user_has_journey_read(user: str | None = None) -> bool:
    """Return ``True`` if *user* (defaults to current session) can read Procurement Journey.

    Useful for programmatic checks without raising exceptions.
    """
    u = user or frappe.session.user
    if u == "Guest":
        return False
    return bool(frappe.has_permission("Procurement Journey", "read", user=u))


# ---------------------------------------------------------------------------
# Handoff Card permission guards
# ---------------------------------------------------------------------------


def require_handoff_read(operation: str = "") -> None:
    """Enforce ``read`` access on ``Procurement Handoff Card`` (pack §10.4 / G0-006).

    Applies to: get_handoff_card.

    Supplier portal users are denied by default — no supplier-visible variant is
    defined until PLC-NB-005 is designed and accepted.

    :raises frappe.PermissionError: Guest, or user without read DocPerm.
    """
    _require_auth(operation)
    if not frappe.has_permission("Procurement Handoff Card", "read"):
        suffix = f" ({operation})" if operation else ""
        frappe.throw(
            f"You do not have permission to read Procurement Handoff Card records{suffix}.",
            frappe.PermissionError,
        )


def require_handoff_write(operation: str = "") -> None:
    """Enforce ``write`` access on ``Procurement Handoff Card`` (pack §10.4 / G0-006).

    Applies to: refresh_handoff_card.  Intended for authorised source-module roles
    or system services; by default only System Manager / Administrator have write.

    :raises frappe.PermissionError: Guest, or user without write DocPerm.
    """
    _require_auth(operation)
    if not frappe.has_permission("Procurement Handoff Card", "write"):
        suffix = f" ({operation})" if operation else ""
        frappe.throw(
            f"You do not have permission to refresh Procurement Handoff Card records{suffix}. "
            "This action is restricted to authorised source module roles.",
            frappe.PermissionError,
        )


def user_has_handoff_read(user: str | None = None) -> bool:
    """Return ``True`` if *user* (defaults to current session) can read Handoff Cards."""
    u = user or frappe.session.user
    if u == "Guest":
        return False
    return bool(frappe.has_permission("Procurement Handoff Card", "read", user=u))


def user_has_handoff_write(user: str | None = None) -> bool:
    """Return ``True`` if *user* (defaults to current session) can write Handoff Cards."""
    u = user or frappe.session.user
    if u == "Guest":
        return False
    return bool(frappe.has_permission("Procurement Handoff Card", "write", user=u))
