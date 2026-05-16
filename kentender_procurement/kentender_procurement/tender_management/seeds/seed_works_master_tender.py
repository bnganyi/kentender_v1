# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-009 entry point — bench execute wrapper for the works master tender seed.

Usage::

    bench --site kentender.midas.com execute \
        kentender_procurement.tender_management.seeds.seed_works_master_tender.run
"""

from __future__ import annotations

from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
	upsert_works_master_tender,
)


def run() -> dict:
	return upsert_works_master_tender()
