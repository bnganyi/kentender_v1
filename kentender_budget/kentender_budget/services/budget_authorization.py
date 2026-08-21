"""Shared authorization projections for Budget records and workflow tasks."""

from __future__ import annotations

from collections.abc import Iterable
import frappe
from frappe import _

from kentender_core.services.authorization_policy import ResourceContext, evaluate_capability, require_capability
from kentender_core.services.workflow_routing import RoutingContext
from kentender_core.services.workflow_tasks import TaskSpec, create_routed_task, get_authorized_task, transition_task

CAP_BUDGET_LIST = "budget.list"
CAP_BUDGET_VIEW = "budget.view"
CAP_BUDGET_CREATE = "budget.create"
CAP_BUDGET_EDIT = "budget.edit"
CAP_BUDGET_SUBMIT = "budget.submit"
CAP_BUDGET_REVIEW = "budget.review"
CAP_BUDGET_RETURN = "budget.return"
CAP_BUDGET_APPROVE = "budget.approve"
CAP_BUDGET_EXPORT = "budget.export"
# BUD-CHG-001 §8 — Budget Activation Authority (CAP_BUDGET_APPROVE, above) is
# distinct from Revision Authority and Finance Confirmation Officer: each is an
# independently assignable capability, not a shared role.
CAP_BUDGET_REVISION_APPLY = "budget.revision.apply"
CAP_BUDGET_RESERVE = "budget.reserve"


def budget_resource(budget, *, resource_type: str = "Budget", resource_id: str = "") -> ResourceContext:
	return ResourceContext(
		resource_type=resource_type,
		resource_id=resource_id or budget.name,
		procuring_entity_id=budget.procuring_entity,
		financial_year_id=budget.fiscal_period or "",
		organisation_unit_id=getattr(budget, "owner_org_unit", None) or "",
		state=getattr(budget, "status", None) or "",
		relationships={"owner": getattr(budget, "owner", None) or ""},
	)


def require_budget_capability(capability: str, budget) -> None:
	require_capability(frappe.session.user, capability, budget_resource(budget))


def can_budget(capability: str, budget) -> bool:
	return evaluate_capability(frappe.session.user, capability, budget_resource(budget)).allowed


def create_budget_task(
	budget,
	*,
	capability: str,
	task_type: str,
	subject_type: str = "Budget",
	subject_id: str = "",
	predecessor_task_id: str = "",
	iteration: int = 1,
):
	subject_id = subject_id or budget.name
	if iteration <= 0:
		iteration = (
			frappe.db.count(
				"Workflow Task",
				{"subject_type": subject_type, "subject_id": subject_id, "task_type": task_type},
			)
			+ 1
		)
	return create_routed_task(
		TaskSpec(
			routing=RoutingContext(
				module_name="Budget & Funding",
				task_type=task_type,
				procuring_entity_id=budget.procuring_entity,
				financial_year_id=budget.fiscal_period or "",
				organisation_unit_id=getattr(budget, "owner_org_unit", None) or "",
				resource_scope_type=subject_type,
				resource_scope_id=subject_id,
			),
			subject_type=subject_type,
			subject_id=subject_id,
			idempotency_key=f"budget:{subject_type}:{subject_id}:{task_type}:{iteration}",
			task_iteration=iteration,
			predecessor_task_id=predecessor_task_id,
		),
		actor=frappe.session.user,
	)


def require_budget_task(
	payload: dict,
	*,
	capability: str,
	subject_type: str,
	subject_id: str,
):
	task_id = (payload.get("task_id") or "").strip()
	token = (payload.get("concurrency_token") or "").strip()
	if not task_id or not token:
		frappe.throw(
			_("A current My Work task and concurrency token are required."),
			frappe.PermissionError,
			title="BUDGET_TASK_REQUIRED",
		)
	task = get_authorized_task(task_id, actor=frappe.session.user, capability=capability)
	if task.subject_type != subject_type or task.subject_id != subject_id:
		frappe.throw(_("The task does not belong to this Budget record."), frappe.PermissionError, title="BUDGET_TASK_SUBJECT_MISMATCH")
	return task, token


def complete_budget_task(task, token: str, *, capability: str, target_state: str = "Completed", prior_actions=None):
	return transition_task(
		task.name,
		actor=frappe.session.user,
		capability=capability,
		target_state=target_state,
		expected_token=token,
		prior_actions=prior_actions or [],
	)


def authorized_budget_task(
	*,
	actor: str,
	subject_type: str,
	subject_id: str,
	capabilities: Iterable[str],
	task_id: str = "",
):
	"""Return the current matching task and allowed commands, or no task.

	A record state is deliberately insufficient. The actor must have both an
	active assignment for the capability and access to the current task.
	"""
	filters = {
		"subject_type": subject_type,
		"subject_id": subject_id,
		"state": "Open",
	}
	if task_id:
		filters["name"] = task_id

	for name in frappe.get_all("Workflow Task", filters=filters, pluck="name", order_by="created_at desc"):
		task = frappe.get_doc("Workflow Task", name)
		resource = {
			"resource_type": task.subject_type,
			"resource_id": task.subject_id,
			"procuring_entity_id": task.procuring_entity_id,
			"financial_year_id": task.financial_year_id,
			"organisation_unit_id": task.organisation_unit_id,
		}
		allowed = tuple(
			capability
			for capability in capabilities
			if evaluate_capability(actor, capability, resource, task_id=task.name).allowed
		)
		if allowed:
			return task, allowed
	return None, ()
