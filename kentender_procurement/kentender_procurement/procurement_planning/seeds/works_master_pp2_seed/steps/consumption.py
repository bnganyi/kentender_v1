# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Mark PKGREL consumed by TND-MOH-2026-001 (spec §15–§16)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_lifecycle.handoff_card_service import (
	create_or_update_handoff_card,
)
from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_CONSUMED,
	PKG_RELEASED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	PKGCONSUME_AUDIT_EVENT_REF,
	PKGCONSUME_CODE,
	PKGCONSUME_CONSUMED_AT,
	PKGCONSUME_CONSUMED_BY_EMAIL,
	PKGCONSUME_CONSUMED_BY_USER_CODE,
	PKGREL_CODE,
	PKG_CODE,
	SEED_ACTOR,
	TENDER_CODE,
	strict_consumption_result,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.release import (
	build_strict_release_consumed_handoff_payload,
)

_REPAIRABLE_CONSUMPTION_FIELDS = (
	"consumption_code",
	"release_code",
	"package_code",
	"consumed_by_module",
	"consumed_by",
	"consumed_at",
	"target_object_type",
	"target_object_code",
	"consumption_status",
	"consumption_result_json",
	"return_reason",
	"audit_event_ref",
	"is_master_seed",
)


def _consumption_seed_repair_allowed() -> bool:
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return False
	status = (frappe.db.get_value("Procurement Package", PKG_CODE, "status") or "").strip()
	return status in (PKG_RELEASED, PKG_CONSUMED)


def _ensure_master_tender() -> None:
	if frappe.db.exists("TM2 Tender", TENDER_CODE):
		return
	try:
		from kentender_procurement.tender_management.seeds.works_master_tender_seed import (
			upsert_works_master_tender,
		)

		upsert_works_master_tender()
	except Exception:
		frappe.log_error(
			title="PP2 seed tender canonicalization skipped",
			message=frappe.get_traceback(),
		)
	if not frappe.db.exists("TM2 Tender", TENDER_CODE):
		frappe.throw(
			f"TM2 Tender {TENDER_CODE} not found.",
			title="MISSING_TENDER",
		)


def _strict_consumption_values(*, consumed_by: str) -> dict[str, Any]:
	return {
		"consumption_code": PKGCONSUME_CODE,
		"release_code": PKGREL_CODE,
		"package_code": PKG_CODE,
		"consumed_by_module": "Tender Management",
		"consumed_by": consumed_by,
		"consumed_at": get_datetime(PKGCONSUME_CONSUMED_AT),
		"target_object_type": "TM2 Tender",
		"target_object_code": TENDER_CODE,
		"consumption_status": "Consumed",
		"consumption_result_json": strict_consumption_result(),
		"return_reason": None,
		"audit_event_ref": PKGCONSUME_AUDIT_EVENT_REF,
		"is_master_seed": 1,
	}


def _cleanup_orphan_consumption_records() -> None:
	for code in frappe.get_all(
		"Planning Release Consumption Record",
		filters={"release_code": PKGREL_CODE},
		pluck="consumption_code",
	):
		if code != PKGCONSUME_CODE:
			frappe.delete_doc("Planning Release Consumption Record", code, force=1)


def sync_master_release_consumed_overlay() -> dict[str, Any]:
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		return {"action": "missing", "release_code": PKGREL_CODE}
	out = create_or_update_handoff_card(build_strict_release_consumed_handoff_payload())
	return {
		"action": out.get("action", "updated"),
		"release_code": PKGREL_CODE,
	}


def _sync_package_consumed_fields() -> None:
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{
			"status": PKG_CONSUMED,
			"release_code": PKGREL_CODE,
			"tender_code": TENDER_CODE,
			"locked_after_release": 1,
			"consumed_at": get_datetime(PKGCONSUME_CONSUMED_AT),
		},
		update_modified=False,
	)


def ensure_release_consumed(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	del actor
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")
	if not frappe.db.exists("Procurement Handoff Card", PKGREL_CODE):
		frappe.throw(
			f"Planning release {PKGREL_CODE} not found.",
			title="MISSING_RELEASE",
		)

	_ensure_master_tender()

	consumed_by = _ensure_seed_user(
		email=PKGCONSUME_CONSUMED_BY_EMAIL,
		user_code=PKGCONSUME_CONSUMED_BY_USER_CODE,
		full_name="Procurement Officer MOH",
	)
	values = _strict_consumption_values(consumed_by=consumed_by)
	existed = bool(frappe.db.exists("Planning Release Consumption Record", PKGCONSUME_CODE))

	if not _consumption_seed_repair_allowed():
		return {
			"action": "existing",
			"consumption_code": PKGCONSUME_CODE,
			"tender_code": TENDER_CODE,
			"status": frappe.db.get_value("Procurement Package", PKG_CODE, "status") or PKG_CONSUMED,
		}

	if existed:
		doc = frappe.get_doc("Planning Release Consumption Record", PKGCONSUME_CODE)
		for fieldname in _REPAIRABLE_CONSUMPTION_FIELDS:
			doc.set(fieldname, values[fieldname])
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		action = "repaired"
	else:
		doc = frappe.get_doc(
			{"doctype": "Planning Release Consumption Record", **values}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	_cleanup_orphan_consumption_records()
	sync_master_release_consumed_overlay()
	_sync_package_consumed_fields()

	return {
		"action": action,
		"consumption_code": PKGCONSUME_CODE,
		"tender_code": TENDER_CODE,
		"status": PKG_CONSUMED,
	}
