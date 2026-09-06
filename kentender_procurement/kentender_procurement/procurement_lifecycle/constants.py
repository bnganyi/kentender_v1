# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R1-002 — versioned journey step configuration (rectification pack §6.2, cursor pack §5.2).

Each row maps one spine step to owning module vocabulary, primary source object wording,
handoff / evidence artefact title, and a **default** standard status category for WORKS
checkpoint **Tender Published** (steps 1–9 materially complete; post-publish spine not
started). Aggregation services (R3+) replace per-journey runtime status; this field is
for layout defaults and contract tests only (ADR-PLC-002).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from kentender_procurement.procurement_lifecycle.journey_status_category import (
	ProcurementJourneyStatusCategory,
)


@dataclass(frozen=True, slots=True)
class JourneyStepConfig:
	"""One spine step — stable ``step_key`` and display / mapping metadata."""

	step_key: str
	label: str
	owner_module: str
	source_object_type: str
	handoff_title: str
	standard_status_category: ProcurementJourneyStatusCategory


# Bump when adding/removing/reordering steps or changing semantics (LV-R1-002-01).
JOURNEY_STEP_CONFIG_VERSION: Final[int] = 1

# Pack §6.2 spine order (rows 1–14). ``standard_status_category``: WORKS @ TENDER_PUBLISHED.
JOURNEY_STEP_CONFIG: Final[tuple[JourneyStepConfig, ...]] = (
	JourneyStepConfig(
		step_key="strategy",
		label="Strategic Priority",
		owner_module="Strategy",
		source_object_type="Strategic Plan / Programme / Objective",
		handoff_title="Strategy Alignment Reference",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="budget",
		label="Funding Available",
		owner_module="Budget",
		source_object_type="Procurement Budget Line",
		handoff_title="Budget Funding Confirmation",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="demand_captured",
		label="Need Captured",
		owner_module="Demand Intake",
		source_object_type="Demand",
		handoff_title="Demand Submission Record",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="demand_approved",
		label="Need Approved",
		owner_module="Demand Intake",
		source_object_type="Demand",
		handoff_title="Demand Approval Certificate",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="procurement_planned",
		label="Procurement Planned",
		owner_module="Procurement Planning",
		source_object_type="Procurement Plan",
		handoff_title="Planning Inclusion Record",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="package_prepared",
		label="Package Prepared",
		owner_module="Procurement Planning",
		source_object_type="Procurement Package",
		handoff_title="Package Readiness Summary",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="package_released",
		label="Package Released",
		owner_module="Procurement Planning",
		source_object_type="Procurement Package",
		handoff_title="Planning Release Package",
		standard_status_category=ProcurementJourneyStatusCategory.HANDED_OFF,
	),
	JourneyStepConfig(
		step_key="std_readiness",
		label="Tender Document Ready",
		owner_module="STD Admin / Tender Management",
		source_object_type="Tender STD Instance / Binding",
		handoff_title="STD Readiness Certificate",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="tender_published",
		label="Tender Published",
		owner_module="Tender Management",
		source_object_type="TM2 Tender",
		handoff_title="Tender Publication Certificate / Publication Snapshot",
		standard_status_category=ProcurementJourneyStatusCategory.COMPLETED,
	),
	JourneyStepConfig(
		step_key="tender_closed",
		label="Tender Closed",
		owner_module="Tender Management",
		source_object_type="TM2 Tender Closing Record",
		handoff_title="Tender Closing Certificate",
		standard_status_category=ProcurementJourneyStatusCategory.NOT_STARTED,
	),
	JourneyStepConfig(
		step_key="opening_ready",
		label="Opening Ready",
		owner_module="Tender Management",
		source_object_type="TM2 Opening Readiness Record",
		handoff_title="Opening Readiness Record",
		standard_status_category=ProcurementJourneyStatusCategory.NOT_STARTED,
	),
	JourneyStepConfig(
		step_key="opening_complete",
		label="Opening Complete",
		owner_module="Bid Opening",
		source_object_type="Future Opening Record",
		handoff_title="Opening Record",
		standard_status_category=ProcurementJourneyStatusCategory.NOT_STARTED,
	),
	JourneyStepConfig(
		step_key="award_approved",
		label="Award Approved",
		owner_module="Evaluation & Award",
		source_object_type="Future Award Decision",
		handoff_title="Award Decision",
		standard_status_category=ProcurementJourneyStatusCategory.NOT_STARTED,
	),
	JourneyStepConfig(
		step_key="contract_handoff",
		label="Contract Handoff",
		owner_module="Tender/Evaluation/Contract",
		source_object_type="Contract Handoff Reference",
		handoff_title="Contract Handoff Reference",
		standard_status_category=ProcurementJourneyStatusCategory.NOT_STARTED,
	),
)

_STEP_BY_KEY: Final[dict[str, JourneyStepConfig]] = {c.step_key: c for c in JOURNEY_STEP_CONFIG}

JOURNEY_STEP_KEYS_IN_ORDER: Final[tuple[str, ...]] = tuple(c.step_key for c in JOURNEY_STEP_CONFIG)


def get_journey_step_config(step_key: str) -> JourneyStepConfig:
	"""Return config for ``step_key`` or raise ``KeyError``."""
	return _STEP_BY_KEY[step_key]


def iter_journey_step_configs() -> tuple[JourneyStepConfig, ...]:
	"""Spine order — same sequence as :data:`JOURNEY_STEP_CONFIG`."""
	return JOURNEY_STEP_CONFIG
