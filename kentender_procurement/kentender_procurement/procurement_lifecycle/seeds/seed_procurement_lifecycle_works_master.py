# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master seed — public ``bench execute`` entry (R2-001 / seed spec §19.1).

Run::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.load_procurement_lifecycle_works_master \\
	  --kwargs '{"reset": true, "checkpoint": "TENDER_PUBLISHED"}'

Validate (R2-003 / §21)::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.validate_procurement_lifecycle_works_master_seed \\
	  --kwargs '{"checkpoint": "TENDER_PUBLISHED"}'

To drop **test-only** PLC rows that are not in G0-008 §4.1–4.2 (before re-seeding), see
``purge_plc_outside_works_master_registry.purge_procurement_lifecycle_plc_outside_works_master_registry``.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import run_load
from kentender_procurement.procurement_lifecycle.seeds.works_master_seed_validate import run_validate


def load_procurement_lifecycle_works_master(
	reset: bool = False,
	checkpoint: str = "TENDER_PUBLISHED",
) -> dict[str, Any]:
	"""Load WORKS master PLC seed (journey + steps + handoffs). See ``works_master_loader.run_load``."""
	return run_load(reset=reset, checkpoint=checkpoint)


def validate_procurement_lifecycle_works_master_seed(
	checkpoint: str = "TENDER_PUBLISHED",
) -> dict[str, Any]:
	"""Validate WORKS master seed (§21). See ``works_master_seed_validate.run_validate``."""
	return run_validate(checkpoint=checkpoint)
