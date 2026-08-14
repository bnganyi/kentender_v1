# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared fixture constants — KenTender MVP Canonical Demo Data Contract v2.0."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Final

FIXTURE_NS: Final[str] = "KENTENDER_MVP_V1"
# Legacy namespace still purged on clear for one migration cycle.
LEGACY_FIXTURE_NS: Final[str] = "MOH_MVP_V1"
PLAYWRIGHT_FIXTURE_NS: Final[str] = "KENTENDER_PLAYWRIGHT"

FIXTURE_TZ = timezone(timedelta(hours=3))
FIXTURE_NOW: Final[datetime] = datetime(2027, 11, 5, 12, 0, 0, tzinfo=FIXTURE_TZ)
FIXTURE_NOW_STR: Final[str] = "2027-11-05 12:00:00"
FIXTURE_DATE: Final[str] = "2027-11-05"
FINANCE_FRESHNESS_DAYS: Final[int] = 1

PE_MOH: Final[str] = "PE-MOH"
PE_MOH_NAME: Final[str] = "Ministry of Health"
PE_CGKIS: Final[str] = "PE-CGKIS"
PE_CGKIS_NAME: Final[str] = "County Government of Kisumu"
# Kept for transitional denial tests / shims.
PE_MOE: Final[str] = "PE-MOE"
PE_MOE_NAME: Final[str] = "Ministry of Education"

OUT_STATE_DEPT: Final[str] = "OUT-STATE-DEPT"
OUT_DIRECTORATE: Final[str] = "OUT-DIRECTORATE"
OUT_COUNTY_DEPT: Final[str] = "OUT-COUNTY-DEPT"

OU_SDMS: Final[str] = "MOH-SDMS"
OU_SDMS_NAME: Final[str] = "State Department for Medical Services"
OU_DIR_DHP: Final[str] = "MOH-DIR-DHP"
OU_DIR_DHP_NAME: Final[str] = "Directorate of Digital Health and Policy"
OU_SDPHPS: Final[str] = "MOH-SDPHPS"
OU_SDPHPS_NAME: Final[str] = (
	"State Department for Public Health and Professional Standards"
)
OU_DIR_HRMD: Final[str] = "MOH-DIR-HRMD"
OU_DIR_HRMD_NAME: Final[str] = "Human Resources Management and Development"
OU_CGK_HEALTH: Final[str] = "CGK-DEPT-HEALTH"
OU_CGK_HEALTH_NAME: Final[str] = "Medical Services, Public Health and Sanitation"

# Aliases used by older call sites during migration.
SD_MEDICAL = OU_SDMS
SD_PUBLIC = OU_SDPHPS
DIR_DHP = OU_DIR_DHP
DIR_HRMD = OU_DIR_HRMD
SD_MEDICAL_NAME = OU_SDMS_NAME
SD_PUBLIC_NAME = OU_SDPHPS_NAME
DIR_DHP_NAME = OU_DIR_DHP_NAME
DIR_HRMD_NAME = OU_DIR_HRMD_NAME

PLAN_CODE: Final[str] = "MOH-SP-2026-2030"
PLAN_TITLE: Final[str] = "Ministry of Health Strategic Plan 2026–2030"
CGK_PLAN_CODE: Final[str] = "CGK-SP-HEALTH-2027-2028"
CGK_PLAN_TITLE: Final[str] = "Kisumu County Health Services Operational Plan FY 2027/28"

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

CGK_OUT_COLDCHAIN: Final[str] = "CGK-OUT-COLDCHAIN"
CGK_IND_COLDCHAIN: Final[str] = "CGK-IND-COLDCHAIN-01"
CGK_TGT_COLDCHAIN: Final[str] = "CGK-TGT-COLDCHAIN-2028"

BUD_ACTIVE: Final[str] = "MOH-BUD-2027-2028"
BUD_DRAFT: Final[str] = "MOH-BUD-2028-2029"
BUD_CLOSED: Final[str] = "MOH-BUD-2026-2027"
BL_DHI_2027: Final[str] = "MOH-BL-DHI-2027"
BL_HWD_2027: Final[str] = "MOH-BL-HWD-2027"
BL_DHI_2028: Final[str] = "MOH-BL-DHI-2028"
BL_HWD_2028: Final[str] = "MOH-BL-HWD-2028"
CGK_BUD_ACTIVE: Final[str] = "CGK-BUD-2027-2028"
CGK_BL_COLDCHAIN: Final[str] = "CGK-BL-COLDCHAIN-2027"

