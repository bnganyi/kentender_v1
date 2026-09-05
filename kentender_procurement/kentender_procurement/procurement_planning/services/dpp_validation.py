# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.12 §4.6 / §5 — DPP validation decisions.

`AcceptDepartmentalPlan` records one governed classification per submitted
entry that proceeds (never on the entry — §8.1), marks the Version accepted,
publishes the §4.4 not-proceeding outcome back to Departmental Needs for any
entry the department recorded as not proceeding, and in the same
transaction creates or reuses the initial Draft Annual Plan under the DB
uniqueness constraint (invariants 2/28): a concurrent first acceptance
reloads the winner instead of duplicating. `ReturnDepartmentalPlan`
preserves the submitted snapshot and creates the copied correction Draft
with the structured issues attached.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import envelope, references
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.dpp_lifecycle import _next_version_number, copy_entries
from kentender_procurement.procurement_planning.services.planning_roles import ROLE_PROCUREMENT_PLANNER


def _open_task(task_name: str):
	if not task_name or not frappe.db.exists("Departmental Plan Validation Task", task_name):
		authz.not_found()
	task = frappe.get_doc("Departmental Plan Validation Task", task_name)
	if task.status != "Open":
		fail("PLN_REVIEW_STALE")
	return task


def _decide(task, *, decision: str, actor: str, assignment, classifications=None, issues=None, idempotency_key: str = "") -> Any:
	version_number = frappe.db.get_value("Departmental Plan Version", task.dpp_version, "version_number")
	dpp_reference = frappe.db.get_value(
		"Departmental Plan",
		frappe.db.get_value("Departmental Plan Version", task.dpp_version, "departmental_plan"),
		"dpp_reference",
	)
	doc = frappe.get_doc(
		{
			"doctype": "Departmental Plan Validation Decision",
			"decision_reference": references.validation_decision_reference(dpp_reference, version_number),
			"task": task.name,
			"submission": task.submission,
			"decision": decision,
			"classifications": json.dumps(classifications) if classifications else None,
			"issues": json.dumps(issues) if issues else None,
			"actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Departmental Plan Validation Task", task.name, {"status": "Completed", "decision": doc.name}, update_modified=False,
	)
	return doc


def return_departmental_plan(
	*, task: str, issues: list[dict[str, str]] | str, task_token: str, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(issues, str):
		issues = json.loads(issues)
	payload = {"task": task, "issues": json.dumps(issues, sort_keys=True)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task)
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	envelope.assert_task_token(task_doc, task_token)
	authz.require_not_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task_doc.submission)
	cleaned = [
		{
			"entry_id": cstr(row.get("entry_id")).strip(),
			"problem": cstr(row.get("problem")).strip(),
			"correction": cstr(row.get("correction")).strip(),
		}
		for row in (issues or [])
	]
	if not cleaned or any(not (row["entry_id"] and row["problem"] and row["correction"]) for row in cleaned):
		fail(
			"PLN_ENTRY_INCOMPLETE",
			"State at least one structured issue: the affected entry, the concise problem and the exact correction required.",
		)

	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	if version.version_status != "Submitted":
		fail("PLN_REVIEW_STALE")
	decision = _decide(
		task_doc, decision="Return to department", actor=actor, assignment=assignment, issues=cleaned, idempotency_key=idempotency_key,
	)
	frappe.db.set_value("Departmental Plan Version", version.name, "version_status", "Returned", update_modified=False)
	next_number = _next_version_number(root.name)
	correction = frappe.get_doc(
		{
			"doctype": "Departmental Plan Version",
			"version_reference": f"{root.dpp_reference}-V{next_number}",
			"departmental_plan": root.name,
			"version_number": next_number,
			"based_on_version": version.based_on_version or None,
			"returned_from_submission": task_doc.submission,
			"version_status": "Draft",
			"record_version": 0,
			"fixture_namespace": cstr(root.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	copy_entries(version.name, correction, cstr(root.fixture_namespace))
	envelope.bump(root, current_state="Returned", current_version=correction.name)
	result = {
		"ok": True,
		"idempotent": False,
		"action": "returned",
		"decision_reference": decision.decision_reference,
		"correction_version": correction.version_reference,
		"dpp_reference": root.dpp_reference,
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReturnDepartmentalPlan", payload=payload, result=result,
		document_type="Departmental Plan Validation Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def accept_departmental_plan(
	*, task: str, classifications: dict[str, str] | str, task_token: str, idempotency_key: str, user: str | None = None,
) -> dict[str, Any]:
	actor = authz.actor(user)
	if isinstance(classifications, str):
		classifications = json.loads(classifications)
	payload = {"task": task, "classifications": json.dumps(classifications, sort_keys=True)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task)
	assignment = authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	envelope.assert_task_token(task_doc, task_token)
	authz.require_not_segregated(actor, authz.ACTION_DPP_VALIDATE, submission=task_doc.submission)

	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	if version.version_status != "Submitted":
		fail("PLN_REVIEW_STALE")

	snapshots = json.loads(frappe.db.get_value("Departmental Plan Submission", task_doc.submission, "entry_snapshots"))
	active_types = set(frappe.get_all("Requirement Type", filters={"status": "Active"}, pluck="name"))
	proceeding = [row for row in snapshots if not cstr(row.get("not_proceeding_reason")).strip()]
	unclassified = [row["entry_id"] for row in proceeding if cstr(classifications.get(row["entry_id"])) not in active_types]
	if unclassified:
		fail("PLN_CLASSIFICATION_INCOMPLETE", f"Classify every submitted requirement before accepting the plan: {', '.join(unclassified)}.")
	from kentender_procurement.procurement_planning.services import needs_intake

	for row in snapshots:
		if row.get("need"):
			current = needs_intake.current_accepted_version_of(row["need"], task_doc.fiscal_year)
			if current != cstr(row.get("need_version")):
				fail("PLN_SOURCE_UNAVAILABLE")

	decision = _decide(
		task_doc, decision="Accept departmental plan", actor=actor, assignment=assignment,
		classifications={k: v for k, v in classifications.items() if k in {r["entry_id"] for r in proceeding}},
		idempotency_key=idempotency_key,
	)
	prior_accepted = cstr(root.current_accepted_version)
	frappe.db.set_value("Departmental Plan Version", version.name, "version_status", "Accepted", update_modified=False)
	if prior_accepted and prior_accepted != version.name:
		frappe.db.set_value("Departmental Plan Version", prior_accepted, "version_status", "Superseded", update_modified=False)
	envelope.bump(root, current_state="Accepted", current_version=version.name, current_accepted_version=version.name)
	plan = ensure_annual_plan(fiscal_year=task_doc.fiscal_year, fixture_namespace=cstr(root.fixture_namespace))
	_publish_not_proceeding(snapshots, decision.name)
	result = {
		"ok": True,
		"idempotent": False,
		"action": "accepted",
		"decision_reference": decision.decision_reference,
		"dpp_reference": root.dpp_reference,
		"annual_plan": plan["plan_reference"],
		"annual_plan_version": plan["version_reference"],
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="AcceptDepartmentalPlan", payload=payload, result=result,
		document_type="Departmental Plan Validation Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def _publish_not_proceeding(snapshots: list[dict[str, Any]], decision_name: str) -> None:
	"""§4.4 / PLN-AC-092 — the outcome reaches Departmental Needs through its
	own published usage contract (D12), never a table write."""
	from kentender_procurement.departmental_needs.services import usage as needs_usage

	for row in snapshots:
		reason = cstr(row.get("not_proceeding_reason")).strip()
		if not row.get("need") or not reason:
			continue
		needs_usage.project_planning_usage(
			departmental_need=row["need"],
			accepted_version=row["need_version"],
			usage="Not proceeding",
			not_proceeding_reason=reason,
			source_event_id=f"{decision_name}:{row['need_version']}:not-proceeding",
			source_event_time=now_datetime(),
			user="Administrator",
		)


def ensure_annual_plan(*, fiscal_year: str, fixture_namespace: str = "") -> dict[str, str]:
	"""Create or reuse the one Annual Plan root + Draft Version 1 (invariant 28).

	The insert races only against another first acceptance; the DB unique on
	`fiscal_year` guarantees one winner, and the loser reloads it."""
	existing = frappe.db.get_value(
		"Annual Plan", {"fiscal_year": fiscal_year},
		["name", "plan_reference", "open_successor_version", "active_version"], as_dict=True,
	)
	if existing:
		open_version = cstr(existing.open_successor_version)
		version_reference = cstr(frappe.db.get_value("Annual Plan Version", open_version, "version_reference")) if open_version else ""
		return {"plan_reference": existing.plan_reference, "version_reference": version_reference}

	pe_name = cstr(frappe.db.get_single_value("Site Procuring Entity", "pe_name"))
	try:
		plan = frappe.get_doc(
			{
				"doctype": "Annual Plan",
				"plan_reference": references.plan_reference(fiscal_year),
				"title": f"{pe_name} Annual Procurement Plan {references.fy_period_label(fiscal_year)}",
				"fiscal_year": fiscal_year,
				"record_version": 0,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
	except frappe.UniqueValidationError:
		return ensure_annual_plan(fiscal_year=fiscal_year, fixture_namespace=fixture_namespace)
	version = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V1",
			"annual_plan": plan.name,
			"version_number": 1,
			"version_status": "Draft",
			"funding_state": "Not requested",
			"record_version": 0,
			"fixture_namespace": fixture_namespace,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", version.name, update_modified=False)
	return {"plan_reference": plan.plan_reference, "version_reference": version.version_reference}
