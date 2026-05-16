# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Entry-point for R2-013 — WORKS master seed conflict report.

Usage::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_conflict_report.run
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.procurement_lifecycle.seeds.works_master_conflict_report import (
    generate_works_master_conflict_report,
)


def run(**_kwargs: object) -> None:
    """Generate and print the R2-013 conflict report."""
    report = generate_works_master_conflict_report()

    # Print a compact version without the full non_master_seed_registry for readability
    compact = {k: v for k, v in report.items() if k != "non_master_seed_registry"}
    compact["non_master_seed_registry_count"] = len(report.get("non_master_seed_registry", []))
    compact["non_master_seed_ids"] = [r["seed_id"] for r in report.get("non_master_seed_registry", [])]

    print(json.dumps(compact, indent=2, default=str))

    if not report["ok"]:
        print("\n--- CRITICAL CONFLICTS DETECTED — STOP FOR APPROVAL ---")
        for c in report["critical_conflicts"]:
            print(f"  [{c['check_id']}] {c['message']}")
