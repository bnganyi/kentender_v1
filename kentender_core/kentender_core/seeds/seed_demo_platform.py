# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demo platform seed — bench execute entry points.

Load / reset::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_demo_platform.run \\
        --kwargs '{"reset": true}'

Validate only::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_demo_platform.validate

Transition probes::

    bench --site kentender.midas.com execute kentender_core.seeds.seed_demo_platform.probe_transitions
"""

from __future__ import annotations

import json

import frappe

from kentender_core.seeds.demo_platform_seed.clear import clear_demo_platform
from kentender_core.seeds.demo_platform_seed.constants import DEFAULT_PLANNING_CHECKPOINT
from kentender_core.seeds.demo_platform_seed.load import load_demo_platform_seed
from kentender_core.seeds.demo_platform_seed.transitions import probe_demo_platform_transitions
from kentender_core.seeds.demo_platform_seed.validate import validate_demo_platform_seed


def run(**kwargs: object) -> None:
	"""Load the demo platform seed and print JSON summary."""
	reset = bool(kwargs.get("reset", True))
	planning_checkpoint = str(
		kwargs.get("planning_checkpoint", DEFAULT_PLANNING_CHECKPOINT)
	)
	import_it_std = bool(kwargs.get("import_it_std", True))
	result = load_demo_platform_seed(
		reset=reset,
		planning_checkpoint=planning_checkpoint,
		import_it_std=import_it_std,
	)
	if result.get("ok"):
		result["transitions"] = probe_demo_platform_transitions(mutate=False)
	print(json.dumps(result, indent=2, default=str))


def validate(**kwargs: object) -> None:
	"""Validate demo platform without loading."""
	_ = kwargs
	print(json.dumps(validate_demo_platform_seed(), indent=2, default=str))


def clear(**kwargs: object) -> None:
	"""Clear demo + stable platform rows (no reload)."""
	clear_it_std = bool(kwargs.get("clear_it_std", False))
	print(
		json.dumps(
			clear_demo_platform(clear_stable=True, clear_it_std=clear_it_std),
			indent=2,
			default=str,
		)
	)


def probe_transitions(**kwargs: object) -> None:
	"""Run transition smoke probes."""
	mutate = bool(kwargs.get("mutate", False))
	print(json.dumps(probe_demo_platform_transitions(mutate=mutate), indent=2, default=str))
