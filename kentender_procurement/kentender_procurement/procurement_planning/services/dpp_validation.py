# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.2 §4.6 / §5 — DPP validation decisions.

`AcceptDepartmentalPlan` records one governed classification per submitted
entry on the immutable decision (never on the entry — §8.1), marks the
Version accepted, and in the same transaction creates or reuses the initial
Draft Annual Plan under the DB uniqueness constraint (invariants 2/24): a
concurrent first acceptance reloads the winner instead of duplicating.
`ReturnDepartmentalPlan` preserves the submitted snapshot and creates the
copied correction Draft with the structured issues attached.
"""

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	authority,
	envelope,
	references,
)
from kentender_procurement.procurement_planning.services.dpp_lifecycle import (
	copy_entries,
	_next_version_number,
)
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_PROCUREMENT_PLANNER,
)


def _open_task(task_name: str):
	if not task_name or not frappe.db.exists("Departmental Plan Validation Task", task_name):
		authority.not_found()
	task = frappe.get_doc("Departmental Plan Validation Task", task_name)
	if task.status != "Open":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	return task


def _authorise_planner(actor: str, task) -> str:
	role = authority.require_scope(
		actor,
		roles=(ROLE_PROCUREMENT_PLANNER,),
		procuring_entity=task.procuring_entity,
	)
	# Planner OU scope narrows only when OU rows exist (§6: assigned PE and
	# permitted OUs); PE-wide planners hold no OU rows.
	ous = authority.permitted_org_units(actor)
	if ous and cstr(task.organisation_unit) not in ous:
		authority.not_found()
	return role


def _maker_checker(actor: str, submission_name: str) -> None:
	submitted_by = frappe.db.get_value(
		"Departmental Plan Submission", submission_name, "submitted_by_user"
	)
	if cstr(submitted_by) == actor:
		fail(
			"PLN_SEGREGATION_CONFLICT",
			"You cannot make this decision because you performed an incompatible earlier action.",
		)


def _decide(task, *, decision: str, actor: str, role: str, classifications=None, issues=None,
            idempotency_key: str = "") -> Any:
	root_scope = (task.procuring_entity, task.organisation_unit, task.financial_year)
	version_number = frappe.db.get_value(
		"Departmental Plan Version", task.dpp_version, "version_number"
	)
	dpp_reference = frappe.db.get_value(
		"Departmental Plan",
		frappe.db.get_value("Departmental Plan Version", task.dpp_version, "departmental_plan"),
		"dpp_reference",
	)
	doc = frappe.get_doc(
		{
			"doctype": "Departmental Plan Validation Decision",
			"decision_reference": references.validation_decision_reference(
				dpp_reference, version_number
			),
			"task": task.name,
			"submission": task.submission,
			"decision": decision,
			"classifications": json.dumps(classifications) if classifications else None,
			"issues": json.dumps(issues) if issues else None,
			"actor": actor,
			"authority_snapshot": authority.authority_snapshot(actor, role=role, values=root_scope),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Departmental Plan Validation Task", task.name,
		{"status": "Completed", "decision": doc.name},
		update_modified=False,
	)
	return doc


def return_departmental_plan(
	*,
	task: str,
	issues: list[dict[str, str]] | str,
	task_token: str,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	if isinstance(issues, str):
		issues = json.loads(issues)
	payload = {"task": task, "issues": json.dumps(issues, sort_keys=True)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task)
	role = _authorise_planner(actor, task_doc)
	envelope.assert_task_token(task_doc, task_token)
	_maker_checker(actor, task_doc.submission)
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
			"State at least one structured issue: the affected entry, the concise "
			"problem and the exact correction required.",
		)

	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	if version.version_status != "Submitted":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")
	decision = _decide(
		task_doc, decision="Return to department", actor=actor, role=role,
		issues=cleaned, idempotency_key=idempotency_key,
	)
	frappe.db.set_value(
		"Departmental Plan Version", version.name, "version_status", "Returned",
		update_modified=False,
	)
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
		idempotency_key=idempotency_key, command="ReturnDepartmentalPlan", payload=payload,
		result=result, document_type="Departmental Plan Validation Decision",
		document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def accept_departmental_plan(
	*,
	task: str,
	classifications: dict[str, str] | str,
	task_token: str,
	idempotency_key: str,
	user: str | None = None,
) -> dict[str, Any]:
	actor = cstr(user or frappe.session.user)
	if isinstance(classifications, str):
		classifications = json.loads(classifications)
	payload = {"task": task, "classifications": json.dumps(classifications, sort_keys=True)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task)
	role = _authorise_planner(actor, task_doc)
	envelope.assert_task_token(task_doc, task_token)
	_maker_checker(actor, task_doc.submission)

	version = frappe.get_doc("Departmental Plan Version", task_doc.dpp_version)
	root = envelope.locked("Departmental Plan", version.departmental_plan)
	if version.version_status != "Submitted":
		fail("PLN_REVIEW_STALE", "This task has already changed. Reload to see the current decision.")

	snapshots = json.loads(
		frappe.db.get_value("Departmental Plan Submission", task_doc.submission, "entry_snapshots")
	)
	active_types = set(
		frappe.get_all("Requirement Type", filters={"status": "Active"}, pluck="name")
	)
	unclassified = [
		row["entry_id"]
		for row in snapshots
		if cstr(classifications.get(row["entry_id"])) not in active_types
	]
	if unclassified:
		fail(
			"PLN_CLASSIFICATION_INCOMPLETE",
			"Classify every submitted requirement before accepting the plan: "
			f"{', '.join(unclassified)}.",
		)
	# source currency: every Need-origin snapshot must still be the current
	# accepted version (§12.6), read through the published contract (D5)
	from kentender_procurement.procurement_planning.services import needs_intake

	for row in snapshots:
		if row.get("need"):
			current = needs_intake.current_accepted_version_of(
				row["need"], task_doc.procuring_entity, task_doc.financial_year
			)
			if current != cstr(row.get("need_version")):
				fail(
					"PLN_SOURCE_UNAVAILABLE",
					"One or more selected departmental entries are no longer "
					"available for Plan Item formation.",
				)

	decision = _decide(
		task_doc, decision="Accept departmental plan", actor=actor, role=role,
		classifications=classifications, idempotency_key=idempotency_key,
	)
	prior_accepted = cstr(root.current_accepted_version)
	frappe.db.set_value(
		"Departmental Plan Version", version.name, "version_status", "Accepted",
		update_modified=False,
	)
	if prior_accepted and prior_accepted != version.name:
		frappe.db.set_value(
			"Departmental Plan Version", prior_accepted, "version_status", "Superseded",
			update_modified=False,
		)
	envelope.bump(
		root, current_state="Accepted",
		current_version=version.name, current_accepted_version=version.name,
	)
	plan = ensure_annual_plan(
		procuring_entity=task_doc.procuring_entity,
		financial_year=task_doc.financial_year,
		pe_fy_context=cstr(root.pe_fy_context),
		fixture_namespace=cstr(root.fixture_namespace),
	)
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
		idempotency_key=idempotency_key, command="AcceptDepartmentalPlan", payload=payload,
		result=result, document_type="Departmental Plan Validation Decision",
		document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def ensure_annual_plan(
	*,
	procuring_entity: str,
	financial_year: str,
	pe_fy_context: str,
	fixture_namespace: str = "",
) -> dict[str, str]:
	"""Create or reuse the one Annual Plan root + Draft Version 1 (invariant 24).

	The insert races only against another first acceptance; the DB unique on
	`pe_fy_context` guarantees one winner, and the loser reloads it."""
	existing = frappe.db.get_value(
		"Annual Plan", {"pe_fy_context": pe_fy_context},
		["name", "plan_reference", "open_successor_version", "active_version"],
		as_dict=True,
	)
	if existing:
		open_version = cstr(existing.open_successor_version)
		version_reference = (
			cstr(frappe.db.get_value("Annual Plan Version", open_version, "version_reference"))
			if open_version
			else ""
		)
		return {"plan_reference": existing.plan_reference, "version_reference": version_reference}

	pe_label = cstr(
		frappe.db.get_value("Procuring Entity", procuring_entity, "legal_name")
		or frappe.db.get_value("Procuring Entity", procuring_entity, "entity_name")
		or procuring_entity
	)
	fy_label = cstr(
		frappe.db.get_value("Financial Year", financial_year, "label") or financial_year
	)
	fy_period = fy_label.removeprefix("FY").strip()
	try:
		plan = frappe.get_doc(
			{
				"doctype": "Annual Plan",
				"plan_reference": references.plan_reference(procuring_entity, financial_year),
				"title": f"{pe_label} Annual Procurement Plan {fy_period}",
				"pe_fy_context": pe_fy_context,
				"procuring_entity": procuring_entity,
				"financial_year": financial_year,
				"record_version": 0,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
	except frappe.UniqueValidationError:
		# a concurrent first acceptance won the insert — reuse the winner
		return ensure_annual_plan(
			procuring_entity=procuring_entity,
			financial_year=financial_year,
			pe_fy_context=pe_fy_context,
			fixture_namespace=fixture_namespace,
		)
	version = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V1",
			"annual_plan": plan.name,
			"version_number": 1,
			"version_status": "Draft",
			"record_version": 0,
			"fixture_namespace": fixture_namespace,
		}
	).insert(ignore_permissions=True)
	frappe.db.set_value(
		"Annual Plan", plan.name, "open_successor_version", version.name,
		update_modified=False,
	)
	return {"plan_reference": plan.plan_reference, "version_reference": version.version_reference}
