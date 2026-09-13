# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.5.2 / §7.2 — the asynchronous publication pipeline
(plan D8, PLN18-209).

`commit_approved_plan` runs inside `ApproveAnnualPlan`'s own transaction: it
freezes the exact immutable content (`Approved Plan Snapshot`), a durable
publication record (`Plan Publication`) and dispatch intent
(`Publication Intent`) — nothing here reaches outside the database. External
transmission is `publish_annual_plan`, a system worker that would run
post-commit via `frappe.enqueue` in production; this bench runs no RQ worker,
so callers (tests, seeds) invoke it inline after the approving transaction
commits, exactly as `ApproveAnnualPlan` itself would enqueue it. Acknowledgement,
activation, reconciliation and retry are separate authenticated system
functions so a real external callback, a technical reconciliation job and a
technical retry are each their own auditable action — never a manufactured
success.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, plan_finance, plan_json, plan_publication
from kentender_procurement.procurement_planning.services import planning_authorization as authz

DESTINATION_ADAPTER = "KenTender Annual Plan Publication Sandbox"


def _ensure_destination() -> str:
	existing = frappe.db.get_value("Annual Plan Publication Destination", {"adapter": DESTINATION_ADAPTER, "active": 1})
	if existing:
		return existing
	return frappe.get_doc(
		{
			"doctype": "Annual Plan Publication Destination", "destination_id": "MOH-APP-SANDBOX-v1",
			"title": "KenTender Annual Plan Publication Sandbox", "adapter": DESTINATION_ADAPTER, "active": 1, "sandbox_outcome": "Acknowledge",
		}
	).insert(ignore_permissions=True).name


def commit_approved_plan(*, version, plan, decision, actor: str) -> dict[str, str]:
	"""§5.5.2 — get-or-create, keyed by the exact Version: a retried or
	duplicated `ApproveAnnualPlan` after a partial failure lands on the same
	snapshot/publication/intent identifiers, never a second approved package."""
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

	existing_intent = frappe.db.get_value("Publication Intent", {"publication": publication.name}, "name")
	if existing_intent:
		intent = frappe.get_doc("Publication Intent", existing_intent)
	else:
		intent = frappe.get_doc(
			{
				"doctype": "Publication Intent", "publication": publication.name, "dispatch_state": "Committed",
				"created_at": now_datetime(), "record_version": 0, "fixture_namespace": cstr(version.fixture_namespace),
			}
		).insert(ignore_permissions=True)
	return {"snapshot": snapshot.name, "publication": publication.name, "intent": intent.name}


def _active_hold(plan_version: str):
	return frappe.db.get_value("Plan Publication Hold", {"plan_version": plan_version, "hold_state": "Active"}, "name")


def _payload_and_hash(publication):
	return json.loads(publication.manifest)[0] if publication.manifest else None, publication.package_hash


def _transmit(destination: str) -> tuple[str, str]:
	"""The sandbox adapter: `Annual Plan Publication Destination.sandbox_outcome`
	drives the simulated result so tests can prove the Failed/Indeterminate
	recovery paths without a real external destination to fail against."""
	outcome = cstr(frappe.db.get_value("Annual Plan Publication Destination", destination, "sandbox_outcome") or "Acknowledge")
	if outcome == "Fail":
		return "Failed", ""
	if outcome == "Indeterminate":
		return "Indeterminate", ""
	return "Acknowledged", frappe.generate_hash(length=16)


