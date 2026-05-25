# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Record PKGREV-PKG-MOH-2026-001-001 (spec §13)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cint, get_datetime

from kentender_procurement.procurement_planning.pp2_constants import (
	PKG_APPROVED,
	PKG_CONSUMED,
	PKG_DRAFT,
	PKG_IN_REVIEW,
	PKG_RELEASED,
	PKG_RETURNED,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	JOURNEY_CODE,
	METHDEC_CODE,
	METHDEC_REVIEWER_EMAIL,
	METHDEC_REVIEWER_USER_CODE,
	PKG_CODE,
	PKGREV_AUDIT_EVENT_REF,
	PKGREV_CODE,
	PKGREV_DECIDED_AT,
	PKGREV_DECISION_REASON,
	PKGREV_FROM_STATE,
	PKGREV_TO_STATE,
	PKGRDY_CODE,
	SEED_ACTOR,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)

_REPAIRABLE_REVIEW_DECISION_FIELDS = (
	"review_decision_code",
	"package_code",
	"decision_type",
	"decided_by",
	"decided_at",
	"from_state",
	"to_state",
	"decision_reason",
	"required_correction",
	"readiness_code",
	"method_decision_code",
	"audit_event_ref",
	"is_master_seed",
)


def _review_seed_repair_allowed() -> bool:
	locked = cint(frappe.db.get_value("Procurement Package", PKG_CODE, "locked_after_release"))
	status = (frappe.db.get_value("Procurement Package", PKG_CODE, "status") or "").strip()
	return not locked and status not in (PKG_RELEASED, PKG_CONSUMED)


def _strict_review_decision_values(
	*,
	decided_by: str,
	readiness_code: str | None = None,
) -> dict[str, Any]:
	return {
		"review_decision_code": PKGREV_CODE,
		"package_code": PKG_CODE,
		"decision_type": "Approved",
		"decided_by": decided_by,
		"decided_at": get_datetime(PKGREV_DECIDED_AT),
		"from_state": PKGREV_FROM_STATE,
		"to_state": PKGREV_TO_STATE,
		"decision_reason": PKGREV_DECISION_REASON,
		"required_correction": None,
		"readiness_code": readiness_code,
		"method_decision_code": METHDEC_CODE,
		"audit_event_ref": PKGREV_AUDIT_EVENT_REF,
		"is_master_seed": 1,
	}


def _cleanup_orphan_review_decisions() -> None:
	for code in frappe.get_all(
		"Package Review Decision",
		filters={"package_code": PKG_CODE},
		pluck="review_decision_code",
	):
		if code != PKGREV_CODE:
			frappe.delete_doc("Package Review Decision", code, force=1)


def _ensure_package_in_review_if_needed() -> None:
	status = (frappe.db.get_value("Procurement Package", PKG_CODE, "status") or "").strip()
	if status in (PKG_DRAFT, PKG_RETURNED):
		frappe.db.set_value(
			"Procurement Package",
			PKG_CODE,
			"status",
			PKG_IN_REVIEW,
			update_modified=False,
		)


def _sync_package_review_fields(*, review_decision_code: str) -> None:
	frappe.db.set_value(
		"Procurement Package",
		PKG_CODE,
		{
			"status": PKG_APPROVED,
			"latest_review_code": review_decision_code,
			"workflow_reason": None,
		},
		update_modified=False,
	)


def _ensure_master_review_decision(*, actor: str) -> dict[str, Any]:
	del actor
	if not frappe.db.exists("Procurement Package", PKG_CODE):
		frappe.throw("Procurement Package not found.", title="MISSING_PACKAGE")

	_ensure_package_in_review_if_needed()

	decided_by = _ensure_seed_user(
		email=METHDEC_REVIEWER_EMAIL,
		user_code=METHDEC_REVIEWER_USER_CODE,
		full_name="Planning Reviewer MOH",
	)
	values = _strict_review_decision_values(decided_by=decided_by, readiness_code=None)
	existed = bool(frappe.db.exists("Package Review Decision", PKGREV_CODE))

	if existed:
		if _review_seed_repair_allowed():
			doc = frappe.get_doc("Package Review Decision", PKGREV_CODE)
			for fieldname in _REPAIRABLE_REVIEW_DECISION_FIELDS:
				doc.set(fieldname, values[fieldname])
			doc.flags.ignore_mandatory = True
			doc.save(ignore_permissions=True)
			action = "repaired"
		else:
			action = "existing"
	else:
		doc = frappe.get_doc({"doctype": "Package Review Decision", **values})
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		action = "created"

	if _review_seed_repair_allowed():
		_cleanup_orphan_review_decisions()
		_sync_package_review_fields(review_decision_code=PKGREV_CODE)

	return {
		"action": action,
		"review_decision_code": PKGREV_CODE,
	}


def sync_master_review_decision_links() -> dict[str, Any]:
	if not frappe.db.exists("Package Review Decision", PKGREV_CODE):
		return {"action": "missing", "review_decision_code": PKGREV_CODE}

	if not _review_seed_repair_allowed():
		return {"action": "existing", "review_decision_code": PKGREV_CODE}

	current_readiness, current_method = frappe.db.get_value(
		"Package Review Decision",
		PKGREV_CODE,
		("readiness_code", "method_decision_code"),
	)
	if (
		(current_readiness or "").strip() == PKGRDY_CODE
		and (current_method or "").strip() == METHDEC_CODE
	):
		return {"action": "existing", "review_decision_code": PKGREV_CODE}

	frappe.db.set_value(
		"Package Review Decision",
		PKGREV_CODE,
		{
			"readiness_code": PKGRDY_CODE if frappe.db.exists("Package Readiness Result", PKGRDY_CODE) else None,
			"method_decision_code": METHDEC_CODE,
			"is_master_seed": 1,
		},
		update_modified=False,
	)
	return {"action": "synced", "review_decision_code": PKGREV_CODE}


def ensure_master_review_decision(*, actor: str = SEED_ACTOR) -> dict[str, Any]:
	return _ensure_master_review_decision(actor=actor)
