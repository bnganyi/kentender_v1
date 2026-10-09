# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.31 §5.5.2 / §7.2 — what approval commits, and the guarded
activation.

`commit_approved_plan` runs inside `ApproveAnnualPlan`'s own transaction: it
freezes the exact immutable content (`Approved Plan Snapshot`) and the
publication record (`Plan Publication`) whose manifest and hash identify the
generated document the Planner downloads and confirms. Nothing here reaches
outside the database and nothing is dispatched.

MVP 1 publication is manual (Project Owner instruction, 9 October 2026): the
Procurement Planner confirms Treasury submission and entity-website publication
(`publication_confirmation.confirm_plan_publication`), which then calls
`activate_plan_version` below. v1.30 and earlier had a post-commit worker with a
sandbox adapter, an authenticated acknowledgement, a technical retry and a
reconciliation, and the Head of Procurement Function's Publish; all of that is
retired (PLN-CHG-001 v1.31 §5.5.2.0). Existing attempts, acknowledgements and
intents stay as read-only history."""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, plan_finance, plan_json, plan_publication
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.write_family import planning_command

DESTINATION_ADAPTER = "Manual publication — Planner confirmation"


def _ensure_destination() -> str:
	"""`Plan Publication.destination` is required. MVP 1 has no external
	destination, so every publication points at the one manual record."""
	existing = frappe.db.get_value("Annual Plan Publication Destination", {"adapter": DESTINATION_ADAPTER, "active": 1})
	if existing:
		return existing
	return frappe.get_doc(
		{
			"doctype": "Annual Plan Publication Destination", "destination_id": "MOH-APP-MANUAL-v1",
			"title": "Entity website, recorded by the Planner", "adapter": DESTINATION_ADAPTER, "active": 1, "sandbox_outcome": "Acknowledge",
		}
	).insert(ignore_permissions=True).name


def commit_approved_plan(*, version, plan, decision, actor: str) -> dict[str, str]:
	"""§5.5.2 — get-or-create, keyed by the exact Version: a retried or
	duplicated `ApproveAnnualPlan` after a partial failure lands on the same
	snapshot and publication identifiers, never a second approved package."""
	existing_snapshot = frappe.db.get_value("Approved Plan Snapshot", {"plan_version": version.name}, "name")
	if existing_snapshot:
		snapshot = frappe.get_doc("Approved Plan Snapshot", existing_snapshot)
	else:
		content = plan_json.build_snapshot(version, plan)
		snapshot = frappe.get_doc(
			{
				"doctype": "Approved Plan Snapshot", "plan_version": version.name, "annual_plan": plan.name,
				"content": json.dumps(content, default=str), "evidence_index": json.dumps(content["evidence"]),
				"content_digest": plan_json.content_digest(content), "approval_decision": decision.name,
				"strategy_approval_snapshot": next((i.get("strategicObjectivePath") for i in content["items"] if i.get("strategicObjectivePath")), "") or "",
				"approved_at": now_datetime(), "fixture_namespace": cstr(version.fixture_namespace),
			}
		).insert(ignore_permissions=True)

	destination = _ensure_destination()
	publication_id = f"PUB-{version.name}"
	existing_publication = frappe.db.get_value("Plan Publication", {"publication_id": publication_id}, "name")
	if existing_publication:
		publication = frappe.get_doc("Plan Publication", existing_publication)
	else:
		payload = plan_json.build_public_payload(snapshot)
		payload["publicationId"] = publication_id
		package_hash = plan_json.content_digest(payload)
		publication = frappe.get_doc(
			{
				"doctype": "Plan Publication", "publication_id": publication_id, "snapshot": snapshot.name, "plan_version": version.name,
				"destination": destination, "schema_version": plan_json.SCHEMA_VERSION,
				"manifest": json.dumps(plan_json.manifest_for(payload, package_hash)), "package_hash": package_hash,
				"publication_state": "Pending", "record_version": 0, "fixture_namespace": cstr(version.fixture_namespace),
			}
		).insert(ignore_permissions=True)

	return {"snapshot": snapshot.name, "publication": publication.name}


def _active_hold(plan_version: str):
	return frappe.db.get_value("Plan Publication Hold", {"plan_version": plan_version, "hold_state": "Active"}, "name")


def _activation_blockers(version, plan) -> list[str]:
	"""§5.5.2.3 — sources, financial basis, locks/allowances and the
	predecessor compare-and-swap; never invents an Active predecessor."""
	from kentender_procurement.procurement_planning.services import plan_read, readiness

	reasons = []
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")}, pluck="name")
	for item_name in items:
		for allocation in readiness._allocations(item_name):
			if plan_read.source_correction_required(allocation.dpp_entry):
				reasons.append("source_correction_required")
				break
	if not plan_finance.funding_is_current(version):
		reasons.append("funding_not_current")
	# §5.4.4 / §5.5.2.3 predecessor CAS — `based_on_version` already carries the
	# explicit real Active predecessor through every successor and correction
	# copy (BeginPlanUpdate, ReturnPlanVersion, BeginHeldPlanCorrection); an
	# initial Plan expects none. Never invented here.
	if cstr(plan.active_version) != cstr(version.based_on_version):
		reasons.append("predecessor_changed")
	return reasons


@planning_command
def activate_plan_version(*, plan_version: str, idempotency_key: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `ActivatePlanVersion` — system; preserves the publication fact
	even when activation checks fail (`Published — activation held`, one
	governed correction successor permitted, never forced Active)."""
	actor = cstr(user or frappe.session.user or "Administrator")
	version = envelope.locked("Annual Plan Version", plan_version)
	# "Publication failed" is a valid starting state: a technical retry that
	# succeeds calls this exactly as the first attempt would.
	if version.version_status not in ("Approved — publication pending", "Publication failed", "Published — activation held"):
		return {"ok": True, "idempotent": True, "action": "already_settled", "version_status": version.version_status}
	plan = envelope.locked("Annual Plan", version.annual_plan)
	blockers = _activation_blockers(version, plan)
	if blockers:
		envelope.bump(version, version_status="Published — activation held")
		result = {"ok": True, "idempotent": False, "action": "activation_held", "blockers": blockers}
	else:
		plan_publication._activate_version(version, plan)
		result = {"ok": True, "idempotent": False, "action": "activated", "plan_version": version.name}
	if idempotency_key:
		envelope.record_command(
			idempotency_key=idempotency_key, command="ActivatePlanVersion", payload={"plan_version": plan_version}, result=result,
			document_type="Annual Plan Version", document_name=version.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
		)
	return result


