"""Strategy plan readiness and workflow APIs."""

import frappe
from frappe import _

from kentender_strategy.services.strategy_readiness import evaluate_plan_readiness


def _get_plan(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	doc = frappe.get_doc("Strategic Plan", plan_name)
	frappe.has_permission(doc, ptype="read", throw=True)
	return doc


def _user_has_any_role(*roles: str) -> bool:
	user_roles = set(frappe.get_roles())
	if "Administrator" in frappe.session.user or "System Manager" in user_roles:
		return True
	return bool(user_roles.intersection(roles))


def _transition(plan_name: str, from_statuses: tuple[str, ...], to_status: str, allowed_roles: tuple[str, ...]):
	doc = _get_plan(plan_name)
	if not _user_has_any_role(*allowed_roles):
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	current = (doc.status or "").strip()
	if current not in from_statuses:
		frappe.throw(_("Cannot transition from {0} to {1}.").format(current, to_status))
	doc.status = to_status
	doc.save(ignore_permissions=True)
	return {"name": doc.name, "status": doc.status}


@frappe.whitelist()
def get_plan_readiness(plan_name: str):
	doc = _get_plan(plan_name)
	payload = evaluate_plan_readiness(plan_name)
	payload["status"] = doc.status
	return payload


@frappe.whitelist()
def submit_plan(plan_name: str):
	from kentender_strategy.services.strategy_readiness import assert_plan_readiness

	assert_plan_readiness(plan_name)
	return _transition(plan_name, ("Draft",), "Submitted", ("Strategy Manager",))


@frappe.whitelist()
def approve_plan(plan_name: str):
	return _transition(plan_name, ("Submitted",), "Approved", ("Planning Authority",))


@frappe.whitelist()
def activate_plan(plan_name: str):
	return _transition(plan_name, ("Approved",), "Active", ("Planning Authority", "Strategy Manager"))


@frappe.whitelist()
def archive_plan(plan_name: str):
	return _transition(plan_name, ("Active", "Approved"), "Archived", ("Planning Authority", "Strategy Manager"))


@frappe.whitelist()
def return_for_correction(plan_name: str):
	return _transition(plan_name, ("Submitted", "Approved"), "Draft", ("Planning Authority",))
