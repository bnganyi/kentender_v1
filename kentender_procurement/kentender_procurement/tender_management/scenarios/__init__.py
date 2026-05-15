# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""P12 — TM2 Works seed scenarios (doc 7 §2) and harness entrypoints."""

from kentender_procurement.tender_management.scenarios.tm2_works_scenarios import (
	TM2WorksScenarioSpec,
	iter_tm2_works_scenario_codes,
	scenario_by_code,
	scenario_tracker_slug,
	tm2_works_scenarios,
)

__all__ = (
	"TM2WorksScenarioSpec",
	"iter_tm2_works_scenario_codes",
	"scenario_by_code",
	"scenario_tracker_slug",
	"tm2_works_scenarios",
)
