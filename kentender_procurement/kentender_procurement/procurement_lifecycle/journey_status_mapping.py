# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map source module raw statuses to :class:`ProcurementJourneyStatusCategory` (R1-001 / LV-R1-001-02).

Only **procurement_package** is implemented here. Demand, TM2, and other modules get their own
rows in a later ticket (R1-002+ / matrix automation); unknown ``module_key`` or ``raw_status``
raises ``ValueError`` so new source states must extend this table explicitly.
"""

from __future__ import annotations

from kentender_procurement.procurement_planning.doctype.procurement_package.procurement_package import (
	ST_APPROVED,
	ST_COMPLETED,
	ST_DRAFT,
	ST_READY_FOR_TENDER,
	ST_REJECTED,
	ST_RELEASED_TO_TENDER,
	ST_RETURNED,
	ST_SUBMITTED,
)

from kentender_procurement.procurement_lifecycle.journey_status_category import ProcurementJourneyStatusCategory

# Cursor pack §5.4 example uses machine-style token for source_status.
_ALIAS_RELEASED_TO_TENDER = "RELEASED_TO_TENDER"

_PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY: dict[str, ProcurementJourneyStatusCategory] = {
	ST_DRAFT: ProcurementJourneyStatusCategory.NOT_STARTED,
	ST_SUBMITTED: ProcurementJourneyStatusCategory.NEEDS_ACTION,
	ST_APPROVED: ProcurementJourneyStatusCategory.IN_PROGRESS,
	ST_READY_FOR_TENDER: ProcurementJourneyStatusCategory.IN_PROGRESS,
	ST_RELEASED_TO_TENDER: ProcurementJourneyStatusCategory.HANDED_OFF,
	ST_RETURNED: ProcurementJourneyStatusCategory.RETURNED,
	ST_REJECTED: ProcurementJourneyStatusCategory.CANCELLED,
	ST_COMPLETED: ProcurementJourneyStatusCategory.COMPLETED,
	_ALIAS_RELEASED_TO_TENDER: ProcurementJourneyStatusCategory.HANDED_OFF,
}

_MODULE_KEY_PACKAGE = "procurement_package"


def map_raw_to_journey_status_category(*, module_key: str, raw_status: str) -> ProcurementJourneyStatusCategory:
	"""Return the standard journey category for a source module status string.

	:param module_key: Stable key, e.g. ``\"procurement_package\"`` for :doc:`Procurement Package`.
	:param raw_status: Exact status string from the source (or ``RELEASED_TO_TENDER`` alias).
	:raises ValueError: Unknown module or unknown / empty raw status.
	"""
	if not raw_status or not raw_status.strip():
		raise ValueError("raw_status must be a non-empty string")

	key = module_key.strip().lower()
	if key != _MODULE_KEY_PACKAGE:
		raise ValueError(f"Unknown module_key for journey status mapping: {module_key!r}")

	normalized = raw_status.strip()
	if normalized in _PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY:
		return _PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY[normalized]

	raise ValueError(f"Unknown procurement_package status for journey mapping: {raw_status!r}")
