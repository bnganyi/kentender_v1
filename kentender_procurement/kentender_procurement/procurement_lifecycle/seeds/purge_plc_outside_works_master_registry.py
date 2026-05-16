# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Purge PLC rows outside the WORKS master registry (G0-008 / seed spec §4.1–4.2).

Use on dev/UAT benches to drop **test-only** or ad-hoc **Procurement Journey** /
**Procurement Handoff Card** rows. **In scope:** only these two DocTypes.

**Kept** (canonical registry):

- Journey: ``JRN-MOH-2026-001`` (§4.1).
- Handoffs: the nine §4.2 codes, **only** when ``journey_code`` matches the documented journey
  (avoids keeping a §4.2 code row still attached to a test journey).

**Removed:** any other journey; any handoff whose code is not §4.2 or whose ``journey_code`` is
not ``JRN-MOH-2026-001``.

Run::

	bench --site kentender.midas.com execute \\
	  kentender_procurement.procurement_lifecycle.seeds.purge_plc_outside_works_master_registry.purge_procurement_lifecycle_plc_outside_works_master_registry \\
	  --kwargs '{"dry_run": False}'
"""

from __future__ import annotations

from typing import Any, Final

import frappe

from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)

_DOCUMENTED_JOURNEYS: Final[frozenset[str]] = frozenset({JOURNEY_CODE})
_DOCUMENTED_HANDOFF_CODES: Final[frozenset[str]] = frozenset(
	tuple(BASE_HANDOFF_CODES) + tuple(OPENING_HANDOFF_CODES)
)


def _handoff_is_canonical(row: dict[str, Any]) -> bool:
	code = (row.get("handoff_code") or row.get("name") or "").strip()
	jc = (row.get("journey_code") or "").strip()
	if code not in _DOCUMENTED_HANDOFF_CODES:
		return False
	return jc == JOURNEY_CODE


def _journey_is_canonical(row: dict[str, Any]) -> bool:
	jc = (row.get("journey_code") or row.get("name") or "").strip()
	return jc in _DOCUMENTED_JOURNEYS


def purge_procurement_lifecycle_plc_outside_works_master_registry(*, dry_run: bool = False) -> dict[str, Any]:
	"""Delete PLC rows outside G0-008 §4.1–4.2 registry (see module docstring).

	:param dry_run: When ``True``, only return what would be deleted.
	"""
	handoffs = frappe.get_all(
		"Procurement Handoff Card",
		fields=["name", "handoff_code", "journey_code"],
	)
	handoffs_to_remove = [h for h in handoffs if not _handoff_is_canonical(h)]

	journeys = frappe.get_all("Procurement Journey", fields=["name", "journey_code"])
	journeys_to_remove = [j for j in journeys if not _journey_is_canonical(j)]

	if dry_run:
		return {
			"ok": True,
			"dry_run": True,
			"would_delete_handoff_cards": [h["name"] for h in handoffs_to_remove],
			"would_delete_journeys": [j["name"] for j in journeys_to_remove],
			"counts": {
				"handoff_cards": len(handoffs_to_remove),
				"journeys": len(journeys_to_remove),
			},
		}

	deleted_handoffs: list[str] = []
	for h in handoffs_to_remove:
		name = h["name"]
		if frappe.db.exists("Procurement Handoff Card", name):
			frappe.delete_doc("Procurement Handoff Card", name, force=True, ignore_permissions=True)
			deleted_handoffs.append(name)

	deleted_journeys: list[str] = []
	for j in journeys_to_remove:
		name = j["name"]
		if frappe.db.exists("Procurement Journey", name):
			frappe.delete_doc("Procurement Journey", name, force=True, ignore_permissions=True)
			deleted_journeys.append(name)

	return {
		"ok": True,
		"dry_run": False,
		"deleted_handoff_cards": deleted_handoffs,
		"deleted_journeys": deleted_journeys,
		"counts": {"handoff_cards": len(deleted_handoffs), "journeys": len(deleted_journeys)},
	}
