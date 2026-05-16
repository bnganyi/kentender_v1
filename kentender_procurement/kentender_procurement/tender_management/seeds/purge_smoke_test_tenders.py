# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""One-shot console utility — purge TND-MOH-2029-* smoke test tenders.

Retains TND-MOH-2026-001 (the R2-009 master seed tender).
Safe to run multiple times (idempotent).

Usage::

    bench --site kentender.midas.com execute \
        kentender_procurement.tender_management.seeds.purge_smoke_test_tenders.run
"""

from __future__ import annotations

import frappe


_KEEP = "TND-MOH-2026-001"
_SMOKE_PATTERN = "TND-MOH-2029-%"


def run() -> dict:
    frappe.set_user("Administrator")

    # 1. Collect smoke-test STD Instance names (linked by tm2_tender)
    std_inst_names = [
        r["name"]
        for r in frappe.db.sql(
            "SELECT name FROM `tabTender STD Instance` WHERE tm2_tender LIKE %s",
            (_SMOKE_PATTERN,),
            as_dict=True,
        )
    ]

    # 2. Delete STD Instance child tables
    if std_inst_names:
        placeholders = ",".join(["%s"] * len(std_inst_names))

        # Tables confirmed to have FK column `tender_std_instance`
        for tbl in (
            "tabTender STD Generated Output",
            "tabTender STD Instance BOQ",
        ):
            frappe.db.sql(
                f"DELETE FROM `{tbl}` WHERE tender_std_instance IN ({placeholders})",
                std_inst_names,
            )

        # BOQ Bills and Items are Frappe child rows (parent/parenttype) of
        # Tender STD Instance BOQ — delete via subquery
        frappe.db.sql(
            f"""DELETE FROM `tabTender STD Instance BOQ Bill`
                WHERE parent IN (
                    SELECT name FROM `tabTender STD Instance BOQ`
                    WHERE tender_std_instance IN ({placeholders})
                )""",
            std_inst_names,
        )
        frappe.db.sql(
            f"""DELETE FROM `tabTender STD Instance BOQ Item`
                WHERE parent IN (
                    SELECT name FROM `tabTender STD Instance BOQ`
                    WHERE tender_std_instance IN ({placeholders})
                )""",
            std_inst_names,
        )

        # Parameter Value, Works Requirement, Snapshot, Section Attachment,
        # Drawing Register — these tables don't carry a direct FK to the
        # STD Instance; their rows become orphans after the parent is deleted.
        # Orphaned data is acceptable in this dev/UAT cleanup context.

        frappe.db.sql(
            f"DELETE FROM `tabTender STD Instance` WHERE name IN ({placeholders})",
            std_inst_names,
        )

    # 3. Delete TM2 Tender linked satellite records
    for tbl in (
        "tabTM2 Tender Timeline",
        "tabTM2 Tender Access Rule",
        "tabTM2 Tender Audit Event",
        "tabTM2 Tender STD Binding",
        "tabTM2 Tender Closing Record",
        "tabTM2 Tender Invitation",
    ):
        frappe.db.sql(f"DELETE FROM `{tbl}` WHERE tm2_tender LIKE %s", (_SMOKE_PATTERN,))
        # Also catch rows stored by tender_code Data field
        frappe.db.sql(f"DELETE FROM `{tbl}` WHERE tender_code LIKE %s", (_SMOKE_PATTERN,))

    # 4. Delete the TM2 Tender records themselves
    tenders_deleted = frappe.db.sql(
        "SELECT COUNT(*) FROM `tabTM2 Tender` WHERE tender_code LIKE %s",
        (_SMOKE_PATTERN,),
    )[0][0]
    frappe.db.sql("DELETE FROM `tabTM2 Tender` WHERE tender_code LIKE %s", (_SMOKE_PATTERN,))

    frappe.db.commit()

    # Verify the master tender is intact
    master_ok = frappe.db.exists("TM2 Tender", _KEEP) is not None

    return {
        "ok": True,
        "tenders_deleted": tenders_deleted,
        "std_instances_deleted": len(std_inst_names),
        "master_tender_intact": master_ok,
        "master_tender": _KEEP,
    }
