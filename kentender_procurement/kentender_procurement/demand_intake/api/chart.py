# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE

"""DIA Hub — Budget Consumption chart data (H12).

Returns the top 5 departments by total active demand value, with two
series per department:

  total_value    — sum of total_amount for all non-cancelled, non-rejected demands
  approved_value — sum of total_amount for Approved + Planning Ready demands only

Used to render the grouped bar chart on the DIA Hub landing page.
"""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import flt, now_datetime


# Statuses considered "active" (i.e. not terminal-rejected/cancelled)
_ACTIVE_STATUSES = (
    "Draft",
    "Pending HoD Approval",
    "Pending Finance Approval",
    "Approved",
    "Planning Ready",
)

# Statuses that count as "approved/ready" for the second series
_APPROVED_STATUSES = ("Approved", "Planning Ready")


def _current_fy_label() -> str:
    """Return a human-readable period label e.g. 'FY 2026'."""
    try:
        year = now_datetime().year
        # Kenya FY runs Jul–Jun: if month >= 7 we are in the new FY
        month = now_datetime().month
        fy_start = year if month >= 7 else year - 1
        return f"FY {fy_start}/{str(fy_start + 1)[2:]}"
    except Exception:
        return "Current FY"


@frappe.whitelist()
def get_dia_consumption_chart_data():
    """Return top-5 departments by total active demand value for the hub chart."""
    from kentender_procurement.demand_intake.api.dia_access import user_has_dia_workspace_access

    if not frappe.db.exists("DocType", "Demand"):
        return {"ok": False, "message": _("Demand DocType not installed."), "bars": [], "period_label": ""}

    if not user_has_dia_workspace_access():
        return {
            "ok": False,
            "message": _("You are not allowed to access Demand Intake."),
            "bars": [],
            "period_label": "",
        }

    if not frappe.has_permission("Demand", "read"):
        return {"ok": False, "message": _("No read permission on Demand."), "bars": [], "period_label": ""}

    active_in = ", ".join(f"'{s}'" for s in _ACTIVE_STATUSES)
    approved_in = ", ".join(f"'{s}'" for s in _APPROVED_STATUSES)

    rows = frappe.db.sql(
        f"""
        SELECT
            COALESCE(pd.department_name, d.requesting_department, 'Unknown') AS label,
            CAST(SUM(COALESCE(d.total_amount, 0)) AS DECIMAL(20,2))          AS total_value,
            CAST(SUM(
                CASE WHEN d.status IN ({approved_in})
                     THEN COALESCE(d.total_amount, 0)
                     ELSE 0
                END
            ) AS DECIMAL(20,2))                                               AS approved_value
        FROM `tabDemand` d
        LEFT JOIN `tabProcuring Department` pd ON pd.name = d.requesting_department
        WHERE d.status IN ({active_in})
          AND COALESCE(d.total_amount, 0) > 0
        GROUP BY d.requesting_department, pd.department_name
        ORDER BY total_value DESC
        LIMIT 5
        """,
        as_dict=True,
    )

    bars = [
        {
            "label":          str(r.label or "Unknown"),
            "total_value":    flt(r.total_value),
            "approved_value": flt(r.approved_value),
        }
        for r in rows
    ]

    return {
        "ok": True,
        "bars": bars,
        "period_label": _current_fy_label(),
    }
