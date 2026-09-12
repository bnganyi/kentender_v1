# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""PLN-CHG-001 v1.18 §5.2 / §6 / §7.2 — Annual Plan governance (see the command docstrings; v1.18: HOPF preparation signature, collective capacities, positive vs corrective predicates, correction cohort, held correction, late-activation explanation).

`SubmitConsolidatedPlan`/`SubmitCorrectedPlan` freeze the exact immutable
Plan Version (every accepted source allocated, every item passing the exact
readiness blockers, funding confirmation current, affordability within
approved) and create the Accounting Officer task; `AdoptAndSubmitPlan`
records adoption and creates exactly one statutory-approval task resolved
from the site's configured `statutory_approval_route` (four values, never
None — an unconfigured route blocks with `PLN_STATUTORY_ROUTE_UNCONFIGURED`);
`ApproveAnnualPlan` moves the Version to publication pending and runs the
system publication; `ReturnPlanVersion` preserves the submitted Version and
creates the next numbered Draft correction containing exactly its sources
and carrying the funding confirmation forward — repeated only when the
per-line totals or an approved amount changed (§5.2). Every corrected
submission restarts at Accounting Officer adoption (invariant 23). Late
activation (invariant 27) requires a recorded reason at submission (owner
default O2).
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe.utils import cstr, flt, getdate, now_datetime, nowdate

from kentender_procurement.procurement_planning.errors import fail
from kentender_procurement.procurement_planning.services import (
	envelope,
	plan_finance,
	plan_read,
	readiness,
	references,
	schedule,
)
from kentender_procurement.procurement_planning.services import planning_authorization as authz
from kentender_procurement.procurement_planning.services.planning_roles import (
	ROLE_ACCOUNTING_OFFICER,
	ROLE_HEAD_OF_PROCUREMENT_FUNCTION,
	ROLE_PLAN_STATUTORY_APPROVER,
	ROLE_PROCUREMENT_PLANNER,
)

STAGE_AO = "Accounting Officer adoption"
STAGE_STATUTORY = "Statutory approval"

CAPACITY_BY_ROUTE = {
	"Cabinet Secretary": "Responsible Cabinet Secretary",
	"County Executive Committee Member": "County Executive Committee Member",
	"Board of Directors": "Board of Directors",
	"Council": "Council",
}
# v1.18 §6.1 — Board and Council decide collectively: their decisions carry
# the collective resolution reference and the authorised recording actor.
COLLECTIVE_ROUTES = {"Board of Directors", "Council"}
CAPACITY_HOPF = "Head of Procurement Function"


def statutory_route() -> str:
	return cstr(frappe.db.get_single_value("Site Procuring Entity", "statutory_approval_route"))


def capacity_for_site() -> str:
	"""§4.12 — the one route configured for this entity; blank blocks."""
	route = statutory_route()
	if route not in CAPACITY_BY_ROUTE:
		fail("PLN_STATUTORY_ROUTE_UNCONFIGURED")
	return CAPACITY_BY_ROUTE[route]


def is_collective_capacity(capacity: str) -> bool:
	return cstr(capacity) in {CAPACITY_BY_ROUTE[r] for r in COLLECTIVE_ROUTES} or cstr(capacity) == "Governing body"


def _open_task(task_name: str, *, stage: str | None = None):
	if not task_name or not frappe.db.exists("Plan Governance Task", task_name):
		authz.not_found()
	task = frappe.get_doc("Plan Governance Task", task_name)
	if stage and task.stage != stage:
		authz.not_found()
	if task.status != "Open":
		fail("PLN_REVIEW_STALE")
	return task


def _stage_role(stage: str) -> str:
	return ROLE_ACCOUNTING_OFFICER if stage == STAGE_AO else ROLE_PLAN_STATUTORY_APPROVER


def _stage_action(stage: str) -> str:
	return authz.ACTION_AO_DECIDE if stage == STAGE_AO else authz.ACTION_STATUTORY_DECIDE


def _next_plan_version_number(annual_plan: str) -> int:
	rows = frappe.get_all("Annual Plan Version", filters={"annual_plan": annual_plan}, pluck="version_number")
	return max([int(n or 0) for n in rows] or [0]) + 1