def publish_annual_plan(*, plan_version: str, idempotency_key: str | None = None, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `PublishAnnualPlan` — the system worker. Gated on valid current
	Treasury evidence and no active hold; sends the exact frozen manifest
	under the publication's own stable identity (never a new package)."""
	actor = authz.require_technical(user)
	payload_key = {"plan_version": plan_version}
	if idempotency_key:
		replay = envelope.replay_or_none(idempotency_key, payload_key)
		if replay:
			return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	if version.version_status not in ("Approved — publication pending", "Publication failed"):
		fail("PLN_REVIEW_STALE")
	publication_name = frappe.db.get_value("Plan Publication", {"plan_version": version.name}, "name")
	if not publication_name:
		fail("PLN_REVIEW_STALE", "Approval has not committed a publication yet.")
	publication = frappe.get_doc("Plan Publication", publication_name)
	if _active_hold(version.name):
		fail("PLN_PUBLICATION_HELD")
	current_evidence = frappe.db.get_value("Treasury Submission Evidence", {"plan_version": version.name, "evidence_state": "Current"}, "name")
	if not current_evidence:
		fail("PLN_TREASURY_EVIDENCE_REQUIRED")

	attempt_number = frappe.db.count("Publication Attempt", {"publication": publication.name}) + 1
	result, external_reference = _transmit(publication.destination)
	attempt = frappe.get_doc(
		{
			"doctype": "Publication Attempt", "publication": publication.name, "attempt_number": attempt_number, "result": result,
			"attempted_at": now_datetime(), "external_reference": external_reference or None,
			"completed_at": now_datetime() if result != "Pending" else None, "fixture_namespace": cstr(version.fixture_namespace),
		}
	).insert(ignore_permissions=True)

	if result == "Failed":
		envelope.bump(version, version_status="Publication failed")
		frappe.db.set_value("Plan Publication", publication.name, "publication_state", "Failed", update_modified=False)
	elif result == "Indeterminate":
		frappe.db.set_value("Plan Publication", publication.name, "publication_state", "Indeterminate", update_modified=False)
		frappe.db.set_value("Publication Intent", {"publication": publication.name}, "dispatch_state", "Dispatched", update_modified=False)
	else:
		frappe.db.set_value("Publication Intent", {"publication": publication.name}, {"dispatch_state": "Dispatched", "dispatched_at": now_datetime()}, update_modified=False)
		receive_publication_acknowledgement(
			event_id=f"{publication.name}:{attempt.name}", publication=publication.name, package_hash=publication.package_hash,
			external_reference=external_reference, acknowledged_at=now_datetime(), user="Administrator",
		)
	version.reload()
	result_dict = {"ok": True, "idempotent": False, "action": "publish_attempted", "publication": publication.name, "attempt": attempt.name, "result": result, "version_status": version.version_status}
	if idempotency_key:
		envelope.record_command(
			idempotency_key=idempotency_key, command="PublishAnnualPlan", payload=payload_key, result=result_dict,
			document_type="Publication Attempt", document_name=attempt.name, actor=actor, fixture_namespace=cstr(version.fixture_namespace),
		)
	return result_dict


def receive_publication_acknowledgement(
	*, event_id: str, publication: str, package_hash: str, public_location: str = "", external_reference: str = "",
	acknowledged_at=None, idempotency_key: str | None = None, user: str | None = None,
) -> dict[str, Any]:
	"""§7.2 `ReceivePublicationAcknowledgement` — authenticated exact-package
	correlation; duplicate event id is idempotent; a mismatched hash never
	activates. Runs the activation predicates and switches once, or holds."""
	actor = authz.require_technical(user)
	event_id = cstr(event_id).strip()
	if not event_id:
		fail("PLN_ENTRY_INCOMPLETE", "An acknowledgement needs its adapter event id.", {"field": "event_id"})
	existing = frappe.db.get_value("Publication Acknowledgement", {"event_id": event_id}, "name")
	if existing:
		ack = frappe.get_doc("Publication Acknowledgement", existing)
		return {"ok": True, "idempotent": True, "action": "acknowledged", "acknowledgement": ack.name, "publication": ack.publication, "matched": bool(ack.matched)}
	pub = envelope.locked("Plan Publication", publication)
	matched = cstr(package_hash) == cstr(pub.package_hash)
	ack = frappe.get_doc(
		{
			"doctype": "Publication Acknowledgement", "event_id": event_id, "publication": pub.name, "snapshot": pub.snapshot,
			"destination": pub.destination, "package_hash": cstr(package_hash), "public_location": public_location,
			"external_reference": external_reference, "acknowledged_at": acknowledged_at or now_datetime(), "received_at": now_datetime(),
			"matched": 1 if matched else 0, "mismatch_reason": "" if matched else "The acknowledged package hash does not match this publication.",
			"fixture_namespace": cstr(pub.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	if not matched:
		fail("PLN_PUBLICATION_ACK_MISMATCH", detail={"publication": pub.name, "acknowledgement": ack.name})

	frappe.db.set_value("Plan Publication", pub.name, {"publication_state": "Acknowledged", "acknowledged_at": ack.acknowledged_at, "public_location": public_location, "external_reference": external_reference}, update_modified=False)
	open_attempt = frappe.db.get_value("Publication Attempt", {"publication": pub.name, "result": ("in", ("Pending", "Acknowledged"))}, "name", order_by="attempt_number desc")
	if open_attempt:
		frappe.db.set_value("Publication Attempt", open_attempt, {"result": "Acknowledged", "completed_at": ack.acknowledged_at, "external_reference": external_reference}, update_modified=False)
	frappe.db.set_value("Publication Intent", {"publication": pub.name}, "dispatch_state", "Completed", update_modified=False)

	activation = activate_plan_version(plan_version=pub.plan_version, user="Administrator")
	result_dict = {"ok": True, "idempotent": False, "action": "acknowledged", "acknowledgement": ack.name, "publication": pub.name, "matched": True, "activation": activation}
	if idempotency_key:
		envelope.record_command(
			idempotency_key=idempotency_key, command="ReceivePublicationAcknowledgement", payload={"publication": publication, "event_id": event_id},
			result=result_dict, document_type="Publication Acknowledgement", document_name=ack.name, actor=actor, fixture_namespace=cstr(pub.fixture_namespace),
		)
	return result_dict


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


def reconcile_publication(*, publication: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `ReconcilePublication` — technical; reads the authoritative
	destination result. Never sets success manually; an unknown result
	stays Indeterminate."""
	actor = authz.require_technical(user)
	replay = envelope.replay_or_none(idempotency_key, {"publication": publication})
	if replay:
		return replay
	if not publication or not frappe.db.exists("Plan Publication", publication):
		authz.not_found()
	pub = envelope.locked("Plan Publication", publication)
	if pub.publication_state != "Indeterminate":
		fail("PLN_REVIEW_STALE", "Only an indeterminate publication needs reconciliation.")
	attempt_name = frappe.db.get_value("Publication Attempt", {"publication": pub.name, "result": "Indeterminate"}, "name", order_by="attempt_number desc")
	looked_up = _transmit(pub.destination)[0]  # sandbox: the destination's own current outcome answers the reconciliation query
	if looked_up == "Acknowledged":
		outcome = receive_publication_acknowledgement(event_id=f"reconcile:{publication}", publication=pub.name, package_hash=pub.package_hash, user="Administrator")
		result = {"ok": True, "idempotent": False, "action": "reconciled", "outcome": "Acknowledged", "detail": outcome}
	elif looked_up == "Failed":
		if attempt_name:
			frappe.db.set_value("Publication Attempt", attempt_name, {"result": "Failed", "completed_at": now_datetime()}, update_modified=False)
		envelope.bump(pub, publication_state="Failed")
		version = frappe.get_doc("Annual Plan Version", pub.plan_version)
		if version.version_status not in ("Active", "Published — activation held"):
			frappe.db.set_value("Annual Plan Version", pub.plan_version, "version_status", "Publication failed", update_modified=False)
		result = {"ok": True, "idempotent": False, "action": "reconciled", "outcome": "Failed"}
	else:
		result = {"ok": True, "idempotent": False, "action": "reconciled", "outcome": "Indeterminate"}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReconcilePublication", payload={"publication": publication}, result=result,
		document_type="Plan Publication", document_name=pub.name, actor=actor, fixture_namespace=cstr(pub.fixture_namespace),
	)
	return result


def retry_publication(*, publication: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `RetryPublication` — technical; the SAME frozen manifest and
	identity, from a confirmed Failed publication only (Indeterminate must
	reconcile first)."""
	actor = authz.require_technical(user)
	replay = envelope.replay_or_none(idempotency_key, {"publication": publication})
	if replay:
		return replay
	if not publication or not frappe.db.exists("Plan Publication", publication):
		authz.not_found()
	pub = frappe.get_doc("Plan Publication", publication)
	version = frappe.get_doc("Annual Plan Version", pub.plan_version)
	if version.version_status != "Publication failed":
		fail("PLN_REVIEW_STALE")
	result_dict = publish_annual_plan(plan_version=version.name, user="Administrator")
	result_dict = {**result_dict, "action": "retried"}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RetryPublication", payload={"publication": publication}, result=result_dict,
		document_type="Publication Attempt", document_name=result_dict["attempt"], actor=actor, fixture_namespace=cstr(pub.fixture_namespace),
	)
	return result_dict


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
