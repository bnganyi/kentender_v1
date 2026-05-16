# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-011 entry point — bench execute wrapper for the works master handoff seed.

Usage::

    bench --site kentender.midas.com execute \
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_handoff.run
"""

from __future__ import annotations

from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_seed import (
	upsert_works_master_handoff_cards,
)


def run() -> dict:
	return upsert_works_master_handoff_cards()
