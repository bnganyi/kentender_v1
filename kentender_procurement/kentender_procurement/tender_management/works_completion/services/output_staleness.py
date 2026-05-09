# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS-COMP-0510 — Works output staleness mapping façade.

Pack §15 logical mapping is implemented in ``std_instance`` (parameter codes,
BOQ, works requirements, drawing register). This module documents the table and
exposes read helpers for callers and tests.

Staleness application (merge ``outputs_stale_flags``, clear ``current_*`` pointers,
``readiness_status`` Blocked) and ``EVT_STDINST_OUTPUTS_STALED`` audit emission live
in ``parameter``, ``boq``, ``works_requirement``, and ``drawing_register`` helpers.
"""

from __future__ import annotations

from typing import Any

from kentender_procurement.tender_management.std_instance.boq import BOQ_STALE_OUTPUT_KEYS
from kentender_procurement.tender_management.std_instance.parameter import (
	PARAMETER_CODE_TO_STALE_OUTPUTS,
	_normalize_pc,
)


# Pack §15 — semantic source rows (reference only; engine uses finer parameter/row keys).
PACK_OUTPUT_STALENESS_TABLE: tuple[tuple[str, frozenset[str]], ...] = (
	("TDS dates/deadlines", frozenset({"Bundle", "DSM", "DOM"})),
	("Tender security", frozenset({"Bundle", "DSM", "DEM"})),
	("Bid validity", frozenset({"Bundle", "DSM", "DEM"})),
	("Evaluation thresholds", frozenset({"Bundle", "DSM", "DEM"})),
	("Works specifications", frozenset({"Bundle", "DSM", "DEM", "DCM"})),
	("Site information", frozenset({"Bundle", "DSM", "DEM", "DCM"})),
	("Drawings", frozenset({"Bundle", "DEM", "DCM"})),
	("BOQ", frozenset({"Bundle", "DSM", "DEM", "DCM"})),
	("SCC values", frozenset({"Bundle", "DCM"})),
)


class WorksOutputStalenessService:
	"""Read-only access to Works tender-stage output staleness rules."""

	@staticmethod
	def get_pack_staleness_table() -> tuple[tuple[str, frozenset[str]], ...]:
		return PACK_OUTPUT_STALENESS_TABLE

	@staticmethod
	def get_stale_outputs_for_parameter_code(parameter_code: str | None) -> frozenset[str] | None:
		"""Return logical outputs that become stale when ``parameter_code`` changes, if mapped."""
		pc = _normalize_pc(parameter_code)
		if not pc:
			return None
		return PARAMETER_CODE_TO_STALE_OUTPUTS.get(pc)

	@staticmethod
	def get_boq_change_stale_outputs() -> frozenset[str]:
		"""Logical outputs marked stale on any BOQ structural change (pack §15)."""
		return BOQ_STALE_OUTPUT_KEYS

	@staticmethod
	def describe_parameter_mapping() -> dict[str, Any]:
		"""Snapshot of ``PARAMETER_CODE_TO_STALE_OUTPUTS`` for introspection (sorted keys)."""
		return {
			pc: sorted(outputs) for pc, outputs in sorted(PARAMETER_CODE_TO_STALE_OUTPUTS.items())
		}
