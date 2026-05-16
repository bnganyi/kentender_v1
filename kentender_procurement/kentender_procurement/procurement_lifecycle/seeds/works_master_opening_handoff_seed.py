# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-011A — Ensure CLOSECERT and OPENREADY handoff cards exist (spec §16.9–16.10).

## Handoff cards (optional ``OPENING_READY`` checkpoint)

| Code | Title | Status |
|---|---|---|
| CLOSECERT-TND-MOH-2026-001 | Tender Closing Certificate   | Consumed   |
| OPENREADY-TND-MOH-2026-001 | Opening Readiness Record     | Handed Off |

These two cards are **only** created at the ``OPENING_READY`` checkpoint — never by the
base ``TENDER_PUBLISHED`` seed.  The existing TM2 fixture (``TND-MOH-2026-001`` in
**Published** status from R2-009) safely supports this scenario.

## Side effects

``load_procurement_lifecycle_works_master(checkpoint="OPENING_READY")`` also:

* Mutates journey step ``tender_closing`` → ``Completed``
  (``handoff_code=CLOSECERT-TND-MOH-2026-001``, ``source_object_code=CLS-TND-MOH-2026-001``)
* Mutates journey step ``opening_readiness`` → ``Ready for Handoff``
  (``handoff_code=OPENREADY-TND-MOH-2026-001``, ``source_object_code=ORR-TND-MOH-2026-001``)
* Sets journey ``current_stage_key = "opening_ready"``,
  ``opening_readiness_ref = "ORR-TND-MOH-2026-001"``

These are intentional; the full lifecycle seed represents the opening-ready state.

## Idempotency

Re-running returns ``ok=True`` with ``action="existing"`` for both cards.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	JOURNEY_CODE,
	OPENING_HANDOFF_CODES,
)

_CHECKPOINT = "OPENING_READY"


def upsert_works_master_opening_handoff_cards(*, reset: bool = False) -> dict[str, Any]:
	"""Idempotently create/update CLOSECERT and OPENREADY handoff cards (spec §16.9–16.10).

	Also applies the ``OPENING_READY`` journey step mutations and header update.

	:param reset: When ``True`` deletes master-flagged PLC rows first, then re-seeds
	    all 9 cards (7 base + 2 opening) at the OPENING_READY checkpoint.
	:returns: Result dict with ``ok``, ``handoff_codes``, per-card ``cards`` summary,
	    ``journey_stage``, and ``warnings``.
	"""
	frappe.set_user("Administrator")

	out = load_procurement_lifecycle_works_master(reset=reset, checkpoint=_CHECKPOINT)
	if not out.get("ok"):
		return out

	# Collect per-card evidence for the two opening cards
	cards: list[dict[str, Any]] = []
	all_present = True
	for code in OPENING_HANDOFF_CODES:
		exists = bool(frappe.db.exists("Procurement Handoff Card", code))
		if not exists:
			all_present = False
			cards.append({"handoff_code": code, "exists": False})
			continue
		row = frappe.db.get_value(
			"Procurement Handoff Card",
			code,
			[
				"handoff_title",
				"status",
				"source_object_code",
				"target_object_code",
				"journey_code",
				"is_master_seed",
			],
			as_dict=True,
		)
		cards.append(
			{
				"handoff_code": code,
				"exists": True,
				"handoff_title": (row or {}).get("handoff_title", ""),
				"status": (row or {}).get("status", ""),
				"source_object_code": (row or {}).get("source_object_code", ""),
				"target_object_code": (row or {}).get("target_object_code", ""),
				"journey_code": (row or {}).get("journey_code", ""),
				"is_master_seed": bool((row or {}).get("is_master_seed")),
			}
		)

	journey_stage = (
		frappe.db.get_value("Procurement Journey", JOURNEY_CODE, "current_stage_key") or ""
	)

	return {
		"ok": all_present,
		"handoff_codes": list(OPENING_HANDOFF_CODES),
		"cards": cards,
		"journey_stage": journey_stage,
		"warnings": out.get("warnings", []),
	}
