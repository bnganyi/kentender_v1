"""Planning usage projection (NDS-CHG-001 v1.1 §4.7, §7.2, §8.2).

Usage is `Not included`, `Fully included` or — since PLN-CHG-001 v1.12 §4.4 —
`Not proceeding` (the department recorded in its departmental plan that it is
not pursuing the accepted Need this financial year, with a reason).
`Partially included` is removed by §1.1 and forbidden by §17, along with any
partial Need allocation or Planning quantity override (NDS-AC-014, NDS-AC-015).

Usage is *not* lifecycle state and changes only from an idempotent Planning
projection event tied to an Active Plan (NDS-BR-014). Nothing here queries
Procurement Planning: the firm D1 boundary makes the event the only channel,
and Planning publishes `NeedPlanningUsageChanged.v1` when an Active Plan starts
or stops representing an accepted Need version (§7.2).
"""

from __future__ import annotations

from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.departmental_needs.constants import (
	REVISION_CONTENT_FIELDS,
	REVISION_SUPERSEDED,
	ROLE_PROCUREMENT_PLANNER,
	USAGE_FULL,
	USAGE_NOT_INCLUDED,
	USAGE_NOT_PROCEEDING,
	USAGE_VALUES,
)
from kentender_procurement.departmental_needs.errors import fail
from kentender_procurement.departmental_needs.services.permissions import (
	actor,
	in_scope,
	is_administrative,
	require_view,
)


def _projection(accepted_revision: str) -> dict[str, Any] | None:
	if not accepted_revision:
		return None
	row = frappe.db.get_value(
		"Need Planning Usage Projection",
		cstr(accepted_revision),
		["name", "usage", "active_plan", "active_plan_item", "not_proceeding_reason", "source_event_id", "source_event_time"],
		as_dict=True,
	)
	return dict(row) if row else None


def planning_usage(need: str) -> str:
	"""The current accepted version's usage, defaulting to `Not included`.

	A Need with no projection has never been reported by Planning, which is
	exactly `Not included` — the §14.3 design-clock value for all four seeded
	Needs.
	"""
	accepted_revision = frappe.db.get_value("Departmental Need", need, "current_accepted_revision")
	if not accepted_revision:
		return USAGE_NOT_INCLUDED
	row = _projection(accepted_revision)
	return cstr(row["usage"]) if row else USAGE_NOT_INCLUDED


def planning_usage_detail(need: str, accepted_revision: str = "") -> dict[str, Any]:
	"""Usage plus the Plan references that support **View Plan Item** (§4.7)."""
	version = cstr(accepted_revision) or cstr(
		frappe.db.get_value("Departmental Need", need, "current_accepted_revision") or ""
	)
	row = _projection(version) or {}
	return {
		"need": cstr(need),
		"accepted_revision": version,
		# §11.8A NONE / NDS11-AC-071 — a Need Planning has never reported on is
		# distinct from one confirmed `Not included`; `usage` still defaults to
		# `Not included` for callers that only need the display value (the
		# workspace table's status pill), but `recorded` tells the detail
		# screen which case it actually is.
		"recorded": bool(row),
		"usage": cstr(row.get("usage") or USAGE_NOT_INCLUDED),
		"active_plan": cstr(row.get("active_plan") or ""),
		"active_plan_item": cstr(row.get("active_plan_item") or ""),
		"not_proceeding_reason": cstr(row.get("not_proceeding_reason") or ""),
		"source_event_id": cstr(row.get("source_event_id") or ""),
	}


