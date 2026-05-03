# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""seed_strategy_empty — same as core minimal: no Strategic Plans (empty Strategy workspace)."""

from __future__ import annotations

from kentender_core.seeds.seed_core_minimal import run as run_core


def run():
	return run_core()
