# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable platform seed — load, clear, and validate entry points.

Load (idempotent upsert)::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_stable_platform.run

Reset then reload::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_stable_platform.run \\
        --kwargs '{"reset": true}'

Load with a different PP2 checkpoint::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_stable_platform.run \\
        --kwargs '{"reset": true, "planning_checkpoint": "RELEASED_TO_TENDER"}'

Validate only::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_stable_platform.validate

Clear only (no reload)::

    bench --site kentender.midas.com execute kentender_core.seeds.clear_stable_platform.run
"""

from __future__ import annotations

import json

import frappe

from kentender_core.seeds.stable_platform_seed.clear import clear_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.load import load_stable_platform_seed
from kentender_core.seeds.stable_platform_seed.validate import validate_stable_platform_seed


def run(**kwargs: object) -> None:
	"""Load the stable platform seed pack and print JSON summary."""
	reset = bool(kwargs.get("reset", False))
	planning_checkpoint = str(kwargs.get("planning_checkpoint", "PACKAGE_DRAFT"))
	import_it_std = bool(kwargs.get("import_it_std", True))
	include_it_supplement = bool(kwargs.get("include_it_supplement", True))
	purge_non_master = bool(kwargs.get("purge_non_master", False))

	result = load_stable_platform_seed(
		reset=reset,
		planning_checkpoint=planning_checkpoint,
		import_it_std=import_it_std,
		include_it_supplement=include_it_supplement,
		purge_non_master=purge_non_master,
	)
	if result.get("ok"):
		validation = validate_stable_platform_seed(
			planning_checkpoint=planning_checkpoint,
			expect_it_std=import_it_std,
			expect_it_supplement=include_it_supplement,
		)
		result["validation"] = validation
		frappe.db.commit()
	print(json.dumps(result, indent=2, default=str))


def validate(**kwargs: object) -> None:
	"""Validate stable platform seed without loading."""
	planning_checkpoint = kwargs.get("planning_checkpoint")
	result = validate_stable_platform_seed(
		planning_checkpoint=str(planning_checkpoint) if planning_checkpoint else None,
		expect_it_std=bool(kwargs.get("expect_it_std", True)),
		expect_it_supplement=bool(kwargs.get("expect_it_supplement", True)),
	)
	print(json.dumps(result, indent=2, default=str))