def older_revision_usage(need: str, current_accepted_revision: str) -> dict[str, Any] | None:
	"""§11.8A OLDER — when the Need's current accepted revision has never
	itself been projected by Planning, the current annual plan may still be
	using an *earlier* accepted (now superseded) revision's inclusion. Walks
	revisions previously accepted for this Need, most recent first, and
	returns the first one Planning actually reported as `Fully included`.

	This never changes the current revision's own `Not included` status
	(§11.8A is explicit the two-row section keeps reporting the current
	revision plainly) — it is a separate supplementary fact for the "current
	annual plan still uses the previously accepted details" disclosure.
	"""
	if not current_accepted_revision or _projection(current_accepted_revision):
		return None
	prior_revisions = frappe.get_all(
		"Departmental Need Revision",
		filters={"departmental_need": need, "revision_status": REVISION_SUPERSEDED},
		fields=["name", "revision_number", *REVISION_CONTENT_FIELDS],
		order_by="revision_number desc",
	)
	for row in prior_revisions:
		projection = _projection(row.name)
		if projection and cstr(projection.get("usage")) == USAGE_FULL:
			return {
				"revision": row.name,
				"revision_number": row.revision_number,
				"required_by_date": str(row.required_by_date or ""),
				"active_plan": cstr(projection.get("active_plan") or ""),
				"active_plan_item": cstr(projection.get("active_plan_item") or ""),
				# §11.8A "View earlier requirement" — the older revision's own
				# six content facts, not the current revision's.
				"content": {field: row.get(field) for field in REVISION_CONTENT_FIELDS},
			}
	return None


def planning_status_for_need(need: str, user: str | None = None) -> dict[str, Any]:
	"""§11.8A's dedicated Planning-status re-check — separate from
	`get_departmental_need()`'s atomic payload so the client can revalidate
	this section independently (REFRESHING while in flight, UNAVAILABLE if
	this call itself fails — a real exception here, e.g. a transient DB
	error, is left to propagate to the caller rather than swallowed).

	Same §9 view authorisation as `get_departmental_need()` — this reads the
	same protected record, just a narrower slice of it.
	"""
	principal = actor(user)
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	doc = frappe.get_doc("Departmental Need", need)
	require_view(doc, principal)
	current_accepted_revision = cstr(doc.current_accepted_revision or "")
	return {
		"need": cstr(need),
		"planning_usage": planning_usage_detail(need, current_accepted_revision),
		"planning_disposition": planning_disposition_detail(need),
		"older_usage": older_revision_usage(need, current_accepted_revision),
		"checked_at": cstr(now_datetime()),
	}


def project_planning_usage(
	*,
	departmental_need: str,
	accepted_revision: str,
	usage: str,
	source_event_id: str,
	source_event_time: str | None = None,
	active_plan: str = "",
	active_plan_item: str = "",
	not_proceeding_reason: str = "",
	user: str | None = None,
) -> dict[str, Any]:
	"""§8.2 `project_need_planning_usage` — accept one ordered Planning event.

	Idempotent on `source_event_id` and ordered on `source_event_time`, so a
	replayed event is a no-op and a late-arriving older event cannot overwrite a
	newer projection (§4.7).
	"""
	principal = actor(user)
	# The event is Planning's to publish; §6 gives no other role this
	# authority. Procurement Planner is Site-wide (AUTH-ADR-001 v1.6 §4.4),
	# so the Organisation Unit passed to the scope check is immaterial.
	if not (
		in_scope(principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="")
		or is_administrative(principal)
	):
		fail("NDS_SCOPE_DENIED", "Only Procurement Planning may project Need planning usage.")
	usage_value = cstr(usage).strip()
	if usage_value not in USAGE_VALUES:
		fail("NDS_FIELD_REQUIRED", f"Usage must be one of: {', '.join(sorted(USAGE_VALUES))}.")
	reason_value = cstr(not_proceeding_reason).strip() if usage_value == USAGE_NOT_PROCEEDING else ""
	if usage_value == USAGE_NOT_PROCEEDING and not reason_value:
		fail("NDS_FIELD_REQUIRED", "A not-proceeding outcome carries the department's reason.")
	event_id = cstr(source_event_id).strip()
	if not event_id:
		fail("NDS_FIELD_REQUIRED", "A source event identifier is required.")
	need = cstr(departmental_need).strip()
	version = cstr(accepted_revision).strip()
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	occurred = source_event_time or now_datetime()

	frappe.db.sql(
		"select name from `tabNeed Planning Usage Projection` where name=%s for update", version
	)
	existing = _projection(version)
	if existing:
		if cstr(existing["source_event_id"]) == event_id:
			return {"ok": True, "idempotent": True, **planning_usage_detail(need, version)}
		if existing["source_event_time"] and str(occurred) < str(existing["source_event_time"]):
			# Out-of-order delivery: the newer projection stands.
			return {"ok": True, "idempotent": True, "superseded": True, **planning_usage_detail(need, version)}
		doc = frappe.get_doc("Need Planning Usage Projection", version)
		doc.update(
			{
				"usage": usage_value,
				"active_plan": cstr(active_plan),
				"active_plan_item": cstr(active_plan_item),
				"not_proceeding_reason": reason_value,
				"source_event_id": event_id,
				"source_event_time": occurred,
			}
		)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc(
			{
				"doctype": "Need Planning Usage Projection",
				"departmental_need": need,
				"accepted_revision": version,
				"usage": usage_value,
				"active_plan": cstr(active_plan),
				"active_plan_item": cstr(active_plan_item),
				"not_proceeding_reason": reason_value,
				"source_event_id": event_id,
				"source_event_time": occurred,
			}
		).insert(ignore_permissions=True)
	return {"ok": True, "idempotent": False, **planning_usage_detail(need, version)}


