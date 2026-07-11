# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Stable platform seed — canonical business codes and scenario metadata."""

from __future__ import annotations

from typing import Final

PACK_NAME: Final[str] = "stable-platform-moh-2026"
PACK_TITLE: Final[str] = "Ministry of Health Stable Platform Seed FY 2026/2027"
MASTER_SCENARIO_WORKS: Final[str] = "District Hospital Renovation Works"
MASTER_SCENARIO_IT: Final[str] = "District Hospital HMIS Upgrade and Network Infrastructure"

PE_CODE: Final[str] = "PE-MOH"
PE_DISPLAY: Final[str] = "Ministry of Health"

# Works chain (delegates to existing WORKS master seeds)
WORKS_DEMAND_CODE: Final[str] = "DEM-MOH-2026-001"
WORKS_PLAN_CODE: Final[str] = "PLAN-MOH-2026"
WORKS_PKG_CODE: Final[str] = "PKG-MOH-2026-001"
WORKS_JOURNEY_CODE: Final[str] = "JRN-MOH-2026-001"

# IT strategy supplement (same STRAT-MOH-2026 strategic plan)
IT_PROGRAM_CODE: Final[str] = "PROG-MOH-DIGITAL"
IT_PROGRAM_TITLE: Final[str] = "Digital Health Systems Modernization"
IT_PROGRAM_DESCRIPTION: Final[str] = (
	"Modernize hospital information systems, network infrastructure, and digital health "
	"platforms across priority Ministry of Health facilities."
)
IT_SUB_PROGRAM_CODE: Final[str] = "SUB-MOH-DIGITAL-001"
IT_SUB_PROGRAM_TITLE: Final[str] = "HMIS and network infrastructure"
IT_OBJECTIVE_CODE: Final[str] = "OBJ-MOH-HMIS-UPGRADE"
IT_OBJECTIVE_TITLE: Final[str] = "Upgrade hospital information management systems"
IT_OBJECTIVE_DESCRIPTION: Final[str] = (
	"Deploy integrated HMIS, network backbone, and clinical workstation infrastructure "
	"at priority district hospitals."
)
IT_TARGET_CODE: Final[str] = "TGT-MOH-HMIS-2026"
IT_TARGET_TITLE: Final[str] = "Deploy integrated HMIS at priority district hospitals in FY 2026/2027"
IT_TARGET_METRIC: Final[str] = "Number of district hospitals with live HMIS deployment"

# IT budget supplement (same BUDGET-MOH-2026 cycle)
IT_BUDGET_LINE_CODE: Final[str] = "BUD-MOH-IT-2026-001"
IT_BUDGET_LINE_TITLE: Final[str] = "Hospital HMIS and ICT Infrastructure"
IT_BUDGET_LINE_NOTES: Final[str] = (
	"Stable platform seed — funding for HMIS software licences, servers, network equipment, "
	"and implementation services at Makutano District Hospital."
)
IT_AMOUNT_ALLOCATED: Final[float] = 45_000_000.0
IT_AMOUNT_RESERVED: Final[float] = 38_000_000.0

# IT demand
IT_DEMAND_CODE: Final[str] = "DEM-MOH-2026-002"
IT_DEMAND_ITEM_CODE: Final[str] = "DEMITEM-MOH-2026-002-001"
IT_DEMAND_TITLE: Final[str] = "District Hospital HMIS Upgrade and Network Infrastructure"
IT_DEMAND_ESTIMATE: Final[float] = 38_000_000.0
IT_DEPT_NAME: Final[str] = "Health Informatics and Digital Services Directorate"

# IT planning supplement (same PLAN-MOH-2026)
IT_INCLUSION_CODE: Final[str] = "PLANINCL-MOH-2026-002"
IT_PKG_CODE: Final[str] = "PKG-MOH-2026-002"
IT_PKG_TITLE: Final[str] = "District Hospital HMIS Upgrade"
IT_PKG_LINE_CODE: Final[str] = "PKGLINE-MOH-2026-002-001"
IT_STD_VERSION_CODE: Final[str] = "KE-PPRA-IT-2022-04"
IT_STD_FAMILY_CODE: Final[str] = "KE-PPRA-IT"
IT_PROCUREMENT_CATEGORY: Final[str] = "Goods"
IT_REQUIRED_STD_CATEGORY: Final[str] = "Information Technology"
IT_REQUIRED_STD_TYPE: Final[str] = "Information Technology"

DEFAULT_PLANNING_CHECKPOINT: Final[str] = "PACKAGE_DRAFT"
SUPPORTED_PLANNING_CHECKPOINTS: Final[tuple[str, ...]] = (
	"INCLUDED_IN_PLAN",
	"PACKAGE_DRAFT",
	"READY_FOR_RELEASE",
	"RELEASED_TO_TENDER",
	"CONSUMED_BY_TENDER",
)
