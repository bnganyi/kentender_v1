# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Release PKG-MOH-2026-001 to tender (spec §14)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	JOURNEY_CODE,
	PKGREL_CODE,
	PKGREL_NEXT_ACTION,
	PKGREL_RELEASED_AT,
	PKGREL_RELEASED_BY_EMAIL,
	PKGREL_RELEASED_BY_USER_CODE,
	PKG_CODE,
	SEED_ACTOR,
	strict_release_evidence_links,
	strict_release_locked_summary,
	strict_release_passed_forward_summary,
	strict_release_technical_refs,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.package import (
	promote_master_package_line_released,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)

_HANDOFF_STATUS_RELEASED = "Handed Off"


def _release_seed_repair_allowed() -> bool:
	package_status = (frappe.db.get_value("Procurement Package", PKG_CODE, "status") or "").strip()
	if package_status == PKG_CONSUMED:
		return False
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return True
	handoff_status = (
		frappe.db.get_value("Procurement Handoff Card", PKGREL_CODE, "status") or ""
	).strip()
	return handoff_status != "Consumed"


def _strict_release_handoff_payload(*, generated_by: str) -> dict[str, Any]:
	return {
		"handoff_code": PKGREL_CODE,
		"handoff_title": "Planning Release Package",
		"journey_code": JOURNEY_CODE,
		"source_module": "Procurement Planning",
		"target_module": "Tender Management",
		"source_object_type": "Procurement Package",
		"source_object_code": PKG_CODE,
		"status": _HANDOFF_STATUS_RELEASED,
		"generated_by": generated_by,
		"generated_at": PKGREL_RELEASED_AT,
		"next_action": PKGREL_NEXT_ACTION,
		"locked_summary": strict_release_locked_summary(),
		"passed_forward_summary": strict_release_passed_forward_summary(),
		"evidence_links": strict_release_evidence_links(include_tender=False),
		"technical_refs": strict_release_technical_refs(),
		"is_master_seed": True,
	}


def _cleanup_orphan_release_handoffs() -> None:
	for code in frappe.get_all(
		"Procurement Handoff Card",
		filters={"source_object_code": PKG_CODE},
		pluck="handoff_code",
	):
		if code != PKGREL_CODE:
			frappe.delete_doc("Procurement Handoff Card", code, force=1)


def _sync_package_release_fields() -> None:
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{
			"status": PKG_RELEASED,
			"release_code": PKGREL_CODE,
			"locked_after_release": 1,
			"released_to_tender_at": get_datetime(PKGREL_RELEASED_AT),
			"tender_code": None,
		},
		update_modified=False,
	)


def build_strict_release_consumed_handoff_payload() -> dict[str, Any]:
	"""Spec §14.3 consumed overlay for PKGREL-MOH-2026-001."""
	from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
		PKGCONSUME_CONSUMED_AT,
		PKGCONSUME_CONSUMED_BY_USER_CODE,
		TENDER_CODE,
		strict_release_evidence_links,
	)

	payload = _strict_release_handoff_payload(generated_by=PKGREL_RELEASED_BY_USER_CODE)
	payload.update(
		{
			"status": "Consumed",
			"target_object_type": "TM2 Tender",
			"target_object_code": TENDER_CODE,
			"consumed_by": PKGCONSUME_CONSUMED_BY_USER_CODE,
			"consumed_at": PKGCONSUME_CONSUMED_AT,
			"evidence_links": strict_release_evidence_links(include_tender=True),
		}
	)
	return payload


def ensure_planning_release(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	del actor
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")

	generated_by = _ensure_seed_user(
		email=PKGREL_RELEASED_BY_EMAIL,
		user_code=PKGREL_RELEASED_BY_USER_CODE,
		full_name="Planning Authority MOH",
	)
	del generated_by
	payload = _strict_release_handoff_payload(generated_by=PKGREL_RELEASED_BY_USER_CODE)
	existed = bool(frappe.db.exists("Procurement Handoff Card", PKGREL_CODE))

	if existed:
		if _release_seed_repair_allowed():
			create_or_update_handoff_card(payload)
			action = "repaired"
		else:
			action = "existing"
	else:
		create_or_update_handoff_card(payload)
		action = "created"

	if _release_seed_repair_allowed():
		_cleanup_orphan_release_handoffs()
		_sync_package_release_fields()
		promote_master_package_line_released()

	return {
		"action": action,
		"release_code": PKGREL_CODE,
		"status": PKG_RELEASED,
	}
