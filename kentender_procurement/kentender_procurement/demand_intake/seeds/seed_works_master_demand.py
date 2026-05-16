# Copyright (c) 2026, KenTender and contributors
# License: MIT. See LICENSE
"""Bench execute entry point for R2-006 WORKS master demand seed.

Usage::

    bench --site kentender.midas.com execute \\
        kentender_procurement.demand_intake.seeds.seed_works_master_demand.run
"""

from __future__ import annotations

import frappe

from kentender_procurement.demand_intake.seeds.works_master_demand_seed import (
    upsert_works_master_demand,
)


def run() -> dict:
    """Idempotent: create/verify DEM-MOH-2026-001 and return result summary."""
    result = upsert_works_master_demand()
    frappe.db.commit()
    return result