def is_actively_included(accepted_revision: str) -> bool:
	"""Whether an Active Plan currently represents this exact version (NDS-BR-016)."""
	row = _projection(accepted_revision)
	return bool(row and cstr(row["usage"]) == USAGE_FULL)



# --------------------------------------------------------------------------
# PLN-CHG-001 v1.18 §5.1.4 / §7.3 — `NeedPlanningDispositionChanged.v1`
# (NDS-CHG-001 v1.11 is owed: NDS FOLLOW_UPS §FU-07). Planning emits it only
# after a departmental submission is *accepted*; it records the department's
# certified disposition of one exact Need revision in one exact Submission.
# It is separate from the usage projection above: a DPP exclusion never
# clears an existing Active-plan dependency (v1.18 §5.1.4).
# --------------------------------------------------------------------------

DISPOSITION_PROCEEDING = "Proceeding"
DISPOSITION_NOT_PROCEEDING = "Not proceeding"
DISPOSITION_VALUES = frozenset({DISPOSITION_PROCEEDING, DISPOSITION_NOT_PROCEEDING})
DISPOSITION_DOCTYPE = "Need Planning Disposition Projection"


def _disposition_rows(need: str) -> list[dict[str, Any]]:
	return frappe.get_all(
		DISPOSITION_DOCTYPE,
		filters={"departmental_need": need},
		fields=[
			"name", "need_revision", "dpp_submission", "disposition", "reason", "actor",
			"decision_at", "source_event_id", "producer_sequence",
		],
		order_by="producer_sequence desc, decision_at desc, creation desc",
	)


def planning_disposition_detail(need: str) -> dict[str, Any]:
	"""The latest accepted Planning disposition of a Need, as Planning
	information for the Need's readers (§4.7 display; no lifecycle effect)."""
	rows = _disposition_rows(cstr(need))
	if not rows:
		return {"need": cstr(need), "recorded": False, "disposition": "", "reason": "", "dpp_submission": "", "need_revision": "", "actor": "", "actor_label": "", "decision_at": "", "history": []}
	latest = rows[0]
	return {
		"need": cstr(need),
		"recorded": True,
		"disposition": cstr(latest["disposition"]),
		"reason": cstr(latest["reason"] or ""),
		"dpp_submission": cstr(latest["dpp_submission"]),
		"need_revision": cstr(latest["need_revision"]),
		"actor": cstr(latest["actor"] or ""),
		"actor_label": (frappe.db.get_value("User", latest["actor"], "full_name") or latest["actor"]) if latest["actor"] else "",
		"decision_at": str(latest["decision_at"] or ""),
		"source_event_id": cstr(latest["source_event_id"]),
		"history": [
			{
				"need_revision": r["need_revision"],
				"dpp_submission": r["dpp_submission"],
				"disposition": r["disposition"],
				"reason": r["reason"] or "",
				"decision_at": str(r["decision_at"] or ""),
				"producer_sequence": int(r["producer_sequence"] or 0),
			}
			for r in rows
		],
	}


