# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""WORKS master planning seed — compatibility shim (delegates to PP2 canonical loader).

Legacy R2-007 bypass implementation removed per ``kentender-pp2-legacy-removal.mdc``.
All WORKS planning materialization runs through
:func:`seed_procurement_planning_works_master` at ``RELEASED_TO_TENDER`` (minimum for
downstream TM2 / PLC chains that previously called ``upsert_works_master_planning``).

Run (canonical)::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master.seed_procurement_planning_works_master \\
        --kwargs '{"checkpoint": "RELEASED_TO_TENDER", "force_reset": False}'

Run (shim — same behavior)::

    bench --site kentender.midas.com execute \\
        kentender_procurement.procurement_planning.seeds.works_master_planning_seed.upsert_works_master_planning
"""

from __future__ import annotations

from typing import Any

import frappe

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	BUDGET_LINE_CODE,
	DEMAND_CODE,
	ESTIMATED_VALUE,
	FISCAL_YEAR,
	PKG_CODE,
	PKG_LINE_CODE,
	PKG_TITLE,
	PLAN_CODE,
	PLAN_NAME,
	JOURNEY_CODE,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.loader import (
	clear_master_planning_seed,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.upstream import (
	validate_upstream_for_checkpoint,
)
from kentender_procurement.procurement_planning.seeds.seed_procurement_planning_works_master import (
	seed_procurement_planning_works_master,
)

# Re-export for legacy import sites (purge scripts, lifecycle tests).
__all__ = [
	"BUDGET_LINE_CODE",
	"DEMAND_ID",
	"ESTIMATED_VALUE",
	"FISCAL_YEAR",
	"PKG_CODE",
	"PKG_LINE_CODE",
	"PKG_NAME",
	"PLAN_CODE",
	"PLAN_NAME",
	"upsert_works_master_planning",
]

DEMAND_ID = DEMAND_CODE
PKG_NAME = PKG_TITLE


def resolve_procuring_entity_moh() -> str | None:
	for code in ("PE-MOH", "MOH"):
		if frappe.db.exists("Procuring Entity", code):
			return code
		name = frappe.db.get_value("Procuring Entity", {"entity_code": code}, "name")
		if name:
			return name
	return None


def _ensure_pp2_prerequisites() -> dict[str, Any] | None:
	"""Bootstrap rows legacy chains assumed but PP2 loader requires."""
	if not frappe.db.exists("Procurement Journey", JOURNEY_CODE):
		from kentender_procurement.procurement_lifecycle.seeds.works_master_journey_seed import (
			upsert_works_master_journey,
		)

		j_out = upsert_works_master_journey(reset=False)
		if not j_out.get("ok"):
			return {
				"ok": False,
				"error_code": "MISSING_JOURNEY",
				"message": f"Procurement Journey {JOURNEY_CODE} could not be created.",
			}

	if not frappe.db.exists("STD Template", {"template_code": "KE-PPRA-WORKS-BLDG-2022-04-POC"}):
		from kentender_procurement.tender_management.seeds.works_master_std_seed import (
			upsert_works_master_std,
		)

		std_out = upsert_works_master_std()
		if not std_out.get("ok"):
			return {
				"ok": False,
				"error_code": "MISSING_STD_VERSION",
				"message": "WORKS STD template prerequisite could not be loaded.",
			}
	return None


def _map_legacy_shape(pp2_out: dict[str, Any], *, was_complete_before: bool) -> dict[str, Any]:
	if not pp2_out.get("ok"):
		err = pp2_out.get("error_code") or "SEED_FAILED"
		return {
			"ok": False,
			"error_code": err,
			"message": pp2_out.get("message") or pp2_out.get("failures", ["Planning seed failed."])[0],
		}

	pkg_name = frappe.db.get_value("Procurement Package", {"package_code": PKG_CODE}, "name")
	return {
		"ok": True,
		"idempotent": was_complete_before,
		"plan": PLAN_CODE,
		"plan_code": PLAN_CODE,
		"plan_created": not was_complete_before,
		"package": pkg_name or PKG_CODE,
		"package_code": PKG_CODE,
		"package_created": not was_complete_before,
		"package_line_created": not was_complete_before,
		"plan_status": frappe.db.get_value("Procurement Plan", PLAN_CODE, "status"),
		"package_status": frappe.db.get_value("Procurement Package", PKG_CODE, "status"),
		"pp2_checkpoint": pp2_out.get("checkpoint"),
		"pp2_summary": pp2_out.get("records"),
	}


def upsert_works_master_planning(*, force_reset: bool = False) -> dict[str, Any]:
	"""Load WORKS master planning via PP2 ``RELEASED_TO_TENDER`` checkpoint (shim)."""
	frappe.set_user("Administrator")

	entity = resolve_procuring_entity_moh()
	if not entity:
		return {
			"ok": False,
			"error_code": "MISSING_PROCURING_ENTITY",
			"message": "No Procuring Entity found with code MOH or PE-MOH. Run entity seed first.",
		}

	pre = _ensure_pp2_prerequisites()
	if pre:
		return pre

	upstream = validate_upstream_for_checkpoint("RELEASED_TO_TENDER")
	if not upstream.get("ok"):
		# Preserve legacy error_code names where they match.
		return {
			"ok": False,
			"error_code": upstream.get("error_code"),
			"message": upstream.get("message"),
		}

	was_complete = bool(
		frappe.db.exists("Procurement Plan", PLAN_CODE)
		and frappe.db.exists("Procurement Package", PKG_CODE)
		and frappe.db.get_value(
			"Procurement Package Line", {"package_line_code": PKG_LINE_CODE}, "name"
		)
		and frappe.db.exists("Procurement Handoff Card", "PKGREL-MOH-2026-001")
	)

	if force_reset:
		clear_master_planning_seed()

	pp2_out = seed_procurement_planning_works_master(
		checkpoint="RELEASED_TO_TENDER",
		force_reset=False,
	)
	return _map_legacy_shape(pp2_out, was_complete_before=was_complete)
