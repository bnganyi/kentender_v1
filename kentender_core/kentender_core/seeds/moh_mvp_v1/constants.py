# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixture constants — KenTender_MVP_Canonical_Demo_Data_Contract v1.1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Final

FIXTURE_NS: Final[str] = "MOH_MVP_V1"

# Fixed fixture clock (Africa/Nairobi +03:00).
FIXTURE_TZ = timezone(timedelta(hours=3))
FIXTURE_NOW: Final[datetime] = datetime(2027, 11, 3, 12, 0, 0, tzinfo=FIXTURE_TZ)
FIXTURE_NOW_STR: Final[str] = "2027-11-03 12:00:00"
FIXTURE_DATE: Final[str] = "2027-11-03"

# Days after which finance snapshots are Stale (seed configures/reads this).
FINANCE_FRESHNESS_DAYS: Final[int] = 1

PE_MOH: Final[str] = "PE-MOH"
PE_MOH_NAME: Final[str] = "Ministry of Health"
PE_MOE: Final[str] = "PE-MOE"
PE_MOE_NAME: Final[str] = "Ministry of Education"

# State Departments / Directorates (Procuring Department.department_code)
SD_MEDICAL: Final[str] = "MOH-SDMS"
SD_MEDICAL_NAME: Final[str] = "State Department for Medical Services"
SD_PUBLIC: Final[str] = "MOH-SDPHPS"
SD_PUBLIC_NAME: Final[str] = (
	"State Department for Public Health and Professional Standards"
)
DIR_DHP: Final[str] = "MOH-DIR-DHP"
DIR_DHP_NAME: Final[str] = "Directorate of Digital Health and Policy"
DIR_HRMD: Final[str] = "MOH-DIR-HRMD"
DIR_HRMD_NAME: Final[str] = "Human Resources Management and Development"

# Strategy
PLAN_CODE: Final[str] = "MOH-SP-2026-2030"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026–2030"
PROG_DH: Final[str] = "MOH-PROG-DH"
SUB_HIS: Final[str] = "MOH-SUB-HIS"
OUT_RELIABILITY: Final[str] = "MOH-OUT-RELIABILITY"
IND_AVAIL: Final[str] = "MOH-IND-AVAIL-01"
IND_RESTORE: Final[str] = "MOH-IND-RESTORE-01"
TGT_AVAIL_2028: Final[str] = "MOH-TGT-AVAIL-2028"
TGT_RESTORE_2028: Final[str] = "MOH-TGT-RESTORE-2028"
TGT_AVAIL_2029: Final[str] = "MOH-TGT-AVAIL-2029"
TGT_RESTORE_2029: Final[str] = "MOH-TGT-RESTORE-2029"
SUB_DHC: Final[str] = "MOH-SUB-DHC"
OUT_CAPABILITY: Final[str] = "MOH-OUT-CAPABILITY"
IND_SKILLS: Final[str] = "MOH-IND-SKILLS-01"
TGT_SKILLS_2029: Final[str] = "MOH-TGT-SKILLS-2029"
TGT_SKILLS_2030: Final[str] = "MOH-TGT-SKILLS-2030"

# Budget
BUD_ACTIVE: Final[str] = "MOH-BUD-2027-2028"
BUD_DRAFT: Final[str] = "MOH-BUD-2028-2029"
BUD_CLOSED: Final[str] = "MOH-BUD-2026-2027"
BL_DHI_2027: Final[str] = "MOH-BL-DHI-2027"
BL_HWD_2027: Final[str] = "MOH-BL-HWD-2027"
BL_DHI_2028: Final[str] = "MOH-BL-DHI-2028"
BL_HWD_2028: Final[str] = "MOH-BL-HWD-2028"
RSV_CODE: Final[str] = "RSV-MOH-0001"
COM_CODE: Final[str] = "COM-MOH-2027-005"
EXP_CODE: Final[str] = "EXP-MOH-2027-005-01"
DEMAND_CODE: Final[str] = "DMD-MOH-2027-014"
CONTRACT_CODE: Final[str] = "CTR-MOH-2027-005"
PLAN_ITEM_CODE: Final[str] = "PPI-MOH-2027-021"
TENDER_CODE: Final[str] = "TND-MOH-2027-008"

# §4.4 users
USER_MEDICAL: Final[str] = "moh.medicalservices.officer@example.test"
USER_PUBLIC: Final[str] = "moh.publichealth.officer@example.test"
USER_STR_REVIEWER: Final[str] = "moh.strategy.reviewer@example.test"
USER_BUD_REVIEWER: Final[str] = "moh.budget.reviewer@example.test"
USER_BUD_AUTHORITY: Final[str] = "moh.budget.authority@example.test"
USER_VIEWER: Final[str] = "moh.viewer@example.test"
USER_OTHER_ENTITY: Final[str] = "other.entity.officer@example.test"
USER_BUD_DUAL: Final[str] = "moh.budget.officer.authority@example.test"

CANONICAL_USERS: Final[tuple[str, ...]] = (
	USER_MEDICAL,
	USER_PUBLIC,
	USER_STR_REVIEWER,
	USER_BUD_REVIEWER,
	USER_BUD_AUTHORITY,
	USER_VIEWER,
	USER_OTHER_ENTITY,
	USER_BUD_DUAL,
)

# Prior Strategy/Budget matrix personas retired from demo keep-set.
RETIRED_DEMO_USERS: Final[tuple[str, ...]] = (
	"strategy.viewer@moh.test",
	"strategy.officer@moh.test",
	"strategy.reviewer@moh.test",
	"strategy.viewer@moe.test",
	"budget.viewer@moh.test",
	"budget.officer@moh.test",
	"budget.reviewer@moh.test",
	"budget.authority@moh.test",
	"budget.officer.authority@moh.test",
	"budget.officer@moe.test",
)


def fixture_datetime_offset_days(days: int) -> str:
	"""Return MySQL-friendly datetime string relative to fixture clock."""
	dt = FIXTURE_NOW + timedelta(days=days)
	return dt.strftime("%Y-%m-%d %H:%M:%S")


def fixture_date_offset_days(days: int) -> str:
	dt = FIXTURE_NOW + timedelta(days=days)
	return dt.strftime("%Y-%m-%d")