actor_of = actor


def project_planning_disposition(
	*,
	departmental_need: str,
	need_revision: str,
	dpp_submission: str,
	disposition: str,
	source_event_id: str,
	producer_sequence: int,
	reason: str = "",
	actor: str = "",
	decision_at: str | None = None,
	user: str | None = None,
) -> dict[str, Any]:
	"""Accept one `NeedPlanningDispositionChanged.v1` event. Idempotent on
	`source_event_id`; ordered per Need on `producer_sequence` (an older event
	arriving late cannot overwrite a newer disposition). Only Procurement
	Planning (or an administrative principal) may project it."""
	principal = actor_of(user)
	if not (in_scope(principal, business_role=ROLE_PROCUREMENT_PLANNER, organisation_unit="") or is_administrative(principal)):
		fail("NDS_SCOPE_DENIED", "Only Procurement Planning may project Need planning dispositions.")
	value = cstr(disposition).strip()
	if value not in DISPOSITION_VALUES:
		fail("NDS_FIELD_REQUIRED", f"Disposition must be one of: {', '.join(sorted(DISPOSITION_VALUES))}.")
	reason_value = cstr(reason).strip() if value == DISPOSITION_NOT_PROCEEDING else ""
	if value == DISPOSITION_NOT_PROCEEDING and not (20 <= len(reason_value) <= 500):
		fail("NDS_FIELD_REQUIRED", "A not-proceeding disposition carries the department's reason (20–500 characters).")
	event_id = cstr(source_event_id).strip()
	if not event_id:
		fail("NDS_FIELD_REQUIRED", "A source event identifier is required.")
	need = cstr(departmental_need).strip()
	revision = cstr(need_revision).strip()
	submission = cstr(dpp_submission).strip()
	if not frappe.db.exists("Departmental Need", need):
		fail("NDS_SCOPE_DENIED", "Departmental Need not found.")
	if not revision or not submission:
		fail("NDS_FIELD_REQUIRED", "The exact Need revision and departmental Submission are required.")
	sequence = int(producer_sequence or 0)
	occurred = decision_at or now_datetime()

	frappe.db.sql("select name from `tabDepartmental Need` where name=%s for update", need)
	if frappe.db.exists(DISPOSITION_DOCTYPE, {"source_event_id": event_id}):
		return {"ok": True, "idempotent": True, **planning_disposition_detail(need)}
	key = f"{revision}::{submission}"
	existing = frappe.db.get_value(DISPOSITION_DOCTYPE, {"disposition_key": key}, ["name", "producer_sequence"], as_dict=True)
	if existing and int(existing.producer_sequence or 0) >= sequence:
		return {"ok": True, "idempotent": True, "superseded": True, **planning_disposition_detail(need)}
	values = {
		"departmental_need": need,
		"need_revision": revision,
		"dpp_submission": submission,
		"disposition_key": key,
		"disposition": value,
		"reason": reason_value,
		"actor": cstr(actor) or principal,
		"decision_at": occurred,
		"source_event_id": event_id,
		"producer_sequence": sequence,
	}
	if existing:
		doc = frappe.get_doc(DISPOSITION_DOCTYPE, existing.name)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": DISPOSITION_DOCTYPE, **values}).insert(ignore_permissions=True)
	return {"ok": True, "idempotent": False, **planning_disposition_detail(need)}
