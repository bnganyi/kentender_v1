# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create Demand Wizard — save_demand_draft API.

Supports the 4-step Create Demand wizard by providing a single endpoint that:
  - Creates a new Draft Demand on Step 1 → Step 2 transition.
  - Updates the Draft's items on Step 2 → Step 3 transition.

Both create and update paths go through this function; callers pass
`demand_name` only when updating an existing draft.
"""

from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import today

from kentender_procurement.demand_intake.api.dia_access import require_dia_workspace_user


def _parse_items(items_json: str | None, requisition_type: str | None) -> list[dict]:
    """Parse JSON item rows from the wizard into Demand Item dicts."""
    if not items_json:
        return []
    try:
        rows = json.loads(items_json)
    except (json.JSONDecodeError, TypeError):
        frappe.throw(_("Invalid items format."))
    result = []
    for row in rows:
        desc = (row.get("desc") or row.get("item_description") or "").strip()
        if not desc:
            continue
        result.append(
            {
                "item_description": desc,
                "quantity": float(row.get("qty") or row.get("quantity") or 0),
                "estimated_unit_cost": float(
                    row.get("unit_price") or row.get("estimated_unit_cost") or 0
                ),
                "uom": row.get("uom") or "Units",
                "category": row.get("category") or requisition_type or "",
            }
        )
    return result


@frappe.whitelist()
def save_demand_draft(
    title: str | None = None,
    requesting_department: str | None = None,
    requisition_type: str | None = None,
    procuring_entity: str | None = None,
    required_by_date: str | None = None,
    priority_level: str | None = None,
    beneficiary_summary: str | None = None,
    items: str | None = None,
    demand_name: str | None = None,
) -> dict:
    """Create (or update) a Draft Demand from the Create Demand wizard.

    Returns:
        { ok: True, demand_name: str, demand_id: str | None }

    Raises:
        frappe.ValidationError — title missing, or demand not in Draft status.
        frappe.PermissionError — caller lacks DIA workspace access or write permission.
    """
    require_dia_workspace_user()

    demand_name = (demand_name or "").strip() or None

    if demand_name:
        return _update_existing_draft(
            demand_name=demand_name,
            title=title,
            requesting_department=requesting_department,
            requisition_type=requisition_type,
            procuring_entity=procuring_entity,
            required_by_date=required_by_date,
            priority_level=priority_level,
            beneficiary_summary=beneficiary_summary,
            items=items,
        )

    # New demand creation path
    title_clean = (title or "").strip()
    if not title_clean:
        frappe.throw(_("Title is required."), frappe.ValidationError)

    if not frappe.has_permission("Demand", "create"):
        frappe.throw(_("You do not have permission to create a Demand."), frappe.PermissionError)

    doc = frappe.new_doc("Demand")
    doc.title = title_clean
    if requesting_department:
        doc.requesting_department = requesting_department
    if requisition_type:
        doc.requisition_type = requisition_type
    if procuring_entity:
        doc.procuring_entity = procuring_entity
    if required_by_date:
        doc.required_by_date = required_by_date
    if priority_level:
        doc.priority_level = priority_level
    if beneficiary_summary:
        doc.beneficiary_summary = beneficiary_summary
        # Single wizard justification field covers both summary fields
        if not doc.specification_summary:
            doc.specification_summary = beneficiary_summary
    if not doc.request_date:
        doc.request_date = today()

    parsed_items = _parse_items(items, requisition_type or doc.requisition_type)
    for item_data in parsed_items:
        doc.append("items", item_data)

    doc.insert(ignore_permissions=True)

    return {
        "ok": True,
        "demand_name": doc.name,
        "demand_id": doc.demand_id or None,
    }


def _update_existing_draft(
    demand_name: str,
    title: str | None,
    requesting_department: str | None,
    requisition_type: str | None,
    procuring_entity: str | None,
    required_by_date: str | None,
    priority_level: str | None,
    beneficiary_summary: str | None,
    items: str | None,
) -> dict:
    """Update scalar fields and/or items on an existing Draft demand."""
    if not frappe.db.exists("Demand", demand_name):
        frappe.throw(_("Demand {0} not found.").format(demand_name))

    if not frappe.has_permission("Demand", "write", doc=demand_name):
        frappe.throw(_("You do not have permission to update this demand."), frappe.PermissionError)

    doc = frappe.get_doc("Demand", demand_name)

    if doc.status not in ("Draft", "Rejected"):
        frappe.throw(
            _("Only Draft or Rejected demands can be updated through the wizard."),
            frappe.ValidationError,
        )

    if title is not None:
        title_clean = title.strip()
        if not title_clean:
            frappe.throw(_("Title is required."), frappe.ValidationError)
        doc.title = title_clean

    if requesting_department is not None:
        doc.requesting_department = requesting_department
    if requisition_type is not None:
        doc.requisition_type = requisition_type
    if procuring_entity is not None:
        doc.procuring_entity = procuring_entity
    if required_by_date is not None:
        doc.required_by_date = required_by_date
    if priority_level is not None:
        doc.priority_level = priority_level
    if beneficiary_summary is not None:
        doc.beneficiary_summary = beneficiary_summary
        # Single wizard justification field satisfies both summary checks
        if beneficiary_summary and not doc.specification_summary:
            doc.specification_summary = beneficiary_summary

    if items is not None:
        parsed_items = _parse_items(items, requisition_type or doc.requisition_type)
        doc.set("items", [])
        for item_data in parsed_items:
            doc.append("items", item_data)

    doc.save(ignore_permissions=True)

    return {
        "ok": True,
        "demand_name": doc.name,
        "demand_id": doc.demand_id or None,
    }
