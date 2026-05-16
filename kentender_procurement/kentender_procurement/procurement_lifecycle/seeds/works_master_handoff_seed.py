# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-011 — Ensure all 7 base handoff cards exist with spec §16.2–16.8 JSON payloads.

## Handoff cards (base ``TENDER_PUBLISHED`` checkpoint)

| Code | Title | Status |
|---|---|---|
| STRATREF-MOH-2026-001  | Strategy Alignment Reference         | Consumed   |
| BUDCONF-MOH-2026-001   | Budget Funding Confirmation          | Consumed   |
| DEMAPP-MOH-2026-001    | Demand Approval Certificate          | Consumed   |
| PLANINCL-MOH-2026-001  | Planning Inclusion Record            | Consumed   |
| PKGREL-MOH-2026-001    | Planning Release Package             | Consumed   |
| STDREADY-TND-MOH-2026-001 | Tender Document Readiness Certificate | Consumed |
| PUBCERT-TND-MOH-2026-001  | Tender Publication Certificate     | Handed Off |

## Approach

``load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")`` is the
approved materialisation path for both the journey (R2-010) and handoff cards (R2-011).
This wrapper calls the loader with ``reset=False`` for an idempotent upsert,
then validates all 7 cards exist and returns per-card evidence for R2-011 data proof.

CLOSECERT and OPENREADY are **not** created here — those are R2-011A / ``OPENING_READY``
checkpoint only.
"""

from __future__ import annotations

import json
from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	BASE_HANDOFF_CODES,
	JOURNEY_CODE,
)

_CHECKPOINT = "TENDER_PUBLISHED"


def upsert_works_master_handoff_cards(*, reset: bool = False) -> dict[str, Any]:
	"""Idempotently create/update the 7 base handoff cards (spec §16.2–16.8).

	:param reset: When ``True`` deletes master-flagged PLC rows first (§19.4).
	    Pass ``False`` (default) for a pure upsert.
	:returns: Result dict with ``ok``, ``handoff_codes``, per-card ``cards`` summary,
	    and ``warnings``.
	"""
	frappe.set_user("Administrator")

	out = load_procurement_lifecycle_works_master(reset=reset, checkpoint=_CHECKPOINT)
	if not out.get("ok"):
		return out

	# Collect per-card evidence
	cards: list[dict[str, Any]] = []
	all_present = True
	for code in BASE_HANDOFF_CODES:
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

	return {
		"ok": all_present,
		"handoff_codes": list(BASE_HANDOFF_CODES),
		"cards": cards,
		"warnings": out.get("warnings", []),
	}
