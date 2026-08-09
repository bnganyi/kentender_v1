# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Map source module raw statuses to :class:`ProcurementJourneyStatusCategory`.

PP2 Package DocType retired — status string map retained for historical journey rows only.
"""

from __future__ import annotations

from kentender_procurement.procurement_lifecycle.journey_status_category import ProcurementJourneyStatusCategory

_ALIAS_RELEASED_TO_TENDER = "RELEASED_TO_TENDER"

_PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY: dict[str, ProcurementJourneyStatusCategory] = {
	"Draft": ProcurementJourneyStatusCategory.NOT_STARTED,
	"In Review": ProcurementJourneyStatusCategory.NEEDS_ACTION,
	"Returned": ProcurementJourneyStatusCategory.RETURNED,
	"Approved": ProcurementJourneyStatusCategory.IN_PROGRESS,
	"Ready for Release": ProcurementJourneyStatusCategory.IN_PROGRESS,
	"Released": ProcurementJourneyStatusCategory.HANDED_OFF,
	"Consumed": ProcurementJourneyStatusCategory.COMPLETED,
	"Superseded": ProcurementJourneyStatusCategory.CANCELLED,
	"Cancelled": ProcurementJourneyStatusCategory.CANCELLED,
	_ALIAS_RELEASED_TO_TENDER: ProcurementJourneyStatusCategory.HANDED_OFF,
}

_MODULE_KEY_PACKAGE = "procurement_package"


def map_raw_to_journey_status_category(*, module_key: str, raw_status: str) -> ProcurementJourneyStatusCategory:
	"""Return the standard journey category for a source module status string."""
	if not raw_status or not raw_status.strip():
		raise ValueError("raw_status must be a non-empty string")

	key = module_key.strip().lower()
	if key != _MODULE_KEY_PACKAGE:
		raise ValueError(f"Unknown module_key for journey status mapping: {module_key!r}")

	normalized = raw_status.strip()
	if normalized in _PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY:
		return _PROCUREMENT_PACKAGE_STATUS_TO_CATEGORY[normalized]

	raise ValueError(f"Unknown procurement_package status for journey mapping: {raw_status!r}")
