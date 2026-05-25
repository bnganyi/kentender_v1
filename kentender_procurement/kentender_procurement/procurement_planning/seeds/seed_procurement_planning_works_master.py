# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P3-001 — PP2 WORKS master planning seed public API (implementation pack §6).

Run::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master \\
        --kwargs '{"checkpoint": "CONSUMED_BY_TENDER", "force_reset": true}'
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	DEFAULT_CHECKPOINT,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	run_load,
)


def seed_procurement_planning_works_master(
	checkpoint: str = DEFAULT_CHECKPOINT,
	force_reset: bool = False,
) -> dict[str, Any]:
	"""Load WORKS master planning seed at the requested checkpoint."""
	return run_load(checkpoint=checkpoint, force_reset=force_reset)


def validate_procurement_planning_works_master_seed(
	checkpoint: str = DEFAULT_CHECKPOINT,
) -> dict[str, Any]:
	"""Validate WORKS master planning seed (spec §21). See ``works_master_pp2_seed.validate.run_validate``."""
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.validate import (
		run_validate,
	)

	return run_validate(checkpoint=checkpoint)


def clear_procurement_planning_works_master_seed() -> dict[str, Any]:
	"""Development/test reset for PP2 master planning seed (spec §24, P3-003)."""
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.clear import (
		run_clear,
	)

	return run_clear()


def load_procurement_planning_negative_fixture(fixture_code: str) -> dict[str, Any]:
	"""Load isolated NEG-PP2 negative fixture preconditions (spec §22, P3-016)."""
	from kentender_procurement.procurement_planning.seeds.negative_fixtures.loader import (
		run_load,
	)

	return run_load(fixture_code=fixture_code)


def clear_procurement_planning_negative_fixture(fixture_code: str) -> dict[str, Any]:
	"""Development/test teardown for a NEG-PP2 negative fixture (spec §24, P3-016)."""
	from kentender_procurement.procurement_planning.seeds.negative_fixtures.clear import (
		run_clear,
	)

	return run_clear(fixture_code=fixture_code)


def validate_procurement_planning_negative_fixture(fixture_code: str) -> dict[str, Any]:
	"""Validate NEG-PP2 negative fixture blocker proof (spec §22, P3-017)."""
	from kentender_procurement.procurement_planning.seeds.negative_fixtures.validate import (
		run_validate,
	)

	return run_validate(fixture_code=fixture_code)