@planning_command
def hold_plan_publication(*, plan_version: str, reason: str, hold_kind: str = "Detected invalidity", idempotency_key: str = "", user: str | None = None) -> dict[str, Any]:
	"""§7.2 `HoldPlanPublication` — a recorded control over transmission,
	never an unrecorded withdrawal of statutory approval."""
	from kentender_procurement.procurement_planning.services.planning_roles import ROLE_ACCOUNTING_OFFICER

	from kentender_core.services.authorization import is_technical

	actor = authz.actor(user)
	reason = " ".join(cstr(reason).split())
	payload = {"plan_version": plan_version, "reason": reason, "hold_kind": hold_kind}
	if idempotency_key:
		replay = envelope.replay_or_none(idempotency_key, payload)
		if replay:
			return replay
	if not (1 <= len(reason) <= 1000):
		fail("PLN_ENTRY_INCOMPLETE", "State the reason for the hold.", {"field": "reason"})
	if hold_kind not in ("Detected invalidity", "Accounting Officer correction request", "Withdrawal request"):
		fail("PLN_ENTRY_INCOMPLETE", "Unknown hold kind.", {"field": "hold_kind"})
	raised_by_service = ""
	if hold_kind in ("Accounting Officer correction request", "Withdrawal request"):
		authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	elif not is_technical(actor):
		authz.not_found()
	else:
		raised_by_service = "publication_pipeline"
	version = envelope.locked("Annual Plan Version", plan_version)
	existing = _active_hold(version.name)
	if existing:
		return {"ok": True, "idempotent": True, "action": "held", "hold": existing}
	publication_name = frappe.db.get_value("Plan Publication", {"plan_version": version.name}, "name")
	hold = frappe.get_doc(
		{
			"doctype": "Plan Publication Hold", "plan_version": version.name, "publication": publication_name, "hold_kind": hold_kind,
			"reason": reason, "raised_by": actor if not raised_by_service else None, "raised_by_service": raised_by_service,
			"raised_at": now_datetime(), "hold_state": "Active", "record_version": 0, "fixture_namespace": cstr(version.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	if publication_name:
		frappe.db.set_value("Publication Intent", {"publication": publication_name}, "hold", hold.name, update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "held", "hold": hold.name}
	if idempotency_key:
		envelope.record_command(
			idempotency_key=idempotency_key, command="HoldPlanPublication", payload=payload, result=result,
			document_type="Plan Publication Hold", document_name=hold.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
		)
	return result
