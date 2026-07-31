# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Demo platform seed — codes and stage roles."""

from __future__ import annotations

from typing import Final

PACK_NAME: Final[str] = "demo-platform-moh-2026"
PACK_TITLE: Final[str] = "KenTender Demo Platform Seed FY 2026/2027 (MOH IT STD)"

PE_MOH: Final[str] = "PE-MOH"
PE_MOH_NAME: Final[str] = "Ministry of Health"
PE_MOE: Final[str] = "PE-MOE"
PE_MOE_NAME: Final[str] = "Ministry of Education"

# Legacy / clutter entities to migrate or remove
LEGACY_MOH: Final[str] = "MOH"
LEGACY_MOE: Final[str] = "MOE"
REMOVE_PE_CODES: Final[tuple[str, ...]] = ("PE-DOE", "PE-SDT", "TCFG-JOURNEY-PE", "TCFG-LEAN-IT-PE")

DEMO_PREFIX: Final[str] = "DEMO-MOH-2026"

# DIA actionable
DEMAND_DRAFT: Final[str] = f"{DEMO_PREFIX}-DEM-DRAFT"
DEMAND_PENDING_HOD: Final[str] = f"{DEMO_PREFIX}-DEM-HOD"

# CFG / packages (IT STD walkable + gate-ready + published)
PKG_READY_TO_CONFIGURE: Final[str] = f"{DEMO_PREFIX}-PKG-READY"
PKG_WALKABLE: Final[str] = f"{DEMO_PREFIX}-PKG-IP"
CFG_WALKABLE: Final[str] = f"{DEMO_PREFIX}-CFG-IP"
PKG_NEEDS_ATTENTION: Final[str] = f"{DEMO_PREFIX}-PKG-NA"
CFG_NEEDS_ATTENTION: Final[str] = f"{DEMO_PREFIX}-CFG-NA"
PKG_GATE_READY: Final[str] = f"{DEMO_PREFIX}-PKG-RFP"
CFG_GATE_READY: Final[str] = f"{DEMO_PREFIX}-CFG-RFP"
PKG_PUBLISHED: Final[str] = f"{DEMO_PREFIX}-PKG-PUB"
CFG_PUBLISHED: Final[str] = f"{DEMO_PREFIX}-CFG-PUB"
# Second open (receiving) publication so /tenders Open filter is not a single card
PKG_PUBLISHED_OPEN2: Final[str] = f"{DEMO_PREFIX}-PKG-PUB-OPEN2"
CFG_PUBLISHED_OPEN2: Final[str] = f"{DEMO_PREFIX}-CFG-PUB-OPEN2"

DEFAULT_PLANNING_CHECKPOINT: Final[str] = "RELEASED_TO_TENDER"
