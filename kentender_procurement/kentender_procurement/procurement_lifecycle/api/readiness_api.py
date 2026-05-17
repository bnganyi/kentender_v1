# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R6-001 / R6-002 / R6-003 — Desk whitelist for `get_business_readiness_summary` (pack §13).

Authenticated users with read access on the target object may load the summary JSON
used by ``BusinessReadinessSummary`` (`plc-business-readiness-summary`).

R6-003 adds ``can_view_technical_output_codes`` so the client may show Bundle / DSM /
DOM / DEM / DCM lines only when authorized (UI still keeps them inside a collapsed
drawer until expanded).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr

from kentender_procurement.procurement_lifecycle.business_readiness_summary import (
    get_business_readiness_summary,
)


def _require_logged_in() -> None:
    if frappe.session.user in (None, "Guest"):
        frappe.throw(
            frappe._("You must be logged in to view business readiness."),
            frappe.PermissionError,
        )


def _can_view_technical_output_codes_for_session() -> bool:
    """R6-003 — STD output codes (Bundle, DSM, …) may be shown in the technical drawer.

    Desk sessions that already passed ``TM2 Tender`` read are treated as internal
    procurement users. **Website User** sessions without a clearing internal role do
    not receive raw output codes (supplier-style portal users).

    Matches PLC-NB-004: technical evidence stays available to appropriate internal users.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return False
    user_type = frappe.db.get_value("User", user, "user_type") or "System User"
    roles = set(frappe.get_roles(user))
    internal_clearing = {
        "System Manager",
        "Administrator",
        "Purchase User",
        "Purchase Manager",
        "Procurement Officer",
        "Auditor",
        "Accounts User",
    }
    if roles & internal_clearing:
        return True
    if user_type != "Website User":
        return True
    return False


@frappe.whitelist()
def read_business_readiness_summary(
    object_type: str | None = None,
    object_code: str | None = None,
) -> dict[str, Any]:
    """Return the R3-016 business readiness summary for a supported object (Desk / frappe.call).

    :param object_type: Currently only ``\"TM2 Tender\"``.
    :param object_code: Tender code (document name equals ``tender_code``).
    :raises frappe.PermissionError: Guest or missing TM2 read permission.
    """
    _require_logged_in()
    ot = cstr(object_type or "").strip()
    oc = cstr(object_code or "").strip()
    if not ot or not oc:
        frappe.throw(
            frappe._("object_type and object_code are required."),
            frappe.ValidationError,
        )
    if ot != "TM2 Tender":
        frappe.throw(
            frappe._("Unsupported object_type for business readiness."),
            frappe.ValidationError,
        )
    if not frappe.db.exists("TM2 Tender", oc):
        frappe.throw(
            frappe._("TM2 Tender not found."),
            frappe.DoesNotExistError,
        )
    if not frappe.has_permission("TM2 Tender", "read", doc=oc):
        frappe.throw(
            frappe._("You are not permitted to read this TM2 Tender."),
            frappe.PermissionError,
        )

    out = get_business_readiness_summary(ot, oc)
    out["can_view_technical_output_codes"] = _can_view_technical_output_codes_for_session()
    return out
