# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master budget seed — neutralized by MVP-1 Budget preparatory teardown.

Constants are retained so lifecycle / planning / stable-platform importers keep
resolving. ``upsert_works_master_budget`` is a no-op skip.
"""

from __future__ import annotations

from typing import Any, Final

BUDGET_NAME: Final[str] = "BUDGET-MOH-2026"
BUDGET_TITLE: Final[str] = "Ministry of Health Budget FY 2026/2027"
FISCAL_YEAR: Final[int] = 2026

BUDGET_LINE_CODE: Final[str] = "BUD-MOH-INFRA-2026-001"
BUDGET_LINE_TITLE: Final[str] = "District Health Facility Infrastructure Rehabilitation"
BUDGET_LINE_NOTES: Final[str] = "Neutralized (mvp1-budget-teardown)."

AMOUNT_ALLOCATED: Final[float] = 120_000_000.0
AMOUNT_RESERVED: Final[float] = 98_000_000.0

FUNDING_SOURCE_TITLE: Final[str] = "Government of Kenya Development Budget"

PROGRAM_CODE: Final[str] = "PROG-MOH-INFRA"
OBJECTIVE_CODE: Final[str] = "OBJ-MOH-HOSP-RENOV"
TARGET_CODE: Final[str] = "TGT-MOH-HOSP-RENOV-2026"
PLAN_START_YEAR: Final[int] = 2026
PLAN_END_YEAR: Final[int] = 2030
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026\u20132030"

WORKS_SUB_PROGRAM_TITLE: Final[str] = "District health facility rehabilitation (WORKS seed)"


def resolve_procuring_entity_moh() -> str | None:
	return None


def _ensure_funding_source(*_args: Any, **_kwargs: Any) -> str | None:
	return None


def upsert_works_master_budget(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
	return {"ok": True, "skipped": True, "reason": "mvp1-budget-teardown"}
