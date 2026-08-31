# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §5.2/§7.1/§8.2 — Publication, Active and successor
(Slice G).

`PublishAnnualPlan` is a system action, never a business-role command
(§11.15/§12.11): it runs automatically at the end of `ApproveAnnualPlan`
against the one `KenTender Annual Plan Publication Sandbox` adapter, which
always acknowledges — no external destination exists to actually integrate
with in MVP-1, and the sandbox exists so the idempotent-retry mechanics
(§12.11, System Manager only) are real even though the happy path never
needs them. Only an acknowledged attempt activates the Version (invariant
16); activation supersedes the predecessor, releases the unconverted
remainder of every removed item's reservation (invariant 22) and publishes
`NeedPlanningUsageChanged.v1` for every Need-origin source that starts or
stops being represented (§7.1) — the outbound half of the Needs handoff
Phase 2 only wired the read side of.
"""

from __future__ import annotations

import hashlib
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	budget_gateway,
	envelope,
	references,
)
from kentender_procurement.procurement_planning.services.plan_governance import (
	_copy_version_content,
	_next_plan_version_number,
)
from kentender_procurement.procurement_planning.services.plan_workbench import (
	_item_doc_name,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_PROCUREMENT_PLANNER,
)

DESTINATION_ADAPTER = "KenTender Annual Plan Publication Sandbox"


def _authorise_planner(actor: str, procuring_entity: str) -> None:
	authority.require_scope(actor, roles=(ROLE_PROCUREMENT_PLANNER,), procuring_entity=procuring_entity)


def _ensure_destination() -> str:
	existing = frappe.db.get_value(
		"Annual Plan Publication Destination", {"adapter": DESTINATION_ADAPTER, "active": 1}
	)
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "Annual Plan Publication Destination",
			"destination_id": "PLN-SANDBOX-01",
			"title": "KenTender Annual Plan Publication Sandbox",
			"adapter": DESTINATION_ADAPTER,
			"active": 1,
		}
	).insert(ignore_permissions=True)
	return doc.name


def _transmit(payload_hash: str) -> tuple[str, str]:
	"""The sandbox adapter: always acknowledges the exact approved payload
	immediately. Tests patch this to prove the Failed/Indeterminate retry
	path (§12.11) without a real external destination to fail against."""
	return "Acknowledged", f"ACK-{payload_hash[:16]}"


def _publish_usage_events(version, plan, *, event_suffix: str) -> None:
	"""§7.1 `NeedPlanningUsageChanged.v1` — "Fully included" for every
	Need-origin source in the now-Active version, "Not included" for every
	Need-origin source a Removed-in-successor item drops."""
	from kentender_procurement.departmental_needs.services import usage as needs_usage

	active_items = frappe.get_all(
		"Annual Plan Item", filters={"plan_version": version.name, "item_state": "Active"},
		fields=["name", "plan_item_id"],
	)
	items_by_name = {i.name: i.plan_item_id for i in active_items}
	included = frappe.get_all(
		"Plan Source Allocation",
		filters={
			"plan_item": ("in", list(items_by_name) or ("",)),
			"source_origin": "Accepted Departmental Need", "allocation_state": "Active",
		},
		fields=["plan_item", "need", "need_version"],
	)
	for row in included:
		needs_usage.project_planning_usage(
			departmental_need=row.need, accepted_version=row.need_version, usage="Fully included",
			source_event_id=f"{event_suffix}:{row.need_version}:included",
			source_event_time=now_datetime(), active_plan=plan.plan_reference,
			active_plan_item=items_by_name.get(row.plan_item, ""), user="Administrator",
		)

	removed_items = frappe.get_all(
		"Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"},
		pluck="name",
	)
	dropped = frappe.get_all(
		"Plan Source Allocation",
		filters={"plan_item": ("in", removed_items or ("",)), "source_origin": "Accepted Departmental Need"},
		fields=["need", "need_version"],
	)
	for row in dropped:
		needs_usage.project_planning_usage(
			departmental_need=row.need, accepted_version=row.need_version, usage="Not included",
			source_event_id=f"{event_suffix}:{row.need_version}:removed",
			source_event_time=now_datetime(), user="Administrator",
		)


def _activate_version(version, plan) -> None:
	"""§5.2/§5.3 invariants 16-18/21-22 — the controlled activation process:
	supersede the predecessor, mark this Version's items Active, release the
	unconverted remainder for every item this successor removed, and update
	the one Active pointer."""
	predecessor = cstr(plan.active_version)
	if predecessor and predecessor != version.name:
		removed_ids = frappe.get_all(
			"Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"},
			pluck="plan_item_id",
		)
		if removed_ids:
			frappe.db.set_value(
				"Annual Plan Item",
				{"plan_version": predecessor, "plan_item_id": ("in", removed_ids)},
				"item_state", "Superseded", update_modified=False,
			)
			removed_item_names = frappe.get_all(
				"Annual Plan Item", filters={"plan_version": version.name, "item_state": "Removed in successor"},
				pluck="name",
			)
			# The predecessor's own copy of the reservation reference (its
			# `plan_item` names the Superseded item above, not this
			# successor's copy — §5.2's _copy_version_content gives every
			# carried-over item its own new reference row onto the same
			# underlying reservation) must be marked released too, or its
			# history silently disagrees with the money actually being
			# freed. Release each distinct reservation once, then stamp
			# every reference row — predecessor's and successor's alike —
			# that names it.
			reservations = sorted(set(
				frappe.get_all(
					"Plan Reservation Reference", filters={"plan_item": ("in", removed_item_names)},
					pluck="reservation",
				)
			))
			if reservations:
				correlation_id = f"activate:{version.name}"
				released = budget_gateway.release_planning_reservations(
					reservation_refs=[{"reservation": r} for r in reservations],
					correlation_id=correlation_id, event_type="SuccessorActivated",
				)
				release_code_by_reservation = {
					r: outcome["reservation"]["reservation_code"] for r, outcome in zip(reservations, released)
				}
				all_refs = frappe.get_all(
					"Plan Reservation Reference", filters={"reservation": ("in", reservations)},
					fields=["name", "reservation"],
				)
				for ref in all_refs:
					frappe.db.set_value(
						"Plan Reservation Reference", ref.name,
						{
							"release_reference": release_code_by_reservation[ref.reservation],
							"release_correlation": correlation_id,
						},
						update_modified=False,
					)
			frappe.db.set_value(
				"Plan Source Allocation",
				{"plan_item": ("in", removed_item_names)}, "allocation_state", "Removed in successor",
				update_modified=False,
			)
		frappe.db.set_value("Annual Plan Version", predecessor, "version_status", "Superseded", update_modified=False)

	frappe.db.set_value(
		"Annual Plan Item", {"plan_version": version.name, "item_state": "Draft"}, "item_state", "Active",
		update_modified=False,
	)
	frappe.db.set_value(
		"Plan Source Allocation", {"plan_version": version.name, "allocation_state": "Draft"},
		"allocation_state", "Active", update_modified=False,
	)
	envelope.bump(version, version_status="Active", activated_at=now_datetime())
	frappe.db.set_value(
		"Annual Plan", plan.name, {"active_version": version.name, "open_successor_version": ""},
		update_modified=False,
	)
	_publish_usage_events(version, plan, event_suffix=f"activate:{version.name}")


def publish_annual_plan(*, plan_version: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§8.2/§12.11 — a system action; called automatically at the end of
	`ApproveAnnualPlan`, never a standalone business command."""
	actor = cstr(user or frappe.session.user)
	version = envelope.locked("Annual Plan Version", plan_version)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	plan = frappe.get_doc("Annual Plan", version.annual_plan)

	destination = _ensure_destination()
	payload_hash = hashlib.sha256(cstr(version.submitted_snapshot).encode()).hexdigest()
	attempt_number = frappe.db.count("Annual Plan Publication", {"plan_version": version.name}) + 1
	result, external_reference = _transmit(payload_hash)
	publication = frappe.get_doc(
		{
			"doctype": "Annual Plan Publication",
			"publication_reference": references.publication_reference(version.name, attempt_number),
			"plan_version": version.name,
			"destination": destination,
			"attempt_number": attempt_number,
			"result": result,
			"payload_hash": payload_hash,
			"external_reference": external_reference if result == "Acknowledged" else None,
			"attempted_at": now_datetime(),
			"acknowledged_at": now_datetime() if result == "Acknowledged" else None,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)

	if result == "Acknowledged":
		_activate_version(version, plan)
	else:
		envelope.bump(version, version_status="Publication failed")

	result_dict = {
		"ok": True, "idempotent": False, "action": "published", "publication": publication.name,
		"result": result,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="PublishAnnualPlan", payload={"plan_version": plan_version},
		result=result_dict, document_type="Annual Plan Publication", document_name=publication.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result_dict


def retry_publication(*, publication: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§11.15/§12.11 — System Manager only; retries the SAME approved
	payload, edits nothing, creates no new approval."""
	actor = cstr(user or frappe.session.user)
	if actor != "Administrator" and "System Manager" not in frappe.get_roles(actor):
		authority.not_found()
	if not publication or not frappe.db.exists("Annual Plan Publication", publication):
		authority.not_found()
	prior = frappe.get_doc("Annual Plan Publication", publication)
	version = envelope.locked("Annual Plan Version", prior.plan_version)
	if version.version_status != "Publication failed":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	plan = frappe.get_doc("Annual Plan", version.annual_plan)

	attempt_number = frappe.db.count("Annual Plan Publication", {"plan_version": version.name}) + 1
	result, external_reference = _transmit(prior.payload_hash)
	publication_doc = frappe.get_doc(
		{
			"doctype": "Annual Plan Publication",
			"publication_reference": references.publication_reference(version.name, attempt_number),
			"plan_version": version.name,
			"destination": prior.destination,
			"attempt_number": attempt_number,
			"result": result,
			"payload_hash": prior.payload_hash,
			"external_reference": external_reference if result == "Acknowledged" else None,
			"attempted_at": now_datetime(),
			"acknowledged_at": now_datetime() if result == "Acknowledged" else None,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	if result == "Acknowledged":
		_activate_version(version, plan)
	result_dict = {
		"ok": True, "idempotent": False, "action": "retried", "publication": publication_doc.name,
		"result": result,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RetryPublication", payload={"publication": publication},
		result=result_dict, document_type="Annual Plan Publication", document_name=publication_doc.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result_dict


def begin_plan_update(*, plan_reference: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§8.2/§5.2 — create/reuse the sole Draft successor from the Active
	Version, copying its exact items (invariant 22: unchanged lineage is
	preserved until an acknowledged successor changes it)."""
	actor = cstr(user or frappe.session.user)
	payload = {"plan_reference": plan_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	if not name:
		authority.not_found()
	plan = envelope.locked("Annual Plan", name)
	_authorise_planner(actor, plan.procuring_entity)
	if not plan.active_version:
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	if plan.open_successor_version:
		existing_status = frappe.db.get_value("Annual Plan Version", plan.open_successor_version, "version_status")
		if existing_status not in ("Active", "Superseded", "Cancelled"):
			result = {
				"ok": True, "idempotent": True, "action": "reused",
				"successor_version": plan.open_successor_version,
			}
			envelope.record_command(
				idempotency_key=idempotency_key, command="BeginPlanUpdate", payload=payload,
				result=result, document_type="Annual Plan Version", document_name=plan.open_successor_version,
				actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
			)
			return result

	active_version = frappe.get_doc("Annual Plan Version", plan.active_version)
	successor = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V{_next_plan_version_number(plan.name)}",
			"annual_plan": plan.name,
			"version_number": _next_plan_version_number(plan.name),
			"based_on_version": active_version.name,
			"version_status": "Draft",
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	_copy_version_content(active_version.name, successor, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", successor.name, update_modified=False)

	result = {"ok": True, "idempotent": False, "action": "created", "successor_version": successor.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="BeginPlanUpdate", payload=payload,
		result=result, document_type="Annual Plan Version", document_name=successor.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def _no_downstream_use(item) -> bool:
	"""§12.12's fresh downstream check (drawdown, Tender handoff, commitment,
	contract) — the check point Phase 10's `GetRequisitionEligiblePlanItem.v2`
	and this repo's out-of-scope Requisition/Tender consumers would inform.
	None of them exist in this repo yet (§2.1 scope exclusions), so there is
	nothing to find and this always permits removal today; the call site
	never assumes that in advance."""
	return True


def remove_plan_item_in_successor(
	*, plan_item: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§8.2/§12.12 — propose whole-item removal only after fresh downstream
	checks show no drawdown, Tender handoff, commitment or contract. MVP-1
	has no consuming Requisition/Tender module in this repo yet (§2.1 scope
	exclusions) — the check point exists and is called every time, but it
	has nothing to find until one of those modules exists; it always
	permits removal today."""
	actor = cstr(user or frappe.session.user)
	payload = {"plan_item": plan_item}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	item = envelope.locked("Annual Plan Item", _item_doc_name(plan_item))
	version = frappe.get_doc("Annual Plan Version", item.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	_authorise_planner(actor, plan.procuring_entity)
	if version.version_status != "Draft" or not version.based_on_version:
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(item, expected_record_version)
	if item.item_state != "Draft":
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	if not _no_downstream_use(item):
		fail(
			"PLN_REMOVAL_BLOCKED",
			"This Active Plan Item has downstream use and cannot be removed through Planning.",
		)

	envelope.bump(item, item_state="Removed in successor")
	result = {"ok": True, "idempotent": False, "action": "removed", "plan_item": item.plan_item_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RemovePlanItemInSuccessor", payload=payload,
		result=result, document_type="Annual Plan Item", document_name=item.name,
		actor=actor, fixture_namespace=cstr(item.fixture_namespace),
	)
	return result


def cancel_plan_update(
	*, plan_reference: str, expected_record_version, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	"""§8.2/§5.3 invariant 21 — release only the successor's OWN reservations
	(never a reservation the Active predecessor's own allocation still
	references) and leave the Active Version untouched."""
	actor = cstr(user or frappe.session.user)
	payload = {"plan_reference": plan_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay

	name = frappe.db.get_value("Annual Plan", {"plan_reference": plan_reference})
	if not name:
		authority.not_found()
	plan = envelope.locked("Annual Plan", name)
	_authorise_planner(actor, plan.procuring_entity)
	successor_name = cstr(plan.open_successor_version)
	if not successor_name:
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	successor = frappe.get_doc("Annual Plan Version", successor_name)
	if successor.version_status != "Draft" or not successor.based_on_version:
		fail("PLN_STALE_WRITE", "Another user changed this record. Reload before continuing.")
	envelope.check_record_version(successor, expected_record_version)

	items = frappe.get_all("Annual Plan Item", filters={"plan_version": successor.name}, pluck="name")
	refs = frappe.get_all(
		"Plan Reservation Reference", filters={"plan_item": ("in", items or ("",))},
		fields=["name", "reservation"],
	)
	# `pluck` already returns bare values, not row objects — a `.reservation`
	# attribute access here was the previously untested bug (there was no
	# real caller of CancelPlanUpdate before this phase's tests).
	other_refs = set(
		frappe.get_all(
			"Plan Reservation Reference",
			filters={"reservation": ("in", [r.reservation for r in refs] or ("",)), "plan_item": ("not in", items or ("",))},
			pluck="reservation",
		)
	)
	successor_only = [r for r in refs if r.reservation not in other_refs]
	if successor_only:
		correlation_id = f"cancel:{successor.name}:{idempotency_key}"
		released = budget_gateway.release_planning_reservations(
			reservation_refs=[{"reservation": r.reservation} for r in successor_only],
			correlation_id=correlation_id, event_type="PlanUpdateCancelled",
		)
		for ref, outcome in zip(successor_only, released):
			frappe.db.set_value(
				"Plan Reservation Reference", ref.name,
				{
					"release_reference": outcome["reservation"]["reservation_code"],
					"release_correlation": correlation_id,
				},
				update_modified=False,
			)

	envelope.bump(successor, version_status="Cancelled")
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", "", update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "cancelled", "successor_version": successor.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="CancelPlanUpdate", payload=payload,
		result=result, document_type="Annual Plan Version", document_name=successor.name,
		actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
