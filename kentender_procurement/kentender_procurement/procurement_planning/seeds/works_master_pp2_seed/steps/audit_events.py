# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Create/validate ordered Planning Audit Events for WORKS master seed (spec §17)."""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import get_datetime

from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.constants import (
	CHECKPOINT_ORDER,
	DEFAULT_CHECKPOINT,
	JOURNEY_CODE,
	METHDEC_REVIEWER_EMAIL,
	METHDEC_REVIEWER_USER_CODE,
	PLAN_APPROVER_EMAIL,
	PLAN_APPROVER_USER_CODE,
	PLAN_CODE,
	PLAN_CREATOR_EMAIL,
	PLAN_CREATOR_USER_CODE,
	PKGCONSUME_CONSUMED_BY_EMAIL,
	PKGCONSUME_CONSUMED_BY_USER_CODE,
	SEED_ACTOR,
	SEED_SYSTEM_ACTOR_EMAIL,
	SEED_SYSTEM_ACTOR_USER_CODE,
	master_planning_audit_events_for_checkpoint,
)
from kentender_procurement.procurement_planning.seeds.works_master_pp2_seed.steps.plan import (
	_ensure_seed_user,
)

_REPAIRABLE_AUDIT_EVENT_FIELDS = (
	"event_code",
	"event_type",
	"object_type",
	"object_code",
	"actor",
	"occurred_at",
	"from_state",
	"to_state",
	"reason",
	"evidence_ref",
	"journey_code",
	"is_master_seed",
)

_ACTOR_PROFILES: dict[str, tuple[str, str]] = {
	PLAN_CREATOR_USER_CODE: (PLAN_CREATOR_EMAIL, "Procurement Planner MOH"),
	METHDEC_REVIEWER_USER_CODE: (METHDEC_REVIEWER_EMAIL, "Planning Reviewer MOH"),
	PLAN_APPROVER_USER_CODE: (PLAN_APPROVER_EMAIL, "Planning Authority MOH"),
	PKGCONSUME_CONSUMED_BY_USER_CODE: (PKGCONSUME_CONSUMED_BY_EMAIL, "Procurement Officer MOH"),
}


def _checkpoint_index(checkpoint: str) -> int:
	cp = (checkpoint or DEFAULT_CHECKPOINT).strip().upper()
	try:
		return CHECKPOINT_ORDER.index(cp)
	except ValueError:
		frappe.throw(f"Unsupported checkpoint: {checkpoint}", title="INVALID_CHECKPOINT")


def _ensure_system_actor() -> str:
	if frappe.db.exists("User", SEED_SYSTEM_ACTOR_USER_CODE):
		return SEED_SYSTEM_ACTOR_USER_CODE
	by_username = frappe.db.get_value("User", {"username": SEED_SYSTEM_ACTOR_USER_CODE}, "name")
	if by_username:
		return by_username
	if frappe.db.exists("User", SEED_SYSTEM_ACTOR_EMAIL):
		frappe.db.set_value(
			"User",
			SEED_SYSTEM_ACTOR_EMAIL,
			{"enabled": 1, "username": SEED_SYSTEM_ACTOR_USER_CODE},
			update_modified=False,
		)
		return SEED_SYSTEM_ACTOR_EMAIL
	doc = frappe.get_doc(
		{
			"doctype": "User",
			"email": SEED_SYSTEM_ACTOR_EMAIL,
			"username": SEED_SYSTEM_ACTOR_USER_CODE,
			"first_name": "System",
			"full_name": "System",
			"enabled": 1,
			"user_type": "System User",
			"send_welcome_email": 0,
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	return doc.name


def _resolve_audit_actor(user_code: str) -> str:
	code = (user_code or "").strip()
	if code == SEED_SYSTEM_ACTOR_USER_CODE:
		return _ensure_system_actor()
	email, full_name = _ACTOR_PROFILES.get(code, ("", ""))
	if not email:
		frappe.throw(f"Unsupported audit actor code: {user_code}", title="INVALID_AUDIT_ACTOR")
	return _ensure_seed_user(email=email, user_code=code, full_name=full_name)


def _audit_seed_repair_allowed() -> bool:
	return bool(frappe.db.exists("Procurement Plan", PLAN_CODE))


def _strict_audit_event_values(*, spec_row: dict[str, Any], actor_user: str) -> dict[str, Any]:
	return {
		"event_code": spec_row["event_code"],
		"event_type": spec_row["event_type"],
		"object_type": spec_row["object_type"],
		"object_code": spec_row["object_code"],
		"actor": actor_user,
		"occurred_at": get_datetime(spec_row["occurred_at"]),
		"from_state": spec_row.get("from_state"),
		"to_state": spec_row.get("to_state"),
		"reason": None,
		"evidence_ref": spec_row["evidence_ref"],
		"journey_code": JOURNEY_CODE,
		"is_master_seed": 1,
	}


def _upsert_master_audit_event(*, event_code: str, values: dict[str, Any]) -> str:
	existed = bool(frappe.db.exists("Planning Audit Event", event_code))
	if existed:
		doc = frappe.get_doc("Planning Audit Event", event_code)
		for fieldname in _REPAIRABLE_AUDIT_EVENT_FIELDS:
			doc.set(fieldname, values[fieldname])
		doc.flags.ignore_pp_aud_append_only_override = True
		doc.flags.ignore_mandatory = True
		doc.save(ignore_permissions=True)
		return "repaired"
	doc = frappe.get_doc({"doctype": "Planning Audit Event", **values})
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_permissions=True)
	return "created"


def _cleanup_orphan_audit_events(*, allowed_codes: set[str]) -> None:
	for event_code in frappe.get_all(
		"Planning Audit Event",
		filters={"journey_code": JOURNEY_CODE, "is_master_seed": 1},
		pluck="name",
	):
		if event_code in allowed_codes:
			continue
		doc = frappe.get_doc("Planning Audit Event", event_code)
		doc.flags.ignore_pp_aud_allow_delete = True
		doc.delete(ignore_permissions=True)


def ensure_planning_audit_events(*, checkpoint: str = DEFAULT_CHECKPOINT, actor: str = SEED_ACTOR) -> dict[str, Any]:
	del actor
	if not frappe.db.exists("DocType", "Planning Audit Event"):
		return {"action": "skipped", "event_codes": []}

	idx = _checkpoint_index(checkpoint)
	if idx < _checkpoint_index("INCLUDED_IN_PLAN"):
		return {"action": "skipped", "event_codes": []}

	if not _audit_seed_repair_allowed():
		return {"action": "blocked", "event_codes": []}

	spec_rows = master_planning_audit_events_for_checkpoint(checkpoint)
	allowed_codes = {row["event_code"] for row in spec_rows}
	actions: list[str] = []
	event_codes: list[str] = []

	for spec_row in spec_rows:
		actor_user = _resolve_audit_actor(spec_row["actor_user_code"])
		values = _strict_audit_event_values(spec_row=spec_row, actor_user=actor_user)
		action = _upsert_master_audit_event(event_code=spec_row["event_code"], values=values)
		actions.append(action)
		event_codes.append(spec_row["event_code"])

	_cleanup_orphan_audit_events(allowed_codes=allowed_codes)

	return {
		"action": "repaired" if "repaired" in actions else ("created" if "created" in actions else "existing"),
		"event_codes": event_codes,
	}
