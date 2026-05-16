# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-005 — WORKS master budget seed (spec §9). Public ``bench execute`` entry.

Creates / refreshes:

* **Budget** ``BUDGET-MOH-2026`` — "Ministry of Health Budget FY 2026/2027"
* **Budget Line** ``BUD-MOH-INFRA-2026-001`` — "District Health Facility
  Infrastructure Rehabilitation" (120 000 000 KES allocated, 98 000 000 reserved)

Run::

    bench --site kentender.midas.com execute \\
      kentender_budget.seeds.seed_works_master_budget.run

Prerequisites: ``PE-MOH`` procuring entity (LV-R2-001-03) and the §8 strategy
hierarchy (R2-004 / LV-R2-001-04) must exist first.
"""

from __future__ import annotations

from typing import Any

from kentender_budget.seeds.works_master_budget_seed import upsert_works_master_budget


def run() -> dict[str, Any]:
    """Upsert BUDGET-MOH-2026 and BUD-MOH-INFRA-2026-001 per WORKS master seed spec §9."""
    return upsert_works_master_budget()
