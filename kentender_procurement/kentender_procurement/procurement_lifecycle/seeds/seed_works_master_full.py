# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Entry-point for R2-012 — WORKS master full seed with spec §20 summary output.

Usage::

    # Base checkpoint (default)
    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_full.run

    # Opening-ready checkpoint
    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_full.run \\
        --kwargs '{"checkpoint": "OPENING_READY"}'

    # Force reset of master PLC rows before re-seed
    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_full.run \\
        --kwargs '{"reset": True}'
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.procurement_lifecycle.seeds.works_master_full_seed import (
    run_works_master_full_seed,
)


def run(**kwargs: object) -> None:
    """Run the WORKS master full seed and print the spec §20 summary."""
    checkpoint = str(kwargs.get("checkpoint", "TENDER_PUBLISHED"))
    reset = bool(kwargs.get("reset", False))
    result = run_works_master_full_seed(checkpoint=checkpoint, reset=reset)
    frappe.db.commit()
    print(json.dumps(result, indent=2, default=str))
