# Copyright (c) 2026, KenTender and contributors
"""Removed in MVP-1 Strategy preparatory teardown.

Import path retained so works-master / stable seeds and tests do not ImportError.
No legacy hierarchy is created. Rebuild restores MOH-SP-2026-2030
(STRATEGY-MVP1-REQ-1.0 §19).
"""

from __future__ import annotations

from typing import Any, Final

# --- Canonical codes (kept as constants for import compatibility only) ---
STRATEGY_PLAN_CODE: Final[str] = "STRAT-MOH-2026"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026\u20132030"
START_YEAR: Final[int] = 2026
END_YEAR: Final[int] = 2030
PROGRAM_CODE: Final[str] = "PROG-MOH-INFRA"
PROGRAM_TITLE: Final[str] = "Healthcare Infrastructure Rehabilitation"
PROGRAM_DESCRIPTION: Final[str] = (
	"Rehabilitation and improvement of priority district health facilities to improve access and quality of care."
)
OBJECTIVE_CODE: Final[str] = "OBJ-MOH-HOSP-RENOV"
OBJECTIVE_TITLE: Final[str] = "Improve district hospital infrastructure readiness"
OBJECTIVE_DESCRIPTION: Final[str] = (
	"Renovate and restore critical district hospital facilities to support safe and continuous healthcare service delivery."
)
SUB_PROGRAM_CODE: Final[str] = "SUB-MOH-INFRA-001"
SUB_PROGRAM_TITLE: Final[str] = "District health facility rehabilitation"
TARGET_CODE: Final[str] = "TGT-MOH-HOSP-RENOV-2026"
TARGET_TITLE: Final[str] = "Renovate priority district hospital facilities in FY 2026/2027"
TARGET_METRIC_TEXT: Final[str] = "Number of priority district hospital renovation projects initiated"


def desk_visibility(procuring_entity_name: str) -> dict[str, str]:
	return {
		"procuring_entity": procuring_entity_name,
		"scope_rule": "MVP-1 Strategy teardown: strategy domain removed pending rebuild.",
		"optional_seed_fix": "",
	}


def resolve_procuring_entity_moh() -> str | None:
	import frappe

	for code in ("PE-MOH", "MOH"):
		name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if name:
			return name
	return None


def upsert_works_master_strategy_hierarchy(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {
		"ok": True,
		"skipped": True,
		"reason": "mvp1-strategy-teardown",
		"plan": None,
		"program": None,
		"sub_program": None,
		"objective": None,
		"target": None,
		"procuring_entity": resolve_procuring_entity_moh(),
	}
