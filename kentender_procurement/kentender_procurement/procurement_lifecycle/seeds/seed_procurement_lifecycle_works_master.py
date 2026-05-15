# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master seed — public ``bench execute`` entry (R2-001 / seed spec §19.1).

Run::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master.load_procurement_lifecycle_works_master \\
	  --kwargs '{"reset": true, "checkpoint": "TENDER_PUBLISHED"}'
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.procurement_lifecycle.seeds.works_master_loader import run_load


def load_procurement_lifecycle_works_master(
	reset: bool = False,
	checkpoint: str = "TENDER_PUBLISHED",
) -> dict[str, Any]:
	"""Load WORKS master PLC seed (journey + steps + handoffs). See ``works_master_loader.run_load``."""
	return run_load(reset=reset, checkpoint=checkpoint)