RSV_CODE: Final[str] = "RSV-MOH-0001"
COM_CODE: Final[str] = "COM-MOH-2027-005"
EXP_CODE: Final[str] = "EXP-MOH-2027-005-01"
DEMAND_CODE: Final[str] = "DMD-MOH-2027-014"
DEMAND_CODE_RETURNED: Final[str] = "DMD-MOH-2027-019"
DEMAND_CODE_COUNTY: Final[str] = "DMD-CGK-2027-006"
CONTRACT_CODE: Final[str] = "CTR-MOH-2027-005"
PROCUREMENT_PLAN_CODE: Final[str] = "PLN-MOH-2027-001"
PROCUREMENT_PLAN_VERSION_CODE: Final[str] = "PLN-MOH-2027-001-V1"
PLAN_ITEM_CODE: Final[str] = "PPI-MOH-2027-021"
PLAN_ITEM_CODE_SCN: Final[str] = "PPI-MOH-2027-022"
PROCUREMENT_PLAN_VERSION_V2: Final[str] = "PLN-MOH-2027-001-V2"
TENDER_CODE: Final[str] = "TND-MOH-2027-008"
PLAN_AMOUNT_V1: Final[float] = 455_000_000
PLAN_AMOUNT_V2: Final[float] = 535_000_000
PLAN_ITEM_SCN_AMOUNT: Final[float] = 80_000_000
RSV_CODE_SCN: Final[str] = "RSV-MOH-0002"
RSV_SHORT_CODE: Final[str] = "RSV-MOH-SHORT-001"

USER_MEDICAL: Final[str] = "moh.medicalservices.officer@example.test"
USER_PUBLIC: Final[str] = "moh.publichealth.officer@example.test"
USER_STR_REVIEWER: Final[str] = "moh.strategy.reviewer@example.test"
USER_BUD_REVIEWER: Final[str] = "moh.budget.reviewer@example.test"
USER_BUD_AUTHORITY: Final[str] = "moh.budget.authority@example.test"
USER_VIEWER: Final[str] = "moh.viewer@example.test"
USER_KISUMU_OFFICER: Final[str] = "kisumu.health.officer@example.test"
USER_KISUMU_VIEWER: Final[str] = "kisumu.viewer@example.test"
USER_BUD_DUAL: Final[str] = "moh.budget.officer.authority@example.test"
# Contract v2.2 §4.6 / §7.5 — Demand creation-scope demonstration personas.
USER_MULTISCOPE: Final[str] = "kentender.multiscope.admin@example.test"
USER_SYSTEM_ADMIN: Final[str] = "kentender.system.admin@example.test"
# Demo v2.7 §4.6 — Planning personas
USER_PLANNING_OFFICER: Final[str] = "moh.planning.officer@example.test"
USER_PLANNING_REVIEWER: Final[str] = "moh.planning.reviewer@example.test"
# Extra SoD persona (not listed in Demo §4.6).
USER_ACCOUNTING_OFFICER: Final[str] = "moh.accounting.officer@example.test"
USER_PLAN_APPROVER: Final[str] = "moh.plan.approver@example.test"
USER_TENDER_INITIATOR: Final[str] = "moh.tender.initiator@example.test"
USER_COUNTY_PLANNER: Final[str] = "kisumu.planning.officer@example.test"
# Demo v2.7 §4.6 — named HoD / HoP / Budget Officer login personas.
USER_BUSINESS_APPROVER: Final[str] = "moh.business.approver@example.test"
USER_HOP: Final[str] = "moh.procurement.authority@example.test"
USER_BUD_OFFICER: Final[str] = "moh.budget.officer@example.test"
# Retired primary denial persona (kept disabled).
USER_OTHER_ENTITY: Final[str] = "other.entity.officer@example.test"

CANONICAL_USERS: Final[tuple[str, ...]] = (
	USER_MEDICAL,
	USER_PUBLIC,
	USER_STR_REVIEWER,
	USER_BUD_REVIEWER,
	USER_BUD_AUTHORITY,
	USER_VIEWER,
	USER_KISUMU_OFFICER,
	USER_KISUMU_VIEWER,
	USER_BUD_DUAL,
	USER_MULTISCOPE,
	USER_SYSTEM_ADMIN,
	USER_PLANNING_OFFICER,
	USER_PLANNING_REVIEWER,
	USER_ACCOUNTING_OFFICER,
	USER_PLAN_APPROVER,
	USER_TENDER_INITIATOR,
	USER_COUNTY_PLANNER,
	USER_BUSINESS_APPROVER,
	USER_HOP,
	USER_BUD_OFFICER,
)

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
	USER_OTHER_ENTITY,
)

# Browser factories historically created these users with the same @example.test
# domain as canonical personas. Keep the identities explicit so cleanup never
# guesses from the email domain and never removes a real demo persona.
PLAYWRIGHT_USERS: Final[tuple[str, ...]] = (
	"dem-ui03-ba@example.test",
	"moh.procurement.approver@example.test",
	"dem-ui09-planner@example.test",
	"pln.ui.viewer@example.test",
	"pln.ui.multi@example.test",
)


def fixture_datetime_offset_days(days: int) -> str:
	dt = FIXTURE_NOW + timedelta(days=days)
	return dt.strftime("%Y-%m-%d %H:%M:%S")


def fixture_date_offset_days(days: int) -> str:
	dt = FIXTURE_NOW + timedelta(days=days)
	return dt.strftime("%Y-%m-%d")
