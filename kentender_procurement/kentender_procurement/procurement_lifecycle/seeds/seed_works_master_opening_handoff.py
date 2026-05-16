# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Entry-point for R2-011A optional opening handoff seed.

Usage::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_opening_handoff.run
"""

from __future__ import annotations

import json

import frappe

from kentender_procurement.procurement_lifecycle.seeds.works_master_opening_handoff_seed import (
	upsert_works_master_opening_handoff_cards,
)


def run(**kwargs: object) -> None:
	"""Create/update CLOSECERT and OPENREADY handoff cards (spec §16.9–16.10)."""
	reset = bool(kwargs.get("reset", False))
	result = upsert_works_master_opening_handoff_cards(reset=reset)
	frappe.db.commit()
	print(json.dumps(result, indent=2, default=str))
