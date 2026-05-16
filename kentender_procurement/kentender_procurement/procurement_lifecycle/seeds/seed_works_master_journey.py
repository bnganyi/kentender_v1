# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-010 entry point — bench execute wrapper for the works master journey seed.

Usage::

    bench --site kentender.midas.com execute \
        kentender_procurement.procurement_lifecycle.seeds.seed_works_master_journey.run
"""

from __future__ import annotations

from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import (
	upsert_works_master_journey,
)


def run() -> dict:
	return upsert_works_master_journey()
