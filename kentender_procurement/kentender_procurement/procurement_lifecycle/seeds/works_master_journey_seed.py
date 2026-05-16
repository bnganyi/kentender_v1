# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""R2-010 — Ensure ``JRN-MOH-2026-001`` and 12 journey steps exist (spec §14–15).

## Approach

``load_procurement_lifecycle_works_master(checkpoint="TENDER_PUBLISHED")`` is the
approved materialisation path (R2-001 / ``works_master_loader.run_load``).  It
idempotently creates/updates:

* ``Procurement Journey``  ``JRN-MOH-2026-001``  (spec §14 header fields)
* 12 × ``Procurement Journey Step`` child rows  (spec §15 TENDER_PUBLISHED snapshot)
* 7 × ``Procurement Handoff Card``  (spec §16.2–16.8, R2-011 scope)

R2-010 scopes to the **Journey record + steps**; handoff-card evidence is reported
under R2-011.  This wrapper is a thin call through to the loader, returning a
focused result dict for the R2-010 data-proof requirement.

All steps are idempotent: re-running is safe.
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_lifecycle.seeds.seed_procurement_lifecycle_works_master import (
	load_procurement_lifecycle_works_master,
)
from kentender_procurement.procurement_lifecycle.seeds.works_master_handoff_payloads import (
	JOURNEY_CODE,
)

_CHECKPOINT = "TENDER_PUBLISHED"


def upsert_works_master_journey(*, reset: bool = False) -> dict[str, Any]:
	"""Idempotently create/update ``JRN-MOH-2026-001`` and its 12 journey steps.

	:param reset: When ``True`` deletes master-flagged PLC rows first (§19.4 / R2-002).
	    Pass ``False`` (default) for a pure upsert without dropping existing rows.
	:returns: Result dict with ``ok``, ``journey_code``, ``journey_steps``,
	    ``handoff_cards``, ``action`` (``created`` / ``existing``), and ``warnings``.
	"""
	frappe.set_user("Administrator")

	already_existed = bool(frappe.db.exists("Procurement Journey", JOURNEY_CODE))

	out = load_procurement_lifecycle_works_master(reset=reset, checkpoint=_CHECKPOINT)
	if not out.get("ok"):
		return out

	journey = frappe.get_doc("Procurement Journey", JOURNEY_CODE)
	return {
		"ok": True,
		"action": "existing" if already_existed and not reset else "created",
		"journey_code": JOURNEY_CODE,
		"journey_title": journey.journey_title,
		"current_stage_key": journey.current_stage_key,
		"current_status_category": journey.current_status_category,
		"is_master_seed": bool(journey.is_master_seed),
		"journey_steps": len(journey.steps or []),
		"handoff_cards": out.get("created_or_updated", {}).get("handoff_cards", 0),
		"warnings": out.get("warnings", []),
	}