def _build_snapshot(version, plan) -> dict[str, Any]:
	"""The exact immutable rows PLN-DES-11/12's ten-column Plan table renders,
	frozen once at submission — governance tasks read this JSON, never the
	live tables. Carries the advisory line (reserved share, splitting) too."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	eligible = {row["id"]: row for row in strategy_gateway.list_eligible_strategic_objectives()}
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")},
		fields=[
			"name", "plan_item_id", "title", "requirement_type", "procurement_category", "procurement_method",
			"strategic_objective", "reservation_category", "threshold_band_at_readiness", "baseline_delivery_completion_date",
			"plan_horizon", "aggregation_indicator", "lotting_indicator", "lot_count", "item_state",
		],
		order_by="creation asc",
	)
	rows = []
	for item in items:
		allocations = frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=["organisation_unit", "source_origin", "quantity", "unit", "indicative_amount"],
		)
		departments = sorted({cstr(frappe.db.get_value("Organisation Unit", a.organisation_unit, "unit_name") or a.organisation_unit) for a in allocations})
		origins = {a.source_origin for a in allocations}
		total_qty = sum(flt(a.quantity) for a in allocations)
		unit_label = plan_read._unit_label(allocations[0].unit) if allocations else ""
		value = sum(flt(a.indicative_amount) for a in allocations)
		objective = eligible.get(cstr(item.strategic_objective), {})
		rows.append(
			{
				"plan_item_id": item.plan_item_id,
				"title": item.title,
				"department": " / ".join(departments),
				"source_origin": next(iter(origins)) if len(origins) == 1 else "Multiple",
				"quantity_display": f"{total_qty:g} {unit_label.lower()}".strip() if allocations else "",
				"strategic_objective_label": objective.get("title", "") or cstr(frappe.db.get_value("Strategy Node", item.strategic_objective, "title") or ""),
				"procurement_method": cstr(item.procurement_method),
				"procurement_category": cstr(item.procurement_category),
				"reservation_category": cstr(item.reservation_category) or "None",
				"value": value,
				"value_display": plan_read._money(value),
				"delivery_completion_display": plan_read._date(item.baseline_delivery_completion_date),
				"funding": "Within budget",
				"value_band": cstr(item.threshold_band_at_readiness),
				"item_state": item.item_state,
			}
		)
	reference = readiness.reference_for(plan.fiscal_year)
	share = readiness.reservation_allocations(version.name, plan.fiscal_year, reference)
	target = share["target_percent"]
	advisories = readiness.splitting_advisory(version.name, reference)
	return {
		"rows": rows,
		"reserved_share_percent": round(share["percent_of_plan"], 1),
		"reservation_target_percent": target,
		"reservation_allocations": share,
		"splitting_advisory_count": len(advisories),
		"splitting_confirmation": cstr(version.splitting_confirmation),
	}


def _validate_ready_to_submit(version, plan) -> None:
	"""§8.2 `SubmitConsolidatedPlan`: every accepted source allocated, every
	item passing readiness, funding confirmation current."""
	unallocated = [
		row for row in plan_read._accepted_entry_rows(plan.fiscal_year)
		if row["dpp_entry"] not in plan_read._allocated_dpp_entries(version.name)
	]
	if unallocated:
		fail("PLN_ENTRY_INCOMPLETE", "Every accepted departmental entry must be allocated to a Plan Item before submission.")
	items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")}, pluck="name")
	if not items:
		fail("PLN_ENTRY_INCOMPLETE", "Form at least one Plan Item before submission.")
	plan_finance.validate_plan_ready(version, plan, stage="submission")
	statement = plan_finance.affordability_statement(plan, version)
	if not statement.get("within_approved"):
		fail("PLN_PLAN_NOT_AFFORDABLE", detail={"failing_lines": statement.get("failing_lines", [])})
	if not plan_finance.funding_is_current(version, statement):
		if version.funding_state == "Confirmed":
			frappe.db.set_value("Annual Plan Version", version.name, "funding_state", "Stale", update_modified=False)
		fail("PLN_FINANCE_STALE")


def _require_correction_cohort(version) -> None:
	"""§5.4.2 — a correction's allocations stay within the returned Version's
	stable source cohort (current revisions of the same sources; withdrawn
	or not-proceeding sources may be dropped)."""
	cohort = set(json.loads(version.source_cohort or "[]"))
	if not cohort:
		return
	strangers = sorted(k for k in source_cohort(version.name) if k not in cohort)
	if strangers:
		fail("PLN_CORRECTION_COHORT_VIOLATION", detail={"source_keys": strangers})


def record_late_activation_explanation(*, plan_version: str, reason: str, supersedes: str = "", idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `RecordLateActivationExplanation` — the Accounting Officer's
	append-only accountability for an initial Plan adopted after the
	financial year began; never rewrites publication or activation time."""
	actor = authz.actor(user)
	payload = {"plan_version": plan_version, "reason": " ".join(cstr(reason).split()), "supersedes": cstr(supersedes)}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	if version.version_status in ("Draft", "Returned", "Cancelled"):
		fail("PLN_STALE_WRITE", "A late-activation explanation belongs to an initial Plan Version under or after governance.")
	if cstr(version.based_on_version):
		fail("PLN_STALE_WRITE", "A late-activation explanation belongs to an initial Plan Version, not a successor.")
	if payload["supersedes"] and not frappe.db.exists("Late Activation Explanation", {"name": payload["supersedes"], "plan_version": version.name}):
		fail("PLN_STALE_WRITE", "The explanation being corrected does not belong to this Plan Version.")
	explanation = _record_late_explanation(version, plan, reason=payload["reason"], actor=actor, assignment=assignment, supersedes=payload["supersedes"])
	result = {"ok": True, "idempotent": False, "action": "late_explanation_recorded", "explanation": explanation.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="RecordLateActivationExplanation", payload=payload, result=result,
		document_type="Late Activation Explanation", document_name=explanation.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def begin_held_plan_correction(*, plan_version: str, reason: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `BeginHeldPlanCorrection` — one linked Draft correction of a
	**Published — activation held** Version: the correction origin is the
	held Version, the Active predecessor (if any) the real one; the held
	Version is never treated as Active. Fixed correction cohort."""
	actor = authz.actor(user)
	reason = " ".join(cstr(reason).split())
	payload = {"plan_version": plan_version, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (20 <= len(reason) <= 1000):
		fail("PLN_ENTRY_INCOMPLETE", "State why the held Version is being corrected (20–1,000 characters).", {"field": "reason"})
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = envelope.locked("Annual Plan", version.annual_plan)
	authz.require_site_role(ROLE_PROCUREMENT_PLANNER, actor)
	if version.version_status != "Published — activation held":
		fail("PLN_STALE_WRITE", "Only a Published — activation held Version takes a held correction.")
	if plan.open_successor_version and frappe.db.get_value("Annual Plan Version", plan.open_successor_version, "version_status") not in ("Active", "Superseded", "Cancelled", "Published — activation held"):
		fail("PLN_STALE_WRITE", "An open candidate already exists for this Plan.")
	number = _next_plan_version_number(plan.name)
	correction = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V{number}",
			"annual_plan": plan.name,
			"version_number": number,
			"based_on_version": plan.active_version or None,
			"correction_of_plan_version": version.name,
			"version_status": "Draft",
			"funding_state": "Not requested",
			"change_reason": reason,
			"project_name": version.project_name,
			"source_cohort": version.source_cohort or json.dumps(source_cohort(version.name)),
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	_copy_version_content(version.name, correction, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", correction.name, update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "held_correction_started", "correction_version": correction.name, "active_predecessor": cstr(plan.active_version)}
	envelope.record_command(
		idempotency_key=idempotency_key, command="BeginHeldPlanCorrection", payload=payload, result=result,
		document_type="Annual Plan Version", document_name=correction.name, actor=actor, fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def source_cohort(version_name: str) -> list[str]:
	"""§4.5 — the tagged stable source keys of the Version's live allocations."""
	keys = frappe.get_all(
		"Plan Source Allocation", filters={"plan_version": version_name, "allocation_state": ("in", ("Draft", "Active"))}, pluck="source_key", distinct=True,
	)
	return sorted(cstr(k) for k in keys if cstr(k))


def _freeze_and_task(version, plan, actor: str, assignment, *, idempotency_key: str) -> Any:
	"""§5.2.3 **Sign and submit Annual Plan** — lock the exact content, record
	the Head of Procurement Function's preparation signature for that exact
	snapshot, freeze the source cohort and create the Accounting Officer task."""
	snapshot = _build_snapshot(version, plan)
	snapshot_json = json.dumps(snapshot, sort_keys=True, default=str)
	snapshot_hash = hashlib.sha256(snapshot_json.encode()).hexdigest()
	snapshot_id = f"SNAP-{version.name}-{snapshot_hash[:12]}"
	signed_at = now_datetime()
	signature = frappe.get_doc(
		{
			"doctype": "Plan Preparation Signature",
			"plan_version": version.name,
			"submitted_snapshot_id": snapshot_id,
			"snapshot_hash": snapshot_hash,
			"actor": actor,
			"capacity": CAPACITY_HOPF,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"signed_at": signed_at,
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	envelope.bump(
		version,
		version_status="Awaiting Accounting Officer",
		submitted_snapshot=snapshot_json,
		snapshot_hash=snapshot_hash,
		submitted_snapshot_id=snapshot_id,
		preparation_signature=signature.name,
		source_cohort=json.dumps(source_cohort(version.name)) if not cstr(version.source_cohort) else version.source_cohort,
		submitted_by_user=actor,
		submitted_at=signed_at,
	)
	return frappe.get_doc(
		{
			"doctype": "Plan Governance Task",
			"task_reference": references.governance_task_reference(STAGE_AO, version.name),
			"annual_plan": plan.name,
			"plan_version": version.name,
			"stage": STAGE_AO,
			"capacity": "Accounting Officer",
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)


def submit_consolidated_plan(*, plan_version: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `SubmitConsolidatedPlan` — **Sign and submit Annual Plan** by the
	Head of Procurement Function (§6.2, D6): preparation accountability for
	the exact snapshot, not an added approval stage."""
	actor = authz.actor(user)
	payload = {"plan_version": plan_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	assignment = authz.require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor)
	if version.version_status != "Draft" or version.correction_of_plan_version:
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)
	capacity_for_site()
	_validate_ready_to_submit(version, plan)
	task = _freeze_and_task(version, plan, actor, assignment, idempotency_key=idempotency_key)
	result = {"ok": True, "idempotent": False, "action": "submitted", "task": task.name, "preparation_signature": version.preparation_signature, "submitted_snapshot_id": version.submitted_snapshot_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitConsolidatedPlan", payload=payload, result=result,
		document_type="Plan Governance Task", document_name=task.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result


def _decision(task_doc, version, *, decision: str, capacity: str, actor: str, assignment, resolution_reference: str = "", return_reason: str = "", idempotency_key: str = ""):
	return frappe.get_doc(
		{
			"doctype": "Plan Governance Decision",
			"decision_reference": references.governance_decision_reference(task_doc.stage, version.name),
			"task": task_doc.name,
			"plan_version": version.name,
			"stage": task_doc.stage,
			"decision": decision,
			"capacity": capacity,
			# PLN-CHG-001 v1.18 §6.1 / D7 — the collective resolution reference of a
			# Board or Council decision (the command parameter is renamed in Phase 2e)
			"collective_resolution_reference": resolution_reference or None,
			"return_reason": return_reason or None,
			"actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"decided_at": now_datetime(),
			"command_idempotency_key": idempotency_key,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)


def _require_positive_predicates(version, plan) -> None:
	"""§6.3 — a positive adoption/approval needs current source eligibility,
	current Strategy eligibility and current funding evidence; a return never
	does (its predicates are the corrective ones)."""
	from kentender_procurement.procurement_planning.services import strategy_gateway

	items = frappe.get_all("Annual Plan Item", filters={"plan_version": version.name, "item_state": ("!=", "Dissolved")}, fields=["name", "plan_item_id", "strategic_objective"])
	for item in items:
		for allocation in readiness._allocations(item.name):
			if plan_read.source_correction_required(allocation.dpp_entry):
				fail("PLN_SOURCE_CORRECTION_REQUIRED", detail={"plan_item_id": item.plan_item_id})
	eligible = {row["id"] for row in strategy_gateway.list_eligible_strategic_objectives()}
	for item in items:
		if cstr(item.strategic_objective) and cstr(item.strategic_objective) not in eligible:
			fail("PLN_STRATEGY_REVIEW_CHANGED", detail={"plan_item_id": item.plan_item_id})
	if not plan_finance.funding_is_current(version):
		fail("PLN_FINANCE_STALE")


def _is_initial_plan(version, plan) -> bool:
	return not cstr(version.based_on_version) and not cstr(plan.active_version)


def _fiscal_year_begun(plan) -> bool:
	start = frappe.db.get_value("Fiscal Year", plan.fiscal_year, "year_start_date")
	return bool(start) and getdate(nowdate()) >= getdate(start)


def _record_late_explanation(version, plan, *, reason: str, actor: str, assignment, supersedes: str = "") -> Any:
	reason = " ".join(cstr(reason).split())
	if not (20 <= len(reason) <= 1000):
		fail("PLN_LATE_EXPLANATION_REQUIRED", detail={"field": "reason"})
	return frappe.get_doc(
		{
			"doctype": "Late Activation Explanation",
			"plan_version": version.name,
			"reason": reason,
			"actor": actor,
			"authority_snapshot": authz.authority_snapshot(assignment),
			"recorded_at": now_datetime(),
			"supersedes": supersedes or None,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)


def adopt_and_submit_plan(*, task: str, task_token: str, idempotency_key: str, late_activation_explanation: str = "", user: str | None = None) -> dict[str, Any]:
	"""§7.2 `AdoptAndSubmitPlan` — adopt the exact reviewed Version, recheck
	the positive predicates and create one configured statutory task. An
	initial Plan adopted after its financial year began records the
	Accounting Officer's late-activation explanation (append-only)."""
	actor = authz.actor(user)
	payload = {"task": task, "late_activation_explanation": " ".join(cstr(late_activation_explanation).split())}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task, stage=STAGE_AO)
	assignment = authz.require_site_role(ROLE_ACCOUNTING_OFFICER, actor)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	authz.require_not_segregated(actor, authz.ACTION_AO_DECIDE, plan_version=version.name)
	if version.version_status != "Awaiting Accounting Officer":
		fail("PLN_REVIEW_STALE")
	capacity = capacity_for_site()
	_require_positive_predicates(version, plan)
	explanation = None
	if _is_initial_plan(version, plan) and _fiscal_year_begun(plan):
		if not payload["late_activation_explanation"] and not frappe.db.exists("Late Activation Explanation", {"plan_version": version.name}):
			fail("PLN_LATE_EXPLANATION_REQUIRED", detail={"field": "late_activation_explanation"})
		if payload["late_activation_explanation"]:
			explanation = _record_late_explanation(version, plan, reason=payload["late_activation_explanation"], actor=actor, assignment=assignment)

	decision = _decision(task_doc, version, decision="Adopt and submit", capacity="Accounting Officer", actor=actor, assignment=assignment, idempotency_key=idempotency_key)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Awaiting statutory approval")
	statutory_task = frappe.get_doc(
		{
			"doctype": "Plan Governance Task",
			"task_reference": references.governance_task_reference(STAGE_STATUTORY, version.name),
			"annual_plan": task_doc.annual_plan,
			"plan_version": version.name,
			"stage": STAGE_STATUTORY,
			"capacity": capacity,
			"status": "Open",
			"task_token": envelope.token(),
			"record_version": 0,
			"fixture_namespace": cstr(task_doc.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	result = {"ok": True, "idempotent": False, "action": "adopted", "statutory_task": statutory_task.name, "capacity": capacity, "late_activation_explanation": explanation.name if explanation else ""}
	envelope.record_command(
		idempotency_key=idempotency_key, command="AdoptAndSubmitPlan", payload=payload, result=result,
		document_type="Plan Governance Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def approve_annual_plan(*, task: str, task_token: str, collective_resolution_reference: str = "", idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `ApproveAnnualPlan` — the configured statutory capacity's positive
	decision; Board and Council record the collective resolution reference
	(§6.1). Positive predicates rechecked; publication is enqueued, never
	sent synchronously (Phase 2f completes the pipeline)."""
	actor = authz.actor(user)
	resolution_reference = cstr(collective_resolution_reference).strip()
	payload = {"task": task, "collective_resolution_reference": resolution_reference}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	task_doc = _open_task(task, stage=STAGE_STATUTORY)
	assignment = authz.require_site_role(ROLE_PLAN_STATUTORY_APPROVER, actor)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	authz.require_not_segregated(actor, authz.ACTION_STATUTORY_DECIDE, plan_version=version.name)
	if version.version_status != "Awaiting statutory approval":
		fail("PLN_REVIEW_STALE")
	if is_collective_capacity(task_doc.capacity) and not resolution_reference:
		fail("PLN_COLLECTIVE_RESOLUTION_REQUIRED", detail={"field": "collective_resolution_reference"})
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	capacity_for_site()
	_require_positive_predicates(version, plan)

	decision = _decision(
		task_doc, version, decision="Approve Annual Procurement Plan", capacity=task_doc.capacity, actor=actor,
		assignment=assignment, resolution_reference=resolution_reference, idempotency_key=idempotency_key,
	)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Approved — publication pending")

	# §5.5.2 (plan D8) — approval commits the exact immutable content and a
	# durable publication intent; external transmission happens afterwards,
	# never inside this transaction. Snapshot/publication/intent are
	# get-or-created keyed by the exact Version, so a retried or duplicated
	# ApproveAnnualPlan call after a partial failure lands on the same
	# identifiers rather than a second approved package (deterministic retry).
	from kentender_procurement.procurement_planning.services import publication_pipeline

	committed = publication_pipeline.commit_approved_plan(version=version, plan=plan, decision=decision, actor=actor)
	result = {
		"ok": True, "idempotent": False, "action": "approved", "plan_version": version.name,
		"snapshot": committed["snapshot"], "publication": committed["publication"], "intent": committed["intent"],
	}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ApproveAnnualPlan", payload=payload, result=result,
		document_type="Plan Governance Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


ITEM_COPY_FIELDS = (
	"plan_item_id", "title", "description", "strategic_objective", "strategy_plan", "strategy_plan_version",
	"objective_path", "requirement_type", "procurement_category", "procurement_method", "aggregation_reason",
	"plan_horizon", "aggregation_indicator", "lotting_indicator", "lot_count",
	"reservation_category", "reservation_category_reason", "county_resident_reservation", "exclusive_preference",
	"threshold_band_at_readiness", "baseline_invitation_date", *schedule.PERIOD_FIELDS, *schedule.BASELINE_FIELDS,
	"item_status",
	# PLN-CHG-001 v1.18 §4.6 — stable root, rule-profile evidence, method evidence, estimate basis, periods, feasibility
	"plan_item", "method_profile_version", "schedule_profile_version", "method_condition_evidence", "mandatory_restriction_results",
	"estimate_basis", "estimate_basis_reference", "estimated_delivery_period_days", "period_inputs", "baseline_milestones", "estimated_completion_date",
)
ALLOCATION_COPY_FIELDS = (
	"allocation_id", "dpp_entry", "source_origin", "source_key", "need", "need_revision", "organisation_unit",
	"quantity", "unit", "required_by_date", "budget_line", "indicative_amount",
)


def _copy_version_content(source_version: str, target_version, fixture_namespace: str) -> None:
	"""§4.8/§5.2 — a correction or successor contains exactly the source
	Version's items and allocations. Forecast and actual dates are never
	copied: forecasts exist only on an Active Version (invariant 12e)."""
	items = frappe.get_all(
		"Annual Plan Item",
		filters={"plan_version": source_version, "item_state": ("!=", "Dissolved")},
		fields=["name", *ITEM_COPY_FIELDS],
	)
	for source_item in items:
		new_item = frappe.get_doc(
			{
				"doctype": "Annual Plan Item",
				"plan_version": target_version.name,
				**{field: source_item.get(field) for field in ITEM_COPY_FIELDS},
				"item_state": "Draft",
				"record_version": 0,
				"fixture_namespace": fixture_namespace,
			}
		).insert(ignore_permissions=True)
		for allocation in frappe.get_all(
			"Plan Source Allocation",
			filters={"plan_item": source_item.name, "allocation_state": ("in", ("Draft", "Active"))},
			fields=list(ALLOCATION_COPY_FIELDS),
		):
			frappe.get_doc(
				{
					"doctype": "Plan Source Allocation",
					"plan_item": new_item.name,
					"plan_item_id": new_item.plan_item_id,
					"plan_version": target_version.name,
					**{field: allocation.get(field) for field in ALLOCATION_COPY_FIELDS},
					"allocation_state": "Draft",
					"fixture_namespace": fixture_namespace,
				}
			).insert(ignore_permissions=True)


def return_plan_version(*, task: str, reason: str, task_token: str, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	actor = authz.actor(user)
	reason = cstr(reason).strip()
	payload = {"task": task, "reason": reason}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	if not (10 <= len(reason) <= 500):
		fail("PLN_ENTRY_INCOMPLETE", "State one actionable correction reason.", {"field": "reason"})
	task_doc = _open_task(task)
	assignment = authz.require_site_role(_stage_role(task_doc.stage), actor)
	envelope.assert_task_token(task_doc, task_token)
	version = envelope.locked("Annual Plan Version", task_doc.plan_version)
	authz.require_not_segregated(actor, _stage_action(task_doc.stage), plan_version=version.name)
	expected_status = "Awaiting Accounting Officer" if task_doc.stage == STAGE_AO else "Awaiting statutory approval"
	if version.version_status != expected_status:
		fail("PLN_REVIEW_STALE")

	decision = _decision(task_doc, version, decision="Return for correction", capacity=task_doc.capacity, actor=actor, assignment=assignment, return_reason=reason, idempotency_key=idempotency_key)
	envelope.bump(task_doc, status="Completed", decision=decision.name)
	envelope.bump(version, version_status="Returned")

	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	number = _next_plan_version_number(plan.name)
	correction = frappe.get_doc(
		{
			"doctype": "Annual Plan Version",
			"version_reference": f"{plan.plan_reference}-V{number}",
			"annual_plan": plan.name,
			"version_number": number,
			"based_on_version": version.based_on_version or None,
			"correction_of_plan_version": version.name,
			"version_status": "Draft",
			# §5.2 — an unchanged plan carries its confirmation forward; the
			# staleness rules decide at resubmission whether Finance repeats.
			"funding_state": "Confirmed" if version.funding_state == "Confirmed" else "Not requested",
			"funding_line_totals_hash": version.funding_line_totals_hash if version.funding_state == "Confirmed" else None,
			"splitting_confirmation": version.splitting_confirmation,
			# §5.4.2 — the correction keeps the returned Version's stable source cohort
			"source_cohort": version.source_cohort or json.dumps(source_cohort(version.name)),
			"project_name": version.project_name,
			"change_reason": version.change_reason,
			"record_version": 0,
			"fixture_namespace": cstr(plan.fixture_namespace),
		}
	).insert(ignore_permissions=True)
	_copy_version_content(version.name, correction, cstr(plan.fixture_namespace))
	frappe.db.set_value("Annual Plan", plan.name, "open_successor_version", correction.name, update_modified=False)
	result = {"ok": True, "idempotent": False, "action": "returned", "correction_version": correction.name}
	envelope.record_command(
		idempotency_key=idempotency_key, command="ReturnPlanVersion", payload=payload, result=result,
		document_type="Plan Governance Decision", document_name=decision.name, actor=actor,
		fixture_namespace=cstr(task_doc.fixture_namespace),
	)
	return result


def submit_corrected_plan(*, plan_version: str, expected_record_version, idempotency_key: str, user: str | None = None) -> dict[str, Any]:
	"""§7.2 `SubmitCorrectedPlan` — the same final-submission service and
	guards as `SubmitConsolidatedPlan` (Finance basis evaluation, new
	preparation signature by the Head of Procurement Function); a corrected
	Plan always restarts at Accounting Officer adoption."""
	actor = authz.actor(user)
	payload = {"plan_version": plan_version}
	replay = envelope.replay_or_none(idempotency_key, payload)
	if replay:
		return replay
	version = envelope.locked("Annual Plan Version", plan_version)
	plan = frappe.get_doc("Annual Plan", version.annual_plan)
	assignment = authz.require_site_role(ROLE_HEAD_OF_PROCUREMENT_FUNCTION, actor)
	if version.version_status != "Draft" or not version.correction_of_plan_version:
		fail("PLN_STALE_WRITE")
	envelope.check_record_version(version, expected_record_version)
	capacity_for_site()
	_validate_ready_to_submit(version, plan)
	_require_correction_cohort(version)
	task = _freeze_and_task(version, plan, actor, assignment, idempotency_key=idempotency_key)
	result = {"ok": True, "idempotent": False, "action": "submitted", "task": task.name, "preparation_signature": version.preparation_signature, "submitted_snapshot_id": version.submitted_snapshot_id}
	envelope.record_command(
		idempotency_key=idempotency_key, command="SubmitCorrectedPlan", payload=payload, result=result,
		document_type="Plan Governance Task", document_name=task.name, actor=actor,
		fixture_namespace=cstr(plan.fixture_namespace),
	)
	return result
