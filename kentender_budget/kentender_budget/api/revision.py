# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt
"""Budget Revision lifecycle API — Budget Revision Process.md.

Workflow (combined Approved+Applied per product decision):
    Active → (request_revision) → new Draft revision
    Draft  → (submit_revision)  → Submitted
    Submitted → (return_revision)  → Draft (sent back for correction)
    Submitted → (approve_revision) → Active (revision), Revised (predecessor) — atomic
    Draft  → (cancel_revision)  → Cancelled
"""
from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import cint, flt, now_datetime


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_revision_or_throw(budget_name: str):
    if not budget_name:
        frappe.throw(_("Budget name is required."))
    doc = frappe.get_doc("Budget", budget_name)
    doc.check_permission("write")
    return doc


def _assert_is_revision(doc) -> None:
    """A revision must have a supersedes_budget link."""
    if not doc.get("supersedes_budget"):
        frappe.throw(
            _("This budget is not a revision (no predecessor linked)."),
            title=_("Not a revision"),
        )


# ── API ───────────────────────────────────────────────────────────────────────


@frappe.whitelist()
def request_revision(budget_name: str | None = None) -> dict:
    """Create a Draft revision Budget that supersedes the given Active budget.

    Copies all active Budget Lines to the new revision document.
    Returns the new revision's name.
    """
    if not budget_name:
        frappe.throw(_("Budget name is required."))

    predecessor = frappe.get_doc("Budget", budget_name)
    predecessor.check_permission("write")

    if predecessor.status not in ("Active",):
        frappe.throw(
            _("Only Active budgets can be revised. Current status: {0}.").format(predecessor.status),
            title=_("Cannot revise"),
        )

    # Build new revision document — copy scalar fields, reset lifecycle fields
    new_doc = frappe.new_doc("Budget")
    scalar_copy = [
        "budget_name", "procuring_entity", "fiscal_year",
        "currency", "effective_date", "closing_date", "budget_owner",
        "order_index", "is_current_version",
    ]
    for f in scalar_copy:
        new_doc.set(f, predecessor.get(f))

    new_doc.version_no = (cint(predecessor.version_no) or 1) + 1
    new_doc.supersedes_budget = predecessor.name
    new_doc.is_current_version = 1
    new_doc.status = "Draft"
    new_doc.total_budget_amount = flt(predecessor.total_budget_amount)
    # Clear lifecycle audit fields
    new_doc.submitted_by = None
    new_doc.submitted_at = None
    new_doc.approved_by = None
    new_doc.approved_at = None
    new_doc.rejection_reason = None
    new_doc.rejected_by = None
    new_doc.rejected_at = None
    new_doc.created_by = frappe.session.user
    new_doc.insert(ignore_permissions=False)

    # Copy active Budget Lines
    source_lines = frappe.get_all(
        "Budget Line",
        filters={"budget": predecessor.name, "is_active": 1},
        fields=[
            "budget_line_code", "budget_line_name", "amount_allocated",
            "funding_source",
            "department", "economic_classification", "notes", "line_status",
        ],
        limit=5000,
    )
    for src in source_lines:
        line = frappe.new_doc("Budget Line")
        line.budget = new_doc.name
        line.procuring_entity = new_doc.procuring_entity
        line.fiscal_year = new_doc.fiscal_year
        line.currency = new_doc.currency
        line.budget_line_name = src.budget_line_name
        line.budget_line_code = None  # cleared so autoname generates a new unique code
        line.amount_allocated = flt(src.amount_allocated)
        # Revision lines start with zero obligations — actual reservations/commitments
        # belong to the predecessor's lines; the revision represents planned changes only.
        line.amount_reserved = 0.0
        line.amount_committed = 0.0
        line.amount_consumed = 0.0
        line.funding_source = src.funding_source
        line.department = src.department
        line.economic_classification = src.economic_classification
        line.notes = src.notes or ""
        line.is_active = 1
        line.insert(ignore_permissions=True)

    frappe.db.commit()
    return {"name": new_doc.name, "version_no": new_doc.version_no}


@frappe.whitelist()
def submit_revision(budget_name: str | None = None) -> dict:
    """Draft revision → Submitted. Only revisions (supersedes_budget set) can use this path."""
    doc = _get_revision_or_throw(budget_name)
    _assert_is_revision(doc)
    if doc.status != "Draft":
        frappe.throw(_("Only Draft revisions can be submitted. Current status: {0}.").format(doc.status))
    doc.status = "Submitted"
    doc.submitted_by = frappe.session.user
    doc.submitted_at = now_datetime()
    doc.save()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def return_revision(budget_name: str | None = None, reason: str | None = None) -> dict:
    """Submitted revision → Draft (returned for correction)."""
    doc = _get_revision_or_throw(budget_name)
    _assert_is_revision(doc)
    if doc.status != "Submitted":
        frappe.throw(_("Only Submitted revisions can be returned. Current status: {0}.").format(doc.status))
    note = (reason or "").strip()
    doc.status = "Draft"
    doc.rejection_reason = note or None
    doc.rejected_by = frappe.session.user
    doc.rejected_at = now_datetime()
    doc.save()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def approve_revision(budget_name: str | None = None, justification: str | None = None) -> dict:
    """Approve a Submitted revision — atomic combined Approve+Apply.

    1. Revision: Submitted → Active (new baseline).
    2. Predecessor: Active → Revised, is_current_version = 0.
    3. Revision: is_current_version = 1, total_budget_amount = sum of active lines.
    """
    doc = _get_revision_or_throw(budget_name)
    _assert_is_revision(doc)
    if doc.status != "Submitted":
        frappe.throw(_("Only Submitted revisions can be approved. Current status: {0}.").format(doc.status))

    predecessor_name = doc.supersedes_budget

    # Validate: no line reduced below its obligations
    lines = frappe.get_all(
        "Budget Line",
        filters={"budget": doc.name, "is_active": 1},
        fields=["name", "amount_allocated", "amount_reserved", "amount_committed"],
        limit=5000,
    )
    for line in lines:
        alloc = flt(line.amount_allocated)
        floor = flt(line.amount_reserved) + flt(line.amount_committed)
        if alloc < floor - 1e-9:
            frappe.throw(
                _(
                    "Line '{0}': allocated amount ({1}) is below its obligations ({2}). "
                    "Release reservations or commitments before approving."
                ).format(line.name, alloc, floor),
                title=_("Revision Guard"),
            )

    allocated_sum = sum(flt(l.amount_allocated) for l in lines)

    # Promote revision to Active
    doc.status = "Active"
    doc.approved_by = frappe.session.user
    doc.approved_at = now_datetime()
    doc.total_budget_amount = allocated_sum
    doc.is_current_version = 1
    doc.save()

    # Lock predecessor
    frappe.db.set_value(
        "Budget",
        predecessor_name,
        {"status": "Revised", "is_current_version": 0},
        update_modified=True,
    )
    frappe.db.commit()
    return {"name": doc.name, "status": doc.status, "predecessor": predecessor_name}


@frappe.whitelist()
def cancel_revision(budget_name: str | None = None) -> dict:
    """Cancel a Draft revision — sets status to Cancelled.

    Blocked if any revision lines already carry active reservations or commitments.
    """
    doc = _get_revision_or_throw(budget_name)
    _assert_is_revision(doc)
    if doc.status != "Draft":
        frappe.throw(_("Only Draft revisions can be cancelled. Current status: {0}.").format(doc.status))

    # Block if revision lines have live Budget Reservation records (real financial obligations)
    rev_lines = frappe.get_all(
        "Budget Line",
        filters={"budget": doc.name, "is_active": 1},
        pluck="name",
        limit=5000,
    )
    if rev_lines:
        has_reservations = frappe.db.sql(
            """
            SELECT name
            FROM `tabBudget Reservation`
            WHERE budget_line IN %s
              AND status = 'Active'
            LIMIT 1
            """,
            (rev_lines,),
            as_dict=True,
        )
        if has_reservations:
            frappe.throw(
                _("This revision cannot be cancelled: one or more lines carry active reservations or commitments."),
                title=_("Cannot cancel"),
            )

    doc.status = "Cancelled"
    doc.save()
    return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_revision_diff(budget_name: str | None = None) -> dict:
    """Return a before/after comparison between a revision and its predecessor.

    Used by the workbench diff panel.
    """
    if not budget_name:
        frappe.throw(_("Budget name is required."))
    if not frappe.has_permission("Budget", "read", budget_name):
        frappe.throw(_("Not permitted."), frappe.PermissionError)

    revision = frappe.db.get_value(
        "Budget",
        budget_name,
        ["name", "supersedes_budget", "version_no", "total_budget_amount"],
        as_dict=True,
    )
    if not revision or not revision.supersedes_budget:
        return {"is_revision": False}

    predecessor_name = revision.supersedes_budget

    def _line_map(bname):
        rows = frappe.get_all(
            "Budget Line",
            filters={"budget": bname, "is_active": 1},
            fields=[
                "name", "budget_line_code", "budget_line_name",
                "amount_allocated", "amount_reserved", "amount_committed", "amount_available",
            ],
            limit=5000,
        )
        return {r.budget_line_code: r for r in rows}

    pred_lines = _line_map(predecessor_name)
    rev_lines  = _line_map(budget_name)

    all_codes = sorted(set(list(pred_lines.keys()) + list(rev_lines.keys())))
    line_diffs = []
    for code in all_codes:
        pred = pred_lines.get(code)
        rev  = rev_lines.get(code)
        change = flt(rev.amount_allocated if rev else 0) - flt(pred.amount_allocated if pred else 0)
        line_diffs.append({
            "budget_line_code": code,
            "budget_line_name": (rev or pred).budget_line_name,
            "before_allocated": flt(pred.amount_allocated) if pred else 0.0,
            "after_allocated":  flt(rev.amount_allocated)  if rev  else 0.0,
            "change":           change,
            "is_new":           pred is None,
            "is_removed":       rev  is None,
        })

    def _totals(bname):
        rows = frappe.get_all(
            "Budget Line",
            filters={"budget": bname, "is_active": 1},
            fields=["amount_allocated", "amount_reserved", "amount_committed", "amount_available"],
            limit=5000,
        )
        return {
            "allocated": sum(flt(r.amount_allocated) for r in rows),
            "reserved":  sum(flt(r.amount_reserved)  for r in rows),
            "committed": sum(flt(r.amount_committed)  for r in rows),
            "available": sum(flt(r.amount_available)  for r in rows),
        }

    return {
        "is_revision": True,
        "predecessor_name": predecessor_name,
        "version_no": cint(revision.version_no),
        "predecessor": _totals(predecessor_name),
        "revision":    _totals(budget_name),
        "line_diffs":  line_diffs,
    }

